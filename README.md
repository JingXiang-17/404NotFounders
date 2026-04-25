# 🌍 LintasNiaga 🚀

> **Choose the best-value supplier with less hidden risk.**

LintasNiaga is a procurement decision-support copilot built for Malaysian plastics SMEs that import polypropylene (PP) resin. It turns fragmented supplier PDF quotes and noisy market data into one clear, defensible procurement decision — complete with a supplier recommendation, timing stance, and FX hedge ratio.

---

## 🔗 Quick Links

| Document | Link |
|---|---|
| **📄 PRD (Product)** | [Link to PRD](./docs/official/LintasNiaga_PRD_UMHackathon2026.pdf) |
| **⚙️ SAD (System)** | [Link to SAD](./docs/official/LintasNiaga_SAD_UMHackathon2026.pdf) |
| **🧪 QATD (Testing)** | [Link to QATD](./docs/official/LintasNiaga_STAD_UMHackathon2026.pdf) |
| **📊 Pitching Deck** | [Link to Pitch Deck](./docs/official/LintasNiaga_Slide_Pitch_Deck.pdf) |
| **🎥 10 Minutes Pitching Video** | [Link to Video](https://drive.google.com/file/d/1J79C9tnpJVAfAhyvLtiq49tGgRWkcmBm/view?usp=sharing) |

---

## 👥 Team 404NotFounders

| Name | Role |
|---|---|
| LIM XUAN NING | Product Lead |
| YEW LIENN | Data Lead |
| KOR JING XIANG | Demo Lead |
| NG HONG JON | Frontend Developer |
| OOI FU CHUIN | Backend Developer |

*(UMHackathon 2026, Domain 2)*

---

## 🔄 App Workflow

LintasNiaga walks the user through a focused four-stage workflow:

1. **📥 Upload:** Upload up to five supplier quote PDFs. The system extracts key fields using deterministic extraction with a GLM-5.1 vision fallback.
2. **🔍 Review and Repair:** Extracted fields are surfaced for review. Users can correct values, select order quantity, urgency level, and hedge preference (Balanced / Conservative / Aggressive).
3. **🧠 Analysis:** The backend refreshes live market and logistics context (FX rates, Brent crude, weather risk, macro indicators, news signals) then runs deterministic landed-cost calculations and a 30-day Monte Carlo fan chart, capped off by bounded AI reasoning.
4. **📊 Decision Result:** Receive a single, traceable recommendation:
   - Which supplier to choose (with ranked alternatives)
   - Whether to lock now or wait
   - How much FX exposure to hedge
   - A 30-day landed-cost fan chart with p10 / p50 / p90 bands
   - Downloadable bank-instruction PDF

---

## 🏗️ Architecture Diagram

```mermaid
graph TD
    %% Frontend
    subgraph Frontend [🌐 Next.js Frontend]
        UI[Decision Workspace UI]
        Upload[Quote Upload & Review]
        Results[Fan Chart & Insights]
    end

    %% Backend APIs
    subgraph Backend [⚡ FastAPI Backend]
        API[FastAPI Routes]
        LCC[Deterministic Landed Cost Calculator]
        MC[Monte Carlo Engine]
    end

    %% AI & Orchestration
    subgraph AI_Layer [🤖 AI Orchestration]
        LG[LangGraph Pipeline]
        GLM[ILMU-GLM-5.1 Provider]
        Trace[Langfuse Observability]
    end

    %% Data & External
    subgraph Data [📁 Data & External APIs]
        Local[File-Backed Snapshots & Ref Data]
        Ext[yFinance, OpenWeather, GNews, SunSirs]
    end

    %% Wiring
    UI --> |PDFs / Config| API
    API --> |Validation & Matching| Local
    Local -.-> |Update Snapshots| Ext
    
    API --> |Compute Landed Cost| LCC
    LCC --> |Simulate 2,000 Paths| MC
    
    MC --> |Results & Context| LG
    LG <--> |Reasoning / Justification| GLM
    LG -.-> |Tracing| Trace
    
    LG --> |Bounded Recommendation JSON| API
    API --> |Render Dashboard| Results
```

---

## 🛠️ Setup Guide

### 1. Clone the repository
```bash
git clone https://github.com/JingXiang-17/404NotFounders.git
cd 404NotFounders
```

### 2. Backend Setup
```bash
cd apps/api
python -m venv .venv
source .venv/Scripts/activate  # On Windows
pip install -e .
cp .env.example .env           # Configure your API keys (e.g., ZHIPU_API_KEY)
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd apps/web
pnpm install
pnpm dev
```

The application will be running at `http://localhost:3000`.

---

## 📁 Repository Structure

```text
404NotFounders/
├── apps/
│   ├── api/                 # FastAPI Backend (Routes, Services, Providers, AI Orchestrator)
│   └── web/                 # Next.js Frontend (UI Components, Analysis Flow, Results Dashboard)
├── data/                    # Local Reference & Snapshot Data Storage
├── docs/                    # Architecture Blueprints, PRDs, & Technical Documentation
├── example_pdf/             # Sample Quotation PDFs for Demonstration
├── scripts/                 # Utility Scripts
├── tests/                   # Pytest Suite and Fixtures
├── .agent/                  # AI Agent Skills & Workflows
├── Makefile                 # Development Helper Commands
└── README.md                # Project Documentation
```
