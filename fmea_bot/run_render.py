"""Render-compatible launcher: runs Telegram bot + lightweight HTTP health server."""
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
    t = threading.Thread(target=_start_bot, daemon=True)
    t.start()
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
