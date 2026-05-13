import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.middleware.manifest_validator import validate_endpoint
from src.middleware.vault_injection_adapter import inject_vault_credentials, get_injected_credentials, clear_credentials
from src.middleware.phi_audit_decorator import phi_audit_required
from src.utils.exceptions import WorkflowHaltedException

# ---------------------------------------------------------
# Test Manifest Validator
# ---------------------------------------------------------
def test_manifest_validator_approved():
    assert validate_endpoint("approved-portal-001", "v1.0.0") is True

@patch("src.middleware.manifest_validator.log_event")
def test_manifest_validator_unapproved(mock_log):
    assert validate_endpoint("unapproved-system", "v1.0.0") is False
    assert mock_log.called
    kwargs = mock_log.call_args.kwargs
    assert kwargs["event_type"] == "prohibited_action"

# ---------------------------------------------------------
# Test Vault Injection Adapter
# ---------------------------------------------------------
@pytest.mark.asyncio
@patch("src.middleware.vault_injection_adapter.httpx.AsyncClient.post")
async def test_vault_injection(mock_post):
    # Mock vault response
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"credentials": {"api_key": "secret123"}}
    mock_post.return_value = mock_response

    session_id = "SES-001"
    agent = "data_entry_agent"
    
    # Ensure clear state
    clear_credentials(session_id)
    
    success = await inject_vault_credentials(session_id, agent)
    assert success is True
    
    creds = get_injected_credentials(session_id)
    assert creds == {"api_key": "secret123"}
    
    clear_credentials(session_id)
    assert get_injected_credentials(session_id) is None

# ---------------------------------------------------------
# Test PHI Audit Decorator
# ---------------------------------------------------------
@pytest.mark.asyncio
@patch("src.tools.write_phi_audit_log.execute", new_callable=AsyncMock)
@patch("src.tools.trigger_emergency_stop.execute", new_callable=AsyncMock)
async def test_phi_audit_decorator_failure(mock_trigger_stop, mock_write_audit):
    # Mock audit log failure
    mock_write_audit.return_value = {"success": False}
    
    @phi_audit_required(["patient_dob"])
    async def dummy_node(state: dict):
        return {"status": "executed"}
        
    state = {"session": {"session_id": "test_session", "case_id": "test_case"}}
    
    with pytest.raises(WorkflowHaltedException):
        await dummy_node(state)
        
    assert mock_write_audit.called
    assert mock_trigger_stop.called
