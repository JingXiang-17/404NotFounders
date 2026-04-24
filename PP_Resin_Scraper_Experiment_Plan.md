# PP Resin Price Scraper Experiment Plan

## Purpose

This document is a practical step-by-step plan for building and testing a **PP resin benchmark ingestion pipeline** outside the main repo first.

The current approved direction is:
- use **SunSirs** as the primary source,
- treat the scraped value as a **benchmark/reference price input**,
- keep the pipeline narrow and reliable,
- and only move it into the main repo once the extraction path is stable.

---

# 1. Core Recommendation: isolated folder vs notebook

## Best choice: use a **new isolated folder/project**, not a notebook, as the primary workspace

### Why the isolated folder is better

A scraper pipeline is not just exploration. It quickly becomes:
- multiple files,
- repeatable runs,
- parsing rules,
- saved raw HTML,
- extracted JSON,
- logs,
- tests,
- fallback strategies,
- and eventually repo integration.

A notebook is useful for fast exploration, but it becomes messy for:
- versioning,
- file organization,
- re-running the exact same pipeline,
- managing multiple parser versions,
- adding tests,
- and turning the prototype into production code.

### Best practical approach

Use:
- **isolated folder/project** as the main workspace,
- **optional notebook** only as a scratchpad for quick regex/text experiments.

### Decision

**Primary workspace:** isolated folder/project  
**Optional support tool:** notebook for exploration only

---

# 2. What you are actually building

You are **not** building “scrape everything about polypropylene.”

You are building one narrow pipeline:

> Fetch the newest SunSirs PP-related article, extract the clean text, parse the benchmark/reference price, normalize the output into a structured record, and save all evidence for later use.

That means the pipeline should output:
- source name,
- source URL,
- article title,
- article publish date,
- extracted paragraph/sentence,
- parsed numeric price,
- currency,
- unit,
- parse confidence,
- and normalized downstream fields.

---

# 3. Scope discipline

## In scope for this experiment

- one primary source: **SunSirs**
- one target commodity family: **PP / polypropylene / wire drawing grade references**
- article-list fetch
- newest article fetch
- text extraction
- deterministic parsing first
- LLM fallback only if needed
- structured JSON output
- local persistence of evidence

## Out of scope for this experiment

- multi-site scraping from day one
- anti-bot warfare on backup sites
- broad chemical news scraping
- automatic conversion into full landed-cost recommendation logic
- production deployment
- scheduling/cron before the parser is stable

---

# 4. Architecture of the experiment

## Recommended architecture

### Stage 1: source discovery
Fetch the SunSirs PP news feed page and identify the latest relevant article URL.

### Stage 2: article fetch
Fetch the article HTML.

### Stage 3: text extraction
Try extraction in this order:
1. simple HTML selector extraction,
2. Trafilatura cleanup,
3. LLM fallback only if necessary.

### Stage 4: deterministic parse
Extract benchmark/reference fields using regex and parsing rules.

### Stage 5: confidence scoring
Assign a parser confidence score based on whether the record contains expected fields.

### Stage 6: persistence
Save:
- raw HTML,
- cleaned text,
- parsed JSON,
- logs/errors.

### Stage 7: manual review
Review whether the parsed number is actually the PP benchmark/reference price and not another number from the article.

---

# 5. Workspace setup

## Recommended folder name

Use something explicit, like:
- `pp-resin-scraper-lab`
- or `sunsirs-pp-experiment`

## Suggested structure

```text
pp-resin-scraper-lab/
  README.md
  pyproject.toml
  .env
  src/
    config.py
    main.py
    fetch/
      feed_fetcher.py
      article_fetcher.py
    extract/
      html_extract.py
      trafilatura_extract.py
    parse/
      benchmark_parser.py
      confidence.py
    models/
      records.py
    storage/
      save_raw.py
      save_json.py
    utils/
      logging.py
      text_cleaning.py
  data/
    raw/
    cleaned/
    parsed/
    logs/
  notebooks/
    scratch.ipynb
  tests/
    test_parser.py
    test_text_cleaning.py
    fixtures/
```

---

# 6. Environment and tooling

## Python environment

Use a normal Python project, not a notebook-only workflow.

## Recommended packages

Core:
- `httpx` or `requests`
- `beautifulsoup4`
- `lxml`
- `trafilatura`
- `pydantic`
- `python-dotenv`

Optional:
- `y if normal fetch starts failing
- `pandas` only if you want quick inspection tables
- `jupyter` only for scratch exploration

## Suggested principle

Start with the **lightest possible stack**:
- normal HTTP fetch first,
- browser automation only if needed.

---

# 7. Step-by-step build plan

## Phase 0 — Prepare the lab

### Goal
Set up a clean sandbox where you can iterate without polluting the main repo.

### Tasks
1. Create the isolated folder.
2. Initialize git.
3. Create Python environment.
4. Install core dependencies.
5. Add a minimal README describing the experiment goal.
6. Create the folder structure.

### Exit condition
You can run a simple `python src/main.py` entrypoint without import problems.

---

## Phase 1 — Verify the source manually

### Goal
Confirm that the current SunSirs PP feed and article pages still behave as expected from your environment.

### Tasks
1. Open the feed page manually.
2. Confirm the page is reachable from your machine.
3. Inspect the latest article links.
4. Open the latest article manually.
5. Confirm the article still contains a benchmark/reference-style PP sentence.
6. Save one sample page HTML manually for offline inspection.

### Questions to answer
- Does the feed page expose article links cleanly?
- Is the article content server-rendered or JS-dependent?
- Does the relevant benchmark sentence still exist in plain text?

### Exit condition
You have one feed page and one article page saved locally and confirmed usable.

---

## Phase 2 — Build feed discovery

### Goal
Programmatically fetch the SunSirs PP news feed and identify the latest article.

### Tasks
1. Build `feed_fetcher.py`.
2. Fetch the feed HTML.
3. Parse all visible article links.
4. Filter to the newest likely relevant article.
5. Print and save:
   - title,
   - URL,
   - publish date if available.

### Output
A structured object like:

```json
{
  "source": "SunSirs",
  "feed_url": "...",
  "latest_article_title": "...",
  "latest_article_url": "...",
  "published_at": "..."
}
```

### Exit condition
You can reliably obtain the latest article URL from code.

---

## Phase 3 — Build article fetch

### Goal
Fetch the article page content cleanly.

### Tasks
1. Build `article_fetcher.py`.
2. Request the article URL.
3. Save raw HTML to `data/raw/`.
4. Log status code, fetch timestamp, and URL.
5. Build basic retry logic.

### Minimum requirements
- timeout handling
- user-agent header
- clean filename generation
- error logging

### Exit condition
You can fetch and save article HTML repeatedly.

---

## Phase 4 — Build text extraction

### Goal
Turn article HTML into clean text.

### Strategy
Use a layered extraction strategy.

### Option sequence
1. **HTML selector extraction**
2. **Trafilatura extraction**
3. **Fallback to raw text cleanup**

### Tasks
1. Try pulling article body using HTML parsing.
2. Run Trafilatura on the saved HTML.
3. Compare results.
4. Decide which extraction path becomes default.
5. Save the cleaned text to `data/cleaned/`.

### Important rule
Do not assume Trafilatura is always best. Compare it against simple selector extraction on this site.

### Exit condition
You can consistently produce readable article text from the fetched HTML.

---

## Phase 5 — Build deterministic parser

### Goal
Extract the benchmark/reference price and related metadata without relying on an LLM first.

### Fields to extract
At minimum:
- source
- article URL
- article title
- article publish date
- commodity label
- extracted sentence
- numeric price
- currency
- unit
- benchmark date reference if present
- percentage change if present
- parse confidence

### Parser logic
Build regex patterns for sentences like:
- `PP ... benchmark price ... RMB/ton`
- `PP (wire drawing) ... price ... RMB/ton`
- `% compared to the beginning of this month`

### Tasks
1. Build sentence splitter.
2. Search for PP-relevant candidate sentences.
3. Rank candidate sentences.
4. Extract numeric price.
5. Extract currency and unit.
6. Extract any associated delta.
7. Save parsed result.

### Exit condition
The parser successfully extracts the correct benchmark/reference price from several saved examples.

---

## Phase 6 — Add confidence logic

### Goal
Know when the parser is reliable and when it needs help.

### Confidence dimensions
Score confidence based on:
- PP keyword present,
- one clear price present,
- recognized currency,
- recognized unit,
- benchmark-like phrasing,
- no major ambiguity from multiple candidate values.

### Example confidence buckets
- **High**: PP-specific sentence + price + currency + unit all found clearly
- **Medium**: price found but sentence is noisier or more ambiguous
- **Low**: multiple conflicting values or missing unit/currency

### Exit condition
Every parsed output includes a confidence rating and reason.

---

## Phase 7 — Add LLM fallback only if needed

### Goal
Use the model only when deterministic parsing is weak.

### Trigger conditions
Only call the LLM when:
- confidence is low,
- multiple candidate prices exist,
- the sentence structure changes,
- or the deterministic parser fails.

### LLM input
Send:
- article title,
- cleaned text,
- candidate sentences,
- and an explicit extraction schema.

### LLM output schema
Ask for strict JSON:
- benchmark price
- currency
- unit
- justification sentence
- confidence

### Important rule
The LLM is a **fallback extractor**, not your default parser.

### Exit condition
You can recover some low-confidence cases without making the whole system AI-dependent.

---

## Phase 8 — Persist everything properly

### Goal
Make the experiment auditable.

### Save all of these
1. raw feed HTML
2. raw article HTML
3. cleaned text
4. parsed JSON
5. logs
6. fallback/LLM output if used

### Why this matters
When the parser breaks later, you need to know whether:
- the site changed,
- the extractor changed,
- or your regex broke.

### Exit condition
One run leaves behind enough evidence for debugging and review.

---

## Phase 9 — Build a review loop

### Goal
Make sure you are extracting the right number, not just any number.

### Manual review checklist
For each experimental run, verify:
- Was the source page correct?
- Was the newest article actually PP-related?
- Did the extracted sentence clearly refer to PP benchmark/reference price?
- Is the price tied to RMB/ton or another unit?
- Did the parser pick the correct number if multiple numbers exist?

### Exit condition
You trust the parsed record after review.

---

## Phase 10 — Normalize for downstream usage

### Goal
Separate scraping from decision-engine normalization.

### Store two layers

#### Layer 1: raw source value
Example:
- `9183.33 RMB/ton`

#### Layer 2: normalized value
Example:
- converted to USD/MT
- converted to MYR/MT
- normalized timestamp field

### Important rule
Do not bury FX conversion inside scraping logic.
Keep scraping and normalization as separate steps.

### Exit condition
The parser output is ready for later integration into the procurement system.

---

# 8. Suggested development order

Do it in this exact order:

1. create isolated project
2. manually inspect SunSirs pages
3. build feed fetcher
4. build article fetcher
5. build text extractor
6. build deterministic parser
7. test parser against saved examples
8. add confidence scoring
9. add persistence/logging
10. add LLM fallback if necessary
11. add normalization layer
12. review whether it is stable enough to move into main repo

Do **not** start with:
- Playwright,
- LLM-first extraction,
- multi-site scraping,
- scheduling,
- or deployment.

---

# 9. Brainstorming recursively: what can go wrong?

## A. Source-level failure

### Possible issue
The SunSirs feed page changes structure.

### Mitigation
- save raw HTML,
- use selector abstraction,
- keep tests against saved fixtures.

## B. Article-level failure

### Possible issue
The latest article is PP-related but does not contain a parseable benchmark sentence.

### Mitigation
- scan the top N newest articles,
- not just the top 1,
- then choose the best PP candidate.

## C. Extraction-level failure

### Possible issue
Trafilatura strips too much or too little.

### Mitigation
- compare selector extraction vs Trafilatura,
- choose default based on evidence,
- keep fallback path.

## D. Parsing-level failure

### Possible issue
The article contains multiple numeric values and the parser picks the wrong one.

### Mitigation
- sentence-level candidate ranking,
- confidence scoring,
- optional LLM fallback.

## E. Semantics-level failure

### Possible issue
You confuse benchmark/reference pricing with actual transaction price.

### Mitigation
- always label it as benchmark/reference input,
- not “market truth.”

## F. Integration-level failure

### Possible issue
You cram this into the main repo too early and pollute architecture.

### Mitigation
- stabilize in isolated folder first,
- then migrate only the proven parts.

---

# 10. Testing plan

## Minimum tests you should write

### 1. Feed parser test
Given a saved feed HTML fixture, confirm that the parser extracts article links correctly.

### 2. Article text extraction test
Given saved article HTML, confirm that cleaned text contains the expected PP sentence.

### 3. Benchmark parser test
Given cleaned text fixtures, confirm the parser extracts:
- price,
- currency,
- unit,
- sentence.

### 4. Ambiguity test
Given a text with multiple numbers, confirm the parser either:
- chooses the correct one,
- or marks confidence low.

### 5. Regression fixtures
Save a few historical examples so you can detect future parser breakage.

---

# 11. What success looks like

You are successful when you can run one command and get a clean structured output like:

```json
{
  "source": "SunSirs",
  "article_url": "...",
  "article_title": "...",
  "published_at": "2026-04-22",
  "commodity": "PP wire-drawing benchmark",
  "price": 9183.33,
  "currency": "RMB",
  "unit": "ton",
  "benchmark_sentence": "...",
  "parser_confidence": "high",
  "normalized": {
    "price_usd_per_mt": null,
    "price_myr_per_mt": null
  }
}
```

Even better if the run also saves:
- raw HTML,
- cleaned text,
- logs,
- and a parser decision trace.

---

# 12. What to do after the experiment is stable

Only after the experiment is stable should you move it into the main repo.

## Migration rule
Move only these proven pieces:
- feed fetcher
- article fetcher
- text extraction logic
- deterministic parser
- confidence logic
- persistence schema

Do **not** move over:
- scratch notebook junk,
- experimental regex variants,
- unused backup-site logic,
- or half-working Playwright code.

---

# 13. Final recommendation summary

## Use this setup
- **Primary workspace:** isolated folder/project
- **Optional:** notebook for scratch experiments only
- **Primary source:** SunSirs only
- **Acquisition strategy:** normal HTTP fetch first
- **Text extraction:** selector extraction first, Trafilatura second
- **Parsing strategy:** deterministic parser first, LLM fallback only when necessary
- **Storage:** raw HTML + cleaned text + parsed JSON + logs
- **Mindset:** benchmark/reference ingestion, not full market truth

## Best next move
Build the smallest pipeline that can:
1. fetch the feed,
2. fetch the newest article,
3. extract readable text,
4. parse the PP benchmark/reference value,
5. save all evidence.

That is the right first win.

