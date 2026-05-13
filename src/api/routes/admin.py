"""
src/api/routes/admin.py
Step 13 — Admin routes (role-authenticated)

POST /admin/emergency-stop  — UM Manager triggers system-wide or case-level halt
POST /admin/restart         — UM Manager releases a suspended workflow

Both endpoints require the X-Manager-Token header for role authentication.
The token value is validated against MANAGER_AUTH_TOKEN from environment —
never hardcoded, never logged.

Security note: Credentials are validated at the transport layer only.
No credential values reach LangGraph state or structured logs.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from src.graph.graph_builder import graph
from src.tools.trigger_emergency_stop import execute as trigger_emergency_stop_execute

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Role authentication dependency ─────────────────────────────────────────────
def require_manager_auth(x_manager_token: str = Header(...)) -> None:
    """
    Validates the X-Manager-Token header against the environment variable.
    Raises 403 on mismatch. Token value is never logged.
    """
    expected = os.environ.get("MANAGER_AUTH_TOKEN", "")
    if not expected or x_manager_token != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="UM Manager authentication required.",
        )


# ── Request / Response models ─────────────────────────────────────────────────
class EmergencyStopRequest(BaseModel):
    case_id: str = ""       # Empty string means system-wide scope
    scope: str = "case"     # case | system
    reason: str


class EmergencyStopResponse(BaseModel):
    status: str
    scope: str
    case_id: str
    timestamp: str


class RestartRequest(BaseModel):
    case_id: str
    reason: str


class RestartResponse(BaseModel):
    status: str
    case_id: str
    timestamp: str


# ── Routes ────────────────────────────────────────────────────────────────────
@router.post(
    "/emergency-stop",
    response_model=EmergencyStopResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_manager_auth)],
)
async def emergency_stop(body: EmergencyStopRequest) -> EmergencyStopResponse:
    """
    POST /admin/emergency-stop

    Triggers emergency stop for a specific case or system-wide.
    All active workflow processing is halted. Awaits explicit restart.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    params: Dict[str, Any] = {
        "scope": body.scope,
        "reason": body.reason,
        "case_id": body.case_id,
        "triggered_by": "um_manager",
        "timestamp": timestamp,
    }

    result = await trigger_emergency_stop_execute(params)

    if not result.get("success", False):
        logger.error(
            "admin.emergency_stop_tool_failed",
            case_id=body.case_id,
            scope=body.scope,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Emergency stop tool failed to execute.",
        )

    logger.warning(
        "admin.emergency_stop_triggered",
        case_id=body.case_id,
        scope=body.scope,
        # reason is NOT logged — may contain PHI-adjacent context
    )

    return EmergencyStopResponse(
        status="halted",
        scope=body.scope,
        case_id=body.case_id,
        timestamp=timestamp,
    )


@router.post(
    "/restart",
    response_model=RestartResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_manager_auth)],
)
async def restart_workflow(body: RestartRequest) -> RestartResponse:
    """
    POST /admin/restart

    Releases a suspended workflow by updating shared state active_mode
    from 'suspended' back to the appropriate active mode, allowing the
    LangGraph graph to resume from the checkpointed state.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    config: Dict[str, Any] = {"configurable": {"thread_id": body.case_id}}

    # Fetch current state to determine which mode to restore
    state_snapshot = await graph.aget_state(config)
    if not state_snapshot or not state_snapshot.values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No checkpoint found for case_id '{body.case_id}'.",
        )

    current_state = state_snapshot.values
    current_context = current_state.get("current_context", {})

    if current_context.get("active_mode") != "suspended":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Case '{body.case_id}' is not in suspended state.",
        )

    # Determine the prior mode from criteria evaluation
    whitelist_determination = current_state.get("criteria_evaluation", {}).get(
        "whitelist_determination", "mode_b"
    )

    await graph.aupdate_state(
        config,
        {
            "current_context": {
                **current_context,
                "active_mode": whitelist_determination,
            }
        },
    )

    logger.warning(
        "admin.workflow_restarted",
        case_id=body.case_id,
        restored_mode=whitelist_determination,
    )

    return RestartResponse(
        status="restarted",
        case_id=body.case_id,
        timestamp=timestamp,
    )
