# PP Resin Scraper -> Core System Integration Plan

## 1. Objective

Integrate the scraper output into the core system as a reliable, idempotent, observable data ingestion flow so each SunSirs PP benchmark update becomes a trusted core price record with auditability.

## 2. Current State (What Exists Today)

The scraper currently:

1. Fetches SunSirs pages and bypasses `HW_CHECK`.
2. Discovers a PP article/page.
3. Extracts text (selectors first, trafilatura fallback with table support).
4. Parses benchmark values into JSON.
5. Writes artifacts to local disk:
   - `data/raw/*.html`
   - `data/cleaned/*.txt`
   - `data/parsed/*.json`
   - `data/logs/*.log`

Current parsed payload example:

```json
{
  "source": "SunSirs",
  "article_url": "https://www.sunsirs.com/uk/prodetail-718.html",
  "article_title": "PP",
  "published_at": "2026-04-24",
  "commodity": "PP wire-drawing benchmark",
  "price": 9113.33,
  "currency": "unknown",
  "unit": "ton",
  "benchmark_sentence": "| PP | Rubber & plastics | 9113.33 | 2026-04-24 |",
  "parser_confidence": "high",
  "confidence_reason": "parsed from PP commodity table row",
  "percentage_change": null,
  "normalized": {
    "price_usd_per_mt": null,
    "price_myr_per_mt": null
  }
}
```

## 3. Target End-to-End Architecture

```text
Scheduler
  -> Scraper Run
    -> Parsed JSON + Evidence Artifacts
      -> Integration Adapter (map + validate + enrich)
        -> Core Ingestion API (idempotent upsert)
          -> Core Validation + Canonicalization
            -> Core Price Store
              -> Downstream Analytics/Alerts/UI
```

## 4. Integration Model (Recommended)

Use a **push-based adapter** from scraper to core ingestion API, with local retry queue for resilience.

### Why this model

1. Fast delivery (no external polling needed).
2. Explicit delivery status and retries.
3. Clear ownership boundary between scraper and core.
4. Easier idempotency and alerting.

## 5. Data Contract Design

## 5.1 Contract A: Scraper Output (Producer Contract)

Maintain current schema as producer payload, but wrap it in an envelope when sending to core.

## 5.2 Contract B: Core Ingestion Envelope (Transport Contract)

```json
{
  "schema_version": "1.0",
  "event_id": "uuid-v4",
  "producer": "pp-resin-scraper-lab",
  "produced_at": "2026-04-24T03:46:56Z",
  "run_id": "20260424_114656",
  "payload": {
    "...current parsed payload..."
  },
  "evidence": {
    "raw_html_path": "data/raw/prodetail-718_20260424_114656.html",
    "cleaned_text_path": "data/cleaned/article_20260424_114656.txt",
    "parsed_json_path": "data/parsed/parsed_20260424_114656.json",
    "log_path": "data/logs/run_20260424_114651.log"
  }
}
```

## 5.3 Contract C: Core Canonical Price Record (Internal Core Model)

```json
{
  "series_key": "sunsirs.pp.wire_drawing.cn",
  "source": "SunSirs",
  "commodity": "PP wire-drawing benchmark",
  "observation_date": "2026-04-24",
  "value": 9113.33,
  "unit": "ton",
  "currency": "CNY",
  "confidence": "high",
  "confidence_reason": "parsed from PP commodity table row",
  "source_url": "https://www.sunsirs.com/uk/prodetail-718.html",
  "provenance": {
    "event_id": "uuid-v4",
    "run_id": "20260424_114656"
  }
}
```

## 5.4 Field Mapping Rules

| Scraper field | Core field | Rule |
| --- | --- | --- |
| `source` | `source` | direct |
| `commodity` | `commodity` | direct |
| `price` | `value` | direct numeric |
| `unit` | `unit` | normalize to enum (`ton`, `mt`, etc.) |
| `published_at` | `observation_date` | direct date; fallback from benchmark row date |
| `parser_confidence` | `confidence` | direct |
| `confidence_reason` | `confidence_reason` | direct |
| `article_url` | `source_url` | direct |
| `currency` | `currency` | if `unknown`, apply core policy (see below) |
| `normalized.*` | optional derived fields | keep nullable until FX normalization finalized |

### Currency policy for `unknown`

1. Ingest as `currency = null` + `currency_inferred = true`, or
2. Infer `CNY` for known SunSirs PP series using deterministic source rule.

Recommendation: start with option 2 for this specific series, but mark `currency_inference_reason` for auditability.

## 6. End-to-End Process (Granular Runtime Flow)

## 6.1 Job Trigger

1. Scheduler triggers scraper (cron, Airflow, GitHub Actions, or internal orchestrator).
2. Generate `run_id`.
3. Start structured run logging.

## 6.2 Scrape + Parse

1. Fetch feed page.
2. Resolve anti-bot challenge.
3. Discover latest PP page.
4. Fetch article/page HTML.
5. Extract text/table.
6. Parse benchmark payload.
7. Write local artifacts.

## 6.3 Integration Adapter Stage

1. Load parsed JSON.
2. Validate producer schema.
3. Enrich with `event_id`, `run_id`, timestamps, evidence paths.
4. Map to core ingestion envelope.
5. Apply pre-send quality gates:
   - required fields present
   - `price > 0`
   - confidence threshold (default allow `high` and `medium`, quarantine `low`)

## 6.4 Delivery Stage

1. POST envelope to core ingestion endpoint.
2. Use idempotency key:
   - `hash(source + article_url + published_at + price + commodity)`
3. On success (2xx), mark delivered.
4. On transient failure (429/5xx/timeouts), retry with backoff.
5. On permanent failure (4xx validation), send to quarantine queue and alert.

## 6.5 Core Ingestion Stage

1. Authenticate request.
2. Validate envelope and payload schema.
3. Deduplicate via idempotency key.
4. Transform to canonical model.
5. Upsert canonical price table.
6. Persist raw envelope for audit.
7. Emit downstream event (`price_ingested`).

## 6.6 Post-Ingestion Reconciliation

1. Compare scraper run count vs ingested count.
2. Alert if mismatch.
3. Publish run summary metrics.

## 7. Required Changes in This Repo (Scraper Side)

Add integration module and wiring:

1. `src/integrations/core_client.py`
   - HTTP client, auth headers, retries, timeout
2. `src/integrations/mapper.py`
   - map parsed payload -> ingestion envelope
3. `src/integrations/idempotency.py`
   - deterministic idempotency key generator
4. `src/integrations/retry_queue.py`
   - local disk retry/quarantine files
5. `src/main.py`
   - invoke adapter after `save_parsed_json(result)`
6. `src/config.py`
   - add core integration env vars

Recommended new env vars:

```dotenv
CORE_INGEST_ENABLED=true
CORE_INGEST_URL=https://core.example.com/api/v1/market-data/ingest
CORE_INGEST_API_KEY=...
CORE_INGEST_TIMEOUT_SECONDS=20
CORE_INGEST_MAX_RETRIES=5
CORE_MIN_CONFIDENCE=medium
CORE_RETRY_DIR=data/retry
CORE_QUARANTINE_DIR=data/quarantine
```

## 8. Required Changes in Core System

1. Add `POST /api/v1/market-data/ingest` endpoint.
2. Add request schema validator (strict versioned schema).
3. Add idempotency store (Redis or DB unique index).
4. Add canonical upsert service for PP benchmark series.
5. Add ingestion audit table:
   - event_id
   - idempotency_key
   - received_at
   - validation_result
   - canonical_record_id
6. Add dead-letter/quarantine handling API or table.
7. Add observability dashboards and alerts.

## 9. Reliability, Error Handling, and Idempotency

### Retry strategy

1. Retry only transient errors: network timeout, 429, 5xx.
2. Backoff: exponential with jitter.
3. Max retry attempts: configurable.
4. Persist retry payload locally between runs.

### Permanent failure handling

1. 4xx schema/validation failures -> quarantine file/table.
2. Raise alert with event_id and reason.
3. Manual replay command after fix.

### Idempotency guardrails

1. Client sends idempotency key header.
2. Server enforces unique key window.
3. Duplicate requests return safe success response with existing record id.

## 10. Security and Access

1. API key or service token auth from scraper to core.
2. TLS required.
3. No secrets in repo; env/secret manager only.
4. Audit log must include caller identity and trace id.

## 11. Observability and Ops

Track these metrics on both sides:

1. `scraper_runs_total`
2. `scraper_parse_success_total`
3. `core_ingest_attempt_total`
4. `core_ingest_success_total`
5. `core_ingest_failure_total` (by code class)
6. `core_ingest_latency_ms`
7. `quarantine_count`
8. `duplicate_event_count`

Essential alerts:

1. No successful ingest for N schedule intervals.
2. Failure rate > threshold over rolling window.
3. Quarantine count > 0.
4. Price delta anomaly vs last accepted value.

## 12. Testing Strategy

## 12.1 Scraper-side tests

1. Unit tests for mapper field mapping.
2. Unit tests for idempotency key generation stability.
3. Unit tests for retry decision logic.
4. Contract test against sample core ingestion schema.

## 12.2 Core-side tests

1. Endpoint validation tests (good/bad envelopes).
2. Idempotency duplicate tests.
3. Upsert behavior tests.
4. Authorization tests.

## 12.3 End-to-end tests

1. Replay known parsed payload and verify canonical write.
2. Simulate transient 5xx and confirm retry success.
3. Simulate invalid payload and confirm quarantine path.
4. Re-submit same payload and confirm deduped response.

## 13. Rollout Plan

## Phase 0: Contract Alignment

1. Finalize schema versions and mapping rules.
2. Approve currency inference policy.
3. Define confidence gating policy.

## Phase 1: Dark Launch

1. Enable adapter in "send + no-core-write" test endpoint mode.
2. Verify payload correctness and stability.
3. Validate dashboards/alerts.

## Phase 2: Limited Production

1. Enable writes for PP series only.
2. Keep manual reconciliation daily.
3. Monitor duplicate, latency, and failure metrics.

## Phase 3: Full Production

1. Make ingestion path primary.
2. Enable auto-replay from retry queue.
3. Add on-call runbook and operational ownership.

## 14. Runbook (Day-2 Operations)

## Common incidents and actions

1. **Anti-bot change causes empty feed**
   - confirm challenge signature changed
   - patch challenge solver
   - replay failed runs
2. **Core endpoint 5xx spike**
   - allow retry queue accumulation
   - pause schedule if sustained
   - replay when recovered
3. **Schema drift**
   - quarantine bad payloads
   - patch mapper/validator
   - replay quarantined events
4. **Unexpected price jump**
   - trigger anomaly review
   - compare with source evidence
   - mark accepted/rejected in core

## 15. Acceptance Criteria

Integration is complete when:

1. Scraper run automatically sends envelope to core.
2. Core stores canonical PP benchmark record with idempotent upsert.
3. Duplicate sends do not create duplicate records.
4. Failed sends are retried/quarantined with operator visibility.
5. Metrics and alerts are active and tested.
6. End-to-end tests pass in CI for the integration path.

## 16. Suggested Implementation Backlog (Execution Order)

1. Define shared JSON schema files (producer + envelope).
2. Implement scraper integration adapter + mapper.
3. Implement core ingestion endpoint + schema validation.
4. Implement idempotency + upsert.
5. Add retry/quarantine mechanisms.
6. Add metrics, dashboards, and alerts.
7. Run dark launch.
8. Run limited production.
9. Cut over to full production.

