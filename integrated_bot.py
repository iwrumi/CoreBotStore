"""
Integrated Telegram Store Bot with Complete Admin Panel
Combines all advanced features into one comprehensive system
"""
import os
import logging
from telegram.ext import Application
from telegram import Update
from telegram.ext import ContextTypes

# Import admin panel and all command systems
from admin_panel import get_admin_panel_handlers, AdminPanel
from financial_commands import get_financial_callback_handlers, FinancialCommands
from broadcast_commands import get_broadcast_conversation_handler, BroadcastCommands
from voucher_commands import get_voucher_conversation_handler, VoucherCommands
from payment_commands import get_payment_conversation_handler, AdminPaymentCommands
from welcome_commands import get_welcome_conversation_handler, WelcomeCommands
from support_commands import get_support_conversation_handler, AdminSupportCommands

# Import core systems
from welcome_system import WelcomeMessageSystem
from advanced_data_manager import AdvancedDataManager

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class IntegratedStoreBot:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.application = Application.builder().token(bot_token).build()
        
        # Initialize systems
        self.admin_panel = AdminPanel()
        self.welcome_system = WelcomeMessageSystem()
        self.data_manager = AdvancedDataManager()
        
        # Initialize command classes
        self.financial_commands = FinancialCommands()
        self.broadcast_commands = BroadcastCommands()
        self.voucher_commands = VoucherCommands()
        self.payment_commands = AdminPaymentCommands()
        self.welcome_commands = WelcomeCommands()
        self.support_commands = AdminSupportCommands()
        
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up all bot handlers"""
        
        # Core bot commands
        self.application.add_handler(self.admin_panel.admin_command)
        
        # Main user commands
        from telegram.ext import CommandHandler, CallbackQueryHandler
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Admin panel handlers
        admin_handlers = get_admin_panel_handlers()
        for handler in admin_handlers:
            self.application.add_handler(handler)
        
        # Financial system handlers
        financial_handlers = get_financial_callback_handlers()
        for handler in financial_handlers:
            self.application.add_handler(handler)
        
        # Individual system handlers
        self.application.add_handler(CallbackQueryHandler(self.financial_commands.admin_financial_menu, pattern='^admin_financial_menu$'))
        self.application.add_handler(CallbackQueryHandler(self.broadcast_commands.admin_broadcast_menu, pattern='^admin_broadcast_menu$'))
        self.application.add_handler(CallbackQueryHandler(self.voucher_commands.admin_voucher_menu, pattern='^admin_voucher_menu$'))
        self.application.add_handler(CallbackQueryHandler(self.payment_commands.admin_payment_menu, pattern='^admin_payment_menu$'))
        self.application.add_handler(CallbackQueryHandler(self.welcome_commands.admin_welcome_menu, pattern='^admin_welcome_menu$'))
        self.application.add_handler(CallbackQueryHandler(self.support_commands.admin_support_menu, pattern='^admin_support_menu$'))
        
        # Conversation handlers for complex interactions
        try:
            self.application.add_handler(get_broadcast_conversation_handler())
            self.application.add_handler(get_voucher_conversation_handler())
            self.application.add_handler(get_payment_conversation_handler(self.bot_token))
            self.application.add_handler(get_welcome_conversation_handler())
            self.application.add_handler(get_support_conversation_handler(self.bot_token))
        except Exception as e:
            logger.warning(f"Could not add conversation handlers: {e}")
        
        # Add other callback handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_queries))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced start command with personalized welcome"""
        user = update.effective_user
        user_telegram_id = str(user.id)
        
        # Get personalized welcome message
        welcome_data = self.welcome_system.get_welcome_message(user_telegram_id, user.first_name)
        
        # Create keyboard from welcome message buttons
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = []
        
        for button in welcome_data.get('buttons', []):
            keyboard.append([InlineKeyboardButton(button['text'], callback_data=button['action'])])
        
        # Add admin access for admins
        if self.admin_panel.is_admin(user.id):
            keyboard.append([InlineKeyboardButton("🛠️ Admin Panel", callback_data="admin_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_data['message'], 
            reply_markup=reply_markup, 
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced help command with support system integration"""
        from support_commands import SupportCommands
        support_commands = SupportCommands(self.bot_token)
        await support_commands.help_command(update, context)
    
    async def handle_callback_queries(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle miscellaneous callback queries"""
        query = update.callback_query
        await query.answer()
        
        # Handle basic navigation
        if query.data == "main_menu":
            await self.start_command(update, context)
        elif query.data == "help_menu":
            await self.help_command(update, context)
        elif query.data == "catalog":
            await query.edit_message_text("🏪 **Product Catalog**\n\nBrowse our amazing products!\n\n*Feature coming soon...*")
        elif query.data == "cart":
            await query.edit_message_text("🛒 **Your Shopping Cart**\n\nYour cart is currently empty.\n\n*Add products to see them here!*")
        elif query.data == "orders":
            await query.edit_message_text("📦 **Your Orders**\n\nNo orders found.\n\n*Place your first order to see it here!*")
        else:
            await query.edit_message_text(f"🔄 Processing: {query.data}\n\n*This feature is being implemented...*")
    
    def run_polling(self):
        """Run the bot with polling"""
        logger.info("Starting Integrated Store Bot with polling...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    def run_webhook(self, webhook_url: str, port: int = 5000):
        """Run the bot with webhook"""
        logger.info(f"Starting Integrated Store Bot with webhook at {webhook_url}")
        self.application.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url,
            allowed_updates=Update.ALL_TYPES
        )

def main():
    """Main function to run the integrated bot"""
    # Get bot token from environment
    bot_token = os.environ.get('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN environment variable not set!")
        return
    
    # Create and run the integrated bot
    bot = IntegratedStoreBot(bot_token)
    
    # Choose running mode based on environment
    webhook_url = os.environ.get('WEBHOOK_URL')
    if webhook_url:
        bot.run_webhook(webhook_url)
    else:
        bot.run_polling()

if __name__ == '__main__':
    main()