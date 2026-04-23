# LintasNiaga Data Gathering & Web Scraping Guide
## Role Playbook for the Person in Charge of Scraping + Data Collection

**Role:** Data ingestion owner / scraping owner  
**Project:** LintasNiaga  
**Audience:** Teammate responsible for collecting, normalizing, validating, and handing off external data to the backend  
**Version:** 1.0  
**Based on:** latest repo README + v2.1 PRD + v2.1 architecture + v2.1 tech stack

---

## 0. What I checked in your repo first

I reviewed the current source-of-truth docs in the repo:

- `README.md`
- `LintasNiaga_Comprehensive_PRD_v2_1_IngestionLocked.md`
- `LintasNiaga_Architecture_Blueprint_v2_1_IngestionAligned.md`
- `LintasNiaga_Tech_Stack_Blueprint_v2_1_IngestionAligned.md`

### What that means for your role

Your job is **not** to build a random scraper farm.

Your job is to produce **clean, reliable, analysis-ready data** for the backend-owned decision engine.

That means:
1. gather the right external data,
2. save the raw artifacts when useful,
3. normalize it into the agreed snapshot format,
4. validate it,
5. keep the newest good snapshot,
6. never let scraping logic leak into the live quote-comparison request path.

---

## 1. First important answer: IDE or notebook?

## Recommendation
Use an **IDE as your primary working environment**.  
Use a **notebook only as a temporary exploration tool**.

## Use an IDE for:
- provider adapters
- scraper modules
- snapshot writers
- validation logic
- file/path management
- retries/timeouts
- reproducible scripts
- git-tracked code
- test files

## Use a notebook only for:
- quickly testing a single API response
- inspecting a CSV/Parquet file once
- experimenting with HTML extraction on 1–2 pages
- debugging one-off parsing issues
- plotting or inspecting a time series briefly

## Do NOT make the notebook your real workflow
Because your task is operational, not exploratory only.

You need:
- reusable scripts
- reproducible outputs
- deterministic folder paths
- code your teammates can run

### Best practice
- **IDE first**
- notebook only for quick experiments
- once something works in a notebook, move it into a proper Python module immediately

---

## 2. Your mission in one sentence

You must create **trusted local reference files and normalized snapshots** so the analysis pipeline can consume market/logistics context without relying on unstable live scraping during comparison runs.

---

## 3. Data categories you own

You are responsible for the parts below.

## A. Local deterministic anchors
These are not “scraping tasks.”  
They are curated local files.

You should prepare:
- `freight_rates.json`
- `tariffs_my_hs.json`
- `ports.json`
- `source_registry.json`

## B. Snapshot-producing pipelines
You should help gather or generate:
- FX snapshots
- energy snapshots
- holiday snapshots
- weather-risk snapshots
- OpenDOSM macro snapshots
- GNews event snapshots
- PP resin benchmark snapshots

## C. Raw artifacts where useful
You should store:
- raw HTML for resin sources
- extracted text for resin sources
- downloaded raw datasets if debugging is needed
- maybe raw news metadata dumps if useful for ranking/deduping

---

## 4. Folder structure you should work against

Use this mental model when doing your work:

```text
apps/api/
  app/
    providers/
    scrapers/
    repositories/
    services/
    schemas/

data/
  reference/
    freight_rates.json
    tariffs_my_hs.json
    ports.json
    source_registry.json

  snapshots/
    fx/
    energy/
    holidays/
    weather/
    opendosm/
    news/
    resin/

  raw/
    opendosm/
    news/
    resin_html/
    resin_text/

  tmp/
```

### Your rule
- **reference/** = deterministic anchors
- **snapshots/** = normalized outputs the analysis engine can trust
- **raw/** = ugly input artifacts kept for debugging and traceability

---

## 5. Your output contract

All snapshot outputs should eventually follow the agreed envelope:

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

You should think in terms of:
- **raw input**
- **normalized snapshot**
- **promotion to latest usable version**

Not just “I scraped something.”

---

## 6. The exact working approach I recommend

## Day 1 mindset
Build the **safe, deterministic, easy layers first**.

## Day 2 mindset
Build the **networked but manageable source pipelines**.

## Day 3 mindset
Fight the **PP resin benchmark extraction** and validation.

---

# 7. Step-by-step guide by source

## Step 1 — Create the local reference anchors first

This is the first thing you should do before any scraping.

### 1.1 Create `freight_rates.json`
You need rows that describe supported corridors into Port Klang.

At minimum capture:
- origin country
- origin port
- destination port = MYPKG
- incoterm = FOB
- currency
- rate value
- rate unit
- valid_from
- valid_to
- source_note

### 1.2 Create `tariffs_my_hs.json`
Start extremely narrow:
- HS code `3902.10`
- product = PP Resin
- import country = MY
- tariff rate %
- tariff type
- source note

### 1.3 Create `ports.json`
You need this because weather-risk logic depends on coordinates.

At minimum:
- port_code
- port_name
- country_code
- latitude
- longitude
- is_destination_hub

Include:
- Port Klang
- your chosen China ports
- your Thailand port
- your Indonesia port

### 1.4 Create `source_registry.json`
This is for the resin benchmark scraper.

At minimum:
- source_name
- url
- domain
- expected_region
- expected_content_type
- language
- priority
- notes
- enabled

### 1.5 Validate all 4 files before doing anything else
Do not move on until:
- they parse correctly
- no missing required fields
- values look sane
- date formats are consistent
- country/port codes are standardized

---

## Step 2 — Gather FX and energy data

These are not scraping tasks. Use the provider path.

### 2.1 What to collect
Required:
- USDMYR
- CNYMYR
- THBMYR
- IDRMYR if Indonesia is active

Energy:
- Brent crude required
- natural gas optional

### 2.2 What to save
For FX:
- date
- open
- high
- low
- close

For energy:
- symbol
- series_name
- date
- open
- high
- low
- close

### 2.3 How to work
1. write one small provider script/module
2. fetch one pair first
3. inspect the raw returned dataframe
4. normalize columns immediately
5. save into `/data/snapshots/fx/`
6. repeat for the rest

### 2.4 What to check
- are dates ascending?
- any missing values?
- is currency orientation consistent?
- are weekend gaps acceptable?
- did symbol mapping accidentally invert the pair?

### 2.5 Your handoff condition
You are done only when another teammate can read one normalized FX snapshot without knowing `yfinance`.

---

## Step 3 — Build the holiday snapshot

This is easy and should be done early.

### 3.1 Countries
- MY
- CN
- TH
- ID

### 3.2 What to generate
Per row:
- country_code
- date
- holiday_name
- is_holiday
- is_long_weekend
- days_until_next_holiday

### 3.3 How to work
1. generate a one-year window first
2. inspect actual outputs country by country
3. confirm date formatting
4. compute useful derived fields
5. save to `/data/snapshots/holidays/`

### 3.4 Why this matters
This is one of the easiest and most valuable context layers:
- port closures
- customs/banking delay assumptions
- supplier shutdown windows

---

## Step 4 — Build weather-risk, not “weather”

This is one of the most important conceptual rules.

You are **not** collecting weather for the sake of weather.

You are collecting **port disruption risk**.

### 4.1 Use `ports.json`
Read the coordinates from the reference anchor.

### 4.2 What raw weather fields may be useful
Examples:
- wind speed
- rain volume
- precipitation probability
- storm alerts
- severe weather indicators

### 4.3 What the normalized snapshot should contain
Do not pass raw weather payloads downstream by default.

Create a normalized risk output like:
- port_code
- forecast_date
- raw_weather_summary
- alert_present
- wind_risk_flag
- precipitation_risk_flag
- derived_port_risk_score
- notes

### 4.4 How to work
1. test one port first
2. inspect raw JSON response
3. map only the fields you actually need
4. create a tiny risk-derivation function
5. save normalized rows
6. repeat for the remaining ports

### 4.5 Mistake to avoid
Do not let the rest of the app depend on giant raw weather blobs.

---

## Step 5 — Build OpenDOSM macro snapshots

This is where you collect Malaysia-specific macro context.

### 5.1 Start with the easiest datasets
Do not try to ingest everything.

Start with:
- fuel price
- IPI or one industrial indicator

### 5.2 What to do first
1. find the direct downloadable dataset URL if available
2. manually download once
3. inspect the schema
4. identify the date column and value columns
5. normalize the column names
6. save a compact snapshot shape

### 5.3 Normalize aggressively
Do not expose huge raw tables to analysis.

You want compact context like:
- latest value
- previous value
- month-over-month movement
- year-over-year movement if easy
- source date

### 5.4 Save two things if needed
- optional raw file in `/data/raw/opendosm/`
- normalized snapshot in `/data/snapshots/opendosm/`

### 5.5 Mistake to avoid
Do not overbuild discovery logic first.  
For hackathon, direct dataset handling is usually enough.

---

## Step 6 — Build GNews event snapshots

Again: not “news truth.”  
This is **event-intake metadata**.

### 6.1 Use a double-query strategy
Create two buckets of searches.

#### Bucket A — logistics / supply / geopolitics
Examples:
- polypropylene shipping disruption Asia
- petrochemical supply disruption Asia
- port congestion Asia plastics
- red sea shipping plastics

#### Bucket B — finance / FX / oil / Malaysia macro
Examples:
- ringgit outlook Malaysia imports
- oil prices Asia plastics
- USD MYR Malaysia manufacturing

### 6.2 What to collect
At minimum:
- title
- description/snippet
- published date
- source/publisher
- URL
- query bucket
- keyword match score (simple heuristic is enough)

### 6.3 How to work
1. fetch small batches only
2. store the raw metadata list
3. normalize field names
4. dedupe by normalized title + domain
5. rank by relevance
6. save top-N as event snapshot

### 6.4 What the normalized event snapshot should contain
Examples:
- event_id
- title
- published_at
- source
- url
- category
- relevance_score
- affected_dimension
- notes

### 6.5 Mistake to avoid
Do not pass raw article titles directly into ranking logic.  
This is context for reasoning, not deterministic truth.

---

## Step 7 — Do the PP resin benchmark “boss fight” properly

This is your hardest task.

Treat it like a mini pipeline, not a one-off scraper.

### 7.1 Pick sources first, not code first
Open `source_registry.json`.

Only enable:
- sources that are relevant to Asia / PP / chemical market commentary
- sources with article-like content
- sources you can fetch consistently

Do not start by scraping random pages.

### 7.2 For each source, do this exact flow

#### Phase A — fetch raw HTML
1. request the page
2. save raw HTML into `/data/raw/resin_html/`
3. include a timestamp and slug in filename

#### Phase B — extract clean text
1. run Trafilatura on the HTML
2. save extracted text / JSON into `/data/raw/resin_text/`
3. inspect whether the result actually contains useful benchmark content

#### Phase C — LLM parse
Ask the model to extract:
- commodity
- region
- price_value
- currency
- unit
- date_reference
- confidence
- evidence_snippet

#### Phase D — validate
Reject or flag any output that fails:
- currency not USD
- unit not normalizable to MT
- absurd price range
- no date
- no evidence snippet
- wrong commodity / wrong region

#### Phase E — promote only if valid
Only after validation should it become:
- `/data/snapshots/resin/...`

### 7.3 Your biggest quality rule
Never overwrite the latest trusted benchmark snapshot with a weak parse just because the scraper technically “returned something.”

### 7.4 Mistakes to avoid
- scraping live during analysis requests
- not saving raw HTML
- not saving extracted text
- trusting LLM parse without validation
- scraping too many sites at once before one pipeline is stable

---

## Step 8 — Build freshness and fallback habits

This matters a lot.

### 8.1 Every dataset should have:
- fetched_at
- as_of
- source
- status
- record_count

### 8.2 For fragile datasets, also keep:
- last good snapshot
- last failed attempt timestamp
- warning note

### 8.3 Why this matters
When something fails, the right behavior is:
- keep the last valid snapshot,
- mark freshness,
- do not crash the system.

---

## Step 9 — Validate before handoff

Before telling your team “done,” do this checklist.

## 9.1 Reference files
- valid JSON
- no missing required keys
- country codes and ports standardized
- dates standardized

## 9.2 Snapshots
- use the common snapshot envelope
- dataset names consistent
- record count correct
- no weird null storms
- source field present

## 9.3 Raw artifacts
- resin HTML saved
- resin extracted text saved
- raw files not mixed into snapshot folders

## 9.4 Reproducibility
Ask:
- can another teammate rerun this?
- can another teammate find the latest snapshot?
- can another teammate understand what failed?

If no, your work is not production-ready enough for the hackathon.

---

# 8. Granular “what should I do first” execution order

## Phase A — First 2–4 hours
1. set up your IDE environment
2. pull latest repo
3. create/verify folder structure
4. create `freight_rates.json`
5. create `tariffs_my_hs.json`
6. create `ports.json`
7. create `source_registry.json`

## Phase B — Next 3–5 hours
8. build FX snapshot pipeline
9. build energy snapshot pipeline
10. build holiday snapshot pipeline
11. validate snapshot envelope consistency

## Phase C — Next 4–6 hours
12. build one-port weather-risk pipeline
13. expand to all required ports
14. build first OpenDOSM snapshot
15. build first GNews event snapshot
16. confirm normalized output formats

## Phase D — Last heavy block
17. choose 1–2 resin benchmark sources only
18. save raw HTML
19. run Trafilatura
20. inspect extracted text manually
21. build LLM parser prompt
22. build validator
23. promote only validated benchmark snapshots

---

# 9. Exact working style I recommend for you

## Use IDE for main work
Recommended workflow:
1. keep one terminal for running scripts
2. keep one terminal for tests or quick API checks
3. keep one editor tab for schemas
4. keep one for providers/scrapers
5. keep one for inspecting snapshot outputs

## Use notebook only for:
- checking one API response shape
- quickly testing one HTML extraction
- inspecting one dataset

Then move the logic into the repo immediately.

---

# 10. How to think about your deliverables

By the end of your work, your team should have:

## Deterministic anchors
- freight matrix
- tariff rules
- ports
- scrape source registry

## Stable generated snapshots
- FX
- energy
- holidays
- weather risk
- OpenDOSM macro
- GNews event metadata
- resin benchmark

## Debuggability
- raw HTML for resin pages
- extracted text for resin pages
- clear file naming
- freshness metadata

If you achieve that, you have done your job well.

---

# 11. Practical final recommendation

## Use an IDE as your main environment
Best fit for:
- building provider modules
- writing reusable scripts
- saving data correctly
- validating outputs
- handing work off to teammates

## Use notebooks only as a scratchpad
Good for:
- testing one idea quickly
- not good as your real implementation environment

## Your core discipline
Do not optimize for “I managed to scrape something.”  
Optimize for:

> **I created reliable, validated, reusable data artifacts the analysis pipeline can trust.**

---

# 12. Very short checklist before you start

- [ ] pull latest repo
- [ ] verify current source-of-truth docs
- [ ] set up IDE + virtual environment
- [ ] create reference anchors first
- [ ] implement easy snapshot pipelines second
- [ ] do weather/news as normalized risk/event context only
- [ ] do resin scraping last
- [ ] validate before promoting snapshots
- [ ] keep raw artifacts for the resin pipeline
- [ ] hand off clean snapshot paths, not messy notes
