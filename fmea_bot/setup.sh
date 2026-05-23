#!/bin/bash
set -e

echo "🚀 FMEA Bot setup start"
python -m pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "✅ .env file created from .env.example"
fi

echo "✅ Setup complete"
echo "Next: .env me BOT_TOKEN set karke run karein: python bot.py"
