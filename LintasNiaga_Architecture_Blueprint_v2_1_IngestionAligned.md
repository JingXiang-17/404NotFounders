# LintasNiaga Architecture Blueprint

## System Architecture for Hackathon v1 (Ingestion-Aligned Rewrite)

**Project:** LintasNiaga  
**Document Type:** Architecture blueprint  
**Version:** 2.1  
**Scope:** Architecture only, aligned to the latest PRD, locked ingestion contracts, and 48-hour backend plan  
**Primary Goal:** Build a stable, explainable, judge-ready AI decision system without overengineering

---

## 1. Architecture Intent

LintasNiaga is not a generic chatbot and not a spreadsheet dashboard with an LLM pasted on top.

It is a **backend-owned procurement decision system** with **two major runtime responsibilities** and **one support subsystem**:

1. **Quote Prep**  
   - ingest supplier quote PDFs,  
   - extract structured quote data,  
   - validate scope and required fields.

2. **Analysis**  
   - load validated quotes,  
   - load deterministic anchors and latest approved market/logistics snapshots,  
   - compute landed-cost and risk outputs,  
   - run bounded AI reasoning on top of those outputs,  
   - return a canonical recommendation object.

3. **Snapshot Ingestion Backbone**  
   - fetch external data from selected sources,  
   - normalize and validate it,  
   - persist raw artifacts and cleaned snapshots,  
   - feed analysis without introducing runtime scraping fragility.

The architecture is designed to optimize for:

- demo stability,
- clear ownership of truth,
- explainable failure handling,
- bounded AI behavior,
- modular data ingestion,
- and fast implementation in hackathon conditions.

---

## 2. High-Level Architecture Principles

These principles are treated as non-negotiable.

1. **FastAPI is the system backbone.**
2. **The backend owns the workflow, not the browser.**
3. **The workflow is sequential by default.**
4. **Quote prep and analysis are logically separate stages.**
5. **Ingestion refresh and quote analysis are logically separate concerns.**
6. **Validation gates analysis.**
7. **Deterministic math runs before AI reasoning.**
8. **LangGraph remains thin and bounded.**
9. **Provider adapters isolate third-party dependencies.**
10. **Snapshots are consumed at analysis time; raw scraping is not.**
11. **Fallback logic is centralized.**
12. **Frontend never becomes the source of truth.**

---

## 3. System Context

### 3.1 Core Topology

- **Frontend:** Next.js app
- **Backend:** FastAPI app
- **AI orchestration:** thin LangGraph layer inside backend
- **Local persistence:** SQLite + JSON + local disk
- **Hosted persistence later:** Supabase Postgres + Supabase Storage
- **External ingestion-facing services:**
  - FX and energy source adapter (`yfinance` in hackathon mode)
  - OpenWeatherMap
  - OpenDOSM / data.gov.my
  - GNews
  - curated web pages for PP resin benchmark extraction
- **AI / runtime services:**
  - extraction + reasoning model provider
  - observability provider

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
   |-- [Snapshot Ingestion Services]
   |-- [Deterministic Analysis Services]
   |-- [Thin LangGraph AI Layer]
   |-- [Persistence Layer]
   |
   |---> [LLM Provider / Vision / Reasoning]
   |---> [yfinance Adapter]
   |---> [OpenWeatherMap]
   |---> [OpenDOSM / data.gov.my]
   |---> [GNews]
   |---> [Curated Web Pages -> Trafilatura]
   |---> [Langfuse]
   |
   |---> [SQLite]
   |---> [Local JSON Reference Repository]
   |---> [Snapshot Store]
   |---> [Raw Artifact Store]
   |---> [Local Disk / Supabase Storage]
```

### 3.3 Architecture Delta vs Previous Blueprint

The earlier blueprint assumed:

- static JSON reference data,
- BNM-centered live FX,
- no first-class ingestion subsystem,
- and analysis-centric data loading only. fileciteturn25file0

The updated architecture keeps the same **backend-owned, deterministic-first** philosophy, but adds:

- a dedicated **snapshot ingestion subsystem**,
- provider adapters for external sources,
- raw artifact persistence for debugging,
- normalized snapshots as the only analysis-facing external-data input,
- and updated source boundaries aligned with the new PRD and build plan.

---

## 4. Option Review and Final Architecture Decisions

This section captures the main architectural options and the chosen default.

### 4.1 Overall Execution Model

**Options**
- A. One backend-owned orchestrator workflow per analysis run plus a separate backend-owned ingestion refresh flow
- B. Browser chains multiple backend calls step by step
- C. Event-driven / queued pipeline from day one

**Chosen:** A

**Reasoning**
- Keeps workflow control in one place.
- Keeps failures, retries, traces, and recommendation assembly centralized.
- Prevents the browser from becoming an accidental workflow engine.
- Adds ingestion without forcing a queue/worker stack on day one.

---

### 4.2 Top-Level Pipeline Shape

**Options**
- A. Strict sequential stages
- B. Partially parallel by default
- C. Dynamic agent chooses order

**Chosen:** A

**Reasoning**
- The major workflows are naturally stage-based.
- Easier to trace, test, and explain.
- Parallelism can be introduced later inside isolated ingestion steps if needed.

---

### 4.3 Macro Workflow Split

**Options**
- A. Three backend workflows: Quote Prep, Snapshot Ingestion, Analysis
- B. One giant workflow covering everything
- C. Frontend handles prep and some data loading

**Chosen:** A

**Reasoning**
- Quote extraction/repair, external data refresh, and procurement analysis have different lifecycle rules.
- Avoids scraping or source-refresh logic contaminating quote comparison requests.
- Makes persistence, retry, caching, and UX clearer.

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

### 4.5 Snapshot Ingestion Placement

**Options**
- A. Dedicated backend ingestion subsystem producing normalized snapshots
- B. Fetch external data ad hoc inside each analysis request
- C. Frontend fetches some source data itself

**Chosen:** A

**Reasoning**
- Protects demo stability.
- Makes snapshot freshness explicit.
- Supports source-specific retry and validation.
- Prevents raw scraping and external HTTP variability from entering the analysis request path.

---

### 4.6 Validation Gate

**Options**
- A. Hard validation gate before analysis
- B. Partial analysis first, validate later
- C. Validate only at the end

**Chosen:** A

**Reasoning**
- Prevents the engine from calculating on malformed or unsupported quote data.
- Enables the repair flow and partial-exclusion flow cleanly.

---

### 4.7 Deterministic Engine Placement

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

### 4.8 AI Reasoning Placement

**Options**
- A. AI runs after deterministic outputs are available
- B. AI reasons first, then math follows
- C. AI and math are interleaved throughout

**Chosen:** A

**Reasoning**
- AI should reason over trusted structured state.
- Deterministic outputs become grounding context for recommendation and explanation.

---

### 4.9 Data Loading and Fallback Strategy

**Options**
- A. Centralized data stage loads anchors + latest snapshots + fallback logic before compute
- B. Each service fetches its own data ad hoc
- C. Frontend provides context

**Chosen:** A

**Reasoning**
- Makes failover deterministic.
- Prevents inconsistent source behavior.
- Keeps the hybrid anchor/snapshot model explicit.

---

### 4.10 Persistence Checkpoints

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
4. snapshot refresh completed (per dataset)
5. analysis run started
6. final recommendation saved

---

### 4.11 Long-Running Interaction Model

**Options**
- A. POST creates run; frontend subscribes to status/result stream where needed
- B. One blocking request waits for everything
- C. Queue/worker architecture from day one

**Chosen:** A

**Reasoning**
- Allows progress UX without introducing a full worker stack.
- Keeps API ownership on the backend.

---

### 4.12 Streaming Scope

**Options**
- A. No streaming
- B. Stream only analyst/status output
- C. Make the whole system realtime-first

**Chosen:** B

**Reasoning**
- Only the AI Analyst panel and perhaps ingest status truly benefit from progressive output.
- The rest of the product remains request/response.

---

### 4.13 Internal Service Decomposition

**Options**
- A. Separate backend services by responsibility
- B. One giant analysis service
- C. Microservices from day one

**Chosen:** A

**Reasoning**
- Gives modularity without operational overhead.
- Keeps service ownership clear.

---

### 4.14 Recommendation Assembly Authority

**Options**
- A. One backend recommendation assembler merges numeric engine + bounded AI output
- B. AI decides final recommendation directly
- C. Frontend merges ranking and AI explanation

**Chosen:** A

**Reasoning**
- Preserves the numeric engine as primary authority.
- Enforces bounded AI behavior.
- Produces one canonical response object.

---

### 4.15 Error Model

**Options**
- A. Stage-specific typed failures
- B. Generic 500s only
- C. Silent degradation with little explanation

**Chosen:** A

**Reasoning**
- This product needs explainable failure, not only explainable success.
- Supports better repair UX and easier debugging.

---

### 4.16 Queue / Background Job Posture

**Options**
- A. No real queue initially; lightweight background tasks only if needed
- B. Celery/Redis from the start
- C. Full event bus / worker fleet

**Chosen:** A

**Reasoning**
- Keeps hackathon complexity low.
- A proper worker stack is only justified if ingestion or analysis times become a real bottleneck.

---

### 4.17 Hosted Runtime Topology

**Options**
- A. Web and API are separate; web talks only to API; API talks to storage/providers
- B. Web sometimes talks directly to providers/storage
- C. All-in-one deploy with blurred boundaries

**Chosen:** A

**Reasoning**
- Preserves the backend as the only business logic authority.
- Prevents direct frontend bypasses around validation, logging, snapshot policy, or fallback rules.

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
- optional ingest-status visibility for debugging/admin mode

**Not responsible for**
- business truth
- ranking logic
- simulation logic
- fallback logic
- source fetching logic
- recommendation assembly

---

### 5.2 Layer 2 — API/Application Layer (FastAPI)

**Responsibilities**
- receive requests
- create quote-prep runs, ingest runs, and analysis runs
- coordinate workflow stages
- expose REST endpoints
- expose SSE streaming endpoints where needed
- coordinate persistence and final response delivery

**Rule**
Route handlers stay thin.

---

### 5.3 Layer 3 — Domain / Service Layer

This is the real logic center.

**Quote Services**
- `quote_ingest_service`
- `quote_validation_service`

**Ingestion Services**
- `reference_data_service`
- `market_data_service`
- `weather_risk_service`
- `holiday_service`
- `macro_data_service`
- `news_event_service`
- `resin_benchmark_service`
- `ingest_orchestrator_service`

**Analysis Services**
- `fx_service`
- `cost_engine_service`
- `recommendation_engine_service`
- `analysis_run_service`
- `recommendation_assembler_service`

**AI Services**
- `ai_orchestrator_service`
- `context_builder_service`

---

### 5.4 Layer 4 — Infrastructure / Provider Layer

**Responsibilities**
- local disk / storage access
- SQLite access
- JSON repository access
- snapshot repository access
- raw artifact repository access
- LLM provider wrapper
- `yfinance` adapter
- OpenWeatherMap client wrapper
- OpenDOSM/data.gov.my client wrapper
- GNews provider wrapper
- Trafilatura wrapper
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
3. Call extraction model
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

## 6.2 Workflow B — Snapshot Ingestion

### Purpose
Refresh external market/logistics context and convert it into normalized local snapshots.

### Stages
1. Create ingest job
2. Load source config and required anchors
3. Fetch external source data through provider adapters
4. Normalize to internal contracts
5. Validate records
6. Save raw artifacts where relevant
7. Save snapshot envelope
8. Persist job result and warnings

### Output states
- `success`
- `partial`
- `failed`

### Phase 1 datasets
- reference anchors
- FX
- energy
- holidays

### Phase 2+ datasets
- weather risk
- OpenDOSM macro context
- GNews event context
- PP resin benchmark

---

## 6.3 Workflow C — Analysis

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
4. Load reference anchors and latest approved snapshots
5. Run deterministic cost engine
6. Run ranking engine
7. Build AI context package
8. Run thin LangGraph reasoning flow
9. Merge deterministic and AI outputs
10. Persist final result
11. Return result / stream analyst output

---

## 6.4 Workflow D — Single-Quote Fallback

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
- load market/event/risk snapshots
- load supplier seed data
- select latest approved snapshot version per dataset
- invoke fallback strategy if critical snapshot is stale or missing

**Rule**
The analysis stage must never scrape arbitrary sites or fetch raw article pages.

---

### Stage 4 — Deterministic Engine

**Responsibility**
- hard costs
- MOQ penalty
- supplier trust penalty
- probabilistic FX outputs
- ranking base score
- lead-time/disruption adjustments where applicable

**Outputs**
- p10 / p50 / p90
- normalized per-ton cost
- total landed cost for buyer-required quantity
- base ranking

---

### Stage 5 — AI Reasoning Layer

**Responsibility**
- interpret market and timing context
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
- snapshot freshness metadata (internal or judge/debug surface)

---

### Stage 7 — Persistence + Delivery

**Responsibility**
- persist final run result
- stream analyst text if enabled
- return final payload to frontend

---

## 8. Snapshot Ingestion Architecture

## 8.1 Design Principle

External sources are not analysis-time truth.  
**Normalized snapshots are analysis-time truth.**

This means:
- ingestion is allowed to be imperfect, retried, or partially stale,
- while analysis remains deterministic, bounded, and stable.

## 8.2 Snapshot Classes

### A. Reference Anchors
Static JSON:
- freight matrix
- tariff rules
- port coordinates
- curated scrape source registry

### B. Generated Snapshots
Refreshed by backend jobs:
- FX
- energy
- holidays
- weather risk
- OpenDOSM macro context
- news-derived event context
- PP resin benchmark

### C. Raw Artifacts
Debug/provenance storage:
- raw OpenDOSM downloads
- raw GNews result sets
- raw resin HTML pages
- extracted resin text

## 8.3 Common Snapshot Envelope

All ingestion datasets must use the same envelope:

```json
{
  "dataset": "string",
  "source": "string",
  "fetched_at": "ISO-8601 timestamp",
  "as_of": "YYYY-MM-DD or null",
  "status": "success | partial | failed",
  "record_count": 0,
  "data": []
}
```

## 8.4 Snapshot Promotion Rule

A dataset may become the active snapshot only if:
- fetch succeeded or partially succeeded in an acceptable way,
- normalization succeeded,
- validation rules passed,
- and freshness metadata is captured.

## 8.5 Last-Known-Good Policy

If refresh fails for a non-critical dataset:
- keep last valid snapshot,
- mark freshness/staleness,
- continue analysis if allowed by policy.

---

## 9. Provider Adapter Architecture

## 9.1 Why Adapters Exist

Provider adapters isolate:
- third-party library quirks,
- API semantics,
- credentials,
- retries,
- and response-shape changes.

Services must not consume raw provider payloads directly.

## 9.2 Required Adapters

- `llm_provider.py`
- `yfinance_provider.py`
- `openweather_provider.py`
- `opendosm_provider.py`
- `gnews_provider.py`
- `trafilatura_client.py`

## 9.3 Adapter Contract Rule

Every adapter should:
- return normalized internal shapes,
- hide raw SDK/client complexity,
- raise typed provider errors,
- avoid leaking source-specific object models into services.

---

## 10. Repositories and Data Access

## 10.1 Repository Types

### `reference_repository`
Loads and validates static anchors.

### `snapshot_repository`
Reads/writes latest normalized snapshots.

### `raw_repository`
Reads/writes raw artifacts for provenance/debugging.

## 10.2 Core Rule

Services should never read files directly.  
All file and snapshot access must go through repositories.

## 10.3 Why

This prevents:
- duplicate file logic,
- inconsistent fallback behavior,
- silent schema drift,
- and future migration pain when moving to hosted storage.

---

## 11. Suggested Internal Data Models

These are conceptual architecture entities, not exact code.

### 11.1 QuoteUpload
- upload_id
- filename
- storage_path
- uploaded_at
- status

### 11.2 ExtractedQuote
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

### 11.3 QuoteValidationResult
- quote_id
- status
- reason_codes
- missing_fields
- user_corrected_fields

### 11.4 IngestJob
- job_id
- dataset
- source
- started_at
- completed_at
- status
- warnings

### 11.5 SnapshotManifest
- dataset
- source
- as_of
- fetched_at
- status
- record_count
- storage_path
- freshness_state

### 11.6 AnalysisRun
- run_id
- valid_quote_ids
- quantity
- urgency
- hedge_preference
- run_status
- started_at
- completed_at

### 11.7 RecommendationResult
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

## 12. Error and Fallback Architecture

## 12.1 Typed Failure Categories

Recommended architecture-level error types:

- `ExtractionFailed`
- `ValidationFailed`
- `UnsupportedScope`
- `ExternalFetchFailed`
- `NormalizationFailed`
- `SnapshotWriteFailed`
- `SnapshotStaleUsingLastValid`
- `NoValidQuotes`
- `SingleValidQuoteFallback`
- `ComputationFailed`
- `AIReasoningFailedFallbackToDeterministic`

## 12.2 Failure Strategy

- Fail early at the validation boundary.
- Continue with valid quotes when partial failure is acceptable.
- Surface human-readable repair actions.
- Never fabricate missing critical data.
- If a non-critical source refresh fails, use last valid snapshot if policy permits.
- Keep scraping failures isolated from live comparison requests.

---

## 13. API Surface Recommendation

The exact endpoint names may vary, but the shape should stay like this.

### Quote Prep
- `POST /quote-uploads`
- `GET /quote-uploads/{upload_id}`
- `POST /quotes/{quote_id}/repair`

### Ingestion
- `POST /ingest/reference/load`
- `POST /ingest/market/fx`
- `POST /ingest/market/energy`
- `POST /ingest/holidays`
- `POST /ingest/weather/ports`
- `POST /ingest/macro/opendosm`
- `POST /ingest/news/gnews`
- `POST /ingest/resin/scrape`
- `POST /ingest/run/daily`
- `GET /ingest/status/{job_id}`
- `GET /snapshots/latest/{dataset}`

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

## 14. Frontend-Backend Interaction Model

## 14.1 Quote Prep UX

1. User uploads PDFs
2. Frontend sends files to FastAPI
3. FastAPI stores files and runs extraction
4. Frontend receives quote prep results
5. User fixes invalid/incomplete quotes if needed

## 14.2 Analysis UX

1. User enters required quantity and urgency
2. Frontend sends one analysis request
3. Backend owns the full pipeline
4. Backend loads latest approved snapshots internally
5. Frontend subscribes to run status / analyst stream if needed
6. Frontend renders final recommendation object

## 14.3 Ingestion UX

This is optional for normal users and may be hidden or admin/debug only.

1. User/developer triggers an ingest refresh or scheduled refresh runs
2. Backend fetches, normalizes, validates, and stores snapshots
3. Backend returns ingest status and any warnings
4. Analysis later consumes the latest approved snapshots

---

## 15. Observability and Tracing Architecture

## 15.1 Langfuse

Use for:
- AI traces
- model calls
- tool/use-step traces
- reasoning workflow observability
- optionally resin benchmark extraction chain observability

## 15.2 Structured App Logs

Use for:
- upload lifecycle
- extraction errors
- validation failures
- snapshot refresh failures
- provider timeouts / warnings
- JSON load issues
- run lifecycle logs
- internal exceptions

## 15.3 Why This Split

AI traces and app/system logs serve different purposes and should remain separate.

---

## 16. Security and Boundary Rules

Even for hackathon v1, keep these architecture boundaries clear.

1. Frontend must not bypass FastAPI for core business actions.
2. Business rules are never enforced only in the frontend.
3. AI provider access is wrapped behind one backend provider layer.
4. External data access is wrapped behind provider adapters.
5. Static anchors and snapshots are only accessed through repository layers.
6. Raw scraped content must not be treated as analysis-ready truth without normalization/validation.

---

## 17. Recommended Folder-to-Architecture Mapping

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
  app/
    main.py
    api/
      routes/
        health.py
        ingest_reference.py
        ingest_market.py
        ingest_weather.py
        ingest_macro.py
        ingest_news.py
        ingest_resin.py
    core/
      config.py
      logging.py
      constants.py
      exceptions.py
    schemas/
      reference.py
      market.py
      weather.py
      macro.py
      news.py
      resin.py
      common.py
    providers/
      yfinance_provider.py
      openweather_provider.py
      opendosm_provider.py
      gnews_provider.py
      llm_provider.py
    scrapers/
      trafilatura_client.py
      resin_source_registry.py
      resin_extractor.py
      resin_validators.py
    repositories/
      reference_repository.py
      snapshot_repository.py
      raw_repository.py
    services/
      reference_data_service.py
      market_data_service.py
      weather_risk_service.py
      holiday_service.py
      macro_data_service.py
      news_event_service.py
      resin_benchmark_service.py
      ingest_orchestrator_service.py
      quote_ingest_service.py
      quote_validation_service.py
      fx_service.py
      cost_engine_service.py
      recommendation_engine_service.py
      analysis_run_service.py
      recommendation_assembler_service.py
      ai_orchestrator_service.py
    models/
      snapshot_manifest.py
      ingest_job.py
    utils/
      time.py
      hashing.py
      dedupe.py
      text_cleaning.py
```

### Data Storage Layout

```text
apps/api/data/
  reference/
    freight_rates.json
    tariffs_my_hs.json
    ports.json
    source_registry.json
  snapshots/
    fx/
    energy/
    weather/
    holidays/
    opendosm/
    news/
    resin/
  raw/
    opendosm/
    news/
    resin_html/
    resin_text/
  tmp/
```

---

## 18. Three Review Points Worth Checking Before Build

These do not block the architecture, but they are the best places for final review.

### 18.1 Analyst Streaming Necessity
Should the demo truly show progressive analyst streaming, or would stage progress + final explanation be enough?

### 18.2 Ingestion Trigger Policy
Should ingest refresh be manual-only during hackathon, or should there also be a lightweight scheduled refresh path?

### 18.3 Snapshot Freshness Thresholds
Which datasets should be treated as hard-critical vs soft-critical when stale?

---

## 19. Final Recommended Architecture Summary

LintasNiaga v1 should be implemented as a **backend-owned sequential procurement decision system** with **three core backend workflows**:

1. **Quote Prep**
   - upload
   - extract
   - normalize
   - validate
   - repair

2. **Snapshot Ingestion**
   - fetch external data through adapters
   - normalize and validate
   - persist raw artifacts and approved snapshots

3. **Analysis**
   - load valid quotes
   - load reference anchors and latest snapshots
   - compute deterministic cost/risk outputs
   - run bounded AI reasoning
   - assemble canonical recommendation
   - persist and return results

The final system should have:
- a thin frontend,
- a strong FastAPI backbone,
- a thin LangGraph AI layer,
- provider adapters for all external dependencies,
- a snapshot store that insulates analysis from runtime scraping,
- centralized fallback logic,
- and strict architecture boundaries that keep math, rules, ingestion, and AI cleanly separated.

That is the architecture most likely to be:
- buildable,
- explainable,
- debuggable,
- and persuasive to judges.

---

## 20. Nuances and Open Uncertainties

1. **FX source choice is now adapter-driven**  
   The original architecture assumed BNM-centric FX. The new ingestion-aligned architecture assumes a swappable market-data adapter, with `yfinance` acceptable for hackathon speed and a more official source possible later.

2. **Weather must stay derived, not raw**  
   The architecture supports weather only as a logistics-risk derivation pipeline, not as generic weather exploration.

3. **News must stay event-derived, not headline-driven**  
   GNews belongs in ingestion and event normalization, not in live analysis-time raw form.

4. **Resin benchmark scraping is the most fragile subsystem**  
   The source registry, raw artifact capture, extraction validation, and promotion rules matter more than scraper volume.

5. **Payment-horizon logic is architecturally important even if it remains rule-based at first**  
   The current architecture leaves room for it to remain a deterministic rule layer even before richer source integration exists.
