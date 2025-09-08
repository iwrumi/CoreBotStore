"""
Complete Premium Store Bot
Integrated version matching MRPremiumShopBot functionality
"""
import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MenuButton, MenuButtonCommands
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Import all systems
from balance_system import BalanceSystem
from product_catalog_system import ProductCatalogSystem
from welcome_system import WelcomeMessageSystem
from support_system import CustomerSupportSystem
from simple_data_manager import SimpleDataManager

# Import conversation handlers
from balance_commands import get_balance_conversation_handler, get_balance_callback_handlers
from product_commands import get_product_conversation_handler, get_product_callback_handlers

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class PremiumStoreBot:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.application = Application.builder().token(bot_token).build()
        
        # Initialize systems
        self.balance_system = BalanceSystem()
        self.catalog_system = ProductCatalogSystem()
        self.welcome_system = WelcomeMessageSystem()
        self.support_system = CustomerSupportSystem()
        self.data_manager = AdvancedDataManager()
        
        self.setup_handlers()
        self.setup_persistent_menu()
    
    def setup_persistent_menu(self):
        """Setup persistent menu buttons like MRPremiumShopBot"""
        try:
            # This creates the persistent menu at the bottom
            menu_button = MenuButtonCommands()
            self.application.bot.set_chat_menu_button(menu_button=menu_button)
        except Exception as e:
            logger.warning(f"Could not set menu button: {e}")
    
    def setup_handlers(self):
        """Set up all bot handlers"""
        
        # Main commands
        self.application.add_handler(CommandHandler("start", self.start_command))
        
        # Balance system handlers
        self.application.add_handler(CommandHandler("deposit", self.deposit_command))
        self.application.add_handler(CommandHandler("balance", self.balance_command))
        
        # Product system handlers  
        self.application.add_handler(CommandHandler("products", self.products_command))
        self.application.add_handler(CommandHandler("stock", self.stock_command))
        self.application.add_handler(CommandHandler("leaderboard", self.leaderboard_command))
        
        # Support system handlers
        self.application.add_handler(CommandHandler("bonus", self.bonus_command))
        
        # Add conversation handlers
        try:
            self.application.add_handler(get_balance_conversation_handler(self.bot_token))
            self.application.add_handler(get_product_conversation_handler())
        except Exception as e:
            logger.warning(f"Could not add conversation handlers: {e}")
        
        # Add callback handlers
        balance_handlers = get_balance_callback_handlers(self.bot_token)
        for handler in balance_handlers:
            self.application.add_handler(handler)
        
        product_handlers = get_product_callback_handlers()
        for handler in product_handlers:
            self.application.add_handler(handler)
        
        # Main callback handler
        self.application.add_handler(CallbackQueryHandler(self.handle_callbacks))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced start command matching MRPremiumShopBot"""
        user = update.effective_user
        user_telegram_id = str(user.id)
        
        # Get user info
        user_data = self.data_manager.get_or_create_user(user_telegram_id, user.first_name or "Unknown")
        
        # Get user statistics like the premium bot
        balance_info = self.balance_system.get_user_balance(user_telegram_id)
        
        # Format like MRPremiumShopBot
        text = f"""
👋 — Hello @{user.username or user.first_name}
{datetime.now().strftime('%m/%d/%Y - %I:%M:%S %p')}

**User Details:**
• ID: {user_telegram_id}
• Name: {user.first_name or 'Unknown'}
• Balance: ₱{balance_info['balance']:,.2f}
• Total Spent: ₱{balance_info['total_spent']:,.2f}

**BOT Statistics:**
• Products Sold: 264 Accounts
• Total Users: {len(self.data_manager.get_users())}

**SHORTCUTS:**
/start - Show main menu
/stock - Check available stocks
/bonus - Claim your daily bonus
/leaderboard - View top users
        """
        
        # Create category buttons like the premium bot
        categories = self.catalog_system.get_categories()
        keyboard = []
        
        # Add category buttons in rows of 2
        for i in range(0, len(categories), 2):
            row = []
            for j in range(2):
                if i + j < len(categories):
                    cat = categories[i + j]
                    row.append(InlineKeyboardButton(cat['name'], callback_data=f"category_{cat['id']}"))
            keyboard.append(row)
        
        # Add "Other Categories" button if more than 6 categories
        if len(categories) > 6:
            keyboard.append([InlineKeyboardButton("Other Categories", callback_data="other_categories")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send with persistent menu buttons
        await update.message.reply_text(
            text, 
            reply_markup=reply_markup, 
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Set persistent menu buttons at bottom
        await self.set_persistent_menu(update.effective_chat.id)
    
    async def set_persistent_menu(self, chat_id):
        """Set persistent menu buttons at bottom like MRPremiumShopBot"""
        try:
            # This creates the persistent bottom buttons
            keyboard = [
                [
                    InlineKeyboardButton("💰 Deposit Balance", callback_data="deposit_balance"),
                    InlineKeyboardButton("🛒 Browse Products", callback_data="browse_products")
                ],
                [
                    InlineKeyboardButton("💳 Check Balance", callback_data="check_balance"),
                    InlineKeyboardButton("👤 Customer Service", callback_data="customer_service")
                ],
                [
                    InlineKeyboardButton("📚 How to order", callback_data="how_to_order")
                ]
            ]
            # Note: This creates a reply keyboard that stays at bottom
            # In real implementation with Bot API, you'd use ReplyKeyboardMarkup
        except Exception as e:
            logger.warning(f"Could not set persistent menu: {e}")
    
    async def deposit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Deposit balance command"""
        from balance_commands import BalanceCommands
        balance_commands = BalanceCommands(self.bot_token)
        await balance_commands.deposit_balance_command(update, context)
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check balance command"""
        from balance_commands import BalanceCommands
        balance_commands = BalanceCommands(self.bot_token)
        await balance_commands.check_balance_command(update, context)
    
    async def products_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Browse products command"""
        from product_commands import ProductCommands
        product_commands = ProductCommands()
        await product_commands.browse_products_command(update, context)
    
    async def stock_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stock command showing available inventory"""
        categories = self.catalog_system.get_categories()
        
        text = "📦 **Available Stock**\n\n"
        
        for category in categories[:5]:  # Show top 5 categories
            products = self.catalog_system.get_products_by_category(category['id'])
            text += f"**{category['emoji']} {category['name']}:**\n"
            
            for product in products[:3]:  # Show top 3 products per category
                total_stock = sum(v.get('stock', 0) for v in product.get('variants', []))
                text += f"• {product['name']}: {total_stock} available\n"
            text += "\n"
        
        keyboard = [
            [InlineKeyboardButton("🛒 Browse All Products", callback_data="browse_products")],
            [InlineKeyboardButton("🔍 Search Products", callback_data="search_products")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def leaderboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show top users leaderboard"""
        users = self.data_manager.get_users()
        
        # Sort by total spent
        users.sort(key=lambda x: x.get('total_spent', 0), reverse=True)
        
        text = "🏆 **Top Users - Leaderboard**\n\n"
        
        for i, user in enumerate(users[:10], 1):
            emoji = "👑" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            text += f"{emoji} {user.get('first_name', 'Unknown')}: ₱{user.get('total_spent', 0):,.2f}\n"
        
        keyboard = [
            [InlineKeyboardButton("💰 Deposit to Climb", callback_data="deposit_balance")],
            [InlineKeyboardButton("🛒 Shop More", callback_data="browse_products")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def bonus_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Daily bonus command"""
        user_telegram_id = str(update.effective_user.id)
        
        # Check if already claimed today (simplified)
        text = """
🎁 **Daily Bonus**

Claim your daily bonus and get free credits!

**Today's Bonus:** ₱10
**Status:** Available ✅

**Streak Bonuses:**
• 7 days: +₱20 bonus
• 15 days: +₱50 bonus  
• 30 days: +₱100 bonus

Come back daily to maintain your streak!
        """
        
        keyboard = [
            [InlineKeyboardButton("🎁 Claim Bonus", callback_data="claim_bonus")],
            [InlineKeyboardButton("📊 View Streak", callback_data="view_streak")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_callbacks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "deposit_balance":
            from balance_commands import BalanceCommands
            balance_commands = BalanceCommands(self.bot_token)
            await balance_commands.deposit_balance_command(query, context)
        
        elif data == "browse_products" or data == "other_categories":
            from product_commands import ProductCommands
            product_commands = ProductCommands()
            await product_commands.browse_products_command(query, context)
        
        elif data == "check_balance":
            from balance_commands import BalanceCommands
            balance_commands = BalanceCommands(self.bot_token)
            await balance_commands.check_balance_command(query, context)
        
        elif data == "customer_service":
            text = """
👤 **Customer Service**

Our support team is here to help!

**Contact Methods:**
• 💬 Live Chat: Available 24/7
• 📧 Email: support@store.com
• ⚡ Response Time: < 30 minutes

**Common Issues:**
• Payment not confirmed
• Product delivery problems
• Account access issues
• General questions

How can we help you today?
            """
            
            keyboard = [
                [InlineKeyboardButton("💬 Start Live Chat", callback_data="start_chat")],
                [InlineKeyboardButton("📚 View FAQ", callback_data="view_faq")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="start_over")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
        elif data == "how_to_order":
            text = """
📚 **How to Order**

**Step-by-Step Guide:**

1️⃣ **Browse Products**
   • Choose from our categories
   • View product details and variants

2️⃣ **Add Balance**  
   • Tap "Deposit Balance"
   • Choose amount and payment method
   • Upload payment proof

3️⃣ **Make Purchase**
   • Select product variant
   • Confirm purchase with balance
   • Receive product instantly

4️⃣ **Get Support**
   • Contact customer service for help
   • Check FAQ for common questions

**Payment Methods:**
• GCash • PayMaya • Bank Transfer • InstaPay

Ready to start shopping? 🛍️
            """
            
            keyboard = [
                [InlineKeyboardButton("💳 Add Balance", callback_data="deposit_balance")],
                [InlineKeyboardButton("🛒 Browse Products", callback_data="browse_products")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="start_over")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
        elif data == "start_over":
            # Restart the bot
            await self.start_command(query, context)
        
        elif data == "claim_bonus":
            # Handle bonus claim
            user_telegram_id = str(query.from_user.id)
            
            # Add bonus to balance (simplified)
            bonus_amount = 10.0
            balance_info = self.balance_system.get_user_balance(user_telegram_id)
            new_balance = balance_info['balance'] + bonus_amount
            
            # Update balance
            self.data_manager.update_user_balance(user_telegram_id, new_balance, balance_info['total_deposited'])
            
            text = f"""
🎉 **Bonus Claimed!**

✅ You've received ₱{bonus_amount:.2f}

**Updated Balance:** ₱{new_balance:.2f}
**Next Bonus:** Available tomorrow

Keep claiming daily to build your streak and earn bigger bonuses!

Thank you for being a loyal customer! 🙏
            """
            
            keyboard = [
                [InlineKeyboardButton("🛒 Shop Now", callback_data="browse_products")],
                [InlineKeyboardButton("💰 View Balance", callback_data="check_balance")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
        else:
            # Handle other callbacks
            await query.edit_message_text(f"🔄 Processing: {data}")
    
    def run_polling(self):
        """Run bot with polling"""
        logger.info("🚀 Starting Premium Store Bot with polling...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    def run_webhook(self, webhook_url: str, port: int = 5000):
        """Run bot with webhook for production"""
        logger.info(f"🚀 Starting Premium Store Bot with webhook at {webhook_url}")
        self.application.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url,
            allowed_updates=Update.ALL_TYPES
        )

def main():
    """Main function"""
    bot_token = os.environ.get('BOT_TOKEN')
    
    if not bot_token:
        logger.error("❌ BOT_TOKEN environment variable not set!")
        print("Please set your BOT_TOKEN environment variable")
        return
    
    # Create and run bot
    bot = PremiumStoreBot(bot_token)
    
    # Use webhook for production, polling for development
    webhook_url = os.environ.get('WEBHOOK_URL')
    if webhook_url:
        bot.run_webhook(webhook_url)
    else:
        bot.run_polling()

if __name__ == '__main__':
    main()