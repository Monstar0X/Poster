#!/usr/bin/env bash
# Start the bot, installing the pinned requirements first if the sandbox wiped them.
set -u
cd "$(dirname "$0")"

python - <<'PY' || pip install -r requirements.txt
import importlib, sys
for m in ("pyrogram", "PIL", "numpy", "dotenv", "httpx", "tgcrypto"):
    try:
        importlib.import_module(m)
    except ImportError:
        sys.exit(1)
PY

# stop only this bot's process, matched on its exact command line
for pid in $(pgrep -f "^python main\.py$"); do
    kill "$pid" && echo "stopped old bot (pid $pid)"
done
sleep 2

nohup python main.py > /tmp/bot_run.log 2>&1 &
echo "bot started (pid $!) - log: /tmp/bot_run.log"
