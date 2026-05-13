"""
src/api/streaming/ws_handler.py
Step 14 — WebSocket Handler

Manages active WebSocket connections per case_id.
Used by the Workflow Supervisor to push the Mode B recommendation package
to the connected specialist client and to await their action.

The specialist.py route (Step 13) handles the raw WebSocket lifecycle;
this handler provides the higher-level send/receive abstraction that
agent nodes call directly.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

import structlog
from fastapi import WebSocket

logger = structlog.get_logger(__name__)


class WebSocketHandler:
    """
    Registry of active WebSocket connections, keyed by case_id.

    Lifecycle:
        1. specialist.py calls register(case_id, ws) on WebSocket accept.
        2. Agent node calls send_mode_b_package(case_id, package).
        3. Agent node calls receive_specialist_action(case_id) — awaits reply.
        4. specialist.py calls deregister(case_id) on disconnect.
    """

    def __init__(self) -> None:
        self._connections: Dict[str, WebSocket] = {}
        self._action_futures: Dict[str, asyncio.Future] = {}

    # ── Connection management ──────────────────────────────────────────────────

    def register(self, case_id: str, websocket: WebSocket) -> None:
        """Register an active WebSocket for a case."""
        self._connections[case_id] = websocket
        logger.info("ws_handler.registered", case_id=case_id)

    def deregister(self, case_id: str) -> None:
        """Remove connection on close/disconnect."""
        self._connections.pop(case_id, None)
        # Cancel any pending future if client disconnects before responding
        future = self._action_futures.pop(case_id, None)
        if future and not future.done():
            future.cancel()
        logger.info("ws_handler.deregistered", case_id=case_id)

    def is_connected(self, case_id: str) -> bool:
        return case_id in self._connections

    # ── Mode B messaging ──────────────────────────────────────────────────────

    async def send_mode_b_package(
        self,
        case_id: str,
        package: Dict[str, Any],
        escalation_reason_codes: list[str] | None = None,
    ) -> bool:
        """
        Send the Mode B Full Recommendation Package to the specialist client.

        Returns True on success, False if no connection is open for this case.
        """
        ws = self._connections.get(case_id)
        if ws is None:
            logger.warning("ws_handler.no_connection_for_mode_b", case_id=case_id)
            return False

        from datetime import datetime, timezone
        payload = {
            "event": "mode_b_package",
            "case_id": case_id,
            "recommendation_package": package,
            "escalation_reason_codes": escalation_reason_codes or [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            await ws.send_json(payload)
            logger.info("ws_handler.mode_b_package_sent", case_id=case_id)
            return True
        except Exception as exc:
            logger.error("ws_handler.send_failed", case_id=case_id, error=str(exc))
            return False

    async def receive_specialist_action(
        self, case_id: str, timeout_seconds: float = 3600.0
    ) -> Optional[Dict[str, Any]]:
        """
        Await the specialist action message from the connected client.

        Returns the action dict on success, None on timeout or disconnect.
        The calling agent node must never block indefinitely — default timeout
        is 1 hour, matching the Mode B SLA window.
        """
        ws = self._connections.get(case_id)
        if ws is None:
            logger.warning("ws_handler.no_connection_for_receive", case_id=case_id)
            return None

        try:
            raw = await asyncio.wait_for(ws.receive_json(), timeout=timeout_seconds)
            logger.info("ws_handler.action_received", case_id=case_id)
            return raw
        except asyncio.TimeoutError:
            logger.warning("ws_handler.receive_timeout", case_id=case_id)
            return None
        except Exception as exc:
            logger.error("ws_handler.receive_error", case_id=case_id, error=str(exc))
            return None


# ── Module-level singleton ────────────────────────────────────────────────────
ws_handler = WebSocketHandler()
