# StayOps Optimization Report

**Status:** Completed and validated  
**Target branch at completion:** `v4`  
**Recommended pin/tag:** `v4-optimized`  
**Final benchmark model:** `gpt-5.6-luna`  
**Final benchmark date:** 2026-10-07

---

## 1. Purpose

This document records the optimization work performed on StayOps after the V3.0.1 production release and before beginning the next development branch.

The goal of this work was not to redesign StayOps or change its agent architecture. The goal was to measure the existing system, identify the largest sources of latency and token/tool overhead, improve them without weakening correctness or operational safety, and leave behind reproducible benchmark instrumentation.

The optimization work focused on:

- measuring latency and model usage
- measuring prompt-cache behavior
- identifying redundant tool calls
- eliminating per-request MCP startup overhead
- preloading deterministic operational context
- preserving the deterministic safety boundary
- pinning the agent model for reproducibility
- estimating token cost per guest interaction

The optimization work deliberately did **not** expand V4 product scope.

---

## 2. Architecture Principle Preserved

The optimization work kept the central StayOps design unchanged:

> The LLM handles ambiguity, intent, tool choice, and communication. Deterministic services own permissions, state transitions, persistence, financial authority, idempotency, and resolution gates.

The agent still decides:

- what the guest means
- which operational category applies
- whether a message is a follow-up
- which operational action is needed
- how to communicate with the guest
- when a human handoff is required

Deterministic services still own:

- database writes
- Case creation and lifecycle
- task creation
- escalation creation
- Case workflow state transitions
- access authorization
- duplicate prevention
- compensation workflow
- financial decisions
- resolution gates
- evidence and persisted operational state

No optimization moved financial authority, permission checks, or state-transition authority into the LLM.

---

## 3. Original Performance Baseline

Before changing the runtime, a dedicated performance benchmark and LLM usage instrumentation were added.

The initial benchmark covered three representative scenarios:

1. `plumbing_worsening_leak`
2. `heating_failure`
3. `refund_request`

Each scenario was run three times.

### Original baseline

| Scenario | Pass | Avg latency | Avg LLM calls | Avg tool calls | Avg input tokens | Cache hit |
|---|---:|---:|---:|---:|---:|---:|
| Plumbing | 100% | 32.11s | 4.67 | 8.00 | 47,954 | 75.1% |
| Heating | 100% | 16.80s | 5.00 | 8.67 | 45,886 | 77.2% |
| Refund | 100% | 18.53s | 6.00 | 9.00 | 42,392 | 80.8% |

Approximate overall averages:

- **Latency:** 22.48s per interaction
- **LLM calls:** 5.22 per interaction
- **Tool calls:** 8.56 per interaction
- **Input tokens:** ~45.4k per interaction
- **Prompt-cache hit rate:** ~78%
- **Deterministic scenario pass rate:** 100%

This established the measurement baseline before optimization.

---

## 4. Instrumentation Added

### Files

- `backend/observability/llm_metrics.py`
- `backend/evals/run_performance_baseline.py`
- `tests/test_llm_metrics.py`

The benchmark records:

- total latency
- number of model requests
- number of tool calls
- input tokens
- cached input tokens
- cache-write input tokens
- output tokens
- reasoning tokens
- total tokens
- cache-hit rate
- tool-call breakdown
- estimated token cost
- pinned model name

The instrumentation was kept separate from the production control flow so measurement did not become part of business logic.

---

## 5. Prompt Caching Investigation

Prompt caching was investigated before attempting any cache-specific optimization.

The original system already showed approximately **75–81% cache hit rates** across the three benchmark scenarios.

This was an important finding.

It showed that prompt caching was already functioning reasonably well and was **not the primary latency bottleneck**.

Therefore the following were intentionally not prioritized:

- semantic response caching
- aggressive prompt-cache-specific restructuring
- application-level caching of live operational responses

### Why semantic response caching was skipped

StayOps responses depend on live operational state.

For example, the same guest message may need a different answer depending on:

- Case status
- task status
- escalation status
- human compensation decision
- reservation state
- newly persisted operational evidence

Caching complete responses risks returning stale operational information.

The preferred optimization strategy was therefore:

> reduce unnecessary work rather than cache state-dependent answers.

---

## 6. Optimization 1 — Persistent MCP Server Lifecycle

### Problem

Originally every call to `run_guest_agent()` created two new MCP subprocesses:

- StayOps Operations MCP
- StayOps Knowledge / Qdrant MCP

The knowledge MCP also needed to initialize its embedding environment.

That meant every guest chat interaction repeatedly paid MCP process startup costs.

### Change

MCP ownership was moved to the FastAPI application lifespan using `MCPServerManager`.

The production lifecycle became:

```text
FastAPI startup
    |
    +-- Operations MCP starts once
    |
    +-- Knowledge MCP starts once
    |
    +-- Guest request
    |      |
    |      +-- reuse active MCP servers
    |
    +-- Guest request
    |      |
    |      +-- reuse active MCP servers
    |
    +-- ...
    |
FastAPI shutdown
    |
    +-- MCP servers cleaned up
```

The full evaluation suite retained its isolated behavior where appropriate.

### Relevant files

- `backend/agent/guest_agent.py`
- `backend/api/main.py`
- `backend/evals/run_performance_baseline.py`

### Result

First persistent-MCP benchmark:

| Scenario | Before | Persistent MCP |
|---|---:|---:|
| Plumbing | 32.11s | 13.27s |
| Heating | 16.80s | 11.09s |
| Refund | 18.53s | 13.96s |

Average latency:

- **Before:** 22.48s
- **After persistent MCP:** ~12.77s
- **Improvement:** ~43%

Correctness remained unchanged.

This confirmed that per-request MCP startup was a major performance bottleneck.

---

## 7. Tool-Call Breakdown

After removing MCP startup overhead, the next question was whether the agent was spending unnecessary model/tool turns retrieving context Python already knew.

The benchmark was extended to record the exact tool-call distribution.

### Before deterministic context prefetch

Across nine benchmark runs:

| Tool | Average calls per run |
|---|---:|
| `lookup_guest` | 1.00 |
| `lookup_reservation` | 1.00 |
| `lookup_operational_playbook` | 1.00 |
| `ensure_operational_case` | 1.00 |
| `ensure_operations_task` | 1.00 |
| `update_case_workflow_status` | 1.00 |
| `ensure_human_escalation` | 1.11 |
| `lookup_open_cases_for_booking` | 0.44 |
| `ensure_refund_workflow` | 0.33 |
| `qdrant-find` | 0.33 |
| `lookup_open_incidents` | 0.22 |
| `lookup_property` | 0.22 |

The important observation was that several calls were deterministic reads that could be performed before the agent started:

- `lookup_guest`
- `lookup_reservation`
- `lookup_property`
- `lookup_open_cases_for_booking`

Open Cases, recent Case history, and recent conversation were already being partially preloaded.

---

## 8. Optimization 2 — Deterministic Context Prefetch

### Goal

Remove unnecessary LLM/tool round trips without reducing agent reasoning responsibility.

### Prefetched context

Before invoking the agent, Python now loads:

- guest
- reservation
- property
- open Cases
- recent Case history
- recent booking conversation

The request contains this as authoritative preloaded operational context.

The agent instructions explicitly tell the model not to re-fetch guest, reservation, property, or open Cases when the corresponding authoritative data is already supplied.

### What remains agent-driven

The following remain tool-driven:

- operational playbook retrieval
- Qdrant knowledge retrieval
- access authorization
- Case creation/reuse
- task creation/reuse
- escalation creation/reuse
- workflow-state updates
- refund workflow
- compensation workflow
- financial authority
- Case-context lookup when additional Case-owned state is required

This keeps the LLM responsible for interpretation and tool selection while Python handles obvious deterministic reads.

### Result

Benchmark immediately after context prefetch:

| Scenario | Latency | LLM calls | Tool calls | Input tokens |
|---|---:|---:|---:|---:|
| Plumbing | 10.95s | 3.67 | 5.67 | 25,950 |
| Heating | 11.33s | 4.33 | 5.00 | 30,298 |
| Refund | 11.80s | 4.33 | 6.00 | 31,431 |

Compared with the prior persistent-MCP/tool-breakdown run:

- average latency improved by roughly 12%
- model calls fell roughly 18%
- tool calls fell roughly 36%
- input tokens fell roughly 25%

The redundant lookup calls disappeared from the benchmark.

---

## 9. Optimization 3 — Explicit Model Pinning

The agent previously relied on the SDK model default.

That makes benchmark reproducibility weaker because a future SDK release could change the default model behavior.

The StayOps agent is now explicitly pinned to:

```text
gpt-5.6-luna
reasoning effort: none
verbosity: low
```

The purpose of this change is reproducibility rather than intentionally changing model behavior.

### Relevant file

- `backend/agent/guest_agent.py`

The benchmark now records the model name alongside the measurements.

---

## 10. Optimization 4 — Cost Instrumentation

The usage metrics were extended to estimate text-token cost per agent interaction.

The benchmark records:

- model name
- input tokens
- cached input tokens
- cache-write tokens
- output tokens
- estimated USD cost
- pricing date used by the benchmark

### Pricing assumptions encoded by the benchmark

As of 2026-10-07:

```text
Input:        $0.20 / 1M tokens
Cached input: $0.02 / 1M tokens
Cache write:  $0.25 / 1M tokens
Output:       $1.20 / 1M tokens
```

These figures are benchmark assumptions and should be refreshed if model pricing changes.

The estimate excludes:

- infrastructure
- EC2
- local MCP process overhead
- local Qdrant execution
- networking
- separate LLM-judge calls used by the full evaluation suite

---

## 11. Final Reproducible Benchmark

The final benchmark was run with **five runs per scenario** to reduce noise.

### Final results

| Scenario | N | Pass | Latency | LLM calls | Tool calls | Input tokens | Output tokens | Cache | Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Plumbing | 5 | 100% | 10.36s | 3.40 | 5.80 | 24,250 | 383 | 67.4% | $0.002760 |
| Heating | 5 | 100% | 10.58s | 4.40 | 5.00 | 30,834 | 349 | 75.3% | $0.002788 |
| Refund | 5 | 100% | 11.02s | 4.00 | 6.00 | 29,214 | 465 | 72.0% | $0.003026 |

Final averages:

- **Latency:** ~10.65s
- **LLM calls:** ~3.93
- **Tool calls:** ~5.60
- **Input tokens:** ~28.1k
- **Estimated token cost:** ~$0.00286 per guest interaction
- **Pass rate:** 100%

Final one-time MCP startup measured:

- **2.88s**

That startup value is excluded from per-chat latency because MCP servers remain alive for the process lifetime.

---

## 12. Original vs Final

| Metric | Original baseline | Final optimized | Change |
|---|---:|---:|---:|
| Average latency | 22.48s | 10.65s | **~52.6% lower** |
| Average LLM calls | 5.22 | 3.93 | **~24.7% fewer** |
| Average tool calls | 8.56 | 5.60 | **~34.6% fewer** |
| Average input tokens | ~45.4k | ~28.1k | **~38.1% fewer** |
| Deterministic quality | 100% | 100% | preserved |
| Token cost | not measured | ~$0.00286/chat | now measured |
| Model | implicit SDK default | `gpt-5.6-luna` | explicitly pinned |

The main outcome is therefore:

> StayOps cut average guest-interaction latency by roughly half while preserving the deterministic and agentic correctness gates.

---

## 13. Final Tool-Call Distribution

The final five-run-per-scenario benchmark produced the following overall tool distribution:

| Tool | Total calls | Average per run |
|---|---:|---:|
| `ensure_human_escalation` | 15 | 1.00 |
| `ensure_operational_case` | 15 | 1.00 |
| `ensure_operations_task` | 15 | 1.00 |
| `lookup_operational_playbook` | 15 | 1.00 |
| `update_case_workflow_status` | 15 | 1.00 |
| `ensure_refund_workflow` | 5 | 0.33 |
| `lookup_open_incidents` | 2 | 0.13 |
| `lookup_case_context` | 1 | 0.07 |
| `qdrant-find` | 1 | 0.07 |

The recurring calls that remain are mostly meaningful operational actions rather than redundant reads.

The following redundant lookups were successfully removed from the normal benchmark path:

```text
lookup_guest
lookup_reservation
lookup_property
lookup_open_cases_for_booking
```

---

## 14. Quality Gates After Optimization

The final state passed:

```text
100/100 pytest tests
```

The complete StayOps agent evaluation suite also passed:

```text
Deterministic scenarios: 3/3
LLM judge scenarios:     3/3
Overall scenarios:       3/3

Idempotency:             PASS
Multi-turn Case reuse:   PASS
Human handoff:           PASS
Financial authority:     PASS
Financial approval:      PASS
Financial denial:        PASS
Historical refund:       PASS

Overall suite:           PASS
```

The optimization work therefore did not trade correctness for speed.

---

## 15. Files Touched During Optimization

Primary product/runtime files:

```text
backend/agent/guest_agent.py
backend/agent/instructions.py
backend/api/main.py
```

Evaluation and observability:

```text
backend/evals/run_evals.py
backend/evals/run_performance_baseline.py
backend/observability/llm_metrics.py
```

Tests:

```text
tests/test_llm_metrics.py
tests/test_preloaded_context.py
```

Temporary migration/patch scripts were used during development but are not part of the product architecture and should not be committed.

Backup files such as:

```text
*.pre-mcp-lifespan
*.pre-prefetch
*.pre-prefetch-v2
*.pre-model-cost
```

should also remain untracked.

---

## 16. Benchmark Commands

### Unit/regression suite

```powershell
uv run pytest
```

Expected current result:

```text
100 passed
```

### Full agent evaluation suite

```powershell
uv run python -m backend.evals.run_evals
```

Expected:

```text
Overall suite: PASS
```

### Final performance benchmark

```powershell
uv run python -m backend.evals.run_performance_baseline --runs 5 --output artifacts/final_optimized.json
```

The JSON artifact contains the machine-readable benchmark output.

---

## 17. Interview / Portfolio Explanation

A concise explanation:

> I first instrumented StayOps rather than optimizing blindly. The baseline averaged about 22.5 seconds per guest interaction, with roughly 5.2 model calls, 8.6 tool calls, and 45k input tokens. Prompt caching was already working at around 78%, so caching was not the main bottleneck. I found that both MCP servers were being spawned for every request, so I moved them to the FastAPI application lifespan. I then measured tool usage and found the agent was repeatedly looking up deterministic guest, reservation, property, and Case information that Python already had. I prefetched that context and kept only meaningful operational actions tool-driven. Finally, I pinned the model and added cost instrumentation. The final benchmark averaged about 10.7 seconds, 3.9 model calls, 5.6 tool calls, and 28k input tokens, at roughly $0.0029 in text-token cost per interaction. The complete regression and agent evaluation suites still passed.

This demonstrates:

- measurement before optimization
- agent-harness engineering
- deterministic/LLM boundary design
- MCP lifecycle management
- context engineering
- token efficiency
- latency optimization
- evaluation-driven development
- reproducibility
- cost awareness

---

## 18. Deliberately Deferred Work

The following were identified but intentionally not added during this optimization phase:

### Streaming

`Runner.run_streamed` could improve perceived latency but would not significantly reduce total computation time.

### Model routing

Simple messages could potentially use a smaller/faster model and refund or ambiguous workflows could use a stronger model.

This should only be introduced with dedicated routing evaluations.

### Further tool-schema reduction

StayOps exposes many MCP tools. Tool descriptions could be reduced or progressively disclosed, but the current remaining tool-call pattern is already meaningful and correctness takes priority.

### MCP cold-start investigation

One benchmark observed a much larger MCP cold start than normal.

The final measured startup was 2.88s, but cold-start variance may deserve a separate future investigation if deployment startup latency becomes important.

### Structured production observability

Future work could add:

- error categories
- per-tool latency
- execution IDs
- state-transition metrics
- tool failure metrics
- operator outcome correlation

### Response caching

Not recommended for live operational responses because they depend on mutable state.

---

## 19. Completion State

The optimization phase is considered complete.

Final status:

```text
[x] baseline instrumentation
[x] prompt-cache visibility
[x] MCP lifecycle optimization
[x] tool-call instrumentation
[x] deterministic context prefetch
[x] redundant lookup removal
[x] explicit model pinning
[x] cost estimation
[x] 100/100 tests
[x] complete evaluation suite PASS
[x] final five-run benchmark
```

The next branch can now build on a measured and pinned agent runtime without reopening optimization work unless new evidence shows a regression.

---

## 20. Recommended Git Pin

After committing this document and the final optimization files:

```powershell
git add STAYOPS_OPTIMIZATION_REPORT.md
git commit -m "Document StayOps optimization results"
git push origin v4
```

Pin this exact state with an annotated tag:

```powershell
git tag -a v4-optimized -m "StayOps optimized agent runtime"
git push origin v4-optimized
```

Then create the next branch from the pinned state:

```powershell
git checkout -b v5
git push -u origin v5
```

This makes `v4-optimized` an immutable reference point for the completed optimization work while `v5` can evolve independently.
