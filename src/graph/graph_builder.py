"""
src/graph/graph_builder.py
Step 11 — Wire LangGraph State Graph

Constructs the deterministic DAG for Bridge-PA:
  START → session_auth → proxy_check → credential_injection
        → document_processing → criteria_evaluation → mode_routing
        → [mode_a_execution | mode_b_handoff] → END

Mode B is gated by an interrupt_before on mode_b_specialist_action_node
so that graph execution suspends until the Workflow Supervisor confirms
a specialist action, releasing it via graph.update_state().
"""

from __future__ import annotations

from typing import Any, Dict, Literal

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from src.graph.state_schema import PACaseState
from src.graph.checkpointer import get_checkpointer
from src.utils.exceptions import WorkflowHaltedException

# ─── Agent node imports ────────────────────────────────────────────────────────
from src.agents.workflow_supervisor import workflow_supervisor_node
from src.agents.document_processing import document_processing_node
from src.agents.criteria_evaluation import criteria_evaluation_node
from src.agents.data_entry import data_entry_node
from src.agents.sla_monitor import sla_monitor_node

# ──────────────────────────────────────────────────────────────────────────────
# Node name constants — single source of truth for all edge wiring
# ──────────────────────────────────────────────────────────────────────────────
NODE_SESSION_AUTH = "session_auth_node"
NODE_PROXY_CHECK = "proxy_check_node"
NODE_CREDENTIAL_INJECTION = "credential_injection_node"
NODE_DOCUMENT_PROCESSING = "document_processing_node"
NODE_CRITERIA_EVALUATION = "criteria_evaluation_node"
NODE_MODE_ROUTING = "mode_routing_node"
NODE_MODE_A_EXECUTION = "mode_a_execution_node"
NODE_MODE_B_HANDOFF = "mode_b_handoff_node"
NODE_MODE_B_SPECIALIST_ACTION = "mode_b_specialist_action_node"  # interrupt_before gate
NODE_CASE_CLOSURE = "case_closure_node"


# ──────────────────────────────────────────────────────────────────────────────
# Emergency-stop guard
# Applied at each node entry. Raises WorkflowHaltedException if the
# workflow has been suspended by a prior emergency stop trigger.
# ──────────────────────────────────────────────────────────────────────────────
def _guard_suspended(state: Dict[str, Any]) -> None:
    """Raise WorkflowHaltedException if the graph is in suspended state."""
    active_mode = state.get("current_context", {}).get("active_mode", "")
    if active_mode == "suspended":
        raise WorkflowHaltedException(
            "Workflow is in SUSPENDED state. Awaiting human restart authorization."
        )


# ──────────────────────────────────────────────────────────────────────────────
# Thin wrapper nodes (delegation to supervisor / specialist action stub)
# The Workflow Supervisor orchestrates Steps 1-3; individual wrappers allow
# the DAG to express each step as a named node for observability.
# ──────────────────────────────────────────────────────────────────────────────
async def session_auth_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Step 1 — Verify UM Specialist session authorization."""
    _guard_suspended(state)
    result = await workflow_supervisor_node(state)
    return {**result, "current_context": {**state.get("current_context", {}), "workflow_phase": "session_auth"}}


async def proxy_check_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Step 2 — Confirm Veea Lobster Trap audit proxy is reachable."""
    _guard_suspended(state)
    result = await workflow_supervisor_node(state)
    return {**result, "current_context": {**state.get("current_context", {}), "workflow_phase": "proxy_check"}}


async def credential_injection_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Step 3 — Initiate credential injection from Enterprise Secret Vault."""
    _guard_suspended(state)
    result = await workflow_supervisor_node(state)
    return {**result, "current_context": {**state.get("current_context", {}), "workflow_phase": "credential_injection"}}


async def mode_routing_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Step 6 — Read whitelist determination, write routing audit log, register SLA."""
    _guard_suspended(state)
    result = await workflow_supervisor_node(state)
    return {**result, "current_context": {**state.get("current_context", {}), "workflow_phase": "mode_routing"}}


async def mode_a_execution_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Step 7A — Delegate to Data Entry Agent for autonomous Mode A execution."""
    _guard_suspended(state)
    result = await data_entry_node(state)
    return {**result, "current_context": {**state.get("current_context", {}), "workflow_phase": "mode_a_execution"}}


async def mode_b_handoff_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Step 7B (first half) — Assemble recommendation package and notify specialist."""
    _guard_suspended(state)
    result = await workflow_supervisor_node(state)
    awaiting_ctx = {**state.get("current_context", {}), "awaiting_human_action": True, "workflow_phase": "mode_b_handoff"}
    return {**result, "current_context": awaiting_ctx}


async def mode_b_specialist_action_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 7B (interrupt gate) — Suspends graph execution.
    LangGraph interrupt_before pauses here; graph.update_state() releases it
    when the Workflow Supervisor confirms a logged specialist action.
    The specialist action payload is written into state by the WebSocket handler
    before calling graph.update_state(), so this node simply acknowledges.
    """
    _guard_suspended(state)
    # This node is never invoked autonomously — it is released only by
    # graph.update_state() carrying the confirmed specialist_action.
    result = await workflow_supervisor_node(state)
    return {**result, "current_context": {**state.get("current_context", {}), "awaiting_human_action": False, "workflow_phase": "mode_b_specialist_confirmed"}}


async def case_closure_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Step 8 — Confirm complete audit log and close case."""
    _guard_suspended(state)
    result = await workflow_supervisor_node(state)
    return {**result, "current_context": {**state.get("current_context", {}), "workflow_phase": "closed"}}


# ──────────────────────────────────────────────────────────────────────────────
# Routing function — deterministic binary Mode A / Mode B gate
# Reads all_whitelist_conditions_met from shared state written by
# the Criteria Evaluation Agent. Never guesses — strict boolean only.
# ──────────────────────────────────────────────────────────────────────────────
def route_by_mode(state: Dict[str, Any]) -> Literal["mode_a_execution_node", "mode_b_handoff_node"]:
    """
    Strict binary routing gate.
    all_whitelist_conditions_met = True  → mode_a_execution_node
    any condition False                  → mode_b_handoff_node
    """
    all_met: bool = state.get("criteria_evaluation", {}).get("all_whitelist_conditions_met", False)
    if all_met:
        return NODE_MODE_A_EXECUTION
    return NODE_MODE_B_HANDOFF


# ──────────────────────────────────────────────────────────────────────────────
# Graph builder
# ──────────────────────────────────────────────────────────────────────────────
def _build_graph(checkpointer: Any | None) -> Any:
    """
    Assembles and compiles the LangGraph StateGraph for Bridge-PA.

    Args:
        checkpointer: An AsyncPostgresSaver instance (production) or
                      MemorySaver (unit tests). Injected to keep this
                      function synchronous and testable.

    Returns:
        A compiled CompiledGraph object with interrupt_before set on the
        Mode B specialist action gate node.
    """
    builder: StateGraph = StateGraph(PACaseState)

    # ── Register nodes ────────────────────────────────────────────────────────
    builder.add_node(NODE_SESSION_AUTH, session_auth_node)
    builder.add_node(NODE_PROXY_CHECK, proxy_check_node)
    builder.add_node(NODE_CREDENTIAL_INJECTION, credential_injection_node)
    builder.add_node(NODE_DOCUMENT_PROCESSING, document_processing_node)
    builder.add_node(NODE_CRITERIA_EVALUATION, criteria_evaluation_node)
    builder.add_node(NODE_MODE_ROUTING, mode_routing_node)
    builder.add_node(NODE_MODE_A_EXECUTION, mode_a_execution_node)
    builder.add_node(NODE_MODE_B_HANDOFF, mode_b_handoff_node)
    builder.add_node(NODE_MODE_B_SPECIALIST_ACTION, mode_b_specialist_action_node)
    builder.add_node(NODE_CASE_CLOSURE, case_closure_node)

    # ── Sequential edges (directed acyclic — no back-edges) ──────────────────
    builder.add_edge(START, NODE_SESSION_AUTH)
    builder.add_edge(NODE_SESSION_AUTH, NODE_PROXY_CHECK)
    builder.add_edge(NODE_PROXY_CHECK, NODE_CREDENTIAL_INJECTION)
    builder.add_edge(NODE_CREDENTIAL_INJECTION, NODE_DOCUMENT_PROCESSING)
    builder.add_edge(NODE_DOCUMENT_PROCESSING, NODE_CRITERIA_EVALUATION)
    builder.add_edge(NODE_CRITERIA_EVALUATION, NODE_MODE_ROUTING)

    # ── Conditional edge: Mode A or Mode B routing ───────────────────────────
    builder.add_conditional_edges(
        NODE_MODE_ROUTING,
        route_by_mode,
        {
            NODE_MODE_A_EXECUTION: NODE_MODE_A_EXECUTION,
            NODE_MODE_B_HANDOFF: NODE_MODE_B_HANDOFF,
        }
    )

    # ── Mode A path ──────────────────────────────────────────────────────────
    builder.add_edge(NODE_MODE_A_EXECUTION, NODE_CASE_CLOSURE)

    # ── Mode B path: handoff → interrupt gate → closure ──────────────────────
    builder.add_edge(NODE_MODE_B_HANDOFF, NODE_MODE_B_SPECIALIST_ACTION)
    builder.add_edge(NODE_MODE_B_SPECIALIST_ACTION, NODE_CASE_CLOSURE)

    # ── Terminal edge ────────────────────────────────────────────────────────
    builder.add_edge(NODE_CASE_CLOSURE, END)

    # ── Compile with interrupt gate and checkpointer ─────────────────────────
    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=[NODE_MODE_B_SPECIALIST_ACTION],
    )


# ──────────────────────────────────────────────────────────────────────────────
# Module-level graph (production) — uses in-memory saver as default
# so imports never raise during test collection (no DB required at import time).
# Call `initialize_graph()` on server startup to swap in the PG checkpointer.
# ──────────────────────────────────────────────────────────────────────────────
graph = _build_graph(checkpointer=MemorySaver())


async def initialize_graph() -> None:
    """
    Replaces the module-level graph with one backed by the AsyncPostgresSaver.
    Call this from FastAPI's startup event handler (Step 13).
    """
    global graph
    pg_checkpointer = await get_checkpointer()
    graph = _build_graph(checkpointer=pg_checkpointer)


def get_memory_graph() -> Any:
    """
    Returns a fresh in-memory graph for unit / integration tests.
    Uses MemorySaver so tests never need a live PostgreSQL connection.
    """
    return _build_graph(checkpointer=MemorySaver())
