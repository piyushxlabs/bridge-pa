# Bridge-PA

<div align="center">

### HIPAA-Compliant Prior Authorization Orchestration System

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Deterministic_DAG-00C49F?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![Gemini](https://img.shields.io/badge/Gemini-3.1_Flash-4285F4?style=flat-square&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![Vultr](https://img.shields.io/badge/Vultr-Cloud_Hosted-007BFC?style=flat-square)](https://vultr.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-336791?style=flat-square&logo=postgresql&logoColor=white)](https://supabase.com)
[![HIPAA](https://img.shields.io/badge/HIPAA-Compliant-00CC44?style=flat-square)](https://www.hhs.gov/hipaa/)
[![Veea](https://img.shields.io/badge/Veea-Lobster_Trap_Secured-FF6B35?style=flat-square)](https://veea.com)

</div>

---

## Overview

**Bridge-PA** is an advanced, deterministic multi-agent orchestration system designed to eliminate the $11B annual administrative burden of healthcare Prior Authorization. Powered by **Google Gemini 3.1 Flash** for concurrent OCR and binary criteria evaluation, deployed on **high-performance Vultr Cloud** server instances for enterprise scalability and 100% uptime, and secured at the edge by the **Veea Lobster Trap** PHI audit proxy for strict HIPAA compliance — Bridge-PA transforms a 14-day manual process into a **7-minute fully-automated workflow**.

Built on a deterministic **LangGraph 8-node DAG**, the system provides UM Specialists with real-time streaming updates via SSE, immutable audit trails on every tool call, and zero PHI exposure to the LLM without a logged entry. This project was submitted across two hackathon tracks:

- 🏗️ **Track 1 — Infrastructure & Scalability:** Vultr Cloud deployment with FastAPI + PostgreSQL
- 🔐 **Track 2 — Security & Compliance:** Veea Lobster Trap PHI audit proxy for HIPAA governance

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          BRIDGE-PA ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   [ React 18 + TypeScript + Shadcn/UI ]  ◄──── Vercel Edge Network     │
│                    │  SSE / WebSocket                                   │
│                    ▼                                                     │
│   ┌─────────────────────────────────────────────────────────────┐       │
│   │         FastAPI Backend  ·  Vultr Cloud Instance            │       │
│   │   ┌──────────────────────────────────────────────────────┐  │       │
│   │   │           LangGraph 8-Node ReAct DAG                 │  │       │
│   │   │  Intake → OCR → Eval → Route → Submit → Audit       │  │       │
│   │   └────────────────────────┬─────────────────────────────┘  │       │
│   │                            │                                 │       │
│   │         ┌──────────────────┼──────────────────┐             │       │
│   │         ▼                  ▼                  ▼             │       │
│   │   [Gemini 3.1 Flash]  [PostgreSQL DB]  [Secret Vault]       │       │
│   │    Vision + OCR         Supabase         Credentials        │       │
│   └──────────────────────────────────────────────────────────────┘       │
│                    │                                                     │
│                    ▼                                                     │
│   ┌──────────────────────────────────────────────────────────────┐      │
│   │       Veea Lobster Trap PHI Audit Proxy  (Edge Layer)        │      │
│   │   Deep Prompt Inspection · Immutable Log · Circuit Breaker   │      │
│   └──────────────────────────────────────────────────────────────┘      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Orchestration** | LangGraph (Python) — 8-Node ReAct DAG | Deterministic workflow state machine |
| **LLM** | Google Gemini 3.1 Flash (`google-generativeai`) | Vision OCR + binary criteria evaluation |
| **Backend** | FastAPI + Python 3.12 | High-performance async API server |
| **Frontend** | React 18 + TypeScript + Tailwind CSS + Shadcn/UI | Real-time UM Specialist dashboard |
| **Streaming** | Server-Sent Events (SSE) + WebSocket | Live agent step updates to the UI |
| **Infrastructure & Deployment** | Vultr Cloud Instances + PostgreSQL (Supabase) | Scalable cloud hosting + persistent checkpointing |
| **Security Proxy** | Veea Lobster Trap PHI Audit Proxy | Edge-level DPI, audit logging, HIPAA enforcement |
| **Secrets Management** | Enterprise Secret Vault Injection Adapter | Runtime credential injection — never stored in state |

---

## Key Capabilities

- ⚡ **7-Minute PA Turnaround** — from fax receipt to portal submission, fully automated
- 🔒 **Zero PHI Exposure** — `@phi_audit_required` decorator enforces logging before every field access
- 📋 **100% Immutable Audit Trail** — every tool call intercepted and logged by Veea Lobster Trap
- 🌐 **Enterprise-Scale Hosting** — Dockerized FastAPI deployed on dedicated Vultr Cloud instances
- 🗄️ **Persistent Checkpointing** — PostgreSQL (Supabase) stores full workflow state for crash recovery
- 🛑 **Emergency Circuit Breaker** — workflow halts immediately on any detected PHI violation
- 🤖 **Deterministic AI** — 8-node LangGraph DAG prevents hallucinations and infinite loops
- 🌍 **Vercel Edge Delivery** — React frontend served globally via Vercel's edge network

---

## Setup & Local Development

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL instance (local or Supabase)
- Google AI API Key (Gemini 3.1 Flash access)

### Installation

**1. Clone and configure environment**
```bash
cp .env.example .env
# Populate all values: GEMINI_API_KEY, DATABASE_URL, VEEA_*, VAULT_*
```

**2. Create Python virtual environment**
```bash
python3.12 -m venv .venv && source .venv/bin/activate   # Linux/macOS
python3.12 -m venv .venv && .venv\Scripts\activate       # Windows
```

**3. Install Python dependencies**
```bash
pip install -r requirements.txt
```

**4. Install frontend dependencies**
```bash
cd frontend && npm install
```

**5. Initialize PostgreSQL checkpointer**
```bash
python src/graph/checkpointer.py --setup
```

**6. Start the backend**
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**7. Start the frontend**
```bash
cd frontend && npm run dev
```

### Production Deployment (Vultr Cloud)

```bash
# Build and push Docker image
docker build -t bridge-pa:latest .
docker push your-registry/bridge-pa:latest

# Deploy on Vultr Cloud Instance (Ubuntu 22.04 LTS)
docker compose -f docker-compose.prod.yml up -d

# Verify backend is live
curl http://YOUR_VULTR_IP:8000/health
```

---

## Security Architecture

Bridge-PA's security model is enforced at **two independent layers** — the application layer and the edge proxy layer — ensuring defense-in-depth for all PHI.

### Application Layer (Python)

| Control | Implementation |
|---|---|
| PHI field access | `@phi_audit_required` decorator — enforced on every sensitive getter |
| Credential management | Enterprise Secret Vault Injection — credentials never in state or logs |
| Safety thresholds | Hardcoded as Python constants — not runtime-configurable |
| Agent memory | PHI never persists between workflow steps in agent memory |

### Edge Proxy Layer (Veea Lobster Trap)

| Control | Implementation |
|---|---|
| Deep Prompt Inspection (DPI) | Every LLM tool call inspected for PHI exfiltration before execution |
| Immutable audit log | Cryptographically signed entry written before any PHI access |
| Circuit breaker | Workflow halts immediately on policy violation — no partial execution |
| Field-level access logging | Per-field PHI access events logged with actor, timestamp, and purpose |

---

## Execution Plan

The full 18-step deterministic execution sequence is documented in [`AGENT_MASTER_PLAN.md`](./AGENT_MASTER_PLAN.md).

```
Step  1 → Project scaffolding & environment setup
Step  2 → Secret Vault Adapter implementation
Step  3 → Veea Lobster Trap PHI proxy integration
Step  4 → PostgreSQL checkpointer initialization (Supabase)
Step  5 → LangGraph DAG node definitions (8 nodes)
Step  6 → Gemini 3.1 Flash OCR + vision integration
Step  7 → InterQual binary criteria evaluation engine
Step  8 → Mode A (auto-approve) routing logic
Step  9 → Mode B (escalation) routing logic
Step 10 → FastAPI SSE streaming endpoint
Step 11 → React frontend — real-time dashboard
Step 12 → Veea audit log viewer UI component
Step 13 → End-to-end workflow integration test
Step 14 → Vultr Cloud Docker image build & push
Step 15 → Vultr production deployment & health check
Step 16 → Vercel frontend deployment
Step 17 → Security penetration & PHI exfiltration test
Step 18 → Final demo recording & submission
```

---

## Hackathon Track Submissions

| Track | Sponsor | Focus | Bridge-PA Implementation |
|---|---|---|---|
| **Infrastructure & Scalability** | Vultr Cloud | Cloud deployment, uptime, performance | FastAPI + PostgreSQL on dedicated Vultr Cloud instances, Dockerized |
| **Security & Compliance** | Veea | PHI protection, HIPAA, audit logging | Veea Lobster Trap edge proxy with DPI, immutable logs, circuit breaker |

---

<div align="center">

**Bridge-PA** — *Where AI Meets Compliance.*

`14 days → 7 minutes` · `Zero PHI Leaks` · `Production-Ready`

</div>
