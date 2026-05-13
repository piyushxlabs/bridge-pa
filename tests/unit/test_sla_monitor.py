import pytest
from src.agents.sla_monitor import sla_monitor_node, SYSTEM_PROMPT

@pytest.mark.asyncio
async def test_sla_monitor_node():
    state = {"session": {"session_id": "test_123", "case_id": "case_123"}, "messages": []}
    result = await sla_monitor_node(state)
    assert result.get("sla_monitor_node_executed") is True
    assert len(result.get("messages", [])) > 0
    assert SYSTEM_PROMPT in result["messages"][0].content
