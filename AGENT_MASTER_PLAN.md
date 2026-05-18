# AGENT MASTER PLAN

**Generated:** May 11, 2026
**Source Documents:**
- AGENT_ORCHESTRATION_BLUEPRINT.md
- AGENT_LOGIC_SPEC.md
- INTERFACE_OBSERVABILITY_SYSTEM.md

**Status:** AUTHORITATIVE — Complete execution plan for agent system implementation

---

## **1. EXECUTION PRINCIPLES**

**Technology Stack:**
- **Orchestration Framework:** LangGraph (Python) with PostgreSQL checkpointer
- **Language:** Python 3.12 (backend); TypeScript / React 18 (frontend)
- **Primary Model:** `gemini-2.5-pro` — Document Processing Agent, Criteria Evaluation Agent
- **Secondary Model:** `gemini-2.5-flash` — Workflow Supervisor Agent, Data Entry Agent, SLA Monitor Agent
- **LLM Provider SDK:** `google-generativeai` Python SDK (latest)
- **Backend API Framework:** FastAPI
- **Streaming Protocol:** Server-Sent Events (SSE) for workflow step progress; WebSocket for Mode B bidirectional approval gate
- **Frontend Component Library:** Shadcn/UI with Tailwind CSS
- **State Persistence:** LangGraph PostgreSQL checkpointer (for case state); `asyncpg` driver
- **External Audit Store:** Veea Lobster Trap (pre-existing compliance system; agent writes to it via HTTP API calls)
- **External Credential Store:** Enterprise Secret Vault (pre-existing; agent requests credential injection via HTTP API)
- **External Config Store:** Payer Master Configuration Table (pre-existing; agent queries via HTTP API)
- **SLA Monitor Concurrency:** Python `asyncio` task running as an independent parallel coroutine registered per case
- **Custom Components (must be implemented):**
  - Veea Lobster Trap Proxy Integration Layer (PHI-access decorator)
  - Enterprise Secret Vault Injection Adapter
  - SLA Monitor Parallel Task Manager
  - Tool Invocation Manifest Validation Layer

**Runtime Assumptions:**
- Python 3.12.x installed on the server/container.
- Node.js 20.x LTS installed for frontend build tooling.
- PostgreSQL 15+ instance provisioned and accessible at the connection string defined in environment variables.
- All external systems (Veea Lobster Trap, Enterprise Secret Vault, Payer Master Configuration Table, payer portals, McKesson, UM Specialist registry) are accessible via HTTPS from the deployment environment.
- Veea Lobster Trap, Secret Vault, and Payer Master Config Table are pre-existing — the agent system writes to / queries them; it does not provision them.
- All approved payer portal APIs and McKesson API integrations are pre-configured with approved endpoints listed in the integration manifest.
- The deployment environment supports persistent long-running processes (FastAPI server + background asyncio tasks).

**Explicit Non-Goals:**
- No implementation of the Veea Lobster Trap audit store backend (pre-existing; agent only calls its API).
- No implementation of the Enterprise Secret Vault backend (pre-existing; agent only calls its injection API).
- No implementation of the Payer Master Configuration Table backend (pre-existing; agent only queries its API).
- No implementation of payer portal APIs or McKesson APIs (pre-existing; agent calls their endpoints).
- No database migrations for the Veea Lobster Trap persistent store.
- No implementation of the UM Specialist authentication provider or personnel registry (pre-existing; verify_session_authorization calls this registry).
- No visual design, graphic design, or custom CSS theming beyond Shadcn/UI and Tailwind utility classes.
- No implementation code for clinical necessity determination logic of any kind.
- No cross-case shared memory or agent memory that persists beyond a single case session.
- No outbound communications to providers, members, or any endpoint not in the approved integration manifest.

**Stability Requirements:**
- Every tool call must include input schema validation before execution. Invalid inputs are rejected — not approximated.
- The LangGraph state graph is a directed acyclic graph per case — no cycles in sequential processing steps.
- The PostgreSQL checkpointer must write state at each node boundary before the next node executes.
- Exponential backoff retries (2s, 4s, 8s) apply to transient failures only — three total attempts maximum.
- `write_phi_audit_log` failures are Emergency Stop conditions with no retry.
- `trigger_emergency_stop` followed by no further tool calls from any agent — the graph halts at the emergency stop node.
- The circuit breaker (3 Emergency Stops across different cases within 5 minutes) activates system-level suspension with no self-recovery.
- All baseline thresholds (`baseline_cost_threshold_usd = 10000`, `baseline_los_threshold_days = 5`) are hardcoded constants in the state schema — they cannot be modified at runtime by any tool, instruction, or configuration value.

---

## **2. ENVIRONMENT & INFRASTRUCTURE SETUP**

**Required API Keys & Secrets:**

1. Google Gemini API — `GEMINI_API_KEY` — Obtain from aistudio.google.com — Used by all five agents
2. Veea Lobster Trap — `VEEA_LOBSTER_TRAP_API_KEY` — Obtain from compliance infrastructure team — Used by PHI audit decorator and write_routing_audit_log
3. Veea Lobster Trap — `VEEA_LOBSTER_TRAP_API_ENDPOINT` — Obtain from compliance infrastructure team — Base URL for all audit log writes
4. Enterprise Secret Vault — `SECRET_VAULT_AUTH_TOKEN` — Obtain from security/infrastructure team — Used by vault injection adapter
5. Enterprise Secret Vault — `SECRET_VAULT_ENDPOINT` — Obtain from security/infrastructure team — Base URL for credential injection requests
6. Payer Master Configuration Table — `PAYER_CONFIG_TABLE_API_KEY` — Obtain from payer operations team — Used by query_payer_config_table
7. Payer Master Configuration Table — `PAYER_CONFIG_TABLE_ENDPOINT` — Obtain from payer operations team — Base URL for config queries
8. UM Specialist Registry — `UM_SPECIALIST_REGISTRY_API_KEY` — Obtain from HR/IT — Used by verify_session_authorization
9. UM Specialist Registry — `UM_SPECIALIST_REGISTRY_ENDPOINT` — Obtain from HR/IT — Base URL for identity verification
10. PostgreSQL — `POSTGRESQL_CONNECTION_STRING` — Provision PostgreSQL 15+ instance — Full connection URL (e.g., `postgresql+asyncpg://user:password@host:5432/dbname`)
11. High Priority Queue — `HIGH_PRIORITY_QUEUE_ENDPOINT` — Obtain from UM operations — Used by reroute_to_high_priority_queue
12. UM Manager Notification — `UM_MANAGER_NOTIFICATION_ENDPOINT` — Obtain from UM operations — Used by notify_um_manager and trigger_sla_alert
13. Fax Intake Source — `INTAKE_SOURCE_BASE_URL` — Obtain from document management team — Base URL for retrieve_fax_document
14. Fax Intake Source — `INTAKE_SOURCE_API_KEY` — Obtain from document management team — Auth for fax retrieval

**Required Environment Variables:**

```
GEMINI_API_KEY=<gemini_api_key>

VEEA_LOBSTER_TRAP_API_ENDPOINT=https://<veea_host>/api/v1/audit
VEEA_LOBSTER_TRAP_API_KEY=<veea_api_key>

SECRET_VAULT_ENDPOINT=https://<vault_host>/api/v1/inject
SECRET_VAULT_AUTH_TOKEN=<vault_auth_token>

PAYER_CONFIG_TABLE_ENDPOINT=https://<config_host>/api/v1/payer-config
PAYER_CONFIG_TABLE_API_KEY=<config_api_key>

UM_SPECIALIST_REGISTRY_ENDPOINT=https://<registry_host>/api/v1/verify
UM_SPECIALIST_REGISTRY_API_KEY=<registry_api_key>

POSTGRESQL_CONNECTION_STRING=postgresql+asyncpg://user:password@host:5432/pa_agent_db

HIGH_PRIORITY_QUEUE_ENDPOINT=https://<queue_host>/api/v1/reroute
UM_MANAGER_NOTIFICATION_ENDPOINT=https://<notify_host>/api/v1/notify

INTAKE_SOURCE_BASE_URL=https://<fax_host>/api/v1/documents
INTAKE_SOURCE_API_KEY=<fax_api_key>

APPROVED_INTEGRATION_MANIFEST_VERSION=v1.0.0

BASELINE_COST_THRESHOLD_USD=10000
BASELINE_LOS_THRESHOLD_DAYS=5

PORTAL_API_RATE_LIMIT_PER_MINUTE=30
PAYER_CONFIG_RATE_LIMIT_PER_MINUTE=10

API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_ORIGIN=http://localhost:3000

LOG_LEVEL=INFO
ENVIRONMENT=local
```

**Dependency Installation Order:**

**Step 1:** Create and activate Python virtual environment
```
python3.12 -m venv .venv && source .venv/bin/activate
```
Verification: `python --version` returns `Python 3.12.x`

**Step 2:** Install Python backend dependencies
```
pip install -r requirements.txt
```
`requirements.txt` contents (exact versions):
```
google-generativeai==0.8.3
langgraph==0.3.5
langgraph-checkpoint-postgres==0.2.0
asyncpg==0.30.0
fastapi==0.115.0
uvicorn[standard]==0.32.0
python-dotenv==1.0.1
httpx==0.28.0
pydantic==2.9.0
structlog==24.4.0
pytest==8.3.0
pytest-asyncio==0.24.0
```
Verification: `pip list | grep langgraph` shows `langgraph 0.3.5`

**Step 3:** Install Node.js frontend dependencies
```
cd frontend && npm install
```
`frontend/package.json` dependencies:
```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "lucide-react": "^0.383.0",
    "tailwindcss": "^3.4.0",
    "@shadcn/ui": "latest"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "vite": "^5.2.0",
    "@types/react": "^18.3.0"
  }
}
```
Verification: `cd frontend && npx tsc --version` returns TypeScript version.

**Step 4:** Initialize Tailwind CSS in frontend
```
cd frontend && npx tailwindcss init -p
```
Verification: `frontend/tailwind.config.js` exists.

**Step 5:** Create PostgreSQL database for LangGraph checkpointer
```
createdb pa_agent_db
```
Verification: `psql -d pa_agent_db -c "\dt"` connects without error.

**Project Directory Structure:**

```text
project-root/
├── .env                                    # Active environment variables (never committed)
├── .env.example                            # Template with all variable names, no values
├── requirements.txt                        # Python backend dependencies (pinned versions)
├── src/
│   ├── agents/
│   │   ├── workflow_supervisor.py          # Workflow Supervisor Agent — Gemini 2.5 Flash
│   │   ├── document_processing.py          # Document Processing Agent — Gemini 2.5 Pro
│   │   ├── criteria_evaluation.py          # Criteria Evaluation Agent — Gemini 2.5 Pro
│   │   ├── data_entry.py                   # Data Entry Agent — Gemini 2.5 Flash
│   │   └── sla_monitor.py                  # SLA Monitor Agent — Gemini 2.5 Flash
│   ├── tools/
│   │   ├── verify_session_authorization.py
│   │   ├── check_audit_proxy_reachability.py
│   │   ├── request_vault_credential_injection.py
│   │   ├── write_routing_audit_log.py
│   │   ├── assemble_recommendation_package.py
│   │   ├── notify_human_handoff.py
│   │   ├── read_specialist_action.py
│   │   ├── notify_um_manager.py
│   │   ├── trigger_emergency_stop.py
│   │   ├── close_case.py
│   │   ├── retrieve_fax_document.py
│   │   ├── parse_document_ocr_vision.py
│   │   ├── extract_structured_fields.py
│   │   ├── write_phi_audit_log.py
│   │   ├── write_extraction_to_state.py
│   │   ├── query_payer_config_table.py
│   │   ├── apply_interqual_matching.py
│   │   ├── evaluate_whitelist_conditions.py
│   │   ├── write_evaluation_to_state.py
│   │   ├── receive_vault_credentials.py
│   │   ├── authenticate_portal_session.py
│   │   ├── authenticate_mckesson_session.py
│   │   ├── prepopulate_portal_fields.py
│   │   ├── prepopulate_mckesson_fields.py
│   │   ├── validate_field_parity.py
│   │   ├── submit_authorization_request.py
│   │   ├── update_fields_post_specialist_action.py
│   │   ├── register_case_for_sla_monitoring.py
│   │   ├── get_case_elapsed_times.py
│   │   ├── trigger_sla_alert.py
│   │   ├── reroute_to_high_priority_queue.py
│   │   └── deregister_case_from_monitoring.py
│   ├── graph/
│   │   ├── state_schema.py                 # LangGraph TypedDict shared state schema
│   │   ├── graph_builder.py                # Node definitions, edge wiring, conditional routing
│   │   └── checkpointer.py                 # PostgreSQL checkpointer initialization
│   ├── middleware/
│   │   ├── phi_audit_decorator.py          # Veea Lobster Trap Proxy Integration Layer
│   │   ├── vault_injection_adapter.py      # Enterprise Secret Vault Injection Adapter
│   │   └── manifest_validator.py           # Approved integration manifest validation
│   ├── sla/
│   │   └── sla_monitor_thread.py           # SLA Monitor asyncio parallel task manager
│   ├── api/
│   │   ├── main.py                         # FastAPI application entry point
│   │   ├── routes/
│   │   │   ├── session.py                  # POST /session/initiate endpoint
│   │   │   ├── workflow.py                 # GET /workflow/{case_id}/stream (SSE)
│   │   │   ├── specialist.py               # WS /workflow/{case_id}/action (WebSocket)
│   │   │   └── admin.py                    # POST /admin/emergency-stop, POST /admin/restart
│   │   ├── streaming/
│   │   │   ├── sse_emitter.py              # SSE event emission — step status updates
│   │   │   └── ws_handler.py               # WebSocket — Mode B approval gate
│   │   └── events.py                       # Structured event type definitions (dataclasses)
│   └── utils/
│       ├── retry.py                        # Exponential backoff retry decorator (2s, 4s, 8s)
│       ├── circuit_breaker.py              # System-level circuit breaker (3 stops / 5 min)
│       └── logger.py                       # Structured JSON event logger (structlog)
├── frontend/
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── src/
│       ├── components/
│       │   ├── WorkflowTimeline.tsx        # Center panel — 8-step workflow timeline
│       │   ├── StepCard.tsx                # Individual step card with status and expansion
│       │   ├── ActivityLog.tsx             # Right sidebar — chronological event feed
│       │   ├── ModeBReviewPanel.tsx        # Full-panel Mode B approval interface
│       │   ├── EmergencyStopButton.tsx     # Persistent header emergency stop control
│       │   ├── SLAHeader.tsx               # Header — case ID, mode badge, SLA counter
│       │   ├── SystemBanner.tsx            # Full-width system message banner (ES, SLA alerts)
│       │   └── ConditionTable.tsx          # Seven whitelist condition results table
│       ├── hooks/
│       │   ├── useSSEStream.ts             # SSE connection and event parsing hook
│       │   └── useWebSocket.ts             # WebSocket connection for Mode B gate
│       ├── types/
│       │   └── events.ts                   # Frontend event type definitions
│       ├── pages/
│       │   ├── SessionInit.tsx             # Session initiation form (case ID, specialist ID, token)
│       │   └── CaseWorkflow.tsx            # Primary workflow execution view
│       └── main.tsx                        # React app entry point
├── tests/
│   ├── mocks/
│   │   ├── mock_verify_session_auth_success.json
│   │   ├── mock_verify_session_auth_failure.json
│   │   ├── mock_check_audit_proxy_reachable.json
│   │   ├── mock_check_audit_proxy_unreachable.json
│   │   ├── mock_vault_injection_success.json
│   │   ├── mock_vault_injection_failure.json
│   │   ├── mock_retrieve_fax_document.json
│   │   ├── mock_parse_document_ocr_complete.json
│   │   ├── mock_parse_document_ocr_illegible.json
│   │   ├── mock_extract_fields_complete.json
│   │   ├── mock_extract_fields_incomplete.json
│   │   ├── mock_phi_audit_log_success.json
│   │   ├── mock_phi_audit_log_failure.json
│   │   ├── mock_payer_config_reachable.json
│   │   ├── mock_payer_config_unreachable.json
│   │   ├── mock_interqual_exact_match.json
│   │   ├── mock_interqual_partial_match.json
│   │   ├── mock_interqual_no_match.json
│   │   ├── mock_whitelist_all_pass_mode_a.json
│   │   ├── mock_whitelist_condition_c_fail.json
│   │   ├── mock_whitelist_condition_d_fail.json
│   │   ├── mock_whitelist_condition_e_fail.json
│   │   ├── mock_whitelist_config_exceeds_baseline.json
│   │   ├── mock_prepopulate_portal_success.json
│   │   ├── mock_prepopulate_portal_clinical_field_rejection.json
│   │   ├── mock_field_parity_confirmed.json
│   │   ├── mock_field_parity_mismatch.json
│   │   ├── mock_submit_auth_success.json
│   │   ├── mock_submit_auth_rejected.json
│   │   ├── mock_specialist_action_approved.json
│   │   ├── mock_specialist_action_modified.json
│   │   ├── mock_specialist_action_overridden.json
│   │   └── mock_emergency_stop.json
│   ├── unit/
│   │   ├── test_state_schema.py
│   │   ├── test_phi_audit_decorator.py
│   │   ├── test_manifest_validator.py
│   │   ├── test_retry_logic.py
│   │   ├── test_circuit_breaker.py
│   │   └── test_whitelist_conditions.py
│   ├── integration/
│   │   ├── test_graph_routing.py
│   │   ├── test_mode_a_flow.py
│   │   ├── test_mode_b_flow.py
│   │   ├── test_emergency_stop.py
│   │   ├── test_sla_alerts.py
│   │   └── test_prohibited_actions.py
│   └── e2e/
│       ├── test_full_mode_a.py
│       └── test_full_mode_b.py
└── README.md
```

**File Purpose Explanation:**

`src/agents/`: One file per agent. Each file defines the agent's node function (the callable LangGraph node), system prompt (as a constant string exactly per AGENT_LOGIC_SPEC.md), model assignment, tool manifest, and Graph-Node ReAct reasoning loop.

`src/tools/`: One file per tool (31 total). Each file contains: the tool's JSON schema (exactly per AGENT_LOGIC_SPEC.md Section 4), the tool's execution function (HTTP call to the appropriate external system), input validation, output validation against expected post-conditions, and failure classification.

`src/graph/state_schema.py`: The LangGraph TypedDict defining the exact shared state schema from AGENT_ORCHESTRATION_BLUEPRINT.md Section 2.1, with baseline thresholds hardcoded as constants.

`src/graph/graph_builder.py`: All LangGraph node additions, edge additions, conditional edge routing functions (Mode A / Mode B), interrupt_before declaration for Step 9b node, and subgraph registration for SLA Monitor.

`src/middleware/phi_audit_decorator.py`: The mandatory PHI-access decorator. Wraps every agent node function that accesses PHI fields. Intercepts the PHI access, calls write_phi_audit_log, awaits confirmed receipt, and only permits state mutation to proceed on success. On any failure: calls trigger_emergency_stop.

`src/middleware/vault_injection_adapter.py`: Calls the Secret Vault injection endpoint and delivers credentials to the Data Entry Agent's execution context. Never writes credentials to LangGraph state.

`src/middleware/manifest_validator.py`: Validates all tool call endpoint identifiers against the approved integration manifest version in config state before any tool call executes. Blocks and logs prohibited endpoint targets.

`src/sla/sla_monitor_thread.py`: Manages the SLA Monitor Agent's asyncio task lifecycle — registration, 5-minute polling loop, alert triggering, and deregistration on case closure.

`src/api/events.py`: Dataclass definitions for all SSE and WebSocket event types as specified in INTERFACE_OBSERVABILITY_SYSTEM.md Section 6.

`tests/mocks/`: JSON files containing exact mock responses for each tool. Used to test all agent logic paths without API calls. PHI field values in mocks are synthetic test data only (e.g., `"member_id": "TEST-MEMBER-001"`).

**Local vs Production Distinctions:**

Local (`ENVIRONMENT=local`): Mock tool responses can be substituted for real external API calls via a test mode flag. PostgreSQL runs locally. SSE and WebSocket served on `localhost:8000`. Frontend dev server on `localhost:3000`. Log level: DEBUG.

Production (`ENVIRONMENT=production`): All external APIs are live. PostgreSQL is a managed cloud instance. HTTPS with TLS termination at load balancer. Log level: INFO. CORS restricted to approved frontend origin. No mock substitution permitted.

---

## **3. CORE AGENT RUNTIME CONSTRUCTION**

**Agent Bootstrap Sequence:**

**Step 1:** Initialize LangGraph TypedDict state schema
- **Action:** Define `PACaseState` as a Python TypedDict in `src/graph/state_schema.py`, implementing the exact shared state schema from AGENT_ORCHESTRATION_BLUEPRINT.md Section 2.1. Hardcode `BASELINE_COST_THRESHOLD_USD = 10000` and `BASELINE_LOS_THRESHOLD_DAYS = 5` as module-level constants in this file. The `config` section of the state initializes with these constants at graph invocation.
- **Dependencies:** None — state schema has no external dependencies.
- **Verification:** Instantiate a `PACaseState` dict with all required fields and confirm it matches the schema structure exactly. Confirm that `config.baseline_cost_threshold_usd` cannot be set above 10000 by any runtime value (enforce via Pydantic validator in the schema or explicit comparison logic).

**Step 2:** Initialize PostgreSQL checkpointer
- **Action:** In `src/graph/checkpointer.py`, initialize `AsyncPostgresSaver` from `langgraph-checkpoint-postgres` using `POSTGRESQL_CONNECTION_STRING`. Call `checkpointer.setup()` to create the LangGraph checkpoint tables in the database.
- **Dependencies:** Step 1 (state schema defined); PostgreSQL instance running; `POSTGRESQL_CONNECTION_STRING` env var set.
- **Verification:** `checkpointer.setup()` completes without error. Connect to the PostgreSQL database and confirm LangGraph checkpoint tables exist.

**Step 3:** Initialize Google GenAI SDK clients
- **Action:** In `src/agents/`, initialize two `google.generativeai.GenerativeModel` client instances at module import: `pro_client` (used by Document Processing Agent and Criteria Evaluation Agent) and `flash_client` (used by Workflow Supervisor, Data Entry Agent, SLA Monitor Agent). Both use `GEMINI_API_KEY` via `genai.configure(api_key=os.environ["GEMINI_API_KEY"])`. Model strings are constants: `PRO_MODEL = "gemini-2.5-pro"` and `FLASH_MODEL = "gemini-2.5-flash"`.
- **Dependencies:** `GEMINI_API_KEY` env var set; `google-generativeai` package installed.
- **Verification:** Call `pro_client.generate_content("ping")` — confirm response received without authentication error.

**Step 4:** Implement Veea Lobster Trap Proxy Integration Layer (PHI audit decorator)
- **Action:** In `src/middleware/phi_audit_decorator.py`, implement `@phi_audit_required` as an async decorator factory. The decorator: (1) identifies all PHI field names to be accessed in the wrapped node function (passed as a parameter list to the decorator); (2) calls `write_phi_audit_log` for each PHI field individually before the node function executes any PHI access; (3) awaits confirmed log receipt (`success = true`, `log_ref` non-null) for each field before proceeding; (4) on any `write_phi_audit_log` failure (network error, proxy error, validation error): calls `trigger_emergency_stop` immediately and raises an exception that halts the LangGraph node without committing any state change.
- **Dependencies:** Step 3 (Google GenAI clients); `write_phi_audit_log` tool implementation; `trigger_emergency_stop` tool implementation.
- **Verification:** Unit test with a mock that causes `write_phi_audit_log` to fail — confirm the decorator calls `trigger_emergency_stop` and raises before any PHI state mutation.

**Step 5:** Implement Enterprise Secret Vault Injection Adapter
- **Action:** In `src/middleware/vault_injection_adapter.py`, implement `inject_vault_credentials(session_id: str, target_agent: str) -> bool`. This function: (1) calls the Secret Vault's injection endpoint at `SECRET_VAULT_ENDPOINT` with `SECRET_VAULT_AUTH_TOKEN`; (2) on success: stores credentials in a module-level `_credential_context` dict keyed by `session_id`, accessible only by the Data Entry Agent's node function within the same process execution; (3) never writes credentials to LangGraph state; (4) on failure: returns False (Workflow Supervisor triggers Emergency Stop on False return). The `_credential_context` is cleared on session close or Emergency Stop.
- **Dependencies:** `SECRET_VAULT_ENDPOINT`, `SECRET_VAULT_AUTH_TOKEN` env vars set; `httpx` installed.
- **Verification:** Unit test confirms credentials are stored in `_credential_context`, NOT in any LangGraph state field. Confirm `_credential_context` does not appear in any state snapshot from the PostgreSQL checkpointer.

**Step 6:** Implement Tool Invocation Manifest Validation Layer
- **Action:** In `src/middleware/manifest_validator.py`, implement `validate_endpoint(endpoint_id: str, manifest_version: str) -> bool`. This function: loads the approved integration manifest from a JSON file versioned by `approved_integration_manifest_version` from shared state config; returns True if `endpoint_id` is in the manifest; returns False and logs a prohibited action event if not. All tool execution functions in `src/tools/` call `validate_endpoint` with their target system identifier before making any HTTP request.
- **Dependencies:** Approved integration manifest JSON file present in `src/config/` directory, versioned by `APPROVED_INTEGRATION_MANIFEST_VERSION`.
- **Verification:** Unit test: call `validate_endpoint` with a known-approved endpoint — confirm True. Call with a fabricated endpoint — confirm False and prohibited action event logged.

**Step 7:** Build all 31 tool implementations
- **Action:** For each of the 31 tools defined in AGENT_LOGIC_SPEC.md Sections 3 and 4: implement the tool function in its dedicated file in `src/tools/`. Each tool file contains: (a) the exact JSON schema from Section 4 as a Python dict constant named `SCHEMA`; (b) an async function `execute(params: dict) -> dict` that validates input against the schema, calls `validate_endpoint` (for tools that call external systems), makes the HTTP request to the appropriate external system, validates the response against the expected post-conditions schema, and returns the structured result; (c) failure classification logic per AGENT_LOGIC_SPEC.md Section 5 failure classification table (network timeout / rate limit / 503 → transient; 401 / 403 / 400 / prohibited field → permanent; `write_phi_audit_log` failure → Emergency Stop); (d) retry logic for transient failures (3 attempts, exponential backoff 2s/4s/8s) implemented via the `@with_retry` decorator from `src/utils/retry.py`.
- **Dependencies:** Steps 4–6 complete (decorators, adapters, manifest validator); all `*_ENDPOINT` and `*_API_KEY` env vars set.
- **Verification:** Per tool: call `execute()` with the corresponding mock JSON from `tests/mocks/` — confirm structured output matches expected post-conditions schema. Confirm each tool correctly classifies transient vs permanent failures.

**Step 8:** Define all agent node functions
- **Action:** For each of the five agents, implement the node function in `src/agents/<agent_name>.py`. Each node function: (a) reads required fields from the LangGraph `state` argument; (b) checks all preconditions (per the agent's system prompt reasoning approach in AGENT_LOGIC_SPEC.md); (c) calls the designated tools in the defined sequence using the tool's `execute()` function; (d) validates each tool result against expected post-conditions before proceeding to the next tool call; (e) writes results to the designated state section via LangGraph state return dict; (f) writes a `task_history` entry for each completed tool call. The system prompt for each agent is defined as a string constant in the agent file, exactly matching AGENT_LOGIC_SPEC.md Section 1. The `@phi_audit_required` decorator is applied to `document_processing_node`, `criteria_evaluation_node`, and `data_entry_node` with the respective PHI field lists.
- **Dependencies:** Step 7 complete (all tools implemented); Step 4 complete (PHI decorator); state schema from Step 1.
- **Verification:** For each agent node: invoke the node function with a mock state dict containing the required input fields (using mock tool responses) — confirm the node returns a correctly structured state update dict and task_history entry.

**Step 9:** Wire LangGraph state graph
- **Action:** In `src/graph/graph_builder.py`, define the complete LangGraph `StateGraph(PACaseState)` with: (a) `add_node()` for each of the eight sequential processing nodes (session_auth, proxy_check, credential_injection, document_processing, criteria_evaluation, mode_routing, mode_a_execution, mode_b_handoff) plus the emergency_stop node and case_closure node; (b) `add_edge()` for sequential connections (START → session_auth → proxy_check → credential_injection → document_processing → criteria_evaluation → mode_routing); (c) `add_conditional_edges()` from `mode_routing` using the routing function: `if state["criteria_evaluation"]["whitelist_determination"] == "mode_a": return "mode_a_execution" else: return "mode_b_handoff"`; (d) `interrupt_before=["mode_b_specialist_action"]` for the Mode B human approval gate node — this is the LangGraph interrupt that suspends execution at Step 9b until a specialist action event is delivered externally; (e) emergency stop branches as conditional edges from every node (check `state["current_context"]["active_mode"] == "suspended"` → route to emergency_stop_node); (f) `compile(checkpointer=postgres_checkpointer)` to produce the compiled graph.
- **Dependencies:** Step 8 complete (all agent nodes defined); Step 2 complete (checkpointer initialized).
- **Verification:** Call `graph.get_graph().draw_mermaid()` and confirm the graph structure matches the execution flow diagram in AGENT_ORCHESTRATION_BLUEPRINT.md Section 3. Confirm `interrupt_before` is set on the Mode B specialist action node. Confirm no cycles exist in the sequential processing path.

**Step 10:** Implement SLA Monitor parallel task manager
- **Action:** In `src/sla/sla_monitor_thread.py`, implement the SLA Monitor as an asyncio-based parallel task manager: (a) `register_case(case_id: str, intake_timestamp: str, assigned_specialist_id: str)` — adds the case to the active monitoring dict and starts an asyncio task for this case; (b) the monitoring task runs a loop: calls `get_case_elapsed_times()` every 300 seconds (5 minutes); checks thresholds (48h, 60h, 66h); calls `trigger_sla_alert` at each threshold exactly once per case per threshold (track `alert_48h_triggered`, `alert_60h_triggered`, `alert_66h_triggered` flags); calls `reroute_to_high_priority_queue` at 66h after `trigger_sla_alert` confirms delivery; (c) `deregister_case(case_id: str)` — cancels the asyncio task for that case_id and removes it from the active monitoring dict; (d) the SLA Monitor's asyncio event loop is initialized and started within the FastAPI startup event handler.
- **Dependencies:** Step 7 complete (SLA monitor tools implemented); FastAPI app initialization.
- **Verification:** Unit test: register a mock case with `intake_timestamp` set to 47 hours ago. Advance the mock clock to 48 hours. Confirm `trigger_sla_alert` is called with `alert_level = "standard"`. Confirm alert is not triggered a second time at the next poll.

---

## **4. TOOL INTEGRATION PLAN**

**Tool Registration Sequence:**

Tools are not registered with LangGraph directly — they are imported and called explicitly within agent node functions. The registration order is the import order in each agent file. The following defines the implementation and wiring order.

---

**Tool Group 1: Workflow Supervisor Tools**
*Implement in this order — each is called sequentially in Steps 1–3 and 6–8.*

**Tool 1: verify_session_authorization**
- Purpose: Validates UM Specialist identity; writes session auth event to Veea Lobster Trap.
- Schema Location: `src/tools/verify_session_authorization.py` — `SCHEMA` constant.
- Dependencies: `UM_SPECIALIST_REGISTRY_ENDPOINT`, `UM_SPECIALIST_REGISTRY_API_KEY`, `VEEA_LOBSTER_TRAP_API_ENDPOINT`, `VEEA_LOBSTER_TRAP_API_KEY`.
- Failure Handling: `verified = false` → permanent failure → Emergency Stop (no retry). Network error → retry 3x → Emergency Stop on third failure.
- Verification: Mock with `mock_verify_session_auth_success.json` — confirm `verified = true` and `authorization_log_ref` non-null returned. Mock with `mock_verify_session_auth_failure.json` — confirm Emergency Stop trigger path reached.

**Tool 2: check_audit_proxy_reachability**
- Purpose: Pings Veea Lobster Trap; confirms it is accepting writes.
- Dependencies: `VEEA_LOBSTER_TRAP_API_ENDPOINT`, `VEEA_LOBSTER_TRAP_API_KEY`.
- Failure Handling: `reachable = false` → Emergency Stop immediately (no retry).
- Verification: Mock with `mock_check_audit_proxy_unreachable.json` — confirm Emergency Stop is triggered.

**Tool 3: request_vault_credential_injection**
- Purpose: Instructs Secret Vault to inject credentials to Data Entry Agent context.
- Dependencies: Vault Injection Adapter (`src/middleware/vault_injection_adapter.py`).
- Failure Handling: Injection failure → Emergency Stop (no retry).
- Verification: Mock injection success — confirm `injection_success = true` and NO credential value appears in shared state. Mock failure — confirm Emergency Stop.

**Tool 4: write_routing_audit_log**
- Purpose: Logs routing decision (mode, condition results, session identity) to Veea Lobster Trap.
- Dependencies: `VEEA_LOBSTER_TRAP_API_ENDPOINT`, `VEEA_LOBSTER_TRAP_API_KEY`.
- Failure Handling: Transient → retry 3x. Permanent → log to error_logs; notify UM Manager.
- Verification: Confirm log_ref returned and non-null. Confirm no PHI field values appear in the log payload.

**Tool 5: assemble_recommendation_package**
- Purpose: Compiles Full Recommendation Package for Mode B specialist review.
- Dependencies: `criteria_evaluation` and `extraction_payload` sections of shared state.
- Failure Handling: Transient → retry 3x. Permanent → Permanent Failure Protocol.
- Verification: Mock with complete criteria_evaluation state — confirm all seven Full Recommendation Package fields present in output. Confirm no clinical necessity determination field in output.

**Tool 6: notify_human_handoff**
- Purpose: Delivers Full Recommendation Package to assigned UM Specialist's dashboard.
- Dependencies: UM Specialist dashboard notification endpoint (in approved integration manifest).
- Failure Handling: Transient → retry 3x. Permanent → Permanent Failure Protocol.
- Verification: Confirm `notification_delivered = true` returned.

**Tool 7: read_specialist_action**
- Purpose: Checks whether specialist has submitted a logged action. Returns null if none.
- Dependencies: LangGraph shared state `current_context.specialist_action` field.
- Failure Handling: Returns null → Workflow Supervisor continues waiting (does NOT proceed). Do not proceed on null.
- Verification: Mock with null return — confirm Workflow Supervisor does not advance graph. Mock with action object — confirm Workflow Supervisor advances to Step 10b.

**Tool 8: notify_um_manager**
- Purpose: Alerts UM Department Manager on permanent failure or Emergency Stop.
- Dependencies: `UM_MANAGER_NOTIFICATION_ENDPOINT`.
- Failure Handling: Transient → retry 3x. Permanent delivery failure → write to error_logs in shared state; await human discovery.
- Verification: Mock delivery success — confirm `notification_delivered = true`.

**Tool 9: trigger_emergency_stop**
- Purpose: Halts all workflow processing; places cases in suspended state; awaits human restart.
- Dependencies: `VEEA_LOBSTER_TRAP_API_ENDPOINT` (for stop event logging).
- Failure Handling: If `trigger_emergency_stop` itself fails: write stop event to `error_logs` in shared state; halt all tool invocations from all agents immediately.
- Critical Constraint: No tool call may follow `trigger_emergency_stop` from any agent. Enforce by raising a `WorkflowHaltedException` after this tool executes, caught by the graph executor to terminate node execution.
- Verification: Confirm `stop_confirmed = true` and `suspended_cases` list populated. Confirm no subsequent tool calls are made after trigger.

**Tool 10: close_case**
- Purpose: Sets case status to closed; confirms audit log completeness; notifies SLA Monitor.
- Dependencies: `submission_confirmation_ref` in artifacts; complete audit log confirmed.
- Failure Handling: Transient → retry 3x. Permanent → log failure; notify UM Manager.
- Verification: Confirm case status set to `closed` in shared state. Confirm SLA Monitor deregistration triggered.

---

**Tool Group 2: Document Processing Agent Tools**
*Implement in this order — sequential per agent execution.*

**Tool 11: retrieve_fax_document**
- Purpose: Retrieves fax document package from designated secure intake source.
- Dependencies: `INTAKE_SOURCE_BASE_URL`, `INTAKE_SOURCE_API_KEY`; `intake_source_ref` from shared state.
- Failure Handling: Transient → retry 3x with exponential backoff. Permanent → halt; report to Workflow Supervisor.
- Verification: Mock with `mock_retrieve_fax_document.json` — confirm `document_pages` array non-empty, `source_document_ids` non-empty.

**Tool 12: parse_document_ocr_vision**
- Purpose: Applies OCR and vision parsing to retrieved document pages.
- Dependencies: Gemini 2.5 Pro's native multimodal long-context vision capability (called via `pro_client.generate_content()` with inline image parts for each page).
- Failure Handling: Transient → retry 3x. Permanent or all pages illegible → set `extraction_completeness = false`; populate `illegibility_flags`; continue to `extract_structured_fields`.
- Verification: Mock with `mock_parse_document_ocr_complete.json` — confirm `parsed_content` returned per page with confidence scores. Mock with illegible document — confirm `illegibility_flags` populated.

**Tool 13: extract_structured_fields**
- Purpose: Extracts all required clinical and administrative data fields from parsed content.
- Dependencies: Gemini 2.5 Pro (structured output extraction); `write_phi_audit_log` confirmed for all PHI fields before execution (enforced by `@phi_audit_required` decorator).
- Failure Handling: Transient → retry 3x. Permanent → halt; report to Workflow Supervisor. Never approximate missing fields.
- Verification: Mock with `mock_extract_fields_complete.json` — confirm `extracted_fields` populated, `extraction_completeness = true`, empty `missing_required_fields`. Mock with `mock_extract_fields_incomplete.json` — confirm `extraction_completeness = false`, non-empty `missing_required_fields`.

**Tool 14: write_phi_audit_log**
- Purpose: Writes field-level PHI interaction record to Veea Lobster Trap before any PHI access.
- Dependencies: `VEEA_LOBSTER_TRAP_API_ENDPOINT`, `VEEA_LOBSTER_TRAP_API_KEY`; `session_id`, `specialist_id` from shared state session section.
- Critical Constraint: Called once per PHI field, not once per document or batch. Called by Document Processing, Criteria Evaluation, and Data Entry agents. `write_phi_audit_log` failure → Emergency Stop (no retry — this is the only tool with this classification).
- Verification: Confirm `log_ref` non-null and `success = true`. Mock failure → confirm Emergency Stop triggered immediately, no retry attempted, no PHI state mutation committed.

**Tool 15: write_extraction_to_state**
- Purpose: Writes complete structured extraction payload to `extraction_payload` section of LangGraph shared state.
- Dependencies: All PHI fields confirmed audit-logged. Only called after all field-level `write_phi_audit_log` calls confirmed.
- Failure Handling: Transient → retry 3x. Permanent → halt; report to Workflow Supervisor.
- Verification: Confirm `extraction_payload` section of shared state contains all expected fields after call.

---

**Tool Group 3: Criteria Evaluation Agent Tools**

**Tool 16: query_payer_config_table**
- Purpose: Retrieves payer-specific thresholds, routing rules, and carve-out logic at runtime.
- Dependencies: `PAYER_CONFIG_TABLE_ENDPOINT`, `PAYER_CONFIG_TABLE_API_KEY`; `payer_id` from extraction payload.
- Rate Limit: 10 queries per minute per agent instance (fixed window). Implement in the tool's execute function.
- Failure Handling: Transient → retry 3x. After third failure OR null/ambiguous result: set `payer_config_reachable = false` in shared state; continue — Condition F fails; `whitelist_determination = mode_b`.
- Verification: Mock with `mock_payer_config_reachable.json` — confirm config data returned. Mock with `mock_payer_config_unreachable.json` — confirm `payer_config_reachable = false` set; graph continues without Emergency Stop.

**Tool 17: apply_interqual_matching**
- Purpose: Identifies the single most specific matching Interqual criteria set in literal read-only mode.
- Dependencies: Gemini 2.5 Pro (criteria matching); `write_phi_audit_log` confirmed for PHI fields accessed during matching.
- Failure Handling: Transient → retry 3x. Permanent → halt; report to Workflow Supervisor (not Emergency Stop).
- Verification: Mock with `mock_interqual_exact_match.json` — confirm `match_type = "exact"`, `missing_data_fields` empty. Mock with `mock_interqual_partial_match.json` — confirm `match_type = "partial"`, Condition A will fail.

**Tool 18: evaluate_whitelist_conditions**
- Purpose: Evaluates all seven whitelist conditions simultaneously; returns `whitelist_determination`.
- Dependencies: Results of `apply_interqual_matching` and `query_payer_config_table`; baseline threshold constants from state config section.
- Critical Constraint: If any runtime config threshold exceeds baseline: set `runtime_config_exceeds_baseline = true`; Condition G = failed; never apply the elevated runtime value. Baseline values are compared from the hardcoded constants, not from any runtime source.
- Failure Handling: Tool failure → retry 3x. Permanent → default `whitelist_determination = "mode_b"`; `escalation_reason_code = "evaluation_tool_failure"`.
- Verification: Mock with `mock_whitelist_all_pass_mode_a.json` — confirm `all_conditions_met = true`, `whitelist_determination = "mode_a"`. Mock with `mock_whitelist_condition_d_fail.json` (ICU acuity flag) — confirm `whitelist_determination = "mode_b"`. Mock with `mock_whitelist_config_exceeds_baseline.json` — confirm Condition G fails and baseline value is used, not the elevated runtime value.

**Tool 19: write_evaluation_to_state**
- Purpose: Writes complete criteria evaluation result to `criteria_evaluation` section of shared state.
- Dependencies: All seven conditions evaluated; `whitelist_determination` non-null.
- Failure Handling: Transient → retry 3x. Permanent → halt; report to Workflow Supervisor.
- Verification: Confirm `criteria_evaluation` section of shared state matches the evaluation result exactly.

---

**Tool Group 4: Data Entry Agent Tools**

**Tool 20: receive_vault_credentials**
- Purpose: Receives runtime-injected credentials into Data Entry Agent execution context.
- Dependencies: Vault Injection Adapter `_credential_context` populated by `request_vault_credential_injection` (Step 3).
- Failure Handling: Any failure → Emergency Stop (no retry).
- Verification: Confirm `credential_injection_confirmed = true`. Confirm no credential value appears in shared state or any log.

**Tool 21: authenticate_portal_session**
- Purpose: Establishes authenticated session with target payer portal. Returns `session_token_ref`.
- Dependencies: `receive_vault_credentials` confirmed. Portal endpoint in approved integration manifest (manifest_validator called first).
- Failure Handling: Transient → retry 3x. Permanent → halt; report to Workflow Supervisor.
- Verification: Confirm `auth_success = true`, `session_token_ref` non-null.

**Tool 22: authenticate_mckesson_session**
- Purpose: Establishes authenticated session with McKesson. Returns `mckesson_session_ref`.
- Dependencies: `receive_vault_credentials` confirmed. McKesson endpoint in approved integration manifest.
- Failure Handling: Transient → retry 3x. Permanent → halt; report.
- Verification: Confirm `auth_success = true`, `mckesson_session_ref` non-null.

**Tool 23: prepopulate_portal_fields**
- Purpose: Writes batch of non-clinical fields to payer portal. Clinical fields blocked by field_type enforcement layer (implemented as a validation function within this tool's `execute()` that checks field names against a versioned clinical field list — if any clinical field is present, the call fails with `prohibited_field_rejected = true`).
- Dependencies: Portal session authenticated. `write_phi_audit_log` confirmed for all PHI fields in batch.
- Failure Handling: Clinical field rejection → Emergency Stop immediately. Transient write failure → retry 3x. Permanent → halt; report.
- Rate Limit: 30 portal API calls per minute per session (token bucket). Implement in the tool's execute function. If queue backlog exceeds 60 seconds: suspend case; notify UM Manager.
- Verification: Mock with `mock_prepopulate_portal_success.json` — confirm `fields_written` list and `prohibited_field_rejected = false`. Mock with `mock_prepopulate_portal_clinical_field_rejection.json` — confirm Emergency Stop triggered.

**Tool 24: prepopulate_mckesson_fields**
- Purpose: Writes batch of non-clinical fields to McKesson. Same clinical field enforcement as Tool 23.
- Dependencies: McKesson session authenticated. `write_phi_audit_log` confirmed for all PHI fields in batch.
- Failure Handling: Same as Tool 23.
- Verification: Same pattern as Tool 23.

**Tool 25: validate_field_parity**
- Purpose: Compares fields written to portal vs McKesson. Returns `parity_confirmed` boolean.
- Dependencies: Both `prepopulate_portal_fields` and `prepopulate_mckesson_fields` completed. `portal_fields_written` and `mckesson_fields_written` lists present.
- Critical Constraint: `submit_authorization_request` must never be called without a prior `validate_field_parity` call that returned `parity_confirmed = true`. Enforced structurally: `submit_authorization_request.execute()` requires a non-null `parity_confirmation_ref` parameter in its schema.
- Failure Handling: `parity_confirmed = false` → permanent failure → halt; UM Manager notified.
- Verification: Mock with `mock_field_parity_confirmed.json` — confirm `parity_confirmed = true`. Mock with `mock_field_parity_mismatch.json` — confirm halt and UM Manager notification triggered.

**Tool 26: submit_authorization_request**
- Purpose: Submits completed authorization to payer portal. Mode A or Mode B post-approval only.
- Dependencies: `parity_confirmation_ref` non-null (from `validate_field_parity`). `mode_confirmation` matches `active_mode` in shared state. For Mode B: `specialist_action_log_ref` non-null.
- Critical Constraint: The tool's `execute()` function cross-validates `mode_confirmation` against `active_mode` from the shared state (passed as an additional parameter) before making any submission call. Mismatch → immediate rejection (not a retry).
- Failure Handling: Portal rejection → permanent failure → halt; UM Manager notified.
- Verification: Mock Mode A with `mock_submit_auth_success.json` — confirm `submission_ref` returned. Mock with mismatched mode — confirm rejection without submission. Mock Mode B without `specialist_action_log_ref` — confirm rejection.

**Tool 27: update_fields_post_specialist_action**
- Purpose: Updates portal and McKesson fields to reflect specialist determination (Modified or Override).
- Dependencies: Specialist action confirmed and logged. Only called in Mode B after specialist action received.
- Failure Handling: Transient → retry 3x. Permanent → halt; report.
- Verification: Mock with `mock_specialist_action_modified.json` — confirm fields updated in both systems. Confirm override path does NOT call `submit_authorization_request`.

---

**Tool Group 5: SLA Monitor Agent Tools**

**Tool 28: register_case_for_sla_monitoring**
- Purpose: Adds case to SLA Monitor's active monitoring set.
- Dependencies: `case_id`, `intake_timestamp`, `assigned_specialist_id` present in shared state.
- Failure Handling: Transient → retry 3x. Permanent → log failure; notify UM Manager (SLA monitoring gap is a compliance risk).
- Verification: Confirm `monitoring_ref` returned. Confirm case appears in SLA Monitor's active set.

**Tool 29: get_case_elapsed_times**
- Purpose: Returns elapsed time in hours for all active monitored cases.
- Dependencies: At least one case registered in active monitoring set.
- Failure Handling: Transient → retry 3x within the polling cycle. If third attempt fails: log polling failure; continue to next polling cycle (do not halt SLA monitoring for all cases on one poll failure).
- Verification: Mock with multiple active cases — confirm array of `{case_id, elapsed_hours}` returned.

**Tool 30: trigger_sla_alert**
- Purpose: Sends tiered SLA alert to defined recipient list. Maximum once per case per alert level.
- Dependencies: Elapsed hours confirm threshold reached. Alert not previously triggered for this case_id at this level (tracked in SLA Monitor's in-memory state per case).
- Failure Handling: Transient → retry 3x with exponential backoff. Permanent delivery failure → call `trigger_sla_alert` with `alert_level = "critical"` to UM Manager for the delivery failure event itself.
- Verification: Mock 48h threshold reached — confirm `alert_level = "standard"` called once. Confirm alert not triggered twice.

**Tool 31: reroute_to_high_priority_queue**
- Purpose: Re-routes case assignment to High Priority / Any Available Specialist queue at 66h.
- Dependencies: `elapsed_hours >= 66` confirmed. `trigger_sla_alert` with `alert_level = "code_red"` confirmed delivered first.
- Critical Constraint: Never called before 66 hours. Never calls `submit_authorization_request`.
- Failure Handling: Transient → retry 3x. Permanent → log failure; notify UM Manager.
- Verification: Confirm `reroute_confirmed = true`. Confirm case `queue` field in shared state SLA section updated to `"high_priority_any_available"`.

*(deregister_case_from_monitoring is implemented within the SLA Monitor task manager in `src/sla/sla_monitor_thread.py` as a direct task cancellation call, not a separate tool.)*

---

**Inter-Tool Dependencies:**
- `verify_session_authorization` must complete with `verified = true` before any other tool is called for a case.
- `check_audit_proxy_reachability` must complete with `reachable = true` before any PHI-touching tool is called.
- `request_vault_credential_injection` must complete with `injection_success = true` before `receive_vault_credentials` is called.
- `write_phi_audit_log` must confirm receipt for each PHI field before `retrieve_fax_document` content is processed, before `extract_structured_fields` accesses extracted PHI values, before `apply_interqual_matching` accesses PHI fields during criteria matching, and before `prepopulate_portal_fields` / `prepopulate_mckesson_fields` write any PHI field.
- `extract_structured_fields` must complete before `write_extraction_to_state` is called.
- `query_payer_config_table` must complete before `apply_interqual_matching` is called.
- `apply_interqual_matching` must complete before `evaluate_whitelist_conditions` is called.
- `evaluate_whitelist_conditions` must complete before `write_evaluation_to_state` is called.
- `authenticate_portal_session` must complete before `prepopulate_portal_fields` is called.
- `authenticate_mckesson_session` must complete before `prepopulate_mckesson_fields` is called.
- Both `prepopulate_portal_fields` AND `prepopulate_mckesson_fields` must complete before `validate_field_parity` is called.
- `validate_field_parity` must return `parity_confirmed = true` before `submit_authorization_request` is called.
- `trigger_sla_alert` with `alert_level = "code_red"` must confirm delivery before `reroute_to_high_priority_queue` is called.
- `trigger_emergency_stop` must not be followed by any other tool call from any agent.

**Error Handling Strategy:**
- Transient failure: Retry up to 3 times with exponential backoff (2s, 4s, 8s). After three failures: reclassify as permanent.
- Permanent failure: Halt case processing. Write error event to `error_logs` in shared state. Call `notify_um_manager`. Call `trigger_emergency_stop` if the failure is a defined Emergency Stop trigger condition.
- `write_phi_audit_log` failure: Emergency Stop immediately (no retry, no reclassification).
- Clinical field rejection from `prepopulate_portal_fields` or `prepopulate_mckesson_fields`: Emergency Stop immediately.
- Out-of-scope case type detected: Write out-of-scope log to Veea Lobster Trap. Notify initiating UM Specialist. Terminate workflow. No Emergency Stop (not a safety violation — a scoping boundary).

**Rate Limits & Safeguards:**
- Portal API calls: Token bucket — max 30 calls/minute/session. Implemented in `prepopulate_portal_fields.execute()` and `prepopulate_mckesson_fields.execute()`. Queue backlog exceeding 60 seconds → suspend case; notify UM Manager.
- Payer Master Config queries: Fixed window — max 10 queries/minute/agent instance. Implemented in `query_payer_config_table.execute()`.
- `write_phi_audit_log`: No rate limit — all PHI audit writes proceed without delay.
- `trigger_sla_alert`: Maximum 1 per case per `alert_level`. Duplicate trigger attempts are rejected in the SLA Monitor task manager (tracked per `case_id + alert_level` combination in the task manager's in-memory dict).
- `submit_authorization_request`: Maximum 1 successful submission per case. Tool rejects duplicate submission attempts by checking for existing `submission_confirmation_ref` in shared state artifacts before executing.

---

## **5. REASONING LOOP IMPLEMENTATION**

**Reasoning Cycle Structure:** Graph-Node ReAct — each agent node executes a single, bounded reasoning cycle: read state → verify preconditions → call designated tools in sequence → validate results → write state update → return. No open-ended reasoning loops. No exploratory branching. No tool call decisions that are not structurally predetermined by the workflow sequence.

**Step-by-Step Reasoning Flow (per agent node execution):**

**Step 1:** Node function invoked by LangGraph graph executor with current `state` dict.
**Step 2:** Read required fields from `state` for this step (e.g., `state["session"]["specialist_verified"]`).
**Step 3:** Verify all preconditions for this node (e.g., `specialist_verified = true`, `audit_proxy_reachable = true`, `active_mode != "suspended"`). If any precondition fails: route to emergency stop node.
**Step 4:** Call the first designated tool's `execute()` function with parameters derived from state.
**Step 5:** Validate tool result against expected post-conditions schema (required fields present and non-null, correct types, no error field).
**Step 6:** If validation fails: classify failure (transient / permanent / Emergency Stop per failure classification table). Apply appropriate response (retry / halt / Emergency Stop).
**Step 7:** Write validated result to designated state section (return as state update dict from node function).
**Step 8:** Write `task_history` entry for this tool call (step, agent, action, result, timestamp, audit_log_ref).
**Step 9:** If more tool calls remain in this node's sequence: repeat Steps 4–8.
**Step 10:** Return complete state update dict from node function. LangGraph commits to PostgreSQL checkpointer.
**Step 11:** LangGraph graph executor evaluates outgoing edges (conditional or fixed) to determine next node.

**Tool Call Decision Flow:**
Tool calls are not decided by the model — they are predetermined by the workflow sequence. Each agent node function calls its tools in the fixed order defined by the agent's system prompt. The only "decisions" are: (1) the binary Mode A / Mode B conditional edge routing based on `all_whitelist_conditions_met` from shared state; (2) failure classification determining whether to retry, halt, or Emergency Stop; (3) the specialist action type routing in Mode B post-approval execution (approved / modified / overridden).

**State Persistence Between Steps:**
The PostgreSQL checkpointer writes a state snapshot after each node function returns its state update dict. The next node's function receives the latest checkpoint as its `state` argument. If a node fails mid-execution (exception raised), the last committed checkpoint is the authoritative state — no partial state from the failed execution is committed.

**Termination Conditions:**
1. Success: `close_case` tool confirms `case_status = closed` and audit log completeness confirmed.
2. Emergency Stop: `trigger_emergency_stop` called → all agents halt → `active_mode = "suspended"` in shared state → graph terminates → awaits UM Manager restart authorization.
3. Out-of-scope detection: `case_type != "concurrent_review"` detected at Step 1 → out-of-scope log written → workflow terminated → no further actions.
4. Permanent failure: Any permanent failure not classified as Emergency Stop → case halted; `active_mode = "failed"` in shared state; UM Manager notified.
5. Mode B specialist override: After `update_fields_post_specialist_action` executes for override action → `close_case` called with override notation → case closed.

**Loop Prevention Mechanisms:**
- Max iterations: The LangGraph directed acyclic graph has no cycles in the sequential processing path — infinite loops are structurally impossible for the main case processing flow.
- SLA Monitor: Bounded by case closure deregistration — once `deregister_case_from_monitoring` is called, the asyncio task is cancelled.
- Mode B re-entry: Step 10b is a one-time node activation triggered by specialist action release of the LangGraph interrupt. It does not loop.
- Emergency Stop: After `trigger_emergency_stop`, no agent makes any further tool calls (enforced by `WorkflowHaltedException` raised after the tool executes, preventing any further code execution in the node function).
- Circuit breaker: After 3 Emergency Stops across different cases within 5 minutes: the Workflow Supervisor's circuit breaker function in `src/utils/circuit_breaker.py` suspends all active case processing and blocks new session initiations until UM Manager restart authorization is received.

---

## **6. INTERFACE & STREAMING INTEGRATION**

**Backend ↔ Frontend Connection Model:**
- **SSE (`GET /workflow/{case_id}/stream`):** Unidirectional server-to-client stream. The backend emits step status events as each LangGraph node completes or updates. The frontend renders these as workflow timeline step card updates.
- **WebSocket (`WS /workflow/{case_id}/action`):** Bidirectional. Used exclusively for the Mode B approval gate: (1) server sends the Full Recommendation Package to the connected specialist client when the Mode B interrupt fires; (2) client sends the specialist action (Approve / Modify / Override with rationale) back to the server; (3) server delivers the action to LangGraph to release the interrupt.
- **REST (`POST /session/initiate`):** Synchronous — session initialization form submission (case ID, specialist ID, session token). Returns session handle and initial shared state. Triggers LangGraph graph invocation.
- **REST (`POST /admin/emergency-stop`):** UM Manager / operator Emergency Stop command trigger (scope: case or system).
- **REST (`POST /admin/restart`):** UM Manager restart authorization submission after Emergency Stop.

**Streaming Protocol:**

**SSE:**
- Technology: FastAPI `EventSourceResponse` (via `sse-starlette` package)
- Message format: Each SSE event is a JSON object with `event` field (event type name) and `data` field (JSON-encoded event payload)
- Update frequency: Real-time — emitted at each LangGraph node boundary and each tool call status change
- Heartbeat: Server sends a comment line (`": keepalive"`) every 10 seconds when no events are emitted, to prevent client-side connection timeout

**WebSocket:**
- Technology: FastAPI WebSocket endpoint
- Message format: JSON objects for both directions
- Lifecycle: Opened when case enters Mode B state; closed when specialist action is submitted and confirmed

**Event & Message Formats:**

**Event Type 1: Step Status Update (SSE)**
```json
{
  "event": "step_status",
  "data": {
    "case_id": "string",
    "step_number": "integer (1-8)",
    "step_label": "string (plain-language — e.g., 'Session & System Verification')",
    "status": "pending | in_progress | completed | failed | suspended",
    "timestamp": "ISO8601",
    "summary": "string (plain-language outcome — e.g., 'Session authorized. Log reference confirmed.')",
    "retry_count": "integer (0 if no retries)",
    "audit_log_ref": "string | null"
  }
}
```

**Event Type 2: Tool Call Status (SSE)**
```json
{
  "event": "tool_call_status",
  "data": {
    "case_id": "string",
    "step_number": "integer",
    "tool_label": "string (plain-language — e.g., 'Verifying audit logging system availability...')",
    "status": "calling | retrying | confirmed | failed",
    "attempt_number": "integer",
    "timestamp": "ISO8601",
    "failure_type": "transient | permanent | emergency_stop | null",
    "failure_reason": "string | null (plain-language failure description — no credential or PHI values)"
  }
}
```

**Event Type 3: PHI Audit Confirmation (SSE)**
```json
{
  "event": "phi_audit_confirmed",
  "data": {
    "case_id": "string",
    "step_number": "integer",
    "field_count": "integer (count of fields audit-logged — never individual field names or values)",
    "confirmed": "boolean",
    "timestamp": "ISO8601"
  }
}
```

**Event Type 4: Whitelist Condition Results (SSE)**
```json
{
  "event": "whitelist_conditions",
  "data": {
    "case_id": "string",
    "whitelist_determination": "mode_a | mode_b",
    "all_conditions_met": "boolean",
    "conditions": [
      {
        "label": "A",
        "name": "Criteria Match Exactness",
        "passed": "boolean",
        "reason": "string (plain-language — e.g., 'Exact match confirmed with no missing fields')"
      },
      {"label": "B", "name": "No Structural Complexity Flags", "passed": "boolean", "reason": "string"},
      {"label": "C", "name": "Projected Cost Threshold", "passed": "boolean", "reason": "string"},
      {"label": "D", "name": "Acuity Category", "passed": "boolean", "reason": "string"},
      {"label": "E", "name": "Length of Stay Threshold", "passed": "boolean", "reason": "string"},
      {"label": "F", "name": "Payer Configuration Available", "passed": "boolean", "reason": "string"},
      {"label": "G", "name": "No Runtime Threshold Exceeded", "passed": "boolean", "reason": "string"}
    ],
    "escalation_reason_codes": ["string"],
    "timestamp": "ISO8601"
  }
}
```

**Event Type 5: Routing Decision (SSE)**
```json
{
  "event": "routing_decision",
  "data": {
    "case_id": "string",
    "mode": "mode_a | mode_b",
    "routing_audit_log_ref": "string",
    "sla_registered": "boolean",
    "timestamp": "ISO8601"
  }
}
```

**Event Type 6: SLA Alert (SSE)**
```json
{
  "event": "sla_alert",
  "data": {
    "case_id": "string",
    "alert_level": "standard | critical | code_red",
    "elapsed_hours": "number",
    "rerouted_to_high_priority": "boolean",
    "timestamp": "ISO8601"
  }
}
```

**Event Type 7: Emergency Stop (SSE)**
```json
{
  "event": "emergency_stop",
  "data": {
    "case_id": "string | null (null if system-level)",
    "scope": "case | system",
    "trigger_condition": "string (plain-language — e.g., 'PHI audit logging system returned an error')",
    "condition_violated": "string (verbatim constraint name)",
    "suspended_cases": ["string"],
    "stop_event_log_ref": "string",
    "timestamp": "ISO8601",
    "restart_requires": "UM_Department_Manager_explicit_authorization"
  }
}
```

**Event Type 8: Case Closure (SSE)**
```json
{
  "event": "case_closed",
  "data": {
    "case_id": "string",
    "mode": "mode_a | mode_b",
    "submission_ref": "string",
    "audit_log_complete": "boolean",
    "timestamp": "ISO8601",
    "override_notation": "string | null"
  }
}
```

**Event Type 9: Mode B Package Ready (WebSocket — Server → Client)**
```json
{
  "type": "mode_b_package",
  "case_id": "string",
  "full_recommendation_package": {
    "case_id": "string",
    "case_metadata": "object (non-PHI header fields only)",
    "interqual_criteria_set_matched": "string",
    "criteria_match_type": "exact | partial | ambiguous | no_match",
    "whitelist_condition_results": "array (all 7 conditions with pass/fail and reason)",
    "escalation_reason_codes": ["string"],
    "structured_clinical_summary": "object (PHI fields included — served over secure authenticated session)",
    "pre_populated_non_clinical_fields": "object (portal and McKesson field values — non-PHI only in this payload)",
    "criteria_based_recommendation": "string (single specific recommendation)",
    "clinical_necessity_determination_excluded": true
  },
  "timestamp": "ISO8601"
}
```

**Event Type 10: Specialist Action Submission (WebSocket — Client → Server)**
```json
{
  "type": "specialist_action",
  "case_id": "string",
  "specialist_id": "string",
  "session_id": "string",
  "action_type": "approved | modified | overridden",
  "rationale": "string (required — minimum 1 character)",
  "modified_fields": "object | null (only if action_type = 'modified')",
  "timestamp": "ISO8601"
}
```

**Event Type 11: System Activity Log Entry (SSE)**
```json
{
  "event": "activity_log_entry",
  "data": {
    "case_id": "string",
    "entry_id": "string (UUID)",
    "event_category": "agent_action | user_action | system_event | sla_event",
    "description": "string (plain-language — no PHI values, no credential values, no raw tool names in non-debug mode)",
    "step_number": "integer | null",
    "timestamp_absolute": "ISO8601",
    "timestamp_relative": "string (e.g., '3 minutes ago')",
    "audit_log_ref": "string | null"
  }
}
```

**Observability Hooks:**
- LangGraph node boundary: emit `step_status` SSE event at node entry (status: `in_progress`) and node exit (status: `completed` or `failed`).
- Each tool `execute()` call: emit `tool_call_status` SSE event at call start (`calling`) and completion (`confirmed` or `failed`).
- Each `write_phi_audit_log` batch: emit `phi_audit_confirmed` SSE event after all field confirmations complete.
- `evaluate_whitelist_conditions` completion: emit `whitelist_conditions` SSE event.
- Mode routing decision: emit `routing_decision` SSE event.
- SLA threshold triggers: emit `sla_alert` SSE event.
- `trigger_emergency_stop` call: emit `emergency_stop` SSE event.
- `close_case` confirmation: emit `case_closed` SSE event.
- All events: emit corresponding `activity_log_entry` SSE event.
- Each SSE event emission point: write entry to `structlog`-based structured JSON log file (`LOG_LEVEL=INFO`).

**Real-Time Update Mechanism:**
The FastAPI SSE endpoint at `/workflow/{case_id}/stream` holds an async generator open for the lifetime of the case session. LangGraph node boundary callbacks and tool execution callbacks are registered as event emitters that push events into an `asyncio.Queue` per case. The SSE generator polls this queue and yields events as they arrive. The frontend's `useSSEStream` hook maintains the EventSource connection and updates React state on each received event.

---

## **7. SAFETY, CONTROL & FAILURE HANDLING**

**Human-in-the-Loop Enforcement Points:**

**Approval Gate 1: Mode B Specialist Action (Step 9b)**
- Trigger: `whitelist_determination = "mode_b"` at Step 6.
- Implementation: LangGraph `interrupt_before=["mode_b_specialist_action_node"]` declared in `graph_builder.py`. Graph execution suspends at this node boundary. `awaiting_human_action = true` written to shared state. WebSocket event `mode_b_package` delivered to specialist frontend. Graph cannot advance until `graph.update_state(config, {"current_context": {"specialist_action": <action_object>}})` is called with a non-null `specialist_action`.
- Timeout: None — graph waits indefinitely. SLA Monitor continues tracking.
- Denial Handling: `action_type = "overridden"` → Data Entry Agent calls `update_fields_post_specialist_action`, logs override, does NOT call `submit_authorization_request`. Graph proceeds to closure.

**Approval Gate 2: Emergency Stop Restart Authorization**
- Trigger: Any Emergency Stop event.
- Implementation: After `trigger_emergency_stop` executes, the graph raises `WorkflowHaltedException`, all nodes cease execution. `active_mode = "suspended"` written to shared state. The `/admin/restart` endpoint is only callable by an authenticated UM Department Manager role (role-based access enforced at API middleware layer). Calling `/admin/restart` with documented acknowledgment calls `graph.update_state(config, {"current_context": {"active_mode": "pending_restart"}})` and emits a restart authorization event. No code path restarts the graph without this explicit API call.

**Emergency Stop Mechanism:**
- **Trigger conditions:** (1) `verify_session_authorization` returns `verified = false` or network failure after 3 retries; (2) `check_audit_proxy_reachability` returns `reachable = false`; (3) `request_vault_credential_injection` fails; (4) `write_phi_audit_log` fails (any failure); (5) any prohibited action detected (clinical field write attempt, credential storage attempt, manifest validation failure); (6) agent operating on case without granted session authorization; (7) human operator POST to `/admin/emergency-stop`; (8) circuit breaker: 3 Emergency Stops across different cases within 5 minutes.
- **Implementation:** `trigger_emergency_stop.execute()` is called. It sends an HTTP POST to the system's own `/admin/emergency-stop` endpoint (for system-level scope) or directly updates shared state for case-level scope. After `execute()` returns: `WorkflowHaltedException` is raised in the node function, propagating to the LangGraph graph executor which marks the node as failed and halts further execution. The SLA Monitor is notified via the case deregistration mechanism for suspended cases.
- **State preservation:** PostgreSQL checkpointer retains the last checkpoint before Emergency Stop. All suspended cases retain their state snapshots.
- **Recovery:** Requires UM Department Manager authentication + POST to `/admin/restart` with documented acknowledgment. The agent system has no self-resume capability.

**Prohibition Enforcement:**

1. **No clinical necessity determination:** Clinical necessity fields absent from all agent tool manifests and all portal/McKesson write tool schemas. The clinical field blocklist is a versioned JSON file loaded by `prepopulate_portal_fields.execute()` and `prepopulate_mckesson_fields.execute()`. Any field name on the blocklist → `prohibited_field_rejected = true` → Emergency Stop.

2. **No provider or member communication:** No outbound communication tools exist in any agent's tool manifest. The approved integration manifest contains no provider portal or member portal endpoints. `manifest_validator.validate_endpoint()` called before every tool HTTP request blocks any unapproved endpoint.

3. **No modification or deletion of existing records:** Portal and McKesson write tools expose only create/append API calls. No update, patch, or delete methods exist in any tool's execute function. The `prepopulate_portal_fields` and `prepopulate_mckesson_fields` tool functions use POST-only HTTP methods.

4. **No credential storage:** `PACaseState` TypedDict has no credential field. The `_credential_context` in `vault_injection_adapter.py` is an in-memory-only dict scoped to the process — it is not written to any database, log, or state. The `write_phi_audit_log` tool's execute function includes a pre-flight check that the log payload does not contain any string matching known credential patterns (regex check for token/secret/password/key patterns) before sending.

5. **No session-free workflow initiation:** `session_auth_node` is the first and only entry node in the LangGraph graph with a `START` edge. No other node has a `START` edge. Topologically impossible to execute any downstream node without passing through session auth first.

6. **No autonomous submission on any unmet whitelist condition:** `submit_authorization_request.execute()` reads `active_mode` from shared state and validates that `mode_confirmation` parameter matches exactly. In Mode B, `specialist_action_log_ref` is a required parameter — the tool's schema validation (Pydantic) rejects calls without it. LangGraph conditional edge routes to Mode B exclusively when `all_whitelist_conditions_met = false`.

7. **No baseline threshold override:** `BASELINE_COST_THRESHOLD_USD = 10000` and `BASELINE_LOS_THRESHOLD_DAYS = 5` are defined as Python constants in `state_schema.py`. `evaluate_whitelist_conditions.execute()` uses Python `min(runtime_value, BASELINE_COST_THRESHOLD_USD)` for threshold comparison — if runtime config value exceeds baseline, `runtime_config_exceeds_baseline = true` is set and the baseline value is used, never the higher runtime value. No API call, instruction, or specialist directive can modify these constant values at runtime.

8. **No autonomous action on high-acuity cases:** `evaluate_whitelist_conditions.execute()` checks `acuity_flags` for `ICU`, `Critical_Care`, `Inpatient_Surgery`, `Substance_Use_Disorder`, `Behavioral_Health`, `Experimental`, `Investigational`, `Non_Formulary` before evaluating Condition D. Detection of any of these → `condition_d_acuity.passed = false` → `all_whitelist_conditions_met = false` → Mode B. No code path exists where these acuity flags coexist with `whitelist_determination = "mode_a"`.

9. **No PHI processing without confirmed audit logging:** The `@phi_audit_required` decorator applied to `document_processing_node`, `criteria_evaluation_node`, and `data_entry_node` enforces this structurally. The decorator intercepts execution before any PHI field access occurs.

10. **No audit logging suppression:** `write_phi_audit_log.execute()` has no parameter that disables logging. The PHI audit decorator does not have a bypass flag. Any modification to the decorator or tool that would suppress logging is a code change requiring peer review and deployment — it cannot occur at runtime.

11. **No runtime threshold elevation:** Enforced by `evaluate_whitelist_conditions.execute()` using hardcoded baseline constants, not runtime-configurable values.

12. **No self-recovery after Emergency Stop:** No asyncio task, scheduled job, or callback exists that calls graph resume after Emergency Stop. The only graph resume mechanism is the `/admin/restart` REST endpoint gated behind UM Manager role authentication.

**Fallback Behaviors:**
- Payer Master Configuration Table unreachable after 3 retries: Set `payer_config_reachable = false`; Condition F fails; `whitelist_determination = mode_b`; continue workflow in Mode B (not a halt — Mode B is a fully functional path).
- `evaluate_whitelist_conditions` permanent tool failure: Default to `whitelist_determination = "mode_b"`; `escalation_reason_code = "evaluation_tool_failure"`; continue in Mode B.
- Model (Gemini) unavailability: The `google-generativeai` SDK raises `google.api_core.exceptions.ServiceUnavailable` or `google.api_core.exceptions.GoogleAPICallError`. This is classified as a transient failure — retry 3x. If third attempt fails: permanent failure → halt; UM Manager notified. No fallback model — the model assignment is fixed per agent.
- Network timeout on any tool: Classified as transient. Retry 3x with exponential backoff. After three failures: permanent failure → halt.

**Logging & Audit Trail:**
- Log format: Structured JSON via `structlog`. Every log entry contains: `timestamp` (ISO8601), `level`, `case_id`, `session_id`, `agent`, `event_type`, `description`, `audit_log_ref` (where applicable). No PHI field values in any log entry. No credential values in any log entry.
- Log location: Local file (`logs/pa_agent.log`) and streamed to the SSE `activity_log_entry` event. In production: ship to centralized log aggregator (configuration outside agent system scope).
- Retention: Local log file retained indefinitely (rotation policy configured at infrastructure level). Veea Lobster Trap audit log retained per HIPAA and organizational policy (permanent; outside agent control).
- Privacy: PHI field values are NEVER written to any log file or structured log entry. Field names (not values) may appear in audit trail entries. Credential values are NEVER written to any log file.

---

## **7.1 TEST DATA STRATEGY & MOCKS**

**Mock User Inputs (For Testing Logic):**

1. **Happy Path — Mode A (Simple Case):** `case_id = "TEST-CASE-001"`, `specialist_id = "SP-001"`, `session_token = "TEST-TOKEN-001"`, `case_type = "concurrent_review"`. All seven whitelist conditions pass: exact criteria match, no flags, cost `$7,500`, no acuity flags, LOS 3 days, payer config reachable. Expected outcome: Mode A autonomous execution → submission confirmed → case closed.

2. **Mode B Path — Cost Threshold Exceeded (Complex Case):** `case_id = "TEST-CASE-002"`, `specialist_id = "SP-002"`, same session token format. Extraction complete. Criteria match exact. But `projected_cost_usd = 12000` (exceeds $10,000 baseline). Expected outcome: Condition C fails → Mode B → Full Recommendation Package assembled → specialist approval gate activated.

3. **Emergency Stop — PHI Audit Log Failure (Edge Case):** `case_id = "TEST-CASE-003"`. Mock `write_phi_audit_log` to return `success = false` during document extraction step. Expected outcome: Emergency Stop triggered immediately → all processing halted → UM Manager notified → `active_mode = "suspended"` → no PHI state mutation committed.

4. **Out-of-Scope Rejection:** `case_id = "TEST-CASE-004"`, `case_type = "retrospective_review"`. Expected outcome: `case_type` validation fails at session auth step → out-of-scope log written → specialist notified → workflow terminated without document processing.

5. **Mode B — Specialist Override:** `case_id = "TEST-CASE-005"`. Mode B path. Specialist submits `action_type = "overridden"` with rationale. Expected outcome: `update_fields_post_specialist_action` called → override logged → `submit_authorization_request` NOT called → case closed with override notation.

6. **Circuit Breaker Activation:** Trigger Emergency Stop on `TEST-CASE-006`, `TEST-CASE-007`, `TEST-CASE-008` within 5 minutes. Expected outcome: circuit breaker activates → all active cases suspended → UM Manager system-level alert sent → no new sessions accepted.

---

**Mock Tool Outputs (For Testing without API Costs):**
*Use these JSON responses to mock tool HTTP calls during unit and integration testing.*

**mock_verify_session_auth_success.json:**
```json
{
  "success": true,
  "result": {
    "verified": true,
    "specialist_id": "SP-001",
    "authorization_log_ref": "VLT-AUTH-20260511-001",
    "session_id": "SES-20260511-001",
    "timestamp": "2026-05-11T10:00:00Z"
  },
  "error": null
}
```

**mock_verify_session_auth_failure.json:**
```json
{
  "success": false,
  "result": {
    "verified": false,
    "specialist_id": "SP-UNKNOWN",
    "authorization_log_ref": null
  },
  "error": "Specialist identity not found in authorized personnel registry"
}
```

**mock_check_audit_proxy_reachable.json:**
```json
{
  "success": true,
  "result": {
    "reachable": true,
    "proxy_endpoint": "https://veea-lobster-trap.internal/api/v1/audit",
    "timestamp": "2026-05-11T10:00:05Z"
  },
  "error": null
}
```

**mock_check_audit_proxy_unreachable.json:**
```json
{
  "success": false,
  "result": {
    "reachable": false
  },
  "error": "Connection refused: audit proxy endpoint unreachable"
}
```

**mock_vault_injection_success.json:**
```json
{
  "success": true,
  "result": {
    "injection_success": true,
    "session_id": "SES-20260511-001",
    "target_agent": "data_entry_agent",
    "timestamp": "2026-05-11T10:00:10Z"
  },
  "error": null
}
```

**mock_retrieve_fax_document.json:**
```json
{
  "success": true,
  "result": {
    "document_pages": [
      {"page_number": 1, "source_document_id": "FAX-DOC-001-P1", "content_type": "typed_physician_notes"},
      {"page_number": 2, "source_document_id": "FAX-DOC-001-P2", "content_type": "nursing_flowsheet"},
      {"page_number": 3, "source_document_id": "FAX-DOC-001-P3", "content_type": "handwritten_annotations"}
    ],
    "source_document_ids": ["FAX-DOC-001-P1", "FAX-DOC-001-P2", "FAX-DOC-001-P3"],
    "retrieval_timestamp": "2026-05-11T10:00:15Z"
  },
  "error": null
}
```

**mock_phi_audit_log_success.json:**
```json
{
  "success": true,
  "result": {
    "log_ref": "VLT-PHI-20260511-001-F001",
    "phi_field_name": "member_date_of_birth",
    "action_type": "extract",
    "agent": "document_processing_agent",
    "session_id": "SES-20260511-001",
    "timestamp": "2026-05-11T10:00:20Z"
  },
  "error": null
}
```

**mock_phi_audit_log_failure.json:**
```json
{
  "success": false,
  "result": null,
  "error": "Veea Lobster Trap proxy returned HTTP 503: service temporarily unavailable"
}
```

**mock_extract_fields_complete.json:**
```json
{
  "success": true,
  "result": {
    "extracted_fields": {
      "member_id": "TEST-MEMBER-001",
      "member_date_of_birth": "1965-04-15",
      "admission_date": "2026-05-10",
      "discharge_date": "2026-05-13",
      "diagnosis_codes": ["J18.9", "I10"],
      "procedure_codes": ["99232"],
      "attending_physician_npi": "1234567890",
      "payer_id": "PAYER-001",
      "requested_los_extension_days": 2,
      "projected_cost_usd": 7500,
      "acuity_flags": []
    },
    "missing_required_fields": [],
    "structural_complexity_flags": [],
    "illegibility_flags": [],
    "extraction_completeness": true
  },
  "error": null
}
```

**mock_extract_fields_incomplete.json:**
```json
{
  "success": true,
  "result": {
    "extracted_fields": {
      "member_id": "TEST-MEMBER-002",
      "admission_date": "2026-05-09"
    },
    "missing_required_fields": ["member_date_of_birth", "diagnosis_codes", "attending_physician_npi", "projected_cost_usd"],
    "structural_complexity_flags": ["conflicting_level_of_care_signals"],
    "illegibility_flags": ["page_3_handwriting_unparseable"],
    "extraction_completeness": false
  },
  "error": null
}
```

**mock_payer_config_reachable.json:**
```json
{
  "success": true,
  "result": {
    "payer_config_reachable": true,
    "payer_id": "PAYER-001",
    "cost_threshold_override_usd": 8000,
    "los_threshold_override_days": 4,
    "carve_out_rules": ["sud_behavioral_health_always_mode_b"],
    "query_timestamp": "2026-05-11T10:01:00Z"
  },
  "error": null
}
```

**mock_payer_config_unreachable.json:**
```json
{
  "success": false,
  "result": {
    "payer_config_reachable": false
  },
  "error": "Connection timeout: Payer Master Configuration Table unreachable after 3 attempts"
}
```

**mock_interqual_exact_match.json:**
```json
{
  "success": true,
  "result": {
    "criteria_set_matched": "IQ-ACUTE-PNEUMONIA-2026-V3",
    "match_type": "exact",
    "missing_data_fields": [],
    "match_confidence": "definite",
    "timestamp": "2026-05-11T10:01:15Z"
  },
  "error": null
}
```

**mock_interqual_partial_match.json:**
```json
{
  "success": true,
  "result": {
    "criteria_set_matched": "IQ-ACUTE-PNEUMONIA-2026-V3",
    "match_type": "partial",
    "missing_data_fields": ["oxygen_saturation_on_admission", "antibiotic_therapy_start_date"],
    "match_confidence": "partial",
    "timestamp": "2026-05-11T10:01:15Z"
  },
  "error": null
}
```

**mock_whitelist_all_pass_mode_a.json:**
```json
{
  "success": true,
  "result": {
    "all_conditions_met": true,
    "whitelist_determination": "mode_a",
    "condition_results": {
      "condition_a_criteria_match": {"passed": true, "detail": "Exact match. No missing data fields."},
      "condition_b_no_complexity_flags": {"passed": true, "detail": "No structural complexity flags. No illegibility flags."},
      "condition_c_cost_threshold": {"passed": true, "detail": "Projected cost $7,500 — within $8,000 payer config threshold and $10,000 baseline."},
      "condition_d_acuity": {"passed": true, "detail": "No high-acuity flags detected."},
      "condition_e_los_threshold": {"passed": true, "detail": "Requested LOS 2 days — within 4-day payer config threshold and 5-day baseline."},
      "condition_f_payer_config": {"passed": true, "detail": "Payer configuration table reachable and returned unambiguous result."},
      "condition_g_runtime_config": {"passed": true, "detail": "No runtime config value exceeds baseline maximums."}
    },
    "runtime_config_exceeds_baseline": false,
    "escalation_reason_codes": [],
    "evaluation_timestamp": "2026-05-11T10:01:30Z"
  },
  "error": null
}
```

**mock_whitelist_condition_c_fail.json:**
```json
{
  "success": true,
  "result": {
    "all_conditions_met": false,
    "whitelist_determination": "mode_b",
    "condition_results": {
      "condition_a_criteria_match": {"passed": true, "detail": "Exact match. No missing data fields."},
      "condition_b_no_complexity_flags": {"passed": true, "detail": "No flags."},
      "condition_c_cost_threshold": {"passed": false, "detail": "Projected cost $12,000 exceeds $10,000 baseline maximum."},
      "condition_d_acuity": {"passed": true, "detail": "No high-acuity flags."},
      "condition_e_los_threshold": {"passed": true, "detail": "LOS within threshold."},
      "condition_f_payer_config": {"passed": true, "detail": "Config reachable."},
      "condition_g_runtime_config": {"passed": true, "detail": "No baseline exceeded."}
    },
    "runtime_config_exceeds_baseline": false,
    "escalation_reason_codes": ["COST_EXCEEDS_BASELINE_C"],
    "evaluation_timestamp": "2026-05-11T10:01:30Z"
  },
  "error": null
}
```

**mock_whitelist_condition_d_fail.json:**
```json
{
  "success": true,
  "result": {
    "all_conditions_met": false,
    "whitelist_determination": "mode_b",
    "condition_results": {
      "condition_a_criteria_match": {"passed": true, "detail": "Exact match."},
      "condition_b_no_complexity_flags": {"passed": true, "detail": "No flags."},
      "condition_c_cost_threshold": {"passed": true, "detail": "Cost within threshold."},
      "condition_d_acuity": {"passed": false, "detail": "Acuity flag detected: Substance_Use_Disorder. Mandatory Mode B per 42 CFR Part 2."},
      "condition_e_los_threshold": {"passed": true, "detail": "LOS within threshold."},
      "condition_f_payer_config": {"passed": true, "detail": "Config reachable."},
      "condition_g_runtime_config": {"passed": true, "detail": "No baseline exceeded."}
    },
    "runtime_config_exceeds_baseline": false,
    "escalation_reason_codes": ["ACUITY_SUD_MANDATORY_ESCALATION_D"],
    "evaluation_timestamp": "2026-05-11T10:01:30Z"
  },
  "error": null
}
```

**mock_whitelist_config_exceeds_baseline.json:**
```json
{
  "success": true,
  "result": {
    "all_conditions_met": false,
    "whitelist_determination": "mode_b",
    "condition_results": {
      "condition_a_criteria_match": {"passed": true, "detail": "Exact match."},
      "condition_b_no_complexity_flags": {"passed": true, "detail": "No flags."},
      "condition_c_cost_threshold": {"passed": true, "detail": "Cost within baseline."},
      "condition_d_acuity": {"passed": true, "detail": "No high-acuity flags."},
      "condition_e_los_threshold": {"passed": true, "detail": "LOS within baseline."},
      "condition_f_payer_config": {"passed": true, "detail": "Config reachable."},
      "condition_g_runtime_config": {"passed": false, "detail": "Runtime config attempted to set cost threshold to $15,000 — exceeds $10,000 baseline maximum. Baseline value applied. runtime_config_exceeds_baseline = true."}
    },
    "runtime_config_exceeds_baseline": true,
    "escalation_reason_codes": ["RUNTIME_CONFIG_EXCEEDS_BASELINE_G"],
    "evaluation_timestamp": "2026-05-11T10:01:30Z"
  },
  "error": null
}
```

**mock_field_parity_confirmed.json:**
```json
{
  "success": true,
  "result": {
    "parity_confirmed": true,
    "mismatched_fields": [],
    "validation_timestamp": "2026-05-11T10:03:00Z"
  },
  "error": null
}
```

**mock_field_parity_mismatch.json:**
```json
{
  "success": true,
  "result": {
    "parity_confirmed": false,
    "mismatched_fields": ["member_plan_id", "authorization_type_code"],
    "validation_timestamp": "2026-05-11T10:03:00Z"
  },
  "error": null
}
```

**mock_submit_auth_success.json:**
```json
{
  "success": true,
  "result": {
    "submission_ref": "SUB-20260511-001",
    "portal_response": "Authorization request received and queued for review",
    "submission_timestamp": "2026-05-11T10:03:30Z"
  },
  "error": null
}
```

**mock_specialist_action_approved.json:**
```json
{
  "action_type": "approved",
  "action_timestamp": "2026-05-11T14:30:00Z",
  "rationale": "Clinical criteria met. Pre-populated fields confirmed accurate.",
  "specialist_id": "SP-002",
  "session_id": "SES-20260511-002"
}
```

**mock_specialist_action_overridden.json:**
```json
{
  "action_type": "overridden",
  "action_timestamp": "2026-05-11T15:00:00Z",
  "rationale": "Clinical determination requires denial based on criteria not captured in extraction. Authorization not appropriate.",
  "specialist_id": "SP-002",
  "session_id": "SES-20260511-002"
}
```

**mock_emergency_stop.json:**
```json
{
  "success": true,
  "result": {
    "stop_confirmed": true,
    "suspended_cases": ["TEST-CASE-003"],
    "stop_event_log_ref": "VLT-STOP-20260511-001",
    "stop_timestamp": "2026-05-11T10:00:25Z",
    "restart_requires": "UM_Department_Manager_explicit_authorization"
  },
  "error": null
}
```

---

**First Tests (Must Pass Before Proceeding to Integration):**

- [ ] `python -c "from src.graph.state_schema import PACaseState, BASELINE_COST_THRESHOLD_USD; assert BASELINE_COST_THRESHOLD_USD == 10000"` — baseline constant correct
- [ ] `python -c "from src.graph.checkpointer import get_checkpointer; import asyncio; asyncio.run(get_checkpointer().setup())"` — PostgreSQL checkpointer tables created
- [ ] Google GenAI SDK test call with `flash_client` returns response — API key valid
- [ ] Google GenAI SDK test call with `pro_client` returns response — API key valid
- [ ] `validate_endpoint("approved-portal-001", "v1.0.0")` returns `True` — manifest validator loads
- [ ] `validate_endpoint("unapproved-endpoint", "v1.0.0")` returns `False` and logs prohibited action event
- [ ] `phi_audit_decorator` unit test: mock `write_phi_audit_log` failure → confirm Emergency Stop triggered and exception raised before any state mutation
- [ ] `circuit_breaker` unit test: trigger 3 Emergency Stops within 5 minutes → confirm `circuit_breaker_active = True`
- [ ] `retry.py` unit test: mock transient failure → confirm 3 attempts with 2s/4s/8s delays

**"Agent Is Working" Success Criteria:**

- [ ] POST `/session/initiate` with TEST-CASE-001 credentials returns `session_handle` and SSE stream URL
- [ ] SSE stream emits `step_status` events for each of Steps 1–3 with `status = "completed"` sequentially
- [ ] Step 4 (document processing) emits `phi_audit_confirmed` event with `field_count > 0`
- [ ] Step 5–6 emits `whitelist_conditions` event with all 7 conditions populated
- [ ] Mode A path: SSE emits `routing_decision` with `mode = "mode_a"` → `step_status` for Mode A execution → `case_closed`
- [ ] Mode B path: SSE emits `routing_decision` with `mode = "mode_b"` → WebSocket `mode_b_package` delivered → specialist action submitted via WebSocket → case proceeds to closure
- [ ] Emergency Stop: mock `write_phi_audit_log` failure → SSE emits `emergency_stop` event → no further `step_status` events emitted for that case
- [ ] Prohibited action test: mock clinical field write attempt → Emergency Stop triggered → `prohibited_field_rejected = true` in error log
- [ ] SLA alert test: register mock case with 47.9h elapsed → advance clock → confirm `sla_alert` with `alert_level = "standard"` emitted at 48h → confirm alert not re-emitted
- [ ] Circuit breaker test: trigger Emergency Stop on 3 different cases within 5 minutes → confirm all active cases suspended → new session initiation blocked
- [ ] Specialist override test: Mode B → `action_type = "overridden"` → confirm `submit_authorization_request` NOT called → `case_closed` emitted with `override_notation` non-null
- [ ] Out-of-scope test: initiate session with `case_type = "retrospective_review"` → confirm out-of-scope log written → workflow terminates without document processing step executing

**Failure Scenarios to Simulate:**

1. `verify_session_authorization` returns `verified = false` → confirm Emergency Stop triggered, no further graph node executes, UM Manager notified.
2. `check_audit_proxy_reachability` returns `reachable = false` → confirm Emergency Stop triggered immediately (no retry).
3. `write_phi_audit_log` returns failure during Step 4 → confirm Emergency Stop triggered, no PHI state mutation committed.
4. `validate_field_parity` returns `parity_confirmed = false` → confirm `submit_authorization_request` never called, case halted with permanent failure, UM Manager notified.
5. `trigger_emergency_stop` itself fails (mock HTTP 500 response) → confirm stop event written to `error_logs` in shared state, all further tool calls blocked.
6. Specialist submits Mode B action with empty rationale → confirm WebSocket action rejected (HTTP 400 from `/workflow/{case_id}/action` — schema validation fails), specialist prompted to provide rationale.
7. Runtime payer config returns `cost_threshold = 15000` (exceeds baseline) → confirm `runtime_config_exceeds_baseline = true` set, Condition G fails, $10,000 baseline used in comparison, Mode B.
8. Clinical field name detected in `prepopulate_portal_fields` call → confirm Emergency Stop triggered, `prohibited_field_rejected = true` logged.
9. Portal API rate limit exceeded (31 calls/minute) → confirm token bucket queues excess calls; if queue backlog exceeds 60 seconds → confirm case suspended, UM Manager notified.
10. 3 consecutive Emergency Stops within 5 minutes → confirm system-level circuit breaker activates, all new session initiations blocked.

**Non-Negotiable Verification Requirements:**

- No scenario exists in which `submit_authorization_request` executes without a prior `validate_field_parity` call returning `parity_confirmed = true` — verified by structural schema enforcement (`parity_confirmation_ref` required parameter).
- No scenario exists in which `submit_authorization_request` executes in Mode B without a `specialist_action_log_ref` — verified by Pydantic schema rejection.
- No scenario exists in which `write_phi_audit_log` failure results in continued PHI access — verified by decorator unit test.
- No scenario exists in which Emergency Stop is followed by any further tool execution — verified by `WorkflowHaltedException` propagation test.
- No scenario exists in which a credential value appears in any LangGraph state snapshot, log entry, or SSE event — verified by a test that checks all state snapshots from PostgreSQL and all log file entries after credential injection.
- No scenario exists in which `BASELINE_COST_THRESHOLD_USD` or `BASELINE_LOS_THRESHOLD_DAYS` is modified at runtime — verified by confirming the constants remain unchanged after test cases that attempt runtime threshold elevation.
- No infinite loops possible — verified by LangGraph graph structure validation (DAG check via `graph.get_graph().draw_mermaid()` showing no cycles in sequential path).

---

## **9. STEP-BY-STEP CODE GENERATOR EXECUTION SEQUENCE**

**Execution Order (Strictly Sequential — Do not proceed to the next step until current step's verification passes):**

---

**STEP 1: Environment & Project Scaffold**
- Action: Create project root directory. Create `.env.example` with all variable names from Section 2 (no values). Create `.env` with all variable values populated. Create `requirements.txt` with exact pinned versions from Section 2. Create full directory tree from Section 2 (all directories and empty `__init__.py` files). Create `README.md` with project title.
- Verification: `ls -R project-root/` shows all directories from the project tree. `cat .env | grep GEMINI_API_KEY` shows value. `cat .env.example | grep GEMINI_API_KEY` shows name only (no value).
- Dependencies: None.
- Safe to run: Yes (no external calls).

---

**STEP 2: Install Python Backend Dependencies**
- Action: `python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Verification: `pip list | grep langgraph` shows `langgraph 0.3.5`. `pip list | grep google-generativeai` shows `google-generativeai 0.8.3`. `pip list | grep fastapi` shows `fastapi 0.115.0`.
- Dependencies: STEP 1 complete. Python 3.12 installed. `requirements.txt` exists.
- Safe to run: Yes (idempotent).

---

**STEP 3: Install Frontend Dependencies**
- Action: `cd frontend && npm install`. Initialize Tailwind: `npx tailwindcss init -p`.
- Verification: `ls frontend/node_modules | grep react` shows `react`. `ls frontend/tailwind.config.js` exists.
- Dependencies: STEP 1 complete. Node.js 20.x installed.
- Safe to run: Yes (idempotent).

---

**STEP 4: Implement State Schema**
- Action: Implement `src/graph/state_schema.py` with the complete `PACaseState` TypedDict matching AGENT_ORCHESTRATION_BLUEPRINT.md Section 2.1 exactly. Define `BASELINE_COST_THRESHOLD_USD = 10000` and `BASELINE_LOS_THRESHOLD_DAYS = 5` as module-level integer constants. Define the initial state factory function `create_initial_state(case_id, specialist_id, session_id, intake_source_ref, intake_timestamp) -> PACaseState` that populates the `config` section with both baseline constants and reads `APPROVED_INTEGRATION_MANIFEST_VERSION` and `VEEA_LOBSTER_TRAP_API_ENDPOINT` from environment variables.
- Verification: `python -c "from src.graph.state_schema import PACaseState, BASELINE_COST_THRESHOLD_USD, BASELINE_LOS_THRESHOLD_DAYS; assert BASELINE_COST_THRESHOLD_USD == 10000; assert BASELINE_LOS_THRESHOLD_DAYS == 5; print('State schema OK')"` — prints `State schema OK`.
- Dependencies: STEP 2 complete. STEP 1 complete (.env present).
- Safe to run: Yes (no external calls).

---

**STEP 5: Initialize PostgreSQL Checkpointer**
- Action: Implement `src/graph/checkpointer.py` with an async function `get_checkpointer()` that creates `AsyncPostgresSaver` using `POSTGRESQL_CONNECTION_STRING` from environment variables. Implement `async def setup_checkpointer()` that calls `checkpointer.setup()` to create LangGraph checkpoint tables. Implement a CLI script `python src/graph/checkpointer.py --setup` that runs `setup_checkpointer()`.
- Verification: `python src/graph/checkpointer.py --setup` completes without error. `psql -d pa_agent_db -c "\dt"` shows LangGraph checkpoint tables.
- Dependencies: STEP 4 complete. STEP 2 complete. PostgreSQL instance running. `POSTGRESQL_CONNECTION_STRING` env var set.
- Safe to run: Yes (creates tables if not exist — idempotent).

---

**STEP 6: Implement Utility Modules**
- Action: Implement `src/utils/retry.py` — `@with_retry(max_attempts=3, backoff_seconds=[2, 4, 8])` async decorator that retries on `httpx.TimeoutException`, `httpx.HTTPStatusError` (HTTP 429, 503), and `google.api_core.exceptions.ServiceUnavailable`. Does NOT retry on HTTP 400, 401, 403, or `WorkflowHaltedException`. Implement `src/utils/circuit_breaker.py` — `CircuitBreaker` class with `record_emergency_stop(case_id: str)` that tracks Emergency Stop events by timestamp; `is_circuit_open() -> bool` that returns True if 3 or more Emergency Stops with different case IDs occurred within the last 5 minutes. Implement `src/utils/logger.py` — `structlog` configuration producing JSON log entries with required fields; `log_event(case_id, session_id, agent, event_type, description, audit_log_ref=None)` function that filters PHI values and credential patterns before logging.
- Verification: Unit test `@with_retry`: mock HTTP 503 response → confirm 3 attempts fired with correct delays. Unit test `CircuitBreaker`: record 3 Emergency Stops for different case IDs within 5 minutes → `is_circuit_open()` returns True. Unit test `log_event`: pass a log entry containing a mock credential pattern → confirm credential not present in log output.
- Dependencies: STEP 2 complete.
- Safe to run: Yes (no external calls).

---

**STEP 7: Implement Middleware Components**
- Action: (a) Implement `src/middleware/manifest_validator.py` — load approved integration manifest from `src/config/integration_manifest_v1.0.0.json` (create this JSON file listing all approved endpoint identifiers from AGENT_ORCHESTRATION_BLUEPRINT.md); `validate_endpoint(endpoint_id: str, manifest_version: str) -> bool`. (b) Implement `src/middleware/vault_injection_adapter.py` — `_credential_context: dict[str, any] = {}` module-level dict; `async def inject_vault_credentials(session_id, target_agent) -> bool` (HTTP POST to `SECRET_VAULT_ENDPOINT`); `get_injected_credentials(session_id) -> dict | None`; `clear_credentials(session_id)`; credential values never written to any file, log, or state. (c) Implement `src/middleware/phi_audit_decorator.py` — `@phi_audit_required(phi_fields: list[str])` async decorator: for each field in `phi_fields`, call `write_phi_audit_log.execute()` with field name, action type, agent name, session ID from state; if `success = false` for any field: call `trigger_emergency_stop.execute()` with emergency stop context; raise `WorkflowHaltedException`. Only permit node function to execute if all field audit confirmations return `success = true`.
- Verification: (a) `validate_endpoint("approved-portal-001", "v1.0.0")` returns True. `validate_endpoint("unapproved-system", "v1.0.0")` returns False and logs prohibited action event. (b) `inject_vault_credentials("SES-001", "data_entry_agent")` with mocked Secret Vault → `_credential_context["SES-001"]` populated; confirm no credential value in any log output. (c) Mock `write_phi_audit_log` to fail → decorator raises `WorkflowHaltedException` before node function body executes.
- Dependencies: STEP 6 complete. STEP 5 complete (for Emergency Stop tool reference). `SECRET_VAULT_ENDPOINT`, `SECRET_VAULT_AUTH_TOKEN` env vars set.
- Safe to run: Yes (unit test with mocks).

---

**STEP 8: Implement All 31 Tool Execute Functions**
- Action: For each of the 31 tools in `src/tools/`, implement the `execute(params: dict) -> dict` async function. Each function: (1) defines `SCHEMA` constant (exact JSON schema from AGENT_LOGIC_SPEC.md Section 4); (2) validates `params` against `SCHEMA` using Pydantic; (3) calls `manifest_validator.validate_endpoint()` for tools that call external systems; (4) makes the appropriate HTTP call via `httpx.AsyncClient` to the external system endpoint from environment variables; (5) validates response against expected post-conditions; (6) applies `@with_retry` decorator from `src/utils/retry.py` for transient-retryable tools; (7) classifies failures and returns structured error responses. Implement tools in the sequence defined in Section 4 of this plan (Group 1 first, then Groups 2–5). For `evaluate_whitelist_conditions.execute()`: implement all seven condition evaluations with hardcoded baseline constant comparisons (`BASELINE_COST_THRESHOLD_USD`, `BASELINE_LOS_THRESHOLD_DAYS`). For `prepopulate_portal_fields.execute()` and `prepopulate_mckesson_fields.execute()`: implement clinical field blocklist validation before any HTTP request.
- Verification: For each tool: run `pytest tests/unit/test_<tool_name>.py` with mock HTTP responses from `tests/mocks/` — all assertions pass. Total: 31 tool unit tests must pass.
- Dependencies: STEP 7 complete. STEP 6 complete. All external API endpoint env vars set. `tests/mocks/` JSON files created.
- Safe to run: Yes (unit tests use mocks, no live API calls required).

---

**STEP 9: Create Test Mock JSON Files**
- Action: Create all 32 mock JSON files in `tests/mocks/` as specified in Section 7.1. Each file contains the exact JSON structure defined in Section 7.1. Additionally create mocks not listed in Section 7.1 for: `mock_prepopulate_portal_clinical_field_rejection.json`, `mock_vault_injection_failure.json`, `mock_submit_auth_rejected.json`, `mock_specialist_action_modified.json`. The mock for clinical field rejection: `{"success": false, "result": {"prohibited_field_rejected": true, "fields_written": []}, "error": "Clinical necessity field detected: medical_necessity_determination"}`.
- Verification: `ls tests/mocks/ | wc -l` returns 32 or greater. `python -c "import json; [json.load(open(f'tests/mocks/{f}')) for f in __import__('os').listdir('tests/mocks/')]"` — all files parse as valid JSON without error.
- Dependencies: STEP 1 complete (mocks directory exists).
- Safe to run: Yes (file creation only).

---

**STEP 10: Implement All Five Agent Node Functions**
- Action: Implement each agent's node function in `src/agents/<agent_name>.py`. Each node function follows the Graph-Node ReAct pattern from Section 5. Include: system prompt constant string (exactly per AGENT_LOGIC_SPEC.md Section 1 for that agent), model constant reference, tool sequence per the agent's cognitive spec, precondition checks, `@phi_audit_required` decorator application (Document Processing, Criteria Evaluation, Data Entry nodes), state update dict return. For `data_entry_node`: use `vault_injection_adapter.get_injected_credentials(session_id)` to access credentials in execution context — never read from or write to shared state.
- Verification: For each agent node function: run `pytest tests/unit/test_<agent_name>.py` with mock state dict and mock tool responses — confirm correct state update dict returned and correct tool call sequence observed. Run all agent unit tests: `pytest tests/unit/ -v` — all pass.
- Dependencies: STEP 8 complete (all tools implemented). STEP 7 complete (decorators available). STEP 4 complete (state schema).
- Safe to run: Yes (unit tests, mocks only).

---

**STEP 11: Wire LangGraph State Graph**
- Action: Implement `src/graph/graph_builder.py`. Define `StateGraph(PACaseState)`. Add all nodes using `add_node()` with node function references from `src/agents/`. Add all edges using `add_edge()` for sequential connections. Add conditional edges from `mode_routing_node` using the routing function: check `state["criteria_evaluation"]["all_whitelist_conditions_met"]` — True routes to `mode_a_execution_node`, False routes to `mode_b_handoff_node`. Add `interrupt_before=["mode_b_specialist_action_node"]` for the Mode B approval gate. Add emergency stop routing: every node's execution function checks `state["current_context"]["active_mode"] == "suspended"` at entry and raises `WorkflowHaltedException` if True. Add `START` edge to `session_auth_node` only. Compile the graph: `graph = builder.compile(checkpointer=get_checkpointer(), interrupt_before=["mode_b_specialist_action_node"])`. Expose `graph` as a module-level variable.
- Verification: `python -c "from src.graph.graph_builder import graph; mermaid = graph.get_graph().draw_mermaid(); print(mermaid)"` — Mermaid diagram shows: START → session_auth → proxy_check → credential_injection → document_processing → criteria_evaluation → mode_routing → (conditional) → mode_a_execution OR mode_b_handoff. No cycles in sequential path. `interrupt_before` confirmed on Mode B specialist action node. Run `pytest tests/unit/test_state_schema.py tests/unit/test_whitelist_conditions.py` — all pass.
- Dependencies: STEP 10 complete. STEP 5 complete.
- Safe to run: Yes (graph compilation, no external calls).

---

**STEP 12: Implement SLA Monitor Parallel Task Manager**
- Action: Implement `src/sla/sla_monitor_thread.py`. `SLAMonitorManager` class with: `_active_tasks: dict[str, asyncio.Task]` and `_case_alert_state: dict[str, dict]` (tracks which alerts have fired per case); `async def register_case(case_id, intake_timestamp, assigned_specialist_id)` — adds to active set, starts asyncio task; `async def _monitor_loop(case_id, intake_timestamp, assigned_specialist_id)` — polling loop every 300 seconds calling `get_case_elapsed_times.execute()`, evaluating 48h/60h/66h thresholds, calling `trigger_sla_alert.execute()` exactly once per threshold per case, calling `reroute_to_high_priority_queue.execute()` at 66h after code_red alert confirmed; `async def deregister_case(case_id)` — cancels asyncio task, removes from active dict. `SLAMonitorManager` instance initialized as a module-level singleton. Circuit breaker check: at each polling cycle, if `circuit_breaker.is_circuit_open()`: pause polling until circuit is cleared.
- Verification: Unit test with `pytest tests/unit/test_sla_monitor_thread.py`: register mock case with `intake_timestamp` = 47.9 hours ago; fast-forward mock clock to 48h; confirm `trigger_sla_alert` called with `alert_level = "standard"` exactly once. Advance to 60h; confirm `trigger_sla_alert` called with `alert_level = "critical"` exactly once. Advance to 66h; confirm `trigger_sla_alert` with `alert_level = "code_red"` and `reroute_to_high_priority_queue` called.
- Dependencies: STEP 8 complete (SLA monitor tools). STEP 6 complete (circuit breaker).
- Safe to run: Yes (unit test, mocks).

---

**STEP 13: Build FastAPI Backend Server**
- Action: Implement `src/api/main.py` with `FastAPI()` app instantiation, CORS middleware (allow origins: `FRONTEND_ORIGIN` from env), startup event handler (calls `setup_checkpointer()` and initializes `SLAMonitorManager`). Implement all routes from `src/api/routes/`: (a) `session.py` — `POST /session/initiate`: validates session initiation payload, creates initial state, calls `graph.invoke(initial_state, config={"configurable": {"thread_id": case_id}})` asynchronously, returns session handle and SSE stream URL; (b) `workflow.py` — `GET /workflow/{case_id}/stream`: SSE endpoint using `sse-starlette`; holds `asyncio.Queue` open per case_id; yields events from the queue as `EventSourceResponse`; sends keepalive comment every 10 seconds; (c) `specialist.py` — `WS /workflow/{case_id}/action`: WebSocket endpoint; on connect: sends Mode B package from shared state; on receive: validates specialist action payload, calls `graph.update_state(config, {"current_context": {"specialist_action": action_object, "awaiting_human_action": False}})` to release LangGraph interrupt, confirms action logged; (d) `admin.py` — `POST /admin/emergency-stop`: role-authenticated UM Manager endpoint; calls `trigger_emergency_stop.execute()` with scope and reason; `POST /admin/restart`: role-authenticated; calls `graph.update_state` to release suspended state. Implement `src/api/events.py` with dataclasses for all 11 event types from Section 6.
- Verification: Start server: `uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload`. `curl https://bridge-pa-production.up.railway.app/health` returns 200 OK. `curl -X POST https://bridge-pa-production.up.railway.app/session/initiate -H "Content-Type: application/json" -d '{"case_id":"TEST-HEALTH","specialist_id":"SP-001","session_token":"TEST-TOKEN","case_type":"concurrent_review"}'` returns 200 with session handle.
- Dependencies: STEP 11 complete (graph compiled). STEP 12 complete (SLA manager). STEP 2 complete (FastAPI installed). `sse-starlette` added to `requirements.txt` and installed.
- Safe to run: Yes (server starts on localhost).

---

**STEP 14: Implement SSE Event Emitter and WebSocket Handler**
- Action: Implement `src/api/streaming/sse_emitter.py` — `SSEEmitter` class with: `_queues: dict[str, asyncio.Queue]`; `get_or_create_queue(case_id) -> asyncio.Queue`; `async def emit(case_id, event_type, data_dict)` — constructs SSE event with `event` and `data` fields and puts it in the case's queue; `emit` is called from all agent node functions and tool execute functions via the observability hooks defined in Section 6. SSE emitter instance is a module-level singleton imported by all agent node functions. Implement `src/api/streaming/ws_handler.py` — `WebSocketHandler` class managing WebSocket connections per case_id; `async def send_mode_b_package(case_id, package)` — sends Event Type 9 to connected client; `async def receive_specialist_action(case_id) -> dict` — awaits Event Type 10 from client, validates payload, returns action dict. Add SSE emit calls into all 5 agent node functions and all 31 tool execute functions at the observability hook points defined in Section 6.
- Verification: Use a mock SSE client: `curl -N https://bridge-pa-production.up.railway.app/workflow/TEST-CASE-001/stream` while running a test LangGraph invocation with mock tools → confirm SSE events arrive in correct sequence: `step_status` for Steps 1–3, `phi_audit_confirmed`, `whitelist_conditions`, `routing_decision`, and either Mode A completion or Mode B package WebSocket event.
- Dependencies: STEP 13 complete (server running). STEP 10 complete (agent nodes with emit hook points). STEP 8 complete (tool execute functions with emit hook points).
- Safe to run: Yes (requires server running).

---

**STEP 15: Build Frontend Interface**
- Action: Implement all frontend components in `frontend/src/` as specified in INTERFACE_OBSERVABILITY_SYSTEM.md Section 2. (a) `useSSEStream.ts` hook — opens `EventSource` to `/workflow/{case_id}/stream`; parses all 11 event types; updates React state via `useReducer` with typed event handlers per event type; implements 10-second keepalive timeout detection (if no event received in 10s during active step, set liveness indicator to `reconnecting`). (b) `useWebSocket.ts` hook — opens WebSocket to `/workflow/{case_id}/action` when `routing_decision.mode = "mode_b"` received; handles send/receive for Mode B approval gate; closes on specialist action confirmed. (c) `WorkflowTimeline.tsx` — renders 8 step cards from SSE state; each `StepCard.tsx` shows status icon, step label, summary line, expandable tool call sub-steps, audit confirmation indicator; `ConditionTable.tsx` renders all 7 whitelist conditions when Step 5 completes (always fully visible). (d) `ActivityLog.tsx` — right sidebar; renders all `activity_log_entry` events in chronological order with timestamps and category badges. (e) `ModeBReviewPanel.tsx` — full-panel replacement for WorkflowTimeline when `mode_b_package` received; renders Full Recommendation Package exactly per INTERFACE_OBSERVABILITY_SYSTEM.md Section 4 (Mode B Handoff); `Approve`, `Modify`, `Override` buttons each open a rationale input step before submission; sends via WebSocket. (f) `EmergencyStopButton.tsx` — always rendered in `SLAHeader.tsx`; POST to `/admin/emergency-stop` on click with confirmation dialog. (g) `SystemBanner.tsx` — renders `emergency_stop` and `sla_alert` events as full-width banners; Emergency Stop banner non-dismissible. (h) `SessionInit.tsx` — session initiation form with `case_id`, `specialist_id`, `session_token` fields; POST to `/session/initiate` on submit.
- Verification: `cd frontend && npm run dev` starts dev server on `localhost:3000`. Navigate to `http://localhost:3000`. Session initiation form renders. Submit TEST-CASE-001 credentials → workflow timeline renders → step cards update in real time as mock SSE events arrive → all 7 whitelist conditions visible in Step 5 card → routing decision visible → Mode A: submission confirmed and case closed card renders. Emergency Stop button always visible in header.
- Dependencies: STEP 14 complete (SSE and WebSocket backend working). STEP 3 complete (frontend dependencies installed).
- Safe to run: Yes (frontend only — no backend writes).

---

**STEP 16: Run Integration Tests**
- Action: Run all integration tests in `tests/integration/` using `pytest tests/integration/ -v`. Each integration test file uses mocked external API calls (via `httpx` mock or `pytest-httpx`) but real LangGraph graph execution with an in-memory checkpointer (substitute `MemorySaver` for `AsyncPostgresSaver` in test configuration). Tests must cover: Mode A happy path end-to-end, Mode B full path with specialist approval, Mode B with override, Emergency Stop on `write_phi_audit_log` failure, Emergency Stop on `verify_session_authorization` failure, prohibited clinical field write attempt, out-of-scope case type rejection, parity mismatch halt, SLA alert triggering, circuit breaker activation.
- Verification: `pytest tests/integration/ -v` — all tests pass. Zero failures. Zero skipped.
- Dependencies: STEPS 10–15 complete.
- Safe to run: Yes (integration tests use mocks — no live API calls).

---

**STEP 17: End-to-End Verification**
- Action: With server running and frontend running, execute the 6 test scenarios from Section 7.1 using live API calls (Gemini API live; external systems can use staging endpoints or mocked via test harness). For each scenario: (1) Submit session initiation; (2) Observe SSE stream events in correct sequence; (3) Verify all "Agent Is Working" success criteria from Section 7.1; (4) Verify all failure scenarios from Section 7.1; (5) Check `pa_agent.log` confirms all expected log entries present and no PHI values or credential values logged; (6) Check PostgreSQL checkpointer — confirm state snapshots present for each test case.
- Verification: All 12 "Agent Is Working" success criteria pass. All 10 failure scenarios produce the expected response (correct SSE event, correct state, correct UM Manager notification). Log file inspection: 0 PHI values found. 0 credential values found. Baseline constants: confirm still equal to 10000 and 5 after all test runs.
- Dependencies: STEPS 1–16 complete.
- Safe to run: Yes (final test — uses live Gemini API, staging external systems).

---

**STEP 18: Production Readiness Check**
- Action: (1) Confirm `.env.example` has all variable names with no values. (2) Confirm `.env` is in `.gitignore`. (3) Set `ENVIRONMENT=production` and `LOG_LEVEL=INFO` in production env. (4) Confirm CORS middleware allows only `FRONTEND_ORIGIN` (not `*`). (5) Confirm `/admin/emergency-stop` and `/admin/restart` endpoints have UM Manager role authentication enforced. (6) Confirm `_credential_context` in vault adapter is not persisted to disk or any external store. (7) Run `pytest tests/ -v` — all unit and integration tests pass. (8) Confirm baseline constants in `state_schema.py` are hardcoded integers, not read from environment variables (they cannot be changed by configuration). (9) Confirm LangGraph graph has no cycles via Mermaid diagram review. (10) Confirm Emergency Stop mechanism works with real `trigger_emergency_stop.execute()` call (not mocked). (11) Confirm PostgreSQL checkpointer retains suspended case state after server restart.
- Verification: All 11 production readiness checks above pass. `pytest tests/ -v` — zero failures. Grep log file for credential pattern strings — zero results. Grep log file for known PHI test data values — zero results.
- Dependencies: STEP 17 complete.
- Safe to run: Yes (verification only — no configuration changes).

---

## **EXECUTION PLAN INTEGRITY DECLARATION**

This master plan is AUTHORITATIVE and COMPLETE.

Downstream code generation systems must:
- Execute steps in exact order specified (STEPS 1–18)
- Verify each step before proceeding to the next
- Never skip steps
- Never combine steps
- Never invent logic not specified in AGENT_ORCHESTRATION_BLUEPRINT.md, AGENT_LOGIC_SPEC.md, or INTERFACE_OBSERVABILITY_SYSTEM.md
- Never modify baseline threshold constants (`BASELINE_COST_THRESHOLD_USD = 10000`, `BASELINE_LOS_THRESHOLD_DAYS = 5`)
- Halt on verification failure — do not proceed
- Use only the model strings specified: `gemini-2.5-pro` and `gemini-2.5-flash`
- Use only the framework specified: LangGraph with PostgreSQL checkpointer
- Implement all 31 tools exactly per schemas in AGENT_LOGIC_SPEC.md Section 4
- Apply `@phi_audit_required` decorator to all three PHI-touching agent nodes
- Implement `interrupt_before` on the Mode B specialist action node — no exceptions
- Never write credentials or PHI field values to any log, state snapshot, or SSE event
- Enforce all 12 prohibitions structurally as specified in Section 7

This plan eliminates all execution ambiguity.
Every dependency is explicit.
Every verification is defined.
Every failure mode is anticipated.

Implementation is deterministic and mechanical.

---
