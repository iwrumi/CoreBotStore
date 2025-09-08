"""
Admin broadcast commands for the Telegram bot
"""
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from advanced_data_manager import AdvancedDataManager
from broadcast_system import BroadcastSystem, send_broadcast_now

# Conversation states for broadcast creation
BROADCAST_TITLE, BROADCAST_MESSAGE, BROADCAST_IMAGE, BROADCAST_TARGET, BROADCAST_CONFIRM = range(5)

class BroadcastCommands:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.data_manager = AdvancedDataManager()
        self.broadcast_system = BroadcastSystem(bot_token)
    
    async def admin_broadcast_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show broadcast management menu (admin only)"""
        user_id = update.effective_user.id
        
        # Check if user is admin (you can implement your own admin check)
        if not self._is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        menu_text = """
📢 **Broadcast Management**

Send messages to all your customers instantly!

**Quick Actions:**
• Send promotional messages
• Stock alerts and updates  
• New product announcements
• Special offers with voucher codes

**Target Options:**
• All customers
• Active customers (ordered recently)
• Inactive customers (haven't ordered)
• VIP customers (high spenders)

Choose an option below:
        """
        
        keyboard = [
            [InlineKeyboardButton("📝 Create Broadcast", callback_data="create_broadcast")],
            [InlineKeyboardButton("📊 View Sent Broadcasts", callback_data="view_broadcasts")],
            [InlineKeyboardButton("🎯 Quick Promo", callback_data="quick_promo")],
            [InlineKeyboardButton("📦 Stock Alert", callback_data="stock_alert")],
            [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def start_create_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start broadcast creation process"""
        query = update.callback_query
        await query.answer()
        
        context.user_data['broadcast_data'] = {}
        
        text = """
📝 **Create New Broadcast**

Let's create a message to send to your customers.

**Step 1: Broadcast Title**
Enter a title for this broadcast (for your reference):
        """
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="broadcast_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return BROADCAST_TITLE
    
    async def get_broadcast_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get broadcast title"""
        context.user_data['broadcast_data']['title'] = update.message.text
        
        text = """
✅ **Title saved!**

**Step 2: Broadcast Message**
Now enter the message you want to send to customers:

💡 **Tips:**
• Use **bold** and *italic* formatting
• Add emojis to make it engaging
• Keep it clear and actionable
• Mention any special offers or deadlines
        """
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="broadcast_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return BROADCAST_MESSAGE
    
    async def get_broadcast_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get broadcast message"""
        context.user_data['broadcast_data']['message'] = update.message.text
        
        text = """
✅ **Message saved!**

**Step 3: Add Image (Optional)**
Would you like to add an image to your broadcast?

You can:
• Send an image URL
• Type "skip" to continue without image
        """
        
        keyboard = [
            [InlineKeyboardButton("⏭️ Skip Image", callback_data="skip_image")],
            [InlineKeyboardButton("❌ Cancel", callback_data="broadcast_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return BROADCAST_IMAGE
    
    async def get_broadcast_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get broadcast image"""
        if update.message:
            if update.message.text and update.message.text.lower() == 'skip':
                context.user_data['broadcast_data']['image_url'] = ""
            elif update.message.text and update.message.text.startswith('http'):
                context.user_data['broadcast_data']['image_url'] = update.message.text
            else:
                await update.message.reply_text("❌ Please send a valid image URL or type 'skip'")
                return BROADCAST_IMAGE
        elif update.callback_query and update.callback_query.data == "skip_image":
            await update.callback_query.answer()
            context.user_data['broadcast_data']['image_url'] = ""
        
        return await self.show_target_selection(update, context)
    
    async def show_target_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show target audience selection"""
        text = """
🎯 **Step 4: Target Audience**

Who should receive this broadcast?

**Options:**
• **All** - Every customer (recommended for important announcements)
• **Active** - Customers who ordered recently (good for follow-ups)
• **Inactive** - Customers who haven't ordered lately (re-engagement)
• **VIP** - High-spending customers (exclusive offers)
        """
        
        keyboard = [
            [InlineKeyboardButton("👥 All Customers", callback_data="target_all")],
            [InlineKeyboardButton("🔥 Active Customers", callback_data="target_active")],
            [InlineKeyboardButton("💤 Inactive Customers", callback_data="target_inactive")],
            [InlineKeyboardButton("💎 VIP Customers", callback_data="target_vip")],
            [InlineKeyboardButton("❌ Cancel", callback_data="broadcast_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
        return BROADCAST_TARGET
    
    async def get_broadcast_target(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get target audience"""
        query = update.callback_query
        await query.answer()
        
        target_map = {
            "target_all": "all",
            "target_active": "active", 
            "target_inactive": "inactive",
            "target_vip": "vip"
        }
        
        context.user_data['broadcast_data']['target_users'] = target_map.get(query.data, "all")
        
        return await self.show_broadcast_preview(query, context)
    
    async def show_broadcast_preview(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Show broadcast preview and confirmation"""
        broadcast_data = context.user_data['broadcast_data']
        
        # Get target user count
        target_users = self.broadcast_system._get_target_users(broadcast_data['target_users'])
        target_count = len(target_users)
        
        target_names = {
            "all": "All Customers",
            "active": "Active Customers",
            "inactive": "Inactive Customers", 
            "vip": "VIP Customers"
        }
        
        preview_text = f"""
📋 **Broadcast Preview**

**Title:** {broadcast_data['title']}
**Target:** {target_names.get(broadcast_data['target_users'], 'All')} ({target_count} users)
**Has Image:** {'Yes' if broadcast_data['image_url'] else 'No'}

**Message Preview:**
{broadcast_data['message']}

━━━━━━━━━━━━━━━━

Ready to send this broadcast to {target_count} customers?
        """
        
        keyboard = [
            [InlineKeyboardButton("🚀 Send Now", callback_data="send_broadcast_now")],
            [InlineKeyboardButton("⏰ Schedule Later", callback_data="schedule_broadcast")],
            [InlineKeyboardButton("✏️ Edit", callback_data="edit_broadcast")],
            [InlineKeyboardButton("❌ Cancel", callback_data="broadcast_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(preview_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return BROADCAST_CONFIRM
    
    async def send_broadcast_now(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send broadcast immediately"""
        query = update.callback_query
        await query.answer()
        
        broadcast_data = context.user_data['broadcast_data']
        
        await query.edit_message_text("🚀 **Sending broadcast...** Please wait...")
        
        try:
            # Send broadcast
            success = await send_broadcast_now(
                bot_token=self.bot_token,
                title=broadcast_data['title'],
                message=broadcast_data['message'],
                target_users=broadcast_data['target_users'],
                image_url=broadcast_data.get('image_url', '')
            )
            
            if success:
                await query.edit_message_text(
                    "✅ **Broadcast sent successfully!**\n\n"
                    "Your message has been delivered to all target customers."
                )
            else:
                await query.edit_message_text(
                    "❌ **Broadcast failed**\n\n"
                    "There was an error sending your broadcast. Please try again."
                )
        
        except Exception as e:
            await query.edit_message_text(
                f"❌ **Error sending broadcast:**\n\n{str(e)}"
            )
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
    
    async def view_broadcasts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View sent broadcasts history"""
        query = update.callback_query
        await query.answer()
        
        broadcasts = self.data_manager.get_broadcasts()
        
        if not broadcasts:
            text = "📭 **No broadcasts found**\n\nYou haven't sent any broadcasts yet."
            keyboard = [[InlineKeyboardButton("📝 Create First Broadcast", callback_data="create_broadcast")]]
        else:
            text = "📊 **Broadcast History**\n\n"
            keyboard = []
            
            for broadcast in broadcasts[-10:]:  # Show last 10
                status_emoji = {
                    'draft': '📝',
                    'scheduled': '⏰',
                    'sending': '🚀',
                    'sent': '✅',
                    'failed': '❌'
                }.get(broadcast['status'], '📋')
                
                text += f"{status_emoji} **{broadcast['title']}**\n"
                text += f"   Status: {broadcast['status'].title()}\n"
                text += f"   Sent: {broadcast['sent_count']} | Failed: {broadcast['failed_count']}\n"
                text += f"   Date: {broadcast['created_at'][:10]}\n\n"
                
                keyboard.append([InlineKeyboardButton(
                    f"📊 {broadcast['title'][:20]}...", 
                    callback_data=f"broadcast_details_{broadcast['id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("📝 Create New", callback_data="create_broadcast")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="broadcast_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def quick_promo_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Quick promotional broadcast with voucher"""
        query = update.callback_query
        await query.answer()
        
        # Get active vouchers
        vouchers = self.data_manager.get_vouchers(is_active=True)
        
        if not vouchers:
            text = """
🎯 **Quick Promo Setup**

⚠️ **No active vouchers found**

To send a promotional broadcast, you need to create a voucher code first.

Would you like to:
            """
            keyboard = [
                [InlineKeyboardButton("🎫 Create Voucher First", callback_data="create_voucher")],
                [InlineKeyboardButton("📝 Send Promo Without Voucher", callback_data="promo_no_voucher")],
                [InlineKeyboardButton("🔙 Back", callback_data="broadcast_menu")]
            ]
        else:
            text = """
🎯 **Quick Promo Broadcast**

Select a voucher to promote, and I'll create an engaging promotional message:
            """
            keyboard = []
            for voucher in vouchers[:5]:  # Show first 5 vouchers
                discount_text = f"{voucher['discount_value']}%" if voucher['discount_type'] == 'percentage' else f"${voucher['discount_value']}"
                keyboard.append([InlineKeyboardButton(
                    f"🎫 {voucher['code']} ({discount_text} off)",
                    callback_data=f"promo_voucher_{voucher['id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("📝 Custom Promo", callback_data="create_broadcast")])
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="broadcast_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def send_voucher_promo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send promotional broadcast for specific voucher"""
        query = update.callback_query
        await query.answer()
        
        voucher_id = int(query.data.split('_')[-1])
        vouchers = self.data_manager.get_vouchers()
        voucher = next((v for v in vouchers if v['id'] == voucher_id), None)
        
        if not voucher:
            await query.edit_message_text("❌ Voucher not found")
            return
        
        # Create promotional message
        discount_text = f"{voucher['discount_value']}% OFF" if voucher['discount_type'] == 'percentage' else f"${voucher['discount_value']} OFF"
        
        title = f"Special Offer: {discount_text}"
        message = f"""
🎉 **SPECIAL OFFER ALERT!** 🎉

💥 Get **{discount_text}** on your next order!

🎫 **Voucher Code:** `{voucher['code']}`
📝 **Details:** {voucher['description']}
💰 **Minimum Order:** ${voucher['minimum_order']:.2f}
⏰ **Valid Until:** {voucher['valid_until'][:10] if voucher['valid_until'] else 'No expiry'}

🛍️ **How to use:**
1. Add items to your cart
2. Use code `{voucher['code']}` at checkout
3. Enjoy your discount!

Don't miss out - shop now! 🚀
        """
        
        await query.edit_message_text("🚀 **Sending promotional broadcast...** Please wait...")
        
        try:
            success = await self.broadcast_system.send_promo_announcement(
                title=title,
                message=voucher['description'],
                voucher_code=voucher['code']
            )
            
            if success:
                await query.edit_message_text(
                    f"✅ **Promo broadcast sent!**\n\n"
                    f"Promotional message with voucher **{voucher['code']}** "
                    f"has been sent to all customers."
                )
            else:
                await query.edit_message_text("❌ **Failed to send promo broadcast**")
        
        except Exception as e:
            await query.edit_message_text(f"❌ **Error:** {str(e)}")
    
    def _is_admin(self, user_id):
        """Check if user is admin - implement your own logic"""
        # You can check against a list of admin IDs or database
        admin_ids = [123456789]  # Replace with actual admin Telegram IDs
        return user_id in admin_ids
    
    async def cancel_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel broadcast creation"""
        if update.callback_query:
            await update.callback_query.edit_message_text("❌ Broadcast creation cancelled.")
        else:
            await update.message.reply_text("❌ Broadcast creation cancelled.")
        
        context.user_data.clear()
        return ConversationHandler.END

# Conversation handler for broadcast creation
def get_broadcast_conversation_handler(bot_token):
    """Get the conversation handler for broadcast creation"""
    broadcast_commands = BroadcastCommands(bot_token)
    
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(broadcast_commands.start_create_broadcast, pattern="^create_broadcast$")],
        states={
            BROADCAST_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_commands.get_broadcast_title)],
            BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_commands.get_broadcast_message)],
            BROADCAST_IMAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_commands.get_broadcast_image),
                CallbackQueryHandler(broadcast_commands.get_broadcast_image, pattern="^skip_image$")
            ],
            BROADCAST_TARGET: [CallbackQueryHandler(broadcast_commands.get_broadcast_target, pattern="^target_")],
            BROADCAST_CONFIRM: [
                CallbackQueryHandler(broadcast_commands.send_broadcast_now, pattern="^send_broadcast_now$"),
                CallbackQueryHandler(broadcast_commands.show_broadcast_preview, pattern="^edit_broadcast$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(broadcast_commands.cancel_broadcast, pattern="^broadcast_menu$"),
            CallbackQueryHandler(broadcast_commands.cancel_broadcast, pattern="^admin_menu$"),
            CommandHandler('cancel', broadcast_commands.cancel_broadcast)
        ],
        per_message=False
    )