.PHONY: dev-web dev-api dev test-web test-api test lint ingest-all

# Development servers
dev-web:
	cd apps/web && pnpm dev

dev-api:
	cd apps/api && source .venv/Scripts/activate && uvicorn app.main:app --reload --port 8000

dev:
	@echo "Run 'make dev-api' and 'make dev-web' in separate terminals"

# Testing
test-api:
	cd apps/api && source .venv/Scripts/activate && pytest -v

test-web:
	cd apps/web && pnpm vitest run

test: test-api test-web

# Linting
lint:
	cd apps/api && source .venv/Scripts/activate && python -m py_compile app/main.py
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
