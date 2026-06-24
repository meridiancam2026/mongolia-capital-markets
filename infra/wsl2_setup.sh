#!/usr/bin/env bash
# Stage 1 WSL2 setup script — run once inside Ubuntu WSL2
# Usage: bash infra/wsl2_setup.sh
set -euo pipefail

PROJECT_DIR="/mnt/c/Users/CameronThomas/OneDrive - Meridian Universal/Documents/02_Agent Projects/Local Capital Markets/mongolia-capital-markets"

echo "=== Step 1: System packages ==="
sudo apt-get update -qq
sudo apt-get install -y \
  python3 python3-venv python3-pip \
  build-essential curl git unzip \
  libpq-dev gnupg ca-certificates

echo "=== Step 2: Node.js 18 ==="
if ! command -v node &>/dev/null || [[ "$(node --version)" != v18* ]]; then
  curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi
echo "Node: $(node --version)  npm: $(npm --version)"

echo "=== Step 3: PostgreSQL 14 + TimescaleDB ==="
if ! command -v psql &>/dev/null; then
  # PostgreSQL apt repo
  sudo apt-get install -y postgresql-common
  sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y

  sudo apt-get install -y postgresql-14

  # TimescaleDB repo
  curl -fsSL https://packagecloud.io/timescale/timescaledb/gpgkey | \
    sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/timescaledb.gpg
  echo "deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -cs 2>/dev/null || echo noble) main" | \
    sudo tee /etc/apt/sources.list.d/timescaledb.list
  sudo apt-get update -qq
  sudo apt-get install -y timescaledb-2-postgresql-14

  sudo timescaledb-tune --quiet --yes
fi

sudo service postgresql start

# Create DB user and database (idempotent)
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='mongolia_user'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE USER mongolia_user WITH PASSWORD 'dev_password_change_me';"

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='mongolia'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE DATABASE mongolia OWNER mongolia_user;"

sudo -u postgres psql -d mongolia -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

echo "PostgreSQL: $(psql --version)"
echo "TimescaleDB: $(sudo -u postgres psql -d mongolia -t -c "SELECT extversion FROM pg_extension WHERE extname='timescaledb';" | tr -d ' ')"

echo "=== Step 4: Redis 7 ==="
if ! command -v redis-cli &>/dev/null; then
  curl -fsSL https://packages.redis.io/gpg | \
    sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
  echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] \
    https://packages.redis.io/deb $(lsb_release -cs 2>/dev/null || echo noble) main" | \
    sudo tee /etc/apt/sources.list.d/redis.list
  sudo apt-get update -qq
  sudo apt-get install -y redis
fi

sudo service redis-server start
redis-cli ping  # expect PONG

echo "=== Step 5: Python virtual environment ==="
cd "$PROJECT_DIR"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip -q
pip install -q \
  fastapi "uvicorn[standard]" \
  asyncpg "sqlalchemy[asyncio]" alembic \
  redis \
  playwright \
  requests beautifulsoup4 \
  python-dotenv \
  pytest pytest-asyncio httpx \
  "celery[redis]" \
  ruff

playwright install chromium

pip freeze > backend/requirements.txt
echo "requirements.txt written"

echo "=== Step 6: Alembic init ==="
cd backend
if [ ! -f alembic.ini ]; then
  alembic init migrations
  # Patch alembic.ini to use env var
  sed -i 's|sqlalchemy.url = .*|sqlalchemy.url = %(DATABASE_URL)s|' alembic.ini
  echo "Alembic initialised — edit backend/migrations/env.py to load .env"
fi
cd ..

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Copy .env.example to .env and fill in credentials:"
echo "     cp .env.example .env && nano .env"
echo "  2. Run database migrations (after Stage 5 migration files are added):"
echo "     make migrate"
echo "  3. Start services: sudo service postgresql start && sudo service redis-server start"
echo ""
echo "Verification:"
sudo -u postgres psql -d mongolia -c "\dx" | grep timescaledb
redis-cli ping
python3 --version
node --version
