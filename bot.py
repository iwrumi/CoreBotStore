"""
Complete Premium Store Bot - Main Entry Point
Matches MRPremiumShopBot functionality exactly
"""
import os
import logging
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, ContextTypes

# Import the complete bot
from complete_bot import PremiumStoreBot

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app for webhook
app = Flask(__name__)

# Initialize bot token
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required!")

# Global bot instance
bot_app = None
bot_instance = None

def initialize_bot():
    """Initialize the complete premium bot"""
    global bot_app, bot_instance
    
    try:
        # Create complete premium bot
        bot_instance = PremiumStoreBot(BOT_TOKEN)
        bot_app = bot_instance.application
        
        # Set webhook
        webhook_domain = os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')
        webhook_url = f"https://{webhook_domain}/webhook"
        
        logger.info(f"Setting webhook URL: {webhook_url}")
        bot_app.bot.set_webhook(url=webhook_url)
        
        logger.info("Complete Premium Store Bot initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize bot: {e}")
        return False

@app.route('/')
def health_check():
    """Health check endpoint"""
    return {'status': 'OK', 'bot': 'Premium Store Bot', 'version': '2.0'}

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Handle incoming webhook updates"""
    if not bot_app:
        return {'error': 'Bot not initialized'}, 500
    
    try:
        update = Update.de_json(request.get_json(), bot_app.bot)
        await bot_app.process_update(update)
        return {'status': 'OK'}
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return {'error': str(e)}, 500

@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    """Set webhook URL"""
    try:
        if not bot_app:
            initialize_bot()
        
        webhook_domain = os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')
        webhook_url = f"https://{webhook_domain}/webhook"
        
        result = bot_app.bot.set_webhook(url=webhook_url)
        return {'status': 'Webhook set', 'url': webhook_url, 'result': str(result)}
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    # Initialize bot on startup
    if initialize_bot():
        logger.info("🚀 Premium Store Bot is ready to receive webhooks")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        logger.error("❌ Failed to initialize bot")