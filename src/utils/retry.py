import asyncio
import functools
import httpx
from google.api_core.exceptions import ServiceUnavailable
from src.utils.exceptions import WorkflowHaltedException

def with_retry(max_attempts=3, backoff_seconds=[2, 4, 8]):
    """
    Async decorator that retries on specific transient errors.
    Does NOT retry on WorkflowHaltedException or HTTP 400, 401, 403.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            attempts = 1
            while True:
                try:
                    return await func(*args, **kwargs)
                except httpx.HTTPStatusError as e:
                    status = e.response.status_code
                    if status in (429, 503):
                        if attempts >= max_attempts:
                            raise
                        await asyncio.sleep(backoff_seconds[attempts - 1])
                        attempts += 1
                    else:
                        raise
                except (httpx.TimeoutException, ServiceUnavailable) as e:
                    if attempts >= max_attempts:
                        raise
                    await asyncio.sleep(backoff_seconds[attempts - 1])
                    attempts += 1
                except WorkflowHaltedException:
                    raise
        return wrapper
    return decorator

from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception, before_sleep_log
import logging
from google.api_core.exceptions import ResourceExhausted

logger = logging.getLogger("agent_retry")

def is_resource_exhausted(exception: BaseException) -> bool:
    """Return True if the exception is ResourceExhausted or contains a 429 status code."""
    if isinstance(exception, ResourceExhausted):
        return True
    if "429" in str(exception) or "ResourceExhausted" in str(exception) or "quota" in str(exception).lower():
        return True
    return False

@retry(
    retry=retry_if_exception(is_resource_exhausted),
    wait=wait_exponential(multiplier=2, min=20, max=60), # Wait at least 20s, up to 60s
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
async def invoke_agent_with_retry(agent, messages):
    """
    Robust wrapper for ReAct agent invocations.
    Catches 429 ResourceExhausted errors and forcefully waits 20+ seconds 
    before retrying to ensure the 15 RPM limits are respected without crashing.
    """
    return await agent.ainvoke({"messages": messages})
