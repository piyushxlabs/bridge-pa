"""
src/api/events.py
Step 13 — SSE Event Dataclasses

Defines all 11 event types streamed to the frontend via Server-Sent Events.
Each dataclass maps to a named SSE `event:` field so the frontend useSSEStream
hook can dispatch on event type deterministically.

Event types:
  1  step_status            — workflow step started/completed/failed
  2  phi_audit_confirmed    — PHI field audit log write confirmed
  3  extraction_complete    — document extraction payload written to state
  4  whitelist_conditions   — all 7 whitelist condition results
  5  routing_decision       — mode_a or mode_b assigned
  6  mode_a_fields_written  — portal + McKesson fields pre-populated (Mode A)
  7  submission_confirmed   — authorization submitted successfully
  8  case_closed            — case closed; audit log complete
  9  mode_b_package         — Full Recommendation Package ready (Mode B)
  10 specialist_action_ack  — specialist action received and logged
  11 emergency_stop         — emergency stop triggered
  12 sla_alert              — SLA threshold alert fired (48h/60h/66h)
  13 activity_log_entry     — generic activity log line (all agents)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StepStatusEvent:
    event: str = "step_status"
    case_id: str = ""
    step_number: int = 0
    step_name: str = ""
    status: str = ""          # started | completed | failed
    agent: str = ""
    timestamp: str = ""


@dataclass
class PhiAuditConfirmedEvent:
    event: str = "phi_audit_confirmed"
    case_id: str = ""
    phi_field_name: str = ""
    action_type: str = ""     # extract | evaluate | write | read
    log_ref: str = ""
    agent: str = ""
    timestamp: str = ""


@dataclass
class ExtractionCompleteEvent:
    event: str = "extraction_complete"
    case_id: str = ""
    extraction_completeness: bool = False
    missing_required_fields: List[str] = field(default_factory=list)
    structural_complexity_flags: List[str] = field(default_factory=list)
    illegibility_flags: List[str] = field(default_factory=list)
    timestamp: str = ""


@dataclass
class WhitelistConditionsEvent:
    event: str = "whitelist_conditions"
    case_id: str = ""
    all_conditions_met: bool = False
    condition_results: Dict[str, bool] = field(default_factory=dict)
    escalation_reason_codes: List[str] = field(default_factory=list)
    timestamp: str = ""


@dataclass
class RoutingDecisionEvent:
    event: str = "routing_decision"
    case_id: str = ""
    mode: str = ""            # mode_a | mode_b
    whitelist_determination: str = ""
    timestamp: str = ""


@dataclass
class ModeAFieldsWrittenEvent:
    event: str = "mode_a_fields_written"
    case_id: str = ""
    portal_fields_count: int = 0
    mckesson_fields_count: int = 0
    parity_confirmed: bool = False
    timestamp: str = ""


@dataclass
class SubmissionConfirmedEvent:
    event: str = "submission_confirmed"
    case_id: str = ""
    submission_ref: str = ""
    mode: str = ""
    timestamp: str = ""


@dataclass
class CaseClosedEvent:
    event: str = "case_closed"
    case_id: str = ""
    audit_log_complete: bool = False
    timestamp: str = ""


@dataclass
class ModeBPackageEvent:
    event: str = "mode_b_package"
    case_id: str = ""
    recommendation_package: Dict[str, Any] = field(default_factory=dict)
    escalation_reason_codes: List[str] = field(default_factory=list)
    timestamp: str = ""


@dataclass
class SpecialistActionAckEvent:
    event: str = "specialist_action_ack"
    case_id: str = ""
    action_type: str = ""     # approved | modified | overridden
    specialist_id: str = ""
    timestamp: str = ""


@dataclass
class EmergencyStopEvent:
    event: str = "emergency_stop"
    case_id: str = ""
    reason: str = ""
    scope: str = ""           # case | system
    timestamp: str = ""


@dataclass
class SLAAlertEvent:
    event: str = "sla_alert"
    case_id: str = ""
    alert_level: str = ""     # standard | critical | code_red
    elapsed_hours: float = 0.0
    timestamp: str = ""


@dataclass
class ActivityLogEntryEvent:
    event: str = "activity_log_entry"
    case_id: str = ""
    category: str = ""        # session | audit | extraction | evaluation | data_entry | sla | admin
    message: str = ""
    agent: str = ""
    timestamp: str = ""
