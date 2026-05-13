# INTERFACE & OBSERVABILITY SYSTEM

**Generated:** May 11, 2026
**Source:** AGENT_LOGIC_SPEC.md
**Status:** AUTHORITATIVE — Defines complete human-agent interaction layer
**Purpose:** Interface design and observability specification for the HIPAA-Regulated Prior Authorization (Concurrent Review) Processing System

---

## **1. INTERACTION PHILOSOPHY**

**Overall Interaction Model:** Task-First

**Description:**
This is not a conversational system. The UM Specialist initiates a discrete, structured case processing workflow and monitors deterministic step-by-step execution in real time. The agent is not responding to open-ended queries — it is executing a fixed eight-step pipeline with two possible routing outcomes (Mode A autonomous execution, or Mode B human review gate). The interface reflects this reality: it is a workflow execution monitor, not a chat surface.

**Human vs Agent Initiative:**
- **User-Driven:** The UM Specialist initiates the session by providing session credentials and case ID. In Mode B, the specialist holds exclusive authority over the case's submission disposition — the system cannot advance without an explicit, logged specialist action.
- **Agent-Driven:** After session initiation, the agent autonomously executes Steps 1–6 (and Steps 7A/8 in Mode A), progressing through each workflow phase without waiting for user input unless a gate condition is triggered.
- **Collaborative:** Mode B cases are collaborative — the agent completes all preparatory work (document processing, criteria evaluation, pre-population, Full Recommendation Package) and suspends at the approval gate. The specialist reviews the assembled package and takes a definitive logged action (Approve / Modify / Override).

**This Agent's Initiative Model:**
After session initiation, the agent drives execution through the fixed workflow sequence. The user observes progress in real time. Initiative returns entirely to the specialist at the Mode B approval gate (Step 7B) and at any Emergency Stop state. In Mode A, the specialist's role is observational until case closure confirmation. The system is semi-autonomous by architectural design — this autonomy level cannot be changed by the user.

**Transparency vs Simplicity Balance:**

**Transparency Priority:**
- Every workflow step's outcome must be visible before the next step begins.
- The binary routing decision (Mode A / Mode B) and all seven whitelist condition results must be shown in full — partial views are prohibited.
- Every Emergency Stop must name the specific trigger condition, with no vague or softened language.
- The Full Recommendation Package (Mode B) must be presented completely — no fields may be collapsed by default.
- PHI audit log confirmation status must be visible before any PHI-dependent result is displayed.

**Simplicity Priority:**
- The names of internal tools (e.g., `write_phi_audit_log`, `verify_session_authorization`) are abstracted into plain-language step labels for the specialist UI (e.g., "Confirming Session Identity," "Verifying Audit Logging System").
- The LangGraph shared state schema, node graph topology, and multi-agent coordination mechanics are not surfaced.
- Individual PHI field-level audit log calls (which may number 30+ per case) are aggregated into a single audit confirmation indicator per step, not listed individually.
- Raw JSON tool input/output schemas are available only in Debug Mode.

**Balance Strategy:**
Show plain-language summaries of every step outcome by default. Expand into technical detail (tool names, condition codes, escalation reason codes, raw flags) on explicit user action. Never collapse content that a specialist needs to make an approval decision.

**Interaction Principles:**
1. The agent never advances a workflow step without visibly confirming the prior step's outcome in the UI.
2. The specialist always has access to the Emergency Stop control at every state of execution.
3. Mode B suspension is never ambiguous — the system makes the waiting-for-human state explicit, persistent, and prominent.
4. Uncertainty, incompleteness, and failure are communicated with the same visual prominence as success.
5. No action taken by the agent is invisible — every tool call that changes case state generates a visible activity log entry.

---

## **2. PRIMARY USER INTERFACE**

**Core Interaction Surface:**
Case Workflow Timeline — a structured, step-by-step vertical timeline view showing the eight workflow phases with real-time status. The specialist sees the case progressing through numbered steps, each with its current status (Pending / In Progress / Completed / Failed / Suspended). The Mode B approval panel appears as a dedicated, persistent full-panel state replacing the timeline view when the approval gate is active.

**Layout Structure:**
Three-panel layout on desktop:
- **Center Panel (Primary):** Workflow timeline with step cards for each of the eight workflow phases. Each card expands to show tool execution detail.
- **Right Sidebar:** Live Activity Log — a chronological event feed showing all agent events for this case session with timestamps and event types.
- **Header Bar:** Case ID, assigned UM Specialist identity (from verified session), current workflow phase label, autonomy mode badge ("Semi-Autonomous — Mode A" or "Semi-Autonomous — Mode B Pending"), SLA elapsed time counter, and Emergency Stop button.

**Message Types:**

### **User Messages**
- **Format:** Not applicable in the primary workflow execution view. The specialist's primary interactions are structured button actions (Approve / Modify / Override), not free text. In the Modification flow, a structured field editor and a required rationale text field are used.
- **Input Mechanisms:** Session initiation form (case ID, specialist ID, session token); Mode B decision buttons; rationale text fields; Emergency Stop button.
- **Display:** Specialist actions are recorded in the Activity Log with the specialist's verified identity, action type, and timestamp, styled distinctly from agent events.

### **Agent Messages**
- **Format:** Structured step cards with status, plain-language outcome summary, and expandable technical detail.
- **Display:** Each step card updates in real time as the agent executes. Completed steps show a status icon (success, failure, or routed-to-human). In-progress steps show an animated status indicator. Agent step cards never contain free-text conversational language.
- **Components:** Step label, plain-language status summary, key result values (e.g., "Routing Decision: Mode B — 3 of 7 conditions failed"), expandable condition detail, expandable tool detail, timestamp.

### **System Messages**
- **Purpose:** Emergency Stop state announcements, circuit breaker activations, out-of-scope case type detections, SLA threshold alerts (when surfaced to the specialist's view), and session expiration warnings.
- **Display:** System messages appear as full-width banner interrupts at the top of the center panel, styled with a visually distinct treatment (warning or critical severity level) that cannot be dismissed without acknowledgment. They persist until the triggering condition is resolved or the specialist takes an explicit action.

### **Tool Output Messages**
- **Purpose:** Detailed results from individual tool executions, available on expansion of a step card.
- **Display:** Within each step card's expanded view, individual tool calls are listed with their plain-language label, status, and key output values. Raw JSON output is available in Debug Mode only.
- **Interactivity:** Step cards are expandable/collapsible. Mode B Full Recommendation Package is presented as a non-collapsible structured document panel.

**Technical Implementation Specs:**

**Frontend Tech Recommendations:**
- **Component Library:** Shadcn/UI with Tailwind CSS
- **Reason:** Shadcn's composable unstyled primitives support the highly structured, data-dense step card and approval panel patterns this interface requires without imposing visual chrome that would obscure workflow state. Tailwind enables precise status-state styling (e.g., suspended, emergency, in-progress) without a heavy theming layer.

**Connection Protocol:**
- **Protocol:** Server-Sent Events (SSE) for workflow step status streaming from the LangGraph execution graph; WebSocket for the Mode B interrupt gate (bidirectional: agent suspends execution, specialist submits action, agent receives release event).
- **Justification:** SSE is appropriate for the primary unidirectional step-progress stream. WebSocket is required for the Mode B interrupt gate because the specialist's action must be transmitted back to the suspended LangGraph graph to release execution — this is a bidirectional event, not a one-way stream.

**Accessibility (A11y) Standards:**
- **Live Regions:** `aria-live="polite"` on each step card's status region. `aria-live="assertive"` on Emergency Stop state banners and Mode B approval gate activation announcements to ensure screen readers announce these immediately.
- **Keyboard Nav:** Focus management must advance to each newly completed step card as it resolves, allowing keyboard-only specialists to follow the workflow progression without manual navigation. The Mode B approval panel must receive focus automatically when the interrupt gate activates.
- **Screen Readers:** "In Progress" animated states must be announced once on transition (not repeatedly). The animated liveness indicator must have a static `aria-label` (e.g., "Step in progress — Extracting document fields") that does not re-announce on each animation frame.

**Responsive Strategy:**
- **Mobile View:** The three-panel layout collapses to a single scrollable timeline. The Activity Log is accessible via a bottom sheet. The Mode B approval panel renders full-screen. The Emergency Stop button is always pinned to the top of the viewport.
- **Desktop View:** Full three-panel layout with the Activity Log sidebar open by default. Step cards show summary content at rest; expansion reveals tool detail.

**Streaming Behavior:**

**Streaming Granularity:** Step-by-step. Each workflow step (Steps 1–8) streams as a discrete unit — the step card transitions from Pending → In Progress → Completed/Failed. Within a step, individual tool call statuses stream in sequence. Token-level text streaming is not applicable; this is a structured workflow, not a generative text interface.

**Streaming Strategy:**
- **Workflow Steps:** Each step card updates its status indicator and summary line as the agent completes each step. No buffering — status transitions appear as they occur in the execution graph.
- **Agent Reasoning:** The Graph-Node ReAct reasoning loop's "think" phase is summarized as a single plain-language precondition-check line per step (e.g., "Verifying audit log system reachability before proceeding..."). Full reasoning traces are available in Debug Mode.
- **Tool Execution:** Each tool call within a step streams its own status: Calling → Awaiting Response → Confirmed / Failed.

**Real-Time Updates:**
- **Status Indicators:** Each step card has an animated "in-progress" indicator (pulsing status dot) while the step is executing. The header SLA counter ticks in real time.
- **Progress Bars:** Not applicable — the eight-step workflow is discrete, not continuous. A step-completion indicator (e.g., "Step 3 of 8") provides positional context without implying proportional time.
- **Cancellation:** The specialist can trigger an Emergency Stop at any point via the always-visible header button. This is the only mid-execution user control — there is no pause capability separate from Emergency Stop.

**Message Threading:**
Not applicable. This is a single-case, single-session workflow execution per interface instance — there is no multi-turn conversation threading. Each case session is a discrete execution run. The Activity Log provides the chronological event record for the session.

---

## **3. REASONING VISIBILITY MODEL**

**Visibility Philosophy:**
The agent's cognitive loop is Graph-Node ReAct: at each node, the agent reads shared state, checks preconditions, calls a designated tool, validates the tool result against expected schema, writes to shared state, and advances. This is deterministic and structurally transparent. The interface exposes the precondition-check logic and tool validation outcome at each step, not internal chain-of-thought text. Specialists need to understand what the agent did and why the workflow advanced or halted — not the full internal reasoning trace.

**Visible Reasoning Components:**

### **Precondition Verification (per step)**
- **What's Shown:** A plain-language precondition summary for each step (e.g., "Confirmed: session authorization verified and audit proxy reachable. Proceeding to document retrieval."). If a precondition is not met, the condition that failed is named explicitly.
- **When Shown:** Inline, displayed as the first element of each step card as the step begins.
- **Format:** Single-line status text within the step card. Failure cases use warning-level styling.
- **User Control:** Always visible in step card. Cannot be hidden.

### **Tool Call Decision (per tool within step)**
- **What's Shown:** Plain-language label for each tool call (e.g., "Retrieving fax document from secure intake source..."), the key parameter used (case ID, step name — never credential values or PHI field values), and whether the call succeeded, is being retried, or failed permanently.
- **When Shown:** Inline during step execution, in real time as each tool call fires.
- **Format:** Collapsible list within the step card. Default view shows label and status only. Expanded view shows additional non-PHI, non-credential output values.
- **User Control:** Expandable per tool call. Default state is collapsed within completed steps. Default state is expanded for in-progress and failed steps.

### **Schema Validation Outcome**
- **What's Shown:** Whether the tool's output matched the expected schema. If not, what field failed validation (e.g., "Tool returned null for required field: whitelist_determination — halting step."). Schema failures are shown with error styling.
- **When Shown:** Immediately after each tool call result is received.
- **Format:** Single status line within the tool call entry. On failure, expands to show the specific failed field.
- **User Control:** Always visible for failures. Collapsed by default for successful validations.

### **Whitelist Condition Evaluation Results (Step 5 — Criteria Evaluation)**
- **What's Shown:** All seven whitelist conditions, each with its individual pass/fail result and the plain-language reason (e.g., "Condition C: FAILED — Projected cost $12,400 exceeds $10,000 baseline maximum"). The overall whitelist_determination (mode_a / mode_b) is shown as the step's primary outcome.
- **When Shown:** Inline within Step 5's step card, non-collapsible.
- **Format:** Structured table showing condition label, pass/fail status, and reason text for each of the seven conditions. The routing determination is displayed prominently above the table.
- **User Control:** The condition table is always fully visible when Step 5 is complete. Escalation reason codes (from cognitive spec) are shown verbatim in the table's reason column.

### **Mode Routing Decision (Step 6)**
- **What's Shown:** The binary routing decision — "Mode A: Autonomous Execution" or "Mode B: Specialist Review Required" — with the full list of failed conditions as the basis for Mode B routing. The routing audit log reference is shown as a confirmation indicator.
- **When Shown:** Inline in Step 6's step card.
- **Format:** Prominent single-line routing outcome (Mode A or Mode B), followed by the condition results that drove the decision. Cannot be collapsed.
- **User Control:** Always visible.

**Summarization Strategy:**

**When to Summarize:**
- PHI field-level audit log calls: The system calls write_phi_audit_log once per field — there may be 30+ calls per step. These are summarized as "PHI audit logging confirmed for [N] fields" per step, not listed individually.
- Retry attempts for transient tool failures: Summary "Retried 2 times — success on attempt 3" rather than showing each retry event inline.

**How to Summarize:**
- Aggregate count with confirmation status. Never hide whether a summary represents success or failure.
- If a summarized set contains any failure, the summary is styled as a warning even if ultimately resolved by retry.

**When to Show Full Detail:**
- Any tool failure (permanent) — full tool name, failure reason, and response values shown.
- Mode B approval gate — Full Recommendation Package is never summarized; every field is presented.
- Emergency Stop — the trigger condition, condition violated, and action attempted are shown in full.
- Debug Mode — all tool names, all tool inputs (excluding credential values and PHI field values), and all tool output fields.

**Progressive Disclosure:**

**Default View:**
- Step card: Status icon, step label, plain-language outcome summary, key result values.
- PHI audit: Aggregated count and confirmation status.
- Tool calls: Label and status only (collapsed).
- Whitelist conditions: Full table (not collapsed — too critical to hide by default).

**Expandable View:**
- Tool call detail: Non-credential, non-PHI input parameters and output field values.
- Retry history: Count and timing of retry attempts.
- Routing audit log reference: Log_ref identifier for traceability.
- SLA registration confirmation.

**Hidden Entirely:**
- Raw system prompt text for any agent.
- Internal LangGraph state schema and node graph topology.
- Credential injection confirmation details beyond "Credential injection: Confirmed."
- PHI field values at any point — never displayed in the UI regardless of context.
- Raw API call payloads (available in Debug Mode as non-PHI subsets only).
- Agent-to-agent communication internals (orchestration details).

**Safety Filters for Sensitive Reasoning:**

**Content That Must Be Filtered:**
- PHI field values: Never displayed in any view mode. Only field names and audit log references are shown.
- Credential values: Never displayed. Credential operations are shown only as confirmation/failure status.
- Exact safety check implementation logic: Shown as outcome ("Guardrail triggered: [condition name]"), not as implementation detail.
- Internal session token or session_token_ref values: Never displayed.

**Filtering Strategy:**
PHI field values and credential values are replaced with a fixed "[Protected]" placeholder if they would otherwise appear in any log or status display. Field names are shown (e.g., "member_date_of_birth") but not values. Credential references show only opaque handle identifiers (session_token_ref is shown as a reference label, not its value).

**Transparency About Filtering:**
A persistent footnote in the step card footer states: "PHI field values and credential values are not displayed in this interface. Audit logging of all PHI interactions is confirmed via the Veea Lobster Trap audit proxy." This footnote appears on all steps that involve PHI or credential operations.

---

## **4. TOOL & ACTION OBSERVABILITY**

**Tool Call Visibility:**

Each tool call is represented in the step card of its owning agent's workflow step. The interface does not expose the agent-tool access matrix to the specialist directly — specialist-facing display shows step-level labels, not internal tool names. Internal tool names appear in Debug Mode only.

---

### **Session Authorization Tools (Steps 1–3 — Workflow Supervisor)**

**Displayed Step Label:** "Session & System Verification" (covering verify_session_authorization, check_audit_proxy_reachability, request_vault_credential_injection)

**Before Execution:**
- **Announcement:** "Verifying UM Specialist session identity..." / "Confirming audit logging system availability..." / "Initiating secure credential delivery..."
- **Parameters Shown:** Case ID, Specialist ID (from session initiation form — specialist sees their own identity reflected back). Session token is never displayed after form submission.
- **User Approval:** Not required.

**During Execution:**
- **Status Indicator:** Animated pulsing dot with step label. Each sub-step (session auth, proxy check, vault injection) shown sequentially as individual status lines.
- **Estimated Duration:** Not shown — these are fast operations. If any step exceeds 5 seconds, a "Still verifying..." message replaces the default indicator.
- **Cancellation:** Emergency Stop only.

**After Execution:**
- **Success Display:** Each sub-step shows a success status indicator. Session authorization log reference is shown (log_ref identifier, not contents). Audit proxy reachability is confirmed. Credential injection shows "Credential delivery: Confirmed" — no credential values displayed.
- **Output Visibility:** Session authorization log reference (non-PHI metadata only). Credential: confirmation only.
- **Output Format:** Three status lines with icons within the step card.

**Failure Display:**
- verify_session_authorization failure: Emergency Stop banner. "Session authorization failed — workflow halted. Case placed in suspended state. UM Department Manager has been notified. Explicit restart authorization required." Condition named: "Identity verification failure."
- check_audit_proxy_reachability failure: Emergency Stop banner. "Audit logging system unreachable — workflow halted. PHI processing cannot proceed without confirmed audit logging. UM Department Manager has been notified."
- request_vault_credential_injection failure: Emergency Stop banner. "Secure credential delivery failed — workflow halted. UM Department Manager has been notified."
- **Retry Option:** No retry on any of these tools — all failures are immediate Emergency Stop per cognitive spec.

---

### **Document Processing Tools (Step 4 — Document Processing Agent)**

**Displayed Step Label:** "Document Retrieval & Field Extraction"

**Before Execution:**
- **Announcement:** "Retrieving fax document from secure intake source..." then "Parsing document pages..." then "Extracting required fields..."
- **Parameters Shown:** Case ID, intake source reference label (not the source URL or path).
- **User Approval:** Not required.

**During Execution:**
- **Status Indicator:** Sequential status lines for: retrieve → parse → extract → audit log confirmation.
- **Estimated Duration:** Not shown for individual operations. If retrieve_fax_document exceeds 15 seconds without response, "Retrieval taking longer than expected — still in progress..." is shown.
- **Cancellation:** Emergency Stop only.

**After Execution:**
- **Success Display:** Inline summary card: "Document retrieved — [N] pages. Extraction complete. [N] fields extracted. [N] PHI fields audit-logged." If extraction_completeness = true: "Extraction complete — all required fields extracted." If extraction_completeness = false: Warning-level display listing count of missing_required_fields, illegibility_flags, and structural_complexity_flags (by category, not by PHI value).
- **Output Visibility:** Extraction completeness status, flag counts by type, structural complexity flag types (e.g., "1 conflicting Level of Care signal detected"). Field names that are flagged as missing or illegible are shown (not their values).
- **Output Format:** Summary card with expandable flag detail. PHI field values never shown.

**Failure Display:**
- retrieve_fax_document permanent failure: "Document retrieval failed after 3 attempts. Case halted. UM Department Manager notified." Retry option: not available (permanent failure).
- write_phi_audit_log failure (during extraction): Emergency Stop. "PHI audit logging system returned an error during field extraction. All processing halted. No PHI was accessed without confirmed logging."
- parse_document_ocr_vision permanent failure: "Document parsing failed permanently. Illegibility flags set for all affected pages. Extraction will reflect missing required fields."

---

### **Criteria Evaluation Tools (Step 5 — Criteria Evaluation Agent)**

**Displayed Step Label:** "Criteria Evaluation & Routing Determination"

**Before Execution:**
- **Announcement:** "Querying payer configuration..." then "Applying Interqual criteria matching..." then "Evaluating all seven whitelist conditions..."
- **Parameters Shown:** Payer ID (non-PHI metadata). PHI fields accessed during matching are shown only as a count ("Evaluating [N] clinical data fields").
- **User Approval:** Not required.

**During Execution:**
- **Status Indicator:** Three sequential sub-steps with status indicators.
- **Cancellation:** Emergency Stop only.

**After Execution:**
- **Success Display:** Full seven-condition table (always visible, never collapsible). Each row: Condition label (A through G), Pass/Fail status, plain-language reason. Routing determination shown above table with high visual prominence: "ROUTING DECISION: Mode A — Autonomous Execution" or "ROUTING DECISION: Mode B — Specialist Review Required."
- **Payer config unreachable:** "Payer configuration table unreachable after 3 attempts. Condition F: FAILED. Routing decision: Mode B (automatic)." Shown as a named failure within the condition table — not hidden.
- **Output Format:** Structured table. Escalation reason codes shown verbatim as the reason text for each failed condition.

**Failure Display:**
- query_payer_config_table permanent failure: Condition F marked FAILED. Mode B forced. Named in condition table.
- apply_interqual_matching permanent failure: Emergency Stop not triggered — this is a permanent failure that halts case, reported to Workflow Supervisor. Display: "Criteria matching failed permanently. Case halted. UM Manager notified."
- evaluate_whitelist_conditions failure: Defaults to Mode B per cognitive spec. Display: "Evaluation tool failure — defaulting to Mode B as a safety measure. Escalation reason: evaluation_tool_failure."
- write_phi_audit_log failure: Emergency Stop.

---

### **Mode Routing Audit & SLA Registration (Step 6 — Workflow Supervisor)**

**Displayed Step Label:** "Routing Logged & SLA Monitoring Initiated"

**Before Execution:**
- **Announcement:** "Logging routing decision to audit record..." then "Registering case with SLA monitor..."
- **Parameters Shown:** Case ID, mode assigned (Mode A or Mode B), routing audit log reference label.
- **User Approval:** Not required.

**After Execution:**
- **Success Display:** "Routing decision logged. SLA monitoring active — [elapsed time] of 72 hours elapsed." SLA counter begins in the header.
- **Failure Display:** write_routing_audit_log failure: "Routing audit log write failed. Case halted." register_case_sla failure: "SLA registration failed. UM Manager notified — monitoring gap is a compliance risk."

---

### **Mode A Execution Tools (Step 7A — Data Entry Agent)**

**Displayed Step Label:** "Autonomous Data Entry & Authorization Submission"

**Before Execution:**
- **Announcement:** "Authenticating to payer portal and McKesson..." then "Populating non-clinical fields..." then "Validating portal-McKesson field parity..." then "Submitting authorization request..."
- **Parameters Shown:** Portal name (not portal URL or session token). McKesson session label. Field counts ("[N] fields to be populated"). No PHI values shown.
- **User Approval:** Not required for Mode A.

**During Execution:**
- **Status Indicator:** Four sequential sub-steps: Authenticate → Populate → Validate Parity → Submit.
- **Parity validation mid-point:** "Parity check in progress — confirming portal and McKesson field consistency..."
- **Cancellation:** Emergency Stop only.

**After Execution:**
- **Success Display:** "Authorization submitted. Submission reference: [submission_ref]. Portal confirmed receipt." Parity confirmation shown: "Field parity confirmed — all fields match between portal and McKesson."
- **Output Visibility:** Submission reference ID. Field count written to each system. Parity confirmation indicator. Submission timestamp.
- **Output Format:** Inline success card within step 7A.

**Failure Display:**
- prepopulate_portal_fields clinical field rejection: Emergency Stop. "Prohibited action detected: attempt to write a clinical necessity field to the portal. System halted. UM Manager notified."
- validate_field_parity failure (parity_confirmed = false): "Parity validation failed — field mismatch detected between portal and McKesson. Mismatched field names: [list of field names, no PHI values]. Submission blocked. Case halted. UM Manager notified."
- submit_authorization_request rejection: "Authorization submission rejected by portal. Case halted. UM Manager notified. Reason: [portal_response — shown if non-PHI]."
- authenticate_portal_session or authenticate_mckesson_session permanent failure: "Portal/McKesson authentication failed after 3 attempts. Case halted. UM Manager notified."
- write_phi_audit_log failure at any sub-step: Emergency Stop.

---

### **Mode B Handoff & Approval Gate (Step 7B — Workflow Supervisor + Specialist Action)**

**Displayed Step Label:** "Specialist Review Required" (prominent interrupt state)

**Interface state on Mode B activation:**
The workflow timeline transitions to a dedicated full-panel Mode B Review state. This is not a modal — it replaces the center panel as the primary interaction surface. The panel persists until the specialist submits a logged action. The Activity Log sidebar continues to update (SLA counter, any background events).

**Before Execution:**
- **Announcement:** "Assembling Full Recommendation Package..." then "Delivering to specialist dashboard..."
- **Parameters Shown:** Package assembly confirmation. No PHI values in the announcement — the package itself contains structured clinical summary (displayed within the review panel).

**Approval Panel Contents (Full Recommendation Package — never collapsed):**
- Case ID and case metadata (non-PHI header fields).
- Interqual criteria set matched and match_type (exact / partial / ambiguous / no_match).
- All seven whitelist condition results with pass/fail and reason.
- Escalation reason codes — shown verbatim.
- Structured clinical summary (derived from extraction payload — PHI values shown within the authenticated specialist session only, subject to existing PHI display policy of the surrounding application).
- Pre-populated non-clinical fields confirmed in portal and McKesson (field names and values confirmed as written — non-PHI fields only).
- Criteria-based recommendation (single, specific — as assembled by assemble_recommendation_package).
- Explicit statement: "This package does not include a clinical necessity determination. The specialist retains full clinical authority."

**User Approval Options:**
- **Approve:** Confirms the agent's pre-populated fields and recommendation. Requires explicit button click — passive non-response is not approval.
- **Modify:** Opens a structured field editor for non-clinical fields. Requires rationale text (minimum 1 character — field cannot be submitted empty). Triggers update_fields_post_specialist_action in the agent.
- **Override:** Logs that the specialist's clinical determination supersedes the agent's recommendation. Requires rationale text. Triggers override log, field update, and case closure without resubmission attempt by the agent.

**Timeout:** None — the system waits indefinitely for specialist action per cognitive spec. The SLA Monitor continues tracking elapsed time and will surface SLA alerts (48h, 60h, 66h) as banner interrupts within the review panel.

**Suspension State Communication:** The header badge changes to "AWAITING SPECIALIST ACTION" with an elapsed time indicator. The Activity Log entry reads: "Case suspended — awaiting specialist action. awaiting_human_action = true."

**Rejection Handling:**
- Override action: Display "Specialist override logged. Case closed with override notation. No resubmission will be attempted." The override rationale is shown in the Activity Log.

---

### **PHI Audit Logging (write_phi_audit_log — background, all PHI-touching steps)**

**Display Format:** Not surfaced as individual tool calls in the default view. Each step card that involves PHI interactions shows an aggregate audit confirmation: "PHI audit logging: [N] fields confirmed" with a confirmation indicator. If write_phi_audit_log fails at any call: immediate Emergency Stop banner, workflow halted.

**Failure Display:** Emergency Stop — "PHI audit logging system returned an error. PHI field [field_name — not value] was not processed without confirmed audit logging. All workflow processing halted. UM Department Manager notified. Explicit restart authorization required."

---

### **SLA Monitor Tools (parallel — SLA Monitor Agent)**

**Display Format:** The SLA Monitor runs in parallel — its alerts appear as banner interrupts in the header and within the Mode B review panel (if active), not as step cards in the workflow timeline.

**SLA Threshold Alerts:**
- **48 hours (Standard):** Yellow banner in the specialist's interface. "SLA Alert — Standard: Case [case_id] has been active for 48 hours. CMS 72-hour deadline: 24 hours remaining."
- **60 hours (Critical):** Orange banner. "SLA Alert — Critical: Case [case_id] has been active for 60 hours. 12 hours remaining. UM Department Manager has been notified."
- **66 hours (Code Red):** Red persistent banner. "SLA Code Red: Case [case_id] has been active for 66 hours. 6 hours remaining. Case has been re-routed to High Priority / Any Available Specialist queue. UM Department Manager notified."

**Failure Display:**
- trigger_sla_alert delivery failure: "SLA alert delivery failed for case [case_id] at [threshold]. Retry attempted. If third attempt fails, UM Manager will be notified directly." Shown in Activity Log.
- reroute_to_high_priority_queue failure: "Code Red re-routing failed. UM Manager notified. Manual re-assignment required." Shown as persistent banner.

---

### **Emergency Stop (trigger_emergency_stop — Workflow Supervisor)**

**Display Format:** Full-screen persistent banner interrupting all views. Cannot be dismissed by the specialist.

**Before Execution:** Not applicable — Emergency Stop is immediate.

**After Execution:**
- **Announcement:** "EMERGENCY STOP — All workflow processing halted."
- **Contents:** Trigger condition (plain language), specific constraint violated (verbatim from cognitive spec), action that triggered the stop, all cases currently suspended (case IDs), stop event log reference.
- **User Options:** None until UM Department Manager provides explicit restart authorization through the designated restart channel (outside this interface's scope — interface shows "Awaiting UM Department Manager restart authorization" with no action buttons available to the specialist).

**Restart State:** When restart authorization is received and confirmed, the Emergency Stop banner clears and the interface returns to the suspended case state for the UM Manager's review. Specialists do not initiate restart — the interface reflects the restart state only after authorization is confirmed.

---

### **Case Closure (Step 8 — Workflow Supervisor)**

**Displayed Step Label:** "Case Closure"

**After Execution:**
- **Success Display:** "Case closed. Authorization submission confirmed. Audit log completeness verified. SLA Monitor deregistered. Case status: Closed." Submission reference and closure timestamp shown.
- **Output Format:** Final step card with closure confirmation. Activity Log shows closure event as final entry.

**Failure Display:**
- close_case permanent failure: "Case closure failed. UM Manager notified. Case remains in active state pending manual closure confirmation."

---

**Input/Output Visibility Rules:**

**Always Show:**
- Case ID in all step cards and activity log entries.
- Specialist identity (from verified session) in the header throughout.
- Step outcome status (success, failure, routed-to-human) for every step.
- Whitelist condition results (all 7) in full when Step 5 completes.
- Routing decision (Mode A / Mode B) prominently.
- Escalation reason codes for Mode B.
- Emergency Stop trigger conditions in full.
- SLA elapsed time counter.

**Show on Request (Expandable):**
- Tool call sub-steps within step cards.
- Retry history for transient failures.
- Routing audit log reference IDs.
- Non-PHI tool output parameter values.
- Credential injection confirmation reference.

**Never Show:**
- PHI field values (in any view mode — including Debug Mode).
- Credential values (passwords, API keys, session tokens, vault secrets).
- Raw system prompt text.
- Internal LangGraph shared state schema contents.
- Agent-to-agent orchestration messages.
- Approved integration manifest contents.

**Latency & Waiting States:**

**Short Operations (<2 seconds):** Pulsing status dot with step label only. No explicit duration estimate.

**Medium Operations (2–10 seconds):** Status dot plus plain-language in-progress text (e.g., "Parsing document pages — [N] of [N] pages processed").

**Long Operations (>10 seconds):** Status text updates every 5 seconds with elapsed time (e.g., "Document retrieval in progress — 12 seconds elapsed"). No estimated completion time shown (to avoid false expectations on variable-length operations).

**Stuck/Timeout:** If any tool call produces no response after 30 seconds: "Tool response taking longer than expected — still waiting. Step will halt automatically if no response is received within [timeout threshold]."

**Heartbeat/Liveness Indicators:**
- **Mechanism:** A pulsing status dot on the in-progress step card updates its animation on every SSE event received from the execution graph. If no SSE event is received for 10 seconds during active execution, a static text line appears: "Waiting for agent response..." to reassure the specialist the connection is alive.
- **Purpose:** Distinguish a slow but live operation from a dropped connection. If the SSE stream itself drops, a "Connection lost — attempting to reconnect..." banner replaces the liveness indicator.

**Success vs Failure Representation:**

**Success Indicators:**
- Step card: Green-bordered completion state with a success icon.
- Verbal confirmation in the step summary line: "Session authorized. Audit log reference confirmed."

**Failure Indicators:**
- Step card: Red-bordered or amber-bordered (transient vs permanent) state with an error icon.
- Verbal explanation in the step summary: names the specific tool that failed, the failure type, and the action taken (retry / halt / emergency stop).

**Partial Success:**
- Shown when extraction_completeness = false but extraction proceeded: "Extraction complete with flags — [N] required fields missing, [N] illegibility flags, [N] structural complexity flags. Routing determination will account for incompleteness."

---

## **5. ACTIVITY & AUDIT LOGS**

**Event Types Logged:**

### **Logged Events:**

**User Actions:**
- Session initiated (specialist ID, case ID, session timestamp)
- Emergency Stop triggered by specialist (button press)
- Mode B action submitted: Approve, Modify (with rationale), Override (with rationale)
- Debug Mode enabled/disabled

**Agent Reasoning:**
- Precondition check outcome per step (conditions met / conditions not met — named)
- Workflow phase advancement (step N complete → advancing to step N+1)
- Binary routing decision with basis (mode_a or mode_b, all seven condition results)
- Emergency Stop condition detected (trigger named)
- Out-of-scope case type detected (case_type value logged, action taken)

**Agent Actions:**
- Tool call initiated (plain-language label, step context)
- Tool call completed (success or failure classification)
- PHI audit log confirmed (field count, step context — no field values)
- Credential injection confirmed
- Retry attempt (attempt number, tool label)
- Mode B package assembled and delivered to specialist
- Specialist action received and logged (action_type, log reference)
- SLA alert triggered (alert_level, elapsed_hours)
- Case re-routed to High Priority queue (Code Red)
- Case closed (submission ref, audit log completeness confirmed)

**System Events:**
- Emergency Stop activated (trigger condition, scope, suspended case IDs)
- Circuit breaker activated (system-level — 3 consecutive Emergency Stops within 5 minutes)
- SLA alert delivery failure
- Tool permanent failure (tool label, failure reason)
- UM Manager notification sent
- SSE stream interruption and reconnection

**User-Visible Activity Log:**

**Purpose:** Give the UM Specialist complete transparency into what the agent did, in what order, with what outcome, throughout the session.
**Contents:** All events listed above — high-level and plain-language. Technical event codes appear only in Debug Mode.
**Format:** Chronological timeline in the right sidebar. Each entry: timestamp (absolute + relative), event type badge (Agent Action / User Action / System Event / SLA Event), plain-language description, case ID.
**Access:** Always visible in the right sidebar. Expandable to full-panel view on demand.

**Internal Debug Logs:**

**Purpose:** Technical auditing, troubleshooting, and deep inspection by system administrators or developers.
**Contents:** All user-visible events plus: raw tool names (not plain-language labels), non-PHI tool input parameters, tool output field values (non-PHI subset), LangGraph state section names written per step, retry timing detail (attempt timestamps, backoff durations), schema validation outcomes per field, SSE event stream payloads.
**Format:** Structured JSON entries with full event metadata.
**Access:** Debug Mode toggle in Settings (accessible to system administrators and implementation engineers — not shown in the default specialist interface). PHI field values remain filtered in Debug Mode — this is non-negotiable.

**Timestamping & Trace Structure:**

**Timestamp Format:** Both absolute (e.g., "2:47:03 PM") and relative (e.g., "3 minutes ago") shown for each event. ISO 8601 format used in Debug Mode exports.

**Trace Linking:** Each Activity Log event includes a reference to its parent workflow step (step number) and, in Debug Mode, the tool call name that generated it. Emergency Stop events link to the triggering event's log entry. Mode B specialist actions link to the Mode B package delivery event.

**Session Boundaries:** The Activity Log is scoped to the current case session. Each case session is a discrete log. Prior sessions for the same case_id (if reprocessed after an Emergency Stop) appear as separate session sections with a clear session boundary marker.

**Debug vs Normal User Modes:**

**Normal User Mode (UM Specialist):**
- Shows: All workflow step outcomes, routing decisions, condition results, SLA events, Emergency Stop events, specialist actions, case closure.
- Hides: Raw tool names, LangGraph state key names, tool parameter schemas, retry timing detail, structured JSON payloads.
- Purpose: Full operational transparency without technical overhead.

**Debug Mode (System Administrator / Implementation Engineer):**
- Shows: Everything in normal mode, plus all technical implementation detail listed above (excluding PHI values and credential values, which remain permanently filtered).
- Access: Settings panel toggle, visible only to users with administrator role. Not visible to UM Specialists.
- Purpose: Full observability for system troubleshooting, compliance auditing, and implementation verification.

**Log Retention & Export:**

**Retention:** Per-session Activity Logs are retained for the session duration plus 30 days in the interface layer, after which they are accessible only via the Veea Lobster Trap audit system (outside this interface's scope).

**Export:** Activity Log for a case session is exportable as a structured JSON file or formatted PDF from the Activity Log panel header. Export excludes PHI field values (same filtering as display). Export includes all non-PHI event metadata.

---

## **6. USER FEEDBACK & CONTROL LOOP**

**Interrupt Mechanisms:**

**How User Interrupts Agent:**
- **Emergency Stop Button:** A persistently visible, clearly labeled button in the header bar. Available at all workflow states. Triggers trigger_emergency_stop with scope = "case" (or scope = "system" if the system-level circuit breaker condition is applicable — the scope is determined by the cognitive spec's trigger conditions, not by the specialist).
- **Text Commands:** Not supported — the interface is structured, not conversational. The Emergency Stop button is the only interrupt mechanism.
- **No Pause:** The cognitive spec does not define a pause capability separate from Emergency Stop. There is no pause button.

**What Happens on Interrupt:**
1. trigger_emergency_stop is called immediately. All in-progress tool calls are halted.
2. All active cases for the current system instance are placed in suspended state.
3. Emergency Stop banner displays with full trigger detail.
4. Activity Log entry: "Emergency Stop triggered by specialist [specialist_id] at [timestamp]."
5. UI displays: "Emergency Stop active. All processing halted. Awaiting UM Department Manager restart authorization. No further action is available until restart is authorized."
6. No case state changes are possible from the specialist interface until restart authorization is confirmed.

**Correction Mechanisms:**

**How User Corrects Agent:**
- Corrections are not applicable during workflow execution — the agent executes a deterministic fixed sequence and does not accept mid-execution corrections to its interpretation of case data.
- The only correction mechanism is the Mode B specialist action: the specialist can Modify or Override the agent's pre-populated fields and recommendation. This is the defined correction pathway.
- If the specialist believes the extraction payload contains an error: the appropriate action is Override with a rationale explaining the discrepancy. The agent logs the override and does not dispute it.

**Agent Response to Correction:**
- Modify action: Data Entry Agent calls update_fields_post_specialist_action with the specialist's values, re-validates parity, then submits.
- Override action: Data Entry Agent calls update_fields_post_specialist_action, logs the override with rationale, and stops — no resubmission. Workflow Supervisor closes with override notation.

**Approval / Rejection Mechanisms:**

**Approval UI:**
- **Trigger:** Mode B routing — Step 7B activates when whitelist_determination = "mode_b".
- **Presentation:** Full-panel Mode B Review state replaces the center panel. Not a modal (modals can be dismissed accidentally). The review panel is the primary interface until action is taken.
- **Information Shown:** Complete Full Recommendation Package (all seven fields listed in cognitive spec Section 8 — approval request format). No content is collapsed by default in the review panel.
- **Approval Options:** Three structured buttons: Approve / Modify / Override. Each requires a deliberate action — no defaults pre-selected.
- **Modify and Override Flows:** Both open a confirmation step that requires the specialist to enter a rationale (text field, minimum 1 character, cannot be submitted empty). The specialist sees the action they're about to confirm and its implications before submitting.
- **Timeout:** None — waits indefinitely per cognitive spec.

**Rejection Handling:**
- Override: Display "Override confirmed. Specialist determination logged. Case will be closed with override notation. Authorization will not be resubmitted by the system." Activity Log records: override event, specialist identity, rationale, timestamp, specialist_action_log_ref.
- The word "rejected" is not used in the UI — the cognitive spec defines this as "overridden" (specialist clinical authority supersedes recommendation). UI language mirrors this precisely.

**Regeneration vs Continuation:**

**Regeneration:** Not applicable. The agent does not generate alternative interpretations, competing criteria matches, or multiple recommendation options. The cognitive spec produces exactly one output per step. There is no regeneration concept in a deterministic workflow pipeline.

**Continuation (Post-Emergency-Stop):**
- **Trigger:** UM Department Manager provides explicit restart authorization after an Emergency Stop.
- **Mechanism:** External to the specialist interface — restart authorization is confirmed via the UM Manager's access channel. Once confirmed, the interface reflects the restart authorization and the case returns to suspended state for the UM Manager's decision on how to proceed.
- **Behavior:** The agent does not auto-resume. Human explicit decision is required to continue or discard the suspended case.

**Confidence Signals Shown to User:**

The cognitive spec's agents do not produce probabilistic confidence scores — they produce deterministic binary or categorical outputs (exact/partial/ambiguous/no_match; mode_a/mode_b; true/false). Confidence communication in this interface therefore reflects extraction quality and criteria match quality, not LLM probability scores.

- **High Confidence (extraction_completeness = true, match_type = exact):** No special indicator — step card shows clean success state.
- **Medium Quality (partial match or minor flags):** Step card uses amber styling. Summary line: "Criteria match: Partial — one or more required data fields missing from the extraction payload." Condition A failure named.
- **Low Quality (no_match, significant illegibility, structural complexity):** Step card uses red-amber warning styling. All specific flags and missing fields named in the step card. Route to Mode B is guaranteed in these cases.
- **Ambiguous Config:** When payer_config_reachable = false: "Payer configuration unavailable — Condition F failed. Routing to Mode B as a safety measure." Named explicitly, not softened.

**User Trust Signals:**
- **Thumbs up/down:** Not implemented — specialist feedback on workflow outcomes is out of scope for this processing system. Cases have regulatory dispositions (submitted / overridden / halted), not quality ratings.
- **Explicit Audit Trail:** The Activity Log and Veea Lobster Trap log references serve as the trust mechanism — the specialist can see exactly what the agent did and verify it against the audit record.

---

## **7. AUTONOMY & SAFETY CONTROLS**

**Autonomy Level Indicators:**

**Current Autonomy Display:**
- **Location:** Header bar, always visible.
- **Format:** Text badge: "Semi-Autonomous" (persistent label, reflects the system's defined autonomy level). After routing, the badge updates to show the active path: "Semi-Autonomous — Mode A (Autonomous Execution)" or "Semi-Autonomous — Mode B (Awaiting Specialist Review)".
- **Clarity:** A tooltip on the badge defines: "This system executes standard low-complexity cases autonomously (Mode A). Cases with elevated complexity, cost, acuity, or data quality flags require specialist approval before submission (Mode B)."

**Autonomy Level Settings:**

**Semi-Autonomous (Fixed — Cannot Be Changed by User):**
- **Default State:** Semi-autonomous, enforced by the LangGraph conditional edge architecture. The Mode A / Mode B split is determined by the seven whitelist conditions — it is not a user-selectable setting.
- **User Control:** None — the autonomy architecture is not configurable from the interface. This is communicated to the specialist: "Workflow routing is determined automatically by case characteristics. Specialist review is required for all cases that do not meet the full autonomous execution criteria."
- **Mode Switching:** Not applicable — mode is determined per-case by criteria evaluation outcome, not by user preference.

**Manual Override Mechanisms:**

**Override Controls:**
- **Emergency Stop:** Immediately halts all processing. Always available in the header.
- **Mode B Override:** After reviewing the Full Recommendation Package, the specialist may exercise clinical authority by selecting Override. This does not reprocess the case — it logs the specialist's determination and closes the case.
- **Takeover:** Not applicable — the interface does not provide a mechanism for the specialist to manually operate the agent's tools or impersonate its steps. The specialist's authority is exercised at the Mode B gate and via Emergency Stop.

**Override Availability:**
- Emergency Stop: Available at all times, including during Mode B suspension, during tool execution, and during the Emergency Stop state itself (for scope escalation from case to system).
- Mode B Approve/Modify/Override: Available only when the Mode B gate is active.

**Human-in-the-Loop Trigger Visualization:**

**Approval Gates:**
- The Mode B gate is the system's defined human-in-the-loop checkpoint. Its activation is visually prominent: the full center panel transitions to the Mode B Review state, the header badge updates, and the Activity Log records the suspension event.
- **Pending Approval:** The header badge displays "AWAITING SPECIALIST ACTION" in amber. The Mode B panel has no countdown timer (indefinite wait) but the SLA counter in the header continues incrementing.
- **Approval Request:** The Full Recommendation Package displays all content the specialist needs to make their determination, as defined by the cognitive spec's approval request format.
- **Timeout Warning:** No automatic timeout, but SLA alert banners at 48h, 60h, and 66h appear within the Mode B review panel to signal urgency.

**Escalation States:**

**When Agent Escalates to Human:**
- Mode B routing (criteria-based — any whitelist condition failure).
- Emergency Stop (infrastructure failure, safety violation, prohibited action detected, explicit stop command, circuit breaker).
- SLA Code Red (66 hours — re-routed to high priority queue with UM Manager notification).

**Escalation UI:**
- Mode B: Mode B Review Panel (full panel, persistent, non-dismissible until action taken).
- Emergency Stop: Emergency Stop Banner (full-width persistent, non-dismissible, header-level).
- SLA Code Red: Red persistent SLA banner (visible in all interface states including Mode B panel).

**User Options per Escalation Type:**
- Mode B: Approve / Modify / Override (with rationale).
- Emergency Stop: None for specialist — awaiting UM Manager authorization (UI shows this explicitly).
- SLA Code Red: The specialist is informed that the case has been re-routed. No additional action is required from the specialist unless they are the re-assigned specialist.

**Failure or Escalation States:**

**Agent Failure Display:**
- Tool failure (permanent): Named tool (plain-language label), failure classification, UM Manager notification confirmed.
- Infrastructure failure (Emergency Stop trigger): Full Emergency Stop UI with named trigger condition.
- Prohibited action detected: Emergency Stop UI with specific prohibition named (e.g., "Attempt to write a clinical necessity field to the portal — Prohibition 1 violation").

**Safety Guardrail Activations:**

**When Guardrail Triggers:**
Per cognitive spec — all nine safety guardrails have defined trigger conditions mapped to Emergency Stop or Mode B forced routing.

**User Communication:**
- **Visible:** Always — no guardrail activation is hidden from the specialist.
- **Message Format:** "Safety constraint triggered: [specific constraint name]. Reason: [plain-language explanation]. Action taken: [Emergency Stop / Mode B routing]."
- **Specific vs General:** The specific constraint is named — e.g., "PHI audit logging failure — processing halted per HIPAA compliance requirement" rather than a vague "system error."
- **Clinical Field Rejection (Prohibition 1):** "The system attempted to write a clinical necessity field to the portal. This action is prohibited. Emergency Stop has been triggered. UM Manager notified."
- **Credential Storage Attempt (Prohibition 4):** "A credential storage attempt was detected and blocked. Emergency Stop triggered. UM Manager notified."
- **Baseline Threshold Exceeded (Prohibition 7):** Surfaced as Condition G failure in the whitelist condition table — "Runtime configuration attempted to raise cost threshold above $10,000 baseline. Condition G: FAILED. Routing: Mode B."

---

## **8. ERROR & UNCERTAINTY UX**

**Uncertainty Communication Patterns:**

This system does not produce probabilistic uncertainty — its outputs are binary or categorical. "Uncertainty" in this system manifests as: incomplete extraction (flagged fields), non-exact criteria match, unreachable configuration, or ambiguous match type. Each is communicated with its specific category label, not a generic uncertainty marker.

**No Match / Ambiguous Match (Criteria Evaluation):**
- **Indicator:** Amber-styled step card. Condition A FAILED — named explicitly.
- **Language:** "Criteria matching returned: [match_type]. Exact match required for autonomous execution. Routing to Mode B for specialist review."
- **User Guidance:** The Full Recommendation Package shows the criteria set matched (or not matched) and the specific missing data fields. The specialist uses this information to make a clinical determination.

**Missing Required Fields (Document Processing):**
- **Indicator:** Amber-styled extraction summary card. extraction_completeness = false, missing_required_fields count shown.
- **Language:** "Extraction incomplete — [N] required fields could not be definitively extracted. These fields are flagged as missing in the criteria evaluation. Condition A will evaluate as FAILED."
- **User Guidance:** Field names of missing fields are listed (without values). Specialist may need to obtain the missing clinical information through appropriate channels outside this system.

**Configuration Unavailable:**
- **Language:** "Payer configuration table was unreachable after 3 attempts. Routing threshold data unavailable. Condition F: FAILED. Case automatically routed to Mode B."

**Ambiguity in Specialist Action (N/A):**
Specialist actions are structured button choices — ambiguity is not possible. Rationale text fields are open-form but do not affect the action classification.

**Failure Explanation Approach:**

**What Agent Admits:**
- Specific tool failures with failure type.
- Write_phi_audit_log failures — exact timing of failure and which step was interrupted.
- Parity mismatch — field names that mismatched (not values).
- Criteria match type (partial, ambiguous, no_match) — not softened to "almost matched."
- Routing forced to Mode B due to single condition failure — the specific condition is named.

**What Agent Explains:**
- Why failure occurred: Root cause where determinable (network timeout, authorization denied, document illegible, threshold exceeded).
- What was attempted: Which tool was called, how many retry attempts were made.
- What the specialist can do: Specific recovery options per failure type.

### **Tool-Specific Failure Mapping Table:**

| Tool (Plain-Language Label) | Failure Scenario | User Error Message | Recovery Action (UI) |
|---|---|---|---|
| Session Identity Verification | Identity verification failed | "Session authorization failed — identity not verified in the personnel registry." | No retry. UM Manager notification confirmed. Emergency Stop. Restart authorization required. |
| Session Identity Verification | Network timeout (3 retries exhausted) | "Session authorization system unreachable after 3 attempts." | Emergency Stop. UM Manager notification. Restart authorization required. |
| Audit Logging System Check | Audit proxy unreachable | "Audit logging system unavailable — PHI processing cannot proceed." | Emergency Stop. UM Manager notification. Restart authorization required. |
| Secure Credential Delivery | Vault unreachable | "Secure credential delivery failed — portal authentication cannot proceed." | Emergency Stop. UM Manager notification. Restart authorization required. |
| Fax Document Retrieval | Timeout / temporary unavailability | "Document retrieval taking longer than expected — retrying..." | Auto-retry (up to 3 attempts). If exhausted: "Document retrieval failed. Case halted." UM Manager notified. |
| Fax Document Retrieval | Document not found / access denied | "Document not found at the specified intake source. Case halted." | No retry (permanent). UM Manager notified. Manual investigation required. |
| PHI Audit Logging | Any failure | "PHI audit logging failed — processing halted. No PHI was accessed without confirmed logging." | Emergency Stop (no retry). UM Manager notification. Restart authorization required. |
| Document Parsing (OCR) | Partial illegibility | "Document parsing complete — [N] pages partially illegible. Illegibility flags set." | Continue to field extraction (incompleteness flows to Mode B). No manual retry available. |
| Document Parsing (OCR) | Permanent failure | "Document parsing failed permanently. All pages returned as illegible." | Halt. UM Manager notified. Manual document review required outside system. |
| Payer Configuration Query | Timeout / unavailability (3 retries) | "Payer configuration table unreachable. Using baseline thresholds only. Condition F: FAILED. Routing to Mode B." | No manual retry. Mode B automatic. Specialist reviews case. |
| Interqual Criteria Matching | Permanent tool failure | "Criteria matching system failed permanently. Case halted." | Halt. UM Manager notified. Manual criteria review required outside system. |
| Whitelist Condition Evaluation | Tool failure | "Criteria evaluation tool failed. Defaulting to Mode B as a safety measure." | Mode B automatic. Escalation reason: evaluation_tool_failure. Specialist reviews case. |
| Portal Authentication | Timeout (3 retries exhausted) | "Payer portal authentication failed after 3 attempts. Case halted." | Halt. UM Manager notified. Manual portal access required. |
| McKesson Authentication | Timeout (3 retries exhausted) | "McKesson authentication failed after 3 attempts. Case halted." | Halt. UM Manager notified. |
| Non-Clinical Field Population (Portal) | Clinical field rejection | "Prohibited field detected: system attempted to write a clinical necessity field. Emergency Stop triggered." | Emergency Stop. UM Manager notification. Restart authorization required. |
| Non-Clinical Field Population (Portal) | Transient write failure | "Portal field write failed — retrying..." | Auto-retry (up to 3 attempts). Permanent: Halt. UM Manager notified. |
| Portal-McKesson Parity Validation | Parity mismatch | "Field mismatch between portal and McKesson. Submission blocked. Mismatched fields: [field names]." | Halt (permanent failure). UM Manager notified. Manual reconciliation required. |
| Authorization Submission | Portal rejection | "Authorization submission rejected by the payer portal. Case halted." | Halt. UM Manager notified. Manual submission review required. |
| SLA Alert Delivery | Delivery failure (3 retries) | "SLA alert delivery failed for case [case_id]. UM Manager notified of alert delivery failure." | UM Manager notification. Shown in Activity Log. |
| Case Re-Routing (Code Red) | Re-routing failure | "High Priority queue re-routing failed. UM Manager notified. Manual case re-assignment required." | Persistent red banner. UM Manager manual action required. |
| Case Closure | Closure failure | "Case closure failed. Case remains in active state. UM Manager notified." | Persistent status. UM Manager manual action required. |

**Failure Types:**

### **Tool Failure (Transient)**
- **Message:** "[Tool plain-language label]: Attempting connection — retry [attempt N of 3]..."
- **User Options:** No user action required for transient retries — the system handles automatically. Specialist observes retry progress in the step card.

### **Tool Failure (Permanent)**
- **Message:** "[Tool plain-language label] failed permanently after 3 attempts. Case processing halted. UM Department Manager has been notified."
- **User Options:** Emergency Stop remains available. No further automated action. Manual intervention required per UM Manager direction.

### **PHI Audit Log Failure**
- **Message:** "PHI audit logging returned an error at step [step name]. No PHI was processed after this point. All workflow processing has been halted. UM Department Manager has been notified. Explicit restart authorization is required."
- **User Options:** Emergency Stop already in effect. Awaiting UM Manager restart authorization.

### **Reasoning Failure (Parity Mismatch)**
- **Message:** "Portal and McKesson field values do not match. Authorization submission is blocked. Mismatched fields: [field names — no PHI values]. Case halted. UM Manager notified."
- **User Options:** Manual reconciliation required outside this system. Emergency Stop available if needed.

### **Safety Violation Attempt (Prohibited Action)**
- **Message:** "A prohibited action was detected and blocked: [specific prohibition named, e.g., 'Attempt to write a clinical necessity field to the portal']. Emergency Stop has been triggered. UM Manager notified. No case state was modified as a result of this attempt."
- **User Options:** Awaiting UM Manager restart authorization.

### **Out-of-Scope Case Type**
- **Message:** "This case cannot be processed by this system. Case type '[value]' is outside the defined scope of the Prior Authorization (Concurrent Review) system. An out-of-scope log has been written. This case has been terminated. Please process this request through the appropriate channel."
- **User Options:** No further action in this system. The specialist is informed the log is available for audit purposes.

**Transparency vs Reassurance Balance:**

**Full Transparency When:**
- PHI audit logging fails — exact failure point named, immediate halt communicated.
- Emergency Stop triggers — condition named verbatim.
- Parity mismatch — field names shown.
- Criteria match type is partial, ambiguous, or no_match — exact match type shown.
- Any single whitelist condition fails — that condition named.
- Clinical field write attempt detected — prohibition named.

**Reassurance When:**
- Transient retries — "Retrying — this is normal for temporary connectivity issues. [N] attempt(s) remaining."
- SLA still within safe range — standard SLA alert provides time context ("24 hours remaining") without alarm language.
- Mode B routing is the designed safety pathway — framed as "Specialist review is required for this case" not as a failure: "This case requires your clinical expertise — the system has prepared a complete recommendation for your review."

**Balance Strategy:**
Be precise and honest about every failure and constraint trigger. Never use vague language for safety events. When a condition fails, name it. When a guardrail triggers, state exactly which guardrail and why. Reserve reassuring language for normal operational conditions (transient retries, Mode B routing as designed behavior) and always include a concrete path forward — either automated (retry) or human (UM Manager action, specialist review).

**Trust Preservation Rules:**

**Never:**
- Display a success indicator for a step that involved a temporary failure resolved by retry without showing the retry count ("Success — after 2 retry attempts" not just "Success").
- Soften mode routing language (Mode B is not "pending review" — it is "Specialist Review Required, autonomous execution is not permitted for this case").
- Omit the Emergency Stop trigger condition in favor of a generic "system error."
- Show a parity-confirmed indicator before validate_field_parity has been called and confirmed.
- Indicate that a specialist action has been received when read_specialist_action returned null.

**Always:**
- Show retry count alongside the final success status when retries were needed.
- State which specific condition failed, not just that the routing decision was Mode B.
- Confirm that the UM Manager has been notified when that notification has been sent.
- Show the Emergency Stop log reference so the specialist knows the event has been durably recorded.
- Reflect the exact specialist action taken (Approve / Modify / Override) in the Activity Log with no softening.

**Trust-Building Patterns:**
1. Every workflow step that completes successfully shows a log reference confirming the audit record was written — the specialist can verify the system's claims against the audit trail.
2. Mode B routing is always accompanied by the full reason (all seven condition results) — the specialist is never asked to make a decision without seeing exactly why the system escalated.
3. The Emergency Stop is always available — its presence communicates that the specialist has ultimate authority over the system's operation.

---

## **9. EXPLICIT UI NON-GOALS**

**What the Interface Will NOT Show:**

1. **Raw System Prompt Text for Any Agent**
   - **Reason:** The system prompts are HIPAA-sensitive operational configuration. Exposing them provides no value to the UM Specialist and creates unnecessary surface area for misunderstanding or gaming. System prompt content is auditable through organizational governance processes, not through the live specialist UI.

2. **LangGraph Shared State Schema or Internal State Keys**
   - **Reason:** State keys (e.g., `extraction_payload.structural_complexity_flags`, `current_context.awaiting_human_action`) are implementation-internal. The specialist needs the meaning and outcome, not the data structure. Exposing schema keys would create cognitive overhead with no operational benefit.

3. **Individual PHI Audit Log Calls (write_phi_audit_log per field)**
   - **Reason:** Up to 30+ individual audit log calls may occur per step. Displaying each call individually would overwhelm the UI without adding meaningful transparency — the specialist needs to know that PHI was audit-logged (confirmed), not to track each field-level call. The aggregate confirmation provides the required assurance.

4. **Credential Values, Session Token Values, or API Keys**
   - **Reason:** Security — no exceptions. This applies in all interface modes including Debug Mode. The cognitive spec explicitly prohibits credential storage or logging; the interface must not contradict this by displaying credential values.

5. **PHI Field Values**
   - **Reason:** PHI is displayed only within the secured specialist review context (Mode B Full Recommendation Package) subject to the surrounding application's existing PHI display policy — not exposed in step cards, activity logs, tool call outputs, or debug logs. This is a HIPAA compliance requirement. The interface layer itself does not display PHI values in any status, log, or debug view.

6. **Agent-to-Agent Orchestration Messages or LangGraph Node Graph**
   - **Reason:** Multi-agent coordination (Workflow Supervisor delegating to Document Processing Agent, etc.) is an implementation detail. The specialist sees a unified case workflow, not five separate agents. Surfacing agent names and inter-agent communication would fragment the user's mental model without adding control surface.

7. **Approved Integration Manifest Contents**
   - **Reason:** The manifest of approved portal endpoints is a security and compliance control. Exposing it creates unnecessary information about system boundaries that could be exploited. Specialists are told when a tool call is blocked due to manifest validation, but not what the manifest contains.

8. **Payer Master Configuration Table Raw Contents**
   - **Reason:** The raw payer configuration data (threshold values, routing rules, carve-out logic) is payer-proprietary operational configuration. The specialist sees the output of configuration evaluation (condition results, threshold comparisons) — not the raw configuration table.

9. **SLA Monitor Polling Mechanism or Poll Cycle Timing**
   - **Reason:** The 5-minute poll interval is an implementation detail. The specialist cares about elapsed time and alert thresholds — not the polling architecture. Exposing polling internals creates false precision expectations.

10. **Tool Invocation Manifest Validation Layer Operation**
    - **Reason:** The manifest validation layer blocks unapproved endpoint targets at every tool call. This is a security backstop that operates silently. It is surfaced only when it blocks a specific call (shown as a prohibited action event) — its existence and implementation are not exposed as a visible system component.

11. **Model Assignment Per Agent (Gemini 1.5 Pro vs Gemini 1.5 Flash)**
    - **Reason:** Which LLM model is assigned to which agent is an operational implementation detail with no relevance to the specialist's workflow. It is not actionable by the specialist and should not create differential trust perceptions between agents.

12. **Traditional Dashboard Metrics (Throughput, Tokens, API Cost)**
    - **Reason:** System performance metrics are relevant to system administrators and implementers, not to UM Specialists processing individual cases. Per-session cost caps and token usage are implementation concerns, not specialist-facing information.

**What Will NOT Be Exposed to Users:**

**Internal System Details:**
- LangGraph execution graph topology (node names, edge conditions, graph state schema).
- Model API call details, token counts, context window usage.
- Rate limiting state (portal API token bucket, config query fixed window) — only the consequence of rate limiting (case suspended, UM Manager notified) is shown.
- Orchestration framework internals (LangGraph runtime behavior, state persistence mechanisms).

**Sensitive System Information:**
- Exact safety guardrail implementation logic (e.g., the specific string matching used to detect prohibited field writes).
- The exact conditions that would trigger the system-level circuit breaker beyond what is stated in the Emergency Stop banner.
- Internal agent-to-agent communication payloads.

**What Is Intentionally Abstracted:**

**Technical Implementation:**
- "Querying Interqual criteria database" abstracts apply_interqual_matching — the specialist cares about the match result, not the tool name.
- "Confirming session identity" abstracts verify_session_authorization — the specialist sees their own verification, not the tool call detail.
- "Secure credential delivery confirmed" abstracts the vault injection mechanism — no credential infrastructure detail is exposed.
- "PHI audit logging confirmed for [N] fields" abstracts write_phi_audit_log per-field calls — the compliance outcome is what matters.

**System Complexity:**
- The five-agent architecture is presented as a single unified case workflow. Specialists do not need to know that document processing, criteria evaluation, and data entry are handled by distinct agents.
- The LangGraph interrupt gate mechanism for Mode B is presented as "the system is waiting for your action" — not as an interrupt event in a graph execution framework.

**Abstraction Strategy:**
Use plain-language operational labels that match the specialist's domain vocabulary (session authorization, document processing, criteria evaluation, routing decision, specialist review, submission) rather than technical system vocabulary (LangGraph nodes, tool schemas, agent names). Never use abstraction to hide an error or failure — when something fails, the plain-language label for the failure is shown with specificity. Abstraction applies to mechanism; transparency applies to outcome.

---

## **INTERFACE SYSTEM INTEGRITY DECLARATION**

This interface specification is AUTHORITATIVE.

All downstream systems must:
- Implement the Task-First workflow timeline as the primary interaction surface
- Stream step-by-step workflow progression via SSE per defined granularity
- Display the seven whitelist condition results in full — never collapsed by default
- Show tool call status in real time within each step card per the defined observability rules
- Aggregate PHI audit log calls as a confirmed count indicator — never show individual field audit calls or PHI values
- Present the Mode B Full Recommendation Package as a full-panel, non-collapsible review state
- Require explicit specialist action (Approve / Modify / Override with rationale) before proceeding — passive non-response is never treated as approval
- Maintain the Emergency Stop button in persistent header position at all interface states
- Provide the Activity Log as a chronological, always-visible event record
- Surface SLA alerts as banner interrupts at 48h, 60h, and 66h thresholds
- Communicate Emergency Stop with full trigger condition named — no vague language
- Apply the Tool-Specific Failure Mapping Table exactly as specified for all error states
- Filter PHI field values and credential values in all display modes — including Debug Mode
- Reflect the autonomy level as "Semi-Autonomous" with mode (Mode A / Mode B) shown in the header badge
- Implement WebSocket for the Mode B approval gate bidirectional event (specialist action → graph release)
- Respect all explicit UI non-goals — no exposed system prompts, no LangGraph internals, no credential values, no PHI values in logs

The interface must faithfully reflect the agent cognitive reality defined in AGENT_LOGIC_SPEC.md.
No simplification may hide what the agent actually does.
No embellishment may represent capabilities the agent does not have.

Trust in a HIPAA-regulated autonomous processing system is built through complete transparency about what happened, why it happened, and who authorized it — not through polish or reassurance.

---
