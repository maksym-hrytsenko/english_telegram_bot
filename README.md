# english_telegram_bot

## Setup

1. Copy `.env.example` to `.env` and fill in your values:
   ```
   cp .env.example .env
   ```
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python import_telebot.py`

`TELEGRAM_BOT_TOKEN` and DB credentials are read from environment variables (loaded from `.env` via `python-dotenv`) — never commit real values.