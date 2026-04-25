# LintasNiaga System Analysis Document

**Project:** LintasNiaga  
**Document Type:** System Analysis Document  
**Version:** 1.0 submission draft  
**Grounded Against Code:** 2026-04-25  
**Prepared For:** UMHackathon 2026 Preliminary Round

## 1. System Overview

LintasNiaga is a backend-owned procurement analysis system that processes supplier quotation PDFs, refreshes relevant market and logistics context, computes landed-cost scenarios, and assembles an explainable recommendation.

The current system is implemented as a monorepo with:

- a Next.js frontend in `apps/web`
- a FastAPI backend in `apps/api`
- a local file-backed data layer under `data/`

## 2. Business Objective

The system exists to help Malaysian plastics SMEs answer a real procurement decision:

- which PP resin supplier to choose
- whether to place the order now or wait
- what level of FX hedge to apply

## 3. Problem Analysis

Manual procurement comparison is unreliable because a supplier quote alone does not reveal:

- real landed cost
- FX downside
- freight and tariff effect
- MOQ lock-up
- supplier trust penalty
- benchmark fairness versus market price
- timing and disruption context

The system addresses this by combining structured quote extraction with refreshed context and deterministic risk analysis.

## 4. Current System Boundary

### Inputs

- uploaded PDF quotations
- user-entered quantity
- urgency selection
- hedge preference
- reference data
- external snapshot data

### Outputs

- ranked quote analysis
- recommendation card
- landed-cost fan chart
- hedge replay result
- risk and benchmark explanation
- bank-instruction draft

### External Integrations

- yfinance
- OpenWeather
- OpenDOSM / data.gov.my
- GNews
- SunSirs
- Langfuse
- GLM provider

## 5. Architectural Style

The system currently follows a service-oriented monolith pattern:

- FastAPI owns the business workflow
- provider modules isolate external data access
- repository modules isolate local data access
- services transform raw inputs into analysis-ready structures
- the frontend remains thin and mostly presentation-oriented

## 6. High-Level Component Model

### Frontend

Responsible for:

- upload UI
- extracted-field review
- analysis trigger
- progress display
- result rendering
- hedge slider interactions
- PDF download initiation

### Backend API

Responsible for:

- quote intake and repair
- snapshot ingestion endpoints
- latest snapshot read endpoints
- analysis execution
- hedge replay
- bank-instruction drafting
- health and traceability visibility

### Data Layer

Responsible for:

- reference anchors
- normalized snapshots
- raw artifacts
- uploaded files

## 7. Core Runtime Workflows

## 7.1 Quote Intake Workflow

1. User uploads PDF via `/quotes/upload`
2. Backend stores upload artifact
3. Deterministic text extraction runs first
4. GLM vision fallback runs if needed
5. Quote fields are assembled into `QuoteState`
6. User can repair fields via `/quotes/{quote_id}/repair`

## 7.2 Snapshot Ingestion Workflow

1. Provider fetches source data
2. Service normalizes the response
3. Snapshot envelope is created
4. Snapshot repository writes the snapshot
5. Raw artifacts are stored where required

## 7.3 Analysis Workflow

1. Frontend calls `/analysis/run`
2. Backend loads reference data
3. Backend refreshes and validates required snapshots
4. Deterministic landed-cost calculations run
5. FX + Brent Monte Carlo simulation runs
6. AI context is assembled
7. Bounded reasoning flow executes
8. Final payload is stored in memory and returned

## 7.4 Hedge Replay Workflow

1. Frontend calls `/analysis/{run_id}/hedge-simulate`
2. Backend reloads run context
3. Same seed and stored scenario inputs are reused
4. Hedge-adjusted envelopes are returned

## 7.5 Bank Instruction Workflow

1. Frontend calls `/analysis/{run_id}/bank-instruction-draft`
2. Backend prepares fallback-safe structured draft
3. GLM wording layer may refine content
4. Frontend renders PDF using React PDF

## 8. Data Analysis and Decision Logic

## 8.1 Deterministic Cost Logic

Current landed-cost logic uses:

- material cost
- freight cost
- tariff cost
- MOQ penalty
- trust penalty

## 8.2 Monte Carlo Logic

Current stochastic logic uses:

- quote currency FX path
- `USDMYR` freight conversion path
- Brent oil path
- historical log-return volatility
- FX-oil correlation

Output includes:

- p10
- p50
- p90
- risk width
- hedge-adjusted envelopes

## 8.3 AI Reasoning Logic

AI is used for:

- quote extraction fallback
- recommendation reasoning
- streamed analyst explanation
- bank instruction wording

AI is not the primary source of procurement math.

## 8.4 Benchmark Logic

PP resin benchmark from SunSirs is used to:

- compare quote price against market
- identify suspicious low or premium pricing
- inform explanation and caveat generation

It is not currently a Monte Carlo stochastic driver.

## 9. Data Sources and Their Roles

### FX and Brent

- source: `yfinance`
- role: price history for simulation and market context

### Weather

- source: OpenWeather
- role: derive delay and port-risk signals

### Holidays

- source: `python-holidays`
- role: derive delay buffers around holiday windows

### Macro

- source: OpenDOSM
- role: enrich context and risk explanation

### News

- source: GNews
- role: provide current event context

### PP Resin Benchmark

- source: SunSirs
- role: benchmark fairness and quote-vs-market analysis

## 10. Persistence Analysis

### Persisted to Disk

- uploads
- snapshots
- raw artifacts
- reference files

### Held In Memory

- quote states
- run contexts
- analysis results
- Monte Carlo replay inputs

### Important Current Limitation

Runtime analysis state is not yet durably persisted across server restarts.

## 11. API Surface Analysis

Current route groups:

- health
- quotes
- ingest reference
- ingest market
- ingest weather
- ingest macro
- ingest news
- ingest resin
- ingest holidays
- snapshots
- analysis

Important analysis routes:

- `POST /analysis/run`
- `GET /analysis/{run_id}`
- `GET /analysis/{run_id}/stream`
- `GET /analysis/{run_id}/traceability`
- `POST /analysis/{run_id}/hedge-simulate`
- `POST /analysis/{run_id}/bank-instruction-draft`

## 12. Security and Integrity Considerations

Current system integrity depends on:

- bounded product scope
- validation before comparison
- central backend ownership of logic
- snapshot normalization before analysis
- traceability for AI interactions

Current limitations:

- no full enterprise auth layer
- local file-backed storage
- in-memory active run state

These are acceptable for the hackathon stage but should be addressed in later productionization.

## 13. Traceability and Observability

Current observability includes:

- Langfuse trace visibility
- `/health/langfuse`
- `/analysis/{run_id}/traceability`
- structured logs for provider, upload, and analysis failure paths

This is important because the hackathon handbook emphasizes sound engineering process, documentation, and QA discipline.

## 14. Risks and Gaps

1. Some critical analysis context depends on successful live refresh.
2. Run state is still memory-backed.
3. Settings are split across two systems.
4. Background scheduling covers only part of the ingestion landscape.
5. Hosted deployment and persistent enterprise architecture are not yet active.

## 15. Conclusion

LintasNiaga currently operates as a coherent procurement decision system rather than a disconnected prototype. Its strongest technical characteristic is the combination of:

- quote extraction and repair
- refreshed market context
- deterministic landed-cost logic
- FX + Brent Monte Carlo simulation
- benchmark fairness analysis
- bounded AI reasoning with traceability

This makes the system suitable for a credible hackathon submission focused on real procurement decision intelligence.
