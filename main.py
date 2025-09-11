# --- Imports at the top ---
import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler

# --- Logging setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Flask app ---
app = Flask(__name__)

# --- Bot + Dispatcher ---
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN not found in environment variables!")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, None, workers=0, use_context=True)

# --- Example handler ---
def start(update: Update, context):
    update.message.reply_text("✅ Hello! Your bot is alive on Railway!")

dp.add_handler(CommandHandler("start", start))

# --- Webhook endpoint ---
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = request.get_json(force=True)
        logger.info(f"📩 Incoming update: {update}")

        if update:
            tg_update = Update.de_json(update, bot)
            dp.process_update(tg_update)

        return "ok", 200
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}", exc_info=True)
        return "error", 500

# --- Root (optional health check) ---
@app.route("/")
def index():
    return "🤖 Bot is running!", 200

# --- Register webhook with Telegram ---
@app.before_first_request
def set_webhook():
    railway_url = os.getenv("RAILWAY_STATIC_URL")
    if railway_url:
        webhook_url = railway_url + "/webhook"
        bot.set_webhook(url=webhook_url)
        logger.info(f"✅ Webhook set to {webhook_url}")
    else:
        logger.warning("⚠️ RAILWAY_STATIC_URL not found, running locally?")

# --- Local run (Railway will use Gunicorn) ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
