# LintasNiaga Product Requirements Document

**Project:** LintasNiaga  
**Document Type:** Product Requirements Document  
**Version:** 1.0 submission draft  
**Grounded Against Code:** 2026-04-25  
**Prepared For:** UMHackathon 2026 Preliminary Round

## 1. Executive Summary

LintasNiaga is a procurement decision-support system for Malaysian plastics SMEs importing polypropylene (PP) resin. It helps users upload supplier quotation PDFs, normalize extracted quote data, compare landed-cost scenarios, and receive a recommendation on:

- which supplier to choose
- whether to lock now or wait
- how much FX exposure to hedge

The current product combines deterministic backend calculations, refreshed market and logistics context, and bounded AI reasoning with traceability.

## 2. Problem Statement

SMEs often compare raw-material supplier quotations manually using spreadsheets, intuition, and outdated market assumptions. This creates several problems:

- quoted prices are hard to normalize across currencies and suppliers
- hidden landed-cost drivers such as freight, tariffs, MOQ, and supplier reliability are missed
- currency and oil volatility create timing risk
- procurement teams cannot clearly explain why one quote is safer or better value than another

The result is avoidable margin loss, weak decision confidence, and slow procurement action.

## 3. Product Vision

LintasNiaga should become a disciplined procurement copilot that converts fragmented quote documents and noisy market context into one clear action-oriented decision.

Core product promise:

> Choose the best-value supplier with less hidden risk.

## 4. Target Users

Primary user:

- procurement executive or operations-commercial decision maker at a Malaysian plastics SME

User goals:

- compare supplier offers quickly
- avoid misleading “cheap” quotes
- understand downside risk before committing
- justify procurement decisions to management

## 5. Scope

### In Scope

- PP resin procurement analysis
- supplier PDF quote upload
- quote extraction and repair workflow
- quantity-driven landed-cost comparison
- 30-day landed-cost fan chart
- hedge recommendation and hedge replay
- PP resin benchmark price fairness check
- traceable AI explanation
- bank-instruction PDF draft generation

### Out of Scope

- direct trade execution via WorldFirst
- ERP integration
- multi-industry sourcing
- long-term supplier management
- database-backed enterprise workflow orchestration

## 6. Current Product Flow

The implemented product currently follows four major user stages:

1. Landing page
2. Upload and request setup
3. Review and analysis trigger
4. Analysis progress and final result

### Stage 1: Landing

The user learns the value proposition and starts a new analysis.

### Stage 2: Upload and Setup

The user:

- uploads up to 5 PDF quotes
- enters required quantity in metric tons
- selects urgency: `Normal` or `Urgent`

The UI only allows continuation once at least one quote has uploaded successfully and quantity is valid.

### Stage 3: Review and Repair

The user reviews extracted quote fields and can correct:

- supplier name
- origin
- incoterm
- currency
- unit price
- MOQ
- lead time

The user also selects hedge preference:

- `Balanced hedge`
- `Conservative hedge`
- `Aggressive hedge`

### Stage 4: Analysis and Result

The backend refreshes required market and risk snapshots, runs deterministic analysis plus Monte Carlo simulation, calls the AI reasoning layer, and returns:

- ranked quotes
- recommended quote
- timing recommendation
- hedge percentage
- fan chart
- risk explanation
- PP resin benchmark comparison
- backup option
- bank-instruction draft path

## 7. Functional Requirements

### FR1: Quote Upload

The system shall accept PDF quote uploads and store upload state per file.

### FR2: Quote Extraction

The system shall extract quote fields using deterministic extraction first and model-based fallback when needed.

### FR3: Quote Repair

The system shall allow the user to correct extracted fields before analysis.

### FR4: Validation

The system shall only include valid or repaired quotes in analysis.

### FR5: Quantity-Based Analysis

The system shall require purchase quantity because landed cost and MOQ impact depend on it.

### FR6: Market Context Refresh

The system shall refresh and validate critical analysis context before running analysis.

### FR7: Landed-Cost Calculation

The system shall compute landed-cost components including:

- material cost
- freight
- tariff
- MOQ penalty
- reliability/trust penalty

### FR8: Monte Carlo Fan Chart

The system shall generate a 30-day landed-cost fan chart using real FX and Brent historical data from stored snapshots.

### FR9: Recommendation Engine

The system shall return a recommendation containing:

- recommended quote
- timing (`lock_now` or `wait`)
- hedge ratio
- reasons
- impact summary

### FR10: Single-Quote Mode

If only one valid quote remains, the system shall switch honestly into single-quote evaluation mode with:

- `proceed`
- `review_carefully`
- `do_not_recommend`

### FR11: PP Resin Benchmark

The system shall compare quoted material pricing against SunSirs PP benchmark data and label quotes as:

- `below_market`
- `fair`
- `premium`
- `high_premium`

### FR12: Hedge Replay

The system shall allow the user to adjust a hedge slider and recalculate the displayed scenario without rerolling random shocks.

### FR13: Bank Instruction Draft

The system shall generate a structured bank-instruction draft for hedge workflow storytelling and download as PDF through the frontend.

### FR14: Traceability

The system shall expose AI traceability metadata for judging and debugging when available.

## 8. Non-Functional Requirements

### NFR1: Explainability

Recommendations must be explainable in plain language and tied to visible evidence.

### NFR2: Grounded Analysis

The AI layer must not invent the procurement decision from scratch. Deterministic ranking and simulation remain the primary decision anchors.

### NFR3: Reliability

The product should fail clearly when critical market context is missing, instead of silently producing fake certainty.

### NFR4: Traceability

The system must support observable AI traces for hackathon judge validation.

### NFR5: Demo Fit

The product must remain narrow and credible rather than overly broad and fragile.

## 9. Data Inputs

Current analysis consumes:

- extracted quote data
- freight reference data
- tariff rules
- supplier reliability seed data
- FX snapshots
- Brent energy snapshot
- weather snapshot
- holiday snapshot
- OpenDOSM macro snapshots
- GNews event snapshot
- SunSirs PP resin benchmark snapshot

## 10. Key Outputs

The result payload currently includes:

- recommendation card
- ranked quotes
- landed-cost scenarios
- selected scenario
- hedge simulation
- risk driver breakdown
- resin benchmark
- quote-vs-market risk records
- news context
- trace URLs when available

## 11. Current Constraints

- analysis run state is still in memory
- some analysis latency depends on live refresh
- product scope is tightly PP-resin-centric
- critical data refresh failures can block analysis
- direct execution integrations are not yet live

## 12. Success Criteria

LintasNiaga is successful in the hackathon context if it can demonstrate:

- correct PDF-to-analysis workflow
- grounded landed-cost comparison
- credible 30-day fan chart behavior
- clear supplier, timing, and hedge recommendation
- visible use of refreshed market/logistics data
- traceable AI explanation

## 13. Roadmap

Future expansion may include:

- direct fintech execution workflows
- broader products and corridors
- persistent database-backed run state
- richer ingestion scheduling
- more complete deployment and operational tooling

## 14. Final Statement

LintasNiaga is designed to prove that AI can improve SME procurement decisions when document extraction, deterministic economics, refreshed external context, bounded reasoning, and traceability are combined into one disciplined workflow.
