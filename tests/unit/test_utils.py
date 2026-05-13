import pytest
import asyncio
import httpx
from unittest.mock import patch, MagicMock, AsyncMock
from google.api_core.exceptions import ServiceUnavailable

from src.utils.retry import with_retry
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.exceptions import WorkflowHaltedException
from src.utils.logger import filter_sensitive_data, log_event

# ---------------------------------------------------------
# Test @with_retry
# ---------------------------------------------------------
@pytest.mark.asyncio
async def test_with_retry_http_503():
    # Mock an httpx 503 response
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_error = httpx.HTTPStatusError("503 Service Unavailable", request=MagicMock(), response=mock_response)

    call_count = 0

    @with_retry(max_attempts=3, backoff_seconds=[0.01, 0.01, 0.01])  # fast backoff for test
    async def mock_api_call():
        nonlocal call_count
        call_count += 1
        raise mock_error

    with pytest.raises(httpx.HTTPStatusError):
        await mock_api_call()
        
    assert call_count == 3

@pytest.mark.asyncio
async def test_with_retry_halts_on_workflow_halted():
    call_count = 0

    @with_retry(max_attempts=3, backoff_seconds=[0.01, 0.01, 0.01])
    async def mock_api_call():
        nonlocal call_count
        call_count += 1
        raise WorkflowHaltedException("Permanent failure")

    with pytest.raises(WorkflowHaltedException):
        await mock_api_call()
        
    assert call_count == 1  # Should not retry

# ---------------------------------------------------------
# Test CircuitBreaker
# ---------------------------------------------------------
def test_circuit_breaker():
    cb = CircuitBreaker(time_window_seconds=300, threshold=3)
    
    # 1 stop
    cb.record_emergency_stop("case_1")
    assert cb.is_circuit_open() is False
    
    # 2 stops (different cases)
    cb.record_emergency_stop("case_2")
    assert cb.is_circuit_open() is False
    
    # Same case ID should not trigger threshold
    cb.record_emergency_stop("case_2")
    assert cb.is_circuit_open() is False
    
    # 3 stops (different cases) -> Circuit OPEN
    cb.record_emergency_stop("case_3")
    assert cb.is_circuit_open() is True

# ---------------------------------------------------------
# Test Logger filtering
# ---------------------------------------------------------
def test_filter_sensitive_data():
    # Test credential filtering
    text_with_token = 'Request failed. token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"'
    safe_text = filter_sensitive_data(text_with_token)
    assert "token: [REDACTED]" in safe_text
    assert "eyJ" not in safe_text

    text_with_bearer = 'Auth error Bearer xyz123ABC'
    safe_text = filter_sensitive_data(text_with_bearer)
    assert "Bearer: [REDACTED]" in safe_text
    assert "xyz123ABC" not in safe_text

    # Test PHI SSN filtering
    text_with_ssn = "Patient SSN is 123-45-6789"
    safe_text = filter_sensitive_data(text_with_ssn)
    assert "[PHI_REDACTED]" in safe_text
    assert "123-45-6789" not in safe_text

    # Test Email filtering
    text_with_email = "User john.doe@example.com logged in"
    safe_text = filter_sensitive_data(text_with_email)
    assert "[PHI_REDACTED]" in safe_text
    assert "john.doe@example.com" not in safe_text

def test_log_event_filtering():
    with patch("src.utils.logger.logger.info") as mock_logger_info:
        log_event(
            case_id="case_123",
            session_id="session_456",
            agent="test_agent",
            event_type="test_event",
            description='Attempted login with password "secret123"'
        )
        
        # Verify the logger was called
        assert mock_logger_info.called
        
        # Extract kwargs passed to logger
        call_kwargs = mock_logger_info.call_args.kwargs
        
        # Verify credentials filtered
        assert "password: [REDACTED]" in call_kwargs["description"]
        assert "secret123" not in call_kwargs["description"]
