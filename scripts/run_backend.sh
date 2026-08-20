#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
fi

echo "Starting ReturnGuard AI on http://localhost:8000  (dashboard is served at the same URL)"
uvicorn backend.main:app --reload --port 8000
