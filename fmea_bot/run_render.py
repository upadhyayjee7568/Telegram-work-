"""Render-compatible launcher with optional bot thread + HTTP health server."""
from __future__ import annotations

import asyncio
import os
import threading
import traceback
import fcntl
from flask import Flask

from bot import main as run_bot

app = Flask(__name__)
BOT_LOCK_FILE = "/tmp/fmea_telegram_bot.lock"


@app.get("/")
def root():
    return "FMEA bot is running", 200


@app.get("/healthz")
def healthz():
    return "ok", 200


def _start_bot() -> None:
    """Run bot in background thread with a dedicated asyncio event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        run_bot()
    except Exception:
        traceback.print_exc()
    finally:
        try:
            loop.close()
        except Exception:
            pass


if __name__ == "__main__":
    enable_bot_thread = os.getenv("ENABLE_BOT_THREAD", "true").strip().lower() in {"1", "true", "yes", "on"}
    if enable_bot_thread:
        try:
            lock_fp = open(BOT_LOCK_FILE, "w")
            fcntl.flock(lock_fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            t = threading.Thread(target=_start_bot, daemon=True)
            t.start()
            print("Bot thread started with exclusive local lock.")
        except OSError:
            print("Bot thread not started: another local process already holds bot lock.")
    else:
        print("ENABLE_BOT_THREAD is false; only HTTP health server will run.")

    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
