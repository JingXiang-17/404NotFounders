# LintasNiaga Quality Assurance Testing Document

**Project:** LintasNiaga  
**Document Type:** Quality Assurance Testing Document  
**Version:** 1.0 submission draft  
**Grounded Against Code and Test Runs:** 2026-04-25  
**Prepared For:** UMHackathon 2026 Preliminary Round

## 1. QA Objective

This document records the current quality assurance approach, executed checks, known limitations, and remaining manual verification work for LintasNiaga.

The QA objective is to demonstrate that the system is not only implemented, but tested with a clear understanding of:

- what is covered
- what passed
- what is partially covered
- what still requires manual validation

## 2. QA Scope

Current QA scope covers:

- backend unit and service tests
- API route tests
- Monte Carlo simulation behavior checks
- ingestion normalization checks
- PP resin parsing and fallback behavior checks
- quote validation and ranking logic checks
- manual frontend workflow validation requirements

## 3. Test Strategy

The project currently uses a mixed QA strategy:

### Automated Backend Testing

- pytest-based test suite in `apps/api/tests`
- service and route validation using mocked or local test inputs

### Automated Frontend Testing

- frontend test tooling exists via Vitest
- however, there are currently no checked-in application test files

### Manual End-to-End Validation

Manual testing remains important for:

- PDF upload workflow
- analysis progress UX
- final result rendering
- hedge slider behavior
- PDF generation flow
- traceability visibility

## 4. Test Environment

### Backend

- executed with system Python on the local Windows environment
- command used:

```powershell
cd apps/api
python -m pytest -q
```

### Frontend

- test command checked:

```powershell
cd apps/web
pnpm vitest run
```

Result:

- Vitest is installed
- no web test files currently exist, so no frontend automated tests executed

## 5. Executed Automated Test Results

### Backend Result

Executed on 2026-04-25:

- **42 tests passed**
- **0 tests failed**

Observed command output summary:

- `42 passed, 133 warnings in 26.21s`

### Warning Notes

Warnings were mainly framework/runtime deprecation warnings from:

- FastAPI
- Starlette
- multipart parser import behavior

These warnings did not cause test failures, but they should be tracked for future cleanup.

## 6. Current Automated Backend Coverage Areas

The backend test suite currently includes these files:

- `test_analysis_routes.py`
- `test_cost_engine.py`
- `test_fx_service.py`
- `test_fx_simulation.py`
- `test_holidays.py`
- `test_landed_cost_monte_carlo.py`
- `test_market_data.py`
- `test_quote_ingest_service.py`
- `test_quote_validation.py`
- `test_ranking.py`
- `test_reference_data.py`
- `test_risk_driver_services.py`
- `test_sunsirs_resin.py`

### Coverage Themes

The automated backend coverage currently verifies:

- analysis route behavior
- landed-cost and ranking logic
- FX simulation behavior
- holiday data generation
- market data normalization
- quote ingest and validation
- risk-driver service behavior
- SunSirs PP resin parser behavior

## 7. Key QA Findings by Module

## 7.1 Quote Upload and Extraction

Covered by:

- `test_quote_ingest_service.py`
- `test_quote_validation.py`

Current QA confidence:

- moderate to strong on backend logic
- still needs manual frontend workflow validation with real PDFs

## 7.2 Market Data and Simulation

Covered by:

- `test_market_data.py`
- `test_fx_service.py`
- `test_fx_simulation.py`
- `test_landed_cost_monte_carlo.py`

Current QA confidence:

- strong for deterministic numeric behavior and simulation ordering checks

Key simulation expectations already tested:

- percentile ordering
- widened bands for longer exposure
- widened bands for higher volatility
- correct currency path usage for CNY quotes
- typed error behavior on missing snapshots

## 7.3 Risk Driver Services

Covered by:

- `test_risk_driver_services.py`
- `test_holidays.py`
- `test_sunsirs_resin.py`

Current QA confidence:

- moderate to strong for backend snapshot refresh and parser logic

## 7.4 Analysis Routes

Covered by:

- `test_analysis_routes.py`

Current QA confidence:

- moderate for route contract correctness
- still needs manual full-stack verification

## 8. Frontend QA Status

### Current Truth

Frontend QA tooling exists, but there are no checked-in application test files for the actual UI flow.

Observed result:

- `pnpm vitest run` exited because no test files were found

This means:

- frontend automated QA is currently a tooling-ready but not yet populated layer
- current frontend confidence depends mainly on manual testing

## 9. Manual Test Matrix

The following manual tests should be run before final submission/demo.

### M1: Landing to Upload Flow

Steps:

1. Open landing page
2. Start a new analysis
3. Confirm upload page loads

Expected result:

- CTA routes correctly
- upload screen appears
- quantity and urgency controls are visible

### M2: Multi-PDF Upload

Steps:

1. Upload 2 to 5 valid PDF quotes
2. Observe upload status cards

Expected result:

- each file shows status
- successful uploads display extracted supplier info
- invalid uploads show error state

### M3: Review and Repair

Steps:

1. Continue to review page
2. Edit one or more extracted fields
3. Run analysis

Expected result:

- edited values are submitted through repair
- run starts without stale form state

### M4: Analysis Progress

Steps:

1. Trigger analysis
2. Wait on analysis page

Expected result:

- app loads the run page
- streamed or fetched analysis content appears without dead UI states

### M5: Result Page Rendering

Steps:

1. Open completed result page
2. Inspect recommendation card, supplier ranking, chart, and risk sections

Expected result:

- result page renders all expected blocks
- recommended quote is visible
- hedge ratio is visible
- chart is populated

### M6: Hedge Slider Replay

Steps:

1. Change hedge slider value
2. Wait for replay result

Expected result:

- envelopes update smoothly
- chart does not reroll randomly
- displayed hedge ratio and adjusted values update

### M7: Bank Instruction PDF

Steps:

1. Click generate bank instruction
2. Wait for backend draft and frontend PDF render

Expected result:

- PDF downloads successfully
- content includes title, supplier, currency, tenor, and rationale

### M8: Traceability Visibility

Steps:

1. Run an analysis with Langfuse configured
2. Open traceability-related UI or payload surfaces

Expected result:

- trace URL is present when available
- no hardcoded fake trace data is shown

### M9: Single-Quote Mode

Steps:

1. Run analysis with only one valid quote

Expected result:

- product switches honestly to single-quote mode
- no fake comparison language appears

### M10: PP Resin Benchmark Interpretation

Steps:

1. Run analysis with a quote above and below benchmark
2. Review benchmark-related outputs

Expected result:

- quote-vs-benchmark risk label appears
- explanation treats suspiciously low quotes carefully

## 10. Defects and Known Gaps

### Confirmed QA Gaps

1. Frontend automated tests are not yet implemented.
2. Active analysis/run state remains memory-backed.
3. The repo-local API virtual environment does not currently have `pytest` installed, even though the system Python environment does.
4. Some framework deprecation warnings remain unresolved.

### Product Risk Areas That Need Continued Attention

1. Live refresh latency before analysis
2. External provider instability
3. UI regressions in result-page composition
4. End-to-end consistency between backend payloads and frontend rendering

## 11. Pass/Fail Assessment

### Backend Automated QA

- **Status:** Pass
- **Reason:** 42 backend tests passed successfully on 2026-04-25

### Frontend Automated QA

- **Status:** Partial / Not Yet Implemented
- **Reason:** Vitest is configured, but no app test files currently exist

### End-to-End Product QA

- **Status:** Requires manual verification
- **Reason:** upload, review, result rendering, hedge replay, and PDF generation are best confirmed through manual flow testing

## 12. Recommended Next QA Actions

1. Add at least one frontend test for result page rendering.
2. Add one frontend test for hedge slider interaction.
3. Add one smoke test for bank-instruction PDF action.
4. Ensure the project venv includes `pytest` for reproducible local test execution.
5. Run the manual test matrix with real fixture PDFs before final submission recording.

## 13. Conclusion

LintasNiaga currently shows strong backend QA maturity for a hackathon prototype, especially in:

- landed-cost computation
- simulation logic
- quote validation
- ingestion normalization
- PP resin parser behavior

The main QA weakness is frontend automated coverage, which is currently tooling-ready but not yet implemented. As of 2026-04-25, the project is best described as:

- **backend-tested**
- **frontend manually verifiable**
- **submission-ready with explicit QA limitations documented**
