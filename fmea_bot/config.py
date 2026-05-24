"""Configuration for FMEA bot."""

from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()


def _split_csv(value: str) -> list[str]:
    cleaned = value.replace("\n", ",").replace(" and ", ",")
    return [part.strip() for part in cleaned.split(",") if part.strip()]


def _parse_admin_ids(value: str) -> list[int]:
    ids: list[int] = []
    for raw in _split_csv(value):
        raw = raw.strip()
        if not raw:
            continue
        try:
            ids.append(int(raw))
        except ValueError:
            continue
    return ids


def _parse_admin_usernames(value: str) -> set[str]:
    usernames: set[str] = set()
    for raw in _split_csv(value):
        raw = raw.lower()
        usernames.add(raw[1:] if raw.startswith("@") else raw)
    return usernames


BOT_TOKEN = os.getenv("BOT_TOKEN", "")
_raw_channel_username = os.getenv("CHANNEL_USERNAME", "@FMEA1237802VHKV").strip()
CHANNEL_USERNAME = "@" + _raw_channel_username.rstrip("/").split("/")[-1].lstrip("@") if "t.me/" in _raw_channel_username or _raw_channel_username.startswith("http") else _raw_channel_username
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/FMEA1237802VHKV")
GROUP_LINK = os.getenv("GROUP_LINK", "https://t.me/Fmean756800124876")
_raw_group_username = os.getenv("GROUP_USERNAME", GROUP_LINK).strip()
GROUP_USERNAME = "@" + _raw_group_username.rstrip("/").split("/")[-1].lstrip("@") if "t.me/" in _raw_group_username or _raw_group_username.startswith("http") else _raw_group_username
SUPPORT_LINK = os.getenv("SUPPORT_LINK", "https://t.me/amanjee7568")

ADMIN_IDS = _parse_admin_ids(os.getenv("ADMIN_IDS", "9234906001"))
ADMIN_USERNAMES = _parse_admin_usernames(os.getenv("ADMIN_USERNAMES", "@amanjee7568,@amanjee"))

DB_FILE = os.getenv("DB_FILE", "fmea_database.db")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")

BOT_NAME = os.getenv("BOT_NAME", "Free Money 💰 Earning Adda")
BOT_USERNAME = os.getenv("BOT_USERNAME", "@FMEAN_BOT")
BOT_LINK = os.getenv("BOT_LINK", f"https://t.me/{BOT_USERNAME.lstrip('@')}")
BOT_VERSION = os.getenv("BOT_VERSION", "2.2")

REFERRAL_BONUS = int(os.getenv("REFERRAL_BONUS", "10"))
JOIN_BONUS = int(os.getenv("JOIN_BONUS", "5"))
AUTO_POST_TIMES = [t.strip() for t in os.getenv("AUTO_POST_TIMES", "09:00,14:00,20:00").split(",") if t.strip()]

WELCOME_TEXT = """
🎉 *स्वागत है {name}!* 

╔══════════════════════════╗
║  💰 *Free Money Earning Adda* 💰  ║
╚══════════════════════════╝

✨ *आपका FMEA परिवार में स्वागत है!*

📌 *यहाँ आपको मिलेगा:*
├ 💸 Daily Earning Tips
├ 📱 Online Money Making Methods
├ 🎯 Investment Ideas
├ 💡 Business Tips
├ 🔥 Exclusive Offers & Deals
└ 📊 Market Updates

🎁 *Join Bonus:* +{bonus} Points मिले!

👇 *नीचे दिए बटन से शुरू करें:*
"""

PROMO_MESSAGES = ["""
🔥 *FREE MONEY EARNING ADDA*

💰 हर रोज़ कमाओ घर बैठे!
📱 100% Free Methods
✅ Verified & Trusted

👉 Join करो अभी: {channel_link}
📲 Share करो दोस्तों के साथ!

#FreeMoneyEarning #OnlineEarning #FMEA
    """, """
⚡ *Daily Earning Update - FMEA*

🎯 आज का टॉपिक: Online Earning
💡 नए-नए तरीके सीखो
🚀 अपनी Income बढ़ाओ

📢 Channel: {channel_link}
💬 Support: {support_link}

🔔 Notification ON करो!
    """, """
💎 *EXCLUSIVE - FMEA Members Only*

🏆 Top Earning Methods:
├ ✅ Freelancing
├ ✅ Affiliate Marketing
├ ✅ Online Trading Tips
├ ✅ App से कमाई
└ ✅ YouTube & Content

📲 Join Now: {channel_link}
    """]
