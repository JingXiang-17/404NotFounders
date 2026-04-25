# LintasNiaga Tech Stack Blueprint
## Implementation-Grounded Technical Stack Guide

**Project:** LintasNiaga  
**Document Type:** Technical stack blueprint  
**Previous Version:** 2.1  
**Current Version:** 2.2  
**Last Grounded Against Code:** 2026-04-25  
**Scope:** Real stack and tooling currently present in the repository, with roadmap-only items clearly separated

---

## 1. Current Technical Reality Summary

LintasNiaga is currently a **two-app monorepo** with:

1. a **Next.js frontend** in `apps/web`
2. a **FastAPI backend** in `apps/api`
3. a **local file-backed data layer** under `data/`

The stack is now more mature than the older ingestion-first draft, but it is also more specific than that draft claimed. The repo currently includes:

- real Next.js 16 + React 19 frontend code
- FastAPI + Pydantic backend services
- a real FX + Brent Monte Carlo simulation service
- GLM provider integration with Langfuse tracing
- local snapshot, raw artifact, and upload storage
- background refresh loops for some datasets
- React Query, PDF generation, charting, and streaming analysis UI

This document describes **what is actually used now**, not what was merely intended earlier.

---

## 2. What Is New, Changed, and Removed

### 2.1 New Since the Earlier Stack Blueprint

- `apps/web` now includes:
  - `@tanstack/react-query`
  - `@react-pdf/renderer`
  - Recharts-based fan chart rendering
  - `motion` animation package
- `apps/api` now includes:
  - `fx_simulation_service.py` for real FX + oil Monte Carlo
  - Langfuse simulation span tracing
  - SunSirs resin scraping with raw HTML/text evidence
  - health endpoint for Langfuse status
  - hedge replay and bank-instruction draft endpoints
- Background refresh loops now exist in `main.py` for:
  - hourly GNews
  - daily holidays
  - daily PP resin

### 2.2 Changed From the Earlier Stack Blueprint

- The earlier document treated SQLite as active runtime truth.  
  Current runtime truth is mostly:
  - JSON snapshots
  - raw artifact files
  - uploaded PDFs
  - in-memory quote state
  - in-memory analysis run state
- The earlier document treated the frontend component stack as `shadcn/ui`.  
  Current repo truth is:
  - `components.json` follows shadcn schema style
  - actual primitives are mostly built on `@base-ui/react`
  - custom local UI components wrap those primitives
- The earlier document implied a broad LangGraph-owned AI architecture.  
  Current truth is narrower:
  - LangGraph is used in `ai_orchestrator_service.py`
  - deterministic backend services still own the real business logic
- The earlier document implied broader hosted infrastructure decisions as if they were active.  
  Current repo truth:
  - Vercel / Render / Supabase are not wired in this repo as active deployment config
  - they remain roadmap assumptions, not implemented stack

### 2.3 Removed / Not Actually Present

- No active `orjson` usage
- No active `aiofiles` usage
- No SQLAlchemy layer
- No Redis / Celery / worker queue
- No Docker stack
- No `.github/workflows` CI pipeline currently present
- No active Supabase integration
- No active Firebase integration
- No direct WorldFirst integration

---

## 3. Monorepo and Repo Tooling Truth

### 3.1 Current Repo Shape

```text
404NotFounders/
  apps/
    api/
    web/
  data/
    raw/
    reference/
    snapshots/
    tmp/
  tests/
  scripts/
  Makefile
  pyproject.toml
```

### 3.2 Monorepo Strategy Actually in Use

The repo is a real monorepo, but not a deeply unified workspace system. It currently uses:

- Python packaging via `pyproject.toml`
- frontend dependency management in `apps/web/package.json`
- root `Makefile` for common dev/test tasks

### 3.3 Package Manager and Runtime Tooling Truth

- **Frontend package manager:** `pnpm`
- **Frontend app scripts:** `next dev`, `next build`, `next start`
- **Backend runtime:** `uvicorn`
- **Python environment style in Makefile:** local `.venv`
- **Python project declaration:** `setuptools` build backend via `pyproject.toml`

Important current truth:

- the old doc said `uv` is the Python project manager
- this repo does have a `pyproject.toml`, but the checked-in workflow uses `.venv` activation and `uvicorn`
- `uv` is not the enforced runtime workflow in the repo itself

---

## 4. Frontend Stack Reality

### 4.1 Framework and Language

- **Framework:** Next.js `16.2.4`
- **React:** `19.2.4`
- **Language:** TypeScript
- **Routing style:** App Router

This is confirmed by `apps/web/package.json`, `next.config.ts`, and the `src/app/` layout.

### 4.2 Styling and UI System

- **Styling:** Tailwind CSS `4.x`
- **PostCSS integration:** `@tailwindcss/postcss`
- **Class utility:** `tailwind-merge`
- **UI primitives:** `@base-ui/react`
- **Local UI wrapper components:** `apps/web/src/components/ui/*`

Important current truth:

- the repo has a `components.json` using shadcn schema format
- but the actual UI primitive dependency is `@base-ui/react`, not Radix plus stock shadcn packages
- the correct description is: **custom local design system with shadcn-style project structure, built mainly on Base UI primitives**

### 4.3 Frontend Data Fetching and State

- **Server state:** `@tanstack/react-query`
- **UI state:** local React state
- **No Redux**
- **No Zustand**

`QueryProvider.tsx` confirms React Query is actively mounted and used.

### 4.4 Form Stack

- **Forms:** `react-hook-form`
- **Validation:** `zod`
- **Resolver bridge:** `@hookform/resolvers`

These are real dependencies and are used in the quote review/repair flow.

### 4.5 Charting and PDF

- **Charts:** `recharts`
- **PDF generation:** `@react-pdf/renderer`

Current implemented uses:

- landed-cost fan chart rendering
- downloadable bank-instruction PDF generation

### 4.6 Motion and Interaction

- **Animation package:** `motion`

The earlier blueprint named Framer Motion directly. Current package truth is:

- `motion` is the declared dependency
- its lockfile resolves through the Framer ecosystem under the hood
- the clean implementation-facing description is simply `motion`

### 4.7 Streaming and Browser Consumption

- **Streaming style:** browser `EventSource`
- **Transport:** SSE from FastAPI

This is used in the analysis progress / streamed analyst explanation flow.

---

## 5. Backend Stack Reality

### 5.1 Runtime and Framework

- **Language target in repo metadata:** Python `>=3.12`
- **Framework:** FastAPI
- **ASGI server:** Uvicorn
- **Schema validation:** Pydantic v2
- **Settings helper:** `pydantic-settings`

Important current truth:

- older design discussions referenced Python 3.11
- the checked-in `pyproject.toml` now says `requires-python = ">=3.12"`
- the tech stack doc should follow the checked-in repo declaration

### 5.2 Core Backend Dependencies Actually Declared

From `pyproject.toml`, the backend currently declares:

- `fastapi`
- `beautifulsoup4`
- `holidays`
- `httpx`
- `lxml`
- `pandas`
- `pydantic`
- `PyMuPDF`
- `python-multipart`
- `tenacity`
- `uvicorn`

Optional ingestion dependencies:

- `gnews`
- `langchain-openai`
- `langfuse`
- `yfinance`
- `trafilatura`

### 5.3 Backend Libraries Actively Reflected in Code

- **HTTP client:** `httpx`
- **Retry behavior:** `tenacity`
- **Time series/dataframe handling:** `pandas`
- **Numerical simulation:** `numpy`
- **PDF rendering fallback:** `PyMuPDF`
- **Multipart upload parsing:** `python-multipart`
- **HTML parsing fallback:** `BeautifulSoup` / `lxml`
- **Table/text extraction for SunSirs:** `trafilatura`

### 5.4 What the Old Tech Doc Overstated

The earlier blueprint listed some backend technologies that are not part of the present code truth:

- `orjson` is not a declared dependency
- `aiofiles` is not a declared dependency
- there is no SQLAlchemy persistence layer
- there is no queue worker framework

---

## 6. AI and LLM Stack Reality

### 6.1 Current AI Provider Pattern

The backend uses a **single provider wrapper**:

- `apps/api/app/providers/llm_provider.py`

That wrapper is the real integration boundary for:

- quote extraction
- recommendation reasoning
- streamed analyst output
- Langfuse callback wiring

This part of the original stack blueprint remains correct in principle.

### 6.2 LangChain / LangGraph Truth

Current repo truth:

- `langchain_core.messages` is used directly
- `langgraph` is used in `ai_orchestrator_service.py`
- the orchestration graph is thin and bounded

So the right grounded statement is:

- **AI orchestration uses a small LangGraph flow where installed**
- **deterministic business logic still lives in backend services, not inside the graph**

### 6.3 Langfuse Truth

Langfuse is currently integrated for:

- quote extraction traces
- recommendation traces
- streamed analyst explanation traces
- simulation span tracing in `fx_simulation_service.py`
- health/status visibility via `/health/langfuse`

This is a real implemented stack component, not just a planned observability add-on.

---

## 7. Data, Storage, and Persistence Truth

### 7.1 Current Real Persistence Layers

#### Local file-backed stores

- **Reference data:** `data/reference`
- **Snapshots:** `data/snapshots`
- **Raw artifacts:** `data/raw`
- **Temporary files:** `data/tmp`
- **Uploaded PDFs:** `apps/api/uploads` or configured upload path

#### In-memory state

- quote states
- analysis run contexts
- analysis results
- Monte Carlo replay inputs

### 7.2 SQLite Truth

`core/config.py` still contains:

- `SQLITE_PATH`

But current runtime truth is:

- SQLite is not the authoritative live state store for quote and analysis workflows
- in-memory dictionaries and file-backed JSON currently hold the active runtime truth

So the tech stack should describe SQLite as:

- **configured legacy/optional setting still present**
- **not the main active persistence backbone today**

### 7.3 Hosted Persistence Truth

The earlier tech blueprint presented Supabase/Postgres/Storage as a chosen hosted stack.

Current repo truth:

- there is no active Supabase client integration
- there is no Postgres runtime wiring
- there is no hosted storage adapter checked in

So these must be described as **roadmap options only**, not implemented stack.

---

## 8. External Data Source Stack Reality

### 8.1 FX and Oil

- **Provider:** `yfinance_provider.py`
- **Library:** `yfinance`
- **Storage target:** local normalized snapshot JSON

Used for:

- FX history snapshots such as `fx/USDMYR`, `fx/CNYMYR`, `fx/THBMYR`
- Brent crude snapshot `energy/BZ=F`

### 8.2 Weather

- **Provider:** `openweather_provider.py`
- **API style:** OpenWeather forecast fetch using configured API key
- **Current storage:** weather snapshot JSON

### 8.3 Holidays

- **Library:** `holidays`
- **Mode:** local deterministic calendar generation
- **Current storage:** holiday snapshots

### 8.4 Macro

- **Provider:** `opendosm_provider.py`
- **Source family:** OpenDOSM / data.gov.my datasets
- **Current storage:** macro snapshots

### 8.5 News

- **Provider:** `gnews_provider.py`
- **Modes supported:** API mode if key exists, RSS/library mode otherwise
- **Current storage:** news snapshots

Important truth:

- GNews is not a fake placeholder
- the provider explicitly supports both `gnews_api` and `gnews_rss` modes

### 8.6 PP Resin

- **Provider:** `sunsirs_provider.py`
- **Scraping/parser support:** `trafilatura` + BeautifulSoup fallback
- **Raw evidence retention:** yes, under `data/raw`
- **Current storage:** resin snapshots

Important truth:

- PP resin is implemented as a benchmark ingestion path
- it is not part of the current Monte Carlo stochastic inputs

---

## 9. Backend Service Stack Reality

### 9.1 Core Active Service Families

Current backend service layers include:

- quote ingestion and repair
- validation
- reference loading
- FX market data service
- energy service
- weather service
- holiday service
- macro data service
- news event service
- resin benchmark service
- analysis run service
- AI orchestration service
- recommendation assembler service
- FX simulation service

### 9.2 Simulation Stack

Current implemented simulation layers include:

- legacy `fx_service.py`
- current `fx_simulation_service.py`
- older `landed_cost_monte_carlo_service.py` still present in the repo

Important current truth:

- the main implemented direction has shifted toward `fx_simulation_service.py`
- this uses NumPy-based FX + Brent simulation with Langfuse span tracing
- the tech doc should not imply only one pristine simulation path exists; there is some stack overlap in the repo

---

## 10. API and Transport Stack Reality

### 10.1 API Style Actually Used

- **Main API style:** REST
- **Streaming transport:** SSE over HTTP

### 10.2 Active Endpoint Groups

Current route files show active groups for:

- health
- quotes
- ingest market
- ingest weather
- ingest macro
- ingest news
- ingest resin
- ingest holidays
- ingest reference
- snapshots
- analysis

### 10.3 Endpoint Truth vs Old Spec

The earlier tech doc listed several endpoints that are not the current route surface, such as:

- `GET /quotes/{id}/extraction`
- `POST /quotes/{id}/validate`
- `POST /comparisons/run`
- `GET /ingest/status/{job_id}`

The actual stack today uses:

- `/analysis/run`
- `/analysis/{run_id}`
- `/analysis/{run_id}/stream`
- `/analysis/{run_id}/traceability`
- `/analysis/{run_id}/hedge-simulate`
- `/analysis/{run_id}/bank-instruction-draft`

So the old comparison-centric API description needed to be removed.

---

## 11. Testing and Developer Workflow Reality

### 11.1 Backend Tests

- **Framework:** `pytest`
- **Async support:** `pytest-asyncio`
- **Test location:** `apps/api/tests`

Confirmed test coverage exists for:

- FX simulation
- market data behavior
- risk driver services
- SunSirs resin

### 11.2 Frontend Tests

- **Unit/component test runner:** `vitest`
- **DOM test environment deps:** `jsdom`, Testing Library
- **E2E dependency present:** `@playwright/test`

Important current truth:

- Playwright is installed as a dependency
- but the repo does not currently show a checked-in browser E2E suite in this pass

### 11.3 Root Makefile

The real checked-in `Makefile` includes:

- `dev-web`
- `dev-api`
- `dev`
- `test-api`
- `test-web`
- `test`
- `lint`
- `ingest-all`

That is the real operational workflow today.

### 11.4 CI Truth

- There is no confirmed `.github/workflows` pipeline in the current repo

So CI should not be documented as if it is already active.

---

## 12. Deployment Stack Truth

### 12.1 Current Local Development Stack

- Next.js dev server
- FastAPI via `uvicorn`
- local file-backed snapshots and raw artifacts
- local upload storage
- local `.env` configuration
- in-memory analysis and quote state

### 12.2 Hosted Stack Truth

The earlier blueprint listed:

- Vercel
- Render
- Supabase

These are still reasonable roadmap options, but they are **not active implementation facts inside this repo**.

The grounded way to describe them is:

- **possible target deployment choices**
- **not current implemented stack**

---

## 13. Environment and Configuration Reality

### 13.1 Two Settings Systems Currently Exist

The repo currently uses both:

- `apps/api/app/core/config.py`
- `apps/api/app/core/settings.py`

This is an important current stack truth because it affects:

- env variable loading
- snapshot path resolution
- Langfuse configuration
- demo-mode path switching

### 13.2 Notable Backend Environment Variables in Active Use

Current code references include:

- `MODEL_API_KEY`
- `MODEL_BASE_URL`
- `MODEL_NAME`
- `OPENWEATHER_API_KEY`
- `GNEWS_API_KEY`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_HOST`
- `LANGFUSE_BASE_URL`
- `LANGFUSE_PROJECT_ID`
- `DATA_DIR`
- `SNAPSHOT_DIR`
- `RAW_ARTIFACT_DIR`
- `REFERENCE_DIR`
- `UPLOAD_DIR`
- `DEMO_MODE`
- `MONTE_CARLO_N`

The old doc's environment section was too generic and mixed active keys with future hosted keys.

---

## 14. Honest Gaps and Stack Risks

These are the real stack-level limitations today.

1. **Python version declaration and local environment may drift**
   - repo declares Python `>=3.12`
   - some local machines may still be running other versions

2. **Two settings systems coexist**
   - this is workable, but messy

3. **SQLite is still configured but not the active truth store**
   - this can confuse future contributors

4. **Hosted deployment stack is not yet codified**
   - docs should not present it as finished

5. **The frontend UI system is custom and hybrid**
   - not pure shadcn/ui
   - not pure Base UI either
   - it is a local wrapper stack

6. **Backend stack still has some overlap from earlier implementations**
   - especially around simulation and evolving services

---

## 15. Final Grounded Stack Summary

LintasNiaga as of 2026-04-25 is best described technically as:

> **A Next.js 16 + React 19 frontend, paired with a FastAPI + Pydantic Python backend, using local JSON snapshots, raw artifact retention, NumPy/Pandas-based analysis, GLM reasoning through a single provider wrapper, and Langfuse-backed traceability.**

The current stack in plain terms is:

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- Base UI backed local component library
- React Query
- React Hook Form
- Zod
- Recharts
- React PDF
- SSE consumption

### Backend

- Python
- FastAPI
- Uvicorn
- Pydantic
- Pydantic Settings
- httpx
- tenacity
- pandas
- numpy
- PyMuPDF
- python-multipart
- BeautifulSoup / lxml
- yfinance
- holidays
- GNews
- trafilatura
- LangChain core
- LangGraph
- Langfuse

### Storage

- local reference JSON
- local normalized snapshots
- local raw artifacts
- local uploaded files
- in-memory analysis and quote state

### Roadmap, Not Current Fact

- Vercel deployment
- Render deployment
- Supabase persistence
- database-backed run state
- queue-based ingestion workers

This version is grounded against the checked-in repo and should be treated as the current technical truth.
