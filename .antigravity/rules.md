# LintasNiaga — Antigravity Project Rules

## Design System
Read DESIGN.md in the repo root for all color tokens, typography, spacing, and component patterns. Apply these to every frontend component. Never hardcode colors — use the CSS variables defined in DESIGN.md.
Read DESIGN.md in the repo root for all color tokens, typography, spacing, and component patterns. Apply these to every frontend component. Never hardcode colors — use the CSS variables defined in DESIGN.md.

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
- Do NOT write or modify ANY web scraping logic (PP resin benchmark, trafilatura, etc.); a teammate owns this and we must avoid merge conflicts.
- Do NOT add Supabase, Redis, Celery, Docker, or GraphQL
- Do NOT let the frontend call yfinance or any external API directly
- Do NOT put business logic in Next.js API routes or server actions
- Do NOT use localStorage or sessionStorage
- Do NOT scrape anything inside the analysis request path
- Do NOT expand scope beyond PP Resin / FOB / Port Klang
