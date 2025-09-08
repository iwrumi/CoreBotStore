"""
Admin commands for managing welcome messages
"""
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.constants import ParseMode
from welcome_system import WelcomeMessageSystem, WelcomeMessageVariables
from advanced_data_manager import AdvancedDataManager

# Conversation states
WELCOME_TYPE, WELCOME_TEMPLATE, WELCOME_MESSAGE, WELCOME_BUTTONS, WELCOME_CONFIRM = range(5)

class WelcomeCommands:
    def __init__(self):
        self.welcome_system = WelcomeMessageSystem()
        self.data_manager = AdvancedDataManager()
    
    async def admin_welcome_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show welcome message management menu"""
        user_id = update.effective_user.id
        
        # Check admin permissions
        if not self._is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        # Get analytics
        analytics = self.welcome_system.get_welcome_analytics()
        
        menu_text = f"""
👋 **Welcome Message Management**

**User Statistics:**
• Total Users: {analytics['total_users']}
• New Users: {analytics['new_users']}
• Returning Users: {analytics['returning_users']}
• VIP Users: {analytics['vip_users']}
• Conversion Rate: {analytics['conversion_rate']:.1f}%

**Customize Experience:**
• Personalize first impressions
• Set different messages for user types
• Use dynamic variables
• Track effectiveness

Choose what to customize:
        """
        
        keyboard = [
            [InlineKeyboardButton("✨ Customize Welcome Messages", callback_data="customize_welcome")],
            [InlineKeyboardButton("🎨 Choose Templates", callback_data="welcome_templates")],
            [InlineKeyboardButton("🧪 Test Messages", callback_data="test_welcome")],
            [InlineKeyboardButton("📊 View Analytics", callback_data="welcome_analytics")],
            [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_customize_welcome(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show welcome customization options"""
        query = update.callback_query
        await query.answer()
        
        text = """
✨ **Customize Welcome Messages**

You can create different welcome experiences for different types of customers:

**User Types:**
• 🆕 **New Users** - First-time visitors
• 🔄 **Returning Users** - Customers who've shopped before  
• 👑 **VIP Users** - High-value customers

**Features:**
• Use personalization variables
• Custom buttons and actions
• Dynamic content based on user data
• Professional templates or create from scratch

Which user type would you like to customize?
        """
        
        keyboard = [
            [InlineKeyboardButton("🆕 New Users", callback_data="customize_new_user")],
            [InlineKeyboardButton("🔄 Returning Users", callback_data="customize_returning")],
            [InlineKeyboardButton("👑 VIP Users", callback_data="customize_vip")],
            [InlineKeyboardButton("📝 View Variables", callback_data="show_variables")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_welcome_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def start_welcome_customization(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start welcome message customization process"""
        query = update.callback_query
        await query.answer()
        
        # Extract user type from callback data
        user_type_map = {
            "customize_new_user": "new_user",
            "customize_returning": "returning",
            "customize_vip": "vip"
        }
        
        user_type = user_type_map.get(query.data)
        if not user_type:
            await query.edit_message_text("❌ Invalid user type selected.")
            return
        
        context.user_data['welcome_user_type'] = user_type
        
        # Show template options
        text = f"""
🎨 **Customize {user_type.replace('_', ' ').title()} Welcome**

You can either:
• Choose from pre-made templates
• Create a completely custom message

**Available Templates:**
        """
        
        templates = self.welcome_system.get_available_templates()
        keyboard = []
        
        for template in templates:
            keyboard.append([InlineKeyboardButton(
                f"📋 {template['name']}", 
                callback_data=f"template_{template['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("✏️ Create Custom Message", callback_data="create_custom")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="customize_welcome")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return WELCOME_TEMPLATE
    
    async def handle_template_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle template selection"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "create_custom":
            return await self.start_custom_message(query, context)
        
        if query.data.startswith("template_"):
            template_id = query.data.replace("template_", "")
            user_type = context.user_data['welcome_user_type']
            
            # Apply template
            result = self.welcome_system.apply_template(user_type, template_id)
            
            if result['success']:
                template = result['template']
                
                success_text = f"""
✅ **Template Applied Successfully!**

**Template:** {template['name']}
**User Type:** {user_type.replace('_', ' ').title()}

**Preview:**
{template['message'][:200]}...

**Buttons:** {len(template.get('buttons', []))} buttons configured

The template has been applied and is now active for {user_type.replace('_', ' ')} users!
                """
                
                keyboard = [
                    [InlineKeyboardButton("🧪 Test Message", callback_data=f"test_{user_type}")],
                    [InlineKeyboardButton("✏️ Edit Further", callback_data="create_custom")],
                    [InlineKeyboardButton("🏠 Back to Menu", callback_data="admin_welcome_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(success_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
                return ConversationHandler.END
                
            else:
                await query.edit_message_text(f"❌ **Error applying template:**\n\n{result['message']}")
                return ConversationHandler.END
        
        return WELCOME_TEMPLATE
    
    async def start_custom_message(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Start custom message creation"""
        user_type = context.user_data['welcome_user_type']
        
        text = f"""
✏️ **Create Custom {user_type.replace('_', ' ').title()} Welcome**

Write your custom welcome message below.

**Tips:**
• Use personalization variables (type /variables to see available ones)
• Keep it engaging and clear
• Mention your store's unique value
• Guide users to take action

**Examples of variables:**
• `{{user_name}}` - User's name
• `{{store_name}}` - Your store name
• `{{order_count}}` - Number of orders

Enter your welcome message:
        """
        
        keyboard = [
            [InlineKeyboardButton("📝 Show All Variables", callback_data="show_variables")],
            [InlineKeyboardButton("❌ Cancel", callback_data="admin_welcome_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return WELCOME_MESSAGE
    
    async def get_custom_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get custom welcome message from user"""
        message = update.message.text.strip()
        
        # Validate message
        if len(message) < 20:
            await update.message.reply_text(
                "❌ Message too short. Please write at least 20 characters.\n"
                "Try again:"
            )
            return WELCOME_MESSAGE
        
        if len(message) > 1000:
            await update.message.reply_text(
                "❌ Message too long. Please keep it under 1000 characters.\n"
                "Try again:"
            )
            return WELCOME_MESSAGE
        
        # Validate variables
        validation = WelcomeMessageVariables.validate_message(message)
        if not validation['valid']:
            await update.message.reply_text(
                f"❌ **Invalid variables found:**\n\n{validation['message']}\n\n"
                f"Use the button below to see available variables, then try again:"
            )
            return WELCOME_MESSAGE
        
        context.user_data['welcome_message'] = message
        
        # Show button configuration
        text = f"""
✅ **Message Saved!**

**Preview:**
{message[:200]}{'...' if len(message) > 200 else ''}

**Variables used:** {len(validation.get('used_variables', []))}

**Now let's configure buttons:**

You can add up to 8 buttons for navigation. Each button needs:
• Button text (what users see)
• Action (what happens when clicked)

**Common actions:** catalog, cart, orders, help, support, deals

Would you like to add custom buttons or use default ones?
        """
        
        keyboard = [
            [InlineKeyboardButton("🎯 Add Custom Buttons", callback_data="add_custom_buttons")],
            [InlineKeyboardButton("⚡ Use Default Buttons", callback_data="use_default_buttons")],
            [InlineKeyboardButton("🚫 No Buttons", callback_data="no_buttons")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return WELCOME_BUTTONS
    
    async def handle_button_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button configuration choice"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "no_buttons":
            context.user_data['welcome_buttons'] = []
            return await self.show_welcome_confirmation(query, context)
        
        elif query.data == "use_default_buttons":
            default_buttons = [
                {"text": "🏪 Browse Products", "action": "catalog"},
                {"text": "🛒 View Cart", "action": "cart"},
                {"text": "📦 My Orders", "action": "orders"},
                {"text": "❓ Help & Support", "action": "help"}
            ]
            context.user_data['welcome_buttons'] = default_buttons
            return await self.show_welcome_confirmation(query, context)
        
        elif query.data == "add_custom_buttons":
            text = """
🎯 **Add Custom Buttons**

Enter buttons in this format (one per line):
```
Button Text | action_name
Another Button | another_action
```

**Examples:**
```
🔥 Hot Deals | deals  
🎁 Special Offers | offers
📞 Contact Us | support
🆕 New Arrivals | new_products
```

**Maximum 8 buttons allowed.**
            """
            
            keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="admin_welcome_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return WELCOME_BUTTONS
        
        return WELCOME_BUTTONS
    
    async def get_custom_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Parse custom buttons from user input"""
        button_text = update.message.text.strip()
        
        if not button_text:
            context.user_data['welcome_buttons'] = []
            return await self.show_welcome_confirmation_message(update, context)
        
        # Parse buttons
        buttons = []
        lines = button_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if '|' in line:
                parts = line.split('|', 1)
                if len(parts) == 2:
                    text = parts[0].strip()
                    action = parts[1].strip()
                    
                    if text and action:
                        buttons.append({
                            "text": text,
                            "action": action
                        })
        
        if len(buttons) > 8:
            await update.message.reply_text(
                "❌ Too many buttons! Maximum 8 allowed.\n"
                "Please reduce the number of buttons and try again:"
            )
            return WELCOME_BUTTONS
        
        if not buttons:
            await update.message.reply_text(
                "❌ No valid buttons found. Please use the format:\n"
                "`Button Text | action_name`\n\n"
                "Try again or type 'none' for no buttons:"
            )
            return WELCOME_BUTTONS
        
        context.user_data['welcome_buttons'] = buttons
        return await self.show_welcome_confirmation_message(update, context)
    
    async def show_welcome_confirmation(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Show welcome message confirmation (from callback)"""
        user_type = context.user_data['welcome_user_type']
        message = context.user_data['welcome_message']
        buttons = context.user_data.get('welcome_buttons', [])
        
        preview_text = f"""
📋 **Confirm Custom Welcome Message**

**User Type:** {user_type.replace('_', ' ').title()}
**Message Length:** {len(message)} characters
**Buttons:** {len(buttons)}

**Message Preview:**
{message[:300]}{'...' if len(message) > 300 else ''}

**Buttons:**
"""
        
        for i, button in enumerate(buttons, 1):
            preview_text += f"{i}. {button['text']} → {button['action']}\n"
        
        if not buttons:
            preview_text += "*No buttons configured*\n"
        
        preview_text += "\n✅ Ready to save this welcome message?"
        
        keyboard = [
            [InlineKeyboardButton("✅ Save Message", callback_data="save_welcome_message")],
            [InlineKeyboardButton("🧪 Test First", callback_data="test_custom_message")],
            [InlineKeyboardButton("✏️ Edit Message", callback_data="edit_welcome_message")],
            [InlineKeyboardButton("❌ Cancel", callback_data="admin_welcome_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(preview_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return WELCOME_CONFIRM
    
    async def show_welcome_confirmation_message(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Show welcome message confirmation (from message)"""
        user_type = context.user_data['welcome_user_type']
        message = context.user_data['welcome_message']
        buttons = context.user_data.get('welcome_buttons', [])
        
        preview_text = f"""
📋 **Confirm Custom Welcome Message**

**User Type:** {user_type.replace('_', ' ').title()}
**Message Length:** {len(message)} characters
**Buttons:** {len(buttons)}

**Message Preview:**
{message[:300]}{'...' if len(message) > 300 else ''}

**Buttons:**
"""
        
        for i, button in enumerate(buttons, 1):
            preview_text += f"{i}. {button['text']} → {button['action']}\n"
        
        if not buttons:
            preview_text += "*No buttons configured*\n"
        
        preview_text += "\n✅ Ready to save this welcome message?"
        
        keyboard = [
            [InlineKeyboardButton("✅ Save Message", callback_data="save_welcome_message")],
            [InlineKeyboardButton("🧪 Test First", callback_data="test_custom_message")],
            [InlineKeyboardButton("✏️ Edit Message", callback_data="edit_welcome_message")],
            [InlineKeyboardButton("❌ Cancel", callback_data="admin_welcome_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(preview_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return WELCOME_CONFIRM
    
    async def save_welcome_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save the custom welcome message"""
        query = update.callback_query
        await query.answer()
        
        user_type = context.user_data['welcome_user_type']
        message = context.user_data['welcome_message']
        buttons = context.user_data.get('welcome_buttons', [])
        
        # Save custom welcome message
        result = self.welcome_system.create_custom_welcome(user_type, message, buttons)
        
        if result['success']:
            success_text = f"""
🎉 **Welcome Message Saved!**

Your custom welcome message for **{user_type.replace('_', ' ').title()}** users is now active!

**What's Next:**
• Test the message to see how it looks
• View analytics to track effectiveness  
• Customize other user types
• Update anytime from this menu

Ready to test your new welcome message?
            """
            
            keyboard = [
                [InlineKeyboardButton("🧪 Test Message", callback_data=f"test_{user_type}")],
                [InlineKeyboardButton("📊 View Analytics", callback_data="welcome_analytics")],
                [InlineKeyboardButton("✨ Customize More", callback_data="customize_welcome")],
                [InlineKeyboardButton("🏠 Back to Menu", callback_data="admin_welcome_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(success_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            
        else:
            await query.edit_message_text(f"❌ **Error saving message:**\n\n{result['message']}")
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
    
    async def test_welcome_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test welcome message for a user type"""
        query = update.callback_query
        await query.answer()
        
        # Extract user type from callback data
        if query.data.startswith("test_"):
            user_type = query.data.replace("test_", "")
        else:
            await query.edit_message_text("❌ Invalid test request.")
            return
        
        # Test the message
        result = self.welcome_system.test_welcome_message(user_type, "Test User")
        
        if result['success']:
            preview = result['preview']
            
            test_text = f"""
🧪 **Welcome Message Test**

**User Type:** {user_type.replace('_', ' ').title()}
**Template:** {preview['template_name']}

**How it would look:**
━━━━━━━━━━━━━━━━
{preview['message']}
━━━━━━━━━━━━━━━━

**Buttons ({len(preview['buttons'])}):**
"""
            
            for i, button in enumerate(preview['buttons'], 1):
                test_text += f"{i}. {button['text']}\n"
            
            test_text += "\n**Test completed!** This is how the message appears to users."
            
            keyboard = [
                [InlineKeyboardButton("✏️ Edit Message", callback_data=f"customize_{user_type}")],
                [InlineKeyboardButton("🎨 Try Different Template", callback_data="welcome_templates")],
                [InlineKeyboardButton("✅ Looks Good!", callback_data="admin_welcome_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(test_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            
        else:
            await query.edit_message_text(f"❌ **Test failed:**\n\n{result['message']}")
    
    async def show_variables(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show available personalization variables"""
        query = update.callback_query
        await query.answer()
        
        help_text = WelcomeMessageVariables.get_help_text()
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back", callback_data="customize_welcome")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_welcome_analytics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show welcome message analytics"""
        query = update.callback_query
        await query.answer()
        
        analytics = self.welcome_system.get_welcome_analytics()
        
        analytics_text = f"""
📊 **Welcome Message Analytics**

**User Base Overview:**
• Total Users: {analytics['total_users']:,}
• Conversion Rate: {analytics['conversion_rate']:.1f}%
• New Users (Last 7 days): {analytics['recent_new_users']}

**User Distribution:**
• 🆕 New Users: {analytics['new_users']} ({analytics['new_users']/analytics['total_users']*100:.1f}% of total)
• 🔄 Returning: {analytics['returning_users']} ({analytics['returning_users']/analytics['total_users']*100:.1f}% of total)
• 👑 VIP Users: {analytics['vip_users']} ({analytics['vip_users']/analytics['total_users']*100:.1f}% of total)

**Insights:**
• {analytics['conversion_rate']:.0f} out of 100 new users make a purchase
• You have {analytics['vip_users']} high-value customers
• Recent growth: {analytics['recent_new_users']} new users this week

**Recommendations:**
• Focus on converting {analytics['new_users']} new users
• Reward your {analytics['vip_users']} VIP customers
• Re-engage {analytics['returning_users']} returning users
        """
        
        keyboard = [
            [InlineKeyboardButton("✨ Optimize Messages", callback_data="customize_welcome")],
            [InlineKeyboardButton("🧪 Test Different Approaches", callback_data="test_welcome")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_welcome_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(analytics_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    def _is_admin(self, user_id):
        """Check if user is admin"""
        admin_ids = [123456789]  # Replace with actual admin IDs
        return user_id in admin_ids
    
    async def cancel_welcome_customization(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel welcome customization"""
        if update.callback_query:
            await update.callback_query.edit_message_text("❌ Welcome message customization cancelled.")
        else:
            await update.message.reply_text("❌ Welcome message customization cancelled.")
        
        context.user_data.clear()
        return ConversationHandler.END

def get_welcome_conversation_handler():
    """Get conversation handler for welcome message customization"""
    welcome_commands = WelcomeCommands()
    
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(welcome_commands.start_welcome_customization, pattern="^customize_(new_user|returning|vip)$")
        ],
        states={
            WELCOME_TEMPLATE: [
                CallbackQueryHandler(welcome_commands.handle_template_selection, pattern="^(template_|create_custom)"),
            ],
            WELCOME_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, welcome_commands.get_custom_message)
            ],
            WELCOME_BUTTONS: [
                CallbackQueryHandler(welcome_commands.handle_button_selection, pattern="^(add_custom_buttons|use_default_buttons|no_buttons)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, welcome_commands.get_custom_buttons)
            ],
            WELCOME_CONFIRM: [
                CallbackQueryHandler(welcome_commands.save_welcome_message, pattern="^save_welcome_message$"),
                CallbackQueryHandler(welcome_commands.test_welcome_message, pattern="^test_custom_message$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(welcome_commands.cancel_welcome_customization, pattern="^admin_welcome_menu$"),
            CommandHandler('cancel', welcome_commands.cancel_welcome_customization)
        ],
        per_message=False
    )