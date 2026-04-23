# LintasNiaga Comprehensive Hackathon PRD
## Product Requirements Document

**Project Name:** LintasNiaga  
**Tagline:** Choose the best-value supplier with less hidden risk  
**Document Type:** Hackathon PRD for builders and judges  
**Version:** 2.1 (Comprehensive rewrite with locked ingestion contracts)  
**Primary Audience:** Engineering team, product/design team, hackathon judges  
**Primary Domain:** AI for Economic Empowerment & Decision Intelligence  
**Primary Market:** Malaysian plastics SMEs importing PP Resin into Malaysia

---

## 1. Executive Summary

LintasNiaga is an AI-powered procurement decision copilot for Malaysian plastics SMEs importing **Polypropylene (PP) Resin, HS Code 3902.10** into Malaysia.

The product does **not** aim to find the cheapest quote. It aims to help a procurement executive choose the **best-value supplier quote** after adjusting for:

- true landed cost,
- FX downside risk,
- supplier reliability,
- MOQ lock-up,
- lead-time urgency,
- market timing,
- and logistics disruption risk.

The final decision object is intentionally simple:

1. **Choose Supplier X**
2. **Place order now / wait**
3. **Hedge Y%**

LintasNiaga combines:

- **structured quote extraction** from supplier PDFs,
- **probabilistic landed-cost modeling** in MYR,
- **bounded AI reasoning** over procurement, FX, commodity, and logistics context,
- and **plain-language explanations** that justify why one supplier is recommended over others.

The product remains intentionally narrow to maximize demo credibility and implementation reliability during a hackathon.

---

## 2. Problem Statement

Malaysian SMEs importing raw materials often make procurement decisions using fragmented spreadsheets, manual quote review, historical memory, and gut feel.

That process breaks down when multiple hidden costs and risks sit behind a supplier quotation:

- **Currency volatility:** MYR can move significantly between quote receipt and payment date.
- **Commodity-linked shocks:** oil and petrochemical movements affect both material cost and shipping cost.
- **Supplier reliability risk:** a cheaper quote may become more expensive in reality if the supplier is late or unreliable.
- **MOQ lock-up:** a supplier can look attractive on unit price but force dead-stock or working-capital waste.
- **Timing uncertainty:** the right supplier may differ depending on urgency or upcoming market events.
- **Operational disruption:** holidays, port delays, route disruptions, or severe weather can quietly break an apparently good deal.

The result is not just inefficient analysis. It is **avoidable margin loss**.

---

## 3. Why This Problem Matters

This product is designed for a realistic, economically meaningful decision:

> A Malaysian plastics SME procurement executive must decide which supplier quote to take for a PP resin purchase, whether to place the order now or wait, and how much FX risk to hedge.

If this decision is made poorly, the company can lose money through:

- higher-than-expected landed cost,
- bad supplier choice,
- excessive MOQ lock-up,
- worsened FX outcomes,
- operational delay,
- and unnecessary downside exposure.

LintasNiaga exists to reduce those losses through structured comparison and explainable decision support.

---

## 4. Target User

### 4.1 Primary User
**Procurement executive at a Malaysian plastics SME**

### 4.2 Company Type
Malaysian SME importing PP Resin for manufacturing or packaging operations.

### 4.3 Why This User
This user is closest to the actual buying decision.  
They are responsible for comparing quotes, balancing cost against operational constraints, and acting quickly without having a dedicated treasury analyst or supply-chain analyst beside them.

### 4.4 What They Are Judged On
They are judged on:

- keeping input cost under control,
- securing usable and timely material supply,
- avoiding bad supplier choices,
- and protecting margin from avoidable procurement risk.

They get blamed for:

- taking a quote that looked cheap but was bad in reality,
- choosing unreliable suppliers,
- locking too much capital into unnecessary MOQ,
- exposing the company to avoidable FX downside,
- or missing hidden delay risks.

### 4.5 Their Constant Trade-Offs

- cost vs reliability,
- cost vs urgency,
- price vs downside risk,
- MOQ vs working capital,
- speed vs decision quality.

---

## 5. Product Promise

### Headline Promise
**Choose the best-value supplier with less hidden risk.**

### Supporting Promise
Compare FOB PP resin quotes side by side, convert them into true MYR landed-cost scenarios, adjust for hidden penalties and supplier risk, and get a clear supplier, timing, and hedge recommendation.

---

## 6. Core Decision LintasNiaga Optimizes

LintasNiaga is primarily a **supplier selection copilot**.

### Primary Decision
**Which supplier quote should I choose?**

### Secondary Decision
**Should I place the order now or wait?**

### Downstream Risk-Control Decision
**If I proceed, how much should I hedge?**

### Recommendation Structure
Every valid comparison run should aim to produce:

1. **Recommended supplier**
2. **Timing recommendation:** lock now / wait
3. **Recommended hedge ratio**
4. **Top 3 reasons**
5. **Optional caveat** if there is a materially notable risk
6. **Backup option** with a different trade-off profile

---

## 7. Strategic Scope: Beachhead Strategy

LintasNiaga v1 follows a strict beachhead strategy.

The goal is not to support all procurement. The goal is to deliver one believable and high-quality procurement decision workflow.

### 7.1 Product Scope
**Only PP Resin (HS Code 3902.10)**

#### Business Rationale
PP Resin is a meaningful import category for Malaysian manufacturing and packaging. It also creates a strong reasoning bridge to global oil-linked and petrochemical cost movement.

#### Technical Rationale
Narrowing to one HS code lets the system avoid broad customs complexity and use a single fixed tariff assumption.

### 7.2 Geographic Scope
**Only supported imports into Port Klang, Malaysia (MYPKG)**

Supported origin corridors:

- China (e.g. Ningbo / Shenzhen)
- Thailand (Bangkok)
- Indonesia (Jakarta)

#### Rationale
This keeps the corridor logic stable, locks the base currency to MYR, and avoids multi-country mesh complexity.

### 7.3 Commercial Scope
**FOB quotes only**

#### Rationale
The freight model in v1 is based on FOB import assumptions into Port Klang. Supporting EXW/CIF/CFR in v1 would require fragile normalization and would reduce credibility.

---

## 8. Explicit Out of Scope for v1

This section is intentionally explicit to show product discipline.

### 8.1 Most Important Out-of-Scope Boundary
**Any product outside PP Resin (HS Code 3902.10) is out of scope.**

### 8.2 Additional Out-of-Scope Items

- Any non-FOB quote
- Any corridor outside supported origins into Port Klang
- Any destination other than Port Klang / Malaysia hub model
- Autonomous order execution or purchasing
- Broad customs/tariff coverage for many HS codes
- General-purpose procurement for all industries
- ERP/accounting integration
- Domestic trucking / last-mile optimization
- Unlimited quote uploads
- Fine-tuning or training a custom LLM
- Generic macro/news/weather exploration outside procurement relevance
- Unbounded live web scraping inside the analysis request path

---

## 9. User Inputs Before Analysis

### 9.1 Mandatory Inputs
Before comparison begins, the user must provide:

1. **Uploaded supplier quote PDFs** (up to 5)
2. **Required purchase quantity**
3. **Urgency level**
   - Normal
   - Urgent

### 9.2 Optional Inputs

1. **Hedge preference**
   - Protect margin
   - Balance cost and flexibility (**default**)
   - Minimize hedging
2. Optional internal notes or buying constraints (future extension, not required in v1 UI)

### 9.3 Why Required Quantity Is Mandatory
Without required quantity, the product cannot:

- compare total landed cost fairly,
- apply MOQ penalty honestly,
- or produce a real supplier recommendation.

---

## 10. Quote Intake and Validation Rules

### 10.1 Upload Mode
Users can upload **up to 5 quotes at once**.  
LintasNiaga v1 is **multi-quote comparison first**.

### 10.2 Comparison Assumptions
For quotes to be comparable, the system must enforce:

- same material / same HS code,
- same destination hub,
- same buyer-required quantity assumption,
- normalization of supported currencies into MYR,
- supported corridor only,
- FOB only.

### 10.3 Required Fields Per Quote
A quote must contain or be confirmed for at least:

- supplier name,
- origin port or country,
- incoterm = FOB,
- unit price,
- currency,
- MOQ,
- lead time.

### 10.4 Extraction Policy
**AI extraction first, user confirmation required.**

Flow:
1. User uploads PDF quote.
2. AI extraction pulls key fields.
3. The system pre-fills a structured form.
4. User confirms or edits critical fields.
5. Quote is validated before entering comparison.

### 10.5 Missing or Invalid Data Policy
The system must **not guess** missing critical values.

If fields are incomplete or unsupported:
- valid quotes proceed,
- invalid quotes are excluded,
- and the user is shown why they were excluded and how to fix them.

### 10.6 Fix Flow
When the user clicks **Fix this**:
- open an inline edit form,
- prefill extracted fields,
- let the user correct missing or invalid values,
- revalidate the quote,
- re-enter comparison if valid.

---

## 11. Recommendation Evidence Model

### 11.1 Mandatory Core Inputs
These are the core evidence inputs needed for a credible recommendation:

- supplier quoted unit price,
- currency,
- MOQ,
- lead time,
- freight estimate,
- tariff,
- FX volatility / forecast band,
- supplier reliability history,
- required quantity.

### 11.2 Supporting Intelligence Inputs
These are not strictly required to compute the base comparison, but they improve timing and reasoning quality:

- PP resin benchmark,
- Brent crude benchmark,
- market event calendar,
- public holiday calendar,
- route disruption signals,
- fuel/freight surcharge proxy,
- weather-derived shipping risk,
- payment-horizon rules.

### 11.3 Design Principle
LintasNiaga is built around three layers of evidence:

1. **Math-critical inputs**
2. **Reasoning-enhancing inputs**
3. **Curated or generated snapshots**

---

## 12. Updated Data Architecture and Source Policy

LintasNiaga uses a hybrid data architecture designed for demo reliability and fast hackathon execution.

### 12.1 Source Classes

#### Class A — Local Reference Anchors
These are deterministic local JSON files and are **not scraped**.

- `freight_rates.json`
- `tariffs_my_hs.json`
- `ports.json`
- `source_registry.json` (for curated resin scrape sources)

#### Class B — Snapshot Pipelines
These are ingested by backend jobs and normalized into local snapshots before analysis uses them.

- FX snapshots
- energy snapshots
- weather-risk snapshots
- holiday snapshots
- OpenDOSM snapshots
- GNews event snapshots
- PP resin benchmark snapshots

#### Class C — AI Runtime
These are used at runtime for extraction/reasoning only.

- LLM / extraction model
- observability provider

### 12.2 Approved Ingestion Sources for v1

#### Local JSON Anchors
- Freight matrix
- Tariff rules

#### Macro & Energy Pipelines
- FX via `yfinance`
- Brent crude via `yfinance`
- Natural gas via `yfinance` (optional supporting context, not primary decision input)

#### Logistics & Environment Nodes
- OpenWeatherMap API for port-weather risk derivation
- `holidays` Python package for local holiday calculations

#### Agentic Risk Drivers
- OpenDOSM / data.gov.my datasets for Malaysian macro and trade/industrial context
- `gnews` for structured headline/event ingestion

#### Boss Fight
- `trafilatura` for curated PP resin benchmark text extraction from selected market pages
- LLM parsing layer to extract structured USD/MT benchmark values

### 12.3 Source Usage Rules

#### Runtime Analysis Must Not
- scrape arbitrary websites live during a comparison request,
- fetch unstable article pages synchronously inside the quote comparison flow,
- depend on raw headline text as first-order deterministic truth.

#### Runtime Analysis May
- use the latest normalized snapshots generated by the ingestion backend,
- use local reference anchors,
- use quote-extracted fields,
- use LLM reasoning over bounded structured context.

### 12.4 Updated Must-Have Data Layers
The final must-have layers for v1 are:

1. FX rates + FX history
2. PP resin benchmark / baseline
3. Brent crude benchmark
4. Freight base rates by corridor
5. Tariff / duty reference
6. Market event calendar
7. Public holiday calendar
8. Payment-term / payment-horizon rules

### 12.5 Strong Should-Have Layers
1. Fuel-cost / freight-surcharge proxy
2. Route disruption / geopolitical risk events
3. Seasonal shipping / weather disruption risk
4. Supplier-country benchmark spreads

### 12.6 Good-to-Have Layers
1. Resin benchmark history
2. Malaysia external-trade / trade-index snapshots
3. Country dependency / sourcing concentration metrics
4. Malaysia producer-price / industrial-cost context
5. News-derived event layer

### 12.7 Demo-Stability Rule
The analysis system must use the latest successfully generated snapshots and must not fail just because a non-critical refresh source is temporarily unavailable.

---

## 13. AI Role and Why the Model Is Indispensable

### 13.1 Principle
The numeric engine does the math first.  
The model does the context-aware reasoning and explanation layer.

### 13.2 With the Model
With the model, LintasNiaga can:

- interpret messy, semi-structured quote PDFs,
- extract decision-critical procurement fields,
- reason over commodity, event, and logistics context,
- explain trade-offs in plain language,
- generate timing advice,
- propose hedge guidance,
- and make bounded recommendation adjustments between near-close options.

### 13.3 Without the Model
Without the model, the system collapses into:
- static calculations,
- simple ranking,
- rule-based validations,
- and charts without meaningful explanation.

It would lose:
- robust PDF understanding,
- context-aware trade-off explanation,
- nuanced timing guidance,
- and a credible recommendation layer.

### 13.4 Conclusion
The model is not cosmetic. It is essential for:
- **interpreting structured and unstructured data,**
- **context-aware reasoning,**
- **recommendation,**
- and **clear explanation.**

---

## 14. Artificial Intelligence Methodology

### 14.1 No Fine-Tuning
No model fine-tuning, retraining, or custom training pipelines are allowed in v1.

### 14.2 Runtime Context Injection
At runtime, the backend injects:
- extracted quote data,
- reference anchors,
- latest approved snapshots,
- urgency input,
- hedge preference,
- and comparison context

into the prompt context for the model.

### 14.3 Oil Ripple Reasoning Logic
The AI should understand two distinct effects:

1. **Fuel ripple**
   - Oil spikes can raise freight surcharges quickly.
2. **Raw material ripple**
   - Oil-linked petrochemical movement can raise PP Resin input cost over the next few weeks.

This logic should inform timing recommendations and alert generation.

### 14.4 News and Weather Rule
News and weather are never treated as raw first-order decision truth. They must first be converted into structured event or risk snapshots before the model uses them.

---

## 15. Cost Engine and Recommendation Math

### 15.1 Hard Costs
For each valid quote, the backend computes:
- quote price × buyer required quantity,
- freight estimate,
- tariff.

### 15.2 Hidden Penalties
Then apply:
- **MOQ penalty** for forced overbuy / dead-stock,
- **supplier trust penalty** based on reliability profile.

### 15.3 Future FX Simulation
Using FX historical data, the backend simulates future MYR outcomes and returns:
- **p50** = expected cost
- **p10** = best case
- **p90** = worst case

### 15.4 Comparison Philosophy
The recommendation is driven primarily by:
- **total landed cost for the buyer’s required quantity**, not just normalized unit cost.

However, the system should also show normalized per-ton comparisons for context.

### 15.5 Main Comparison Anchor
The ranked table should privilege:
1. **p50 landed cost**
2. **p90 downside**
3. **p10 upside context**

### 15.6 Cheapest Quote Override Rule
LintasNiaga may recommend a non-cheapest quote if it has a better explainable value profile after adjusting for:
- reliability,
- downside risk,
- MOQ lock-up,
- timing / urgency fit,
- and credible disruption risk.

---

## 16. Ranking Logic

### 16.1 Ranking Headline
LintasNiaga recommends the **best-value supplier quote**, not the cheapest quote.

### 16.2 Top Sorting Principle
Users should first see **expected landed cost (p50 MYR)**.

### 16.3 Other Inputs That Influence Best Value
- p90 downside risk,
- supplier reliability,
- MOQ penalty,
- lead-time fit,
- urgency,
- hedge posture,
- market timing context,
- operational disruption context.

### 16.4 Lead Time Weight
Lead time should affect ranking **lightly**, not dominate it.

### 16.5 Urgency Logic
Urgency should:
- alter lead-time weight slightly,
- affect explanation wording,
- and influence lock-now / wait output.

---

## 17. Recommendation Authority and Override Rules

### 17.1 Decision Authority Model
- **Numeric engine** produces the base ranking.
- **Model layer** can adjust the final recommendation only within bounded rules.

### 17.2 Allowed Override Scope
The model may only swap the winner between **rank #1 and rank #2**.

### 17.3 When Override Is Allowed
The model may override only when:
- the numeric profiles are very close,
- **or** the trade-off difference is materially meaningful and explainable.

### 17.4 Allowed Override Reasons
Override reasons are limited to:
- supplier reliability,
- downside risk,
- MOQ / working-capital lock-up,
- urgency vs lead-time mismatch,
- materially credible disruption risk.

### 17.5 Not Allowed
The model must not override ranking based on vague or purely narrative persuasion.

### 17.6 User-Facing Output Rule
If the model changes the winner, it must explain:
- what trade-off justified the flip,
- why the original #1 was not selected,
- and why the final recommendation is still best value.

---

## 18. Output Design: Comparison Mode

### 18.1 Comparison Mode Requirement
Comparison mode requires **at least 2 valid quotes**.

### 18.2 Ranked Table
The ranked table should show, at minimum:
- supplier,
- p50 landed cost,
- p90 cost,
- p10 cost,
- lead time,
- MOQ penalty indicator,
- reliability indicator,
- rank.

### 18.3 Recommendation Card Structure
The main recommendation card should show:
1. **Recommended supplier**
2. **Timing recommendation**
3. **Recommended hedge ratio**
4. **Top 3 reasons**
5. **Optional caveat** only if materially notable
6. **Backup option**

### 18.4 Explanation Structure
Recommendation explanation should be:
- **Top 3 reasons**
- plus **1 caveat only if necessary**

### 18.5 Caveat Trigger
A caveat appears only when there is a meaningful notable risk, such as:
- large MOQ lock-up,
- weak supplier reliability,
- materially worse p90 downside,
- urgency mismatch,
- market timing risk,
- or structured disruption risk.

### 18.6 Why Not the Others
Each non-winning quote should show:
- one clear plain-language reason for rejection,
- with a click-open option for fuller explanation.

---

## 19. Backup Option Logic

### 19.1 Backup Policy
Always show **one backup option** in comparison mode.

### 19.2 What Backup Means
The backup is not just “the second-best score.”  
It is the **best credible alternative with a different trade-off profile**.

### 19.3 Backup Selection Rule
Choose the backup from the **top 3 ranked quotes**, selecting the one with the clearest different credible trade-off profile.

---

## 20. Output Design: Single-Quote Fallback Mode

### 20.1 Trigger
If exactly **1 valid quote** remains after validation, the app must switch honestly into **single-quote evaluation mode**.

### 20.2 Important UX Rule
Do **not** pretend the system performed supplier comparison.

### 20.3 Recommendation Labels
Single-quote evaluation should classify the quote as:
- **Proceed**
- **Review carefully**
- **Do not recommend**

### 20.4 Single-Quote Output
Show:
- quote status label,
- timing advice,
- hedge suggestion,
- top reasons,
- optional caveat.

### 20.5 What Must Not Be Shown
Do not show:
- winner language implying comparison,
- backup supplier,
- comparative savings vs alternatives.

---

## 21. Failure and Repair Behavior

### 21.1 Partial Failure Policy
If some quotes are invalid:
- compare valid quotes,
- exclude invalid quotes,
- explain why,
- provide a repair path.

### 21.2 UI Pattern
Show:
- a top banner summarizing valid vs excluded quotes,
- each excluded quote as its own visible row/card,
- reason for exclusion,
- missing or invalid field,
- **Fix this** action.

### 21.3 No Valid Quotes
If zero valid quotes remain:
- no analysis is performed,
- only repair flow is shown.

### 21.4 Snapshot Failure Rule
If a non-critical snapshot refresh fails:
- keep the last valid snapshot,
- mark freshness metadata,
- do not crash the recommendation flow unless the missing snapshot is classified as hard-critical.

---

## 22. Hedge Guidance Design

### 22.1 Hedge Output Role
Hedge advice is part of the final recommendation object.

### 22.2 Hedge Preference Input
Optional user preference:
- Protect margin
- Balance cost and flexibility (**default**)
- Minimize hedging

### 22.3 What These Labels Mean
They are not equivalent to p10/p50/p90.  
They describe the user’s desired protection posture toward the simulated risk bands.

### 22.4 Hedge Suggestion Policy
The system recommends a default hedge ratio using:
- p90 downside exposure,
- timing context,
- urgency,
- and hedge preference.

### 22.5 Hedge Slider Policy
The slider is a **what-if exploration tool**, not the source of truth.

### 22.6 Where Hedge Is Shown
- in the main recommendation card,
- and in the dedicated hedge section/chart area.

---

## 23. AI Explanation Layer

### 23.1 Main Explanation Philosophy
The app should not prioritize raw reasoning traces for normal users.

The main experience should be:
- clear recommendation,
- clear trade-offs,
- plain language,
- evidence over jargon.

### 23.2 Main User-Facing Explanation
Show a **clean analyst summary** as the default explanation surface.

### 23.3 Deeper Reasoning Layer
Keep a separate **AI Analyst panel/tab** for deeper explanation, evidence, and judge-facing transparency.

### 23.4 Visibility Rule
The AI Analyst panel should be **available but secondary**, not the default visual focus.

### 23.5 Judge Proof
Use traces and a deeper analysis surface to prove that the AI is doing dynamic work.

---

## 24. Core Feature Set for v1

### 24.1 LintasExtract
- Multi-PDF upload
- AI extraction from quotes
- Validation and user confirmation
- Inline repair flow

### 24.2 LintasCompare
- Side-by-side comparison of up to 5 quotes
- Ranking by best-value logic
- Winner + backup selection
- Why-not explanations

### 24.3 LintasSense
- Secondary AI Analyst panel/tab
- Plain-language analysis
- Macro/timing/risk interpretation
- Deeper evidence for judges

### 24.4 LintasRisk
- FX fan chart with p10 / p50 / p90 over 90 days
- Downside visibility for hedge reasoning

### 24.5 LintasHedge
- Default hedge recommendation
- Interactive what-if slider
- Recalculation of downside impact

### 24.6 Impact Summary
In comparison mode, show:
- **Expected MYR savings** vs cheapest-on-paper quote
- **Worst-case downside difference** vs cheapest-on-paper quote

### 24.7 Ingestion Backbone
A backend ingestion layer must generate normalized snapshots for:
- FX
- energy
- weather risk
- holidays
- OpenDOSM macro context
- news-derived event context
- PP resin benchmark context

---

## 25. Validation Story for Judges

The PRD should support three levels of validation.

### 25.1 Scenario-Based Validation
Show multiple PP Resin quotes and let the app recommend one with reasons.

### 25.2 Quantified Comparison
Show how the recommendation differs from the cheapest-on-paper quote in:
- expected cost,
- downside risk,
- and/or avoidable hidden penalties.

### 25.3 Sensitivity Testing
Show how the recommendation changes when:
- urgency changes,
- hedge preference changes,
- hedge slider assumptions change,
- or disruption/timing context changes.

This proves the system is doing decision intelligence, not static sorting.

---

## 26. Canonical Demo Flow

The demo flow should be written as:

**User action → System response → Judge takeaway**

### 26.1 Happy-Path Demo Flow

#### Step 1
**User action:** Upload up to 5 FOB PP Resin quotes, enter required quantity, select urgency.  
**System response:** Extracts fields, validates scope, flags unsupported or incomplete quotes, and prepares valid quotes for comparison.  
**Judge takeaway:** This is not simple OCR. The system is enforcing procurement-specific structure and guardrails.

#### Step 2
**User action:** Confirm or fix any extracted fields.  
**System response:** Revalidates quotes and includes only valid ones in the decision set.  
**Judge takeaway:** The product is strict on data quality but forgiving on workflow.

#### Step 3
**User action:** Run comparison.  
**System response:** Computes p10/p50/p90 landed cost bands, MOQ penalties, reliability penalties, and best-value ranking.  
**Judge takeaway:** The recommendation is math-backed, not hand-wavy.

#### Step 4
**User action:** Review recommendation card.  
**System response:** Shows recommended supplier, lock now / wait, hedge %, top 3 reasons, optional caveat, and backup option.  
**Judge takeaway:** The product returns an actionable procurement decision, not just analysis.

#### Step 5
**User action:** Open AI Analyst panel and hedge section.  
**System response:** Shows deeper analysis, market interpretation, and what-if hedge exploration.  
**Judge takeaway:** The AI layer is indispensable for reasoning and explanation, while the numeric engine stays grounded.

### 26.2 Fallback / Error Demo Flow

#### Case A: Invalid Quotes
**User action:** Upload quotes where some are missing required fields or outside scope.  
**System response:** Valid quotes proceed; invalid quotes are excluded with reasons and Fix-this actions.  
**Judge takeaway:** The system degrades gracefully instead of guessing.

#### Case B: Only One Valid Quote Remains
**User action:** Proceed with one valid quote after validation.  
**System response:** Switches into single-quote evaluation mode with Proceed / Review carefully / Do not recommend.  
**Judge takeaway:** The system does not fake comparison when comparison is unavailable.

#### Case C: Snapshot Refresh Failure
**User action:** Trigger analysis while one non-critical source refresh has failed.  
**System response:** The app uses the most recent valid snapshot and freshness metadata without crashing.  
**Judge takeaway:** Demo reliability was designed intentionally, not left to luck.

---

## 27. Risks, Assumptions, and Mitigations

### 27.1 Risk: Quote Extraction Errors
**Assumption:** PDF extraction from messy procurement PDFs will not always be perfect.  
**Mitigation:** User confirmation and inline edit flow before comparison.

### 27.2 Risk: FX/Market Source Failure
**Assumption:** An upstream provider can fail during demo.  
**Mitigation:** Snapshot generation + fallback / last-valid-snapshot strategy.

### 27.3 Risk: False Precision
**Assumption:** Broad procurement support would create fragile assumptions.  
**Mitigation:** Narrow scope to PP Resin, FOB only, supported corridors only.

### 27.4 Risk: AI Feels Arbitrary
**Assumption:** Users and judges may distrust composite AI decisions.  
**Mitigation:** Numeric engine ranks first; AI only overrides within bounded top-2 rules and must explain why.

### 27.5 Risk: UI Becomes Too Technical
**Assumption:** Raw reasoning traces can overwhelm normal users.  
**Mitigation:** Summary-first UX, deeper analysis in secondary panel.

### 27.6 Risk: Product Drifts Into Spreadsheet Clone
**Assumption:** Without clear recommendation structure, the app could feel like a ranking table only.  
**Mitigation:** Force final decision object to include supplier, timing, hedge, reasons, and backup.

### 27.7 Risk: Scraping Becomes Runtime Fragility
**Assumption:** Curated benchmark scraping is useful but source pages can change.  
**Mitigation:** Keep scraping in ingestion jobs, not in live comparison requests; validate before promoting snapshots.

---

## 28. Locked Phase 1 Ingestion Contracts

This section is **non-negotiable for the first backend build phase**.

### 28.1 Common Snapshot Envelope

All Phase 1 snapshot datasets must use this envelope:

```json
{
  "dataset": "string",
  "source": "string",
  "fetched_at": "ISO-8601 timestamp",
  "as_of": "YYYY-MM-DD or null",
  "status": "success | partial | failed",
  "record_count": 0,
  "data": []
}
```

### 28.2 Reference Freight Contract

Each freight row must contain:

```json
{
  "origin_country": "CN | TH | ID",
  "origin_port": "string",
  "destination_port": "MYPKG",
  "incoterm": "FOB",
  "currency": "USD",
  "rate_value": 0.0,
  "rate_unit": "container | mt | shipment",
  "valid_from": "YYYY-MM-DD",
  "valid_to": "YYYY-MM-DD",
  "source_note": "string"
}
```

### 28.3 Tariff Contract

Each tariff row must contain:

```json
{
  "hs_code": "3902.10",
  "product_name": "PP Resin",
  "import_country": "MY",
  "tariff_rate_pct": 5.0,
  "tariff_type": "MFN",
  "source_note": "string"
}
```

### 28.4 Port Metadata Contract

Each port row must contain:

```json
{
  "port_code": "string",
  "port_name": "string",
  "country_code": "MY | CN | TH | ID",
  "latitude": 0.0,
  "longitude": 0.0,
  "is_destination_hub": true
}
```

### 28.5 FX Snapshot Contract

The normalized FX snapshot records must contain:

```json
{
  "pair": "USDMYR",
  "date": "YYYY-MM-DD",
  "open": 0.0,
  "high": 0.0,
  "low": 0.0,
  "close": 0.0,
  "volume_optional": 0.0
}
```

Phase 1 required pairs:
- USDMYR
- CNYMYR
- THBMYR
- IDRMYR (if Indonesia remains enabled)

### 28.6 Energy Snapshot Contract

The normalized energy snapshot records must contain:

```json
{
  "symbol": "BZ=F",
  "series_name": "Brent Crude",
  "date": "YYYY-MM-DD",
  "open": 0.0,
  "high": 0.0,
  "low": 0.0,
  "close": 0.0
}
```

Phase 1 required energy series:
- Brent crude

Phase 1 optional supporting series:
- Natural gas

### 28.7 Holiday Snapshot Contract

The normalized holiday snapshot records must contain:

```json
{
  "country_code": "MY | CN | TH | ID",
  "date": "YYYY-MM-DD",
  "holiday_name": "string",
  "is_holiday": true,
  "is_long_weekend": false,
  "days_until_next_holiday": 0
}
```

### 28.8 Phase 1 Endpoint Contracts

The first backend phase must expose at least:

- `GET /health`
- `POST /ingest/reference/load`
- `POST /ingest/market/fx`
- `POST /ingest/market/energy`
- `POST /ingest/holidays`

Each ingestion endpoint must return:
- job status
- dataset name
- snapshot path or identifier
- record count
- fetched timestamp
- any warnings

---

## 29. Non-Negotiable v1 Rules

These rules must not be violated during implementation.

1. Only **PP Resin / HS 3902.10** is supported.
2. Only **FOB** quotes are supported.
3. Only supported corridors into **Port Klang** are supported.
4. Up to **5 quotes** per run.
5. **Required quantity** is mandatory.
6. **Urgency** is mandatory.
7. Hedge preference is optional, default = **Balance cost and flexibility**.
8. AI extraction must be followed by **user confirmation / correction**.
9. The system must **never guess missing critical fields**.
10. Valid quotes may proceed even if some quotes are invalid.
11. Comparison mode requires **at least 2 valid quotes**.
12. Exactly 1 valid quote triggers **single-quote evaluation mode**.
13. Best-value score remains **internal only**.
14. The main comparison anchor is **p50 landed cost**, with p10/p90 also shown.
15. The final recommendation must always include:
    - supplier,
    - timing,
    - hedge,
    - reasons.
16. A **backup option** must be shown in comparison mode.
17. The AI layer may only override between **top 2** ranked quotes.
18. Override is allowed only for:
    - reliability,
    - downside risk,
    - MOQ lock-up,
    - urgency vs lead-time mismatch,
    - credible disruption risk.
19. The app must use **graceful degradation** for invalid quotes and source/API failures.
20. The experience must be **summary-first, analysis-second**.
21. Scraping must occur in ingestion jobs or refresh flows, not live quote-comparison requests.
22. Static anchors and generated snapshots must be accessed only through centralized backend repositories/services.

---

## 30. Handoff Notes for Build

This PRD is intentionally complete enough to support:
1. Backend ingestion implementation
2. Updated architecture implementation
3. Quote workflow implementation
4. Deterministic analysis engine implementation

The next build phase should preserve all locked contracts and non-negotiable rules above.

---

## 31. Nuances and Open Uncertainties

These do not block the PRD, but they should remain visible:

1. **FX source choice changed**  
   The original design assumed BNM. The latest ingestion plan assumes `yfinance` for speed. This is acceptable for hackathon execution, but it is a strategic source-quality trade-off.

2. **Weather data must remain derived risk, not raw truth**  
   Raw weather data is not inherently decision-ready. It must be converted into shipping/port risk signals.

3. **News must remain event-derived, not headline-driven**  
   Generic news should never directly drive ranking. It must become structured event context first.

4. **PP resin benchmark scraping is the highest-fragility layer**  
   Curated source selection and validation quality will matter more than scraper code volume.

5. **Payment-term data is important but still partially assumption-driven**  
   It is one of the strongest missing variables, but v1 may rely on rules/defaults more than real supplier-specific payment feeds.

6. **Country comparison context is useful, but should remain secondary**  
   Supplier-country benchmark spreads and trade context help explanation, but should not dominate quote-level economics.

---

## 32. Final Product Statement

LintasNiaga v1 is a narrowly-scoped, explainable procurement decision engine for Malaysian plastics SMEs.

It helps a procurement executive compare up to 5 valid FOB PP Resin quotes side by side, convert them into true MYR landed-cost scenarios, account for hidden penalties and supplier risk, enrich the analysis with structured market and logistics context, and return a clear recommendation on:

- **which supplier to choose,**
- **whether to lock now or wait,**
- and **how much of the FX exposure to hedge.**

It is intentionally designed to prove one thing well:

> AI can materially improve SME procurement decisions when math, guardrails, snapshots, and explanation are combined into one bounded workflow.
