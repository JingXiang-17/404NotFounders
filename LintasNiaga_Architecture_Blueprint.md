# LintasNiaga Architecture Blueprint

## System Architecture for Hackathon v1

**Project:** LintasNiaga  
**Document Type:** Architecture blueprint  
**Version:** 1.0  
**Scope:** Architecture only, aligned to the finalized PRD and tech stack  
**Primary Goal:** Build a stable, explainable, judge-ready AI decision system without overengineering

---

## 1. Architecture Intent

LintasNiaga is not a generic chatbot and not a spreadsheet dashboard with an LLM pasted on top.

It is a **backend-owned procurement decision pipeline** that:

1. ingests supplier quote PDFs,
2. extracts structured quote data,
3. validates scope and required fields,
4. computes deterministic landed-cost and risk outputs,
5. runs bounded AI reasoning on top of those outputs,
6. returns a final recommendation object:
   - recommended supplier,
   - lock now / wait,
   - hedge percentage,
   - top reasons,
   - optional caveat,
   - backup option.

The architecture is designed to optimize for:

- demo stability,
- clear ownership of truth,
- explainable failure handling,
- bounded AI behavior,
- and fast implementation in hackathon conditions.

---

## 2. High-Level Architecture Principles

These principles are treated as non-negotiable.

1. **FastAPI is the system backbone.**
2. **The backend owns the workflow, not the browser.**
3. **The workflow is sequential by default.**
4. **Quote prep and analysis are logically separate stages.**
5. **Validation gates analysis.**
6. **Deterministic math runs before AI reasoning.**
7. **LangGraph is thin and bounded.**
8. **Streaming is selective, not systemic.**
9. **Fallback logic is centralized.**
10. **Frontend never becomes the source of truth.**

---

## 3. System Context

### 3.1 Core Topology

- **Frontend:** Next.js app
- **Backend:** FastAPI app
- **AI orchestration:** thin LangGraph layer inside backend
- **Local persistence:** SQLite + JSON + local disk
- **Hosted persistence later:** Supabase Postgres + Supabase Storage
- **External services:**
  - Z.AI
  - BNM OpenAPI
  - Langfuse

### 3.2 Context Diagram

```text
[User]
   |
   v
[Next.js Web App]
   |
   | REST / SSE
   v
[FastAPI Application]
   |
   |-- [Quote Prep Services]
   |-- [Deterministic Analysis Services]
   |-- [Thin LangGraph AI Layer]
   |-- [Persistence Layer]
   |
   |---> [Z.AI Vision / GLM]
   |---> [BNM OpenAPI]
   |---> [Langfuse]
   |
   |---> [SQLite]
   |---> [Static JSON Repository]
   |---> [Local Disk / Supabase Storage]
```

---

## 4. Option Review and Final Architecture Decisions

This section captures the main architectural options and the chosen default.

### 4.1 Overall Execution Model

**Options**
- A. One backend-owned orchestrator workflow per analysis run
- B. Browser chains multiple backend calls step by step
- C. Event-driven / queued pipeline from day one

**Chosen:** A

**Reasoning**
- Keeps workflow control in one place.
- Keeps failures, retries, traces, and recommendation assembly centralized.
- Prevents the browser from becoming an accidental workflow engine.

---

### 4.2 Top-Level Pipeline Shape

**Options**
- A. Strict sequential stages
- B. Partially parallel by default
- C. Dynamic agent chooses order

**Chosen:** A

**Reasoning**
- The workflow is naturally stage-based.
- Easier to trace, test, and explain.
- Parallelism can be introduced later inside isolated stages if needed.

---

### 4.3 Macro Workflow Split

**Options**
- A. Two backend workflows: Quote Prep and Analysis
- B. One giant workflow paused mid-flight for repair
- C. Frontend handles prep, backend handles analysis only

**Chosen:** A

**Reasoning**
- Quote extraction/repair and procurement analysis have different lifecycle rules.
- Avoids awkward long-running workflows waiting for user edits.
- Makes persistence, retry, and UX clearer.

---

### 4.4 Quote Extraction Placement

**Options**
- A. Dedicated first-class backend stage
- B. Mixed into analysis later
- C. Mostly on frontend

**Chosen:** A

**Reasoning**
- Keeps PDF understanding separate from recommendation logic.
- Preserves a clean boundary: raw file -> structured quote -> validated quote.

---

### 4.5 Validation Gate

**Options**
- A. Hard validation gate before analysis
- B. Partial analysis first, validate later
- C. Validate only at the end

**Chosen:** A

**Reasoning**
- Prevents the engine from calculating on malformed or unsupported quote data.
- Enables the repair flow and partial-exclusion flow cleanly.

---

### 4.6 Deterministic Engine Placement

**Options**
- A. Deterministic services outside LangGraph
- B. Put all math and rules inside LangGraph nodes
- C. Split some rules into frontend

**Chosen:** A

**Reasoning**
- Makes the rules and math auditable.
- Keeps unit testing simple.
- Prevents the AI layer from becoming the owner of truth.

---

### 4.7 AI Reasoning Placement

**Options**
- A. AI runs after deterministic outputs are available
- B. AI reasons first, then math follows
- C. AI and math are interleaved throughout

**Chosen:** A

**Reasoning**
- AI should reason over trusted structured state.
- Deterministic outputs become grounding context for recommendation and explanation.

---

### 4.8 Data Loading and Fallback Strategy

**Options**
- A. Centralized data stage loads BNM + static JSON + fallback logic before compute
- B. Each service fetches its own data ad hoc
- C. Frontend provides some context

**Chosen:** A

**Reasoning**
- Makes failover deterministic.
- Prevents inconsistent FX behavior.
- Keeps the hybrid live/static model explicit.

---

### 4.9 Persistence Checkpoints

**Options**
- A. Persist key checkpoints only
- B. Persist only final result
- C. Persist every tiny internal state mutation

**Chosen:** A

**Reasoning**
- Gives enough observability and recovery without building an event-sourcing system.

**Checkpoint set**
1. upload created
2. extraction completed
3. validation result saved
4. analysis run started
5. final recommendation saved

---

### 4.10 Long-Running Analysis Interaction Model

**Options**
- A. POST creates run; frontend subscribes to status/result stream
- B. One blocking request waits for everything
- C. Queue/worker architecture from day one

**Chosen:** A

**Reasoning**
- Allows progress UX without introducing a real worker stack.
- Keeps API ownership on the backend.

---

### 4.11 Streaming Scope

**Options**
- A. No streaming
- B. Stream only analyst/status output
- C. Make the whole system realtime-first

**Chosen:** B

**Reasoning**
- Only the AI Analyst panel really benefits from progressive output.
- The rest of the product remains request/response.

---

### 4.12 Internal Service Decomposition

**Options**
- A. Separate backend services by responsibility
- B. One giant analysis service
- C. Microservices from day one

**Chosen:** A

**Reasoning**
- Gives modularity without operational overhead.
- Keeps service ownership clear.

---

### 4.13 Recommendation Assembly Authority

**Options**
- A. One backend recommendation assembler merges numeric engine + bounded GLM output
- B. GLM decides final recommendation directly
- C. Frontend merges ranking and AI explanation

**Chosen:** A

**Reasoning**
- Preserves the numeric engine as primary authority.
- Enforces bounded GLM behavior.
- Produces one canonical response object.

---

### 4.14 Error Model

**Options**
- A. Stage-specific typed failures
- B. Generic 500s only
- C. Silent degradation with little explanation

**Chosen:** A

**Reasoning**
- This product needs explainable failure, not only explainable success.
- Supports better repair UX and easier debugging.

---

### 4.15 Queue / Background Job Posture

**Options**
- A. No real queue initially; only lightweight background tasks if needed
- B. Celery/Redis from the start
- C. Full event bus / worker fleet

**Chosen:** A

**Reasoning**
- Keeps hackathon complexity low.
- A proper worker stack is only justified if analysis times become a real bottleneck.

---

### 4.16 Hosted Runtime Topology

**Options**
- A. Web and API are separate; web talks only to API; API talks to storage/providers
- B. Web sometimes talks directly to Supabase/providers
- C. All-in-one deploy with blurred boundaries

**Chosen:** A

**Reasoning**
- Preserves the backend as the only business logic authority.
- Prevents direct frontend bypasses around validation, logging, or fallback rules.

---

## 5. Architecture Layers

### 5.1 Layer 1 — UI Layer (Next.js)

**Responsibilities**
- file upload UI
- quote repair form UI
- comparison workspace UI
- recommendation card UI
- backup option UI
- analyst panel UI
- FX fan chart UI
- hedge slider UI
- loading/error states

**Not responsible for**
- business truth
- ranking logic
- simulation logic
- fallback logic
- recommendation assembly

---

### 5.2 Layer 2 — API/Application Layer (FastAPI)

**Responsibilities**
- receive requests
- create quote-prep runs and analysis runs
- coordinate workflow stages
- expose REST endpoints
- expose SSE streaming endpoint where needed
- coordinate persistence and final response delivery

**Rule**
Route handlers stay thin.

---

### 5.3 Layer 3 — Domain / Service Layer

This is the real logic center.

**Services**
- `quote_ingest_service`
- `quote_validation_service`
- `reference_data_service`
- `fx_service`
- `cost_engine_service`
- `recommendation_engine_service`
- `analysis_run_service`
- `ai_orchestrator_service`
- `recommendation_assembler_service`

---

### 5.4 Layer 4 — Infrastructure / Provider Layer

**Responsibilities**
- local disk / storage access
- SQLite access
- JSON repository access
- Z.AI provider wrapper
- BNM client wrapper
- Langfuse trace wrapper
- structured logging

---

## 6. Core Workflows

## 6.1 Workflow A — Quote Prep

### Purpose
Turn uploaded PDFs into validated structured quotes.

### Stages
1. Create quote-prep run
2. Save uploaded PDF to local disk (or storage later)
3. Call Z.AI Vision extraction
4. Normalize output into internal quote schema
5. Validate against required fields and scope
6. Persist validation result
7. Return:
   - valid quote
   - invalid quote with reasons
   - fixable fields

### Output states
- `valid`
- `invalid_fixable`
- `invalid_out_of_scope`

### Notes
This workflow may run for each file independently.

---

## 6.2 Workflow B — Analysis

### Purpose
Compare valid quotes and produce one canonical recommendation object.

### Preconditions
- required quantity present
- urgency present
- at least one quote valid

### Stages
1. Create analysis run
2. Load valid quotes
3. Enforce comparison assumptions
4. Load reference data
5. Fetch BNM rates/history with timeout rule
6. Fail over to fallback rates if necessary
7. Run deterministic cost engine
8. Run ranking engine
9. Build AI context package
10. Run thin LangGraph reasoning flow
11. Merge deterministic and AI outputs
12. Persist final result
13. Return result / stream analyst output

---

## 6.3 Workflow C — Single-Quote Fallback

### Trigger
Exactly one valid quote remains after validation.

### Behavior
Switch from comparison mode to single-quote evaluation mode.

### Outputs
- Proceed
- Review carefully
- Do not recommend

### Important rule
The system must not pretend a multi-quote comparison happened.

---

## 7. Stage-by-Stage Analysis Pipeline

### Stage 1 — Request Intake

**Input**
- quote IDs or uploaded files
- required quantity
- urgency
- optional hedge preference

**Responsibility**
- basic request validation
- create run record

---

### Stage 2 — Validation Gate

**Responsibility**
- ensure at least required quote structure exists
- reject unsupported product / corridor / incoterm
- classify quotes into valid vs invalid buckets

**Output**
- valid quotes list
- invalid quotes list with reasons

---

### Stage 3 — Data Preparation

**Responsibility**
- load freight data
- load tariff data
- load commodity baseline
- load macro calendar
- load supplier seed data
- fetch BNM rates/history
- invoke fallback rates if needed

---

### Stage 4 — Deterministic Engine

**Responsibility**
- hard costs
- MOQ penalty
- supplier trust penalty
- probabilistic FX outputs
- ranking base score

**Outputs**
- p10 / p50 / p90
- normalized per-ton cost
- total landed cost for buyer-required quantity
- base ranking

---

### Stage 5 — AI Reasoning Layer

**Responsibility**
- interpret macro and timing context
- generate analyst explanation
- support bounded recommendation adjustment
- produce plain-language reasons and caveat

**Rule**
The AI layer may not invent unsupported data and may only adjust within backend guardrails.

---

### Stage 6 — Recommendation Assembly

**Responsibility**
Produce one canonical response object.

**Canonical recommendation object**
- mode: comparison or single-quote
- recommended supplier or quote status
- lock now / wait
- hedge percentage
- top 3 reasons
- optional caveat
- backup option if comparison mode
- why-not-the-others summaries
- impact summary

---

### Stage 7 — Persistence + Delivery

**Responsibility**
- persist final run result
- stream analyst text if enabled
- return final payload to frontend

---

## 8. LangGraph Placement

## 8.1 What LangGraph Should Own

Use LangGraph only for AI-specific workflow steps:

- extraction orchestration wrapper if needed
- context assembly for reasoning
- reasoning call sequencing
- bounded recommendation-adjustment step
- streamed analyst output coordination

## 8.2 What LangGraph Must Not Own

Do not let LangGraph become the owner of:

- validation rules
- cost engine logic
- fallback logic
- ranking truth
- persistence truth
- storage truth

## 8.3 Why

The system must remain understandable even if the AI layer fails or is bypassed.

---

## 9. Data Architecture Inside the System

## 9.1 Static Reference Data

Lives in JSON and is loaded through a centralized repository layer.

**Files**
- `freight_rates.json`
- `tariffs_my_hs.json`
- `commodity_baselines.json`
- `macro_calendar.json`
- `suppliers_seed.json`
- `fallback_rates.json`

## 9.2 Dynamic Runtime Data

Lives in SQLite for hackathon mode.

**Entities**
- upload record
- quote record
- extraction result
- validation result
- analysis run
- recommendation result

## 9.3 Hosted Later

- Supabase Postgres for structured data
- Supabase Storage for PDFs

---

## 10. Suggested Internal Data Models

These are conceptual architecture entities, not exact code.

### 10.1 QuoteUpload
- upload_id
- filename
- storage_path
- uploaded_at
- status

### 10.2 ExtractedQuote
- quote_id
- upload_id
- supplier_name
- origin_port_or_country
- incoterm
- unit_price
- currency
- moq
- lead_time_days
- extraction_confidence_optional

### 10.3 QuoteValidationResult
- quote_id
- status
- reason_codes
- missing_fields
- user_corrected_fields

### 10.4 AnalysisRun
- run_id
- valid_quote_ids
- quantity
- urgency
- hedge_preference
- run_status
- started_at
- completed_at

### 10.5 RecommendationResult
- run_id
- mode
- winner_quote_id_optional
- backup_quote_id_optional
- timing_recommendation
- hedge_percent
- reasons
- caveat_optional
- p10
- p50
- p90
- impact_summary

---

## 11. Error and Fallback Architecture

## 11.1 Typed Failure Categories

Recommended architecture-level error types:

- `ExtractionFailed`
- `ValidationFailed`
- `UnsupportedScope`
- `BNMTimeoutUsingFallback`
- `NoValidQuotes`
- `SingleValidQuoteFallback`
- `ComputationFailed`
- `AIReasoningFailedFallbackToDeterministic`

## 11.2 Failure Strategy

- Fail early at the validation boundary.
- Continue with valid quotes when partial failure is acceptable.
- Surface human-readable repair actions.
- Never fabricate missing critical data.
- If BNM fails, switch to fallback without crashing.

---

## 12. API Surface Recommendation

The exact endpoint names may vary, but the shape should stay like this.

### Quote Prep
- `POST /quote-uploads`
- `GET /quote-uploads/{upload_id}`
- `POST /quotes/{quote_id}/repair`

### Analysis
- `POST /analysis-runs`
- `GET /analysis-runs/{run_id}`
- `GET /analysis-runs/{run_id}/stream`
- `POST /analysis-runs/{run_id}/hedge-scenarios`

### Health / Infra
- `GET /health`
- `GET /ready`

### API Style Rule
- REST by default
- SSE only for analyst/status streaming

---

## 13. Frontend-Backend Interaction Model

## 13.1 Quote Prep UX

1. User uploads PDFs
2. Frontend sends files to FastAPI
3. FastAPI stores files and runs extraction
4. Frontend receives quote prep results
5. User fixes invalid/incomplete quotes if needed

## 13.2 Analysis UX

1. User enters required quantity and urgency
2. Frontend sends one analysis request
3. Backend owns the full pipeline
4. Frontend subscribes to run status / analyst stream
5. Frontend renders final recommendation object

---

## 14. Observability and Tracing Architecture

## 14.1 Langfuse

Use for:
- AI traces
- model calls
- tool/use-step traces
- reasoning workflow observability

## 14.2 Structured App Logs

Use for:
- upload lifecycle
- extraction errors
- validation failures
- BNM timeouts and fallback events
- JSON load issues
- run lifecycle logs
- internal exceptions

## 14.3 Why This Split

AI traces and app/system logs serve different purposes and should remain separate.

---

## 15. Security and Boundary Rules

Even for hackathon v1, keep these architecture boundaries clear.

1. Frontend must not bypass FastAPI for core business actions.
2. Business rules are never enforced only in the frontend.
3. AI provider access is wrapped behind one backend provider layer.
4. BNM access is wrapped behind one FX service/client.
5. Static data is only accessed through the data repository layer.

---

## 16. Recommended Folder-to-Architecture Mapping

### Web

```text
apps/web/
  app/
  components/
  features/
    quote-upload/
    quote-repair/
    comparison/
    recommendation/
    analyst-panel/
    hedge/
  lib/
    api/
    schemas/
    query/
```

### API

```text
apps/api/
  api/
    routes/
  services/
    quote_ingest_service.py
    quote_validation_service.py
    reference_data_service.py
    fx_service.py
    cost_engine_service.py
    recommendation_engine_service.py
    analysis_run_service.py
    recommendation_assembler_service.py
  ai/
    provider/
    graphs/
    prompts/
    context_builders/
  data/
    repositories/
    clients/
  schemas/
  core/
```

---

## 17. Three Review Points Worth Checking Before Build

These do not block the architecture, but they are the best places for final review.

### 17.1 Analyst Streaming Necessity
Should the demo truly show progressive analyst streaming, or would stage progress + final explanation be enough?

### 17.2 User Workflow Boundary
Should quote prep and analysis be two explicit user actions, or one seamless UX with two backend workflows hidden underneath?

### 17.3 Partial Run Persistence
Do you want minimal checkpoint persistence only, or richer persistence for draft/abandoned quote-prep sessions?

---

## 18. Final Recommended Architecture Summary

LintasNiaga v1 should be implemented as a **backend-owned sequential procurement decision pipeline** with two core workflows:

1. **Quote Prep**
   - upload
   - extract
   - normalize
   - validate
   - repair

2. **Analysis**
   - load valid quotes
   - load hybrid data
   - compute deterministic cost/risk outputs
   - run bounded AI reasoning
   - assemble canonical recommendation
   - persist and return results

The final system should have:
- a thin frontend,
- a strong FastAPI backbone,
- a thin LangGraph AI layer,
- centralized fallback logic,
- and strict architecture boundaries that keep math, rules, and AI cleanly separated.

That is the architecture most likely to be:
- buildable,
- explainable,
- debuggable,
- and persuasive to judges.
