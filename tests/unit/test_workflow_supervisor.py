import pytest
from src.agents.workflow_supervisor import workflow_supervisor_node, SYSTEM_PROMPT

@pytest.mark.asyncio
async def test_workflow_supervisor_node():
    state = {"session": {"session_id": "test_123", "case_id": "case_123"}, "messages": []}
    result = await workflow_supervisor_node(state)
    assert result.get("workflow_supervisor_node_executed") is True
    assert len(result.get("messages", [])) > 0
    assert SYSTEM_PROMPT in result["messages"][0].content
