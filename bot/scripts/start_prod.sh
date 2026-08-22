#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
if [[ -n "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  export FREQTRADE__TELEGRAM__ENABLED=true
  export FREQTRADE__TELEGRAM__TOKEN="$TELEGRAM_BOT_TOKEN"
  export FREQTRADE__TELEGRAM__CHAT_ID="${TELEGRAM_CHAT_ID:?TELEGRAM_CHAT_ID is required}"
fi
python3 scripts/prod_preflight.py
exec freqtrade trade \
  --userdir user_data \
  -c user_data/config.json \
  -c user_data/PROD_CONFIG.json \
  --strategy FredbV2ProdStrategy
