# LintasNiaga Tech Stack Blueprint

## Comprehensive Technical Stack & Architecture Guide

**Project:** LintasNiaga  
**Document Type:** Hackathon implementation blueprint  
**Version:** 1.0  
**Purpose:** Translate the agreed PRD into a stable, buildable technical stack and system architecture for hackathon execution.

---

## 1. Technical Strategy Summary

LintasNiaga should be built as a **single monorepo** containing **two primary services**:

1. **Web application** for user interaction, upload flow, comparison UI, charts, and analyst output
2. **API service** for deterministic business logic, AI orchestration, validation, simulation, ranking, and persistence

### Core Architecture Principle

> **Deterministic backend first, agentic wrapper second.**

This means:
- the browser is thin,
- FastAPI is the application backbone,
- LangGraph is only a thin orchestration layer around AI-specific steps,
- and all business-critical rules stay in deterministic backend services.

### What the stack should optimize for

- demo stability
- speed of implementation
- clarity of ownership between frontend and backend
- easy debugging
- explicit schema boundaries
- graceful degradation
- judge-friendly observability

---

## 2. Final Stack Decisions

## 2.1 Frontend

- **Framework:** Next.js (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **UI Components:** shadcn/ui
- **Charts:** Recharts by default
- **Custom chart escape hatch:** D3 only if a single chart needs custom behavior later
- **Forms:** React Hook Form + Zod
- **Client state:** local React state only where needed
- **Server state:** TanStack Query
- **Upload:** multipart file upload from frontend to FastAPI

## 2.2 Backend

- **Language:** Python
- **Framework:** FastAPI
- **AI orchestration:** LangGraph (thin orchestration only)
- **AI provider integration:** one Z.AI provider wrapper module
- **FX integration:** one dedicated BNM client/service with timeout and fallback
- **Static data access:** centralized repository/data-access layer

## 2.3 Persistence

### Local / Hackathon Mode
- **Static reference data:** local JSON files
- **Dynamic runtime/app state:** SQLite
- **Uploaded PDFs:** local disk

### Hosted Mode
- **Database:** Supabase Postgres
- **File storage:** Supabase Storage
- **Backend authority:** still FastAPI only
- **No direct frontend business logic through Supabase**

## 2.4 Observability

- **AI traces:** Langfuse
- **App/system logs:** normal structured logging

## 2.5 Tooling

- **JS package manager:** pnpm
- **Python package/project manager:** uv
- **Backend tests:** pytest
- **Frontend unit tests:** Vitest
- **End-to-end tests:** Playwright
- **CI:** GitHub Actions

## 2.6 Deployment

### Later hosted target
- **Frontend hosting:** Vercel
- **Backend hosting:** Render
- **Database/storage:** Supabase

---

## 3. Repo Strategy

## 3.1 Monorepo Shape

Use **one monorepo** with two clear apps.

```text
lintasniaga/
  apps/
    web/        # Next.js frontend
    api/        # FastAPI backend
  packages/
    docs/       # optional shared docs/contracts
  data/         # static JSON reference data
  scripts/
  .github/
  Makefile
  README.md
```

## 3.2 Why One Repo

A monorepo is the best fit because:
- frontend and backend evolve together
- shared architectural decisions stay visible
- simpler onboarding for a hackathon team
- easier local startup and judge demo prep
- fewer version-sync issues between repos

## 3.3 Why Not Separate Repos

Separate repos increase coordination overhead exactly when the architecture is still changing.

## 3.4 Why Not One Single Next.js App Only

The system has too much deterministic backend logic to hide inside route handlers or server actions:
- Monte Carlo simulation
- validation pipelines
- fallback logic
- ranking engine
- AI orchestration
- hedge recalculation

A proper FastAPI backend is the right boundary.

---

## 4. Frontend Architecture

## 4.1 Web Stack

### Chosen
- Next.js App Router
- TypeScript
- Tailwind CSS
- shadcn/ui

### Why
This stack is fast to build, flexible enough for custom workflow UI, and matches the product shape better than a generic enterprise component library.

It fits:
- upload interactions
- ranked comparison tables
- recommendation cards
- invalid quote repair forms
- analyst panel
- chart surfaces
- slider interactions

## 4.2 Charting

### Chosen
- Recharts by default
- D3 only if one chart later truly requires bespoke interaction

### Why
Charts matter, but charting is not the hardest part of LintasNiaga. Recharts is fast enough for:
- FX fan chart
- recommendation comparison visuals
- risk bands

Do not turn visualization into its own engineering project.

## 4.3 Form Handling

### Chosen
- React Hook Form
- Zod

### Why
The app has several structured forms that need runtime validation:
- extracted quote repair form
- required quantity input
- urgency input
- hedge preference input
- fix-this flow for invalid quotes

Important distinction:
- **AI/backend parses the PDF**
- **RHF + Zod validates the structured extracted data before submit**

## 4.4 State Management

### Chosen
- local React state for UI-only state
- TanStack Query for backend/server state
- no global store by default

### Local React state examples
- open/close panel state
- selected quote row
- active tab
- draft slider position before submit

### TanStack Query examples
- upload/extraction status
- fetched extracted quote data
- comparison results
- recommendation payloads
- hedge what-if recalculation results

### Not chosen by default
- Zustand
- Redux / RTK

Reason: important state in LintasNiaga is mostly **backend truth**, not browser truth.

## 4.5 Upload UX

### Chosen
- native multipart upload via drag-and-drop or file input
- frontend sends PDFs directly to FastAPI

### Why
This keeps FastAPI as the authority from the first moment of ingestion.

### Upload Flow
1. user selects or drags PDF
2. frontend sends multipart request to FastAPI
3. FastAPI stores file locally in hackathon mode
4. FastAPI triggers extraction and validation flow
5. frontend receives or polls for extracted structured result

## 4.6 API Consumption Style

### Chosen
- REST by default
- SSE / HTTP streaming only for the AI Analyst panel
- no WebSockets unless later truly needed

### Why
Most operations are simple request/response actions:
- upload quote
- validate
- compare
- fetch recommendation
- run hedge recalculation

Only the analyst panel benefits from progressive output.

---

## 5. Backend Architecture

## 5.1 Backend Stack

### Chosen
- Python
- FastAPI

### Why
FastAPI should be the real backend backbone because LintasNiaga has many deterministic operations that must be centralized and auditable.

## 5.2 Ownership Rule

### Frontend should NOT own:
- validation truth
- scope enforcement
- landed-cost logic
- penalty logic
- ranking logic
- fallback logic
- AI orchestration logic

### Backend should own:
- quote validation
- corridor/scope enforcement
- JSON/fallback access
- landed-cost computation
- MOQ penalty
- supplier trust penalty
- probabilistic outputs
- ranking engine
- hedge recalculation
- recommendation assembly

## 5.3 FastAPI Internal Structure

### Chosen structure

```text
apps/api/
  app/
    api/        # route handlers
    services/   # deterministic business logic
    ai/         # LangGraph flows, prompt/context builders, provider wrappers
    data/       # BNM client, JSON repositories, fallback loaders
    schemas/    # Pydantic models
    core/       # config, constants, logging, utilities
    main.py
```

### Responsibility split

#### `api/`
Route handlers only.
Keep routes thin.

#### `services/`
Deterministic logic:
- quote comparison
- cost engine
- ranking
- hedge scenario calculation
- validation flow

#### `ai/`
AI-specific flow only:
- quote extraction orchestration
- context assembly
- reasoning call prep
- streaming analyst flow
- bounded recommendation adjustment

#### `data/`
All data access:
- JSON repositories
- BNM client
- fallback client
- SQLite persistence adapter

#### `schemas/`
Pydantic models for:
- request payloads
- responses
- quote records
- validation results
- comparison outputs
- recommendation outputs

#### `core/`
Shared internal infrastructure:
- settings
- environment config
- constants
- logging
- helper utilities

---

## 6. AI Architecture

## 6.1 Orchestration Philosophy

### Chosen
- thin LangGraph orchestration layer around deterministic FastAPI services

### Why
LintasNiaga is not primarily an autonomous agent system. It is a deterministic procurement decision engine with AI-enhanced steps.

So:
- FastAPI remains the system backbone
- LangGraph wraps only the parts where orchestration genuinely helps

## 6.2 What LangGraph Should Own

Only these AI-heavy steps:
- quote extraction flow coordination
- context assembly for GLM
- reasoning / explanation flow
- streaming analyst output
- bounded recommendation-adjustment step

## 6.3 What LangGraph Should NOT Own

Do not move these into the graph unless truly necessary:
- hard validation rules
- static data loading
- freight/tariff access
- Monte Carlo simulation
- core ranking engine
- hedge calculation
- persistence

## 6.4 Z.AI Integration Rule

### Chosen
- one thin provider wrapper module for Z.AI

The rest of the app should never talk to the provider SDK/client directly.

Example provider interface:
- `extract_quote_with_vision()`
- `reason_about_recommendation()`
- `stream_analyst_output()`

This keeps provider-specific logic isolated.

---

## 7. Data Layer

## 7.1 Static Reference Data

Use JSON files as controlled reference inputs.

### Required files
- `freight_rates.json`
- `tariffs_my_hs.json`
- `commodity_baselines.json`
- `macro_calendar.json`
- `suppliers_seed.json`
- `fallback_rates.json`

## 7.2 Dynamic App State

Use SQLite locally for dynamic state.

### Suggested SQLite tables
- `runs`
- `uploaded_quotes`
- `quote_extractions`
- `quote_validations`
- `comparison_results`
- `recommendations`
- `hedge_scenarios` (optional)

## 7.3 JSON vs SQLite Rule

### JSON = static reference data
Examples:
- freight assumptions
- tariffs
- commodity baselines
- macro events
- supplier seed dataset
- fallback FX values

### SQLite = dynamic app state
Examples:
- uploaded quote metadata
- extracted fields
- validation status
- run status
- recommendation outputs

This rule must stay strict.

## 7.4 Centralized Data Access Layer

All data access should go through one repository/data-access boundary.

### Why
This prevents:
- duplicate file-read logic
- inconsistent fallback behavior
- silent schema drift
- future migration pain when moving from JSON to DB/API

### Services should never read files directly.

---

## 8. BNM FX Integration

## 8.1 Chosen Pattern

Use one dedicated **BNM client/service**.

It should own:
- live spot fetch
- historical-rate fetch
- request timeout policy
- fallback to `fallback_rates.json`
- normalized response structure

## 8.2 Why This Matters

BNM access is not a casual helper. It is a critical dependency in the probabilistic landed-cost engine.

Therefore the BNM client should be treated as infrastructure.

## 8.3 Timeout and Fallback Rule

If BNM exceeds the timeout threshold, the backend must automatically fail over to local fallback data without crashing the comparison flow.

---

## 9. Persistence Strategy by Stage

## 9.1 Hackathon / Local Stage

### Database
- SQLite

### File storage
- local disk

### Reference data
- JSON files

### Why
This minimizes infrastructure complexity while preserving a real backend-owned state model.

## 9.2 Hosted Stage

### Chosen
- Supabase for database + storage
- FastAPI remains the only real backend

### Why Supabase later
Supabase becomes useful when the product is hosted because it bundles:
- Postgres
- object storage for PDFs
- optional auth later

## 9.3 Important Hosted Boundary

Do **not** let the frontend bypass FastAPI for business-critical flows.

That means:
- frontend should not directly implement recommendation logic with Supabase
- frontend should not directly own important write patterns into the core business model

FastAPI remains the application boundary.

---

## 10. API Design

## 10.1 API Style

### Chosen
- REST by default
- SSE / HTTP streaming only where truly needed

## 10.2 Suggested Endpoint Groups

### Upload & extraction
- `POST /quotes/upload`
- `GET /quotes/{id}/extraction`
- `POST /quotes/{id}/repair`

### Validation
- `POST /quotes/{id}/validate`

### Comparison
- `POST /comparisons/run`
- `GET /comparisons/{id}`

### Hedge scenario
- `POST /comparisons/{id}/hedge-simulate`

### Analyst output
- `GET /comparisons/{id}/analyst-stream`

## 10.3 Streaming Rule

The AI Analyst panel may use SSE / HTTP streaming.

All other flows should remain standard REST request/response.

---

## 11. Contract Strategy Between Frontend and Backend

## 11.1 Chosen Strategy

- backend: Pydantic models
- frontend: mirrored TypeScript types
- maintain by disciplined convention

## 11.2 Why Not OpenAPI Codegen First

Codegen is useful later, but for hackathon speed it can slow iteration while payloads are still changing.

## 11.3 Suggested Core Schemas

- `ExtractedQuote`
- `QuoteValidationResult`
- `InvalidQuoteReason`
- `ComparisonRequest`
- `ComparisonResult`
- `RecommendationCard`
- `BackupOption`
- `HedgeScenarioResult`
- `AnalystMessage`

## 11.4 Team Rule

Whenever a payload changes:
1. update backend Pydantic model first
2. update frontend TypeScript type immediately
3. update form/parser validation if relevant

---

## 12. Runtime Validation Strategy

## 12.1 Frontend

Use **Zod** for critical input validation and payload parsing.

Use it especially for:
- quote repair form
- required quantity input
- urgency input
- hedge preference input
- parsing critical API responses before rendering

## 12.2 Backend

FastAPI + Pydantic remains the final validation authority.

### Rule
Even if frontend validation passes, backend validation still decides whether the request is valid.

---

## 13. Observability and Logging

## 13.1 AI Observability

### Chosen
- Langfuse for AI traces only

Track:
- prompt/context usage
- tool calls
- streaming reasoning traces
- latency/token usage where relevant

## 13.2 App Logging

### Chosen
- structured app logs only

Track:
- upload failures
- extraction failures
- validation failures
- BNM timeout/fallback events
- static data load issues
- comparison-run errors
- hedge simulation errors

## 13.3 Not Chosen

- heavyweight observability stack
- full tracing stack for the whole system

Reason: too much overhead for hackathon v1.

---

## 14. Tooling and Developer Workflow

## 14.1 JavaScript Tooling

### Chosen
- pnpm

### Why
Fast workspace support and good monorepo ergonomics.

## 14.2 Python Tooling

### Chosen
- uv

### Why
Fast Python dependency/project workflow with less setup friction than a heavier toolchain.

## 14.3 Task Running

### Chosen
- simple root scripts / Makefile

### Why not Turborepo first
This repo is mixed TypeScript + Python. Turborepo is more naturally centered on JS/TS-heavy build graphs. A simple Makefile is cleaner for hackathon speed.

### Suggested root commands
- `make dev-web`
- `make dev-api`
- `make dev`
- `make test-web`
- `make test-api`
- `make lint`

---

## 15. Testing Strategy

## 15.1 Backend

### Chosen
- pytest

### What to test first
- quote validation rules
- corridor/scope enforcement
- MOQ penalty logic
- supplier trust penalty logic
- fallback behavior
- ranking logic
- hedge recalculation

## 15.2 Frontend Unit/Component Tests

### Chosen
- Vitest

### What to test first
- recommendation card rendering
- invalid quote UI states
- fix-this form validation
- hedge slider UI interactions
- comparison table transforms

## 15.3 End-to-End Tests

### Chosen
- Playwright

### Most important E2E paths
1. upload valid quotes → compare → get recommendation
2. upload invalid quote → fix-this flow → revalidate
3. run comparison with 1 valid quote → single-quote fallback mode
4. trigger hedge what-if → update result

---

## 16. PDF Handling Strategy

## 16.1 Core Principle

The AI/backend parses the quote. The frontend does not.

## 16.2 Optional Preprocessing Layer

Use **PyMuPDF** if needed for:
- rendering PDF pages to images
- extracting page previews
- preprocessing PDFs before sending to the extraction model

## 16.3 Important Rule

Do not build a complex PDF parsing subsystem unless the extraction flow clearly needs it.

---

## 17. Deployment Plan

## 17.1 Hackathon / Local Development

Run everything locally:
- Next.js dev server
- FastAPI dev server
- SQLite
- local disk storage
- local JSON reference files

## 17.2 Hosted Deployment Target

### Frontend
- Vercel

### Backend
- Render

### Persistence
- Supabase Postgres + Storage

### Why this split
- Vercel fits Next.js best
- Render is straightforward for FastAPI
- Supabase covers hosted DB + file storage cleanly

---

## 18. Recommended Environment Variables

## Frontend (`apps/web/.env.local`)
- `NEXT_PUBLIC_API_BASE_URL`

## Backend (`apps/api/.env`)
- `ZAI_API_KEY`
- `BNM_BASE_URL`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `SQLITE_PATH`
- `UPLOAD_DIR`
- `DATA_DIR`
- `USE_FALLBACK_FX_ON_TIMEOUT=true`
- `BNM_TIMEOUT_SECONDS`
- `SUPABASE_URL` (hosted later)
- `SUPABASE_SERVICE_ROLE_KEY` (hosted later)
- `SUPABASE_STORAGE_BUCKET` (hosted later)

---

## 19. What Is Explicitly Not Allowed in v1

To prevent stack drift, avoid all of the following unless absolutely necessary.

### Do not add
- microservices
- GraphQL
- Redux / RTK by default
- Zustand by default
- WebSockets by default
- frontend-owned business logic
- direct frontend-to-Supabase critical flows
- multiple AI provider wrappers scattered through the app
- direct file reads inside services
- Celery / Redis / queue stack
- Docker-first complexity if local dev already works
- Turborepo as core repo infrastructure at hackathon stage
- enterprise observability stack

### Why
None of these are the bottleneck right now.
The bottleneck is building a trustworthy recommendation pipeline.

---

## 20. Canonical Runtime Flow

This is the intended technical flow of a happy-path comparison.

1. **Frontend** uploads PDFs to FastAPI
2. **FastAPI** stores PDFs locally
3. **AI orchestration layer** invokes Z.AI Vision extraction
4. **Backend services** validate extracted quote data
5. invalid quotes are flagged for repair
6. user repairs invalid quote data through frontend form
7. repaired data is revalidated in FastAPI
8. comparison request is submitted
9. **BNM client** fetches FX data or falls back to JSON
10. **deterministic services** compute costs, penalties, and probabilistic outputs
11. **ranking engine** generates ranked quotes
12. **AI orchestration** assembles reasoning context and explanation
13. **bounded override step** may adjust winner only between top 2 if rules allow
14. **recommendation payload** is returned to frontend
15. **AI Analyst stream** optionally emits progressive analysis text
16. frontend renders:
    - table
    - recommendation card
    - backup option
    - analyst panel
    - hedge what-if UI

---

## 21. Final Technical Rule Set

These rules should be treated as non-negotiable for implementation.

1. One monorepo, two services.
2. Frontend is thin; backend owns truth.
3. FastAPI is the application backbone.
4. LangGraph must stay thin.
5. REST by default; SSE only for analyst output.
6. JSON = static data, SQLite = dynamic state.
7. Local disk now, Supabase Storage later.
8. Supabase later is database + storage only; FastAPI stays primary backend.
9. One Z.AI provider wrapper only.
10. One BNM client/service only.
11. One centralized data-access layer only.
12. Pydantic is backend schema truth.
13. Frontend uses TypeScript + Zod for critical forms/parsing.
14. React Hook Form powers repair/input forms.
15. TanStack Query is for server state only where useful.
16. Langfuse is only for AI traces; normal app logs handle everything else.
17. Avoid stack bloat unless a concrete bottleneck appears.

---

## 22. Final Recommendation

If the team follows this stack exactly, LintasNiaga will have:
- a clean separation between deterministic logic and AI reasoning,
- a stable demo path,
- an architecture that is easy to explain to judges,
- and a migration path from local hackathon mode to hosted mode without rewriting the system.

The technical design should feel like this:

> **A disciplined procurement decision engine with a modern web shell, a deterministic Python core, and a narrowly-scoped AI reasoning layer.**

