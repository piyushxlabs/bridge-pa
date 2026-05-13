"""
src/api/routes/specialist.py
Step 13 — WS /workflow/{case_id}/action  (WebSocket)

On connect: pushes the Mode B Full Recommendation Package from shared state
to the specialist's dashboard client (Event Type 9 — mode_b_package).

On receive: validates the specialist action payload, writes it into the
LangGraph shared state via graph.update_state() to release the Mode B
interrupt gate on mode_b_specialist_action_node, then sends an acknowledgement
(Event Type 10 — specialist_action_ack).

Protocol:
  client CONNECT  →  server sends mode_b_package JSON
  client SENDS    →  { action_type, rationale }
  server RESPONDS →  { status: "confirmed", case_id, action_type }
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.graph.graph_builder import graph

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/workflow", tags=["specialist"])

VALID_ACTION_TYPES = {"approved", "modified", "overridden"}


@router.websocket("/{case_id}/action")
async def specialist_action_ws(websocket: WebSocket, case_id: str) -> None:
    """
    WS /workflow/{case_id}/action

    Manages the Mode B specialist approval gate via WebSocket.
    """
    await websocket.accept()
    logger.info("ws.connected", case_id=case_id)

    try:
        # 1. Retrieve the Mode B recommendation package from graph state
        config: Dict[str, Any] = {"configurable": {"thread_id": case_id}}
        state_snapshot = await graph.aget_state(config)
        current_state: Dict[str, Any] = state_snapshot.values if state_snapshot else {}

        package = current_state.get("artifacts", {}).get("full_recommendation_package", {})
        escalation_codes = current_state.get("criteria_evaluation", {}).get(
            "escalation_reason_codes", []
        )

        # 2. Send Mode B package to specialist client
        await websocket.send_json(
            {
                "event": "mode_b_package",
                "case_id": case_id,
                "recommendation_package": package,
                "escalation_reason_codes": escalation_codes,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        # 3. Await specialist action from client
        raw_message = await websocket.receive_text()
        payload: Dict[str, Any] = json.loads(raw_message)

        action_type: str = payload.get("action_type", "")
        rationale: str = payload.get("rationale", "")

        if action_type not in VALID_ACTION_TYPES:
            await websocket.send_json(
                {
                    "status": "error",
                    "detail": f"Invalid action_type '{action_type}'. Must be one of {VALID_ACTION_TYPES}.",
                }
            )
            await websocket.close()
            return

        action_timestamp = datetime.now(timezone.utc).isoformat()

        # 4. Release LangGraph Mode B interrupt gate via update_state
        specialist_id = current_state.get("session", {}).get("authorized_specialist_id", "")
        await graph.aupdate_state(
            config,
            {
                "current_context": {
                    **current_state.get("current_context", {}),
                    "awaiting_human_action": False,
                    "specialist_action": {
                        "action_type": action_type,
                        "action_timestamp": action_timestamp,
                        "rationale": rationale,
                    },
                }
            },
        )

        logger.info(
            "ws.specialist_action_confirmed",
            case_id=case_id,
            action_type=action_type,
            specialist_id=specialist_id,
        )

        # 5. Acknowledge to client
        await websocket.send_json(
            {
                "event": "specialist_action_ack",
                "status": "confirmed",
                "case_id": case_id,
                "action_type": action_type,
                "specialist_id": specialist_id,
                "timestamp": action_timestamp,
            }
        )

    except WebSocketDisconnect:
        logger.warning("ws.disconnected", case_id=case_id)
    except Exception as exc:
        logger.error("ws.error", case_id=case_id, error=str(exc))
        await websocket.close(code=1011)
    finally:
        logger.info("ws.closed", case_id=case_id)
