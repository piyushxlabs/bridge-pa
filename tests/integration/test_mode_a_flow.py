"""
Integration test: Mode A end-to-end flow.

Verifies that when all 7 whitelist conditions are met, the graph routes
through mode_a_execution_node and reaches workflow_phase == "closed".

Agent nodes are mocked deterministically — this tests graph routing logic,
not LLM behavior.
"""
import pytest
from src.graph.state_schema import create_initial_state


@pytest.mark.asyncio
async def test_mode_a_end_to_end(memory_graph, mock_agents_mode_a):
    """
    Mode A path: all_whitelist_conditions_met=True → mode_a_execution → closed.
    """
    case_id = "TEST-CASE-MODE-A-001"
    initial_state = create_initial_state(
        case_id=case_id,
        specialist_id="SP-001",
        session_id="SES-001",
        intake_source_ref="INTAKE-001",
        intake_timestamp="2026-05-13T10:00:00Z",
    )

    config = {"configurable": {"thread_id": case_id}}

    # Run the graph end-to-end (no interrupt expected in Mode A)
    result = await memory_graph.ainvoke(initial_state, config=config)

    # ── Assertions ──────────────────────────────────────────────────────────
    assert result is not None, "Graph returned no result"

    # Mode A routing: whitelist must have been True
    criteria = result.get("criteria_evaluation", {})
    assert criteria.get("all_whitelist_conditions_met") is True, (
        f"Expected all_whitelist_conditions_met=True, got: {criteria}"
    )
    assert criteria.get("whitelist_determination") == "mode_a"

    # Final phase must be closed
    ctx = result.get("current_context", {})
    assert ctx.get("workflow_phase") == "closed", (
        f"Expected workflow_phase='closed', got: {ctx.get('workflow_phase')}"
    )

    # Extraction must be complete
    extraction = result.get("extraction_payload", {})
    assert extraction.get("extraction_completeness") is True
    assert len(extraction.get("missing_required_fields", ["x"])) == 0
