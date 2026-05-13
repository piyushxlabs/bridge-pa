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
