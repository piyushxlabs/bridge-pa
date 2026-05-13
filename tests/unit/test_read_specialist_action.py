
import pytest
import httpx
from src.tools.read_specialist_action import execute
import json

@pytest.mark.asyncio
async def test_read_specialist_action_success(httpx_mock):
    # Load mock response
    with open("tests/mocks/mock_read_specialist_action.json", "r") as f:
        mock_response = json.load(f)
        
    httpx_mock.add_response(json=mock_response)
    
    params = {"dummy_param": "value"}
    
    # For evaluate_whitelist_conditions specifically
    if "read_specialist_action" == "evaluate_whitelist_conditions":
        params["projected_cost_usd"] = 5000
        params["total_length_of_stay_days"] = 3
        
    result = await execute(params)
    assert result["success"] is True
    
