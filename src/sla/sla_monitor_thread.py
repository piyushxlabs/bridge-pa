"""
src/sla/sla_monitor_thread.py
Step 12 — Implement SLA Monitor Parallel Task Manager

SLAMonitorManager is a module-level singleton that manages one asyncio.Task
per active case.  Each task polls elapsed time every 300 seconds and fires
tiered alerts at the thresholds defined in AGENT_LOGIC_SPEC.md Section 1:

  48 h → trigger_sla_alert(alert_level="standard")
  60 h → trigger_sla_alert(alert_level="critical")
  66 h → trigger_sla_alert(alert_level="code_red")
       + reroute_to_high_priority_queue()

Alert rules:
- Each threshold fires exactly once per case (tracked in _case_alert_state).
- If a poll skips a threshold (e.g., 47 h → 67 h), all missed thresholds are
  fired in order before the Code Red re-route.
- If trigger_sla_alert fails after 3 retries, a critical alert is sent for the
  delivery failure itself and the failure is logged as a permanent event.
- Circuit breaker check at every poll cycle — if open, polling pauses until
  the circuit is cleared.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

import structlog

from src.utils.circuit_breaker import circuit_breaker
from src.utils.exceptions import WorkflowHaltedException

# Tool execute functions
from src.tools.trigger_sla_alert import execute as trigger_sla_alert_execute
from src.tools.reroute_to_high_priority_queue import execute as reroute_execute
from src.tools.get_case_elapsed_times import execute as get_elapsed_execute

logger = structlog.get_logger(__name__)

# ── Threshold constants (hours) ───────────────────────────────────────────────
THRESHOLD_STANDARD_H: float = 48.0
THRESHOLD_CRITICAL_H: float = 60.0
THRESHOLD_CODE_RED_H: float = 66.0

# Poll interval in seconds (every 5 minutes per spec)
POLL_INTERVAL_SECONDS: int = 300


@dataclass
class CaseMonitorState:
    """Tracks per-case SLA alert firing state."""
    case_id: str
    intake_timestamp: float          # Unix epoch seconds
    assigned_specialist_id: str
    manager_id: str = "UM_MANAGER"
    alert_standard_fired: bool = False
    alert_critical_fired: bool = False
    alert_code_red_fired: bool = False
    reroute_fired: bool = False


class SLAMonitorManager:
    """
    Singleton manager for all active case SLA monitoring tasks.

    Usage:
        await sla_monitor_manager.register_case(case_id, intake_timestamp_iso, specialist_id)
        await sla_monitor_manager.deregister_case(case_id)
    """

    def __init__(self) -> None:
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._case_alert_state: Dict[str, CaseMonitorState] = {}

    # ── Public API ────────────────────────────────────────────────────────────

    async def register_case(
        self,
        case_id: str,
        intake_timestamp: float,   # Unix epoch seconds
        assigned_specialist_id: str,
        manager_id: str = "UM_MANAGER",
    ) -> None:
        """
        Add a case to the active monitoring set and start its polling task.
        Idempotent — if the case is already registered, this is a no-op.
        """
        if case_id in self._active_tasks:
            logger.warning("sla_monitor.already_registered", case_id=case_id)
            return

        state = CaseMonitorState(
            case_id=case_id,
            intake_timestamp=intake_timestamp,
            assigned_specialist_id=assigned_specialist_id,
            manager_id=manager_id,
        )
        self._case_alert_state[case_id] = state

        task = asyncio.create_task(
            self._monitor_loop(state),
            name=f"sla_monitor_{case_id}",
        )
        self._active_tasks[case_id] = task
        logger.info("sla_monitor.registered", case_id=case_id)

    async def deregister_case(self, case_id: str) -> None:
        """
        Remove a case from the monitoring set and cancel its polling task.
        Called only on confirmed closure signal from the Workflow Supervisor.
        """
        task = self._active_tasks.pop(case_id, None)
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass  # Expected — task was intentionally cancelled

        self._case_alert_state.pop(case_id, None)
        logger.info("sla_monitor.deregistered", case_id=case_id)

    def active_case_ids(self) -> list[str]:
        """Return the list of currently monitored case IDs (for testing)."""
        return list(self._active_tasks.keys())

    # ── Internal polling loop ─────────────────────────────────────────────────

    async def _monitor_loop(self, state: CaseMonitorState) -> None:
        """
        Per-case asyncio polling loop.
        Runs every POLL_INTERVAL_SECONDS until the task is cancelled.
        """
        while True:
            try:
                # Circuit breaker check — pause if open
                if circuit_breaker.is_circuit_open():
                    logger.warning(
                        "sla_monitor.circuit_open_pausing",
                        case_id=state.case_id,
                    )
                    await asyncio.sleep(POLL_INTERVAL_SECONDS)
                    continue

                elapsed_hours = self._compute_elapsed_hours(state.intake_timestamp)
                await self._evaluate_thresholds(state, elapsed_hours)

                await asyncio.sleep(POLL_INTERVAL_SECONDS)

            except asyncio.CancelledError:
                logger.info("sla_monitor.task_cancelled", case_id=state.case_id)
                raise  # Re-raise so the task terminates cleanly
            except Exception as exc:
                logger.error(
                    "sla_monitor.loop_error",
                    case_id=state.case_id,
                    error=str(exc),
                )
                await asyncio.sleep(POLL_INTERVAL_SECONDS)

    # ── Threshold evaluation ──────────────────────────────────────────────────

    async def _evaluate_thresholds(
        self, state: CaseMonitorState, elapsed_hours: float
    ) -> None:
        """
        Fire any un-fired alerts whose threshold has been crossed.
        Thresholds are always fired in ascending order (48 → 60 → 66),
        even if the poll interval skipped one.
        """
        if elapsed_hours >= THRESHOLD_STANDARD_H and not state.alert_standard_fired:
            await self._fire_alert(state, "standard")
            state.alert_standard_fired = True

        if elapsed_hours >= THRESHOLD_CRITICAL_H and not state.alert_critical_fired:
            await self._fire_alert(state, "critical")
            state.alert_critical_fired = True

        if elapsed_hours >= THRESHOLD_CODE_RED_H and not state.alert_code_red_fired:
            await self._fire_alert(state, "code_red")
            state.alert_code_red_fired = True
            if not state.reroute_fired:
                await self._fire_reroute(state)
                state.reroute_fired = True

    async def _fire_alert(
        self, state: CaseMonitorState, alert_level: str
    ) -> None:
        """
        Call trigger_sla_alert with exponential backoff retry (2s, 4s, 8s).
        On permanent failure: send a critical delivery-failure alert to manager
        and log the event.
        """
        params = {
            "alert_level": alert_level,
            "case_id": state.case_id,
            "specialist_id": state.assigned_specialist_id,
            "manager_id": state.manager_id,
        }

        delays = [2, 4, 8]
        for attempt, delay in enumerate(delays, start=1):
            result = await trigger_sla_alert_execute(params)
            if result.get("success"):
                logger.info(
                    "sla_monitor.alert_fired",
                    case_id=state.case_id,
                    alert_level=alert_level,
                )
                return
            logger.warning(
                "sla_monitor.alert_retry",
                case_id=state.case_id,
                alert_level=alert_level,
                attempt=attempt,
                error=result.get("error"),
            )
            if attempt < len(delays):
                await asyncio.sleep(delay)

        # All 3 attempts failed → permanent failure
        logger.error(
            "sla_monitor.alert_permanent_failure",
            case_id=state.case_id,
            alert_level=alert_level,
        )
        # Notify UM Manager of the delivery failure itself via critical alert
        await trigger_sla_alert_execute(
            {
                "alert_level": "critical",
                "case_id": state.case_id,
                "specialist_id": state.assigned_specialist_id,
                "manager_id": state.manager_id,
                "note": f"DELIVERY FAILURE: {alert_level} alert could not be delivered after 3 attempts.",
            }
        )

    async def _fire_reroute(self, state: CaseMonitorState) -> None:
        """
        Call reroute_to_high_priority_queue after Code Red alert is confirmed.
        Does NOT submit the authorization — only re-routes human assignment.
        """
        params = {
            "case_id": state.case_id,
            "specialist_id": state.assigned_specialist_id,
            "manager_id": state.manager_id,
        }
        result = await reroute_execute(params)
        if result.get("success"):
            logger.info("sla_monitor.rerouted", case_id=state.case_id)
        else:
            logger.error(
                "sla_monitor.reroute_failed",
                case_id=state.case_id,
                error=result.get("error"),
            )

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_elapsed_hours(intake_timestamp: float) -> float:
        """Return elapsed hours since intake_timestamp (Unix epoch seconds)."""
        return (time.time() - intake_timestamp) / 3600.0


# ── Module-level singleton ────────────────────────────────────────────────────
sla_monitor_manager = SLAMonitorManager()
