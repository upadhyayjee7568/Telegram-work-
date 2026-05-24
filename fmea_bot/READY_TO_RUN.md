# Ready to run checklist

1. `cd fmea_bot`
2. `cp .env.example .env`
3. `.env` me `BOT_TOKEN` daalein.
4. Ensure bot is admin in channel `@FMEA1237802VHKV` with post permissions.
5. Run:
   - `pip install -r requirements.txt`
   - `python bot.py`

## Automated channel posting
- Bot me admin panel se scheduled post create karein.
- Default auto times: `09:00,14:00,20:00` (Asia/Kolkata).

## Important security
- Exposed token ko BotFather se **regenerate** karein.


## One-click cloud deploy
< codex/update-telegram-bot-and-deploy-to-github-v2p6r3
- Render Blueprint create karte waqt **Blueprint Path blank** chhodein (root `render.yaml` auto pick hoga).
- Agar manual dena ho to exact `render.yaml` likhein.
=
- Render Blueprint use karein: `fmea_bot/render.yaml`
> main
- Sirf `BOT_TOKEN` secret set karna hoga.
