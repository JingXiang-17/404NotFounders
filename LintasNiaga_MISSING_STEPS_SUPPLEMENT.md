# LintasNiaga — MISSING STEPS SUPPLEMENT

> Paste these into the main playbook at the marked insertion points, or read alongside it.
> This covers everything the Claude Code version had that the Antigravity version skipped.

---

## SUPPLEMENT A — Antigravity Installation & First Launch (before Setup S1)

If ANY teammate hasn't installed Antigravity yet:

1. Go to https://antigravity.google
2. Click **Download** → pick your OS (Mac / Windows / Linux)
3. Run the installer
4. First launch → it asks some questions:
   - "Import settings from VS Code or Cursor?" → pick **Import from VS Code** if you have extensions you like, otherwise **Start Fresh**
   - "Select theme" → pick **Dark** (matches our product aesthetic)
   - "Agent Manager configuration" → this is crucial:
     - Left side: pick **Agent-Assisted Development** (you stay in control, agent automates safe actions)
     - Right side: Terminal Policy → **Auto** (agent runs standard terminal commands without asking you every time)
   - Click **Next**
   - "Sign in with Google" → use your Google account that has AI Pro subscription
   - Antigravity loads with Gemini 3 Pro as the agent brain
5. Verify: top-right should show your Google account avatar and "Gemini 3.1 Pro" as the active model
6. Open File → Open Folder → navigate to your cloned `lintasniaga/` folder → Open

**How to switch between Editor and Manager:**
- Bottom-left of Antigravity: you'll see two icons — a code editor icon and a grid/dashboard icon
- Click the grid icon → **Manager Surface** (dispatch parallel agents)
- Click the code icon → **Editor View** (normal coding with sidebar chat)
- Keyboard: `Cmd+Shift+P` → type "Manager" → "Open Agent Manager"
- In Editor: `Cmd+L` opens/closes the AI chat sidebar

**How to use Planning mode vs Fast mode:**
- In the Editor chat sidebar, at the top of the input box, you'll see a toggle: **Fast** | **Planning**
- For simple tasks (fix a typo, add one import): use **Fast**
- For complex tasks (build a whole service, create multiple files): use **Planning**
- Planning mode: agent shows you a step-by-step plan first, you click **Approve** before it writes code

---

## SUPPLEMENT B — Langfuse Account Setup (detailed clicks)

This was in the Claude Code version but missing from the Antigravity one.

1. Go to https://cloud.langfuse.com
2. Click **Sign Up** → use GitHub or Google
3. After login, you land on the dashboard
4. Click **+ New Project** (top-left or center)
5. Project name: `lintasniaga` → Create
6. You're now inside the project dashboard
7. Left sidebar → click the **gear icon** (Settings)
8. Click **API Keys** tab
9. Click **+ Create new API key**
10. Name it `hackathon-build`
11. You'll see THREE values displayed — **copy ALL THREE right now** (you won't see the secret again):
    - `LANGFUSE_PUBLIC_KEY` — starts with `pk-lf-...`
    - `LANGFUSE_SECRET_KEY` — starts with `sk-lf-...`
    - `LANGFUSE_HOST` — this is `https://cloud.langfuse.com`
12. Paste these into `apps/api/.env`

**How to verify traces are working (do this on Day 1 after first GLM call):**
1. Go to https://cloud.langfuse.com
2. Click your `lintasniaga` project
3. Left sidebar → **Traces**
4. You should see a trace for each GLM-5.1 call
5. Click into a trace → you'll see:
   - Input messages (what you sent to GLM)
   - Output (what GLM returned)
   - Thinking tokens (if thinking mode was enabled — shown separately)
   - Latency (how long the call took)
   - Token count (input + output + reasoning)
   - Cost estimate
6. **Bookmark this Traces URL** — you'll show it in your pitch video as proof of AI traceability

---

## SUPPLEMENT C — OpenWeatherMap Account Setup

1. Go to https://openweathermap.org
2. Click **Sign Up** → email + password → verify email
3. After login → click your username (top right) → **My API Keys**
4. You'll see a default key already generated
5. Copy it → paste into `apps/api/.env` as `OPENWEATHER_API_KEY`
6. Free tier gives 1,000 calls/day — more than enough
7. Test it works:
```bash
curl "https://api.openweathermap.org/data/2.5/weather?lat=29.87&lon=121.55&appid=YOUR_KEY"
```
This should return weather data for Ningbo port.

**Note:** Weather ingestion is Phase 2 in your architecture. Don't build it on Day 1. Only build it if you have spare time on Day 3.

---

## SUPPLEMENT D — Stitch 2.0 → DESIGN.md → Antigravity Workflow

The first playbook used this as a core workflow. Here's how to do it with Antigravity:

### Step 1: Generate designs in Stitch
1. Go to https://stitch.withgoogle.com
2. Sign in with Google (same account as Antigravity)
3. Click **+ New Project**
4. Click **Create with text**

### Step 2: Paste this prompt for the Results screen (the most important screen)

```
Design a dark fintech analysis results screen for "LintasNiaga" — a procurement decision copilot for Malaysian PP Resin importers.

Brand: electric teal #0DFFD6 accent on very dark charcoal #06060A background. Cards are #111116 with 1px #1A1A24 border. Text #F0F0F5 primary, #8888A0 secondary. Border radius 12px cards, 8px buttons.

Three-column layout:

LEFT (45%): Area chart titled "MYR/USD 90-Day FX Forecast" with three overlapping semi-transparent teal gradient bands (p10 lightest, p50 medium, p90 darkest). Below: a slider labeled "Hedge Ratio" from 0% to 100% with a teal thumb. Below slider: text "At 70% hedge: RM 1,205/MT landed (p50)".

CENTER (35%): Three supplier cards stacked vertically. Top card has a glowing teal border and "RECOMMENDED" pill badge. Shows: "Sinopec Trading" with 🇨🇳, "RM 1,145/MT landed", "RM 23,200 saved vs cheapest", timing "Lock Now", hedge "70%". An expandable "Cost breakdown" section. Cards #2 and #3 are dimmer with "+RM 35/MT vs winner" delta text.

RIGHT (20%): Dark card titled "AI Analyst" with numbered reasoning steps: "1. Sinopec offers lowest p50 landed cost...", "2. FX volatility favors USD hedge...", "3. Reliability score 0.91 reduces delay risk...". A yellow-bordered caveat card "Note: MOQ of 120MT exceeds your 100MT requirement". A link "View Langfuse Trace →".

Desktop only, no mobile needed. Make it look like Bloomberg meets Stripe — data-dense but clean.
```

### Step 3: Generate the upload screen
New screen in same project → paste:

```
Design a dark fintech file upload screen for LintasNiaga. Same brand colors.

Top: a horizontal stepper with 4 steps — "Upload Quotes" (active, teal), "Review", "Analysis", "Decision" — connected by thin lines.

Center: a large dashed-border rectangle (teal dashed border, #111116 fill) with a cloud-upload icon and text "Drop up to 5 FOB PP Resin quote PDFs here". Below the drop zone: three uploaded file cards showing filename, a green checkmark, and extracted supplier name + price.

Below: two form fields side by side — "Required Quantity (MT)" number input and "Urgency" dropdown (Normal / Urgent).

Bottom right: "Continue to Review" button in teal, and a ghost "Save Draft" button.
```

### Step 4: Export DESIGN.md
1. In Stitch, top-right menu (three dots) → **Export**
2. Choose **DESIGN.md**
3. Download the file
4. Save it as `DESIGN.md` in your repo root (next to `.antigravity/rules.md`)
5. Commit: `git add DESIGN.md && git commit -m "design: Stitch 2.0 DESIGN.md export"`

### Step 5: Tell Antigravity to use it
In your `.antigravity/rules.md`, add this line at the top:

```markdown
## Design System
Read DESIGN.md in the repo root for all color tokens, typography, spacing, and component patterns. Apply these to every frontend component. Never hardcode colors — use the CSS variables defined in DESIGN.md.
```

Now every time Antigravity builds a frontend component, it reads DESIGN.md and follows your brand.

### Step 6: (Optional) Connect Stitch MCP for real-time sync
If Stitch MCP is available:
1. In Antigravity → Settings → MCP Servers
2. Click **+ Add Server**
3. Server command: `npx -y @google-labs/stitch-mcp`
4. Name: `stitch`
5. Save and restart Antigravity

Now you can reference Stitch designs directly: type `@stitch` in the chat to pull design context.

**If Stitch MCP doesn't work or isn't available yet:** the DESIGN.md file method above is sufficient. Claude Code's Stitch MCP was also experimental — the file-based approach is more reliable.

---

## SUPPLEMENT E — Nano Banana Pro Image Generation (all 5 quote PDFs + hero image)

### Hero image for landing page (optional but impressive)

Go to https://gemini.google.com → switch model to Gemini 2.5 Pro or 3 Pro at the top.

**Paste this prompt:**
```
Generate a premium dark fintech hero illustration. A sleek abstract 3D globe on a near-black background (#06060A). Continents are rendered in deep teal (#0D3F38). Three glowing electric teal (#0DFFD6) arc lines connect points representing Kuala Lumpur, Ningbo (China), Bangkok (Thailand), and Jakarta (Indonesia). Small pulse dots travel along each arc. Subtle teal atmospheric glow around the globe. Minimalist, clean, no text, no logos. The style should feel like Bloomberg Terminal meets Stripe — premium, data-oriented, not playful. Output in landscape 1920x1080. High detail.
```

Download → save as `apps/web/public/hero-globe.png`

In your landing page component, reference it:
```tsx
<img src="/hero-globe.png" alt="" className="absolute inset-0 w-full h-full object-cover opacity-30" />
```

### All 5 mock quote PDFs (detailed prompts)

You need these as test fixtures AND demo materials. Generate each in Gemini:

**Quote 1 prompt (Ningbo Precision Plastics):**
```
Generate a realistic scanned business document image. Slightly off-white paper, monochrome with navy accents. It's a supplier quotation.

Letterhead: "Ningbo Precision Plastics Co. Ltd."
Address: No. 88 Beilun Industrial Zone, Ningbo, Zhejiang 315800, China
Quotation #: NPP-Q-2026-0412
Date: April 15, 2026
To: Teknologi Rapid Sdn Bhd, No. 12 Jalan Perindustrian, 42100 Klang, Selangor, Malaysia

Items table:
| Item | Description | Qty | Unit Price | Currency |
| 1 | Polypropylene Resin (PP Homopolymer, MFR 12g/10min) HS 3902.10 | 100 MT | 1,180.00 | USD |

Terms:
- Incoterm: FOB Ningbo
- Payment: T/T 30 days after B/L date
- MOQ: 80 MT
- Lead time: 35 days
- Validity: 30 days
- Packing: 25kg bags, palletized

Signature block: "Wang Xiaoming, Sales Manager" with a signature scribble.
Make it look like a real scanned document with slight paper texture.
```

**Quote 2 prompt (Sinopec Trading):**
```
Same style as above but for:
Letterhead: "Sinopec Chemical Trading (Shenzhen) Co. Ltd."
Address: Block A, Petrochemical Tower, Nanshan District, Shenzhen 518000, China
Quotation #: SCT-2026-0891
Date: April 14, 2026
Same buyer.
Items: PP Resin (Injection Grade) HS 3902.10 | 100 MT | USD 1,145.00/MT
Incoterm: FOB Shenzhen (Yantian)
Payment: T/T 60 days
MOQ: 120 MT
Lead time: 30 days
Validity: 21 days
```

**Quote 3 prompt (Thai Polyethylene):**
```
Same style but for:
Letterhead: "Thai Polyethylene Co. Ltd."
Address: 789 Moo 5, Map Ta Phut Industrial Estate, Rayong 21150, Thailand
Quotation #: TPE-Q-26-0234
Date: April 16, 2026
Items: PP Resin (Film Grade) HS 3902.10 | 100 MT | USD 1,210.00/MT
Incoterm: FOB Laem Chabang (Bangkok)
Payment: T/T 30 days
MOQ: 50 MT
Lead time: 18 days
Validity: 30 days
```

**Quote 4 prompt (PT Chandra Asri) — the "cheap but risky" one:**
```
Same style but for:
Letterhead: "PT Chandra Asri Petrochemical Tbk."
Address: Wisma Barito Pacific, Jl. Letjen S. Parman Kav. 62-63, Jakarta 11410, Indonesia
Quotation #: CA-EXP-2026-0156
Date: April 13, 2026
Items: PP Resin (General Purpose) HS 3902.10 | 100 MT | USD 1,095.00/MT
Incoterm: FOB Tanjung Priok (Jakarta)
Payment: T/T 45 days
MOQ: 100 MT
Lead time: 22 days
Validity: 14 days
Note at bottom: "Subject to stock availability at time of order confirmation"
```

**Quote 5 prompt (Zhejiang Borealis) — the CNY-denominated one:**
```
Same style but for:
Letterhead: "Zhejiang Borealis New Materials Co. Ltd."
Address: No. 168 Binhai Avenue, Zhenhai District, Ningbo 315200, China
Quotation #: ZBN-2026-Q0078
Date: April 15, 2026
Items: PP Resin (Raffia Grade) HS 3902.10 | 100 MT | CNY 8,350.00/MT
Note: Price quoted in Chinese Yuan (CNY), not USD
Incoterm: FOB Ningbo
Payment: T/T 30 days
MOQ: 60 MT
Lead time: 40 days
Validity: 30 days
```

**After generating all 5 images:**
1. Download each image
2. Convert to PDF:
   - **Mac:** Open in Preview → File → Export as PDF
   - **Windows:** Open in Photos → Print → Microsoft Print to PDF
   - **Any OS:** Go to https://www.ilovepdf.com/jpg_to_pdf → upload → download
3. Save to:
   - `tests/fixtures/supplier-quotes/quote_1_ningbo_usd1180.pdf`
   - `tests/fixtures/supplier-quotes/quote_2_sinopec_usd1145.pdf`
   - `tests/fixtures/supplier-quotes/quote_3_thai_usd1210.pdf`
   - `tests/fixtures/supplier-quotes/quote_4_chandra_usd1095.pdf`
   - `tests/fixtures/supplier-quotes/quote_5_zhejiang_cny8350.pdf`
4. Also copy to `demo/quotes/` with the same names (for easy demo access)
5. Commit: `git add tests/fixtures/ demo/ && git commit -m "fixtures: 5 mock supplier quote PDFs"`

### Expected extraction JSON fixtures

Create these so you can test extraction accuracy WITHOUT calling GLM every time.

Create `tests/fixtures/expected-extractions/quote_1_expected.json`:
```json
{
  "supplier_name": "Ningbo Precision Plastics Co. Ltd.",
  "origin_port_or_country": "Ningbo",
  "incoterm": "FOB",
  "unit_price": 1180.0,
  "currency": "USD",
  "moq": 80,
  "lead_time_days": 35,
  "payment_terms": "T/T 30 days"
}
```

Create similar files for quotes 2-5. These are your ground truth for testing extraction quality.

---

## SUPPLEMENT F — Backend Testing Setup (detailed)

### Install test dependencies (if not already done)
```bash
cd apps/api
source .venv/bin/activate
uv pip install pytest pytest-asyncio pytest-cov httpx  # httpx for TestClient
```

### Create test configuration
Create `apps/api/pytest.ini`:
```ini
[pytest]
testpaths = tests
asyncio_mode = auto
```

Create `apps/api/tests/__init__.py` (empty file — needed for pytest to find tests)

Create `apps/api/tests/conftest.py`:
```python
import pytest
from app.core.config import Settings

@pytest.fixture
def test_settings():
    """Return settings pointing to test fixtures."""
    return Settings(
        REFERENCE_DIR="../../data/reference",
        SNAPSHOT_DIR="../../data/snapshots",
        SQLITE_PATH=":memory:",
        MODEL_API_KEY="test-key-not-real",
        MODEL_BASE_URL="https://api.z.ai/api/paas/v4/",
        MODEL_NAME="glm-5.1",
    )

@pytest.fixture
def sample_extracted_quote():
    """A known-good extracted quote for testing."""
    from app.schemas.quote import ExtractedQuote
    return ExtractedQuote(
        quote_id="test-q1",
        upload_id="test-u1",
        supplier_name="Ningbo Precision Plastics Co. Ltd.",
        origin_port_or_country="Ningbo",
        incoterm="FOB",
        unit_price=1180.0,
        currency="USD",
        moq=80,
        lead_time_days=35,
        payment_terms="T/T 30 days",
        extraction_confidence=0.92,
    )
```

### How to run tests
```bash
cd apps/api
source .venv/bin/activate

# Run all tests
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=term-missing -v

# Run specific test file
pytest tests/test_quote_validation.py -v

# Run and stop on first failure
pytest -x -v
```

### What tests MUST exist before submission

| Test file | What it tests | Priority |
|-----------|--------------|----------|
| `tests/test_reference_data.py` | All 4 JSON files load and validate as Pydantic models | Day 1 |
| `tests/test_quote_validation.py` | FOB accepted, CIF rejected, missing fields caught, unsupported corridor rejected | Day 1 |
| `tests/test_cost_engine.py` | Known inputs (quote + freight + tariff + FX) produce expected RM output | Day 2 |
| `tests/test_ranking.py` | 3 LandedCostResults rank correctly by p50 | Day 2 |
| `tests/test_fx_simulation.py` | FX simulation produces p10 < p50 < p90 and correct array lengths | Day 2 |
| `tests/test_holidays.py` | MY and CN holidays generated for 2026 | Day 1 |
| `tests/test_snapshot_envelope.py` | Snapshot envelope validates correctly, rejects bad status values | Day 1 |

### Sample test — test_quote_validation.py

Tell Antigravity in Editor:
```
Create apps/api/tests/test_quote_validation.py with these test cases:

1. test_valid_fob_quote — a complete FOB quote with all fields → status should be "valid"
2. test_reject_cif_quote — same quote but incoterm="CIF" → status should be "invalid_out_of_scope", reason should mention "Only FOB supported"
3. test_reject_missing_price — quote with unit_price=None → status should be "invalid_fixable", missing_fields should include "unit_price"
4. test_reject_unsupported_country — origin="Vietnam" → status should be "invalid_out_of_scope"
5. test_accept_cny_currency — quote with currency="CNY" → should be valid (CNY is supported)
6. test_reject_eur_currency — currency="EUR" → should be invalid

Use the sample_extracted_quote fixture from conftest.py and modify fields for each test case.
```

---

## SUPPLEMENT G — Frontend Testing Setup

### Vitest (unit/component tests)
```bash
cd apps/web
pnpm add -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

Create `apps/web/vitest.config.ts`:
```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

Create `apps/web/src/test/setup.ts`:
```typescript
import '@testing-library/jest-dom'
```

Run: `pnpm vitest run`

### Playwright (E2E — only if time permits on Day 3)
```bash
cd apps/web
pnpm add -D @playwright/test
npx playwright install chromium
```

This is lower priority than pytest backend tests.

---

## SUPPLEMENT H — MCP Server Configuration in Antigravity

### How to add MCP servers
1. In Antigravity → click the **gear icon** (bottom-left) → **Settings**
2. Scroll to **MCP Servers** section
3. Click **+ Add Server**

### Recommended MCP servers for this project

**GitHub MCP (for PR management from Antigravity):**
- Click + Add Server
- Transport: **HTTP**
- URL: `https://api.githubcopilot.com/mcp/`
- Name: `github`
- Click Save
- When prompted, authorize with your GitHub account

**Supabase MCP (skip for now — you're using SQLite locally):**
Don't add this. Your tech stack says SQLite for hackathon, Supabase later.

**Stitch MCP (optional — only if you want real-time design sync):**
- Click + Add Server
- Transport: **Command**
- Command: `npx`
- Args: `-y @google-labs/stitch-mcp`
- Name: `stitch`
- Click Save

**Note:** MCP servers in Antigravity work the same way as in Claude Code or Cursor. The agent can access MCP tools via `@server-name` in the chat.

---

## SUPPLEMENT I — Makefile for Quick Commands

Your tech stack doc specifies a root Makefile. Create `Makefile` in repo root:

```makefile
.PHONY: dev-web dev-api dev test-web test-api test lint ingest-all

# Development servers
dev-web:
	cd apps/web && pnpm dev

dev-api:
	cd apps/api && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

dev:
	@echo "Run 'make dev-api' and 'make dev-web' in separate terminals"

# Testing
test-api:
	cd apps/api && source .venv/bin/activate && pytest -v

test-web:
	cd apps/web && pnpm vitest run

test: test-api test-web

# Linting
lint:
	cd apps/api && source .venv/bin/activate && python -m py_compile app/main.py
	cd apps/web && pnpm build

# Ingestion
ingest-all:
	@echo "Loading reference data..."
	curl -s -X POST http://localhost:8000/ingest/reference/load | python -m json.tool
	@echo "\nFetching USDMYR..."
	curl -s -X POST http://localhost:8000/ingest/market/fx -H "Content-Type: application/json" -d '{"pair":"USDMYR"}' | python -m json.tool
	@echo "\nFetching CNYMYR..."
	curl -s -X POST http://localhost:8000/ingest/market/fx -H "Content-Type: application/json" -d '{"pair":"CNYMYR"}' | python -m json.tool
	@echo "\nFetching THBMYR..."
	curl -s -X POST http://localhost:8000/ingest/market/fx -H "Content-Type: application/json" -d '{"pair":"THBMYR"}' | python -m json.tool
	@echo "\nFetching Brent..."
	curl -s -X POST http://localhost:8000/ingest/market/energy -H "Content-Type: application/json" -d '{"symbol":"BZ=F"}' | python -m json.tool
	@echo "\nGenerating holidays..."
	curl -s -X POST http://localhost:8000/ingest/holidays | python -m json.tool
	@echo "\nAll ingestion complete."
```

Usage:
```bash
# Terminal 1: start backend
make dev-api

# Terminal 2: start frontend
make dev-web

# Terminal 3: run all ingestion
make ingest-all

# Run all tests
make test
```

---

## SUPPLEMENT J — How to Run Frontend + Backend Together

You need TWO terminal windows/tabs open simultaneously.

**Terminal 1 — Backend:**
```bash
cd lintasniaga/apps/api
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```
Leave this running. You'll see request logs here.

**Terminal 2 — Frontend:**
```bash
cd lintasniaga/apps/web
pnpm dev
```
Leave this running. Opens at http://localhost:3000.

**Terminal 3 (optional) — for git, tests, curl commands:**
```bash
cd lintasniaga
# Run tests, commit, etc.
```

In Antigravity, you can also use the built-in terminal:
- View → Terminal (or `Ctrl+\``)
- You can split terminals: right-click terminal tab → Split Terminal
- Run backend in left split, frontend in right split

---

## SUPPLEMENT K — Git Workflow (click-by-click)

### Initial setup (one person does this)
```bash
cd lintasniaga
git checkout -b main  # if not already on main
git push -u origin main
```

### Daily workflow (every teammate)
```bash
# Start of work session
git pull origin main

# Create feature branch
git checkout -b feat/day1-fx-ingestion

# ... do work ...

# Stage and commit
git add -A
git commit -m "feat: FX ingestion provider and service"

# Push
git push origin feat/day1-fx-ingestion

# Go to GitHub → Pull Requests → New Pull Request
# Base: main ← Compare: feat/day1-fx-ingestion
# Title: "feat: FX ingestion provider and service"
# Click Create Pull Request
# Ask one teammate to review → they click "Approve"
# Click "Merge Pull Request" → "Confirm Merge"

# Back in terminal
git checkout main
git pull origin main
```

**Rules:**
- NEVER push directly to main
- Every PR needs 1 approval
- Run `make test` before creating PR
- Use conventional commit messages: `feat:`, `fix:`, `test:`, `chore:`, `docs:`
- Commit OFTEN — at least every 30 minutes during active coding

---

## SUPPLEMENT L — SQLite Table Creation

Your tech stack says SQLite for dynamic app state. Tell Antigravity:

```
Create apps/api/app/models/database.py that:

1. Uses Python's built-in sqlite3 module (no ORM needed for hackathon)
2. Creates these tables on startup if they don't exist:

- quote_uploads: upload_id TEXT PK, filename TEXT, storage_path TEXT, uploaded_at TEXT, status TEXT
- quote_extractions: quote_id TEXT PK, upload_id TEXT FK, supplier_name TEXT, origin_port_or_country TEXT, incoterm TEXT, unit_price REAL, currency TEXT, moq INTEGER, lead_time_days INTEGER, payment_terms TEXT, extraction_confidence REAL, created_at TEXT
- quote_validations: quote_id TEXT PK, status TEXT, reason_codes TEXT (JSON), missing_fields TEXT (JSON), created_at TEXT
- analysis_runs: run_id TEXT PK, quote_ids TEXT (JSON array), quantity_mt REAL, urgency TEXT, hedge_preference TEXT, status TEXT, started_at TEXT, completed_at TEXT
- recommendations: run_id TEXT PK, mode TEXT, winner_quote_id TEXT, backup_quote_id TEXT, timing TEXT, hedge_pct REAL, reasons TEXT (JSON), caveat TEXT, p10 REAL, p50 REAL, p90 REAL, created_at TEXT
- ingest_jobs: job_id TEXT PK, dataset TEXT, source TEXT, started_at TEXT, completed_at TEXT, status TEXT, warnings TEXT (JSON)

3. Provides helper functions: get_db(), init_db()
4. Call init_db() in FastAPI startup event in main.py

Use SQLITE_PATH from config. For tests, use ":memory:".
```

---

## SUPPLEMENT M — Vercel Deploy (detailed clicks)

1. Go to https://vercel.com
2. Click **Sign Up** → use GitHub
3. After login → click **Add New...** → **Project**
4. It shows your GitHub repos → find `lintasniaga` → click **Import**
5. Configure:
   - **Framework Preset:** Next.js (auto-detected)
   - **Root Directory:** click **Edit** → type `apps/web` → confirm
   - **Build Command:** leave as `pnpm build` (auto-detected)
   - **Output Directory:** leave as `.next` (auto-detected)
6. **Environment Variables:** click **Add**
   - Key: `NEXT_PUBLIC_API_BASE_URL`
   - Value: your Render backend URL (e.g., `https://lintasniaga-api.onrender.com`)
7. Click **Deploy**
8. Wait 2-3 minutes. Vercel builds and deploys.
9. You get a URL like `https://lintasniaga-xxxxx.vercel.app`
10. Test it — should show your landing page

---

## SUPPLEMENT N — Render Deploy (detailed clicks)

1. Go to https://render.com
2. Click **Sign Up** → use GitHub
3. After login → click **+ New** → **Web Service**
4. Connect your GitHub repo → find `lintasniaga` → click **Connect**
5. Configure:
   - **Name:** `lintasniaga-api`
   - **Region:** Singapore (closest to Malaysia)
   - **Root Directory:** `apps/api`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Before deploying, generate requirements.txt:
   ```bash
   cd apps/api
   source .venv/bin/activate
   uv pip freeze > requirements.txt
   git add requirements.txt && git commit -m "chore: requirements.txt for Render"
   git push
   ```
7. **Environment Variables:** click **Add Environment Variable** for each one from `apps/api/.env`:
   - `MODEL_API_KEY`, `MODEL_BASE_URL`, `MODEL_NAME`
   - `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`
   - `OPENWEATHER_API_KEY` (if using weather)
   - `SQLITE_PATH` → `/opt/render/project/src/lintasniaga.db`
   - `DATA_DIR` → `/opt/render/project/src/../../data` (adjust based on Render's file structure)
   - `USE_LAST_VALID_SNAPSHOT_ON_FAILURE` → `true`
8. Click **Create Web Service**
9. Wait 3-5 minutes for build + deploy
10. Test: `curl https://lintasniaga-api.onrender.com/health`

**Important Render note:** Render free tier spins down after 15 min of inactivity. The first request after idle takes ~30 seconds. For the demo, visit the health endpoint 1 minute before recording to "warm it up."

---

## SUPPLEMENT O — Snapshot Verification Checklist

After running `make ingest-all`, verify every snapshot file:

```bash
# Check FX snapshots exist and have data
cat data/snapshots/fx/USDMYR_latest.json | python -m json.tool | head -20
# Should show: {"dataset": "fx", "source": "yfinance", "status": "success", "record_count": 250+, "data": [...]}

cat data/snapshots/fx/CNYMYR_latest.json | python -m json.tool | head -5
cat data/snapshots/fx/THBMYR_latest.json | python -m json.tool | head -5

# Check energy
cat data/snapshots/energy/BZ=F_latest.json | python -m json.tool | head -20

# Check holidays
cat data/snapshots/holidays/holidays_latest.json | python -m json.tool | head -20

# Check reference data loads
curl http://localhost:8000/ingest/reference/load | python -m json.tool
# Should show counts for freight_rates, tariffs, ports, supplier_seeds
```

If any snapshot is missing or has `"status": "failed"`:
1. Check the terminal where `uvicorn` is running for error logs
2. Common issues:
   - **yfinance timeout:** retry 2-3 times, it's flaky
   - **Currency pair not found:** try different ticker format (e.g., `MYR=X` instead of `USDMYR=X`)
   - **File permission error:** check SNAPSHOT_DIR path in .env

---

## SUPPLEMENT P — Demo Preparation Checklist (non-demo-process, just prep)

Things to have READY so demo recording goes smoothly (you said we'll do demo together later):

1. **5 quote PDFs** in `demo/quotes/` — named clearly with price in filename
2. **All snapshots populated** — run `make ingest-all` and verify
3. **Frozen snapshot backup** — `cp -r data/snapshots data/snapshots_frozen`
4. **Backend running on Render** — warm it up before demo
5. **Frontend running on Vercel** — verify all pages load
6. **Langfuse has at least 3 traces** — from your test runs, verify they show up
7. **One complete happy-path test** — 3 quotes uploaded, analysis run, recommendation shown
8. **One single-quote test** — 1 quote uploaded, single-quote fallback mode works
9. **Browser bookmarks ready:**
   - Production frontend URL
   - Production API health endpoint
   - Langfuse traces page
   - GitHub repo (public or shared with judges)

---

*End of supplement. Paste relevant sections into the main playbook or keep as a companion doc.*
