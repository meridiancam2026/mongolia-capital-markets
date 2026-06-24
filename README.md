# Mongolia Capital Markets Dashboard

A live dashboard for Mongolian Stock Exchange (MSE) equities, MASD OTC bonds, Bank of Mongolia macro data, and FRC regulatory statistics.

## Requirements

- Windows 11 with WSL2 (Ubuntu 26.04 LTS)
- Python 3.10+ (inside WSL2)
- Node.js 18+ (inside WSL2)
- PostgreSQL 14+ with TimescaleDB (inside WSL2)
- Redis 7 (inside WSL2)

## Quick Start (inside WSL2 terminal)

```bash
# 1. Navigate to the project
cd "/mnt/c/Users/CameronThomas/OneDrive - Meridian Universal/Documents/02_Agent Projects/Local Capital Markets/mongolia-capital-markets"

# 2. Set up the environment (creates .venv, installs deps, copies .env.example → .env)
make setup

# 3. Edit .env with your actual credentials
nano .env

# 4. Run database migrations (Stage 5)
make migrate

# 5. Start the backend API
make serve-backend

# 6. In a second terminal, start the frontend
make serve-frontend
```

## Services

| Service    | Port  | Notes                          |
|------------|-------|--------------------------------|
| FastAPI    | 8000  | `make serve-backend`           |
| React/Vite | 5173  | `make serve-frontend`          |
| PostgreSQL | 5432  | Started via `sudo service postgresql start` |
| Redis      | 6379  | Started via `sudo service redis-server start` |

## WSL2 Service Startup

WSL2 services don't auto-start. Run these once per WSL2 session:

```bash
sudo service postgresql start
sudo service redis-server start
```

## Project Structure

```
mongolia-capital-markets/
├── backend/          FastAPI app and Alembic migrations
├── frontend/         React + Vite app
├── scripts/          Data ingestion scripts (MSE, OTC, BOM)
├── db/migrations/    Raw SQL migration files
├── infra/            Dockerfile and docker-compose (Stage 9)
├── data/             Seed files (FRC stats, securities list)
├── tests/            pytest test suite
└── logs/             Runtime logs (gitignored)
```

## Data Sources

See `DATA_SOURCES.md` for licensing status of each data provider.

## Development Stages

See `../Website Development Stages.md` for the full 10-stage build plan.
