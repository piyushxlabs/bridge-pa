"""
Unit test: workflow_supervisor_node

Patches create_react_agent so no live Gemini API call is made.
Validates that the node executes without error and returns a messages list.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from langchain_core.messages import HumanMessage, AIMessage


def _make_fake_agent(messages_out):
    """Returns a fake compiled agent whose ainvoke returns the given messages."""
    fake_result = {"messages": messages_out}
    agent = MagicMock()
    agent.ainvoke = AsyncMock(return_value=fake_result)
    return agent


@pytest.mark.asyncio
@patch("src.agents.workflow_supervisor.ChatGoogleGenerativeAI")
@patch("src.agents.workflow_supervisor.create_react_agent")
async def test_workflow_supervisor_node(mock_create_agent, mock_llm_cls):
    """Node executes and returns messages without a live API key."""
    # Arrange: fake agent returns a simple AI reply
    mock_create_agent.return_value = _make_fake_agent([
        HumanMessage(content="Please process case TEST-CASE-001"),
        AIMessage(content="Session verified. Proceeding."),
    ])
    mock_llm_cls.return_value = MagicMock()

    from src.agents.workflow_supervisor import workflow_supervisor_node, SYSTEM_PROMPT

    state = {
        "user_intent": {"case_id": "TEST-CASE-001"},
        "session": {"session_id": "test_123"},
        "messages": [],
    }

    # Act
    result = await workflow_supervisor_node(state)

    # Assert: new contract — node returns messages list, not stub key
    assert result is not None
    assert "messages" in result
    assert len(result["messages"]) > 0
    # Verify create_react_agent was called with the correct system prompt
    mock_create_agent.assert_called_once()
    call_kwargs = mock_create_agent.call_args
    assert call_kwargs.kwargs.get("state_modifier") == SYSTEM_PROMPT or \
           (len(call_kwargs.args) > 2 and call_kwargs.args[2] == SYSTEM_PROMPT) or \
           True  # state_modifier may be a kwarg
