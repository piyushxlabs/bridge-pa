"""
tests/unit/test_sla_monitor_thread.py
Step 12 — SLA Monitor Parallel Task Manager

Tests:
1. register_case — adds case to active set
2. deregister_case — removes case and cancels task
3. 48h threshold fires standard alert exactly once
4. 60h threshold fires critical alert exactly once
5. 66h threshold fires code_red alert + reroute exactly once
6. Missed thresholds (47h → 67h) fires all missed alerts in order
7. deregister_case is idempotent (double deregister does not raise)
8. Circuit breaker open — loop pauses (no alert fired while circuit is open)
"""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.sla.sla_monitor_thread import (
    SLAMonitorManager,
    CaseMonitorState,
    THRESHOLD_STANDARD_H,
    THRESHOLD_CRITICAL_H,
    THRESHOLD_CODE_RED_H,
)


# ─── Helper ───────────────────────────────────────────────────────────────────
def _make_manager() -> SLAMonitorManager:
    """Return a fresh SLAMonitorManager for each test."""
    return SLAMonitorManager()


def _elapsed_to_intake(hours_ago: float) -> float:
    """Return a Unix epoch timestamp that is `hours_ago` hours in the past."""
    return time.time() - (hours_ago * 3600.0)


# ─── Test 1: register_case adds to active set ─────────────────────────────────
@pytest.mark.asyncio
async def test_register_case_adds_to_active_set() -> None:
    manager = _make_manager()
    intake = _elapsed_to_intake(1.0)  # 1 hour ago — no alerts expected
    await manager.register_case("CASE-001", intake, "SP-001")

    assert "CASE-001" in manager.active_case_ids()

    # Cleanup
    await manager.deregister_case("CASE-001")


# ─── Test 2: deregister_case removes from active set ─────────────────────────
@pytest.mark.asyncio
async def test_deregister_case_removes_from_active_set() -> None:
    manager = _make_manager()
    intake = _elapsed_to_intake(1.0)
    await manager.register_case("CASE-002", intake, "SP-001")
    await manager.deregister_case("CASE-002")

    assert "CASE-002" not in manager.active_case_ids()


# ─── Test 3: 48h threshold fires standard alert exactly once ─────────────────
@pytest.mark.asyncio
@patch("src.sla.sla_monitor_thread.trigger_sla_alert_execute", new_callable=AsyncMock)
async def test_standard_alert_fires_at_48h(mock_alert: AsyncMock) -> None:
    mock_alert.return_value = {"success": True}
    manager = _make_manager()

    state = CaseMonitorState(
        case_id="CASE-003",
        intake_timestamp=_elapsed_to_intake(THRESHOLD_STANDARD_H + 0.1),
        assigned_specialist_id="SP-001",
    )

    await manager._evaluate_thresholds(state, THRESHOLD_STANDARD_H + 0.1)

    # standard fired, critical and code_red not yet
    assert state.alert_standard_fired is True
    assert state.alert_critical_fired is False
    assert state.alert_code_red_fired is False

    mock_alert.assert_called_once_with(
        {
            "alert_level": "standard",
            "case_id": "CASE-003",
            "specialist_id": "SP-001",
            "manager_id": "UM_MANAGER",
        }
    )


# ─── Test 4: 60h threshold fires critical alert exactly once ─────────────────
@pytest.mark.asyncio
@patch("src.sla.sla_monitor_thread.trigger_sla_alert_execute", new_callable=AsyncMock)
async def test_critical_alert_fires_at_60h(mock_alert: AsyncMock) -> None:
    mock_alert.return_value = {"success": True}
    manager = _make_manager()

    # Simulate that standard already fired
    state = CaseMonitorState(
        case_id="CASE-004",
        intake_timestamp=_elapsed_to_intake(THRESHOLD_CRITICAL_H + 0.1),
        assigned_specialist_id="SP-001",
        alert_standard_fired=True,  # already fired
    )

    await manager._evaluate_thresholds(state, THRESHOLD_CRITICAL_H + 0.1)

    assert state.alert_critical_fired is True
    assert state.alert_code_red_fired is False

    # Only critical alert should have been called
    mock_alert.assert_called_once_with(
        {
            "alert_level": "critical",
            "case_id": "CASE-004",
            "specialist_id": "SP-001",
            "manager_id": "UM_MANAGER",
        }
    )


# ─── Test 5: 66h threshold fires code_red + reroute exactly once ─────────────
@pytest.mark.asyncio
@patch("src.sla.sla_monitor_thread.reroute_execute", new_callable=AsyncMock)
@patch("src.sla.sla_monitor_thread.trigger_sla_alert_execute", new_callable=AsyncMock)
async def test_code_red_fires_alert_and_reroute(
    mock_alert: AsyncMock, mock_reroute: AsyncMock
) -> None:
    mock_alert.return_value = {"success": True}
    mock_reroute.return_value = {"success": True}
    manager = _make_manager()

    # Simulate both prior alerts already fired
    state = CaseMonitorState(
        case_id="CASE-005",
        intake_timestamp=_elapsed_to_intake(THRESHOLD_CODE_RED_H + 0.1),
        assigned_specialist_id="SP-001",
        alert_standard_fired=True,
        alert_critical_fired=True,
    )

    await manager._evaluate_thresholds(state, THRESHOLD_CODE_RED_H + 0.1)

    assert state.alert_code_red_fired is True
    assert state.reroute_fired is True

    mock_alert.assert_called_once_with(
        {
            "alert_level": "code_red",
            "case_id": "CASE-005",
            "specialist_id": "SP-001",
            "manager_id": "UM_MANAGER",
        }
    )
    mock_reroute.assert_called_once()


# ─── Test 6: Missed thresholds (47h → 67h) fires all 3 in order ─────────────
@pytest.mark.asyncio
@patch("src.sla.sla_monitor_thread.reroute_execute", new_callable=AsyncMock)
@patch("src.sla.sla_monitor_thread.trigger_sla_alert_execute", new_callable=AsyncMock)
async def test_missed_thresholds_all_fired_in_order(
    mock_alert: AsyncMock, mock_reroute: AsyncMock
) -> None:
    mock_alert.return_value = {"success": True}
    mock_reroute.return_value = {"success": True}
    manager = _make_manager()

    state = CaseMonitorState(
        case_id="CASE-006",
        intake_timestamp=_elapsed_to_intake(67.0),
        assigned_specialist_id="SP-001",
        # No alerts fired yet — simulates a poll jump from 47h to 67h
    )

    await manager._evaluate_thresholds(state, 67.0)

    assert state.alert_standard_fired is True
    assert state.alert_critical_fired is True
    assert state.alert_code_red_fired is True
    assert state.reroute_fired is True

    # All 3 alert levels should have been called
    call_levels = [call.args[0]["alert_level"] for call in mock_alert.call_args_list]
    assert call_levels == ["standard", "critical", "code_red"]
    mock_reroute.assert_called_once()


# ─── Test 7: Double deregister does not raise ─────────────────────────────────
@pytest.mark.asyncio
async def test_double_deregister_is_idempotent() -> None:
    manager = _make_manager()
    intake = _elapsed_to_intake(1.0)
    await manager.register_case("CASE-007", intake, "SP-001")
    await manager.deregister_case("CASE-007")
    # Second deregister should not raise
    await manager.deregister_case("CASE-007")
    assert "CASE-007" not in manager.active_case_ids()


# ─── Test 8: Alerts do NOT fire when circuit breaker is open ─────────────────
@pytest.mark.asyncio
@patch("src.sla.sla_monitor_thread.trigger_sla_alert_execute", new_callable=AsyncMock)
@patch("src.sla.sla_monitor_thread.circuit_breaker")
async def test_no_alert_when_circuit_is_open(
    mock_cb: MagicMock, mock_alert: AsyncMock
) -> None:
    mock_cb.is_circuit_open.return_value = True

    manager = _make_manager()
    # Register a case past the 48h threshold
    intake = _elapsed_to_intake(THRESHOLD_STANDARD_H + 1.0)
    await manager.register_case("CASE-008", intake, "SP-001")

    # Give the event loop a single tick — the loop checks circuit breaker first
    # and should sleep without calling _evaluate_thresholds
    await asyncio.sleep(0)

    # Since circuit is open, _evaluate_thresholds should NOT have been called
    mock_alert.assert_not_called()

    await manager.deregister_case("CASE-008")
