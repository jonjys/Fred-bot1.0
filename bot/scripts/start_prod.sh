#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python3 scripts/prod_preflight.py
exec freqtrade trade \
  --userdir user_data \
  -c user_data/config.json \
  -c user_data/PROD_CONFIG.json \
  --strategy FredbV2ProdStrategy
