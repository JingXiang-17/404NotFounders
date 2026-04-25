# LintasNiaga Architecture Blueprint

## System Architecture for Hackathon v1.1 (Implementation-Aligned)

**Project:** LintasNiaga  
**Document Type:** Architecture blueprint  
**Previous Version:** 2.1  
**Current Version:** 2.2  
**Last Grounded Against Code:** 2026-04-25  
**Scope:** Architecture as currently implemented in the repository, with outdated assumptions removed  
**Primary Goal:** Describe the real backend/frontend/runtime architecture truthfully enough for handoff, debugging, and judging

---

## 1. Current Status Summary

LintasNiaga is currently a **backend-owned procurement analysis system** built around:

1. **Quote intake and validation**
2. **External data ingestion into normalized snapshots**
3. **Deterministic analysis plus bounded GLM reasoning**
4. **Result delivery with hedge simulation, traceability, and bank-instruction drafting**

The codebase is no longer just “ingestion-aligned” in principle. It now contains:

- live snapshot refresh checks inside the analysis run,
- a real FX + Brent correlated Monte Carlo service,
- Langfuse-backed AI traceability endpoints,
- scheduled background refresh for some datasets,
- SunSirs PP benchmark ingestion and quote-vs-market checks,
- OpenWeather, GNews, holidays, and OpenDOSM feeds wired into analysis context.

This document intentionally describes **what exists now**, not the earlier desired end-state.

---

## 2. What Is New, Changed, and Removed

### 2.1 New Since the Earlier Blueprint

- `fx_simulation_service.py` now provides a snapshot-only Monte Carlo service using:
  - quote-currency FX snapshots,
  - `USDMYR` freight FX conversion,
  - Brent crude (`energy/BZ=F`) correlation,
  - deterministic hedge replay using stable seeds,
  - Langfuse span instrumentation for the simulation itself.
- Analysis now exposes:
  - `GET /analysis/{run_id}/traceability`
  - `POST /analysis/{run_id}/hedge-simulate`
  - `POST /analysis/{run_id}/bank-instruction-draft`
- Snapshot read APIs now expose:
  - latest FX points,
  - latest macro,
  - latest news,
  - latest weather,
  - latest resin.
- Background tasks in `main.py` now refresh:
  - GNews hourly,
  - holidays daily,
  - SunSirs resin daily.

### 2.2 Changed From the Earlier Blueprint

- The earlier blueprint said analysis should only consume snapshots and never refresh live sources.  
  Current implementation is stricter and more hybrid:
  - analysis still consumes normalized snapshots,
  - but it first calls refresh/ensure-fresh logic for required datasets before computing results.
- The earlier blueprint implied generalized centralized fallback logic.  
  Current implementation is mixed:
  - some services still support last-valid fallback,
  - but the main analysis path is now intentionally strict and blocks when critical data is missing or invalid.
- The earlier blueprint treated PP resin as a possible simulation driver.  
  Current implementation does **not** do that:
  - PP resin is benchmark context only,
  - used for quote-vs-market risk and GLM explanation,
  - not a Monte Carlo material-price path driver.
- The earlier blueprint implied database-centric persistence.  
  Current implementation is mostly:
  - local JSON snapshots,
  - raw artifact files,
  - uploaded PDF files,
  - in-memory quote states and in-memory analysis run results.

### 2.3 Removed / Not Actually Present

- No `ingest_orchestrator_service.py`
- No `ready` endpoint
- No queue/worker stack
- No real event bus
- No direct WorldFirst execution path
- No generalized snapshot approval/promotion manifest layer
- No persistent database-backed analysis run store in active use

---

## 3. Architecture Intent As Implemented

LintasNiaga is not a general chatbot and not a frontend-driven dashboard.

It is a **FastAPI-owned procurement workflow system** where the backend is the source of truth for:

- quote extraction and repair,
- snapshot refresh and normalization,
- deterministic landed-cost and risk calculations,
- Monte Carlo fan-chart generation,
- GLM reasoning orchestration,
- traceability metadata,
- and final recommendation assembly.

The main architectural qualities currently optimized are:

- judge/demo stability,
- explicit provenance,
- bounded AI behavior,
- traceability,
- source separation,
- and explainable failure.

---

## 4. High-Level Runtime Topology

### 4.1 Core Components

- **Frontend:** Next.js web app in `apps/web`
- **Backend:** FastAPI app in `apps/api`
- **AI orchestration:** LangGraph-style thin reasoning flow in `ai_orchestrator_service.py`
- **Model provider:** GLM provider wrapper in `llm_provider.py`
- **Tracing:** Langfuse for AI traces and now Monte Carlo span traces
- **Persistence:** local filesystem JSON + raw artifacts + uploaded PDFs + in-memory run state

### 4.2 External Source Adapters

- `yfinance_provider.py`
  - FX history
  - Brent crude history via `BZ=F`
- `openweather_provider.py`
  - attempts longest available forecast endpoint for the configured key
- `opendosm_provider.py`
  - Industrial Production Index
  - Malaysia trade data
- `gnews_provider.py`
  - bucketed article fetching across logistics, finance, and geopolitical queries
- `sunsirs_provider.py`
  - PP benchmark page fetch plus challenge handling

### 4.3 Context Diagram

```text
[User]
   |
   v
[Next.js Web App]
   |
   | REST + SSE
   v
[FastAPI]
   |
   |-- Quote upload / repair
   |-- Ingest endpoints
   |-- Snapshot read endpoints
   |-- Analysis run orchestration
   |-- Hedge simulation
   |-- Bank instruction drafting
   |-- Traceability endpoint
   |
   |---> GLM model provider
   |---> Langfuse
   |---> yfinance
   |---> OpenWeather
   |---> OpenDOSM
   |---> GNews
   |---> SunSirs
   |
   |---> data/reference
   |---> data/snapshots
   |---> data/raw
   |---> apps/api/uploads
   |
   |---> in-memory quote states
   |---> in-memory analysis run results
```

---

## 5. Core Architectural Principles That Are Actually True Today

1. **FastAPI is the workflow owner.**
2. **The browser is a client, not the decision engine.**
3. **Deterministic math still runs before final AI recommendation assembly.**
4. **External data enters analysis only through normalized snapshot shapes.**
5. **Some critical datasets are refreshed immediately before analysis rather than trusted blindly.**
6. **PP resin is benchmark evidence, not a Monte Carlo stochastic driver.**
7. **Langfuse traceability is first-class for AI calls and partially extended to numeric simulation.**
8. **The current system prefers strict failure over silent fake fallback in the main analysis path.**
9. **State persistence is still mostly file-backed and memory-backed, not fully database-backed.**

---

## 6. Real Workflow Architecture

### 6.1 Workflow A: Quote Intake and Repair

**Entry points**

- `POST /quotes/upload`
- `POST /quotes/{quote_id}/repair`
- `GET /quotes/{quote_id}`

**Actual behavior**

1. Save uploaded PDF to `apps/api/uploads`
2. Extract text from the first two PDF pages if possible
3. Try deterministic text parsing first
4. If text extraction is insufficient, render page images and call GLM vision extraction
5. Merge page-level quote candidates into one structured quote
6. Validate quote fields with `quote_validation_service`
7. Store resulting `QuoteState` in the in-memory `QUOTE_STATES` dictionary

**Important current truth**

- Quote upload state is not persisted in SQLite or Postgres.
- Extraction trace URLs and trace IDs are stored on the in-memory `QuoteState`.

### 6.2 Workflow B: Snapshot Ingestion

**Entry points**

- `POST /ingest/reference/load`
- `POST /ingest/market/fx`
- `POST /ingest/market/energy`
- `POST /ingest/market/energy/ensure-fresh`
- `POST /ingest/holidays`
- `POST /ingest/holidays/ensure-fresh`
- `POST /ingest/weather`
- `POST /ingest/macro`
- `POST /ingest/macro/ipi`
- `POST /ingest/macro/trade`
- `POST /ingest/news/gnews`
- `POST /ingest/news/gnews/ensure-fresh`
- `POST /ingest/resin/sunsirs`
- `POST /ingest/resin/sunsirs/ensure-fresh`

**Actual behavior**

1. Provider fetches external data
2. Service normalizes into internal records
3. Snapshot envelope is created
4. Snapshot is written through `snapshot_repository`
5. Some services also write raw artifacts

**Important current truth**

- Snapshot freshness policy is service-specific.
- `snapshot_repository.write_snapshot(... keep_history=False)` is widely used for latest-only refresh flows.
- Macro snapshots still keep history by default.

### 6.3 Workflow C: Analysis

**Entry point**

- `POST /analysis/run`

**Actual current sequence**

1. Load reference data
2. Identify required non-MYR currencies from valid quotes
3. Refresh and validate:
   - FX snapshots for quote currencies
   - Brent energy snapshot
   - OpenDOSM IPI snapshot
   - OpenDOSM trade snapshot
   - GNews snapshot
   - SunSirs resin snapshot
   - OpenWeather snapshot
   - holidays snapshot
4. Run legacy FX simulation summaries with `fx_service.py` for context and benchmark conversion
5. Run real landed-cost Monte Carlo with `fx_simulation_service.py`
6. Build deterministic landed-cost results and ranking
7. Build structured AI context including:
   - tariff reference
   - freight reference by quote
   - oil snapshot summary
   - macro context
   - news events
   - resin benchmark and quote-vs-market risk
   - holiday context
   - weather context
   - risk-driver breakdown
   - selected Monte Carlo scenario summary
8. Call bounded GLM reasoning flow
9. Require captured Langfuse trace URL
10. Assemble final recommendation payload
11. Cache result in in-memory run dictionaries

### 6.4 Workflow D: Hedge Replay

**Entry point**

- `POST /analysis/{run_id}/hedge-simulate`

**Actual behavior**

- Reuses stored quote/run context
- Rebuilds FX+oil scenario for the winning quote
- Uses the same run seed so hedge narrows existing shocks instead of rerolling a new future

### 6.5 Workflow E: Bank Instruction Draft

**Entry point**

- `POST /analysis/{run_id}/bank-instruction-draft`

**Actual behavior**

- Reuses selected quote and hedge scenario
- Builds deterministic fallback draft first
- Calls GLM for strict JSON wording only
- Returns fallback draft if the LLM step fails

---

## 7. Dataset-by-Dataset Ingestion Truth

### 7.1 FX

- Source: `yfinance`
- Storage key: `fx/{PAIR}`
- Analysis behavior:
  - refreshed on demand before analysis,
  - required to be `success`,
  - required to have at least 30 rows.

### 7.2 Energy / Oil

- Source: `yfinance`
- Storage key: `energy/BZ=F`
- Used for:
  - freight/oil correlation in Monte Carlo
  - GLM context note about Brent move

### 7.3 Weather

- Source: OpenWeather
- Storage key: `weather`
- Current role:
  - cleaned port forecast summaries,
  - derived max port risk scores,
  - converted into `0/3/5/7` weather delay days for Monte Carlo,
  - included in GLM context and risk notes.
- Current refresh behavior:
  - refreshed during analysis,
  - manual ingest endpoint exists,
  - no background scheduler in `main.py`.

### 7.4 Holidays

- Source: `python-holidays`
- Storage key: `holidays`
- Current role:
  - rolling holiday calendar for MY/CN/TH/ID,
  - holiday window included in GLM context,
  - converted into capped holiday buffer days for Monte Carlo.
- Refresh behavior:
  - daily background refresh,
  - analysis also ensures freshness.

### 7.5 OpenDOSM Macro

- Source: OpenDOSM/data.gov.my
- Storage keys:
  - `macro`
  - `macro_trade`
- Current role:
  - GLM context,
  - risk-driver breakdown input,
  - not directly part of the stochastic Monte Carlo math.
- Refresh behavior:
  - refreshed during analysis,
  - manual ingest endpoints exist,
  - no background scheduler in `main.py`.

### 7.6 GNews

- Source: GNews API or RSS-backed provider mode depending on configuration
- Storage key: `news`
- Current role:
  - normalized article buckets,
  - context for GLM,
  - risk-driver notes,
  - not a hidden direct Monte Carlo coefficient in the new FX+oil simulator.
- Refresh behavior:
  - hourly background refresh,
  - analysis also ensures freshness.

### 7.7 PP Resin Benchmark

- Source: SunSirs
- Storage key: `resin`
- Raw artifacts:
  - HTML written through `RawRepository`
  - extracted text written through `RawRepository`
- Current role:
  - latest benchmark context,
  - quote-vs-market premium/discount classification,
  - GLM explanation support,
  - not part of the Monte Carlo path generator.
- Refresh behavior:
  - daily background refresh,
  - analysis also ensures freshness.

---

## 8. Monte Carlo Architecture As Implemented

The main fan chart is no longer the older “risk-driver multiplier” approximation alone.

### 8.1 Current Main Simulator

`fx_simulation_service.py`

It uses:

- quote currency FX snapshot,
- `USDMYR` snapshot for freight conversion,
- Brent snapshot for oil-linked freight surcharge,
- historical log returns,
- FX-oil correlation,
- deterministic seed replay per run,
- hedge ratio as partial locking of quote FX exposure.

### 8.2 Current Inputs

- quote data
- quantity in MT
- weather delay days
- holiday buffer days
- freight reference
- tariff rule
- supplier reliability
- FX and oil snapshots

### 8.3 Current Outputs

- daily p10/p50/p90 bands
- distribution at delivery
- material / freight / tariff p50 breakdown
- hedge-adjusted scenarios
- scenario objects consumed by the frontend analysis result page

### 8.4 Important Boundary

The new simulator is grounded in FX and oil market history.  
Macro/news/weather/holidays/resin still inform:

- refresh policy,
- delay inputs,
- benchmark checks,
- risk-driver explanation,
- and GLM reasoning,

but they are not all encoded as arbitrary hidden stochastic coefficients.

---

## 9. Persistence Architecture Truth

### 9.1 What Is Persisted to Disk

- uploaded PDFs in `apps/api/uploads`
- reference JSON under `data/reference`
- snapshots under `data/snapshots`
- raw artifacts under `data/raw`

### 9.2 What Is In Memory

- `QUOTE_STATES` in `quote_ingest_service.py`
- `_run_contexts` in `analysis_run_service.py`
- `_run_results` in `analysis_run_service.py`
- `_run_monte_carlo_inputs` in `analysis_run_service.py`

### 9.3 What Exists but Is Not the Main Runtime Store

- `core/config.py` still defines SQLite-related configuration
- current main runtime behavior does not use SQLite as the authoritative analysis state store

---

## 10. Provider and Repository Boundaries

### 10.1 Providers Present

- `llm_provider.py`
- `yfinance_provider.py`
- `openweather_provider.py`
- `opendosm_provider.py`
- `gnews_provider.py`
- `sunsirs_provider.py`
- `holiday_provider.py`

### 10.2 Repositories Present

- `reference_repository.py`
- `snapshot_repository.py`
- `raw_repository.py`

### 10.3 Current Boundary Rule

The code mostly respects provider/repository boundaries, with services owning:

- normalization,
- freshness policy,
- and transformation into analysis-ready structures.

That part of the original architecture remains correct.

---

## 11. Current API Surface

### Health

- `GET /health`
- `GET /health/langfuse`

### Quotes

- `POST /quotes/upload`
- `GET /quotes/{quote_id}`
- `POST /quotes/{quote_id}/repair`

### Ingest

- `POST /ingest/reference/load`
- `POST /ingest/market/fx`
- `POST /ingest/market/energy`
- `POST /ingest/market/energy/ensure-fresh`
- `POST /ingest/holidays`
- `POST /ingest/holidays/ensure-fresh`
- `POST /ingest/weather`
- `POST /ingest/macro`
- `POST /ingest/macro/ipi`
- `POST /ingest/macro/trade`
- `POST /ingest/news/gnews`
- `POST /ingest/news/gnews/ensure-fresh`
- `POST /ingest/resin/sunsirs`
- `POST /ingest/resin/sunsirs/ensure-fresh`

### Snapshots

- `GET /snapshots/latest/fx`
- `GET /snapshots/latest/macro`
- `GET /snapshots/latest/news`
- `GET /snapshots/latest/weather`
- `GET /snapshots/latest/resin`

### Analysis

- `POST /analysis/run`
- `GET /analysis/{run_id}`
- `GET /analysis/{run_id}/stream`
- `GET /analysis/{run_id}/traceability`
- `POST /analysis/{run_id}/hedge-simulate`
- `POST /analysis/{run_id}/bank-instruction-draft`

---

## 12. Frontend-Backend Contract Reality

The frontend is still thin in the intended sense:

- it uploads PDFs,
- triggers one analysis run,
- renders the returned result payload,
- requests hedge recalculation,
- requests bank instruction draft JSON,
- and displays Langfuse trace links and explanation panels.

The backend still owns:

- ranking,
- simulation,
- risk derivation,
- and AI recommendation grounding.

That architectural boundary remains valid.

---

## 13. Observability and Traceability

### 13.1 Langfuse

Currently used for:

- quote extraction traces,
- recommendation reasoning traces,
- streamed analyst explanation traces,
- simulation span traces in `fx_simulation_service.py`,
- traceability status via `/health/langfuse`,
- traceability visibility via `/analysis/{run_id}/traceability`.

### 13.2 Logs

Structured app logs are used for:

- background refresh loops,
- provider failures,
- upload/extraction issues,
- analysis failures,
- and fallback warnings where still applicable.

---

## 14. Folder-to-Architecture Mapping (Current Truth)

```text
apps/web/
  src/app/analysis/[id]/results/
  src/components/

apps/api/app/
  api/routes/
  core/
  providers/
  repositories/
  schemas/
  scrapers/
  services/
  main.py

data/
  reference/
  snapshots/
  raw/
```

### Important current note

The older blueprint mentioned folders such as `models/` and services such as `ingest_orchestrator_service.py`.  
Those are not part of the current repo architecture and should not be described as active components.

---

## 15. Architecture Risks and Honest Gaps

These are real current limitations, not theoretical ones.

1. **Analysis state is still in memory**
   - server restarts lose run context and quote state.

2. **Analysis refreshes live sources before compute**
   - this improves truthfulness,
   - but it means analysis latency still depends on some upstream fetches.

3. **Background scheduling is partial**
   - news, holidays, and resin are scheduled,
   - FX, energy, weather, and macro are not continuously scheduled in `main.py`.

4. **Two settings systems still coexist**
   - `core/config.py`
   - `core/settings.py`

5. **Strict analysis can fail hard when sources are unhealthy**
   - this is deliberate,
   - but it is an architectural tradeoff against resilience.

---

## 16. Final Architecture Summary

LintasNiaga as of 2026-04-25 is best described as a **FastAPI-owned procurement analysis system with file-backed ingestion and in-memory run orchestration**.

It currently consists of:

1. **Quote workflow**
   - PDF upload,
   - deterministic text extraction first,
   - GLM fallback extraction,
   - validation and repair.

2. **Snapshot ingestion workflow**
   - provider adapters fetch external sources,
   - services normalize and validate data,
   - snapshots and raw artifacts are written locally.

3. **Analysis workflow**
   - refreshes critical datasets,
   - loads normalized snapshots and references,
   - computes deterministic results and FX+oil Monte Carlo scenarios,
   - runs bounded GLM reasoning,
   - returns a canonical analysis result with traceability and hedge tooling.

This version is more credible than the older architecture description because it matches the repo’s actual behavior:

- strict data validation before analysis,
- live ensured freshness for critical datasets,
- PP resin as benchmark-only,
- Monte Carlo grounded in FX and Brent history,
- Langfuse traceability endpoints,
- and a clear split between what is implemented versus what remains roadmap.
