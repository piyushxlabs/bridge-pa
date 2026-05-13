
import pytest
import httpx
from src.tools.check_audit_proxy_reachability import execute
import json

@pytest.mark.asyncio
async def test_check_audit_proxy_reachability_success(httpx_mock):
    # Load mock response
    with open("tests/mocks/mock_check_audit_proxy_reachability.json", "r") as f:
        mock_response = json.load(f)
        
    httpx_mock.add_response(json=mock_response)
    
    params = {"dummy_param": "value"}
    
    # For evaluate_whitelist_conditions specifically
    if "check_audit_proxy_reachability" == "evaluate_whitelist_conditions":
        params["projected_cost_usd"] = 5000
        params["total_length_of_stay_days"] = 3
        
    result = await execute(params)
    assert result["success"] is True
    
