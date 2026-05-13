# AGENT ORCHESTRATION BLUEPRINT

**Generated:** May 11, 2026
**Source:** AGENT_BEHAVIOR_PROFILE.md
**Status:** AUTHORITATIVE — Defines complete agent system architecture
**Purpose:** Cognitive architecture and orchestration specification

---

## **1. SYSTEM OVERVIEW**

**High-Level Description:**
This is a five-agent, supervisor-coordinated orchestration system that executes a strictly deterministic, state-machine-driven workflow for Prior Authorization (Concurrent Review) processing within commercial healthcare payer operations. A central Workflow Supervisor agent governs all execution sequencing and binary mode routing (autonomous vs. escalation), delegating to four specialist agents responsible for document ingestion, clinical criteria evaluation, portal/system data entry, and continuous SLA monitoring. All PHI interactions, routing decisions, and audit events are externalized to a compliance proxy — no PHI persists within agent memory.

**Architectural Classification:**
Multi-Agent System

**Justification:**
The behavioral profile defines four cognitively distinct responsibilities — multimodal document parsing, deterministic Interqual criteria matching, portal/system data entry, and continuous SLA clock monitoring — each of which requires different model capabilities (vision, rule-matching, structured output, time-based alerting) and different execution lifecycles (sequential per-case steps vs. persistent concurrent monitoring). A single agent cannot simultaneously execute deterministic sequential case processing and maintain an independent, always-on SLA monitoring loop without role confusion and architectural brittleness incompatible with the Zero Error risk tolerance. The supervisor pattern enforces the strict whitelist routing logic as a structural control point that no specialist agent can bypass.

**Complexity Level:**
Complex — HIPAA-regulated, zero-error-tolerance, multi-modal, multi-system integration with concurrent monitoring, binary mode routing with explicit human-in-the-loop gates, and a strict audit trail requirement covering every PHI interaction.

---

## **2. AGENT TOPOLOGY**

**Number of Agents:** 5

---

### **Agent 1: Workflow Supervisor**
- **Responsibility:** Orchestrates the end-to-end case lifecycle. Enforces session authorization verification before any workflow begins. Receives structured extraction output from the Document Processing Agent, passes it to the Criteria Evaluation Agent, receives the evaluation result, executes the binary Mode A / Mode B routing decision, delegates to the Data Entry Agent (Mode A) or Human Handoff Coordinator (Mode B), and triggers the SLA Monitor Agent for every routed case. Enforces all emergency stop and failure halt conditions.
- **Cognitive Scope:** Session authorization verification; binary Mode A / Mode B routing logic; whitelist condition aggregation; emergency stop detection; failure event logging; case lifecycle state transitions; human escalation initiation; override and restart authorization gating.
- **Execution Authority:** May read shared case state; may invoke all specialist agents; may write case lifecycle status; may trigger SLA alerts; may place cases in suspended state; may not execute any portal or system write action directly.
- **Communication With:** Document Processing Agent, Criteria Evaluation Agent, Data Entry Agent, SLA Monitor Agent, Human Handoff interface.

---

### **Agent 2: Document Processing Agent**
- **Responsibility:** Ingests multimodal fax document packages from the designated secure intake source only. Applies OCR and vision parsing to extract all structured clinical and administrative data fields — including PHI — from typed physician notes, handwritten annotations, nursing flowsheets, and medication lists. Returns a structured extraction payload to the Workflow Supervisor. Flags any illegible, missing, or ambiguous content as structural complexity flags within the payload — it does not infer or approximate.
- **Cognitive Scope:** Multimodal document parsing; field-level structured data extraction; illegibility and completeness detection; structural complexity flag identification; source document provenance tracking.
- **Execution Authority:** May read from the designated secure intake source only; may produce structured extraction payloads; may not access any portal, system, or credential store; may not make clinical judgments about extracted content.
- **Communication With:** Workflow Supervisor (receives task, returns structured extraction payload).

---

### **Agent 3: Criteria Evaluation Agent**
- **Responsibility:** Receives the structured extraction payload from the Workflow Supervisor. Queries the Payer Master Configuration Table at runtime to retrieve payer-specific thresholds, routing rules, and carve-out logic. Applies Interqual criteria matching in literal read-only evaluation mode against the extracted data. Evaluates all seven whitelist conditions simultaneously. Returns a binary whitelist determination (all conditions met = Mode A eligible; any condition unmet = Mode B mandatory), the specific Interqual criteria set matched, all threshold evaluation results, and the specific escalation reason code(s) for any unmet conditions. Does not generate competing recommendations or interpretations.
- **Cognitive Scope:** Runtime Payer Master Configuration Table query and ingestion; literal Interqual criteria set identification and matching; threshold evaluation against dollar, acuity, and duration baselines; whitelist condition checklist evaluation; escalation reason code assignment.
- **Execution Authority:** May query the Payer Master Configuration Table in read-only mode; may read extracted case data; may produce criteria evaluation reports and whitelist determinations; may not modify any case record, portal field, or configuration value; may not make clinical necessity determinations.
- **Communication With:** Workflow Supervisor (receives extraction payload, returns evaluation result and whitelist determination).

---

### **Agent 4: Data Entry Agent**
- **Responsibility:** Executes all portal and McKesson data entry actions. For Mode A cases: pre-populates all non-clinical fields in the payer portal and McKesson, then submits the completed authorization request. For Mode B cases: pre-populates all non-clinical portal and McKesson fields only, then halts — no submission. Accepts dynamically injected credentials from the Enterprise Secret Vault at runtime (never stores, caches, or logs them). After specialist approval in Mode B, re-activates to update pre-populated fields to match specialist determination. Logs all PHI field interactions through the Veea Lobster Trap audit proxy.
- **Cognitive Scope:** Structured field-to-target-field mapping; portal and McKesson API/RPA interaction; credential injection consumption; Mode A submission sequencing; Mode B pre-population-only enforcement; post-approval field update execution.
- **Execution Authority:** May write non-clinical fields in payer portals and McKesson only; may submit completed authorization requests for Mode A cases only; may not write clinical necessity fields; may not modify existing records; may not store credentials beyond the active session; may not take any portal action without a confirmed active session authorization from a verified UM Specialist.
- **Communication With:** Workflow Supervisor (receives task and mode assignment); Enterprise Secret Vault (receives injected credentials); Veea Lobster Trap audit proxy (writes all PHI interaction logs).

---

### **Agent 5: SLA Monitor Agent**
- **Responsibility:** Operates as a persistent, continuously running monitor for every open case — including post-escalation cases. Tracks elapsed time from case intake for every active case ID. Triggers tiered SLA alerts at defined thresholds: Standard Alert at 48 hours (to assigned UM Specialist dashboard), Critical Alert at 60 hours (to assigned UM Specialist + CC to UM Department Manager), and Code Red re-routing at 66 hours (re-routes to High Priority / Any Available Specialist queue — no submission). Monitors independently of case processing status. Does not submit authorizations under any condition.
- **Cognitive Scope:** Multi-case elapsed time tracking; threshold comparison; alert routing and delivery; High Priority queue re-routing at Code Red; SLA breach detection for CMS 72-hour compliance.
- **Execution Authority:** May read case status and elapsed time from shared state; may trigger alert notifications to defined recipient lists; may re-route case assignment at Code Red threshold; may not submit authorizations; may not modify case clinical data; may not override human escalation status.
- **Communication With:** Workflow Supervisor (receives case registration and status updates); UM Specialist dashboard; UM Department Manager notification channel; High Priority queue assignment system.

---

**Control Hierarchy:**
- **Pattern:** Supervisor with Independent Monitor
- **Control Flow:** The Workflow Supervisor is the single control point for all sequential case processing steps. It invokes specialist agents in a strict sequential order (Document Processing → Criteria Evaluation → Data Entry) and cannot be bypassed. The SLA Monitor Agent runs as a parallel, independent monitor registered by the Supervisor at case intake; it operates continuously and does not receive instructions from specialist agents. All routing decisions — Mode A, Mode B, emergency stop, failure halt — are made exclusively by the Workflow Supervisor.
- **Coordination Mechanism:** Shared state object (LangGraph state graph); message passing from Supervisor to specialist agents via graph edges; SLA Monitor reads from shared state independently; all agents write to the shared state only through defined state mutation functions; the Veea Lobster Trap audit proxy is called directly by any agent that touches PHI — the Supervisor does not intermediate audit writes.

---

## **2.1 SHARED STATE SCHEMA**

**Global State Object Structure:**

```json
{
  "session": {
    "session_id": "string",
    "authorized_specialist_id": "string",
    "specialist_verified": "boolean",
    "session_initiated_at": "ISO8601_timestamp",
    "session_authorization_log_ref": "string"
  },
  "user_intent": {
    "case_id": "string",
    "intake_source_ref": "string",
    "case_type": "concurrent_review",
    "requesting_specialist_id": "string",
    "intake_timestamp": "ISO8601_timestamp"
  },
  "task_history": [
    {
      "step": "string",
      "agent": "string",
      "action": "string",
      "result": "string",
      "timestamp": "ISO8601_timestamp",
      "audit_log_ref": "string"
    }
  ],
  "extraction_payload": {
    "extracted_fields": "object",
    "source_document_ids": ["string"],
    "structural_complexity_flags": ["string"],
    "illegibility_flags": ["string"],
    "extraction_completeness": "boolean",
    "missing_required_fields": ["string"]
  },
  "criteria_evaluation": {
    "payer_config_reachable": "boolean",
    "payer_config_query_timestamp": "ISO8601_timestamp",
    "interqual_criteria_set_matched": "string",
    "criteria_match_type": "exact | partial | ambiguous | no_match",
    "threshold_results": {
      "projected_cost_usd": "number",
      "cost_threshold_met": "boolean",
      "length_of_stay_days": "number",
      "los_threshold_met": "boolean",
      "acuity_flags": ["string"],
      "acuity_threshold_met": "boolean",
      "runtime_config_exceeds_baseline": "boolean"
    },
    "whitelist_determination": "mode_a | mode_b",
    "all_whitelist_conditions_met": "boolean",
    "escalation_reason_codes": ["string"]
  },
  "current_context": {
    "active_mode": "mode_a | mode_b | suspended | failed | pending_session_auth",
    "workflow_phase": "string",
    "awaiting_human_action": "boolean",
    "specialist_action": {
      "action_type": "approved | modified | overridden | null",
      "action_timestamp": "ISO8601_timestamp",
      "rationale": "string"
    },
    "sla": {
      "case_registered_at": "ISO8601_timestamp",
      "elapsed_hours": "number",
      "alert_48h_triggered": "boolean",
      "alert_60h_triggered": "boolean",
      "alert_66h_triggered": "boolean",
      "current_assigned_specialist_id": "string",
      "queue": "standard | high_priority_any_available"
    }
  },
  "artifacts": {
    "portal_prepopulated_fields": "object",
    "mckesson_prepopulated_fields": "object",
    "authorization_submission_ref": "string",
    "criteria_match_report": "object",
    "full_recommendation_package": "object",
    "submission_confirmation_ref": "string"
  },
  "error_logs": [
    {
      "error_id": "string",
      "error_type": "transient | permanent | emergency_stop",
      "case_id": "string",
      "agent": "string",
      "action_attempted": "string",
      "condition_violated": "string",
      "timestamp": "ISO8601_timestamp",
      "session_identity": "string",
      "resolution_status": "suspended_awaiting_human"
    }
  ],
  "config": {
    "baseline_cost_threshold_usd": 10000,
    "baseline_los_threshold_days": 5,
    "runtime_payer_config_ref": "string",
    "approved_integration_manifest_version": "string",
    "audit_proxy_endpoint": "string"
  }
}
```

---

## **3. EXECUTION FLOW**

**Entry Point:**
Explicit human session initiation by a named, verified UM Specialist. The UM Specialist authenticates and explicitly initiates a case processing session. The Workflow Supervisor validates the session authorization before any workflow step begins. No execution occurs without a verified, logged session identity.

**Flow Type:**
Graph-based with a strictly deterministic node sequence; no exploratory branching; two terminal routing paths (Mode A: autonomous execution; Mode B: human handoff). One persistent parallel loop (SLA Monitor).

---

**Detailed Execution Steps:**

1. **Session Authorization Verification**
   - **Agent Responsible:** Workflow Supervisor
   - **Action:** Receives session initiation event. Verifies named UM Specialist identity against authorized personnel registry. Logs session authorization event (specialist ID, timestamp, session ID) to Veea Lobster Trap audit proxy. Writes verified session metadata to shared state (`session` object).
   - **Decision Point:** Specialist identity verified AND logged → proceed to Step 2. Identity unverified OR audit log write fails → EMERGENCY STOP. No case processing begins without a confirmed session authorization log entry.
   - **Next Step:** Step 2 (if verified); Emergency Stop Protocol (if not verified or log fails).

2. **PHI Audit Proxy Reachability Check**
   - **Agent Responsible:** Workflow Supervisor
   - **Action:** Pings Veea Lobster Trap audit proxy. Confirms it is reachable and accepting writes. Logs reachability confirmation.
   - **Decision Point:** Proxy reachable and accepting writes → proceed to Step 3. Proxy unreachable or returns logging failure → EMERGENCY STOP. No PHI may be processed without confirmed logging capability.
   - **Next Step:** Step 3 (if reachable); Emergency Stop Protocol (if unreachable).

3. **Credential Injection**
   - **Agent Responsible:** Workflow Supervisor (initiates); Data Entry Agent (receives credentials for later use)
   - **Action:** Workflow Supervisor requests runtime credential injection from Enterprise Secret Vault for the active session. Credentials are injected directly into the Data Entry Agent's active session context only. Credentials are never written to shared state, logged, cached, or persisted by any agent.
   - **Decision Point:** Secret Vault reachable and credential injection succeeds → proceed to Step 4. Secret Vault unreachable or injection fails → EMERGENCY STOP.
   - **Next Step:** Step 4 (if injection succeeds); Emergency Stop Protocol (if fails).

4. **Document Ingestion and Parsing**
   - **Agent Responsible:** Document Processing Agent (supervised by Workflow Supervisor)
   - **Action:** Workflow Supervisor delegates to Document Processing Agent with case ID and designated intake source reference. Document Processing Agent retrieves fax document package from designated secure intake source only. Applies OCR and vision parsing to all document pages (typed notes, handwritten annotations, nursing flowsheets, medication lists). Extracts all structured clinical and administrative data fields. Identifies and flags all illegible content, missing required fields, and structural complexity signals. Returns structured extraction payload to Workflow Supervisor. All PHI accessed during extraction is logged to Veea Lobster Trap (field, action type, document ID, agent identity, timestamp).
   - **Decision Point:** Extraction complete with all required fields present and no parsing errors → continue to Step 5. Structural complexity flags detected OR missing required fields OR illegibility flags → set `extraction_completeness = false`, populate `structural_complexity_flags`; Workflow Supervisor will evaluate in Step 5 but Mode B is guaranteed.
   - **Next Step:** Step 5.

5. **Payer Master Configuration Table Query**
   - **Agent Responsible:** Criteria Evaluation Agent (supervised by Workflow Supervisor)
   - **Action:** Workflow Supervisor delegates to Criteria Evaluation Agent. Criteria Evaluation Agent queries the Payer Master Configuration Table at runtime. Retrieves payer-specific thresholds, routing rules, and contractual carve-out logic. Records query timestamp and reachability status in shared state.
   - **Decision Point:** Table reachable and returns unambiguous result → proceed to Step 6. Table unreachable, offline, returns null, or returns ambiguous result → set `payer_config_reachable = false`; Mode B is guaranteed; proceed to Step 6 (whitelist evaluation will enforce Mode B).
   - **Next Step:** Step 6.

6. **Whitelist Evaluation and Mode Determination**
   - **Agent Responsible:** Criteria Evaluation Agent (supervised by Workflow Supervisor)
   - **Action:** Criteria Evaluation Agent applies Interqual criteria matching in literal read-only mode against the extraction payload. Evaluates all seven whitelist conditions simultaneously and independently:
     (a) Criteria match is exact and unambiguous with zero missing required fields
     (b) No structural complexity flags present
     (c) Projected episode cost does not exceed $10,000 baseline (runtime config may only lower this, never raise it)
     (d) Case does not involve ICU/Critical Care, Inpatient Surgery, SUD, Behavioral Health, or experimental/non-formulary treatment
     (e) Total Length of Stay (including requested extension) does not exceed 5 days
     (f) Payer Master Configuration Table was reachable and returned unambiguous result
     (g) No runtime configuration threshold exceeds any baseline maximum
     Returns binary whitelist determination, matched criteria set, all threshold results, and specific escalation reason code(s) for any unmet condition. Writes evaluation results to shared state (`criteria_evaluation` object).
   - **Decision Point:** ALL seven conditions simultaneously true → `whitelist_determination = mode_a`. ANY single condition false → `whitelist_determination = mode_b`. Determination is binary; no partial or approximate Mode A classification is possible.
   - **Next Step:** Step 7.

7. **Mode Routing**
   - **Agent Responsible:** Workflow Supervisor
   - **Action:** Reads `whitelist_determination` from shared state. Logs routing decision (case ID, mode assigned, all whitelist condition results, timestamp, session identity) to Veea Lobster Trap audit proxy. Registers case with SLA Monitor Agent (passes case ID, intake timestamp). Delegates to the appropriate next step based on mode.
   - **Decision Point:** `mode_a` → Step 8a. `mode_b` → Step 8b.
   - **Next Step:** Step 8a or Step 8b.

8a. **Mode A — Autonomous Data Entry and Submission**
   - **Agent Responsible:** Data Entry Agent (supervised by Workflow Supervisor)
   - **Action:** Data Entry Agent authenticates to payer portal (e.g., Humana AuthPoint) and McKesson using runtime-injected credentials. Pre-populates all non-clinical data fields in the payer portal and McKesson from the structured extraction payload. Validates field-level parity between portal and McKesson entries (zero mismatch tolerance). Submits the completed authorization request to the payer portal. Logs every field write, portal authentication event, and submission action to Veea Lobster Trap (field name, value written, target system, session ID, specialist identity, timestamp). No human approval is requested at any step.
   - **Decision Point:** All fields populated, portal-McKesson parity confirmed, submission accepted → proceed to Step 9a. Any field mismatch, submission rejection, or parity failure → Permanent Failure Protocol (halt, log, suspend).
   - **Next Step:** Step 9a (success); Permanent Failure Protocol (failure).

8b. **Mode B — Pre-Population and Human Handoff**
   - **Agent Responsible:** Data Entry Agent (pre-population); Workflow Supervisor (handoff orchestration)
   - **Action:** Data Entry Agent pre-populates all non-clinical data fields in the payer portal and McKesson. Halts — does not submit. Criteria Evaluation Agent generates a structured clinical summary and a single specific criteria-based recommendation with explicit escalation reason code(s). Workflow Supervisor assembles the Full Recommendation Package (structured clinical summary, pre-populated field confirmation, criteria match report, escalation reason codes) and routes it to the assigned UM Specialist's dashboard. Workflow Supervisor sets `awaiting_human_action = true` in shared state.
   - **Decision Point:** Package delivered to assigned specialist and acknowledged by dashboard → proceed to Step 9b (await specialist action). Dashboard delivery fails → Permanent Failure Protocol.
   - **Next Step:** Step 9b.

9a. **Mode A — Audit Log Completion and Case Closure**
   - **Agent Responsible:** Workflow Supervisor; Data Entry Agent
   - **Action:** Workflow Supervisor confirms submission confirmation reference is written to artifacts. Data Entry Agent confirms complete field-level audit log has been written with no gaps. Workflow Supervisor writes case closure event (case ID, mode, submission ref, audit completeness confirmation, timestamp) to Veea Lobster Trap. Sets case status to closed. Notifies SLA Monitor Agent that case is closed (removes from active monitoring set).
   - **Decision Point:** Audit log confirmed complete with no gaps → case closed. Audit log gap detected → Permanent Failure Protocol (gap in PHI audit trail is a defined failure condition).
   - **Next Step:** Termination (success).

9b. **Mode B — Specialist Review and Action**
   - **Agent Responsible:** Workflow Supervisor (monitors and enforces); SLA Monitor Agent (active)
   - **Action:** Workflow Supervisor holds case in `awaiting_human_action = true` state. SLA Monitor Agent actively monitors elapsed time, triggering alerts at 48h, 60h, and 66h thresholds. Workflow Supervisor waits for an explicit, logged specialist action (approved / modified with rationale / overridden with rationale). Passive non-response is not accepted as approval.
   - **Decision Point:** Specialist takes explicit action → Step 10b. 66h Code Red reached → SLA Monitor re-routes to High Priority / Any Available Specialist queue; case remains in `awaiting_human_action = true` — Workflow Supervisor does not submit. Workflow Supervisor halt command received → Emergency Stop Protocol.
   - **Next Step:** Step 10b (on specialist action).

10b. **Mode B — Post-Specialist Action Execution**
    - **Agent Responsible:** Workflow Supervisor; Data Entry Agent
    - **Action:** Workflow Supervisor logs specialist action (action type, rationale, timestamp, specialist identity) to Veea Lobster Trap. If specialist approved: Data Entry Agent submits pre-populated fields as-is. If specialist modified: Data Entry Agent updates portal and McKesson fields to reflect specialist's determination, then submits. If specialist overridden: Data Entry Agent updates pre-populated fields to reflect override determination; logs override event; does not resubmit, dispute, or flag for review. In all cases: confirms portal-McKesson field parity. Logs all field writes to Veea Lobster Trap.
    - **Decision Point:** All writes confirmed, parity confirmed, audit log complete → proceed to Step 11b. Any mismatch or audit gap → Permanent Failure Protocol.
    - **Next Step:** Step 11b.

11b. **Mode B — Audit Log Completion and Case Closure**
    - **Agent Responsible:** Workflow Supervisor
    - **Action:** Workflow Supervisor confirms complete field-level audit log with no gaps. Writes case closure event to Veea Lobster Trap. Sets case status to closed. Notifies SLA Monitor Agent that case is closed.
    - **Decision Point:** Audit log confirmed complete → case closed. Gap detected → Permanent Failure Protocol.
    - **Next Step:** Termination (success).

---

**Decision Points:**

- **At Step 1:** Session identity verified AND log write confirmed → continue. Either fails → Emergency Stop.
- **At Step 2:** Audit proxy reachable → continue. Unreachable or log failure → Emergency Stop.
- **At Step 3:** Secret Vault reachable and injection succeeds → continue. Fails → Emergency Stop.
- **At Step 4:** Structural complexity flags or missing fields detected → Mode B guaranteed; continue to Step 5.
- **At Step 5:** Config table unreachable or ambiguous → Mode B guaranteed; continue to Step 6.
- **At Step 6:** ALL seven whitelist conditions met → Mode A. ANY one unmet → Mode B. Binary only.
- **At Step 7:** Mode A → 8a. Mode B → 8b.
- **At Step 8a:** Portal-McKesson parity confirmed + submission accepted → 9a. Mismatch or failure → Permanent Failure Protocol.
- **At Step 9b:** Specialist acts → 10b. Code Red reached → SLA re-routes (no submission). Stop command → Emergency Stop Protocol.
- **At Steps 9a, 11b:** Audit log complete → case closed. Gap detected → Permanent Failure Protocol.

**Termination Conditions:**
- **Success:** Case closed with confirmed authorization submission (Mode A or Mode B post-approval) AND complete field-level audit log with zero gaps AND portal-McKesson parity confirmed at 0% mismatch.
- **Failure:** Any condition listed in Section 8 of the behavioral profile is met; case placed in suspended state; all workflow halted pending human instruction.
- **Timeout:** No session-level timeout on case processing; SLA Monitor enforces CMS 72-hour clock with tiered alerts; Code Red at 66 hours re-routes human assignment without agent submission.
- **User Interrupt:** Explicit stop command from human operator or UM Manager triggers Emergency Stop Protocol immediately at any step.

**Loop Prevention:**
- The workflow is a directed acyclic graph per case (no cycles in sequential steps).
- The SLA Monitor Agent's alert loop is bounded by case closure notification from the Workflow Supervisor; once closed, the case is removed from the monitoring set.
- Post-approval re-entry in Mode B (Step 10b) is a one-time re-activation, not a loop; the agent does not resubmit after a specialist override.
- Emergency stop after failure requires explicit human restart authorization — no automatic retry is permitted; self-recovery is architecturally blocked.

---

## **4. ORCHESTRATION FRAMEWORK CHOICE**

**Selected Framework:** LangGraph

**Justification:**
The behavioral profile mandates a fixed, deterministic workflow sequence (ingest → extract → whitelist evaluate → route → execute → log) with explicit binary branching (Mode A vs. Mode B), multiple defined emergency stop conditions that must halt all processing immediately, a persistent parallel monitoring loop (SLA Monitor), and human-in-the-loop interrupt gates that block forward progress until explicit specialist action is received. LangGraph's state graph model maps precisely to this architecture: each workflow step is a node, each routing decision is a conditional edge, the shared state object is the native LangGraph state schema, and the interrupt mechanism directly supports the Mode B human approval gate. No other major framework offers this combination of explicit state machine modeling, deterministic edge routing, and native human-in-the-loop interrupts.

**Key Capabilities Utilized:**
- **State Graph with Typed State:** The shared state JSON schema is defined as the LangGraph TypedDict state; all agents read from and write to this single state object through graph-managed mutations, ensuring state consistency without direct inter-agent communication channels.
- **Conditional Edges:** The binary Mode A / Mode B routing at Step 7 and all emergency stop branches are implemented as LangGraph conditional edges, making routing logic structurally explicit and not dependent on agent judgment.
- **Human-in-the-Loop Interrupt:** LangGraph's `interrupt_before` and `interrupt_after` mechanisms implement the Mode B human approval gate at Step 9b — execution is structurally paused until an explicit specialist action is logged and passed to the graph.
- **Persistent State Checkpointing:** LangGraph's checkpointer (PostgreSQL backend) persists case state between steps, enabling the SLA Monitor to read elapsed-time data independently, and ensuring that suspended cases after an emergency stop can be fully inspected without re-executing prior steps.
- **Subgraph Isolation:** The SLA Monitor Agent runs as a parallel subgraph with its own independent loop, registered by the Supervisor and terminated on case closure notification — preventing any SLA monitoring state from contaminating sequential case processing state.

**Frameworks NOT Chosen:**
- **CrewAI:** Designed for role-based team coordination with sequential or hierarchical task assignment. Lacks native state machine modeling, deterministic conditional edge routing, and structured human-in-the-loop interrupt support — all of which are non-negotiable for this zero-error-tolerance, regulated workflow.
- **AutoGen:** Optimized for conversational peer-to-peer multi-agent dialogue. This system has no conversational or collaborative reasoning requirement; it requires deterministic procedural execution. AutoGen's conversational model introduces ambiguity incompatible with the behavioral profile's determinism requirement.
- **Simple Google GenAI SDK (without graph framework):** Insufficient for managing multi-step state across five agents with conditional branching, persistent checkpointing, concurrent SLA monitoring, and human interrupt gates. Would require significant custom orchestration logic that duplicates what LangGraph provides natively.

**Custom Components Required:**
- **Veea Lobster Trap Proxy Integration Layer:** A custom middleware wrapper that intercepts all PHI-touching state writes and routes them through the audit proxy before committing to shared state. This is not a LangGraph-native capability and must be implemented as a custom node decorator applied to every agent node that accesses PHI fields.
- **Enterprise Secret Vault Injection Adapter:** A custom credential injection function that delivers runtime credentials to the Data Entry Agent's execution context without writing credentials to LangGraph state at any point.
- **SLA Monitor Parallel Thread Manager:** A custom scheduler that maintains the SLA Monitor Agent's elapsed-time tracking loop as a registered, isolated parallel process, ensuring it continues running during Mode B human hold states without consuming case processing graph resources.

---

## **5. MEMORY ARCHITECTURE**

**Memory Strategy:** Hybrid — Session-scoped ephemeral state (per case) + External persistent audit store (Veea Lobster Trap) + No cross-session agent memory.

---

### **Short-Term Memory**
- **Type:** Case-scoped session state managed by LangGraph state graph with PostgreSQL checkpointer.
- **Duration:** Persists for the lifetime of a single case workflow — from session authorization to case closure or emergency stop. Does not persist across case sessions. Suspended cases retain their state snapshot until explicitly released by a human UM Specialist.
- **Contents:** All fields in the shared state schema (session metadata, extraction payload, criteria evaluation results, mode determination, portal/McKesson prepopulated field maps, SLA timestamps, specialist action records, error logs). Does NOT contain credentials at any point.
- **Access:** All agents read from shared state via LangGraph graph context. Agents may only write to their designated state sections through graph-managed mutations. No agent has unrestricted write access to the full state object.
- **Purpose:** Provides the single source of truth for case context across all agents within one workflow execution. Enables deterministic state transitions, failure recovery inspection, and audit completeness verification without inter-agent direct communication.

---

### **Long-Term Memory**
- **Type:** External persistent audit log store — Veea Lobster Trap compliance proxy (not an agent-owned data store).
- **Technology:** Designated compliance audit system (Veea Lobster Trap) — a pre-existing external system; the agent architecture writes to it via API calls but does not own or manage its storage backend. Specific database technology is determined by the compliance infrastructure team.
- **Contents:** Every PHI field interaction (field name, value accessed, action type, source document ID / session ID, agent identity, UM Specialist identity, exact timestamp); all routing decisions (mode assignments, whitelist condition results, escalation reason codes); all specialist actions (action type, rationale, timestamp, specialist identity); all emergency stop and failure events; all session authorization events; all SLA alert triggers and Code Red re-routings. All agent reasoning steps that result in a routing decision are also logged here.
- **Retrieval Strategy:** Not retrieved by agents at runtime. The audit log is write-only from the agent system's perspective. Retrieval is performed by compliance officers, UM Department Managers, and audit tools through the Veea Lobster Trap's own query interface — outside the agent architecture.
- **Update Strategy:** Written synchronously at every PHI interaction and every routing decision. The Veea Lobster Trap Proxy Integration Layer intercepts all qualifying state writes and confirms log receipt before the state mutation is committed. If the audit proxy does not confirm receipt, the write is aborted and an Emergency Stop is triggered.
- **Purpose:** Enforces HIPAA §164.312(b) field-level access logging compliance; provides complete, tamper-evident audit trail for every PHI interaction and every clinical routing decision; supports CMS compliance verification and breach liability defense.

---

**Memory Boundaries:**
- **What Must Be Remembered:** Active case state (extraction payload, evaluation results, mode determination, SLA timestamps, specialist actions) for the duration of each case. All PHI interactions and routing decisions in the external audit log permanently.
- **What Must Be Forgotten:** Credentials — never written to any memory layer at any point. PHI field values — cleared from LangGraph session state upon case closure; not retained in agent memory after case termination. Extraction payloads from prior cases — not accessible to any agent processing a new case.
- **Retention Policy:** LangGraph case state: retained in suspended state for cases that hit emergency stop (until human-released); cleared after confirmed closure. Veea Lobster Trap audit log: permanent retention governed by HIPAA and organizational policy — outside agent architecture control.

**Memory and Behavioral Constraints:**
- Credentials cannot appear in any memory layer — the Secret Vault Injection Adapter delivers credentials directly to the Data Entry Agent's execution context without touching LangGraph state, ensuring architectural impossibility of credential logging.
- PHI cannot be processed unless a Veea Lobster Trap write is confirmed first — the Proxy Integration Layer enforces this as a hard pre-condition on all PHI-touching state mutations.
- Case state from prior sessions is not accessible to agents processing new cases — LangGraph thread isolation (one thread ID per case) prevents cross-case state contamination.
- Agents cannot access memory sections outside their designated write scope — LangGraph state mutation guards are applied per-agent to enforce role-bounded state access.

---

## **6. MODEL STRATEGY**

**Model Selection Philosophy:**
Reasoning/Execution split combined with task-specialized routing. The two highest cognitive-load tasks — multimodal document parsing and Interqual criteria matching — require the full reasoning and vision capabilities of a large model. The deterministic, structured-output tasks — portal/McKesson field mapping, SLA threshold comparison, and workflow orchestration control flow — are handled by a lighter, faster, cost-efficient model. This split respects the behavioral profile's zero-error tolerance while managing cost and latency at scale.

---

### **Primary Model — Document Processing and Criteria Evaluation**
- **Model:** Gemini 2.5 Pro (`gemini-2.5-pro`)
- **Responsibility:** Document Processing Agent (multimodal OCR, handwritten annotation parsing, structured field extraction, structural complexity flag detection) and Criteria Evaluation Agent (literal Interqual criteria matching, payer config table interpretation, whitelist condition evaluation, escalation reason code generation).
- **Why This Model:** Requires Gemini 2.5 Pro's native multimodal long-context vision capabilities for parsing thermal fax documents including handwritten annotations and shorthand. Requires strong instruction-following for literal, non-inferential Interqual criteria matching with zero tolerance for hallucinated field values. Gemini 2.5 Pro's 1M-token context window accommodates multi-page fax packages with complex nursing flowsheets and medication lists. Pro-class reasoning precision is required for the zero-error-tolerance criteria evaluation — Flash-class models carry unacceptable hallucination risk for clinical field extraction.

---

### **Secondary Model — Supervisor Orchestration, Data Entry, SLA Monitoring**
- **Model:** Gemini 2.5 Flash (`gemini-2.5-flash`)
- **Responsibility:** Workflow Supervisor Agent (session auth verification, mode routing logic, emergency stop detection, human handoff assembly), Data Entry Agent (structured field-to-field mapping, portal/McKesson write sequencing, post-approval field updates), SLA Monitor Agent (elapsed time threshold comparison, alert routing, Code Red re-routing).
- **Why This Model:** All three of these agents execute highly deterministic, rule-based operations with structured inputs and structured outputs — no open-ended reasoning, no ambiguity resolution. Gemini 2.5 Flash's latency and cost profile is optimal for these agents, which may execute frequently and concurrently across many cases. Supervisor routing logic is a binary condition check against the whitelist determination already computed by the Criteria Evaluation Agent — it does not require deep reasoning capability.

---

**Routing Logic:**
- Document Processing Agent → Gemini 2.5 Pro (always; vision and extraction required)
- Criteria Evaluation Agent → Gemini 2.5 Pro (always; precision criteria matching required)
- Workflow Supervisor Agent → Gemini 2.5 Flash (always; deterministic routing control)
- Data Entry Agent → Gemini 2.5 Flash (always; structured field mapping, no reasoning required)
- SLA Monitor Agent → Gemini 2.5 Flash (always; simple threshold comparison)

**Reasoning vs Execution Split:** Yes
- **Reasoning Model:** Gemini 2.5 Pro — Document parsing and Interqual criteria matching.
- **Execution Model:** Gemini 2.5 Flash — Orchestration control, portal data entry, SLA alerting.
- **Handoff Logic:** Pro agents return structured payloads (extraction payload, criteria evaluation result with whitelist determination and escalation reason codes) written to LangGraph shared state. Flash agents read these structured outputs from shared state and act deterministically on them — no re-interpretation.

**Fallback Strategy:**
- **Primary Model Failure (Pro):** Criteria evaluation or document extraction cannot complete. Data Entry Agent halts. Workflow Supervisor classifies as Permanent Failure, suspends case, logs failure event, and escalates to UM Department Manager. No retry of clinical reasoning tasks — behavioral profile's zero-error tolerance prohibits approximation on retry.
- **Fallback Model:** None for Pro-class tasks. Given zero-error tolerance, falling back to a less capable model for clinical extraction or criteria matching is architecturally prohibited — it introduces exactly the approximation risk the behavioral profile forbids.
- **Escalation Path:** Permanent Failure Protocol → case suspended → UM Department Manager notified → manual processing by specialist.
- **Flash-class tasks:** Single retry with exponential backoff for transient API failures (max 3 attempts, 2s/4s/8s). On third failure, Permanent Failure Protocol applies.

**Cost & Scalability Analysis:**
- **Estimated Cost Per Case (Mode A):** Low–Medium ($0.05–$0.15) — Gemini 1.5 Pro for extraction + evaluation (2 calls on multi-page fax package), Gemini 1.5 Flash for supervisor, entry, and SLA.
- **Estimated Cost Per Case (Mode B):** Low–Medium ($0.08–$0.20) — Same Gemini 1.5 Pro calls plus recommendation package generation; additional Gemini 1.5 Flash calls for pre-population and post-approval update.
- **Scalability Bottleneck:** Gemini 1.5 Pro throughput limits under high concurrent volume (many cases processed simultaneously). Document Processing Agent calls on large multi-page fax packages are the highest-latency operations.
- **Optimization Strategy:** SLA Monitor Agent runs on Gemini 1.5 Flash at negligible cost regardless of case volume. Gemini 1.5 Pro calls are scoped to two discrete tasks per case — parsing and evaluation — limiting exposure. Gemini 1.5 Flash handles all other agent operations. No speculative or exploratory model calls are made (deterministic flow eliminates wasted inference).

---

## **7. TOOL INVOCATION STRATEGY**

**Tool Usage Permission:**
- Document Processing Agent: May invoke secure intake source reader, OCR/vision tooling.
- Criteria Evaluation Agent: May invoke Payer Master Configuration Table query tool.
- Workflow Supervisor Agent: May invoke session authorization verifier, audit proxy write tool, human handoff notification tool.
- Data Entry Agent: May invoke payer portal API/RPA tool, McKesson write API, Secret Vault credential consumer (receive only), Veea Lobster Trap write tool.
- SLA Monitor Agent: May invoke alert notification tool, High Priority queue re-routing tool.
- No agent may invoke tools outside its designated tool set.

**Invocation Pattern:**
- **Direct Invocation:** Yes for all read-type tools (intake source, config table query, session verifier). Agents call approved read tools immediately upon reaching the relevant workflow step.
- **Approval Required:** Yes for all portal and McKesson write tools in Mode B — the Data Entry Agent may not invoke portal write or submission tools until Workflow Supervisor confirms a logged specialist approval action has been received. In Mode A, direct invocation applies (whitelist conditions enforce the gate structurally prior to tool call).
- **Batching:** Yes for portal field population — all non-clinical field writes are batched per portal session and per McKesson session to minimize authentication overhead and ensure atomic parity validation.

**Tool Access Control:**
- Portal write tools and McKesson write API: Data Entry Agent only.
- Payer Master Configuration Table query: Criteria Evaluation Agent only.
- Veea Lobster Trap write: All agents with PHI access (Document Processing, Criteria Evaluation, Data Entry, Workflow Supervisor for routing decisions); each writes only to its own designated audit record sections.
- Enterprise Secret Vault consumer: Data Entry Agent only (receive credential injection); no other agent calls the vault.
- Alert and re-routing tools: SLA Monitor Agent only.
- Human handoff notification: Workflow Supervisor only.

**Guardrails:**
- **Rate Limiting Strategy:** Token Bucket — maximum 30 portal API calls per minute per active session (enforced at the tool invocation layer, not the agent layer). Maximum 10 Payer Master Configuration Table queries per minute per agent (prevents runaway config polls).
- **Cost Control:** Session-level budget cap of $2.00 in model inference cost; if exceeded, Workflow Supervisor is notified and the case is suspended pending review.
- **Permission Checks:** Each tool invocation includes a session identity assertion check — tools verify that the invoking agent is operating within an active, verified session before executing.
- **Validation:** Extraction payloads are schema-validated before passing to the Criteria Evaluation Agent. Criteria evaluation results are schema-validated before the Workflow Supervisor reads the whitelist determination. Portal write batches are validated for field completeness and non-clinical scope before submission.
- **Prohibited Actions:** Clinical necessity field writes are not available as tool capabilities — they are absent from the tool manifest, making their invocation architecturally impossible. Credential logging tools do not exist in any agent's tool set. Provider-facing or member-facing communication tools do not exist in any agent's tool set. Record modification and deletion tools do not exist in any agent's tool set. Any tool not in the approved integration manifest is not available.

**Tool Call Flow:**
1. Agent determines tool is required based on current workflow step.
2. Agent asserts active session identity to tool invocation layer.
3. For Mode B portal writes: Workflow Supervisor confirms logged specialist approval before tool invocation is permitted.
4. Tool executes with validated inputs.
5. Tool result is schema-validated; written to shared state in designated agent section.
6. If tool result touches PHI: Veea Lobster Trap write is confirmed before state mutation commits.
7. Agent proceeds to next workflow step or triggers failure protocol based on result.

**Tool Failure Handling:**
- Transient tool failure (timeout, rate limit, temporary unavailability): Retry with exponential backoff, max 3 attempts (2s/4s/8s). Applies to: config table query, portal API calls, McKesson write API, alert notification.
- Audit proxy tool failure: No retry; immediate Emergency Stop. PHI may not be processed without confirmed logging.
- Secret Vault tool failure: No retry; immediate Emergency Stop.
- Permanent tool failure (authorization denied, invalid input, schema mismatch): Halt, log to error log, suspend case, escalate to UM Department Manager.

---

## **8. FAILURE & RECOVERY ARCHITECTURE**

**Failure Detection:**
All agents validate tool results and state writes against expected schemas at each step. The Workflow Supervisor monitors for emergency stop conditions as a continuous pre-condition check before each node transition. The Veea Lobster Trap Proxy Integration Layer confirms audit write receipt synchronously — any unconfirmed write halts execution. LangGraph checkpointing detects mid-step state corruption by comparing state hash at node entry and exit.

---

**Failure Categories:**

### **Transient Failures** (Retryable)
- **Examples:** Payer portal API timeout; McKesson write API rate limit; Payer Master Configuration Table momentary unavailability (under 30 seconds); alert notification delivery delay; model API transient error for Flash-class agents.
- **Response:** Retry with exponential backoff. Maximum 3 attempts. If third attempt fails, classify as Permanent Failure.
- **Backoff Strategy:** Attempt 1 immediately; Attempt 2 after 2 seconds; Attempt 3 after 4 seconds. Total max wait: 6 seconds before escalating to Permanent Failure.

### **Permanent Failures** (Non-Retryable)
- **Examples:** Whitelist condition post-submission audit reveals condition was unmet; PHI interaction without audit log confirmation; credential found stored outside Secret Vault; CMS 72-hour deadline breached without all three SLA alerts having triggered; portal-McKesson field mismatch on agent-processed case; session initiated without verified specialist authorization; any prohibited action in Section 4 of behavioral profile executed; Gemini 1.5 Pro model API failure on document extraction or criteria evaluation; audit proxy returns permanent error; portal write authorization denied.
- **Response:** Immediate halt of all active workflow processing for the affected case. Log failure event with full context (case ID, action attempted, condition violated, timestamp, session identity) to error log and to Veea Lobster Trap. Place all in-progress cases in suspended state accessible to UM Department Manager. Await explicit human instruction before any processing resumes. Do not attempt self-recovery or retry.

### **Ambiguous Failures** (Uncertain)
- **Examples:** Model confidence on extracted field value is internally low (field parsed but uncertain); structural complexity flag is borderline; partial Payer Master Configuration Table response (some fields returned, some null).
- **Response:** Treat as Mode B mandatory. Per behavioral profile: any ambiguity defaults to human escalation. Ambiguous failures do not trigger Emergency Stop — they trigger escalation routing. Ambiguity is never resolved by agent approximation.

---

**Recovery Strategies:**

- **Retry Logic:**
  - Max Retries: 3 (for transient failures only)
  - Backoff: Exponential (2s, 4s — total 6s max)
  - Retry Conditions: Transient API failures, timeout errors, rate limit responses only.

- **Graceful Degradation:**
  - Conditions: Payer Master Configuration Table temporarily unreachable during active workflow.
  - Degraded Behavior: Case is routed to Mode B (human escalation) with explicit escalation reason code "config_table_unavailable." Processing continues in Mode B — the degraded path is defined in the behavioral profile and is fully functional, not reduced.

- **Halt and Escalate:**
  - Conditions: Any permanent failure; any emergency stop condition; any prohibited action detected; audit proxy unreachable; Secret Vault unreachable; session authorization unverifiable.
  - Escalation Path: Workflow Supervisor logs full failure event to Veea Lobster Trap error section. UM Department Manager is notified via the alert notification tool with: case ID, failure type, condition violated, timestamp, affected cases list. All in-progress cases suspended. No further action by agent.

- **Rollback:**
  - Conditions: Portal-McKesson mismatch detected after fields have been written to one system but not both.
  - Rollback Scope: The Data Entry Agent does not modify or delete existing records (prohibited). Rollback means: halt submission, log the mismatch as a permanent failure, suspend the case. The partially written data in the target system is flagged in the error log for human review and correction — the agent does not attempt to undo the write (modification is prohibited).

**State Consistency:**
LangGraph's PostgreSQL checkpointer writes state at each node boundary. If a node fails mid-execution, the last committed checkpoint is the authoritative case state — no partial state is committed. The Veea Lobster Trap Proxy Integration Layer enforces that audit log writes precede state commits for PHI-touching operations, ensuring audit completeness is never sacrificed for state update speed.

**Circuit Breaker:**
If the Workflow Supervisor detects three consecutive Emergency Stop events across different cases within a 5-minute window, it initiates a system-level circuit breaker: suspends all active case processing across all cases, notifies the UM Department Manager with a system-level alert, and awaits explicit system-level restart authorization. Individual-case failures do not trigger the circuit breaker — only the pattern of repeated emergency stops indicates a systemic infrastructure failure requiring human review before any case processing continues.

---

## **9. CONSTRAINTS INHERITED FROM LLM-1**

**Behavioral Constraints Enforced Architecturally:**

1. **No autonomous clinical necessity determination (Prohibition 1)**
   - **Architectural Enforcement:** Clinical necessity fields are absent from every agent's tool manifest — they cannot be written to portals or McKesson by any agent under any condition. The Criteria Evaluation Agent's output schema contains only `criteria_match_type`, `whitelist_determination`, and `escalation_reason_codes` — it has no output field for "clinical necessity determination." The routing logic reads the binary whitelist determination; it does not read or act on a clinical necessity conclusion. The Data Entry Agent's field mapping schema explicitly excludes all clinical necessity fields.

2. **No provider or member communication (Prohibitions 2–3)**
   - **Architectural Enforcement:** No outbound communication tools (email, fax, portal message, phone API) directed at provider or member endpoints exist in any agent's tool set. The approved integration manifest does not include any provider portal or member portal. No agent has communication tools available at all — human handoff notification is the only outbound channel, and it routes exclusively to internal UM Specialist and UM Manager endpoints.

3. **No modification or deletion of existing case records (Prohibitions 4–5)**
   - **Architectural Enforcement:** McKesson write API and portal write tools expose only create/append operations on new case records and new field values — no update, patch, or delete operations are available in the tool manifest. The Veea Lobster Trap Proxy Integration Layer would detect any attempted write that targets an existing record ID and block it as a prohibited action.

4. **No credential storage, caching, or logging (Prohibition 6)**
   - **Architectural Enforcement:** Credentials are never written to LangGraph shared state (they are excluded from the shared state schema). The Secret Vault Injection Adapter delivers credentials directly to the Data Entry Agent's runtime execution context — they exist only as ephemeral in-memory values for the duration of the authenticated portal session. The Veea Lobster Trap Proxy Integration Layer scans all audit log writes for credential patterns and would block any log entry containing credential values. The LangGraph state schema has no credential field and no mechanism to add one at runtime.

5. **No workflow initiation without verified UM Specialist session authorization (Prohibition 7)**
   - **Architectural Enforcement:** Session Authorization Verification (Step 1) is the first node in the LangGraph state graph, and it is a prerequisite node — no other node has an incoming edge that bypasses it. The LangGraph graph structure makes it topologically impossible to reach any document processing, evaluation, or data entry node without first passing through the session authorization verification node and confirming a log write to the Veea Lobster Trap.

6. **No autonomous submission when any whitelist condition is unmet (Prohibition 8)**
   - **Architectural Enforcement:** The whitelist determination is binary and written to shared state by the Criteria Evaluation Agent. The LangGraph conditional edge at Step 7 reads `all_whitelist_conditions_met` — if `false`, the graph routes exclusively to Step 8b (Mode B pre-population only). The Data Entry Agent's submission tool is only invocable when the Workflow Supervisor confirms `active_mode = mode_a` in shared state. In Mode B, the submission tool call is structurally blocked until a specialist approval action is logged — the tool invocation layer validates mode status before permitting any submission tool execution.

7. **No autonomous submission when Payer Master Configuration Table is unreachable or ambiguous (Prohibition 9)**
   - **Architectural Enforcement:** `payer_config_reachable = false` in the shared state is evaluated as an automatic `whitelist_determination = mode_b` condition in the Criteria Evaluation Agent's output logic. A false reachability value propagates to `all_whitelist_conditions_met = false` regardless of all other conditions, routing the LangGraph conditional edge to Mode B.

8. **No runtime configuration raising baseline thresholds above locked maximums (Prohibition 10)**
   - **Architectural Enforcement:** Baseline thresholds ($10,000 cost, 5-day LOS) are hardcoded in the `config` section of the shared state schema and in the Criteria Evaluation Agent's evaluation logic. Runtime Payer Master Configuration Table values are only applied if they are strictly lower than the baseline. The Criteria Evaluation Agent's threshold comparison logic evaluates `runtime_value < baseline_value` — if a runtime value equals or exceeds the baseline, `runtime_config_exceeds_baseline = true` is set, which propagates to `all_whitelist_conditions_met = false`, guaranteeing Mode B routing. No runtime instruction from any source can override this comparison logic.

9. **No PHI processing outside the Veea Lobster Trap audit proxy (Prohibitions 11–12)**
   - **Architectural Enforcement:** The Veea Lobster Trap Proxy Integration Layer is implemented as a mandatory decorator on every agent node that accesses PHI fields. The decorator intercepts the PHI access, writes the audit record to Veea Lobster Trap, and only permits the state mutation to proceed upon confirmed receipt. If the decorator fails (proxy unreachable), the node execution is aborted and an Emergency Stop is triggered before any PHI value is read by the agent.

10. **Mandatory human escalation for ICU, Surgery, SUD, Behavioral Health, Experimental cases (Prohibition 13)**
    - **Architectural Enforcement:** These acuity categories are evaluated as a dedicated whitelist condition (d) in the Criteria Evaluation Agent's evaluation logic. Detection of any of these flags in `acuity_flags` sets `acuity_threshold_met = true`, which propagates to `all_whitelist_conditions_met = false`, guaranteeing Mode B routing. The acuity flag evaluation occurs before the whitelist determination is written — there is no code path where an acuity-flagged case receives a Mode A determination.

11. **No data sharing with systems outside the approved integration manifest (Prohibition 14)**
    - **Architectural Enforcement:** All tool invocations include a manifest validation check at the tool invocation layer — the endpoint or system identifier is validated against the approved integration manifest version stored in the `config` section of shared state before any tool call is executed. Any endpoint not in the manifest causes the tool call to be blocked and logged as a prohibited action.

---

**Autonomy Level Enforcement:**
- **Behavioral Profile Specifies:** Semi-Autonomous
- **Architectural Implementation:** The LangGraph state graph structurally enforces the binary Mode A / Mode B determination. Mode A autonomous execution is only reachable through the conditional edge that requires `all_whitelist_conditions_met = true` — a condition that requires all seven independent whitelist criteria to be simultaneously true, evaluated by a separate agent (Criteria Evaluation Agent) from the one taking action (Data Entry Agent), with results passing through the Workflow Supervisor as an intermediate validation step. Mode B always requires an explicit, logged specialist action before any submission tool can be invoked. The human-in-the-loop gate in Mode B is a structural LangGraph interrupt, not a convention — execution cannot continue past Step 9b without a confirmed external specialist action event.

**Human-in-the-Loop Gates:**
- **Required Approvals:** Any case with partial/ambiguous criteria match; any case with structural complexity flags; any case exceeding $10,000 projected cost; any ICU, Surgery, SUD, Behavioral Health, or experimental case; any case with LOS exceeding 5 days; any case where config table is unreachable or ambiguous; any case where runtime config attempts to exceed baseline thresholds; specialist approval before submission in Mode B; UM Department Manager restart authorization after any emergency stop.
- **Architectural Implementation:** All escalation conditions result in `all_whitelist_conditions_met = false`, which routes the LangGraph conditional edge to Mode B. Mode B's human approval gate is implemented as a LangGraph `interrupt_before` on the Step 10b node — the graph suspends and writes `awaiting_human_action = true` to shared state. The graph cannot advance to Step 10b until an external event (specialist action logged to shared state) releases the interrupt. Emergency stop restart requires UM Department Manager action delivered as an explicit graph resume command with documented acknowledgment — the graph has no self-resume capability.

**Prohibited Actions:**
- **From Behavioral Profile:** Clinical necessity determination; provider/member communication; record modification/deletion; credential storage; unsanctioned session initiation; autonomous submission on unmet whitelist conditions; config table bypass; threshold override; PHI processing without audit logging; audit logging suppression; acuity-category autonomous action; external system data sharing.
- **Architectural Prevention:** All prohibited actions are prevented by one or more of: absence of required tools from agent tool manifests; LangGraph conditional edge routing that makes prohibited paths topologically unreachable; Veea Lobster Trap Proxy Integration Layer enforcement; session authorization prerequisite node; baseline threshold hardcoding; approved integration manifest validation at tool invocation layer; LangGraph interrupt gates on submission steps.

**Scope Boundaries:**
- **In Scope:** Prior Authorization (Concurrent Review) processing only; document ingestion from designated secure intake source; non-clinical field population in approved portals and McKesson; Interqual criteria matching in read-only evaluation mode; SLA monitoring and alerting; criteria-based recommendation generation for escalated cases; field-level PHI audit logging.
- **Out of Scope:** Pre-authorization; retrospective review; denial management; appeal processing; claim adjudication; provider contract management; population health analysis; any case type other than Concurrent Review; any system not in approved integration manifest.
- **Architectural Enforcement:** Out-of-scope case types are detected at the session authorization step (case_type field in shared state must equal "concurrent_review"); any other value triggers an out-of-scope log event and workflow termination without any document processing. Out-of-scope system access is prevented by the approved integration manifest validation layer. Scope boundaries are fixed — no runtime configuration, specialist instruction, or manager directive can modify the case_type acceptance criteria or the integration manifest version within an active session.

---

**Verification Statement:**
This architecture fully respects all constraints defined in AGENT_BEHAVIOR_PROFILE.md.
No behavioral boundary can be violated by this orchestration design.

---

## **ARCHITECTURE INTEGRITY DECLARATION**

This orchestration blueprint is AUTHORITATIVE.

All downstream systems must:
- Implement agent topology exactly as specified (five agents: Workflow Supervisor, Document Processing, Criteria Evaluation, Data Entry, SLA Monitor)
- Follow execution flow without deviation (Steps 1–9a / 1–11b as specified, with all decision points and emergency stop branches)
- Use LangGraph as the orchestration framework with PostgreSQL checkpointer
- Implement memory architecture as designed (session-scoped LangGraph state; Veea Lobster Trap as write-only external audit store; no credential persistence in any memory layer)
- Route to models as specified (Gemini 2.5 Pro for Document Processing and Criteria Evaluation; Gemini 2.5 Flash for Supervisor, Data Entry, and SLA Monitor)
- Implement the Veea Lobster Trap Proxy Integration Layer as a mandatory PHI-access decorator on all qualifying agent nodes
- Implement the Secret Vault Injection Adapter as a credential delivery mechanism that never touches LangGraph state
- Enforce tool invocation guardrails (manifest validation, session assertion, Mode B approval gate, prohibited tool absence)
- Handle failures per recovery strategies (transient: max 3 retries with exponential backoff; permanent: halt, log, suspend, escalate; emergency stop: no self-recovery, UM Manager authorization required for restart)
- Respect all inherited behavioral constraints as architecturally enforced in Section 9

No architectural decision may be changed without invalidating this blueprint.

---
