
import pytest
import httpx
from src.tools.prepopulate_portal_fields import execute
import json

@pytest.mark.asyncio
async def test_prepopulate_portal_fields_success(httpx_mock):
    # Load mock response
    with open("tests/mocks/mock_prepopulate_portal_fields.json", "r") as f:
        mock_response = json.load(f)
        
    httpx_mock.add_response(json=mock_response)
    
    params = {"dummy_param": "value"}
    
    # For evaluate_whitelist_conditions specifically
    if "prepopulate_portal_fields" == "evaluate_whitelist_conditions":
        params["projected_cost_usd"] = 5000
        params["total_length_of_stay_days"] = 3
        
    result = await execute(params)
    assert result["success"] is True
    

@pytest.mark.asyncio
async def test_prepopulate_portal_fields_clinical_rejection(httpx_mock):
    params = {"fields": {"medical_necessity_determination": "true"}}
    result = await execute(params)
    assert result["success"] is False
    assert result["result"]["prohibited_field_rejected"] is True
