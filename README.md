# LintasNiaga

> **Choose the best-value supplier with less hidden risk.**

LintasNiaga is a procurement decision-support copilot built for Malaysian plastics SMEs that import polypropylene (PP) resin. It turns fragmented supplier PDF quotes and noisy market data into one clear, defensible procurement decision — complete with a supplier recommendation, timing stance, and FX hedge ratio.

---

## The Problem

Malaysian SMEs sourcing PP resin face a quiet but costly problem: comparing supplier quotes is harder than it looks.

A quote arrives as a PDF. It carries a price, a currency, a lead time. But on its own it tells you almost nothing about the **real landed cost** — after freight, tariffs, MOQ lock-up, currency volatility, and the risk that a suspiciously cheap price is priced against a deteriorating benchmark.

Procurement teams patch this together with spreadsheets, gut feel, and outdated FX assumptions. The result is avoidable margin loss, slow decisions, and limited ability to justify to management *why* one supplier was chosen over another.

---

## What LintasNiaga Does

LintasNiaga walks the user through a focused four-stage workflow:

**1. Upload**
Upload up to five supplier quote PDFs. The system extracts key fields — supplier name, origin, incoterm, currency, unit price, MOQ, and lead time — using deterministic extraction with a GLM-5.1 vision fallback.

**2. Review and Repair**
Extracted fields are surfaced for review before anything is committed to analysis. The user can correct values, select order quantity, urgency level, and hedge preference (Balanced / Conservative / Aggressive).

**3. Analysis**
The backend refreshes live market and logistics context — FX rates, Brent crude, weather risk, macro indicators, news signals, and PP resin benchmark data — then runs:
- deterministic landed-cost calculation across all quotes
- 30-day Monte Carlo fan chart using real FX and Brent volatility
- bounded AI reasoning over the assembled evidence

**4. Decision Result**
The user receives a single, traceable recommendation:
- **Which supplier to choose** (with ranked alternatives)
- **Whether to lock now or wait**
- **How much FX exposure to hedge**
- A 30-day landed-cost fan chart with p10 / p50 / p90 bands
- PP resin benchmark fairness check against SunSirs market data
- A downloadable bank-instruction PDF draft for hedge workflow execution

---

## Why This Matters

The core insight behind LintasNiaga is simple: **the winning quote is not always the cheapest quote**.

Hidden landed-cost drivers — freight terms, tariff exposure, MOQ penalties, supplier reliability, FX trajectory — can silently flip the ranking. A quote that looks 5% cheaper can land 12% more expensive when the full picture is assembled.

LintasNiaga assembles that picture automatically and explains the reasoning in plain language, so a procurement executive can act with confidence and explain their decision to management.

---

## Technology Overview

| Layer | Technology |
|---|---|
| Frontend | Next.js (App Router) |
| Backend | FastAPI (Python) |
| AI Orchestration | LangGraph + ilmu-GLM-5.1 |
| Observability | Langfuse |
| Market Data | yfinance, OpenWeatherMap, OpenDOSM, GNews, SunSirs |
| Data Layer | File-backed snapshot store |

The AI layer is intentionally **bounded**: GLM-5.1 explains and narrates the recommendation, but the procurement math — landed cost, Monte Carlo simulation, benchmark comparison — is fully deterministic and auditable. The model does not invent the decision.

---

## Documentation

For full product, system, and QA documentation:

| Document | Description |
|---|---|
| [`PRD.md`](./PRD.md) | Product requirements — what the system does and why |
| [`SAD.md`](./SAD.md) | System architecture — how the system is structured and how it works |
| [`QATD.md`](./QATD.md) | Quality assurance — test coverage, results, and known gaps |

---

## Team

**404NotFounders** — UMHackathon 2026, Domain 2
