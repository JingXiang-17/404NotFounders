# LintasNiaga - Progress Tracker

> Deadline: 26 April 2026, 07:59:59 UTC+8
> Team: 404NotFounders
> Last updated: 2026-04-24 UTC+8
> Purpose: teammate handoff for the current Day 3 build state

---

## Current Status

We are no longer at early Day 3.

Best current label:
- Day 3A: done
- Day 3B: mostly done
- Day 3C: substantial progress, effectively current state
- Day 3D: not done yet

Short version:
- backend analysis pipeline exists
- hedge recalculation endpoint exists
- single-quote mode exists
- frontend now has the intended 4-step flow
- frontend build passes
- backend test suite passes
- deployment, frozen demo mode, and full end-to-end demo validation are still pending

---

## Verified Working State

These were re-verified in the current handoff session:

- `py -m pytest -q apps/api/tests` -> `18 passed`
- `npm.cmd run build` in `apps/web` -> success
- all three FX snapshot folders exist:
  - `data/snapshots/fx/USDMYR`
  - `data/snapshots/fx/CNYMYR`
  - `data/snapshots/fx/THBMYR`
- holiday snapshots exist in `data/snapshots/holidays/`
- fixture PDFs now exist in `tests/fixtures/supplier-quotes/`

Known non-blocking warnings:
- pytest warns about `asyncio_mode` config
- pytest cannot write cache because of the weird `pytest-cache-files-*` permission issue under `apps/api`
- Next.js warns about workspace root detection because there are multiple lockfiles

Those warnings did not block tests or build.

---

## What Is Implemented

### Backend

- ingestion scaffold and snapshot/repository layer
- reference, holidays, FX, and energy ingestion routes/services
- quote upload route and validation flow
- deterministic analysis services:
  - FX simulation
  - cost engine
  - ranking
  - recommendation assembly
- AI orchestration service and analysis run service
- analysis routes:
  - `POST /analysis/run`
  - `GET /analysis/{run_id}`
  - `GET /analysis/{run_id}/stream`
  - `POST /analysis/{run_id}/hedge-simulate`
- snapshot route:
  - `GET /snapshots/latest/fx`

### Frontend

- landing page rewritten to reflect the real workflow instead of placeholder marketing
- upload page styled and connected to `/quotes/upload`
- review page wired to:
  - quote fetch
  - quote repair
  - `/analysis/run`
- real Step 3 analysis progress page added at:
  - `/analysis/[id]`
- results page uses the shared shell and remains connected to:
  - `GET /analysis/{run_id}`
  - `POST /analysis/{run_id}/hedge-simulate`
- single-quote mode is recognized on the results side
- loading and error states were improved substantially

### Fixtures / Data

- quote PDFs exist:
  - `tests/fixtures/supplier-quotes/quote_1_cn_sinopoly.pdf`
  - `tests/fixtures/supplier-quotes/quote_2_th_siamprime.pdf`
  - `tests/fixtures/supplier-quotes/quote_3_id_nusantara.pdf`
- sample copies also exist under `example_pdf/`
- snapshots exist under `data/snapshots/`

---

## Day 3 Mapping

### 3A - Hedge recalculation

Status: done

Notes:
- playbook says separate `hedge.py`
- actual implementation is inside `apps/api/app/api/routes/analysis.py`
- endpoint exists and tests pass

### 3B - Single-quote fallback and error states

Status: mostly done

Done:
- single-quote mode is implemented in backend analysis flow
- results UI handles `mode=single_quote`
- upload/review/results error handling exists

Still worth checking manually:
- true zero-valid-quotes live path in the browser
- true extraction-failure live path in the browser
- final copy/UX for all edge cases

### 3C - Frontend polish

Status: substantial progress, current active stage

Done:
- shared institutional dark shell
- proper 4-step flow
- loading skeletons on results page
- review page error display
- real processing page with SSE hookup and progress UI
- responsive stacked results layout for smaller screens
- dark theme cleanup

Still worth checking manually:
- mobile layout in an actual browser
- upload/review/results polish on real data
- whether to add toast notifications or keep inline error surfaces

### 3D - Deploy and freeze snapshots

Status: not done

Missing:
- Vercel deployment
- Render deployment
- `snapshots_frozen/`
- `DEMO_MODE`
- deployed end-to-end validation
- frozen demo rehearsal

---

## Current Blockers

### 1. Deployment is still pending

We have local build/test confidence, but not deployed confidence.

### 2. Demo freeze mode is still missing

There is no `data/snapshots_frozen/` path and no `DEMO_MODE` read path yet.

### 3. Full manual end-to-end run is still the main risk

The codebase is much further along than the old tracker suggested, but the next teammate should still manually verify:
- upload all 3 fixture PDFs
- confirm quote extraction/repair flow
- run `/analysis/run`
- watch Step 3 progress page
- confirm results page and hedge slider
- confirm single-quote path

### 4. Repo has had a lot of parallel changes

This handoff push is intended to checkpoint the current combined state for the next teammate.

---

## Recommended Next Steps

Do these in order:

1. Start backend locally and sanity-check live routes
2. Start frontend locally and click through the 4-step flow
3. Run the three fixture PDFs through upload and analysis
4. Verify hedge slider behavior against live backend responses
5. Deploy frontend to Vercel
6. Deploy backend to Render
7. Generate and commit `snapshots_frozen/`
8. Add `DEMO_MODE`
9. Re-test the full happy path on deployed URLs

---

## Commands For Next Teammate

### Backend

```powershell
cd apps\api
py -m uvicorn app.main:app --port 8000 --no-access-log
```

### Frontend

```powershell
cd apps\web
npm.cmd run dev
```

### Backend tests

```powershell
py -m pytest -q apps/api/tests
```

### Frontend build

```powershell
cd apps\web
npm.cmd run build
```

### Manual upload test

```powershell
curl.exe -X POST http://localhost:8000/quotes/upload -F "file=@tests/fixtures/supplier-quotes/quote_1_cn_sinopoly.pdf"
curl.exe -X POST http://localhost:8000/quotes/upload -F "file=@tests/fixtures/supplier-quotes/quote_2_th_siamprime.pdf"
curl.exe -X POST http://localhost:8000/quotes/upload -F "file=@tests/fixtures/supplier-quotes/quote_3_id_nusantara.pdf"
```

After upload:
- collect the returned `quote_id`s
- use them in `POST /analysis/run`
- open the frontend flow from `/analysis/new`

---

## Important Notes

- The old status entries in previous versions of this tracker were stale.
- Do not assume "missing `hedge.py` file" means hedge recalculation is missing. It already exists in `analysis.py`.
- The strongest remaining risk is not implementation absence anymore. It is deployment and final live verification.

---

## Handoff Summary

If you only read one section, read this:

- We are around late 3C, not early Day 3.
- Core backend analysis and frontend flow exist.
- Tests are green and frontend build is green.
- The next teammate should focus on 3D:
  - deploy
  - freeze snapshots
  - run the full happy path and fallback path
  - clean up any last demo issues
