# Bridge-PA

**HIPAA-Compliant Prior Authorization Orchestration System**

Bridge-PA is a deterministic, multi-agent orchestration system built on LangGraph and Google Gemini,
designed to automate concurrent review Prior Authorization workflows for UM Specialists.

## Technology Stack

- **Orchestration:** LangGraph (Python) with PostgreSQL checkpointer
- **LLM:** Google Gemini 2.5 Pro / 2.5 Flash (`google-generativeai` SDK)
- **Backend:** FastAPI + Python 3.12
- **Frontend:** React 18 + TypeScript + Tailwind CSS + Shadcn/UI
- **Streaming:** Server-Sent Events (SSE) + WebSocket
- **Audit:** Veea Lobster Trap PHI Audit Proxy
- **Secrets:** Enterprise Secret Vault Injection Adapter

## Setup

1. Copy `.env.example` to `.env` and populate all values.
2. Create virtual environment: `python3.12 -m venv .venv && source .venv/bin/activate`
3. Install Python dependencies: `pip install -r requirements.txt`
4. Install frontend dependencies: `cd frontend && npm install`
5. Initialize PostgreSQL checkpointer: `python src/graph/checkpointer.py --setup`
6. Start backend: `uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload`
7. Start frontend: `cd frontend && npm run dev`

## Security

- PHI never persists in agent memory — enforced by `@phi_audit_required` decorator
- All PHI field access logged to Veea Lobster Trap before access
- Credentials injected at runtime via Enterprise Secret Vault — never stored in state or logs
- Baseline safety thresholds hardcoded as constants — not runtime-configurable

## Execution Plan

See `AGENT_MASTER_PLAN.md` for the 18-step deterministic execution sequence.
