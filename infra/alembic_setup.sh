#!/usr/bin/env bash
set -euo pipefail
source ~/.venvs/mongolia-capital-markets/bin/activate
PROJ="/mnt/c/Users/CameronThomas/OneDrive - Meridian Universal/Documents/02_Agent Projects/Local Capital Markets/mongolia-capital-markets"

# Init alembic in Linux fs to avoid NTFS chmod errors
TMPWORK=$(mktemp -d)
cd "$TMPWORK"
alembic init migrations
sed -i 's|sqlalchemy.url = .*|sqlalchemy.url = %(DATABASE_URL)s|' alembic.ini

# Copy only text files to OneDrive project path
cp alembic.ini "$PROJ/backend/alembic.ini"
mkdir -p "$PROJ/backend/migrations/versions"
cp migrations/env.py "$PROJ/backend/migrations/env.py"
cp migrations/README "$PROJ/backend/migrations/README"
cp migrations/script.py.mako "$PROJ/backend/migrations/script.py.mako"

rm -rf "$TMPWORK"
echo "Alembic initialised — files in backend/"
ls "$PROJ/backend/migrations/"
