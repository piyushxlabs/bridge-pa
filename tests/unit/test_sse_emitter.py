"""
tests/unit/test_sse_emitter.py
Step 14 — SSE Emitter and WebSocket Handler Tests

Tests:
1.  emit() puts event on the queue
2.  emit() silently ignores empty case_id
3.  emit_step_started() emits correct event shape
4.  emit_step_completed() emits correct event shape
5.  emit_activity_log() emits correct event shape
6.  emit_routing_decision() emits correct payload
7.  emit_emergency_stop() emits correct payload
8.  emit_sla_alert() emits correct payload
9.  emit() never raises even if queue put_nowait fails
10. close_stream() puts None sentinel on queue
11. WebSocketHandler.register / deregister lifecycle
12. WebSocketHandler.is_connected reflects state
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.streaming.sse_emitter import SSEEmitter
from src.api.streaming.ws_handler import WebSocketHandler


# ─── Fixtures ─────────────────────────────────────────────────────────────────
@pytest.fixture
def emitter() -> SSEEmitter:
    return SSEEmitter()


@pytest.fixture
def ws_handler() -> WebSocketHandler:
    return WebSocketHandler()


# ── Test 1: emit() puts event on queue ───────────────────────────────────────
@pytest.mark.asyncio
async def test_emit_puts_event_on_queue(emitter: SSEEmitter) -> None:
    with patch("src.api.streaming.sse_emitter.get_or_create_queue") as mock_get_q:
        mock_q = MagicMock()
        mock_get_q.return_value = mock_q

        await emitter.emit("CASE-001", "step_status", {"step_name": "test"})

        mock_q.put_nowait.assert_called_once()
        payload = mock_q.put_nowait.call_args[0][0]
        assert payload["event"] == "step_status"
        assert payload["data"]["case_id"] == "CASE-001"
        assert payload["data"]["step_name"] == "test"
        assert "timestamp" in payload["data"]


# ── Test 2: emit() ignores empty case_id ─────────────────────────────────────
@pytest.mark.asyncio
async def test_emit_ignores_empty_case_id(emitter: SSEEmitter) -> None:
    with patch("src.api.streaming.sse_emitter.get_or_create_queue") as mock_get_q:
        await emitter.emit("", "step_status", {})
        mock_get_q.assert_not_called()


# ── Test 3: emit_step_started() shape ────────────────────────────────────────
@pytest.mark.asyncio
async def test_emit_step_started_correct_shape(emitter: SSEEmitter) -> None:
    with patch("src.api.streaming.sse_emitter.get_or_create_queue") as mock_get_q:
        mock_q = MagicMock()
        mock_get_q.return_value = mock_q

        await emitter.emit_step_started("CASE-002", 1, "Workflow Supervisor", "workflow_supervisor")

        payload = mock_q.put_nowait.call_args[0][0]
        assert payload["event"] == "step_status"
        assert payload["data"]["status"] == "started"
        assert payload["data"]["step_number"] == 1
        assert payload["data"]["step_name"] == "Workflow Supervisor"


# ── Test 4: emit_step_completed() shape ──────────────────────────────────────
@pytest.mark.asyncio
async def test_emit_step_completed_correct_shape(emitter: SSEEmitter) -> None:
    with patch("src.api.streaming.sse_emitter.get_or_create_queue") as mock_get_q:
        mock_q = MagicMock()
        mock_get_q.return_value = mock_q

        await emitter.emit_step_completed("CASE-003", 4, "Document Processing", "document_processing")

        payload = mock_q.put_nowait.call_args[0][0]
        assert payload["data"]["status"] == "completed"
        assert payload["data"]["step_number"] == 4


# ── Test 5: emit_activity_log() shape ────────────────────────────────────────
@pytest.mark.asyncio
async def test_emit_activity_log_correct_shape(emitter: SSEEmitter) -> None:
    with patch("src.api.streaming.sse_emitter.get_or_create_queue") as mock_get_q:
        mock_q = MagicMock()
        mock_get_q.return_value = mock_q

        await emitter.emit_activity_log("CASE-004", "audit", "PHI field logged", "document_processing")

        payload = mock_q.put_nowait.call_args[0][0]
        assert payload["event"] == "activity_log_entry"
        assert payload["data"]["category"] == "audit"
        assert payload["data"]["message"] == "PHI field logged"


# ── Test 6: emit_routing_decision() ──────────────────────────────────────────
@pytest.mark.asyncio
async def test_emit_routing_decision_payload(emitter: SSEEmitter) -> None:
    with patch("src.api.streaming.sse_emitter.get_or_create_queue") as mock_get_q:
        mock_q = MagicMock()
        mock_get_q.return_value = mock_q

        await emitter.emit_routing_decision("CASE-005", "mode_a", "mode_a")

        payload = mock_q.put_nowait.call_args[0][0]
        assert payload["event"] == "routing_decision"
        assert payload["data"]["mode"] == "mode_a"


# ── Test 7: emit_emergency_stop() ────────────────────────────────────────────
@pytest.mark.asyncio
async def test_emit_emergency_stop_payload(emitter: SSEEmitter) -> None:
    with patch("src.api.streaming.sse_emitter.get_or_create_queue") as mock_get_q:
        mock_q = MagicMock()
        mock_get_q.return_value = mock_q

        await emitter.emit_emergency_stop("CASE-006", "audit log failure", "case")

        payload = mock_q.put_nowait.call_args[0][0]
        assert payload["event"] == "emergency_stop"
        assert payload["data"]["scope"] == "case"


# ── Test 8: emit_sla_alert() ─────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_emit_sla_alert_payload(emitter: SSEEmitter) -> None:
    with patch("src.api.streaming.sse_emitter.get_or_create_queue") as mock_get_q:
        mock_q = MagicMock()
        mock_get_q.return_value = mock_q

        await emitter.emit_sla_alert("CASE-007", "critical", 60.5)

        payload = mock_q.put_nowait.call_args[0][0]
        assert payload["event"] == "sla_alert"
        assert payload["data"]["alert_level"] == "critical"
        assert payload["data"]["elapsed_hours"] == 60.5


# ── Test 9: emit() never raises on queue failure ──────────────────────────────
@pytest.mark.asyncio
async def test_emit_never_raises_on_queue_failure(emitter: SSEEmitter) -> None:
    with patch("src.api.streaming.sse_emitter.get_or_create_queue") as mock_get_q:
        mock_q = MagicMock()
        mock_q.put_nowait.side_effect = Exception("Queue full")
        mock_get_q.return_value = mock_q

        # Must NOT raise
        await emitter.emit("CASE-008", "step_status", {"step_name": "test"})


# ── Test 10: close_stream() sends None sentinel ───────────────────────────────
@pytest.mark.asyncio
async def test_close_stream_sends_none_sentinel(emitter: SSEEmitter) -> None:
    with patch("src.api.streaming.sse_emitter.get_or_create_queue") as mock_get_q:
        mock_q = MagicMock()
        mock_get_q.return_value = mock_q

        await emitter.close_stream("CASE-009")
        mock_q.put_nowait.assert_called_once_with(None)


# ── Test 11: WebSocketHandler register/deregister lifecycle ──────────────────
def test_ws_handler_register_deregister(ws_handler: WebSocketHandler) -> None:
    mock_ws = MagicMock()
    ws_handler.register("CASE-010", mock_ws)
    assert ws_handler.is_connected("CASE-010")
    ws_handler.deregister("CASE-010")
    assert not ws_handler.is_connected("CASE-010")


# ── Test 12: WebSocketHandler.is_connected reflects state ────────────────────
def test_ws_handler_is_connected_false_for_unknown(ws_handler: WebSocketHandler) -> None:
    assert not ws_handler.is_connected("UNKNOWN-CASE")
