.PHONY: setup migrate ingest-mse ingest-otc serve-backend serve-frontend test lint

# Venv lives in the WSL2 Linux filesystem to avoid NTFS permission issues.
# On a fresh clone inside WSL2, run: bash infra/wsl2_setup.sh
VENV := $(HOME)/.venvs/mongolia-capital-markets
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

setup:
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env from .env.example — fill in your credentials"; fi
	@echo "Venv is managed at $(VENV). Run 'bash infra/wsl2_setup.sh' to create it."

migrate:
	cd backend && $(VENV)/bin/alembic upgrade head

ingest-mse:
	$(PYTHON) scripts/ingest_mse.py

ingest-otc:
	$(PYTHON) scripts/ingest_otc.py

serve-backend:
	$(VENV)/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

serve-frontend:
	cd frontend && npm run dev

test:
	$(VENV)/bin/pytest tests/ -v

lint:
	$(VENV)/bin/ruff check backend/ scripts/ tests/
