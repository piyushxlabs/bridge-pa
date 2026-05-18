// frontend/src/types/events.ts
// Step 15 — SSE Event Type Definitions
// Mirrors src/api/events.py on the backend

export type StepStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'suspended';
export type AlertLevel = 'standard' | 'critical' | 'code_red';
export type WorkflowMode = 'mode_a' | 'mode_b' | 'suspended' | null;
export type SpecialistActionType = 'approved' | 'modified' | 'overridden';

export interface BaseEvent {
  event: string;
  data: {
    case_id: string;
    timestamp: string;
    [key: string]: unknown;
  };
}

export interface StepStatusEvent extends BaseEvent {
  event: 'step_status';
  data: {
    case_id: string;
    timestamp: string;
    step_number: number;
    step_name: string;
    status: StepStatus;
    agent: string;
    error?: string;
  };
}

export interface WhitelistConditionsEvent extends BaseEvent {
  event: 'whitelist_conditions';
  data: {
    case_id: string;
    timestamp: string;
    all_conditions_met: boolean;
    condition_results: Record<string, boolean>;
    escalation_reason_codes: string[];
  };
}

export interface RoutingDecisionEvent extends BaseEvent {
  event: 'routing_decision';
  data: {
    case_id: string;
    timestamp: string;
    mode: string;
    whitelist_determination: string;
  };
}

export interface ModeBPackageEvent extends BaseEvent {
  event: 'mode_b_package';
  data: {
    case_id: string;
    timestamp: string;
    recommendation_package: Record<string, unknown>;
    escalation_reason_codes: string[];
  };
}

export interface EmergencyStopEvent extends BaseEvent {
  event: 'emergency_stop';
  data: {
    case_id: string;
    timestamp: string;
    reason: string;
    scope: string;
  };
}

export interface SLAAlertEvent extends BaseEvent {
  event: 'sla_alert';
  data: {
    case_id: string;
    timestamp: string;
    alert_level: AlertLevel;
    elapsed_hours: number;
  };
}

export interface ActivityLogEntryEvent extends BaseEvent {
  event: 'activity_log_entry';
  data: {
    case_id: string;
    timestamp: string;
    category: string;
    message: string;
    agent: string;
  };
}

export type SSEEvent =
  | StepStatusEvent
  | WhitelistConditionsEvent
  | RoutingDecisionEvent
  | ModeBPackageEvent
  | EmergencyStopEvent
  | SLAAlertEvent
  | ActivityLogEntryEvent
  | BaseEvent;

// Workflow step definitions — the 8 fixed pipeline steps
export interface WorkflowStep {
  number: number;
  label: string;
  description: string;
  status: StepStatus;
  agent: string;
  timestamp?: string;
  error?: string;
  expanded: boolean;
}

export const INITIAL_WORKFLOW_STEPS: WorkflowStep[] = [
  { number: 1, label: 'Session & System Verification', description: 'Verifying UM Specialist session identity, audit logging system, and secure credential delivery.', status: 'pending', agent: 'workflow_supervisor', expanded: false },
  { number: 2, label: 'Session Authorized', description: 'Session credentials verified and workflow initialized.', status: 'pending', agent: 'workflow_supervisor', expanded: false },
  { number: 3, label: 'Infrastructure Ready', description: 'Audit proxy reachable. Vault credentials delivered.', status: 'pending', agent: 'workflow_supervisor', expanded: false },
  { number: 4, label: 'Document Retrieval & Field Extraction', description: 'Retrieving fax document, applying OCR, and extracting required fields.', status: 'pending', agent: 'document_processing', expanded: false },
  { number: 5, label: 'Criteria Evaluation & Routing Determination', description: 'Querying payer configuration, applying Interqual matching, and evaluating all seven whitelist conditions.', status: 'pending', agent: 'criteria_evaluation', expanded: false },
  { number: 6, label: 'Routing Logged & SLA Monitoring Initiated', description: 'Logging routing decision to audit record and registering case with SLA monitor.', status: 'pending', agent: 'workflow_supervisor', expanded: false },
  { number: 7, label: 'Autonomous Data Entry & Authorization Submission', description: 'Authenticating to portal and McKesson, populating fields, validating parity, and submitting.', status: 'pending', agent: 'data_entry', expanded: false },
  { number: 8, label: 'Case Closure', description: 'Confirming submission, completing audit log, and deregistering from SLA monitor.', status: 'pending', agent: 'workflow_supervisor', expanded: false },
];
