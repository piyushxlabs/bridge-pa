"""
Unit test: criteria_evaluation_node

Patches create_react_agent (no live LLM call) AND patches write_phi_audit_log
at the phi_audit_decorator middleware level.
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
@patch("src.agents.criteria_evaluation.ChatGoogleGenerativeAI")
@patch("src.agents.criteria_evaluation.create_react_agent")
@patch(
    "src.middleware.phi_audit_decorator.write_phi_audit_log.execute",
    new_callable=AsyncMock,
)
async def test_criteria_evaluation_node(mock_audit, mock_create_agent, mock_llm_cls):
    """Node executes and returns messages without a live API key or proxy server."""
    mock_audit.return_value = {"success": True, "result": {"log_ref": "mocked"}}
    mock_create_agent.return_value = _make_fake_agent([
        HumanMessage(content="Please evaluate criteria for case TEST-CASE-001"),
        AIMessage(content="Whitelist evaluation complete. All conditions met."),
    ])
    mock_llm_cls.return_value = MagicMock()

    from src.agents.criteria_evaluation import criteria_evaluation_node

    state = {
        "user_intent": {"case_id": "TEST-CASE-001"},
        "session": {"session_id": "test_123"},
        "messages": [],
    }

    result = await criteria_evaluation_node(state)

    assert result is not None
    assert "messages" in result
    assert len(result["messages"]) > 0
    mock_create_agent.assert_called_once()
    mock_audit.assert_called()
