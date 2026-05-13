"""
src/api/routes/session.py
Step 13 — POST /session/initiate

Validates the session initiation payload, builds the initial PACaseState,
invokes the LangGraph graph asynchronously, and returns the session handle
with the SSE stream URL.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.graph.graph_builder import graph
from src.graph.state_schema import create_initial_state
from src.sla.sla_monitor_thread import sla_monitor_manager

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/session", tags=["session"])


class SessionInitiateRequest(BaseModel):
    case_id: str
    specialist_id: str
    session_token: str
    case_type: str = "concurrent_review"
    intake_source_ref: str = "secure_fax_intake"


class SessionInitiateResponse(BaseModel):
    case_id: str
    session_handle: str
    stream_url: str
    status: str = "initiated"


@router.post(
    "/initiate",
    response_model=SessionInitiateResponse,
    status_code=status.HTTP_200_OK,
)
async def initiate_session(body: SessionInitiateRequest) -> SessionInitiateResponse:
    """
    POST /session/initiate

    Validates payload, creates initial PACaseState, invokes the LangGraph
    graph in a background task, and returns the SSE stream URL.
    """
    if body.case_type != "concurrent_review":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Out-of-scope case type: '{body.case_type}'. Only 'concurrent_review' is supported.",
        )

    intake_timestamp = datetime.now(timezone.utc).isoformat()
    import time as _time
    intake_epoch = _time.time()

    initial_state = create_initial_state(
        case_id=body.case_id,
        specialist_id=body.specialist_id,
        session_id=f"session_{body.case_id}",
        intake_source_ref=body.intake_source_ref,
        intake_timestamp=intake_timestamp,
    )

    config: Dict[str, Any] = {
        "configurable": {"thread_id": body.case_id}
    }

    # Register case with SLA monitor BEFORE graph starts
    await sla_monitor_manager.register_case(
        case_id=body.case_id,
        intake_timestamp=intake_epoch,
        assigned_specialist_id=body.specialist_id,
    )

    # Invoke graph asynchronously in background — does not block the HTTP response
    asyncio.create_task(
        _run_graph(initial_state=initial_state, config=config, case_id=body.case_id)
    )

    logger.info("session.initiated", case_id=body.case_id, specialist_id=body.specialist_id)

    return SessionInitiateResponse(
        case_id=body.case_id,
        session_handle=f"session_{body.case_id}",
        stream_url=f"/workflow/{body.case_id}/stream",
    )


async def _run_graph(
    initial_state: Dict[str, Any],
    config: Dict[str, Any],
    case_id: str,
) -> None:
    """Background task: invoke the LangGraph graph for the given case."""
    try:
        await graph.ainvoke(initial_state, config=config)
        logger.info("graph.completed", case_id=case_id)
    except Exception as exc:
        logger.error("graph.error", case_id=case_id, error=str(exc))
