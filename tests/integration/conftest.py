"""
Integration test conftest.py for Bridge-PA.

Strategy:
- Agent nodes (which invoke live Gemini) are patched with AsyncMock to return
  deterministic state updates. This tests GRAPH ROUTING LOGIC, not LLM behavior.
- Tool HTTP calls are intercepted by pytest-httpx so no external services needed.
- GEMINI_API_KEY is loaded from .env for other potential uses, but the agent nodes
  themselves are mocked so no live LLM calls are made during integration tests.
"""
import pytest
import json
import httpx
from pathlib import Path
from unittest.mock import AsyncMock, patch
from dotenv import load_dotenv

load_dotenv()

from src.graph.graph_builder import get_memory_graph

# ──────────────────────────────────────────────────────────────────────────────
# HTTP-level mock for all tool endpoints (ports 8080 / external services)
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_all_tool_http(httpx_mock):
    """
    Intercepts every outbound HTTP call made by a tool's execute() function.
    Returns the corresponding mock JSON file from tests/mocks/, or a generic
    success response if no specific mock file exists.

    assert_all_requests_were_expected=False: because mocked agent nodes do not
    make HTTP calls, so the registered callback may never be invoked.
    """
    def custom_response(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        endpoint = url.rstrip("/").split("/")[-1]

        # Named overrides for specific scenarios
        if endpoint == "evaluate_whitelist_conditions":
            mock_path = Path("tests/mocks/mock_whitelist_all_pass_mode_a.json")
        elif endpoint == "extract_structured_fields":
            mock_path = Path("tests/mocks/mock_extract_fields_complete.json")
        else:
            mock_path = Path(f"tests/mocks/mock_{endpoint}.json")

        if mock_path.exists():
            with open(mock_path, "r") as f:
                data = json.load(f)
            return httpx.Response(status_code=200, json=data)

        # Generic fallback: success=True for any unknown endpoint
        return httpx.Response(
            status_code=200,
            json={"success": True, "result": {"mocked": True, "endpoint": endpoint}}
        )

    httpx_mock.add_callback(custom_response, is_reusable=True)


# ──────────────────────────────────────────────────────────────────────────────
# Agent-node patch factories
# These functions produce the deterministic state-update dicts that the
# graph would receive if the ReAct agent ran successfully.
# ──────────────────────────────────────────────────────────────────────────────

def _make_supervisor_return(state, phase: str) -> dict:
    """Generic supervisor node return — merges phase into current_context."""
    return {
        **state,
        "current_context": {
            **state.get("current_context", {}),
            "workflow_phase": phase,
            "active_mode": "mode_a",
        },
        "session": {
            **state.get("session", {}),
            "specialist_verified": True,
            "session_authorization_log_ref": "mock-log-ref-001",
        },
    }


async def _mock_workflow_supervisor_node(state):
    return _make_supervisor_return(state, state.get("current_context", {}).get("workflow_phase", "supervisor"))


async def _mock_document_processing_node(state):
    return {
        **state,
        "extraction_payload": {
            "extracted_fields": {
                "patient_name": "John Doe",
                "dob": "1980-01-01",
                "member_id": "MEM123456789",
                "diagnosis_code": "E11.9",
            },
            "source_document_ids": ["DOC-001"],
            "structural_complexity_flags": [],
            "illegibility_flags": [],
            "extraction_completeness": True,
            "missing_required_fields": [],
        },
    }


def _make_criteria_evaluation_return(all_conditions_met: bool) -> dict:
    return {
        "payer_config_reachable": True,
        "payer_config_query_timestamp": "2026-05-13T10:00:00Z",
        "interqual_criteria_set_matched": "IQ-2024-MED-001",
        "criteria_match_type": "exact",
        "threshold_results": {
            "projected_cost_usd": 8500.0,
            "cost_threshold_met": False,
            "length_of_stay_days": 3.0,
            "los_threshold_met": False,
            "acuity_flags": [],
            "acuity_threshold_met": False,
            "runtime_config_exceeds_baseline": False,
        },
        "whitelist_determination": "mode_a" if all_conditions_met else "mode_b",
        "all_whitelist_conditions_met": all_conditions_met,
        "escalation_reason_codes": [] if all_conditions_met else ["C3"],
    }


async def _mock_data_entry_node(state):
    return {
        **state,
        "artifacts": {
            **state.get("artifacts", {}),
            "authorization_submission_ref": "AUTH-SUBMIT-MOCK-001",
            "submission_confirmation_ref": "CONFIRM-MOCK-001",
        },
    }


async def _mock_sla_monitor_node(state):
    return {
        **state,
        "current_context": {
            **state.get("current_context", {}),
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


# ──────────────────────────────────────────────────────────────────────────────
# Graph fixture
# NOTE: memory_graph is called WITHOUT mock fixtures in conftest — the mock
# fixtures (mock_agents_mode_a / mode_b) set monkeypatch attrs BEFORE the
# test function body runs, but we need the graph to be built AFTER patching.
# Solution: each test requests memory_graph, mock_agents_mode_a in that order.
# Since mock fixtures use monkeypatch (function scope), they run first.
# memory_graph then builds the graph calling get_memory_graph() which calls
# _build_graph() which calls the already-patched module-level wrappers.
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def memory_graph():
    """Returns a freshly compiled in-memory graph. Always call AFTER mock_agents_* fixtures."""
    from src.graph.graph_builder import get_memory_graph  # re-import after patching
    return get_memory_graph()


@pytest.fixture
def mock_agents_mode_a(monkeypatch):
    """
    Patches all agent node functions as they are referenced inside graph_builder.py,
    then rebuilds the graph so compiled node refs point to mocked functions.
    Simulates Mode A: all_whitelist_conditions_met=True.
    """
    import src.graph.graph_builder as gb

    monkeypatch.setattr(gb, "workflow_supervisor_node", _mock_workflow_supervisor_node)
    monkeypatch.setattr(gb, "document_processing_node", _mock_document_processing_node)
    monkeypatch.setattr(gb, "sla_monitor_node", _mock_sla_monitor_node)
    monkeypatch.setattr(gb, "data_entry_node", _mock_data_entry_node)

    async def _mock_criteria_mode_a(state):
        return {
            **state,
            "criteria_evaluation": _make_criteria_evaluation_return(all_conditions_met=True),
        }

    monkeypatch.setattr(gb, "criteria_evaluation_node", _mock_criteria_mode_a)


@pytest.fixture
def mock_agents_mode_b(monkeypatch):
    """
    Patches all agent node functions as they are referenced inside graph_builder.py,
    then rebuilds the graph so compiled node refs point to mocked functions.
    Simulates Mode B: all_whitelist_conditions_met=False.
    """
    import src.graph.graph_builder as gb

    monkeypatch.setattr(gb, "workflow_supervisor_node", _mock_workflow_supervisor_node)
    monkeypatch.setattr(gb, "document_processing_node", _mock_document_processing_node)
    monkeypatch.setattr(gb, "sla_monitor_node", _mock_sla_monitor_node)
    monkeypatch.setattr(gb, "data_entry_node", _mock_data_entry_node)

    async def _mock_criteria_mode_b(state):
        return {
            **state,
            "criteria_evaluation": _make_criteria_evaluation_return(all_conditions_met=False),
        }

    monkeypatch.setattr(gb, "criteria_evaluation_node", _mock_criteria_mode_b)
