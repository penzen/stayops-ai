# StayOps AI — Architecture

```mermaid
flowchart TB
    User["Operator / Demo User"]

    subgraph Frontend["Frontend Delivery"]
        CF_UI["CloudFront"]
        S3["Private S3 Bucket<br/>Static Next.js Export"]
        CF_UI --> S3
    end

    subgraph BackendEdge["Backend Edge"]
        CF_API["CloudFront<br/>HTTPS API Endpoint"]
    end

    subgraph Compute["AWS Compute"]
        EC2["EC2<br/>Amazon Linux"]
        Docker["Docker Container"]
        API["FastAPI"]

        EC2 --> Docker
        Docker --> API
    end

    subgraph AgentLayer["Agent Layer"]
        Agent["Guest Operations Agent<br/>OpenAI Agents SDK"]
        OpsMCP["Operations MCP"]
        KnowledgeMCP["Knowledge MCP"]

        Agent --> OpsMCP
        Agent --> KnowledgeMCP
    end

    subgraph Deterministic["Deterministic Operations"]
        Services["Python Service Layer"]
        SQLite[("SQLite<br/>Guests / Bookings / Tasks /<br/>Escalations / Messages / Incidents")]

        OpsMCP --> Services
        Services --> SQLite
    end

    subgraph Retrieval["Operational Knowledge"]
        Qdrant[("Qdrant")]
        SOP["StayOps Internal SOPs"]
        STR["STR Operations Knowledge"]

        KnowledgeMCP --> Qdrant
        SOP --> Qdrant
        STR --> Qdrant
    end

    subgraph AWSPlatform["AWS Supporting Services"]
        ECR["ECR<br/>Versioned Docker Images"]
        Secrets["Secrets Manager<br/>OpenAI API Key"]
        IAM["IAM Role<br/>Scoped Workload Permissions"]
        CW["CloudWatch<br/>Runtime Logs"]
        SSM["Systems Manager<br/>Instance Administration"]
        TF["Terraform<br/>Infrastructure as Code"]
    end

    User --> CF_UI
    CF_UI --> CF_API
    CF_API --> API
    API --> Agent

    ECR -. image pull .-> EC2
    Secrets -. runtime secret .-> EC2
    IAM -. permissions .-> EC2
    EC2 -. logs .-> CW
    SSM -. administration .-> EC2
    TF -. provisions .-> CF_UI
    TF -. provisions .-> CF_API
    TF -. provisions .-> EC2
    TF -. provisions .-> IAM
    TF -. provisions .-> Secrets
    TF -. provisions .-> CW
```

## Request flow

```text
Guest message
    ↓
CloudFront frontend
    ↓
CloudFront backend HTTPS
    ↓
FastAPI
    ↓
Guest Operations Agent
    ├── structured operational context via Operations MCP
    ├── reusable expertise via Knowledge MCP + Qdrant
    ↓
bounded tool action
    ↓
deterministic service layer
    ↓
SQLite state change
    ↓
agent verifies / responds
    ↓
UI updates tasks, escalations and agent activity
```

## Key architectural boundaries

- **LLM for ambiguity:** interpretation, reasoning, context selection, tool choice.
- **Deterministic code for certainty:** permissions, validation, state mutation, idempotency, database operations.
- **SQL for current truth:** live booking and operational state.
- **RAG for reusable expertise:** SOPs and short-term-rental operational knowledge.
- **MCP as the capability boundary:** the model gets explicit tools rather than direct database access.
- **Human handoff as a valid outcome:** the agent escalates when an action is unsafe or unauthorized.
