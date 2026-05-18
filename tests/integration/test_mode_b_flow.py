"""
Integration test: Mode B end-to-end flow.

Verifies two things:
  1. When not all whitelist conditions are met, the graph routes to
     mode_b_handoff_node and HALTS at mode_b_specialist_action_node
     (interrupt_before gate) with awaiting_human_action=True.
  2. After a specialist action payload is injected via graph.update_state(),
     the graph resumes and reaches workflow_phase == "closed".

Agent nodes are mocked deterministically — this tests graph routing logic,
not LLM behavior.
"""
import pytest
from src.graph.state_schema import create_initial_state


@pytest.mark.asyncio
async def test_mode_b_halts_at_specialist_gate(memory_graph, mock_agents_mode_b):
    """
    Mode B path: all_whitelist_conditions_met=False → mode_b_handoff →
    interrupt at mode_b_specialist_action_node (awaiting_human_action=True).
    """
    case_id = "TEST-CASE-MODE-B-001"
    initial_state = create_initial_state(
        case_id=case_id,
        specialist_id="SP-001",
        session_id="SES-001",
        intake_source_ref="INTAKE-001",
        intake_timestamp="2026-05-13T10:00:00Z",
    )

    config = {"configurable": {"thread_id": case_id}}

    # First invoke: graph should halt BEFORE mode_b_specialist_action_node
    result = await memory_graph.ainvoke(initial_state, config=config)

    # ── Assertions: graph halted at Mode B gate ──────────────────────────────
    assert result is not None, "Graph returned no result"

    criteria = result.get("criteria_evaluation", {})
    assert criteria.get("all_whitelist_conditions_met") is False, (
        f"Expected all_whitelist_conditions_met=False, got: {criteria}"
    )
    assert criteria.get("whitelist_determination") == "mode_b"

    # Phase must be mode_b_handoff (interrupt fired before specialist node)
    ctx = result.get("current_context", {})
    assert ctx.get("workflow_phase") == "mode_b_handoff", (
        f"Expected workflow_phase='mode_b_handoff', got: {ctx.get('workflow_phase')}"
    )
    assert ctx.get("awaiting_human_action") is True, (
        "Expected awaiting_human_action=True after Mode B handoff"
    )


@pytest.mark.asyncio
async def test_mode_b_resumes_after_specialist_action(memory_graph, mock_agents_mode_b):
    """
    Mode B path resumed: after injecting specialist_action via update_state,
    the graph continues from mode_b_specialist_action_node → case_closure → closed.
    """
    case_id = "TEST-CASE-MODE-B-RESUME-001"
    initial_state = create_initial_state(
        case_id=case_id,
        specialist_id="SP-001",
        session_id="SES-001",
        intake_source_ref="INTAKE-001",
        intake_timestamp="2026-05-13T10:00:00Z",
    )

    config = {"configurable": {"thread_id": case_id}}

    # Step 1: First invoke — graph halts at interrupt gate
    await memory_graph.ainvoke(initial_state, config=config)

    # Step 2: Inject specialist action (simulates WebSocket handler call)
    specialist_action_update = {
        "current_context": {
            "active_mode": "mode_b",
            "workflow_phase": "mode_b_handoff",
            "awaiting_human_action": False,
            "specialist_action": {
                "action_type": "approved",
                "action_timestamp": "2026-05-13T12:00:00Z",
                "rationale": "Criteria review confirms medical necessity.",
            },
            "sla": {
                "case_registered_at": "2026-05-13T10:00:00Z",
                "elapsed_hours": 2.0,
                "alert_48h_triggered": False,
                "alert_60h_triggered": False,
                "alert_66h_triggered": False,
                "current_assigned_specialist_id": "SP-001",
                "queue": "standard",
            }
        }
    }
    await memory_graph.aupdate_state(config, specialist_action_update, as_node="mode_b_specialist_action_node")

    # Step 3: Resume — graph should now run to completion
    result = await memory_graph.ainvoke(None, config=config)

    # ── Assertions: graph reached closed ────────────────────────────────────
    assert result is not None, "Graph returned no result after resume"

    ctx = result.get("current_context", {})
    assert ctx.get("workflow_phase") == "closed", (
        f"Expected workflow_phase='closed' after resume, got: {ctx.get('workflow_phase')}"
    )
    assert ctx.get("awaiting_human_action") is False
