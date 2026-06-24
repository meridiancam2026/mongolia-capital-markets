#!/usr/bin/env bash
# Stage 1 WSL2 setup script — run once inside an interactive Ubuntu WSL2 terminal
# Usage: bash infra/wsl2_setup.sh
set -euo pipefail

PROJECT_DIR="/mnt/c/Users/CameronThomas/OneDrive - Meridian Universal/Documents/02_Agent Projects/Local Capital Markets/mongolia-capital-markets"

# Ubuntu 26.04 (noble) is new — some repos fall back to jammy (22.04) packages
CODENAME=$(lsb_release -cs 2>/dev/null || grep VERSION_CODENAME /etc/os-release | cut -d= -f2)
# If repo doesn't support noble yet, fall back to jammy
PG_CODENAME="$CODENAME"
TS_CODENAME="$CODENAME"
REDIS_CODENAME="$CODENAME"

echo "Detected Ubuntu codename: $CODENAME"

echo ""
echo "=== Step 1: System packages ==="
sudo apt-get update -qq
sudo apt-get install -y \
  python3 python3-venv python3-pip \
  build-essential curl git unzip \
  libpq-dev gnupg ca-certificates \
  lsb-release

echo ""
echo "=== Step 2: Node.js 18 ==="
if ! command -v node &>/dev/null; then
  # NodeSource 18.x — supports noble
  curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
  sudo apt-get install -y nodejs
else
  echo "Node.js already installed: $(node --version)"
fi
echo "Node: $(node --version)  npm: $(npm --version)"

echo ""
echo "=== Step 3: PostgreSQL 14 ==="
if ! command -v psql &>/dev/null; then
  # Add PostgreSQL PGDG repo
  sudo apt-get install -y postgresql-common
  # The PGDG script auto-detects the distro; if noble isn't in PGDG yet it falls back gracefully
  sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y || true

  # Try native apt if PGDG script failed
  if ! apt-cache show postgresql-14 &>/dev/null; then
    echo "PGDG repo unavailable for $CODENAME — installing postgresql from Ubuntu universe"
    sudo add-apt-repository -y universe
    sudo apt-get update -qq
  fi

  sudo apt-get install -y postgresql
  PG_VERSION=$(pg_lsclusters -h | awk '{print $1}' | head -1)
  echo "Installed PostgreSQL $PG_VERSION"
else
  PG_VERSION=$(pg_lsclusters -h | awk '{print $1}' | head -1)
  echo "PostgreSQL already installed: version $PG_VERSION"
fi

echo ""
echo "=== Step 4: TimescaleDB ==="
PG_MAJOR=$(pg_lsclusters -h | awk '{print $1}' | head -1)
if ! dpkg -l "timescaledb-*" 2>/dev/null | grep -q "^ii"; then
  # Try to install TimescaleDB; fall back to jammy if noble not supported
  curl -fsSL https://packagecloud.io/timescale/timescaledb/gpgkey | \
    sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/timescaledb.gpg

  for try_codename in "$CODENAME" "noble" "jammy"; do
    echo "Trying TimescaleDB repo for: $try_codename"
    echo "deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $try_codename main" | \
      sudo tee /etc/apt/sources.list.d/timescaledb.list
    sudo apt-get update -qq 2>/dev/null
    if apt-cache show "timescaledb-2-postgresql-$PG_MAJOR" &>/dev/null; then
      sudo apt-get install -y "timescaledb-2-postgresql-$PG_MAJOR"
      echo "TimescaleDB installed for $try_codename"
      break
    fi
  done

  # If TimescaleDB still not installed, warn but don't fail — can be added later
  if ! dpkg -l "timescaledb-*" 2>/dev/null | grep -q "^ii"; then
    echo "WARNING: TimescaleDB package not found for this Ubuntu version."
    echo "         Continuing without TimescaleDB — add it manually or use Docker (Stage 9)."
  else
    sudo timescaledb-tune --quiet --yes || true
  fi
fi

echo ""
echo "=== Step 5: Start PostgreSQL and create database ==="
sudo service postgresql start

sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='mongolia_user'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE USER mongolia_user WITH PASSWORD 'dev_password_change_me';"

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='mongolia'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE DATABASE mongolia OWNER mongolia_user;"

# Enable TimescaleDB extension if available
sudo -u postgres psql -d mongolia -c "CREATE EXTENSION IF NOT EXISTS timescaledb;" 2>/dev/null || \
  echo "NOTE: TimescaleDB extension not available — skipping."

echo ""
echo "=== Step 6: Redis 7 ==="
if ! command -v redis-cli &>/dev/null; then
  curl -fsSL https://packages.redis.io/gpg | \
    sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg

  # Try redis repo; fall back to jammy if noble not supported
  for try_codename in "$CODENAME" "noble" "jammy"; do
    echo "Trying Redis repo for: $try_codename"
    echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] \
https://packages.redis.io/deb $try_codename main" | \
      sudo tee /etc/apt/sources.list.d/redis.list
    sudo apt-get update -qq 2>/dev/null
    if apt-cache show redis &>/dev/null; then
      sudo apt-get install -y redis
      echo "Redis installed for $try_codename"
      break
    fi
  done

  # Fallback: Ubuntu universe has redis-server
  if ! command -v redis-cli &>/dev/null; then
    echo "Redis repo unavailable — installing from Ubuntu universe"
    sudo apt-get install -y redis-server
  fi
fi

sudo service redis-server start
redis-cli ping

echo ""
echo "=== Step 7: Python virtual environment ==="
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
echo "requirements.txt written to backend/requirements.txt"

echo ""
echo "=== Step 8: Alembic init ==="
cd "$PROJECT_DIR/backend"
if [ ! -f alembic.ini ]; then
  alembic init migrations
  sed -i 's|sqlalchemy.url = .*|sqlalchemy.url = %(DATABASE_URL)s|' alembic.ini
  echo "Alembic initialised"
else
  echo "Alembic already initialised"
fi

echo ""
echo "========================================"
echo " Stage 1 Setup Complete"
echo "========================================"
echo ""
echo "Verification:"
echo -n "  PostgreSQL: "; psql --version
echo -n "  Redis:      "; redis-cli --version
echo -n "  Python:     "; python3 --version
echo -n "  Node:       "; node --version
echo -n "  pip:        "; pip --version
echo ""
echo "Next steps:"
echo "  1. Copy .env.example → .env and fill in credentials:"
echo "     cp .env.example .env && nano .env"
echo "  2. After Stage 5 adds migrations, run: make migrate"
echo "  3. Each WSL2 session, start services with:"
echo "     sudo service postgresql start && sudo service redis-server start"
