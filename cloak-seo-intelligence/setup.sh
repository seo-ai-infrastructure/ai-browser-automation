#!/usr/bin/env bash
# Set up the cloak-seo-intelligence Python environment.
set -euo pipefail

cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"

if [[ ! -d ".venv" ]]; then
  echo "==> Creating virtualenv (.venv)"
  "$PYTHON" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Installing dependencies"
pip install --upgrade pip
pip install -r requirements.txt

if [[ ! -f ".env" ]]; then
  echo "==> No .env found; creating one from .env.example"
  cp .env.example .env
  echo "    Edit .env before running ./run.sh bootstrap"
fi

echo "==> Done. Activate with: source .venv/bin/activate"
