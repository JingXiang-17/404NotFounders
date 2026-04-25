# LintasNiaga Comprehensive PRD
## Implementation-Grounded Product Requirements Document

**Project Name:** LintasNiaga  
**Tagline:** Choose the best-value supplier with less hidden risk  
**Document Type:** Product requirements document for builders, product/design, and judges  
**Previous Version:** 2.1  
**Current Version:** 2.2  
**Last Grounded Against Code:** 2026-04-25  
**Primary Market:** Malaysian plastics SMEs importing PP resin into Malaysia  
**Scope:** Product behavior that is actually implemented now, with roadmap items clearly separated

---

## 1. Executive Summary

LintasNiaga is a procurement decision-support product for Malaysian plastics SMEs comparing imported **PP resin** supplier quotes.

The current implemented product helps a user:

1. upload supplier quote PDFs
2. review and repair extracted quote fields
3. run a procurement analysis against live-refreshed market and risk snapshots
4. receive a recommended supplier, timing stance, and hedge ratio
5. inspect the landed-cost fan chart, risk narrative, and quote-vs-benchmark context
6. generate a bank-instruction PDF draft for hedge execution workflow

The product is not trying to be a generic sourcing platform. It is a **narrow procurement workflow** centered on:

- quote normalization
- landed-cost decision support
- bounded AI explanation
- and traceable market context

---

## 2. Current Product Truth

LintasNiaga today is best described as a **four-stage procurement workflow**:

1. **Landing page**
2. **Upload and request setup**
3. **Review and analysis start**
4. **Analysis progress and final decision result**

The implemented backend is the real decision owner. The frontend currently acts as a guided shell for:

- PDF upload
- extracted-field review
- analysis trigger
- streamed explanation consumption
- decision rendering
- hedge replay
- and PDF draft download

This PRD intentionally reflects **what the repo supports now**, not the broader earlier vision.

---

## 3. What Is New, Changed, and Removed

### 3.1 New Since the Earlier PRD

- Real 30-day landed-cost Monte Carlo now exists using:
  - quote-currency FX history
  - `USDMYR` freight conversion
  - Brent crude history
  - hedge replay using the same seeded shocks
- The result payload now includes:
  - `landed_cost_scenarios`
  - `selected_scenario`
  - `risk_driver_breakdown`
  - `hedge_simulation`
  - `resin_benchmark`
  - `market_price_risks`
  - `resin_price_scenario`
  - `trace_url`
  - `stream_trace_url`
- The product now includes:
  - quote-vs-market PP resin benchmark analysis
  - Langfuse traceability visibility
  - bank-instruction draft generation
  - a disabled WorldFirst roadmap action in the UI direction

### 3.2 Changed From the Earlier PRD

- The earlier PRD centered on a more generic "comparison engine" language.  
  Current product is more concretely an **analysis run** workflow through `/analysis/run`.
- The earlier PRD implied broader fallback tolerance for missing data.  
  Current analysis behavior is stricter:
  - critical datasets are refreshed and validated before analysis
  - some non-critical paths still retain fallback behavior
- The earlier PRD described PP resin partly like a simulation input.  
  Current product behavior is:
  - PP resin is a benchmark/risk-explanation input
  - not a current Monte Carlo price-path driver
- Hedge preference wording has changed in the current UI:
  - `Balanced hedge`
  - `Conservative hedge`
  - `Aggressive hedge`

### 3.3 Removed / No Longer Accurate

- The old PRD's generic "comparison" endpoint framing
- Assumptions that SQLite is the active business-state store
- Assumptions that all snapshot failures gracefully fall back without blocking analysis
- Assumptions that scraping only happens fully offline from user analysis timing

---

## 4. Product Vision

### Headline Promise

**Choose the best-value supplier with less hidden risk.**

### Practical User Promise

Upload real supplier PDFs, convert them into comparable procurement inputs, combine them with current market and logistics context, and receive a clear recommendation on:

- which supplier to choose
- whether to lock now or wait
- how much FX exposure to hedge

### Current Product Character

LintasNiaga is not a pure OCR tool and not a pure dashboard.

It is a **guided procurement decision product** with:

- quote extraction
- validation and repair
- deterministic cost math
- real FX + oil scenario modeling
- benchmark checks
- bounded AI reasoning
- and user-facing narrative explanation

---

## 5. Target User

### Primary User

**Procurement executive or operations-commercial decision maker at a Malaysian plastics SME**

### Company Type

SME importing PP resin for manufacturing, packaging, or plastics conversion.

### Core User Need

This user needs to answer three business questions quickly and defensibly:

1. Which quote is actually best value?
2. Should we commit now or wait?
3. How much FX downside should we hedge?

### What They Are Judged On

- landed cost
- supplier reliability
- timing of order placement
- avoiding bad pricing or hidden quote traps
- protecting margin from currency and market volatility

---

## 6. Product Scope That Is Actually Implemented

### 6.1 Product Category Scope

The system is currently built around **PP resin procurement analysis**.

The surrounding architecture, reference data, resin benchmark logic, and messaging are all aligned to that narrow procurement case.

### 6.2 Quote Scope

The current product flow assumes uploaded supplier PDFs containing these fields:

- supplier name
- origin port or country
- incoterm
- unit price
- currency
- MOQ
- lead time

### 6.3 User Input Scope

The current upload/review flow explicitly captures:

- up to **5** quote PDFs
- required quantity in MT
- urgency:
  - `Normal`
  - `Urgent`
- hedge preference:
  - `Balanced hedge`
  - `Conservative hedge`
  - `Aggressive hedge`

### 6.4 Output Scope

Current results include:

- ranked quotes
- recommended quote
- timing recommendation
- hedge percentage recommendation
- top reasons
- caveat when applicable
- backup option
- fan chart
- risk explanation
- bank-instruction draft flow

---

## 7. Current Page and Workflow Requirements

### 7.1 Landing Page

The landing page must:

- introduce the product clearly
- communicate procurement-focused value
- route the user into the new analysis flow

### 7.2 Upload and Request Setup Page

The current product requires a dedicated upload/setup page where the user can:

- drag or browse PDF files
- upload multiple files
- view per-file upload/extraction state
- input required quantity
- choose urgency
- continue only when at least one quote uploaded successfully and quantity is valid

### 7.3 Review Page

The review page must:

- load uploaded quote states
- show extracted fields in editable form
- highlight low-confidence values
- allow repair before analysis
- allow hedge preference selection
- display lightweight macro/FX context
- trigger `/analysis/run`

### 7.4 Analysis Progress Page

The current app includes an intermediate analysis page where:

- the run is already created
- the app fetches the result payload
- SSE can stream analyst explanation
- the user is transitioned into the final result view

### 7.5 Analysis Result Page

The result page must present:

- recommendation summary
- supplier ranking
- landed-cost fan chart
- hedge slider and replay result
- AI analyst explanation panel
- risk narrative
- PP resin benchmark context
- bank-instruction PDF action
- traceability-aware experience for judge/demo needs

---

## 8. Core User Problem

Procurement teams often compare supplier quotes using:

- manual spreadsheet normalization
- informal exchange-rate assumptions
- weak visibility into freight and tariff effects
- poor timing guidance
- limited ability to explain why one quote is safer than another

This breaks down especially when:

- currencies differ
- market conditions are moving
- a quote looks cheap but is suspicious versus benchmark
- risk changes faster than manual review can keep up

LintasNiaga exists to reduce that decision friction with:

- structured quote normalization
- analysis-ready market snapshots
- explainable landed-cost scenarios
- and bounded AI explanation

---

## 9. Core Decision the Product Optimizes

The current product optimizes a single practical decision object:

1. **Recommended supplier**
2. **Timing: `lock_now` or `wait`**
3. **Recommended hedge percentage**

Every successful analysis run should return:

- one recommendation
- reasons
- one backup option in comparison mode
- a confidence-bearing context for the user to act on

---

## 10. Implemented Input Requirements

### 10.1 Mandatory Inputs

Current analysis requires:

- at least one uploaded quote that extracted successfully
- required quantity in MT
- urgency

### 10.2 Required for Meaningful Comparison

To compare quotes properly, the system depends on:

- two or more valid comparable quotes for comparison mode
- otherwise it must switch honestly into single-quote mode

### 10.3 Optional but Current User-Controlled Input

- hedge preference selected on the review page

### 10.4 Why Quantity Is Mandatory

The current backend uses quantity to compute:

- material cost
- MOQ penalty relevance
- landed cost
- hedge context

Without quantity, the result is not a meaningful procurement decision.

---

## 11. Quote Intake and Repair Requirements

### 11.1 Upload Rules

The current UI enforces:

- PDF-only uploads
- maximum 5 files

### 11.2 Extraction Policy

The implemented extraction policy is:

1. upload the PDF
2. attempt deterministic text extraction first
3. fall back to GLM vision extraction if needed
4. surface extracted fields for user review
5. allow repair before analysis

### 11.3 Repair Policy

Users must be able to correct:

- supplier name
- currency
- unit price
- MOQ
- lead time
- incoterm
- origin

### 11.4 Validation and Inclusion Policy

Current product behavior is:

- valid or repaired quotes proceed to analysis
- invalid or out-of-scope quotes are filtered out
- the workflow should not pretend all uploads are usable

### 11.5 Traceability Requirement

Quote extraction should remain traceable enough to show:

- extraction method
- trace URLs / trace IDs where available

This is part of the judge-facing product requirement now, not just an engineering extra.

---

## 12. Current Data and Evidence Model

### 12.1 Deterministic Core Inputs

The current product depends on these structured inputs for real analysis:

- extracted quote data
- reference freight data
- tariff rules
- supplier reliability seed data
- quantity and urgency

### 12.2 Snapshot Context Inputs

The current analysis refreshes and uses:

- FX snapshots
- Brent energy snapshot
- macro snapshots
- weather snapshot
- holiday snapshot
- GNews snapshot
- resin benchmark snapshot

### 12.3 AI Reasoning Inputs

The model receives bounded context including:

- ranked quote results
- deterministic landed-cost outputs
- selected scenario summaries
- benchmark context
- news context
- macro context
- weather and holiday context
- risk-driver notes

### 12.4 Important Product Truth

The AI is not asked to invent the procurement decision from scratch.  
The product requirement is:

- deterministic engine first
- bounded AI explanation and adjustment second

---

## 13. Current Snapshot and Refresh Requirements

### 13.1 Snapshot Use Rule

The product uses normalized snapshots as the main external-data contract.

### 13.2 Refresh Rule Before Analysis

The current analysis flow refreshes and validates critical context before computing results.

This means the live product requirement is now:

- analysis should not blindly trust stale market context
- analysis may incur upstream refresh latency
- critical datasets must be available and valid

### 13.3 Scheduled Refresh Requirements

Current scheduled product behavior includes:

- hourly GNews refresh
- daily holidays refresh
- daily PP resin refresh

### 13.4 On-Demand Refresh Requirements

Current analysis-run refresh behavior includes:

- FX
- energy
- macro
- weather
- news freshness check
- resin freshness check
- holiday freshness check

---

## 14. Current Analytics and Simulation Requirements

### 14.1 Deterministic Cost Layer

The backend must compute:

- material cost
- freight cost
- tariff cost
- MOQ penalty
- trust/reliability penalty
- total landed cost

### 14.2 Monte Carlo Layer

The current product must generate a 30-day landed-cost fan chart using:

- quote currency FX history
- `USDMYR` for freight conversion
- Brent crude history
- seeded replay for deterministic hedge interaction

### 14.3 Monte Carlo Output Requirements

The result must include:

- p10 envelope
- p50 envelope
- p90 envelope
- risk width
- hedge-adjusted replay result

### 14.4 Current Boundary Rule

The current product requirement is:

- PP resin benchmark informs price fairness analysis
- PP resin is **not** currently a stochastic path inside the Monte Carlo engine

### 14.5 Delay and Risk Inputs

Weather and holidays currently affect the simulation through derived delay inputs, not raw narrative interpretation.

---

## 15. Recommendation Requirements

### 15.1 Recommendation Structure

The final recommendation object must include:

- `recommended_quote_id`
- `timing`
- `hedge_pct`
- `reasons`
- `backup_options`
- `impact_summary`

### 15.2 Current Timing Labels

Current timing labels are:

- `lock_now`
- `wait`

### 15.3 Single-Quote Labels

Current single-quote evaluation labels are:

- `proceed`
- `review_carefully`
- `do_not_recommend`

### 15.4 Recommendation Source of Truth

The product requirement remains:

- deterministic ranking first
- bounded AI reasoning second

### 15.5 Override Guardrail

The AI may only make bounded winner adjustments when the backend orchestration rules allow it. The product must not behave like unconstrained narrative AI.

---

## 16. Current PP Resin Benchmark Product Role

PP resin benchmark is now a real product feature with a narrower role than the earlier PRD implied.

### Current Requirement

The result experience must use resin benchmark data to help answer:

- is the quoted material price below market?
- fair?
- premium?
- high premium?

### Current Product Output

The system should surface:

- latest resin benchmark record
- quote-vs-benchmark pricing delta
- risk label:
  - `below_market`
  - `fair`
  - `premium`
  - `high_premium`

### Important Requirement

If a quote is far below benchmark, the product should not automatically frame it as "good." It should warn about:

- validity risk
- grade/spec mismatch risk
- hidden fee risk
- bait-pricing possibility

---

## 17. Current Risk and Explanation Requirements

### 17.1 Main Explanation Surface

The product should show a concise recommendation summary first.

### 17.2 Deeper Explanation Surface

The result page should provide deeper explanation through:

- AI analyst panel
- risk notes
- scenario context
- traceability-aware context for judges

### 17.3 Explanation Standard

The explanation must connect:

- what happened
- why it matters
- what the user should do next

### 17.4 Timing Advice Standard

If the p50 scenario trends lower and urgency permits, the system may recommend:

- wait
- requote
- stage the order

If downside risk is high or the path trends upward, the system should favor:

- lock now
- higher hedge coverage

---

## 18. Current Hedge Workflow Requirements

### 18.1 Hedge Recommendation

The result must include a default hedge recommendation.

### 18.2 Hedge Replay

The current product supports hedge replay through `/analysis/{run_id}/hedge-simulate`.

### 18.3 Slider Behavior Requirement

The hedge slider must:

- update the scenario using the same seeded shocks
- narrow the FX-exposed portion of the distribution
- avoid random rerolling behavior

### 18.4 Hedge Draft Workflow

The result page must support generation of a bank-instruction draft for hedge workflow demonstration.

---

## 19. Bank Instruction Workflow Requirements

### 19.1 Implemented Product Goal

The product supports a **Generate Bank Instruction** workflow for legacy-bank-style execution storytelling.

### 19.2 Current Behavior

The backend generates a structured draft and the frontend renders/downloads the PDF.

### 19.3 Output Requirements

The draft must contain:

- title
- SME name
- supplier name
- target currency
- amount
- tenor days
- requested strike rate
- hedge ratio
- business justification
- risk rationale

### 19.4 Roadmap Boundary

Direct WorldFirst execution is not a current product requirement. It remains roadmap/demo signaling only.

---

## 20. Comparison Mode Requirements

### 20.1 Trigger

Comparison mode requires at least **2 valid quotes**.

### 20.2 Required Comparison Outputs

The current result experience should show:

- ranked quote list
- recommended quote
- backup option
- quote-level landed-cost outputs
- quote-vs-benchmark context when available

### 20.3 Why-Not Requirements

Non-winning quotes should remain explainable through:

- `why_not_others`
- supplier card comparison context

---

## 21. Single-Quote Mode Requirements

### 21.1 Trigger

If only one valid quote remains, the product must switch into single-quote evaluation mode.

### 21.2 Honesty Rule

The product must not pretend comparison happened when it did not.

### 21.3 Required Outputs

Single-quote mode should still provide:

- evaluation label
- timing
- hedge recommendation
- reasons
- caveat when needed

---

## 22. Traceability and Judge-Proof Requirements

### 22.1 Traceability Is a Product Requirement Now

For hackathon and judge credibility, the product must visibly support traceability, not just internal logging.

### 22.2 Current Traceability Requirements

The product should expose:

- analysis trace URL when available
- streamed explanation trace URL when available
- Langfuse health visibility

### 22.3 Why This Matters

This lets judges verify that:

- AI explanation is actually invoked
- reasoning is tied to live analysis context
- the product is not just rendering hardcoded text

---

## 23. Failure and Degradation Requirements

### 23.1 Quote Failure Handling

If some quotes fail validation:

- valid quotes may still proceed
- invalid quotes should be excluded honestly
- repair path should remain available

### 23.2 No Valid Quotes

If zero usable quotes remain:

- no analysis should run
- the user should remain in repair workflow

### 23.3 Snapshot Failure Handling

The current product is stricter than the older PRD implied.

Product requirement now:

- some non-critical paths may still fall back
- but critical missing/stale market data can block analysis
- the app should fail explainably, not silently invent a result

### 23.4 Demo Reliability Requirement

Where fallback still exists, it must be transparent and bounded, not hidden behind fake certainty.

---

## 24. Current Non-Negotiable Rules

1. Uploads are PDF only.
2. The current upload page supports up to 5 quotes.
3. Quantity is mandatory before analysis.
4. Urgency is mandatory before analysis.
5. Review/repair happens before the analysis run.
6. Comparison mode requires at least 2 valid quotes.
7. Exactly 1 valid quote triggers single-quote evaluation mode.
8. The backend is the source of truth for ranking and recommendation assembly.
9. Critical market context is refreshed and validated before analysis.
10. The result must include recommendation, timing, and hedge output.
11. The fan chart must be scenario-based, not static decoration.
12. PP resin benchmark is benchmark-only in the current implementation.
13. Traceability must remain visible enough for hackathon judging.
14. The app must not fake supplier comparison when only one valid quote exists.
15. The app must not present roadmap-only execution features as already live.

---

## 25. Roadmap, Not Current Product Fact

These remain valid future ideas, but should not be described as current implemented behavior:

- direct WorldFirst execution
- database-backed persistent analysis state
- broader corridor and product support
- generalized procurement across industries
- richer scheduled ingestion for every data source
- fully productionized hosted persistence and deployment stack

---

## 26. Honest Product Gaps

These are current product-level limitations that should remain visible.

1. **Run state is still in memory**
   - server restart loses active analysis context

2. **Some analysis latency depends on live refresh**
   - freshness improved
   - latency can increase

3. **Product scope is still tightly PP-resin-centric**
   - good for demo credibility
   - not a broad sourcing product yet

4. **Simulation stack has evolved quickly**
   - the product is now more credible
   - but still in active refinement

5. **Traceability is strong for AI, less mature for every non-LLM subsystem**
   - improved significantly
   - not yet full-system observability

---

## 27. Current Canonical Demo Flow

### Happy Path

1. User uploads up to 5 quote PDFs.
2. System extracts fields and stores quote state.
3. User reviews and repairs fields.
4. User sets quantity, urgency, and hedge preference.
5. System runs analysis with refreshed market context.
6. System returns recommendation, fan chart, supplier ranking, benchmark context, and explanation.
7. User adjusts hedge slider and sees hedge replay.
8. User generates bank-instruction PDF draft.

### Fallback Path

1. Some quotes fail validation or remain incomplete.
2. Valid quotes still proceed where possible.
3. If only one valid quote remains, the app switches honestly to single-quote mode.
4. If critical market context is unavailable, the analysis should fail transparently rather than pretend certainty.

---

## 28. Final Product Statement

LintasNiaga v2.2 is a narrowly-scoped procurement analysis product for Malaysian PP resin import decisions.

It currently lets a user:

- upload and repair supplier quote PDFs
- normalize quotes into structured procurement inputs
- run a real landed-cost analysis against refreshed market and logistics context
- receive a bounded supplier, timing, and hedge recommendation
- inspect fan-chart risk and quote-vs-benchmark price fairness
- and generate a bank-instruction draft for hedge workflow storytelling

The core product claim remains:

> AI can materially improve SME procurement decisions when quote extraction, deterministic math, live context refresh, bounded reasoning, and traceability are combined into one disciplined workflow.
