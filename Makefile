.PHONY: setup migrate ingest-mse ingest-otc serve-backend serve-frontend test lint

# Copy .env.example if .env doesn't exist, then install Python deps
setup:
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env from .env.example — fill in your credentials"; fi
	python3.10 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r backend/requirements.txt
	.venv/bin/playwright install chromium
	@echo "Setup complete. Activate venv with: source .venv/bin/activate"

migrate:
	.venv/bin/alembic upgrade head

ingest-mse:
	.venv/bin/python scripts/ingest_mse.py

ingest-otc:
	.venv/bin/python scripts/ingest_otc.py

serve-backend:
	.venv/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

serve-frontend:
	cd frontend && npm run dev

test:
	.venv/bin/pytest tests/ -v

lint:
	.venv/bin/ruff check backend/ scripts/ tests/
