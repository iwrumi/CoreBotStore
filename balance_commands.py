"""
Balance System Commands for Telegram Bot
Handles balance top-ups, deposits, and balance management
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from telegram.constants import ParseMode
from balance_system import BalanceSystem, DepositNotifications
from advanced_data_manager import AdvancedDataManager

# Conversation states
CUSTOM_AMOUNT, UPLOAD_PROOF = range(2)

class BalanceCommands:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.balance_system = BalanceSystem()
        self.data_manager = AdvancedDataManager()
        self.notifications = DepositNotifications(bot_token)
    
    async def deposit_balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main deposit balance command"""
        user_telegram_id = str(update.effective_user.id)
        user_name = update.effective_user.first_name or "there"
        
        # Get user balance info
        balance_info = self.balance_system.get_user_balance(user_telegram_id)
        
        text = f"""
💳 **Top Up Balance**

**Current Balance:** ₱{balance_info['balance']:,.2f}
**Total Deposited:** ₱{balance_info['total_deposited']:,.2f}

💰 Choose a nominal below or type a custom amount.

**Quick Amounts:**
        """
        
        # Create keyboard with suggested amounts
        suggested_amounts = self.balance_system.get_suggested_amounts()
        keyboard = []
        
        # Add buttons in rows of 2
        for i in range(0, len(suggested_amounts), 2):
            row = []
            for j in range(2):
                if i + j < len(suggested_amounts):
                    amount = suggested_amounts[i + j]
                    row.append(InlineKeyboardButton(f"₱{amount}", callback_data=f"deposit_{amount}"))
            keyboard.append(row)
        
        # Add custom amount and back buttons
        keyboard.append([InlineKeyboardButton("💬 Other Amount", callback_data="custom_amount")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def check_balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check balance command"""
        user_telegram_id = str(update.effective_user.id)
        user = self.data_manager.get_or_create_user(user_telegram_id, update.effective_user.first_name)
        
        # Get comprehensive balance info
        balance_info = self.balance_system.get_user_balance(user_telegram_id)
        deposit_history = self.balance_system.get_deposit_history(user_telegram_id, limit=5)
        
        # Format user info like the premium bot
        text = f"""
📊 **User Details:**
• ID: {user_telegram_id}
• Name: {user.get('first_name', 'Unknown')}
• Balance: ₱{balance_info['balance']:,.2f}
• Total Spent: ₱{balance_info['total_spent']:,.2f}

💰 **Balance Summary:**
• Current Balance: ₱{balance_info['balance']:,.2f}
• Total Deposited: ₱{balance_info['total_deposited']:,.2f}
• Pending Deposits: {len(balance_info['pending_deposits'])}

"""
        
        if deposit_history:
            text += "📈 **Recent Deposits:**\n"
            for deposit in deposit_history[:3]:
                status_emoji = {
                    'completed': '✅',
                    'pending': '⏳',
                    'proof_submitted': '📄',
                    'cancelled': '❌'
                }.get(deposit['status'], '❓')
                
                date = deposit['created_at'][:10]  # YYYY-MM-DD
                text += f"• {status_emoji} ₱{deposit['amount']:.2f} ({date})\n"
        
        text += "\n🛍️ Ready to shop with your balance!"
        
        keyboard = [
            [
                InlineKeyboardButton("💳 Top Up", callback_data="deposit_balance"),
                InlineKeyboardButton("📜 Full History", callback_data="deposit_history")
            ],
            [
                InlineKeyboardButton("🛒 Browse Products", callback_data="browse_products"),
                InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_deposit_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle deposit amount selection"""
        query = update.callback_query
        await query.answer()
        
        user_telegram_id = str(update.effective_user.id)
        
        if query.data == "custom_amount":
            # Ask for custom amount
            text = """
💬 **Enter Custom Amount**

Please enter the amount you want to deposit:

**Minimum:** ₱20
**Maximum:** ₱10,000

Type the amount in numbers only (e.g., 150)
            """
            
            keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="deposit_balance")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return CUSTOM_AMOUNT
        
        elif query.data.startswith("deposit_"):
            # Handle preset amount
            amount = float(query.data.replace("deposit_", ""))
            return await self.create_deposit(query, user_telegram_id, amount)
    
    async def handle_custom_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle custom amount input"""
        try:
            amount = float(update.message.text.strip())
            user_telegram_id = str(update.effective_user.id)
            
            # Validate amount
            validation = self.balance_system.validate_deposit_amount(amount)
            if not validation['valid']:
                await update.message.reply_text(
                    f"❌ {validation['message']}\n\nPlease try again:"
                )
                return CUSTOM_AMOUNT
            
            return await self.create_deposit(update, user_telegram_id, amount)
            
        except ValueError:
            await update.message.reply_text(
                "❌ Please enter a valid number.\n\nExample: 150"
            )
            return CUSTOM_AMOUNT
    
    async def create_deposit(self, update, user_telegram_id: str, amount: float):
        """Create deposit and show payment options"""
        
        # Create manual deposit
        result = self.balance_system.create_manual_deposit(
            user_telegram_id=user_telegram_id,
            amount=amount,
            payment_method='gcash'  # Default to GCash
        )
        
        if not result['success']:
            if hasattr(update, 'callback_query'):
                await update.callback_query.edit_message_text(f"❌ {result['message']}")
            else:
                await update.message.reply_text(f"❌ {result['message']}")
            return ConversationHandler.END
        
        deposit = result['deposit']
        qr_info = result['qr_code_data']
        
        # Create payment display like in the premium bot
        text = f"""
💳 **Manual Deposit Created**

**ID:** #{deposit['deposit_id']}
**Method:** {deposit['payment_method'].upper()} (manual, no fee)
**Total payment:** ₱{amount:.0f}

📱 **InstaPay QR Code**
Scan the QR code above to pay

{qr_info['instructions']}

⏱️ **Upload proof or press the button after payment.**
        """
        
        keyboard = [
            [InlineKeyboardButton("📄 Upload Proof", callback_data=f"upload_proof_{deposit['deposit_id']}")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_deposit")],
            [InlineKeyboardButton("🔙 Back", callback_data="deposit_balance")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send QR code simulation (in real implementation, generate actual QR)
        qr_text = f"""
```
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓                   ▓
▓  📱 InstaPay      ▓
▓                   ▓
▓     ₱{amount:.2f}      ▓
▓                   ▓
▓  DEP{deposit['deposit_id']:>04}         ▓
▓                   ▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
```

{text}
        """
        
        if hasattr(update, 'callback_query'):
            await update.callback_query.edit_message_text(qr_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(qr_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
        # Store deposit ID for later use
        context.user_data['current_deposit_id'] = deposit['deposit_id']
        
        # Notify user about deposit creation
        await self.notifications.notify_deposit_created(user_telegram_id, deposit)
        
        return ConversationHandler.END
    
    async def handle_upload_proof(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle proof upload button"""
        query = update.callback_query
        await query.answer()
        
        deposit_id = query.data.replace("upload_proof_", "")
        
        text = """
📄 **Upload Payment Proof**

Please send the payment proof as a photo.

**Requirements:**
• Clear screenshot of payment confirmation
• Include transaction reference number
• Amount must match your deposit
• Upload within 30 minutes

Send your screenshot now:
        """
        
        keyboard = [
            [InlineKeyboardButton("❌ Cancel", callback_data="main_menu")],
            [InlineKeyboardButton("🔙 Back", callback_data="deposit_balance")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
        # Store deposit ID for proof upload
        context.user_data['upload_deposit_id'] = deposit_id
        return UPLOAD_PROOF
    
    async def handle_proof_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle proof photo upload"""
        user_telegram_id = str(update.effective_user.id)
        deposit_id = context.user_data.get('upload_deposit_id')
        
        if not deposit_id:
            await update.message.reply_text("❌ No deposit found. Please start a new deposit.")
            return ConversationHandler.END
        
        # Process proof submission
        result = self.balance_system.submit_deposit_proof(deposit_id, user_telegram_id)
        
        if result['success']:
            # NO MESSAGE TO CUSTOMER - exactly like primostorebot
            # Just save the receipt silently, no confirmation
            pass
            
        else:
            await update.message.reply_text(f"❌ {result['message']}")
        
        return ConversationHandler.END
    
    # Removed auto-approval simulation - primostorebot requires manual approval only
    
    async def show_deposit_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show full deposit history"""
        query = update.callback_query
        await query.answer()
        
        user_telegram_id = str(update.effective_user.id)
        history = self.balance_system.get_deposit_history(user_telegram_id, limit=20)
        
        if not history:
            text = "📜 **Deposit History**\n\nNo deposits found. Make your first deposit to start shopping!"
        else:
            text = f"📜 **Deposit History ({len(history)} deposits)**\n\n"
            
            for deposit in history:
                status_emoji = {
                    'completed': '✅',
                    'pending': '⏳',
                    'proof_submitted': '📄',
                    'cancelled': '❌'
                }.get(deposit['status'], '❓')
                
                status_text = {
                    'completed': 'Approved',
                    'pending': 'Pending Payment',
                    'proof_submitted': 'Under Review',
                    'cancelled': 'Cancelled'
                }.get(deposit['status'], 'Unknown')
                
                date = deposit['created_at'][:16].replace('T', ' ')  # Format date
                text += f"**#{deposit['deposit_id']}** {status_emoji}\n"
                text += f"• Amount: ₱{deposit['amount']:.2f}\n"
                text += f"• Status: {status_text}\n"
                text += f"• Date: {date}\n"
                text += f"• Method: {deposit['payment_method'].title()}\n\n"
        
        keyboard = [
            [
                InlineKeyboardButton("💳 New Deposit", callback_data="deposit_balance"),
                InlineKeyboardButton("💰 Check Balance", callback_data="check_balance")
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def admin_balance_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin balance management menu"""
        user_id = update.effective_user.id
        
        # Check admin permissions
        if not self._is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        # Get balance analytics
        analytics = self.balance_system.get_balance_analytics()
        pending_deposits = self.data_manager.get_deposits_by_status('proof_submitted')
        
        text = f"""
💳 **Balance Management**

**System Overview:**
• Total Deposits: ₱{analytics['total_deposits']:,.2f}
• Pending Reviews: {analytics['pending_deposits_count']} (₱{analytics['pending_deposits_amount']:,.2f})
• Active Balances: ₱{analytics['total_user_balance']:,.2f}
• Users with Balance: {analytics['active_users_with_balance']}

**Pending Actions:**
• {len(pending_deposits)} deposits need verification

**Top Users by Balance:**
"""
        
        for user in analytics['top_users'][:3]:
            text += f"• {user['first_name']}: ₱{user['balance']:,.2f}\n"
        
        keyboard = [
            [InlineKeyboardButton(f"📄 Review Deposits ({len(pending_deposits)})", callback_data="admin_review_deposits")],
            [InlineKeyboardButton("📊 Balance Analytics", callback_data="admin_balance_analytics")],
            [InlineKeyboardButton("👥 User Balances", callback_data="admin_user_balances")],
            [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    def _is_admin(self, user_id):
        """Check if user is admin"""
        admin_ids = [123456789]  # Replace with actual admin IDs
        return user_id in admin_ids
    
    async def cancel_deposit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel deposit creation"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "❌ **Deposit Cancelled**\n\nYour deposit has been cancelled. You can start a new deposit anytime.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        context.user_data.clear()
        return ConversationHandler.END

def get_balance_conversation_handler(bot_token):
    """Get conversation handler for balance system"""
    balance_commands = BalanceCommands(bot_token)
    
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(balance_commands.handle_deposit_amount, pattern="^(deposit_|custom_amount)"),
            CallbackQueryHandler(balance_commands.handle_upload_proof, pattern="^upload_proof_")
        ],
        states={
            CUSTOM_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, balance_commands.handle_custom_amount)],
            UPLOAD_PROOF: [MessageHandler(filters.PHOTO, balance_commands.handle_proof_photo)]
        },
        fallbacks=[
            CallbackQueryHandler(balance_commands.cancel_deposit, pattern="^(cancel_deposit|main_menu)$"),
            CommandHandler('cancel', balance_commands.cancel_deposit)
        ],
        per_message=False
    )

def get_balance_callback_handlers(bot_token):
    """Get balance system callback handlers"""
    balance_commands = BalanceCommands(bot_token)
    
    return [
        CallbackQueryHandler(balance_commands.deposit_balance_command, pattern="^deposit_balance$"),
        CallbackQueryHandler(balance_commands.check_balance_command, pattern="^check_balance$"),
        CallbackQueryHandler(balance_commands.show_deposit_history, pattern="^deposit_history$")
    ]