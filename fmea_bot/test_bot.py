#!/usr/bin/env python3

def test_config():
    from config import BOT_TOKEN, CHANNEL_USERNAME, ADMIN_IDS, ADMIN_USERNAMES
    assert CHANNEL_USERNAME.startswith("@")
    assert isinstance(ADMIN_IDS, list)
    assert isinstance(ADMIN_USERNAMES, set)
    assert isinstance(BOT_TOKEN, str)


def test_database():
    from database import init_database, get_user_stats
    init_database()
    stats = get_user_stats()
    assert "total" in stats


def test_telegram_import():
    from telegram import Bot
    assert Bot is not None
