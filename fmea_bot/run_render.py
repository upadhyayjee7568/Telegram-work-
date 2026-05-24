"""Render-compatible launcher with optional bot thread + HTTP health server."""
from __future__ import annotations

import os
import threading
from flask import Flask

from bot import main as run_bot

app = Flask(__name__)


@app.get("/")
def root():
    return "FMEA bot is running", 200


@app.get("/healthz")
def healthz():
    return "ok", 200


def _start_bot() -> None:
    run_bot()


if __name__ == "__main__":
    enable_bot_thread = os.getenv("ENABLE_BOT_THREAD", "true").strip().lower() in {"1", "true", "yes", "on"}
    if enable_bot_thread:
        t = threading.Thread(target=_start_bot, daemon=True)
        t.start()
    else:
        print("ENABLE_BOT_THREAD is false; only HTTP health server will run.")

    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
