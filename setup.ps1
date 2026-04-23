$ErrorActionPreference = 'SilentlyContinue'

# 1. Create directories
Write-Host "Creating directories..."
New-Item -ItemType Directory -Force -Path apps\web, apps\api, data\reference, data\snapshots\fx, data\snapshots\energy, data\snapshots\weather, data\snapshots\holidays, data\snapshots\opendosm, data\snapshots\news, data\snapshots\resin, data\raw\opendosm, data\raw\news, data\raw\resin_html, data\raw\resin_text, data\tmp | Out-Null
$ErrorActionPreference = 'Stop'

# 2. Backend Setup
Write-Host "Setting up Backend..."
Push-Location apps\api
uv venv
uv pip install fastapi==0.115.0 uvicorn[standard] pydantic==2.* pydantic-settings
uv pip install httpx tenacity orjson aiofiles
uv pip install pandas numpy
uv pip install yfinance holidays gnews trafilatura
uv pip install lxml beautifulsoup4
uv pip install langgraph langchain langchain-openai langfuse
uv pip install pytest pytest-asyncio
uv pip install PyMuPDF
Pop-Location

# 3. Frontend Setup
Write-Host "Setting up Frontend..."
Push-Location apps\web
# Using create-next-app non-interactive params
pnpm create next-app . --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --yes --use-pnpm
pnpm add recharts motion lucide-react zod react-hook-form @hookform/resolvers @tanstack/react-query
npx --yes shadcn@canary init -d
# Added --yes (-y works best with shadcn add via npx)
npx --yes shadcn@canary add button card dialog tabs tooltip badge skeleton slider accordion select input form separator table -y
Pop-Location

Write-Host "Setup Completed successfully."
