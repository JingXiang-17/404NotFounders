# LintasNiaga — Progress Tracker

> **Deadline:** 26 April 2026, 07:59:59 UTC+8  
> **Team:** 404NotFounders  
> **Last updated:** 2026-04-23

---

## Setup (Pre-Day 1)

| # | Task | Status |
|---|------|--------|
| S1 | System deps (Python 3.11, uv, Node 20, pnpm, Git) | ✅ Done |
| S2 | Clone repo + monorepo scaffold (`apps/`, `data/`) | ✅ Done |
| S3 | Backend Python venv + all deps installed | ✅ Done |
| S4 | Frontend Next.js + shadcn/ui + dependencies | ✅ Done |
| S5 | `.env` + `.env.local` created | ✅ Done |
| S6 | GLM-5.1 curl sanity test | ⬜ Not verified |
| S7 | `.antigravity/rules.md` committed | ✅ Done |
| S7 | `.agent/workflows/` (4 workflows) | ✅ Done |
| S7 | `.agent/skills/langgraph-integration/SKILL.md` | ✅ Done |
| S8 | Reference JSON files in `data/reference/` | ✅ Done (`freight_rates`, `tariffs_my_hs`, `ports`, `supplier_seeds`) |
| S9 | Mock supplier quote PDFs in `tests/fixtures/` | ⬜ Not done |
| S10 | Setup gate — all checkboxes green | 🔶 Partial |

---

## Day 1 — Backend Core + Frontend Scaffold

### Backend Foundation (P2 — 1A)

| File | Status |
|------|--------|
| `apps/api/app/main.py` | ✅ Created |
| `apps/api/app/core/config.py` | ✅ Created |
| `apps/api/app/core/exceptions.py` | ✅ Created |
| `apps/api/app/core/logging.py` | ✅ Created |
| `apps/api/app/repositories/reference_repository.py` | ✅ Created |
| `apps/api/app/repositories/snapshot_repository.py` | ✅ Created |
| `apps/api/app/repositories/raw_repository.py` | ✅ Created |
| `apps/api/app/schemas/common.py` | ✅ Created |
| `apps/api/app/api/routes/health.py` | ✅ Created |
| `GET /health` verified | ⬜ Not verified |

### Ingestion — FX + Energy (P1 — 1B Agent 1)

| File | Status |
|------|--------|
| `app/providers/yfinance_provider.py` | ⬜ Not started |
| `app/schemas/market.py` | ⬜ Not started |
| `app/services/market_data_service.py` | ⬜ Not started |
| `app/api/routes/ingest_market.py` | ⬜ Not started |
| `tests/test_market_data.py` | ⬜ Not started |

### Ingestion — Holidays + Reference (P1 — 1B Agent 2)

| File | Status |
|------|--------|
| `app/schemas/reference.py` | ⬜ Not started |
| `app/services/reference_data_service.py` | ⬜ Not started |
| `app/services/holiday_service.py` | ⬜ Not started |
| `app/api/routes/ingest_reference.py` | ⬜ Not started |
| `app/api/routes/ingest_holidays.py` | ⬜ Not started |
| `tests/test_reference_data.py` | ⬜ Not started |
| `tests/test_holidays.py` | ⬜ Not started |

### Quote Upload + Extraction (P3 — 1C)

| File | Status |
|------|--------|
| `app/schemas/quote.py` | ⬜ Not started |
| `app/providers/llm_provider.py` | ⬜ Not started |
| `app/services/quote_ingest_service.py` | ⬜ Not started |
| `app/services/quote_validation_service.py` | ⬜ Not started |
| `app/api/routes/quote_upload.py` | ⬜ Not started |
| `tests/test_quote_validation.py` | ⬜ Not started |

### Frontend Scaffold (P4 — 1D)

| File | Status |
|------|--------|
| `src/app/layout.tsx` | ✅ Created |
| `src/app/page.tsx` (landing) | ✅ Created |
| `src/app/analysis/new/page.tsx` (upload wizard) | ✅ Directory created |
| `src/lib/api.ts` | ✅ Created |
| `src/lib/types.ts` | ✅ Created |
| `pnpm build` passes | ⬜ Not verified |

### Day 1 Gate

| Check | Status |
|-------|--------|
| `GET /health` → ok | ⬜ |
| `POST /ingest/reference/load` loads all 4 JSONs | ⬜ |
| `POST /ingest/market/fx` writes USDMYR snapshot | ⬜ |
| `POST /ingest/market/energy` writes Brent snapshot | ⬜ |
| `POST /ingest/holidays` writes MY/CN/TH/ID snapshots | ⬜ |
| `POST /quotes/upload` with fixture PDF → extracted fields | ⬜ |
| Quote validation rejects non-FOB / unsupported corridors | ⬜ |
| Frontend landing page renders at localhost:3000 | ⬜ |
| Upload page accepts files + shows extracted data | ⬜ |
| `pytest` passes for reference + validation tests | ⬜ |

---

## Day 2 — Deterministic Engine + Analysis Pipeline + Results UI

### Deterministic Engine (P2 — 2A)

| File | Status |
|------|--------|
| `app/services/fx_service.py` (Monte Carlo sim) | ⬜ Not started |
| `app/services/cost_engine_service.py` | ⬜ Not started |
| `app/services/recommendation_engine_service.py` | ⬜ Not started |
| `app/schemas/analysis.py` | ⬜ Not started |
| `tests/test_cost_engine.py` | ⬜ Not started |
| `tests/test_ranking.py` | ⬜ Not started |

### LangGraph AI Layer (P1 — 2B)

| File | Status |
|------|--------|
| `app/services/context_builder_service.py` | ⬜ Not started |
| `app/services/ai_orchestrator_service.py` | ⬜ Not started |
| `app/services/recommendation_assembler_service.py` | ⬜ Not started |
| `app/services/analysis_run_service.py` | ⬜ Not started |
| `app/api/routes/analysis.py` | ⬜ Not started |
| `app/api/routes/hedge.py` | ⬜ Not started |

### Frontend Results UI (P4 — 2D)

| File | Status |
|------|--------|
| Quote review step page | ⬜ Not started |
| Results / recommendation card screen | ⬜ Not started |
| FX scenario fan chart (Recharts) | ⬜ Not started |
| Hedge ratio slider | ⬜ Not started |
| Analyst streaming explanation panel (SSE) | ⬜ Not started |

---

## Day 3 — Polish + Remaining Ingestion + Demo Prep

| Task | Status |
|------|--------|
| Weather ingestion service (OpenWeatherMap) | ⬜ Not started |
| OpenDOSM / news ingestion (Phase 2) | ⬜ Not started |
| Resin benchmark ingestion (trafilatura + LLM) | ⬜ Not started |
| Error handling + fallback UX | ⬜ Not started |
| End-to-end demo run with all 5 fixture quotes | ⬜ Not started |
| Langfuse traces reviewed | ⬜ Not started |
| README updated | ⬜ Not started |
| Final `pnpm build` + `pytest` green | ⬜ Not started |

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Done / file created |
| 🔶 | In progress / partial |
| ⬜ | Not started |
| ❌ | Blocked / broken |
