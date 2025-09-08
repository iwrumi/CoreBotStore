"""
Admin voucher management commands for Telegram bot
"""
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.constants import ParseMode
from voucher_system import VoucherSystem, VoucherTemplates
from advanced_data_manager import AdvancedDataManager

# Conversation states
VOUCHER_NAME, VOUCHER_TYPE, VOUCHER_VALUE, VOUCHER_CODE, VOUCHER_DETAILS, VOUCHER_EXPIRY = range(6)

class VoucherCommands:
    def __init__(self):
        self.voucher_system = VoucherSystem()
        self.voucher_templates = VoucherTemplates()
        self.data_manager = AdvancedDataManager()
    
    async def admin_voucher_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show voucher management menu"""
        user_id = update.effective_user.id
        
        # Check admin permissions
        if not self._is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        # Get voucher stats
        active_vouchers = self.voucher_system.get_active_vouchers()
        all_vouchers = self.voucher_system.get_all_vouchers()
        
        menu_text = f"""
🎫 **Voucher Management**

**Current Status:**
• Active Vouchers: {len(active_vouchers)}
• Total Vouchers: {len(all_vouchers)}

**What you can do:**
• Create discount codes
• Set expiry dates and usage limits
• Target specific customer groups
• Track voucher usage and savings

**Voucher Types:**
• Percentage discounts (e.g., 20% off)
• Fixed amount discounts (e.g., $10 off)
• Free shipping vouchers
• Minimum order requirements

Choose an option below:
        """
        
        keyboard = [
            [InlineKeyboardButton("➕ Create New Voucher", callback_data="create_voucher")],
            [InlineKeyboardButton("📋 View All Vouchers", callback_data="view_vouchers")],
            [InlineKeyboardButton("⚡ Quick Templates", callback_data="voucher_templates")],
            [InlineKeyboardButton("📊 Voucher Analytics", callback_data="voucher_analytics")],
            [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def start_create_voucher(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start voucher creation process"""
        query = update.callback_query
        await query.answer()
        
        context.user_data['voucher_data'] = {}
        
        text = """
➕ **Create New Voucher**

Let's create a discount code for your customers!

**Step 1: Voucher Name**
Enter a name for this voucher (for your reference):

*Example: "Summer Sale", "Welcome Discount", "Flash Deal"*
        """
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="voucher_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return VOUCHER_NAME
    
    async def get_voucher_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get voucher name"""
        name = update.message.text.strip()
        if len(name) < 3 or len(name) > 50:
            await update.message.reply_text("❌ Name must be 3-50 characters long. Please try again:")
            return VOUCHER_NAME
        
        context.user_data['voucher_data']['name'] = name
        
        text = """
✅ **Name saved!**

**Step 2: Discount Type**
What type of discount do you want to offer?

**Options:**
• **Percentage** - Give % off (e.g., 20% off)
• **Fixed Amount** - Give $ off (e.g., $10 off)
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 Percentage Discount", callback_data="type_percentage")],
            [InlineKeyboardButton("💰 Fixed Amount Discount", callback_data="type_fixed")],
            [InlineKeyboardButton("❌ Cancel", callback_data="voucher_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return VOUCHER_TYPE
    
    async def get_voucher_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get voucher discount type"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "type_percentage":
            context.user_data['voucher_data']['discount_type'] = 'percentage'
            prompt = """
✅ **Percentage discount selected!**

**Step 3: Discount Value**
Enter the percentage discount (1-100):

*Example: Enter "20" for 20% off*
            """
        elif query.data == "type_fixed":
            context.user_data['voucher_data']['discount_type'] = 'fixed_amount'
            prompt = """
✅ **Fixed amount discount selected!**

**Step 3: Discount Value**
Enter the dollar amount discount:

*Example: Enter "10" for $10 off or "25.50" for $25.50 off*
            """
        else:
            return VOUCHER_TYPE
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="voucher_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(prompt, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return VOUCHER_VALUE
    
    async def get_voucher_value(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get voucher discount value"""
        try:
            value = float(update.message.text.strip())
            discount_type = context.user_data['voucher_data']['discount_type']
            
            # Validate value
            if discount_type == 'percentage':
                if not 1 <= value <= 100:
                    await update.message.reply_text("❌ Percentage must be between 1-100. Please try again:")
                    return VOUCHER_VALUE
            else:  # fixed_amount
                if value <= 0:
                    await update.message.reply_text("❌ Amount must be greater than 0. Please try again:")
                    return VOUCHER_VALUE
                if value > 1000:
                    await update.message.reply_text("❌ Amount seems too high. Maximum is $1000. Please try again:")
                    return VOUCHER_VALUE
            
            context.user_data['voucher_data']['discount_value'] = value
            
            # Show confirmation and move to code input
            if discount_type == 'percentage':
                discount_text = f"{value}% OFF"
            else:
                discount_text = f"${value:.2f} OFF"
            
            text = f"""
✅ **Discount set to {discount_text}!**

**Step 4: Voucher Code**
Enter a custom code or let me generate one:

**Options:**
• Type a custom code (3-20 characters, letters/numbers only)
• Click "Auto Generate" for a random code

*Example codes: SAVE20, WELCOME10, FLASH50*
            """
            
            keyboard = [
                [InlineKeyboardButton("🎲 Auto Generate Code", callback_data="auto_generate_code")],
                [InlineKeyboardButton("❌ Cancel", callback_data="voucher_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return VOUCHER_CODE
            
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number:")
            return VOUCHER_VALUE
    
    async def get_voucher_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get or generate voucher code"""
        if update.message:
            # Custom code entered
            code = update.message.text.strip().upper()
            
            # Validate code format
            import re
            if not re.match(r'^[A-Z0-9]{3,20}$', code):
                await update.message.reply_text(
                    "❌ Invalid code format. Use 3-20 characters, letters and numbers only.\n"
                    "Please try again:"
                )
                return VOUCHER_CODE
            
            # Check if code exists
            if self.voucher_system._code_exists(code):
                await update.message.reply_text(
                    f"❌ Code '{code}' already exists. Please choose a different code:"
                )
                return VOUCHER_CODE
            
            context.user_data['voucher_data']['code'] = code
            
        elif update.callback_query and update.callback_query.data == "auto_generate_code":
            # Auto-generate code
            await update.callback_query.answer()
            code = self.voucher_system._generate_voucher_code()
            context.user_data['voucher_data']['code'] = code
        
        return await self.show_voucher_details_form(update, context)
    
    async def show_voucher_details_form(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Show form for additional voucher details"""
        voucher_data = context.user_data['voucher_data']
        
        text = f"""
✅ **Code set to: {voucher_data['code']}**

**Step 5: Additional Details (Optional)**

Set optional restrictions and details:

**Current Settings:**
• Minimum Order: No minimum
• Usage Limit: Unlimited
• Expiry: Never expires
• Description: None

Would you like to add any restrictions?
        """
        
        keyboard = [
            [InlineKeyboardButton("💰 Set Minimum Order", callback_data="set_minimum_order")],
            [InlineKeyboardButton("🔢 Set Usage Limit", callback_data="set_usage_limit")],
            [InlineKeyboardButton("⏰ Set Expiry Date", callback_data="set_expiry")],
            [InlineKeyboardButton("📝 Add Description", callback_data="set_description")],
            [InlineKeyboardButton("✅ Create Voucher", callback_data="create_voucher_final")],
            [InlineKeyboardButton("❌ Cancel", callback_data="voucher_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
        return VOUCHER_DETAILS
    
    async def handle_voucher_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voucher detail settings"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "create_voucher_final":
            return await self.create_voucher_final(update, context)
        elif query.data == "set_minimum_order":
            text = """
💰 **Set Minimum Order Amount**

Enter the minimum order amount required to use this voucher:

*Example: Enter "50" to require at least $50 order*
*Enter "0" for no minimum*
            """
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="voucher_details_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            context.user_data['setting_field'] = 'minimum_order'
            return VOUCHER_DETAILS
            
        elif query.data == "set_usage_limit":
            text = """
🔢 **Set Usage Limit**

How many times can this voucher be used?

*Example: Enter "100" to limit to 100 uses*
*Enter "0" for unlimited uses*
            """
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="voucher_details_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            context.user_data['setting_field'] = 'usage_limit'
            return VOUCHER_DETAILS
            
        elif query.data == "set_expiry":
            text = """
⏰ **Set Expiry Date**

When should this voucher expire?

**Options:**
• Enter days from now (e.g., "30" for 30 days)
• Enter "0" to never expire
            """
            keyboard = [
                [InlineKeyboardButton("📅 7 Days", callback_data="expiry_7")],
                [InlineKeyboardButton("📅 30 Days", callback_data="expiry_30")],
                [InlineKeyboardButton("📅 90 Days", callback_data="expiry_90")],
                [InlineKeyboardButton("♾️ Never Expire", callback_data="expiry_never")],
                [InlineKeyboardButton("🔙 Back", callback_data="voucher_details_back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return VOUCHER_EXPIRY
            
        elif query.data == "set_description":
            text = """
📝 **Add Description**

Enter a description for this voucher (will be shown to customers):

*Example: "Special weekend discount for loyal customers!"*
            """
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="voucher_details_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            context.user_data['setting_field'] = 'description'
            return VOUCHER_DETAILS
        
        return VOUCHER_DETAILS
    
    async def handle_expiry_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle expiry date selection"""
        query = update.callback_query
        await query.answer()
        
        expiry_map = {
            "expiry_7": 7,
            "expiry_30": 30,
            "expiry_90": 90,
            "expiry_never": 0
        }
        
        days = expiry_map.get(query.data, 0)
        if days > 0:
            expiry_date = datetime.utcnow() + timedelta(days=days)
            context.user_data['voucher_data']['valid_until'] = expiry_date
        else:
            context.user_data['voucher_data']['valid_until'] = None
        
        return await self.show_voucher_details_form(query, context)
    
    async def create_voucher_final(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create the voucher with all settings"""
        query = update.callback_query
        await query.answer()
        
        voucher_data = context.user_data['voucher_data']
        
        # Create voucher
        result = self.voucher_system.create_voucher(
            name=voucher_data['name'],
            discount_type=voucher_data['discount_type'],
            discount_value=voucher_data['discount_value'],
            code=voucher_data['code'],
            description=voucher_data.get('description', ''),
            minimum_order=voucher_data.get('minimum_order', 0),
            usage_limit=voucher_data.get('usage_limit', 0),
            valid_until=voucher_data.get('valid_until')
        )
        
        if result['success']:
            voucher = result['voucher']
            
            # Format success message
            if voucher['discount_type'] == 'percentage':
                discount_text = f"{voucher['discount_value']}% OFF"
            else:
                discount_text = f"${voucher['discount_value']:.2f} OFF"
            
            success_text = f"""
🎉 **Voucher Created Successfully!**

🎫 **Code:** `{voucher['code']}`
💰 **Discount:** {discount_text}
📝 **Name:** {voucher['name']}
💵 **Minimum Order:** ${voucher['minimum_order']:.2f}
🔢 **Usage Limit:** {voucher['usage_limit'] if voucher['usage_limit'] > 0 else 'Unlimited'}
⏰ **Expires:** {voucher['valid_until'][:10] if voucher['valid_until'] else 'Never'}

✅ Your voucher is now active and ready to use!

**Next Steps:**
• Share the code with customers
• Send a broadcast announcement
• Track usage in analytics
            """
            
            keyboard = [
                [InlineKeyboardButton("📢 Broadcast This Voucher", callback_data=f"broadcast_voucher_{voucher['id']}")],
                [InlineKeyboardButton("📋 View All Vouchers", callback_data="view_vouchers")],
                [InlineKeyboardButton("➕ Create Another", callback_data="create_voucher")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="voucher_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(success_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            
        else:
            await query.edit_message_text(f"❌ **Error creating voucher:**\n\n{result['message']}")
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
    
    async def view_vouchers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View all vouchers"""
        query = update.callback_query
        await query.answer()
        
        vouchers = self.voucher_system.get_all_vouchers()
        
        if not vouchers:
            text = """
📭 **No vouchers found**

You haven't created any voucher codes yet.

Ready to create your first discount code?
            """
            keyboard = [
                [InlineKeyboardButton("➕ Create First Voucher", callback_data="create_voucher")],
                [InlineKeyboardButton("🔙 Back", callback_data="voucher_menu")]
            ]
        else:
            text = f"📋 **All Vouchers ({len(vouchers)})**\n\n"
            keyboard = []
            
            # Sort by creation date (newest first)
            vouchers.sort(key=lambda x: x['created_at'], reverse=True)
            
            for voucher in vouchers[:10]:  # Show first 10
                # Status emoji
                if not voucher['is_active']:
                    status_emoji = "❌"
                elif voucher['valid_until'] and datetime.fromisoformat(voucher['valid_until']) <= datetime.utcnow():
                    status_emoji = "⏰"
                elif voucher['usage_limit'] > 0 and voucher['usage_count'] >= voucher['usage_limit']:
                    status_emoji = "🔒"
                else:
                    status_emoji = "✅"
                
                # Discount text
                if voucher['discount_type'] == 'percentage':
                    discount = f"{voucher['discount_value']}%"
                else:
                    discount = f"${voucher['discount_value']:.2f}"
                
                text += f"{status_emoji} **{voucher['code']}** - {discount} off\n"
                text += f"   Used: {voucher['usage_count']}"
                if voucher['usage_limit'] > 0:
                    text += f"/{voucher['usage_limit']}"
                text += f" | Expires: {voucher['valid_until'][:10] if voucher['valid_until'] else 'Never'}\n\n"
                
                keyboard.append([InlineKeyboardButton(
                    f"📊 {voucher['code']} Details",
                    callback_data=f"voucher_details_{voucher['id']}"
                )])
            
            if len(vouchers) > 10:
                text += f"*... and {len(vouchers) - 10} more vouchers*"
            
            keyboard.append([InlineKeyboardButton("➕ Create New", callback_data="create_voucher")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="voucher_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_voucher_templates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show quick voucher templates"""
        query = update.callback_query
        await query.answer()
        
        text = """
⚡ **Quick Voucher Templates**

Create common voucher types instantly:

**Popular Templates:**
• Weekend Special - Limited time discount
• Welcome Discount - New customer offer
• Flash Sale - High discount, short time
• Free Shipping - Remove delivery cost
• Bulk Order - Discount for large orders

Choose a template to create instantly:
        """
        
        keyboard = [
            [InlineKeyboardButton("🎉 Weekend Special (20% OFF)", callback_data="template_weekend")],
            [InlineKeyboardButton("👋 Welcome Discount (10% OFF)", callback_data="template_welcome")],
            [InlineKeyboardButton("⚡ Flash Sale (30% OFF)", callback_data="template_flash")],
            [InlineKeyboardButton("🚚 Free Shipping ($10 OFF)", callback_data="template_shipping")],
            [InlineKeyboardButton("📦 Bulk Order (25% OFF)", callback_data="template_bulk")],
            [InlineKeyboardButton("🔙 Back", callback_data="voucher_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def create_template_voucher(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create voucher from template"""
        query = update.callback_query
        await query.answer()
        
        template_map = {
            "template_weekend": self.voucher_templates.create_weekend_special,
            "template_welcome": self.voucher_templates.create_welcome_voucher, 
            "template_flash": lambda: self.voucher_system.create_flash_sale_voucher(30, 24, 50),
            "template_shipping": self.voucher_templates.create_free_shipping_voucher,
            "template_bulk": self.voucher_templates.create_bulk_order_discount
        }
        
        template_func = template_map.get(query.data)
        if not template_func:
            await query.edit_message_text("❌ Template not found")
            return
        
        await query.edit_message_text("🔄 **Creating voucher from template...**")
        
        try:
            result = template_func()
            
            if result['success']:
                voucher = result['voucher']
                
                if voucher['discount_type'] == 'percentage':
                    discount_text = f"{voucher['discount_value']}% OFF"
                else:
                    discount_text = f"${voucher['discount_value']:.2f} OFF"
                
                success_text = f"""
✅ **Template Voucher Created!**

🎫 **Code:** `{voucher['code']}`
💰 **Discount:** {discount_text}
📝 **Name:** {voucher['name']}
📋 **Description:** {voucher['description']}

Your voucher is ready to use!
                """
                
                keyboard = [
                    [InlineKeyboardButton("📢 Broadcast This Voucher", callback_data=f"broadcast_voucher_{voucher['id']}")],
                    [InlineKeyboardButton("📋 View All Vouchers", callback_data="view_vouchers")],
                    [InlineKeyboardButton("⚡ More Templates", callback_data="voucher_templates")],
                    [InlineKeyboardButton("🔙 Back", callback_data="voucher_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(success_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
                
            else:
                await query.edit_message_text(f"❌ **Error creating voucher:**\n\n{result['message']}")
        
        except Exception as e:
            await query.edit_message_text(f"❌ **Error creating template voucher:**\n\n{str(e)}")
    
    def _is_admin(self, user_id):
        """Check if user is admin"""
        # Implement your admin check logic
        admin_ids = [123456789]  # Replace with actual admin IDs
        return user_id in admin_ids
    
    async def cancel_voucher_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel voucher creation"""
        if update.callback_query:
            await update.callback_query.edit_message_text("❌ Voucher creation cancelled.")
        else:
            await update.message.reply_text("❌ Voucher creation cancelled.")
        
        context.user_data.clear()
        return ConversationHandler.END

def get_voucher_conversation_handler():
    """Get conversation handler for voucher creation"""
    voucher_commands = VoucherCommands()
    
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(voucher_commands.start_create_voucher, pattern="^create_voucher$")],
        states={
            VOUCHER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, voucher_commands.get_voucher_name)],
            VOUCHER_TYPE: [CallbackQueryHandler(voucher_commands.get_voucher_type, pattern="^type_")],
            VOUCHER_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, voucher_commands.get_voucher_value)],
            VOUCHER_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, voucher_commands.get_voucher_code),
                CallbackQueryHandler(voucher_commands.get_voucher_code, pattern="^auto_generate_code$")
            ],
            VOUCHER_DETAILS: [
                CallbackQueryHandler(voucher_commands.handle_voucher_details, pattern="^(create_voucher_final|set_|voucher_details_back)"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, voucher_commands.get_voucher_name)  # Handle text input for details
            ],
            VOUCHER_EXPIRY: [CallbackQueryHandler(voucher_commands.handle_expiry_selection, pattern="^expiry_")]
        },
        fallbacks=[
            CallbackQueryHandler(voucher_commands.cancel_voucher_creation, pattern="^voucher_menu$"),
            CommandHandler('cancel', voucher_commands.cancel_voucher_creation)
        ],
        per_message=False
    )