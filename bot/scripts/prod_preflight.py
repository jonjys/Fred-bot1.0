"""Fail-closed checks before starting Fredb with real funds."""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
base = json.loads((ROOT / "user_data/config.json").read_text())
prod = json.loads((ROOT / "user_data/PROD_CONFIG.json").read_text())
lock = json.loads((ROOT / "user_data/PROD_LOCK.json").read_text())
prod_strategy = json.loads((ROOT / "user_data/strategies/FredbV2ProdStrategy.json").read_text())
params = prod_strategy["params"]
errors = []

if params["buy"].get("buy_adx") != lock["params"]["buy_adx"]:
    errors.append("buy_adx differs from PROD LOCK v1")
if round(params["stoploss"].get("stoploss") * 100, 8) != lock["params"]["stoploss"]:
    errors.append("stoploss differs from PROD LOCK v1")
if prod_strategy.get("prod_lock") != f"PROD LOCK {lock['version']}":
    errors.append("production strategy file is not marked PROD LOCK v1")
if int(prod.get("max_open_trades", 0)) > lock["risk"]["max_open_trades"]:
    errors.append("max_open_trades exceeds production lock")

live_requested = os.getenv("FREQTRADE__DRY_RUN", "true").lower() == "false"
if live_requested:
    if os.getenv("LIVE_TRADING_ACK") != f"PROD LOCK {lock['version']}":
        errors.append("LIVE_TRADING_ACK must equal 'PROD LOCK v1'")
    for key in ("FREQTRADE__EXCHANGE__KEY", "FREQTRADE__EXCHANGE__SECRET"):
        if not os.getenv(key):
            errors.append(f"missing {key}")
    has_telegram = bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))
    has_webhook = bool(os.getenv("FREQTRADE__WEBHOOK__URL"))
    if not (has_telegram or has_webhook):
        errors.append("configure Telegram or Discord-compatible webhook alerts")

if errors:
    print("PRODUCTION PREFLIGHT FAILED:\n- " + "\n- ".join(errors), file=sys.stderr)
    raise SystemExit(1)
print(f"Production preflight OK (PROD LOCK {lock['version']}, live_requested={live_requested})")
