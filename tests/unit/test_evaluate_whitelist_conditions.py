import pytest
from src.tools.evaluate_whitelist_conditions import execute
import json

@pytest.mark.asyncio
async def test_evaluate_whitelist_conditions_success():
    params = {"dummy_param": "value"}
    params["projected_cost_usd"] = 5000
    params["total_length_of_stay_days"] = 3
        
    result = await execute(params)
    assert result["success"] is True
