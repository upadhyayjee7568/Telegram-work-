# Deployment (24x7)

Telegram bot ko **GitHub Pages** par permanent run nahi kar sakte, kyunki Pages static hosting hai.
Permanent run ke liye Render/Railway/VPS use karein.

## Render (recommended - included in repo)
Repo me `fmea_bot/render.yaml` add hai for Blueprint deploy.

### Steps
1. Token ko BotFather se generate karke safe rakhein (repo me commit na karein).
2. GitHub repo ko Render se connect karein.
3. Render Dashboard -> **New +** -> **Blueprint** -> repo select karein.
4. `BOT_TOKEN` variable set karein (Render secret env var).
5. Deploy start ho jayega aur push par auto-deploy hoga.

## Required env vars
- `BOT_TOKEN` (secret)
- `CHANNEL_USERNAME` (supports @username or https://t.me/...)
- `ADMIN_IDS` (supports comma/newline/and)
- `ADMIN_USERNAMES`

## Local run
```bash
cd fmea_bot
cp .env.example .env
# .env me BOT_TOKEN set karein
pip install -r requirements.txt
python bot.py
```

## Security
- BOT token ko kabhi code/file me hardcode karke git me push na karein.
- Agar token chat/history me share ho gaya ho to turant regenerate karein.
< codex/update-telegram-bot-and-deploy-to-github-v2p6r3

< codex/update-telegram-bot-and-deploy-to-github-fdh5b8
> main


### Render plan error fix
If you see `service type is not available for this plan`, this repo now uses a **web** service blueprint (not worker) compatible with lower plans.
< codex/update-telegram-bot-and-deploy-to-github-v2p6r3


### If you see YAML parse error with `<<` / `==` / `>>`
That means Render synced an old conflicted commit.
1. GitHub main branch me latest `render.yaml` open karke confirm karein.
2. Render Blueprint page pe **Manual sync** karein.
3. Agar same error rahe to old Blueprint delete karke naya Blueprint create karein (path blank ya `render.yaml`).
4. New Blueprint banate waqt branch `main` select karein.
5. Root `render.yaml` ka expected clean content single `web` service hona chahiye (no `worker` block, no merge markers).
=
=
> main
> main
