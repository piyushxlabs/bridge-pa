import pytest
from src.agents.data_entry import data_entry_node, SYSTEM_PROMPT

from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
@patch("src.tools.write_phi_audit_log.execute", new_callable=AsyncMock)
async def test_data_entry_node(mock_audit):
    mock_audit.return_value = {"success": True, "result": {"log_ref": "mocked"}}
    state = {"session": {"session_id": "test_123", "case_id": "case_123"}, "messages": []}
    result = await data_entry_node(state)
    assert result.get("data_entry_node_executed") is True
    assert len(result.get("messages", [])) > 0
    assert SYSTEM_PROMPT in result["messages"][0].content
