# LintasNiaga — 3-Day Antigravity Build Playbook

> **Deadline:** 26 April 2026, 07:59:59 UTC+8
> **Model:** ilmu-glm-5.1
> **Build tool:** Google Antigravity (Agent-First, Pro tier)
> **Team:** 5 people, all with Antigravity + Google AI Pro
> **Scope lock:** PP Resin HS 3902.10 · FOB only · Port Klang · Up to 5 quotes
> **Source of truth:** PRD v2.1, Architecture v2.1, Tech Stack v2.1 (the 3 MD files in your repo)

---

## How to use this document

This is a BUILD-ONLY playbook. No demo scripting, no pitch writing, no documentation drafting. Just code, test, and fixture prep. Every section tells you **who does what, in which Antigravity surface, with what prompt**. If a step says "Manager Surface" — open Agent Manager and paste the prompt. If it says "Editor" — use the sidebar chat (Cmd+L).

Your 3 MD docs (PRD, Architecture, Tech Stack) are the system-of-record. This playbook does NOT repeat their content. It tells you HOW to build what they describe, in what order, with Antigravity.

---

## BEFORE YOU START — One-Time Setup (all 5 teammates, ~45 min)

### S1. System dependencies

Every machine needs these. If already installed, skip.

```bash
# Python 3.11+ (your tech stack specifies 3.11)
python3 --version  # must show 3.11.x or 3.12.x

# uv (Python package manager — your tech stack choice)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv --version

# Node.js 20+ and pnpm
node --version     # must show 20.x+
npm install -g pnpm
pnpm --version

# Git
git --version

# Poppler (for PDF page rendering if needed by PyMuPDF)
# Mac:
brew install poppler
# Ubuntu/WSL:
sudo apt install poppler-utils
# Windows: download from https://github.com/oschwartz10612/poppler-windows/releases
```

### S2. Clone repo and install

```bash
git clone https://github.com/<your-org>/lintasniaga.git
cd lintasniaga
```

If the monorepo scaffold (`apps/web`, `apps/api`, `data/`) isn't set up yet, create it now:

```bash
mkdir -p apps/web apps/api data/reference data/snapshots/{fx,energy,weather,holidays,opendosm,news,resin} data/raw/{opendosm,news,resin_html,resin_text} data/tmp
```

### S3. Backend Python environment

```bash
cd apps/api
uv venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
uv pip install fastapi==0.115.0 uvicorn[standard] pydantic==2.* pydantic-settings
uv pip install httpx tenacity orjson aiofiles
uv pip install pandas numpy
uv pip install yfinance holidays gnews trafilatura
uv pip install lxml beautifulsoup4
uv pip install langgraph langchain langchain-openai langfuse
uv pip install pytest pytest-asyncio
uv pip install PyMuPDF   # for PDF page rendering
```

### S4. Frontend

```bash
cd apps/web
pnpm create next-app . --ts --tailwind --app --src-dir --import-alias "@/*"
pnpm add recharts motion lucide-react zod react-hook-form @hookform/resolvers
pnpm add @tanstack/react-query
pnpm dlx shadcn@canary init   # pick Zinc, CSS variables yes
pnpm dlx shadcn@canary add button card dialog tabs tooltip badge skeleton slider accordion select input form separator table
```

### S5. Environment variables

Create `apps/api/.env`:

```env
# GLM-5.1
MODEL_API_KEY=<your ilmu key>
MODEL_BASE_URL=https://api.ilmu.ai/v1
MODEL_NAME=ilmu-glm-5.1

# Paths
SQLITE_PATH=./lintasniaga.db
UPLOAD_DIR=./uploads
DATA_DIR=../../data
SNAPSHOT_DIR=../../data/snapshots
RAW_ARTIFACT_DIR=../../data/raw
REFERENCE_DIR=../../data/reference

# Langfuse
LANGFUSE_PUBLIC_KEY=<from cloud.langfuse.com>
LANGFUSE_SECRET_KEY=<from cloud.langfuse.com>
LANGFUSE_HOST=https://cloud.langfuse.com

# OpenWeatherMap
OPENWEATHER_API_KEY=<from openweathermap.org free tier>

# yfinance needs no key

# Snapshot policy
USE_LAST_VALID_SNAPSHOT_ON_FAILURE=true
```

Create `apps/web/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### S6. Verify GLM-5.1 works

```bash
curl https://api.ilmu.ai/v1/chat/completions \
  -H "Authorization: Bearer $MODEL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ilmu-glm-5.1",
    "messages": [{"role": "user", "content": "Say hello in Bahasa Malaysia"}],
    "thinking": {"type": "enabled"},
    "max_tokens": 512
  }'
```

If you get a response with `reasoning_content` — you're good. If the provider gives you a different model string, update `MODEL_NAME` in `.env` and everywhere below. The code is model-string-agnostic — only `.env` changes.

### S7. Antigravity configuration for the ENTIRE team

Every teammate does this in Antigravity after opening the `lintasniaga/` folder:

#### S7.1 Set Agent Mode
Antigravity menu → Settings → Agent Mode → **Agent-Assisted Development** (recommended — you approve terminal commands but agent writes code freely).

Terminal Policy → **Auto** (agent runs standard commands without asking).

#### S7.2 Create project rules

Create `.antigravity/rules.md` in the repo root:

```markdown
# LintasNiaga — Antigravity Project Rules

## Architecture (non-negotiable)
- This is a monorepo: `apps/web` (Next.js) and `apps/api` (FastAPI Python).
- Backend owns ALL business logic. Frontend is thin.
- Deterministic math runs BEFORE AI reasoning. AI is bounded.
- Three backend workflows: Quote Prep, Snapshot Ingestion, Analysis.
- All external data goes through provider adapters → normalized snapshots.
- Analysis NEVER scrapes live. It reads the latest approved snapshot.
- LangGraph stays thin — only wraps AI-heavy steps.

## Tech stack
- Backend: Python 3.11, FastAPI, Pydantic v2, httpx, tenacity, pandas, numpy, yfinance, holidays, gnews, trafilatura
- Frontend: Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui, Recharts, React Hook Form + Zod, TanStack Query
- Persistence: SQLite (dynamic state), local JSON (reference + snapshots)
- AI: ilmu-glm-5.1 via OpenAI-compatible API at https://api.ilmu.ai/v1
- Observability: Langfuse for AI traces, structured logging for app

## Code style
- Python: type hints on all functions, Pydantic models for all schemas, async where possible
- TypeScript: strict mode, no `any`, Zod for API response parsing
- Git: conventional commits (feat:, fix:, docs:, chore:, test:)
- Services never read files directly — go through repositories

## Scope lock (NEVER expand)
- PP Resin HS 3902.10 only
- FOB only
- Port Klang (MYPKG) destination only
- Origins: China (Ningbo/Shenzhen), Thailand (Bangkok), Indonesia (Jakarta)
- Up to 5 quotes per analysis run
- MYR base currency

## Data source rules
- FX + energy: yfinance (wrapped in provider adapter)
- Holidays: holidays Python package (no network)
- Weather: OpenWeatherMap (wrapped in provider adapter)
- Macro: OpenDOSM / data.gov.my
- News: gnews package
- Resin benchmark: trafilatura + LLM extraction from curated sources
- Static anchors: local JSON (freight_rates.json, tariffs_my_hs.json, ports.json)
- All snapshots use the common envelope: {dataset, source, fetched_at, as_of, status, record_count, data}

## What NOT to do
- Do NOT add Supabase, Redis, Celery, Docker, or GraphQL
- Do NOT let the frontend call yfinance or any external API directly
- Do NOT put business logic in Next.js API routes or server actions
- Do NOT use localStorage or sessionStorage
- Do NOT scrape anything inside the analysis request path
- Do NOT expand scope beyond PP Resin / FOB / Port Klang
```

Commit this file. Antigravity reads it automatically on every session.

#### S7.3 Create GEMINI.md (global rules for all Antigravity projects)

Put this in `~/.gemini/GEMINI.md` (personal global config):

```markdown
# Global Antigravity Rules

- Always use Planning mode for complex tasks (more than 3 files)
- Always run tests after code changes
- Commit often with conventional commit messages
- When working on apps/api, always activate the Python venv first
- When creating Pydantic models, use v2 syntax (model_validator, field_validator)
- When creating TypeScript types, mirror the backend Pydantic model exactly
- For all UI components, use shadcn/ui + Tailwind CSS, dark mode by default
```

#### S7.4 Create key workflows

Create `.agent/workflows/` folder in repo root:

**`.agent/workflows/run-backend-tests.md`**
```markdown
---
description: Run all backend tests
---
1. cd apps/api
2. source .venv/bin/activate
3. pytest -v --tb=short
4. Report pass/fail count
```

**`.agent/workflows/run-frontend-build.md`**
```markdown
---
description: Build the frontend and report errors
---
1. cd apps/web
2. pnpm build
3. Report any TypeScript or build errors
```

**`.agent/workflows/create-snapshot-service.md`**
```markdown
---
description: Create a new ingestion service for a dataset
---
1. Read the Architecture v2.1 document for the snapshot ingestion pattern
2. Create a provider adapter in apps/api/app/providers/
3. Create a service in apps/api/app/services/
4. Create a route in apps/api/app/api/routes/
5. Create a schema in apps/api/app/schemas/
6. All snapshots must use the common envelope format from the PRD
7. Write a pytest test
8. Test the endpoint with curl
```

**`.agent/workflows/validate-snapshot-envelope.md`**
```markdown
---
description: Validate that a snapshot file matches the common envelope
---
1. Read the file at the given path
2. Check it has: dataset, source, fetched_at, as_of, status, record_count, data
3. Check data is an array
4. Check each record matches the expected contract for that dataset
5. Report validation result
```

Commit all workflow files.

#### S7.5 Create skills (optional but powerful)

Create `.agent/skills/langgraph-integration/SKILL.md`:

```markdown
---
name: langgraph-integration
description: Use when building or modifying the LangGraph AI orchestration layer. Covers GLM-5.1 integration, thinking mode, tool calling, Langfuse tracing.
---

## GLM-5.1 Integration Pattern

```python
from langchain_openai import ChatOpenAI
import os

llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME", "ilmu-glm-5.1"),
    openai_api_key=os.getenv("MODEL_API_KEY"),
    openai_api_base=os.getenv("MODEL_BASE_URL"),
    temperature=0.3,
    max_tokens=4096,
)
```

## Thinking Mode
GLM-5.1 supports thinking via `extra_body={"thinking": {"type": "enabled"}}`.
The response includes `reasoning_content` separate from `content`.
For streaming: check `chunk.additional_kwargs.get("reasoning_content", "")`.

## Langfuse Tracing
Wrap every LLM call with Langfuse callback:
```python
from langfuse.callback import CallbackHandler
handler = CallbackHandler(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST"),
)
response = llm.invoke(messages, config={"callbacks": [handler]})
```

## LangGraph Rules
- Keep the graph thin — only AI-heavy steps
- Deterministic math stays in FastAPI services, NOT in graph nodes
- Graph nodes: extract_quotes, build_context, reason_recommendation, stream_analyst
- FastAPI services: cost_engine, ranking_engine, hedge_calculator, validation
```

Commit.

### S8. Create reference anchor JSON files

These are the static data files your architecture requires. Create them in `data/reference/`.

**`data/reference/freight_rates.json`**
```json
[
  {"origin_country": "CN", "origin_port": "Ningbo", "destination_port": "MYPKG", "incoterm": "FOB", "currency": "USD", "rate_value": 420.0, "rate_unit": "container", "valid_from": "2026-01-01", "valid_to": "2026-12-31", "source_note": "Flexport Q1 2026 benchmark estimate"},
  {"origin_country": "CN", "origin_port": "Shenzhen", "destination_port": "MYPKG", "incoterm": "FOB", "currency": "USD", "rate_value": 380.0, "rate_unit": "container", "valid_from": "2026-01-01", "valid_to": "2026-12-31", "source_note": "Flexport Q1 2026 benchmark estimate"},
  {"origin_country": "TH", "origin_port": "Bangkok", "destination_port": "MYPKG", "incoterm": "FOB", "currency": "USD", "rate_value": 180.0, "rate_unit": "container", "valid_from": "2026-01-01", "valid_to": "2026-12-31", "source_note": "Freightos Q1 2026 benchmark estimate"},
  {"origin_country": "ID", "origin_port": "Jakarta", "destination_port": "MYPKG", "incoterm": "FOB", "currency": "USD", "rate_value": 210.0, "rate_unit": "container", "valid_from": "2026-01-01", "valid_to": "2026-12-31", "source_note": "Freightos Q1 2026 benchmark estimate"}
]
```

**`data/reference/tariffs_my_hs.json`**
```json
[
  {"hs_code": "3902.10", "product_name": "PP Resin (Polypropylene)", "import_country": "MY", "tariff_rate_pct": 5.0, "tariff_type": "MFN", "source_note": "Malaysia Royal Customs 2026 MFN schedule"},
  {"hs_code": "3901.10", "product_name": "LDPE (Low Density Polyethylene)", "import_country": "MY", "tariff_rate_pct": 5.0, "tariff_type": "MFN", "source_note": "Malaysia Royal Customs 2026 MFN schedule"},
  {"hs_code": "3904.10", "product_name": "PVC (Polyvinyl Chloride)", "import_country": "MY", "tariff_rate_pct": 5.0, "tariff_type": "MFN", "source_note": "Malaysia Royal Customs 2026 MFN schedule"}
]
```

**`data/reference/ports.json`**
```json
[
  {"port_code": "MYPKG", "port_name": "Port Klang", "country_code": "MY", "latitude": 3.0, "longitude": 101.4, "is_destination_hub": true},
  {"port_code": "CNNGB", "port_name": "Ningbo", "country_code": "CN", "latitude": 29.87, "longitude": 121.55, "is_destination_hub": false},
  {"port_code": "CNSZX", "port_name": "Shenzhen (Yantian)", "country_code": "CN", "latitude": 22.57, "longitude": 114.27, "is_destination_hub": false},
  {"port_code": "THBKK", "port_name": "Laem Chabang (Bangkok)", "country_code": "TH", "latitude": 13.08, "longitude": 100.88, "is_destination_hub": false},
  {"port_code": "IDJKT", "port_name": "Tanjung Priok (Jakarta)", "country_code": "ID", "latitude": -6.1, "longitude": 106.88, "is_destination_hub": false}
]
```

**`data/reference/supplier_seeds.json`**
```json
[
  {"supplier_name": "Ningbo Precision Plastics Co. Ltd.", "country_code": "CN", "port": "Ningbo", "reliability_score": 0.82, "typical_lead_days": 35, "notes": "Tier-2 general purpose PP supplier"},
  {"supplier_name": "Sinopec Trading (Shenzhen)", "country_code": "CN", "port": "Shenzhen", "reliability_score": 0.91, "typical_lead_days": 30, "notes": "Major petrochemical group subsidiary"},
  {"supplier_name": "Thai Polyethylene Co. Ltd.", "country_code": "TH", "port": "Bangkok", "reliability_score": 0.88, "typical_lead_days": 18, "notes": "Regional ASEAN PP supplier"},
  {"supplier_name": "PT Chandra Asri Petrochemical", "country_code": "ID", "port": "Jakarta", "reliability_score": 0.75, "typical_lead_days": 22, "notes": "Indonesian petrochemical manufacturer"},
  {"supplier_name": "Zhejiang Borealis New Materials", "country_code": "CN", "port": "Ningbo", "reliability_score": 0.79, "typical_lead_days": 40, "notes": "Smaller PP resin specialist"}
]
```

Commit all reference files.

### S9. Generate mock supplier quote PDFs with Nano Banana Pro

Go to https://gemini.google.com → use Gemini 2.5 Pro or 3 Pro. Generate 5 quote images (we'll save as PDFs later or use as test fixtures directly).

**Prompt for Quote 1 (paste into Gemini):**
```
Generate a realistic scanned business document image of a supplier quotation. It should look like a real PDF printout, slightly off-white paper, monochrome with navy blue accents.

Letterhead: "Ningbo Precision Plastics Co. Ltd." with a small circular logo placeholder, address "No. 88 Beilun Industrial Zone, Ningbo, Zhejiang 315800, China", phone and email.

Quotation number: NPP-Q-2026-0412
Date: April 15, 2026
To: "Teknologi Rapid Sdn Bhd, No. 12 Jalan Perindustrian, 42100 Klang, Selangor, Malaysia"

Items table with columns: Item | Description | Qty (MT) | Unit Price | Currency | Amount
Row 1: 1 | Polypropylene Resin (PP Homopolymer, MFR 12g/10min) HS 3902.10 | 100 MT | USD 1,180 /MT | USD | USD 118,000

Terms:
- Incoterm: FOB Ningbo
- Payment: T/T 30 days after B/L date
- MOQ: 80 MT
- Lead time: 35 days from order confirmation
- Validity: 30 days from quotation date
- Packing: 25kg bags, palletized

Signature block with "Sales Manager" and a scribble signature.

Make it look like a scanned document, not digitally perfect. Slight paper texture.
```

**Repeat for Quotes 2-5 with these variations:**

Quote 2 — Sinopec Trading (Shenzhen): USD 1,145/MT, FOB Shenzhen, MOQ 120 MT, lead 30 days, T/T 60 days
Quote 3 — Thai Polyethylene (Bangkok): USD 1,210/MT, FOB Bangkok, MOQ 50 MT, lead 18 days, T/T 30 days
Quote 4 — PT Chandra Asri (Jakarta): USD 1,095/MT, FOB Jakarta, MOQ 100 MT, lead 22 days, T/T 45 days (this is the "cheap but risky" one)
Quote 5 — Zhejiang Borealis (Ningbo): CNY 8,350/MT, FOB Ningbo, MOQ 60 MT, lead 40 days, T/T 30 days (this is the CNY-denominated one)

Save each image. Convert to PDF:
- Mac: open in Preview → File → Export as PDF
- Or use any "image to PDF" converter online
- Save to `tests/fixtures/supplier-quotes/quote_1_ningbo.pdf` through `quote_5_zhejiang.pdf`

Also save the structured extracted data you expect from each quote as JSON files in `tests/fixtures/expected-extractions/` — Claude Code or Antigravity can generate these for you.

Commit all fixtures.

### S10. Setup gate checkpoint

Before starting Day 1, confirm ALL of these:
- [ ] `cd apps/api && source .venv/bin/activate && python -c "import fastapi; print('ok')"` works
- [ ] `cd apps/web && pnpm dev` shows Next.js default page at localhost:3000
- [ ] GLM-5.1 curl test returns a response
- [ ] All reference JSON files exist in `data/reference/`
- [ ] 5 mock quote PDFs exist in `tests/fixtures/`
- [ ] `.antigravity/rules.md` is committed
- [ ] `.agent/workflows/` has at least 2 workflows
- [ ] Every teammate can open the repo in Antigravity and see rules loaded

**If any box is unchecked, fix it before starting Day 1.**

---

## DAY 1 — Backend Core (Ingestion + Quote Prep + Cost Engine)

### Team assignment for Day 1

| Person | Role | Focus | Antigravity surface |
|--------|------|-------|---------------------|
| P1 (AI Eng) | Backend ingestion | Provider adapters + snapshot services for FX, energy, holidays | Manager (2 parallel agents) |
| P2 (Data Eng) | Backend core | Reference repo + snapshot repo + SQLite models + config | Editor |
| P3 (Full-Stack A) | Backend quote prep | Quote upload + extraction + validation pipeline | Manager (1 agent) |
| P4 (Full-Stack B) | Frontend scaffold | Landing page + upload UI + dark theme + DESIGN.md | Manager (1 agent) |
| P5 (TL) | Coordination | Reference data QA + fixture validation + integration testing | Editor |

### 1A. P2 — Foundation layer (Editor, morning)

Open Antigravity Editor (Cmd+L). Use **Planning mode**.

**Prompt 1A-1: Core infrastructure**
```
I'm building the FastAPI backend for LintasNiaga in apps/api/. Read the .antigravity/rules.md for full context.

Create the following foundation files:

1. apps/api/app/main.py — FastAPI app with CORS (allow localhost:3000), include all route modules, startup event that logs "LintasNiaga API ready"

2. apps/api/app/core/config.py — Pydantic BaseSettings loading from .env: MODEL_API_KEY, MODEL_BASE_URL, MODEL_NAME, SQLITE_PATH, UPLOAD_DIR, DATA_DIR, SNAPSHOT_DIR, RAW_ARTIFACT_DIR, REFERENCE_DIR, LANGFUSE keys, OPENWEATHER_API_KEY, USE_LAST_VALID_SNAPSHOT_ON_FAILURE

3. apps/api/app/core/exceptions.py — typed exception classes matching the Architecture doc: ExtractionFailed, ValidationFailed, UnsupportedScope, ExternalFetchFailed, NormalizationFailed, SnapshotWriteFailed, SnapshotStaleUsingLastValid, NoValidQuotes, SingleValidQuoteFallback, ComputationFailed, AIReasoningFailedFallbackToDeterministic

4. apps/api/app/core/logging.py — structured JSON logger setup using Python logging

5. apps/api/app/repositories/reference_repository.py — loads and validates freight_rates.json, tariffs_my_hs.json, ports.json, supplier_seeds.json from the REFERENCE_DIR. Returns Pydantic models. Raises typed errors if files are missing or malformed.

6. apps/api/app/repositories/snapshot_repository.py — reads/writes snapshot JSON files from SNAPSHOT_DIR. Supports: write_snapshot(dataset, envelope), read_latest(dataset) -> SnapshotEnvelope | None, check_freshness(dataset) -> FreshnessState

7. apps/api/app/repositories/raw_repository.py — writes raw artifacts to RAW_ARTIFACT_DIR for debugging

8. apps/api/app/schemas/common.py — SnapshotEnvelope Pydantic model matching the PRD contract: dataset, source, fetched_at, as_of, status (success|partial|failed), record_count, data (list)

9. apps/api/app/api/routes/health.py — GET /health returning {"status": "ok", "model": MODEL_NAME}

After creating all files, run: cd apps/api && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
Then test: curl http://localhost:8000/health
```

### 1B. P1 — Ingestion provider adapters + services (Manager Surface, morning)

Open Manager Surface. Dispatch 2 agents in parallel:

**Agent 1 prompt (FX + Energy ingestion):**
```
You are building the FX and energy ingestion pipeline for LintasNiaga. Read .antigravity/rules.md for project context.

Create these files in apps/api/:

1. app/providers/yfinance_provider.py
   - async function fetch_fx_history(pair: str, period: str = "1y") -> pd.DataFrame
   - async function fetch_energy_history(symbol: str = "BZ=F", period: str = "1y") -> pd.DataFrame
   - Use yfinance. Wrap in try/except. Return clean DataFrames with columns: date, open, high, low, close
   - Map pair names: "USDMYR" -> "MYR=X", "CNYMYR" -> "CNYMYR=X", "THBMYR" -> "THBMYR=X"
   - Handle yfinance failures with tenacity retry (3 attempts, exponential backoff)

2. app/schemas/market.py
   - FXSnapshotRecord: pair, date, open, high, low, close
   - EnergySnapshotRecord: symbol, series_name, date, open, high, low, close

3. app/services/market_data_service.py
   - async function refresh_fx_snapshot(pair: str) -> SnapshotEnvelope
     - calls yfinance_provider
     - normalizes into FXSnapshotRecord list
     - wraps in SnapshotEnvelope
     - writes via snapshot_repository
     - returns envelope
   - async function refresh_energy_snapshot(symbol: str) -> SnapshotEnvelope
     - same pattern for energy

4. app/api/routes/ingest_market.py
   - POST /ingest/market/fx — body: {pair: str}, calls market_data_service, returns envelope summary
   - POST /ingest/market/energy — body: {symbol: str}, calls market_data_service, returns envelope summary

5. tests/test_market_data.py — pytest tests using cached fixture data (don't hit live yfinance in CI)

After creating all files, test with:
curl -X POST http://localhost:8000/ingest/market/fx -H "Content-Type: application/json" -d '{"pair": "USDMYR"}'
```

**Agent 2 prompt (Holidays + Reference loading):**
```
You are building the holiday ingestion and reference data loading for LintasNiaga. Read .antigravity/rules.md.

Create these files in apps/api/:

1. app/schemas/reference.py
   - FreightRate: origin_country, origin_port, destination_port, incoterm, currency, rate_value, rate_unit, valid_from, valid_to, source_note
   - TariffRule: hs_code, product_name, import_country, tariff_rate_pct, tariff_type, source_note
   - PortMetadata: port_code, port_name, country_code, latitude, longitude, is_destination_hub
   - SupplierSeed: supplier_name, country_code, port, reliability_score, typical_lead_days, notes
   - HolidaySnapshotRecord: country_code, date, holiday_name, is_holiday

2. app/services/reference_data_service.py
   - function load_all_reference_data() -> dict with freight_rates, tariffs, ports, supplier_seeds
   - validates all JSON files through reference_repository
   - returns typed Pydantic model lists

3. app/services/holiday_service.py
   - function refresh_holiday_snapshot(country_codes: list[str] = ["MY","CN","TH","ID"], year: int = 2026) -> SnapshotEnvelope
   - uses the holidays Python package (no network call)
   - generates HolidaySnapshotRecord for each country
   - wraps in SnapshotEnvelope, writes via snapshot_repository

4. app/api/routes/ingest_reference.py
   - POST /ingest/reference/load — calls reference_data_service, returns summary
   
5. app/api/routes/ingest_holidays.py
   - POST /ingest/holidays — calls holiday_service, returns envelope summary

6. tests/test_reference_data.py — test that all reference JSON files load correctly
7. tests/test_holidays.py — test holiday generation for MY, CN

After creating, test:
curl -X POST http://localhost:8000/ingest/reference/load
curl -X POST http://localhost:8000/ingest/holidays
```

### 1C. P3 — Quote upload + extraction pipeline (Manager Surface, afternoon)

**Agent prompt:**
```
You are building the quote upload and AI extraction pipeline for LintasNiaga. Read .antigravity/rules.md.

The user uploads up to 5 supplier quote PDFs. The backend extracts structured fields using GLM-5.1 vision capabilities, then validates them.

Create these files in apps/api/:

1. app/schemas/quote.py — Pydantic models:
   - QuoteUpload: upload_id (uuid), filename, storage_path, uploaded_at, status (pending|extracted|validated|invalid)
   - ExtractedQuote: quote_id (uuid), upload_id, supplier_name, origin_port_or_country, incoterm, unit_price (float), currency, moq (int), lead_time_days (int), payment_terms (str|None), extraction_confidence (float|None)
   - QuoteValidationResult: quote_id, status (valid|invalid_fixable|invalid_out_of_scope), reason_codes (list[str]), missing_fields (list[str])

2. app/providers/llm_provider.py — ONE provider wrapper:
   - Uses ChatOpenAI from langchain_openai with MODEL_API_KEY, MODEL_BASE_URL, MODEL_NAME from config
   - function extract_quote_fields(image_bytes: bytes) -> ExtractedQuote — sends the PDF page image to GLM-5.1 with a structured extraction prompt asking for JSON output with the ExtractedQuote fields
   - function reason_about_recommendation(context: dict) -> str — for later use
   - All calls wrapped with Langfuse callback handler
   - If the key gives you a model without vision, fall back to: render PDF to image with PyMuPDF, base64 encode, send as image_url in the message

3. app/services/quote_ingest_service.py
   - async function process_upload(file: UploadFile) -> QuoteUpload
     - save PDF to UPLOAD_DIR
     - render first 2 pages to images with PyMuPDF
     - call llm_provider.extract_quote_fields for each page
     - merge extracted fields
     - return QuoteUpload with extracted data

4. app/services/quote_validation_service.py
   - function validate_quote(quote: ExtractedQuote) -> QuoteValidationResult
     - check: incoterm must be FOB
     - check: currency must be USD, CNY, THB, or IDR
     - check: supplier_name, unit_price, moq, lead_time_days must not be null
     - check: origin must map to supported corridor (CN, TH, ID)
     - return valid, invalid_fixable, or invalid_out_of_scope

5. app/api/routes/quote_upload.py
   - POST /quotes/upload — multipart file upload, calls quote_ingest_service, returns extraction result
   - POST /quotes/{quote_id}/repair — accepts corrected fields, re-validates
   - GET /quotes/{quote_id} — returns current extraction + validation state

6. tests/test_quote_validation.py — test validation rules with mock ExtractedQuote objects (no LLM needed)

Use PyMuPDF (import fitz) to render PDF pages to images. The extraction prompt to GLM should be:
"Extract the following fields from this supplier quotation image as JSON: supplier_name, origin_port_or_country, incoterm, unit_price (numeric), currency (ISO 4217), moq (integer), lead_time_days (integer), payment_terms. Return only valid JSON, no markdown."
```

### 1D. P4 — Frontend scaffold + upload UI (Manager Surface, full day)

**Agent prompt:**
```
You are building the frontend for LintasNiaga in apps/web/. Read .antigravity/rules.md.

Design: dark fintech aesthetic. Background #06060A. Primary accent #0DFFD6 (electric teal). Surface cards #111116 with #1A1A24 border. Text #F0F0F5 primary, #8888A0 secondary. Use Tailwind CSS dark mode.

Build these pages:

1. src/app/page.tsx — Landing page
   - Full dark background
   - Center headline: "Choose the best-value supplier with less hidden risk" in bold 48px
   - Subtext: "LintasNiaga compares FOB PP Resin quotes, simulates FX scenarios, and recommends the best-value supplier for Malaysian importers."
   - One teal CTA button "Start Analysis" linking to /analysis/new
   - Three feature cards below: "Multi-Supplier Comparison", "FX Risk Simulation", "Explainable AI Reasoning"
   - Footer: "UMHackathon 2026 · Domain 2 · Built on ilmu-glm-5.1"

2. src/app/analysis/new/page.tsx — Quote upload wizard (Step 1 only for now)
   - Top stepper: Step 1 "Upload Quotes" (active) → Step 2 "Review" → Step 3 "Analysis" → Step 4 "Decision"
   - Drag-and-drop zone with dashed teal border, cloud-upload icon from lucide-react
   - "Drop up to 5 FOB PP Resin quote PDFs here"
   - On file drop, send each file to POST http://localhost:8000/quotes/upload via multipart fetch
   - Show uploaded file cards with: filename, processing spinner, then extracted supplier name + price when done
   - Below: required quantity input (number), urgency select (Normal / Urgent)
   - "Continue to Review" button, disabled until ≥2 quotes uploaded and quantity entered
   - Use TanStack Query for managing upload state

3. src/app/layout.tsx — Root layout with dark background, Tailwind globals, font imports

4. src/lib/api.ts — API client helper wrapping fetch with NEXT_PUBLIC_API_BASE_URL

5. src/lib/types.ts — TypeScript types mirroring backend schemas: QuoteUpload, ExtractedQuote, QuoteValidationResult, SnapshotEnvelope

Make sure pnpm build passes with zero errors.
```

### 1E. P5 (TL) — Integration testing + fixture validation (Editor, afternoon)

```
# In Editor, test everything end-to-end:

1. Start backend: cd apps/api && uvicorn app.main:app --reload --port 8000
2. Test reference loading: curl -X POST http://localhost:8000/ingest/reference/load
3. Test FX ingestion: curl -X POST http://localhost:8000/ingest/market/fx -d '{"pair":"USDMYR"}' -H "Content-Type: application/json"
4. Test energy: curl -X POST http://localhost:8000/ingest/market/energy -d '{"symbol":"BZ=F"}' -H "Content-Type: application/json"
5. Test holidays: curl -X POST http://localhost:8000/ingest/holidays
6. Test quote upload: curl -X POST http://localhost:8000/quotes/upload -F "file=@tests/fixtures/supplier-quotes/quote_1_ningbo.pdf"
7. Check that snapshot files appear in data/snapshots/fx/, data/snapshots/energy/, data/snapshots/holidays/
8. Check Langfuse dashboard for the quote extraction trace

Report all failures. Fix critical ones before EOD.
```

### Day 1 gate (EOD)

- [ ] `GET /health` returns ok
- [ ] `POST /ingest/reference/load` loads all 4 reference JSONs
- [ ] `POST /ingest/market/fx` writes a valid FX snapshot for USDMYR
- [ ] `POST /ingest/market/energy` writes a valid energy snapshot for Brent
- [ ] `POST /ingest/holidays` writes holiday snapshots for MY, CN, TH, ID
- [ ] `POST /quotes/upload` with a fixture PDF returns extracted fields
- [ ] Quote validation correctly rejects non-FOB and non-supported corridors
- [ ] Frontend landing page renders at localhost:3000
- [ ] Upload page accepts files and shows extracted data
- [ ] `pytest` passes for reference and validation tests
- [ ] All committed to main

---

## DAY 2 — Deterministic Engine + Analysis Pipeline + Results UI

### Team assignment for Day 2

| Person | Focus | Surface |
|--------|-------|---------|
| P1 (AI Eng) | LangGraph orchestration + GLM reasoning + analyst streaming | Manager |
| P2 (Data Eng) | FX simulation (Monte Carlo) + cost engine + ranking engine | Manager |
| P3 (Full-Stack A) | Recommendation assembler + analysis run service + API routes | Editor |
| P4 (Full-Stack B) | Frontend: Review step + Results screen + FX chart + hedge slider | Manager |
| P5 (TL) | Run all 4 FX pair ingestions + remaining ingestion services (weather, Phase 2) + integration test | Editor |

### 2A. P2 — Deterministic engine (Manager, morning)

**Agent prompt:**
```
Read .antigravity/rules.md. Build the deterministic analysis engine for LintasNiaga in apps/api/.

This is the CORE math — no AI involved here.

1. app/services/fx_service.py
   - function simulate_fx_paths(pair: str, horizon_days: int = 90, n_paths: int = 1000) -> FxSimulationResult
   - Load FX snapshot from snapshot_repository for the given pair
   - Calculate daily log returns from historical close prices
   - Fit simple historical volatility (rolling 30-day std of log returns)
   - Run geometric Brownian motion simulation: n_paths paths over horizon_days
   - Return: current_spot, implied_vol, p10/p50/p90 arrays (one value per day), paths array
   - Use numpy for all math
   - Pydantic model FxSimulationResult with: pair, current_spot, implied_vol, p10_envelope (list[float]), p50_envelope (list[float]), p90_envelope (list[float]), horizon_days

2. app/services/cost_engine_service.py
   - function compute_landed_cost(quote: ExtractedQuote, quantity_mt: float, fx_sim: FxSimulationResult, freight: FreightRate, tariff: TariffRule, supplier: SupplierSeed) -> LandedCostResult
   - Calculate:
     a. material_cost = unit_price * quantity_mt (in quote currency)
     b. material_cost_myr_p50 = material_cost * fx_sim.p50 (at delivery day, use lead_time_days as index)
     c. material_cost_myr_p10 = material_cost * fx_sim.p10[lead_time_days]
     d. material_cost_myr_p90 = material_cost * fx_sim.p90[lead_time_days]
     e. freight_cost_myr = freight.rate_value * (quantity_mt / 20) * current USDMYR rate (load from FX snapshot)
     f. tariff_cost_myr = material_cost_myr_p50 * tariff.tariff_rate_pct / 100
     g. moq_penalty = max(0, (quote.moq - quantity_mt) * unit_price * fx_rate) if moq > quantity
     h. supplier_trust_penalty = (1.0 - supplier.reliability_score) * material_cost_myr_p50 * 0.02
     i. total_landed_p50 = material + freight + tariff + moq_penalty + trust_penalty
     j. total_landed_p10 and p90 similarly
   - Return LandedCostResult with all components broken down

3. app/services/recommendation_engine_service.py
   - function rank_quotes(costs: list[LandedCostResult]) -> list[RankedQuote]
   - Primary sort: total_landed_p50 ascending
   - Secondary sort: total_landed_p90 ascending (tiebreaker)
   - Return ranked list with rank number, delta_vs_winner

4. app/schemas/analysis.py — all Pydantic models: FxSimulationResult, LandedCostResult, RankedQuote, RecommendationCard, BackupOption, HedgeScenarioResult

5. tests/test_cost_engine.py — test with hardcoded quote data (no LLM, no network)
6. tests/test_ranking.py — test ranking logic with 3 mock LandedCostResults
```

### 2B. P1 — LangGraph AI layer (Manager, afternoon)

**Agent prompt:**
```
Read .antigravity/rules.md and the langgraph-integration skill.

Build the THIN LangGraph AI reasoning layer. This layer runs AFTER the deterministic engine has produced ranked results.

1. app/services/context_builder_service.py
   - function build_ai_context(ranked_quotes: list[RankedQuote], costs: list[LandedCostResult], fx_sims: dict, macro_snapshot: dict|None, urgency: str, hedge_preference: str) -> str
   - Assembles a structured text context for GLM-5.1 including:
     - ranked results table
     - cost breakdowns per supplier
     - FX volatility summary
     - urgency and hedge preference
     - any available macro/event context
   - Returns a single context string (keep under 8000 tokens)

2. app/services/ai_orchestrator_service.py
   - Uses LangGraph StateGraph with 2 nodes:
     a. reason_recommendation — calls GLM-5.1 with thinking mode, passes context + system prompt asking for: top_3_reasons, timing_advice (lock_now | wait), hedge_ratio (0-100), caveat (optional), backup rationale
     b. stream_analyst — streams GLM-5.1 analyst explanation via SSE
   - System prompt for reasoning:
     "You are LintasNiaga's procurement analyst. You have been given ranked supplier quotes with full cost breakdowns, FX simulation results, and market context. Your job is to:
     1. Confirm or adjust the winner (you may only swap rank #1 and #2, and only for: reliability, downside risk, MOQ lock-up, urgency mismatch, or disruption risk)
     2. Recommend timing: lock_now or wait
     3. Recommend hedge ratio (0-100%)
     4. Give top 3 reasons for your recommendation
     5. Add one caveat only if there is a material risk
     6. Explain why each non-winning supplier was not chosen (one sentence each)
     Respond in JSON format."
   - All GLM calls traced to Langfuse

3. app/services/recommendation_assembler_service.py
   - function assemble(ranked: list[RankedQuote], ai_output: dict, costs: list[LandedCostResult]) -> RecommendationCard
   - Merges deterministic ranking with bounded AI adjustment
   - If AI swaps winner, validates it's only between rank 1 and 2
   - Produces canonical RecommendationCard: recommended_supplier, timing, hedge_pct, reasons, caveat, backup, why_not_others, impact_summary

4. app/services/analysis_run_service.py
   - async function run_analysis(quote_ids: list[str], quantity_mt: float, urgency: str, hedge_preference: str) -> RecommendationCard
   - Full pipeline:
     a. Load valid quotes
     b. Load reference data
     c. Load latest FX snapshots for relevant currencies
     d. Run FX simulation per currency
     e. Compute landed cost per quote
     f. Rank quotes
     g. Build AI context
     h. Run AI reasoning
     i. Assemble recommendation
     j. Persist result
     k. Return RecommendationCard

5. app/api/routes/analysis.py
   - POST /analysis/run — body: {quote_ids, quantity_mt, urgency, hedge_preference}, returns RecommendationCard
   - GET /analysis/{run_id}/stream — SSE stream of analyst explanation

6. app/api/routes/hedge.py
   - POST /analysis/{run_id}/hedge-simulate — body: {hedge_ratio: float}, recalculates with different hedge assumption, returns HedgeScenarioResult
```

### 2C. P4 — Frontend Results screen (Manager, full day)

**Agent prompt:**
```
Read .antigravity/rules.md. Build the Review and Results screens for LintasNiaga in apps/web/.

1. src/app/analysis/new/review/page.tsx — Step 2 Review
   - Show side-by-side supplier cards for each uploaded quote
   - Each card: supplier name, country flag emoji (🇨🇳🇹🇭🇮🇩), currency, unit price, MOQ, lead time, incoterm
   - Fields with low extraction confidence (<0.7) get an amber border and "Please verify" tooltip
   - All fields editable inline
   - Below cards: macro context panel showing latest FX rates (fetch from /snapshots/latest/fx)
   - "Run Analysis" button → POST /analysis/run with quote IDs + quantity + urgency

2. src/app/analysis/[id]/results/page.tsx — Step 4 Results (THE MONEY SCREEN)
   Three-column layout on desktop (stacks on mobile):

   LEFT (45%): FX Fan Chart
   - Use Recharts AreaChart
   - X-axis: day 0 to 90
   - Y-axis: MYR per unit of quote currency
   - Three overlapping Area components with semi-transparent teal fill: p10 (lightest), p50 (medium), p90 (darkest)
   - Use fillOpacity 0.15, 0.25, 0.35 — NOT stackId (they must overlap, not stack)
   - Below: hedge ratio slider (shadcn Slider, 0-100)
   - Display: "At X% hedge: expected landed cost RM Y/MT (p50)"

   CENTER (35%): Supplier Ranking Cards
   - #1 card: glowing teal border (box-shadow: 0 0 20px rgba(13,255,214,0.2)), "RECOMMENDED" badge
   - Shows: supplier name, "RM X/MT landed (p50)", "RM Y saved vs cheapest", timing advice, hedge recommendation
   - Accordion "Cost breakdown" showing: material, freight, tariff, MOQ penalty, trust penalty
   - #2 and #3 cards: dimmer, show delta vs winner
   - "Why not this supplier?" expandable text

   RIGHT (20%): AI Analyst Panel
   - Collapsible accordion "Why This Recommendation"
   - Shows top 3 reasons as numbered cards
   - Shows caveat if present (amber background)
   - Shows backup option
   - "View Langfuse Trace" link (opens trace URL in new tab)
   - Loading: show skeleton while waiting for /analysis/run response

3. src/app/analysis/[id]/results/components/ — separate component files:
   - FxFanChart.tsx
   - HedgeSlider.tsx
   - SupplierCard.tsx
   - ReasoningPanel.tsx
   - CostBreakdown.tsx

4. src/lib/types.ts — add: RecommendationCard, LandedCostResult, FxSimulationResult, RankedQuote, HedgeScenarioResult

Use TanStack Query for fetching analysis results. Dark theme throughout. All colors from CSS variables.
Make sure pnpm build passes.
```

### 2D. P3 + P5 — Wire remaining + run integration (afternoon)

P3 (Editor): Wire the analysis endpoint, make sure POST /analysis/run returns a valid RecommendationCard with real data.

P5 (Editor): Run ALL ingestion endpoints to populate snapshots:
```bash
# Run these in order:
curl -X POST http://localhost:8000/ingest/reference/load
curl -X POST http://localhost:8000/ingest/market/fx -d '{"pair":"USDMYR"}' -H "Content-Type: application/json"
curl -X POST http://localhost:8000/ingest/market/fx -d '{"pair":"CNYMYR"}' -H "Content-Type: application/json"
curl -X POST http://localhost:8000/ingest/market/fx -d '{"pair":"THBMYR"}' -H "Content-Type: application/json"
curl -X POST http://localhost:8000/ingest/market/energy -d '{"symbol":"BZ=F"}' -H "Content-Type: application/json"
curl -X POST http://localhost:8000/ingest/holidays

# Verify snapshots exist:
ls -la data/snapshots/fx/
ls -la data/snapshots/energy/
ls -la data/snapshots/holidays/
```

Then test the full pipeline:
```bash
# Upload 3 quotes
curl -X POST http://localhost:8000/quotes/upload -F "file=@tests/fixtures/supplier-quotes/quote_1_ningbo.pdf"
curl -X POST http://localhost:8000/quotes/upload -F "file=@tests/fixtures/supplier-quotes/quote_2_sinopec.pdf"
curl -X POST http://localhost:8000/quotes/upload -F "file=@tests/fixtures/supplier-quotes/quote_3_thai.pdf"

# Get quote IDs from responses, then:
curl -X POST http://localhost:8000/analysis/run \
  -H "Content-Type: application/json" \
  -d '{"quote_ids": ["<id1>","<id2>","<id3>"], "quantity_mt": 100, "urgency": "normal", "hedge_preference": "balance"}'
```

### Day 2 gate (EOD)

- [ ] FX simulation produces sensible p10/p50/p90 envelopes (check that p10 < p50 < p90 for MYR weakness)
- [ ] Cost engine produces RM-denominated landed costs that make sense (~RM 500k-600k for 100MT)
- [ ] Ranking sorts by p50 landed cost
- [ ] GLM-5.1 reasoning returns JSON with top_3_reasons, timing, hedge_ratio
- [ ] Langfuse shows the reasoning trace with thinking tokens
- [ ] POST /analysis/run returns a full RecommendationCard
- [ ] Frontend Results page renders the fan chart + supplier cards + reasoning panel
- [ ] Hedge slider is functional (at minimum, shows a number change)
- [ ] `pytest` passes for cost engine and ranking tests

---

## DAY 3 — Integration, Testing, Polish, Demo Prep

### Team assignment for Day 3

| Person | Focus | Surface |
|--------|-------|---------|
| P1 | Fix bugs from Day 2 integration + AI output validation | Editor |
| P2 | Hedge recalculation endpoint + remaining tests | Editor |
| P3 | Single-quote fallback mode + error states | Editor |
| P4 | Frontend polish: loading states, error states, mobile responsiveness | Editor |
| P5 | Deploy to Vercel + Render + full end-to-end validation + snapshot freeze | Editor |

### 3A. P2 — Hedge recalculation (morning)

In Editor:
```
Build POST /analysis/{run_id}/hedge-simulate in apps/api/.

When the user drags the hedge slider to X%, recalculate:
- hedged_cost = p50_cost * (hedge_ratio/100) + p50_cost * (1 - hedge_ratio/100) * (p90/p50 adjustment)
- Basically: higher hedge = cost moves toward p50 (more certain), lower hedge = cost stays exposed to p90 downside
- Return HedgeScenarioResult: hedge_ratio, adjusted_p50, adjusted_p90, impact_vs_unhedged

This is pure math, no GLM call needed. Should respond in <100ms.

Frontend: when slider onChange fires (debounced 300ms), call this endpoint and update the displayed cost figures.
```

### 3B. P3 — Single-quote fallback + error states (morning)

In Editor:
```
Implement single-quote fallback mode per the PRD:

1. In analysis_run_service.py: if exactly 1 valid quote, switch to single-quote evaluation mode
   - Do NOT use comparison language
   - Use labels: "Proceed" / "Review carefully" / "Do not recommend"
   - Still compute landed cost and FX simulation
   - Still run GLM reasoning but with a different prompt: "You are evaluating a single supplier quote, not comparing multiple suppliers..."
   - Do not show backup option or comparative savings

2. In the frontend: detect mode=single_quote in the response and render a different card layout
   - No ranking cards, just one evaluation card
   - Show evaluation label prominently

3. Error states:
   - If zero valid quotes: show "No valid quotes — please fix or upload new quotes" with repair links
   - If extraction fails: show "Extraction failed for [filename] — please re-upload or enter manually"
   - If analysis fails: show "Analysis could not complete — please try again" with error details
```

### 3C. P4 — Frontend polish (full day)

In Editor, iterate on:
```
1. Loading states: skeleton components while waiting for API responses (use shadcn Skeleton)
2. Error states: toast notifications for API failures (use shadcn Sonner or simple toast)
3. Empty states: upload zone with clear instructions before any files are dropped
4. The quote review cards: amber pulsing border for low-confidence fields (use CSS animation)
5. Mobile: stack the 3-column Results layout vertically on screens < 1024px
6. Dark mode: make sure ALL components use the dark theme — no white flashes
7. Processing step: show a simple progress indicator while analysis runs (no Lottie needed — just a pulsing teal dot + "Analyzing..." text + elapsed time counter)
```

### 3D. P5 — Deploy + freeze snapshots (afternoon)

**Deploy frontend to Vercel:**
```bash
cd apps/web
pnpm build  # must pass
# Go to vercel.com → Import → select the repo → set root to apps/web
# Add env var: NEXT_PUBLIC_API_BASE_URL = <your Render URL>
```

**Deploy backend to Render:**
```bash
# Create a new Web Service on render.com
# Set root directory: apps/api
# Build command: pip install -r requirements.txt  (generate with: uv pip freeze > requirements.txt)
# Start command: uvicorn app.main:app --host 0.0.0.0 --port 8000
# Add all env vars from apps/api/.env
```

**Freeze snapshots for demo stability:**
```bash
# Run all ingestion endpoints on the deployed backend
# Then COPY the resulting snapshot files into the repo as "frozen" demo data
# This way, even if yfinance or other APIs are down during demo recording, the app works

cp -r data/snapshots/ data/snapshots_frozen/
# In config.py, add a DEMO_MODE flag that reads from snapshots_frozen/ instead of snapshots/
```

### 3E. Testing checklist (all team, EOD)

Run `/run-backend-tests` workflow in Antigravity. Then manually verify:

**Backend tests (pytest):**
- [ ] test_reference_data — all JSON files load and validate
- [ ] test_quote_validation — FOB accepted, CIF rejected, missing fields caught
- [ ] test_cost_engine — known inputs produce expected outputs
- [ ] test_ranking — 3 costs ranked correctly by p50
- [ ] test_holidays — MY and CN holidays generated

**Frontend tests (manual):**
- [ ] Landing page renders correctly
- [ ] Upload page accepts PDFs and shows extracted data
- [ ] Review page shows supplier cards with editable fields
- [ ] Results page shows fan chart + ranking + reasoning
- [ ] Hedge slider updates displayed costs
- [ ] Single-quote mode shows evaluation (not comparison) language
- [ ] Error state shows when uploading a non-PDF file

**Integration tests (curl against deployed URL):**
- [ ] Full happy path: upload 3 quotes → review → run analysis → get recommendation
- [ ] Full error path: upload 1 quote → single-quote fallback
- [ ] Hedge recalculation responds in <500ms

**GLM-5.1 specific:**
- [ ] Langfuse shows reasoning traces with thinking tokens
- [ ] GLM returns valid JSON with top_3_reasons, timing, hedge_ratio
- [ ] If GLM returns malformed JSON, the system falls back to deterministic-only recommendation

### 3F. Prepare demo fixtures (all team, final hour)

Create a `scripts/prepare-demo.sh`:
```bash
#!/bin/bash
# Refresh all snapshots
curl -X POST $API_URL/ingest/reference/load
curl -X POST $API_URL/ingest/market/fx -d '{"pair":"USDMYR"}' -H "Content-Type: application/json"
curl -X POST $API_URL/ingest/market/fx -d '{"pair":"CNYMYR"}' -H "Content-Type: application/json"
curl -X POST $API_URL/ingest/market/fx -d '{"pair":"THBMYR"}' -H "Content-Type: application/json"
curl -X POST $API_URL/ingest/market/energy -d '{"symbol":"BZ=F"}' -H "Content-Type: application/json"
curl -X POST $API_URL/ingest/holidays
echo "All snapshots refreshed. Ready for demo."
```

Ensure the 5 mock quote PDFs are easily accessible for the demo video recording session. Put them in a `demo/quotes/` folder at the repo root with clear names:
- `demo/quotes/01_ningbo_usd1180.pdf`
- `demo/quotes/02_sinopec_usd1145.pdf`
- `demo/quotes/03_thai_usd1210.pdf`
- `demo/quotes/04_chandra_usd1095.pdf`
- `demo/quotes/05_zhejiang_cny8350.pdf`

---

## Antigravity Power Tips for Maximum Speed

### Tip 1: Use Manager Surface for parallelizable tasks
When two agents are working on non-overlapping files (e.g., Agent 1 on `providers/` and Agent 2 on `services/`), dispatch both from Manager. Review artifacts as they complete.

### Tip 2: Use Planning mode for complex tasks
Before any task touching 3+ files, type in Editor chat: "Use Planning mode." The agent will show you an implementation plan before writing code. Approve or adjust before it writes.

### Tip 3: Use @ to include context
In Editor chat: `@apps/api/app/schemas/common.py` to reference a specific file. Or `@data/reference/freight_rates.json` to show the agent the data shape.

### Tip 4: Use / to trigger workflows
Type `/run-backend-tests` or `/run-frontend-build` to trigger your saved workflows.

### Tip 5: Browser subagent for visual testing
After building a page, tell the agent: "Open localhost:3000/analysis/new in the browser and verify the upload zone renders correctly." Antigravity's browser subagent will open Chrome, take a screenshot, and report issues.

### Tip 6: Context handoff between teammates
When one person finishes a feature and the next person needs to continue:
1. Commit and push
2. The next person pulls and opens in Antigravity
3. Antigravity reads `.antigravity/rules.md` automatically — context is preserved
4. The next person can ask: "Read the latest changes in apps/api/app/services/ and summarize what was built"

### Tip 7: Don't fight the agent
If the agent generates something wrong, don't type a long correction. Just say: "That's wrong. The issue is [X]. Fix it." Short, direct corrections work better than long explanations.

### Tip 8: Freeze successful states
After a major milestone works (e.g., full analysis pipeline returns a result), immediately:
```bash
git add -A && git commit -m "feat: working analysis pipeline milestone" && git push
```
You can always revert to this if something breaks later.

---

## Critical Reminders

1. **GLM-5.1 is mandatory for ALL product reasoning.** Using Gemini (Antigravity's default) for product reasoning disqualifies you. Gemini powers Antigravity as your build tool. GLM-5.1 powers your product's LLM calls. These are different things.

2. **The model string matters.** The repo is currently standardized on `ilmu-glm-5.1`. If your provider gives you a different model string, change `MODEL_NAME`. The code reads from `.env` everywhere — one change propagates.

3. **Snapshot freeze before demo.** Always freeze working snapshot data before recording any demo video. Never rely on live API calls during recording.

4. **The deterministic engine IS the product.** The AI reasoning is the explanation layer. If the deterministic math is wrong, no amount of GLM reasoning fixes it. Get the cost engine right on Day 2 morning.

5. **Don't add features.** Your PRD is locked. Your architecture is locked. Build exactly what's specified. Adding a dashboard page or a suppliers network page will cost you a day you don't have.

---

*End of playbook. Build well.*
