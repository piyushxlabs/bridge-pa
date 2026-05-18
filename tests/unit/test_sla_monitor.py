"""
Unit test: sla_monitor_node

Patches create_react_agent so no live Gemini API call is made.
Validates that the node executes without error and returns a messages list.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from langchain_core.messages import HumanMessage, AIMessage


def _make_fake_agent(messages_out):
    fake_result = {"messages": messages_out}
    agent = MagicMock()
    agent.ainvoke = AsyncMock(return_value=fake_result)
    return agent


@pytest.mark.asyncio
@patch("src.agents.sla_monitor.ChatGoogleGenerativeAI")
@patch("src.agents.sla_monitor.create_react_agent")
async def test_sla_monitor_node(mock_create_agent, mock_llm_cls):
    """Node executes and returns messages without a live API key."""
    mock_create_agent.return_value = _make_fake_agent([
        HumanMessage(content="Please monitor SLA for case TEST-CASE-001"),
        AIMessage(content="Case registered. SLA monitoring active. No alerts triggered."),
    ])
    mock_llm_cls.return_value = MagicMock()

    from src.agents.sla_monitor import sla_monitor_node

    state = {
        "user_intent": {"case_id": "TEST-CASE-001"},
        "session": {"session_id": "test_123"},
        "messages": [],
    }

    result = await sla_monitor_node(state)

    assert result is not None
    assert "messages" in result
    assert len(result["messages"]) > 0
    mock_create_agent.assert_called_once()
