
import pytest
import httpx
from src.tools.validate_field_parity import execute
import json

@pytest.mark.asyncio
async def test_validate_field_parity_success(httpx_mock):
    # Load mock response
    with open("tests/mocks/mock_validate_field_parity.json", "r") as f:
        mock_response = json.load(f)
        
    httpx_mock.add_response(json=mock_response)
    
    params = {"dummy_param": "value"}
    
    # For evaluate_whitelist_conditions specifically
    if "validate_field_parity" == "evaluate_whitelist_conditions":
        params["projected_cost_usd"] = 5000
        params["total_length_of_stay_days"] = 3
        
    result = await execute(params)
    assert result["success"] is True
    
