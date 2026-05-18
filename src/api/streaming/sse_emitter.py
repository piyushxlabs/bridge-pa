"""
src/api/streaming/sse_emitter.py
Step 14 — SSE Event Emitter

Module-level singleton that routes observability events from agent node
functions and tool execute functions into per-case asyncio.Queue instances
backed by the SSE stream endpoint (src/api/routes/workflow.py).

Design:
- emit() is always fire-and-forget via put_nowait() — it never blocks tool
  or agent execution, even if the client has disconnected.
- If the case queue does not exist (no active SSE subscriber), events are
  silently dropped (non-blocking).
- All data_dict values must be JSON-serializable primitives only — no PHI
  field values, no credential values.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict

import structlog

from src.api.routes.workflow import get_or_create_queue

logger = structlog.get_logger(__name__)


class SSEEmitter:
    """
    Fire-and-forget SSE event emitter.

    Usage (from any agent node or tool execute function):
        from src.api.streaming.sse_emitter import sse_emitter
        await sse_emitter.emit(case_id, "step_status", {"step_name": "...", "status": "started"})
    """

    async def emit(
        self,
        case_id: str,
        event_type: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Put an SSE event onto the case's queue.

        Args:
            case_id:    The active PA case identifier.
            event_type: One of the 13 event types defined in src/api/events.py.
            data:       JSON-serializable dict payload (no PHI values, no creds).
        """
        if not case_id:
            return

        # Send as a single stringified JSON under the 'data' field so sse-starlette
        # uses the default 'message' event, which React's EventSource.onmessage catches.
        payload = {
            "data": json.dumps({
                "event": event_type,
                "data": {
                    "case_id": case_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **data,
                }
            })
        }

        try:
            queue = get_or_create_queue(case_id)
            queue.put_nowait(payload)
        except Exception as exc:
            # Queue overflow or missing subscriber — log and continue.
            # Never raise: observability must never interrupt workflow execution.
            logger.warning(
                "sse_emitter.put_failed",
                case_id=case_id,
                event_type=event_type,
                error=str(exc),
            )

    async def emit_step_started(self, case_id: str, step_number: int, step_name: str, agent: str) -> None:
        await self.emit(case_id, "step_status", {
            "step_number": step_number,
            "step_name": step_name,
            "status": "in_progress",
            "agent": agent,
        })

    async def emit_step_completed(self, case_id: str, step_number: int, step_name: str, agent: str) -> None:
        await self.emit(case_id, "step_status", {
            "step_number": step_number,
            "step_name": step_name,
            "status": "completed",
            "agent": agent,
        })

    async def emit_step_failed(self, case_id: str, step_number: int, step_name: str, agent: str, error: str = "") -> None:
        await self.emit(case_id, "step_status", {
            "step_number": step_number,
            "step_name": step_name,
            "status": "failed",
            "agent": agent,
            "error": error,
        })

    async def emit_phi_audit_confirmed(
        self, case_id: str, phi_field_name: str, action_type: str, log_ref: str, agent: str
    ) -> None:
        await self.emit(case_id, "phi_audit_confirmed", {
            "phi_field_name": phi_field_name,
            "action_type": action_type,
            "log_ref": log_ref,
            "agent": agent,
        })

    async def emit_activity_log(self, case_id: str, category: str, message: str, agent: str) -> None:
        await self.emit(case_id, "activity_log_entry", {
            "category": category,
            "message": message,
            "agent": agent,
        })

    async def emit_routing_decision(self, case_id: str, mode: str, whitelist_determination: str) -> None:
        await self.emit(case_id, "routing_decision", {
            "mode": mode,
            "whitelist_determination": whitelist_determination,
        })

    async def emit_emergency_stop(self, case_id: str, reason: str, scope: str) -> None:
        await self.emit(case_id, "emergency_stop", {
            "reason": reason,
            "scope": scope,
        })

    async def emit_sla_alert(self, case_id: str, alert_level: str, elapsed_hours: float) -> None:
        await self.emit(case_id, "sla_alert", {
            "alert_level": alert_level,
            "elapsed_hours": elapsed_hours,
        })

    async def close_stream(self, case_id: str) -> None:
        """Send the None sentinel to terminate the SSE stream cleanly."""
        try:
            queue = get_or_create_queue(case_id)
            queue.put_nowait(None)
        except Exception:
            pass


# ── Module-level singleton ────────────────────────────────────────────────────
sse_emitter = SSEEmitter()
