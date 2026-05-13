"""
src/api/routes/workflow.py
Step 13 — GET /workflow/{case_id}/stream  (SSE)

Holds one asyncio.Queue per case_id open as a Server-Sent Events stream.
Events are yielded to the frontend in real time.
A keepalive comment is sent every 10 seconds if no event arrives.

The queue is created lazily on first subscriber and populated by the
SSE emitter (Step 14) called from agent node functions and tool executors.
"""

from __future__ import annotations

import asyncio
from typing import Any, AsyncGenerator, Dict

import structlog
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/workflow", tags=["workflow"])

# Module-level registry: case_id → asyncio.Queue
# Populated at session initiation; consumed by SSE stream endpoint.
_sse_queues: Dict[str, asyncio.Queue] = {}

KEEPALIVE_INTERVAL_SECONDS: int = 10


def get_or_create_queue(case_id: str) -> asyncio.Queue:
    """Return the SSE queue for a case, creating it if absent."""
    if case_id not in _sse_queues:
        _sse_queues[case_id] = asyncio.Queue()
    return _sse_queues[case_id]


def drop_queue(case_id: str) -> None:
    """Remove a closed case's queue from the registry."""
    _sse_queues.pop(case_id, None)


@router.get("/{case_id}/stream")
async def workflow_stream(case_id: str) -> EventSourceResponse:
    """
    GET /workflow/{case_id}/stream

    Returns a Server-Sent Events stream for the given case.
    Sends keepalive comments every 10 seconds to prevent proxy timeouts.
    """
    queue = get_or_create_queue(case_id)

    async def event_generator() -> AsyncGenerator[Dict[str, Any], None]:
        while True:
            try:
                event_data = await asyncio.wait_for(
                    queue.get(), timeout=KEEPALIVE_INTERVAL_SECONDS
                )
                # None sentinel signals stream end
                if event_data is None:
                    drop_queue(case_id)
                    return
                yield event_data
            except asyncio.TimeoutError:
                # Send keepalive comment to prevent proxy disconnect
                yield {"comment": "keepalive"}

    logger.info("sse.stream_opened", case_id=case_id)
    return EventSourceResponse(event_generator())
