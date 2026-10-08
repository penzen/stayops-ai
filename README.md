# StayOps AI

[![StayOps CI](https://github.com/penzen/stayops-ai/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/penzen/stayops-ai/actions/workflows/ci.yml)

**StayOps is a bounded AI guest-operations system for short-term-rental teams.**

It combines an LLM agent with deterministic operational workflows, persistent Case ownership, human handoffs, financial review, retrieval-augmented operational knowledge, audit trails, and a human operations dashboard.

The core design principle is simple:

> **Use AI for ambiguity. Use normal software for certainty.**

The agent can interpret messy guest messages, understand context, choose tools, retrieve operational guidance, and decide what needs attention.

It cannot bypass deterministic business rules, directly manipulate the database, approve compensation, resolve Cases without evidence, or act outside explicitly exposed capabilities.

---

## Demo

![StayOps AI dashboard](assets/stayops-dashboard.png)

**Live demo:** https://d8hbj9y50bgwb.cloudfront.net

The V5 demo includes isolated public demo sessions, synthetic guest stays, an operational overview, guest directory/detail views, global search, and workflows such as:

- heating failures
- plumbing incidents
- access issues
- operational tasks
- human escalation
- Case ownership
- technician assignment
- compensation requests
- human financial decisions
- multi-turn follow-ups
- deterministic Case resolution
- cross-page Case, guest, and booking navigation

---

# Why StayOps exists

A useful operations agent has to do more than generate a good reply.

It needs to answer questions such as:

> Which guest and booking is this about?

> Is this a new issue or a follow-up to an existing one?

> What operational procedure applies?

> Is the agent allowed to act?

> Does a technician need to be assigned?

> Does a human need to take ownership?

> Has the requested action actually happened?

> Is there enough evidence to close the issue?

> If a guest requests compensation, which operational incident caused it?

StayOps treats those as **system-design problems**, not just prompting problems.

---

# Core architecture

<p align="center">
  <img
    src="assets/stayops-architecture.png"
    alt="StayOps V5 core architecture"
    width="760"
  >
</p>

<p align="center">
  <em>
    The LLM handles ambiguity and tool selection; deterministic services own
    permissions, state transitions, financial authority, and persistence.
  </em>
</p>


The production path intentionally uses **one Guest Operations Agent**.

The system does not use multiple agents simply because the problem can be described as "agentic." Separate deterministic services and human workflows are used where they provide stronger control.

For the dedicated architecture document, see:

[assets/architecture.md](assets/architecture.md)

---

# AI versus deterministic responsibility

```text
                       StayOps
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
             LLM               Deterministic code
              │                       │
      intent interpretation        validation
      issue classification         permissions
      context selection            persistence
      tool choice                  Case lifecycle
      ambiguity handling           idempotency
      guest communication          database writes
      new-vs-follow-up reasoning    financial authority
              │                    resolution gates
              │                       │
              └───────────┬───────────┘
                          ▼
                   bounded autonomy
```

The model is deliberately used where interpretation is valuable.

Normal software owns the parts where correctness should not depend on model behavior.

---

# Case-centric operational model

StayOps V3 introduces a persistent **Case** model for operational ownership.

A guest may have several unrelated problems during the same booking.

```text
Guest
  ↓
Booking
  │
  ├── Heating Case
  ├── Plumbing Case
  ├── Access Case
  └── Refund Case
```

Each Case has its own:

- `case_id`
- booking
- property
- issue category
- workflow status
- summary
- human owner
- creation time
- resolution time

Tasks and escalations belong to Cases.

Messages remain booking-level because one guest message can legitimately affect multiple Cases.

---

## Case states

```text
open
  ↓
in_progress
  ↓
waiting_guest
  ↓
waiting_human
  ↓
resolved
```

The states describe **what must happen next**, not merely which records already exist.

### `open`

The Case has been created.

### `in_progress`

StayOps can continue work without waiting for the guest or a human.

### `waiting_guest`

The workflow requires information or confirmation from the guest.

### `waiting_human`

Progress requires a human operator, technician, approval, or another capability outside agent authority.

### `resolved`

The deterministic resolution gate has confirmed that the Case satisfies its resolution conditions.

---

# Case resolution is evidence-gated

The agent cannot simply decide:

> "The problem looks fixed, so I'll mark it resolved."

Case resolution is handled separately from normal workflow updates.

```text
Agent believes issue may be complete
            ↓
attempt_case_resolution
            ↓
deterministic checks
            │
            ├── required resolution evidence?
            ├── open tasks?
            └── open escalations?
            ↓
       resolve or block
```

A created task is not proof of resolution.

A created escalation is not proof of resolution.

A polite guest response is not proof of resolution.

Even completed human work is not automatically equivalent to the guest's underlying issue being resolved.

For example:

```text
Heating task completed
        +
Heating escalation resolved
        ↓
Human work complete

Guest confirms heating works
        ↓
Resolution evidence

Deterministic resolution gate
        ↓
Heating Case resolved
```

---

# Human handoff

Human escalation is not treated as agent failure.

It is a valid and often correct outcome.

```text
Agent
  ↓
determines human action is required
  ↓
creates/reuses escalation
  ↓
Case → waiting_human
  ↓
Human Operations Queue
  ↓
Operator claims Case
  ↓
Human performs bounded actions
```

Once a Case is claimed, human actions are tied to that operator.

This prevents an arbitrary dashboard user from performing actions on a Case owned by somebody else.

---

# Human Operations Dashboard

StayOps includes an operations interface for Cases waiting on human action.

The dashboard provides:

- human Case queue
- guest and booking context
- property context
- Case ownership
- conversation history
- technician assignment
- task completion
- escalation resolution
- financial review
- compensation evidence
- Case audit timeline
- return-to-agent control

The frontend is intentionally separated into focused components:

```text
frontend/src/app/operations/
├── page.tsx
├── constants.ts
├── types.ts
├── utils.ts
└── components/
    ├── CaseOverview.tsx
    ├── ConversationPanel.tsx
    ├── EscalationPanel.tsx
    ├── FinancialReview.tsx
    ├── QueueList.tsx
    ├── TaskPanel.tsx
    └── Timeline.tsx
```

`page.tsx` primarily owns orchestration, API interaction, and state.

Presentation concerns are kept in dedicated components.

---

# Tasks and technicians

Operational tasks belong to Cases.

```text
Heating Case
    ↓
Operational task
    ↓
Maintenance technician
```

Technicians are loaded from the backend operational database rather than hard-coded into the UI.

Task assignment validates that the selected worker belongs to the technical maintenance team.

The human who owns the Case and the technician performing field work are separate concepts:

```text
Case operator
    ≠
Task technician
```

---

# Escalations

Escalations represent human attention required by a Case.

Supported operational categories include:

- access
- plumbing
- heating
- electrical
- maintenance
- safety
- cleaning
- wifi
- refund
- other

Open escalations contribute to Case workflow state and deterministic resolution checks.

The system also prevents refund workflows from bypassing the dedicated financial orchestration path.

---

# Refund and compensation architecture

Refund handling is intentionally separated from normal operational work.

The Guest Operations Agent does **not** have financial authority.

It cannot:

- approve compensation
- deny compensation
- determine a final refund amount
- invent a refund percentage
- promise payment
- claim a refund has been approved without a recorded human decision

A financial request creates or reuses a dedicated **Refund Case**.

```text
Guest requests refund
        ↓
ensure_refund_workflow
        ↓
Refund Case
        ↓
Compensation Request
        ↓
Financial escalation
        ↓
waiting_human
        ↓
Authorized human decision
```

The deterministic `ensure_refund_workflow` service owns this orchestration.

The agent is not expected to manually assemble the workflow from lower-level tools.

---

# Operational Case ↔ Refund Case relationship

A refund often exists because another operational problem occurred.

Those remain separate Cases.

Example:

```text
Booking
   │
   ├── Heating Case
   │      case_heating_123
   │
   └── Refund Case
          case_refund_456
               │
               ↓
        Compensation Request
        related_case_id =
        case_heating_123
```

The relationship is stored on the compensation request using the existing operational `case_id`.

No artificial third Case is created just to connect them.

This means the financial reviewer can see the operational evidence that caused the request.

---

## Mixed operational + financial messages

A single guest message may contain both intents:

> "The heating has been broken all evening. I want a full refund."

StayOps handles both workflows:

```text
Guest message
     ↓
Heating Case
     ├── heating task
     ├── heating escalation
     └── waiting_human
     │
     │ related_case_id
     ▼
Refund Case
     ├── compensation request
     ├── financial escalation
     └── waiting_human
```

The agent is instructed to process the operational problem and preserve its Case ID when the financial relationship is clear.

The deterministic service layer also provides a safety net.

If `related_case_id` is missing:

```text
Exactly one matching operational Case
        ↓
link automatically

Multiple possible operational Cases
        ↓
do not guess
```

An existing compensation request with no relationship can also be safely backfilled later when the relationship becomes unambiguous.

An already-established relationship is never overwritten automatically.

---

# Compensation evidence

Human reviewers receive a deterministic evidence package.

It can include:

- compensation request
- refund Case
- related operational Case
- booking
- property
- related tasks
- related escalations
- open task count
- open escalation count
- recorded financial decision

Example:

```text
Compensation Review

Requested outcome
Full refund

Related operational Case
Heating · resolved

Operational tasks
1 total
0 open
Restore heating → completed

Operational escalations
1 total
0 open
Heating escalation → resolved
```

Importantly, the evidence relationship survives after the operational Case resolves.

```text
Heating Case
waiting_human
      ↓
in_progress
      ↓
resolved
      │
      │ persistent related_case_id
      ▼
Compensation Request
```

A later financial reviewer still sees the historical incident, completed task, and resolved escalation.

---

# Human financial authority

A compensation request remains pending until an authorized human records a decision.

Before a financial decision can be written:

- the Refund Case must be `waiting_human`
- the Refund Case must be claimed
- the decision-maker must be the operator who owns the Case

Possible final decisions:

```text
approved
denied
```

An approved decision requires:

- amount
- currency
- reason
- human actor

A denied decision requires:

- reason
- human actor

The decision is persisted separately from the model response.

---

# Historical refund safety

A resolved refund workflow should not be recreated simply because a guest later asks:

> "Was my refund completed?"

StayOps distinguishes a historical follow-up from a genuinely new request.

```text
Previous resolved Refund Case
        ↓
Guest asks for status
        ↓
reuse historical workflow
        ↓
NO duplicate Refund Case
NO duplicate compensation request
NO duplicate escalation
```

A distinct new financial request can explicitly create a new workflow.

---

# Idempotency

Repeated turns should not multiply operational records.

StayOps uses deterministic reuse logic for:

- Cases
- tasks
- escalations
- compensation requests
- refund workflows

```text
Same unresolved issue
        ↓
matching active record?
    ┌───────┴───────┐
   yes              no
    │                │
  reuse            create
```

Idempotency is validated against database state, not simply inferred from whether a tool was called.

---

# Follow-up and multi-turn reasoning

The agent receives bounded operational context for the booking.

This allows messages such as:

> "It is still broken."

> "Nobody has fixed it yet."

> "Any update?"

> "It happened again."

to be interpreted against existing Case state.

If a follow-up clearly belongs to an active Case, the agent reuses it.

If several Cases could plausibly match, StayOps does not create a generic replacement Case.

It asks for the minimum clarification required.

---

# Structured operational playbooks

Operational workflow rules are represented as structured playbooks.

Playbooks define things such as:

- required checks
- safe guest actions
- prohibited actions
- operational actions
- priority rules
- escalation conditions
- resolution conditions

The agent uses them as authoritative operational policy.

```text
Guest issue
    ↓
identify category
    ↓
load structured playbook
    ↓
perform bounded workflow
```

This is separate from semantic knowledge retrieval.

---

# SQL versus RAG

StayOps separates:

> **What is true now?**

from:

> **How should this situation be handled?**

```text
                     Agent
                ┌──────┴──────┐
                ▼             ▼
             SQLite         Qdrant
                │             │
          current truth    expertise
                │             │
             guests          SOPs
             bookings        procedures
             Cases           STR knowledge
             tasks
             escalations
             decisions
```

### SQLite is operational truth

SQLite stores current state such as:

- guests
- bookings
- properties
- Cases
- tasks
- escalations
- incidents
- messages
- compensation requests
- compensation decisions
- Case events
- team members
- access configuration

### Qdrant is operational expertise

Qdrant contains:

- StayOps internal SOPs
- short-term-rental operational knowledge
- troubleshooting guidance
- reusable procedural knowledge

Internal StayOps SOPs take precedence over broader retrieved guidance.

> **SQL tells the agent what is true. RAG tells the agent how to handle it.**

---

# MCP as a capability boundary

The LLM never receives arbitrary database access.

Instead:

```text
LLM
 ↓
MCP tool
 ↓
deterministic service
 ↓
validation / permission check
 ↓
SQLite
```

Examples of bounded operational tools include:

- guest lookup
- reservation lookup
- property lookup
- access verification
- Case lookup
- Case context lookup
- operational Case creation/reuse
- Case workflow transitions
- Case resolution attempts
- task creation/reuse
- escalation creation/reuse
- playbook retrieval
- refund workflow orchestration
- compensation evidence lookup

The Knowledge MCP is read-only during agent execution.

> **The agent gets tools, not unlimited power.**

---

# Conversation persistence

Conversation persistence does not depend on the LLM remembering to save messages.

```text
Guest sends message
        ↓
FastAPI
        ↓
persist guest message
        ↓
run agent
        ↓
receive final response
        ↓
persist agent message
        ↓
return response
```

Messages are stored at booking level so the same conversation can provide context across multiple related Cases.

---

# Audit trail

Important Case actions produce persisted Case events.

Examples include:

- Case created
- status changed
- operator claimed Case
- task created
- task assigned
- task completed
- escalation created
- escalation resolved
- compensation review created
- operational Case linked to compensation
- compensation decision recorded
- Case returned to agent
- Case resolved

The operations UI renders these records as the **Case Timeline**.

This creates a business-level audit trail separate from model traces.

---

# Observability

StayOps has several distinct observability layers.

### Agent execution

OpenAI Agents SDK tracing provides visibility into model execution and tool usage.

### Business audit

Persisted `case_events` record meaningful workflow changes.

### Operational UI

The Human Operations Dashboard exposes:

- Case ownership
- workflow state
- tasks
- escalations
- conversation
- financial evidence
- human decisions
- timeline

### Runtime infrastructure

The deployed backend sends runtime logs to CloudWatch.

These layers answer different questions and are intentionally not treated as interchangeable.

---

# Evaluation philosophy

StayOps does not treat:

```text
tool called
```

as equivalent to:

```text
operation succeeded
```

The evaluation system inspects actual tool results and database state.

```text
Agent scenario
      ↓
tool calls
tool outputs
database state
final response
      ↓
deterministic assertions
      +
LLM judge
      ↓
scenario result
```

---

# Testing

The repository contains regression coverage across the major deterministic workflows.

Coverage includes:

- access authorization
- Case creation and reuse
- Case lifecycle
- Case context
- Case API behavior
- Case resolution
- audit timeline
- task creation and idempotency
- task assignment
- task completion
- escalation handling
- human Case claiming
- human action authorization
- return-to-agent behavior
- compensation requests
- compensation evidence
- compensation assessment
- compensation decisions
- Refund Case resolution
- refund historical behavior
- refund workflow idempotency
- operational ↔ financial Case linking
- safe relationship backfilling
- ambiguous multi-Case protection
- demo reset
- technician retrieval
- message persistence

Run deterministic tests with:

```bash
uv run pytest
```

---

# Agent evaluation suite

Agent-level evaluations cover real multi-step behavior rather than isolated helper functions.

The suite checks areas including:

- deterministic scenario requirements
- tool usage
- tool outputs
- database mutations
- duplicate prevention
- multi-turn Case reuse
- human handoff
- financial authority
- financial approval
- financial denial
- historical refund handling
- guest-facing response quality

Run:

```bash
uv run python -m backend.evals.run_evals
```

The evaluation suite uses model calls and local MCP/Qdrant infrastructure, so it remains separate from the fast deterministic unit-test path.

---

# Failure-driven development

Several StayOps capabilities came directly from failures discovered during testing and manual end-to-end validation.

The development loop is:

```text
Run scenario
     ↓
Inspect trace
     ↓
Inspect tool results
     ↓
Inspect database state
     ↓
Find incorrect behavior
     ↓
Add regression test
     ↓
Fix deterministic logic
or agent instruction
     ↓
Run suite again
```

Examples include:

### Cross-category escalation reuse

An early deduplication rule could reuse an unrelated escalation.

The category was added to the deterministic reuse boundary and the failure became regression coverage.

### Tool call without database effect

Evaluation exposed situations where a tool could be invoked without producing the expected persisted state.

Tests were strengthened to inspect the database rather than treating invocation as success.

### Duplicate operational work

Repeated guest messages were tested against Case/task/escalation reuse logic.

### Refund workflow escape hatch

Generic escalation tooling could potentially bypass the canonical financial workflow.

Refund escalation creation is now owned by `ensure_refund_workflow`.

### Human authorization

Human dashboard actions were hardened so explicit human operations require the Case to be claimed by the acting operator.

### Operational ↔ refund Case linkage

An end-to-end heating + refund scenario exposed a compensation request that existed correctly but had no relationship to the heating Case.

The workflow now:

- passes `related_case_id` when the relationship is clear
- automatically links a single unambiguous operational Case
- safely backfills an existing unlinked request
- refuses to guess between multiple operational Cases

The failure remains covered by regression tests.

---

# Example end-to-end workflow

Consider:

> **Guest:** "The heating has been broken all evening. I want a full refund."

StayOps can interpret two related intents.

```text
Guest message
     │
     ├──────────────────────────────────┐
     │                                  │
     ▼                                  ▼
Heating problem                    Refund request
     │                                  │
     ▼                                  │
Heating Case                           │
     │                                  │
     ├── structured heating playbook    │
     ├── operational task               │
     ├── human escalation               │
     └── waiting_human                  │
     │                                  │
     └──────── related_case_id ─────────┘
                                        ↓
                                  Refund Case
                                        │
                              Compensation Request
                                        │
                              Financial escalation
                                        │
                                  waiting_human
```

The guest may later say:

> **Guest:** "The heating is working now, thanks."

Once deterministic resolution requirements are satisfied:

```text
Heating Case → resolved
```

The Refund Case remains independent:

```text
Refund Case → pending human financial review
```

The financial reviewer still sees:

```text
Related operational Case
Heating · resolved

Task
Restore heating · completed

Escalation
Heating · resolved
```

The operational history does not disappear simply because the operational Case was resolved.

---

# Multi-language demo

The synthetic demo data includes guests with different language preferences.

Examples include:

| Guest | Language |
|---|---|
| Emma Carter | English |
| Liliane Bavaud | French |
| Lukas Weber | German |

Preferred language is retrieved from guest data rather than selected through an artificial language toggle.

Operational state remains isolated by booking.

---

# Reproducible state

Generated runtime databases are not treated as source code.

```text
Tracked source data
        ↓
database bootstrap
        ↓
SQLite

Tracked knowledge
        ↓
RAG bootstrap
        ↓
Qdrant
```

### Build the database

```bash
uv run python -m backend.database.bootstrap --force
```

### Build the Qdrant knowledge store

```bash
uv run python -m backend.rag.bootstrap --force
```

Path overrides are supported through:

```text
STAYOPS_DB_PATH
STAYOPS_QDRANT_PATH
```

Demo booking dates are generated relative to bootstrap time so the sample stays do not become invalid simply because the repository gets older.

---

# Docker

The backend is packaged as a reproducible Docker image.

The image:

```text
installs locked dependencies
        ↓
copies tracked application/data/knowledge
        ↓
bootstraps SQLite
        ↓
bootstraps Qdrant
        ↓
starts FastAPI
```

Build:

```bash
docker build -t stayops .
```

Run:

```bash
docker run --rm -p 8000:8000 --env-file .env stayops
```

The backend exposes a health endpoint at:

```text
/health
```

---

# AWS deployment

```text
Browser
  ↓
CloudFront
  ├── Frontend
  │      ↓
  │     S3
  │
  └── Backend HTTPS
          ↓
         EC2
          ↓
        Docker
          ↓
       FastAPI
          ↓
Guest Operations Agent
   ├── Operations MCP
   │      ↓
   │   SQLite
   │
   └── Knowledge MCP
          ↓
        Qdrant
```

Infrastructure includes:

- **Amazon ECR** — versioned backend container images
- **Amazon EC2** — Dockerized FastAPI + agent runtime
- **Amazon S3** — statically exported Next.js frontend
- **Amazon CloudFront** — frontend delivery and backend HTTPS
- **AWS IAM** — scoped workload permissions
- **AWS Secrets Manager** — OpenAI API key
- **Amazon CloudWatch** — runtime logs
- **AWS Systems Manager** — instance administration
- **Terraform** — infrastructure as code

The runtime uses an IAM role rather than embedded developer credentials.

For V5 application releases, the existing EC2 instance is updated in place through AWS Systems Manager rather than being replaced only to change the Docker image. The SQLite database remains mounted from `/opt/stayops/database/stayops.db`, while Terraform continues to own the surrounding infrastructure and the image used for instance bootstrap.

---

# Tech stack

## Agent / AI

- OpenAI Agents SDK
- Model Context Protocol (MCP)
- Qdrant
- RAG
- sentence-transformers
- Pydantic structured outputs

## Backend

- Python 3.12+
- FastAPI
- SQLite
- deterministic service layer
- `uv`

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

## Evaluation

- pytest
- deterministic assertions
- SQLite side-effect validation
- agent scenario evaluations
- LLM-as-judge
- regression tests

## Infrastructure

- Docker
- GitHub Actions
- Terraform
- AWS ECR
- AWS EC2
- AWS S3
- AWS CloudFront
- AWS IAM
- AWS Secrets Manager
- AWS CloudWatch
- AWS Systems Manager

---

# Repository structure

```text
Stay_ops/
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── backend/
│   ├── agent/
│   │   ├── guest_agent.py
│   │   └── instructions.py
│   │
│   ├── api/
│   │
│   ├── database/
│   │   ├── bootstrap.py
│   │   └── demo_dates.py
│   │
│   ├── domain/
│   │   ├── enums.py
│   │   └── playbooks.py
│   │
│   ├── evals/
│   │   ├── judge.py
│   │   └── run_evals.py
│   │
│   ├── mcp/
│   │   └── server.py
│   │
│   ├── rag/
│   │   └── bootstrap.py
│   │
│   └── services/
│       ├── audit.py
│       ├── cases.py
│       ├── compensation.py
│       ├── escalations.py
│       ├── messages.py
│       ├── tasks.py
│       └── teams.py
│
├── frontend/
│   └── src/
│       └── app/
│           ├── page.tsx
│           └── operations/
│               ├── page.tsx
│               ├── constants.ts
│               ├── types.ts
│               ├── utils.ts
│               └── components/
│
├── data/
│
├── knowledge/
│   ├── stayops_sops/
│   └── str_ops/
│
├── tests/
│
├── terraform/
├── assets/
├── Dockerfile
├── pyproject.toml
└── uv.lock
```

---

# Running locally

## 1. Clone the repository

```bash
git clone https://github.com/penzen/stayops-ai.git
cd stayops-ai
```

## 2. Install Python dependencies

StayOps uses `uv`.

```bash
uv sync
```

## 3. Configure the backend environment

Create `.env`:

```env
OPENAI_API_KEY=your_key_here
```

Do not commit local credentials.

## 4. Bootstrap SQLite

```bash
uv run python -m backend.database.bootstrap --force
```

## 5. Bootstrap Qdrant knowledge

```bash
uv run python -m backend.rag.bootstrap --force
```

## 6. Start FastAPI

```bash
uv run uvicorn backend.api.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## 7. Install frontend dependencies

```bash
cd frontend
npm install
```

Configure:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

## 8. Start Next.js

```bash
npm run dev
```

Frontend:

```text
http://localhost:3000
```

Human Operations Dashboard:

```text
http://localhost:3000/operations
```

---

# Demo reset

The demo environment can be reset between scenarios so previous Cases and messages do not contaminate a new test.

Example:

```bash
curl -X POST http://127.0.0.1:8000/demo/reset/book_demo_current_001
```

Then run a fresh guest scenario through the UI or `/agent/chat`.

---

# Development verification

Backend:

```bash
uv run pytest
```

Agent evaluations:

```bash
uv run python -m backend.evals.run_evals
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

Before a release, all four should be clean.

---

# Continuous integration

GitHub Actions validates both backend and frontend behavior on pushes and pull requests to `main` and `v5`.

```text
Push / Pull Request
       ↓
GitHub Actions
       ├── Backend
       │     ↓
       │   Python 3.12
       │     ↓
       │   uv sync --frozen --dev
       │     ↓
       │   uv run pytest
       │
       └── Frontend
             ↓
           Node.js 22
             ↓
           npm ci
             ↓
           npm run lint
             ↓
           npm run build
```

The model-based agent evaluation suite remains separate from the mandatory CI path because it requires model credentials and external model calls.

---

# Current production-style boundaries

StayOps is a portfolio system demonstrating production-oriented agent architecture.

It is not presented as a finished large-scale hospitality platform.

| Current implementation | Production evolution |
|---|---|
| SQLite | PostgreSQL / RDS |
| Local Qdrant | Managed vector infrastructure |
| Single EC2 runtime | ECS/Fargate or another stateless container platform |
| Demo operator | Production authentication + RBAC |
| GitHub Actions test gate | Full CI/CD with staged environments |
| CloudWatch logs | Metrics, alerts, tracing correlation |
| Manual human workflow | Notification integrations and richer operator routing |
| Demo reset endpoint | Environment-restricted admin tooling |

Additional production hardening could include:

- authentication and authorization
- role-based access controls
- rate limiting
- request correlation IDs
- structured logging
- retries and timeout policies
- alerting
- cost/token monitoring
- operator feedback capture
- stronger secrets rotation
- PostgreSQL migrations
- managed vector infrastructure
- multi-instance concurrency controls
- notification integrations

---

# Design principles

> **Use AI for ambiguity. Use normal software for certainty.**

> **The agent gets tools, not unlimited power.**

> **Human handoff is part of the architecture, not an exception.**

> **Tool invocation does not equal successful execution. Verify the resulting state.**

> **SQL is operational truth. RAG is reusable expertise.**

> **Cases own operational work. Messages remain booking-level.**

> **The Case operator and field technician are different roles.**

> **Financial decisions belong to humans.**

> **Resolution requires evidence.**

> **Failures should become regression tests.**

---

# Why I built StayOps

I wanted to build something closer to an actual AI operations product than a chatbot demo.

The main engineering question was:

> **How can an LLM handle ambiguous real-world requests while remaining constrained by deterministic permissions, persistent operational state, evidence-based workflow rules, and human authority?**

StayOps explores that question across the full lifecycle:

```text
understand
   ↓
retrieve context
   ↓
choose bounded tools
   ↓
persist operational state
   ↓
coordinate human work
   ↓
verify effects
   ↓
retain evidence
   ↓
resolve only when justified
```

The goal is not maximum autonomy.

The goal is **useful autonomy with explicit boundaries**.