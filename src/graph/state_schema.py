import os
from typing import List, Optional, Literal, Union
from typing_extensions import TypedDict

# Module-level hardcoded integer constants (Immutable per specification)
BASELINE_COST_THRESHOLD_USD = 10000
BASELINE_LOS_THRESHOLD_DAYS = 5

class SessionState(TypedDict):
    session_id: str
    authorized_specialist_id: str
    specialist_verified: bool
    session_initiated_at: str
    session_authorization_log_ref: Optional[str]

class UserIntentState(TypedDict):
    case_id: str
    intake_source_ref: str
    case_type: Literal["concurrent_review"]
    requesting_specialist_id: str
    intake_timestamp: str

class TaskHistoryEntry(TypedDict):
    step: str
    agent: str
    action: str
    result: str
    timestamp: str
    audit_log_ref: Optional[str]

class ExtractionPayloadState(TypedDict):
    extracted_fields: dict
    source_document_ids: List[str]
    structural_complexity_flags: List[str]
    illegibility_flags: List[str]
    extraction_completeness: bool
    missing_required_fields: List[str]

class ThresholdResultsState(TypedDict):
    projected_cost_usd: float
    cost_threshold_met: bool
    length_of_stay_days: float
    los_threshold_met: bool
    acuity_flags: List[str]
    acuity_threshold_met: bool
    runtime_config_exceeds_baseline: bool

class CriteriaEvaluationState(TypedDict):
    payer_config_reachable: bool
    payer_config_query_timestamp: str
    interqual_criteria_set_matched: str
    criteria_match_type: Literal["exact", "partial", "ambiguous", "no_match"]
    threshold_results: ThresholdResultsState
    whitelist_determination: Literal["mode_a", "mode_b"]
    all_whitelist_conditions_met: bool
    escalation_reason_codes: List[str]

class SpecialistActionState(TypedDict):
    action_type: Literal["approved", "modified", "overridden", "null", None]
    action_timestamp: str
    rationale: str

class SLAState(TypedDict):
    case_registered_at: str
    elapsed_hours: float
    alert_48h_triggered: bool
    alert_60h_triggered: bool
    alert_66h_triggered: bool
    current_assigned_specialist_id: str
    queue: Literal["standard", "high_priority_any_available"]

class CurrentContextState(TypedDict):
    active_mode: Literal["mode_a", "mode_b", "suspended", "failed", "pending_session_auth"]
    workflow_phase: str
    awaiting_human_action: bool
    specialist_action: SpecialistActionState
    sla: SLAState

class ArtifactsState(TypedDict):
    portal_prepopulated_fields: dict
    mckesson_prepopulated_fields: dict
    authorization_submission_ref: str
    criteria_match_report: dict
    full_recommendation_package: dict
    submission_confirmation_ref: str

class ErrorLogEntry(TypedDict):
    error_id: str
    error_type: Literal["transient", "permanent", "emergency_stop"]
    case_id: str
    agent: str
    action_attempted: str
    condition_violated: str
    timestamp: str
    session_identity: str
    resolution_status: Literal["suspended_awaiting_human"]

class ConfigState(TypedDict):
    baseline_cost_threshold_usd: int
    baseline_los_threshold_days: int
    runtime_payer_config_ref: str
    approved_integration_manifest_version: str
    audit_proxy_endpoint: str

class PACaseState(TypedDict):
    session: SessionState
    user_intent: UserIntentState
    task_history: List[TaskHistoryEntry]
    extraction_payload: ExtractionPayloadState
    criteria_evaluation: CriteriaEvaluationState
    current_context: CurrentContextState
    artifacts: ArtifactsState
    error_logs: List[ErrorLogEntry]
    config: ConfigState

def create_initial_state(case_id: str, specialist_id: str, session_id: str, intake_source_ref: str, intake_timestamp: str) -> PACaseState:
    return {
        "session": {
            "session_id": session_id,
            "authorized_specialist_id": specialist_id,
            "specialist_verified": False,
            "session_initiated_at": intake_timestamp,
            "session_authorization_log_ref": None
        },
        "user_intent": {
            "case_id": case_id,
            "intake_source_ref": intake_source_ref,
            "case_type": "concurrent_review",
            "requesting_specialist_id": specialist_id,
            "intake_timestamp": intake_timestamp
        },
        "task_history": [],
        "extraction_payload": {
            "extracted_fields": {},
            "source_document_ids": [],
            "structural_complexity_flags": [],
            "illegibility_flags": [],
            "extraction_completeness": False,
            "missing_required_fields": []
        },
        "criteria_evaluation": {
            "payer_config_reachable": False,
            "payer_config_query_timestamp": "",
            "interqual_criteria_set_matched": "",
            "criteria_match_type": "no_match",
            "threshold_results": {
                "projected_cost_usd": 0.0,
                "cost_threshold_met": False,
                "length_of_stay_days": 0.0,
                "los_threshold_met": False,
                "acuity_flags": [],
                "acuity_threshold_met": False,
                "runtime_config_exceeds_baseline": False
            },
            "whitelist_determination": "mode_b",
            "all_whitelist_conditions_met": False,
            "escalation_reason_codes": []
        },
        "current_context": {
            "active_mode": "pending_session_auth",
            "workflow_phase": "initialization",
            "awaiting_human_action": False,
            "specialist_action": {
                "action_type": None,
                "action_timestamp": "",
                "rationale": ""
            },
            "sla": {
                "case_registered_at": "",
                "elapsed_hours": 0.0,
                "alert_48h_triggered": False,
                "alert_60h_triggered": False,
                "alert_66h_triggered": False,
                "current_assigned_specialist_id": specialist_id,
                "queue": "standard"
            }
        },
        "artifacts": {
            "portal_prepopulated_fields": {},
            "mckesson_prepopulated_fields": {},
            "authorization_submission_ref": "",
            "criteria_match_report": {},
            "full_recommendation_package": {},
            "submission_confirmation_ref": ""
        },
        "error_logs": [],
        "config": {
            "baseline_cost_threshold_usd": BASELINE_COST_THRESHOLD_USD,
            "baseline_los_threshold_days": BASELINE_LOS_THRESHOLD_DAYS,
            "runtime_payer_config_ref": "",
            "approved_integration_manifest_version": os.environ.get("APPROVED_INTEGRATION_MANIFEST_VERSION", ""),
            "audit_proxy_endpoint": os.environ.get("VEEA_LOBSTER_TRAP_API_ENDPOINT", "")
        }
    }
