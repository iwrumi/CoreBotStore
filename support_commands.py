"""
Customer support commands and handlers for Telegram bot
"""
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from telegram.constants import ParseMode
from support_system import CustomerSupportSystem, SupportTicketStatus, SupportTicketPriority, SupportNotifications
from advanced_data_manager import AdvancedDataManager

# Conversation states
TICKET_SUBJECT, TICKET_MESSAGE, TICKET_PRIORITY, SUPPORT_QUERY = range(4)

class SupportCommands:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.support_system = CustomerSupportSystem()
        self.data_manager = AdvancedDataManager()
        self.support_notifications = SupportNotifications()
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main help command"""
        help_text = """
❓ **Need Help?** 

I'm here to assist you! Here's what I can help with:

**Quick Help:**
• 🛍️ **Shopping** - Browse products and place orders
• 💳 **Payments** - Payment methods and verification
• 🚚 **Delivery** - Shipping info and tracking
• 📦 **Orders** - Order status and history
• 🎫 **Support** - Get help or report issues

**How to Get Help:**
• Browse FAQs by category
• Ask me any question
• Create a support ticket
• Contact our team directly

What would you like help with?
        """
        
        keyboard = [
            [InlineKeyboardButton("📚 Browse FAQs", callback_data="browse_faqs")],
            [InlineKeyboardButton("❓ Ask a Question", callback_data="ask_question")],
            [InlineKeyboardButton("🎫 Create Support Ticket", callback_data="create_ticket")],
            [InlineKeyboardButton("📞 Contact Info", callback_data="contact_info")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def support_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Support ticket management command"""
        user_telegram_id = str(update.effective_user.id)
        user_tickets = self.support_system.get_user_tickets(user_telegram_id)
        
        if not user_tickets:
            text = """
🎫 **Your Support Tickets**

You don't have any support tickets yet.

**Need Help?**
• Browse our FAQ for instant answers
• Ask me a question directly  
• Create a support ticket for complex issues

How can I help you today?
            """
            
            keyboard = [
                [InlineKeyboardButton("📚 Browse FAQs", callback_data="browse_faqs")],
                [InlineKeyboardButton("❓ Ask Question", callback_data="ask_question")],
                [InlineKeyboardButton("🎫 Create Ticket", callback_data="create_ticket")]
            ]
        else:
            text = f"🎫 **Your Support Tickets ({len(user_tickets)})**\n\n"
            keyboard = []
            
            for ticket in user_tickets[-10:]:  # Show last 10 tickets
                status_emoji = {
                    'open': '🔓',
                    'in_progress': '⚙️',
                    'resolved': '✅',
                    'closed': '🔒'
                }.get(ticket['status'], '❓')
                
                priority_emoji = {
                    'low': '🟢',
                    'medium': '🟡', 
                    'high': '🟠',
                    'urgent': '🔴'
                }.get(ticket['priority'], '⚪')
                
                text += f"{status_emoji} **{ticket['ticket_number']}** {priority_emoji}\n"
                text += f"   {ticket['subject'][:40]}{'...' if len(ticket['subject']) > 40 else ''}\n"
                text += f"   Status: {ticket['status'].title()} | {ticket['created_at'][:10]}\n\n"
                
                keyboard.append([InlineKeyboardButton(
                    f"📄 {ticket['ticket_number']}",
                    callback_data=f"view_ticket_{ticket['id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("🆕 Create New Ticket", callback_data="create_ticket")])
        
        keyboard.append([InlineKeyboardButton("❓ Help & FAQs", callback_data="browse_faqs")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def browse_faqs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show FAQ categories"""
        query = update.callback_query
        await query.answer()
        
        categories = self.support_system.get_faq_categories()
        
        text = """
📚 **Frequently Asked Questions**

Browse by category to find quick answers to common questions:
        """
        
        keyboard = []
        for category in categories:
            keyboard.append([InlineKeyboardButton(
                f"{category['icon']} {category['name']} ({category['question_count']})",
                callback_data=f"faq_category_{category['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔍 Search FAQs", callback_data="search_faqs")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="help_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_faq_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show FAQs in a specific category"""
        query = update.callback_query
        await query.answer()
        
        category_id = query.data.replace("faq_category_", "")
        category_data = self.support_system.get_category_faqs(category_id)
        
        if not category_data:
            await query.edit_message_text("❌ Category not found.")
            return
        
        text = f"📚 **{category_data['category']}**\n\n"
        keyboard = []
        
        for i, faq in enumerate(category_data['questions']):
            text += f"**{i+1}.** {faq['q']}\n"
            keyboard.append([InlineKeyboardButton(
                f"💡 {faq['q'][:30]}...",
                callback_data=f"show_faq_{category_id}_{i}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Categories", callback_data="browse_faqs")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_faq_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show specific FAQ answer"""
        query = update.callback_query
        await query.answer()
        
        # Parse callback data: show_faq_{category_id}_{faq_index}
        parts = query.data.split('_')
        category_id = parts[2]
        faq_index = int(parts[3])
        
        category_data = self.support_system.get_category_faqs(category_id)
        if not category_data or faq_index >= len(category_data['questions']):
            await query.edit_message_text("❌ FAQ not found.")
            return
        
        faq = category_data['questions'][faq_index]
        
        text = f"💡 **{faq['q']}**\n\n{faq['a']}\n\n"
        text += "**Was this helpful?**"
        
        keyboard = [
            [
                InlineKeyboardButton("👍 Yes", callback_data=f"faq_helpful_{category_id}_{faq_index}"),
                InlineKeyboardButton("👎 No", callback_data=f"faq_not_helpful_{category_id}_{faq_index}")
            ],
            [InlineKeyboardButton("🎫 Still Need Help", callback_data="create_ticket")],
            [InlineKeyboardButton("🔙 Back to Category", callback_data=f"faq_category_{category_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def ask_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle direct questions from users"""
        query = update.callback_query
        await query.answer()
        
        text = """
❓ **Ask Me Anything!**

Type your question below and I'll try to help you instantly:

**Examples:**
• "How do I track my order?"
• "What payment methods do you accept?"
• "How long does delivery take?"
• "Can I change my order?"

**Tips:**
• Be specific about your question
• Include order numbers if relevant
• Ask one question at a time

What's your question?
        """
        
        keyboard = [
            [InlineKeyboardButton("📚 Browse FAQs Instead", callback_data="browse_faqs")],
            [InlineKeyboardButton("❌ Cancel", callback_data="help_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SUPPORT_QUERY
    
    async def handle_user_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user's question and provide automated response"""
        user_message = update.message.text.strip()
        user_telegram_id = str(update.effective_user.id)
        
        if len(user_message) < 5:
            await update.message.reply_text(
                "❌ Please ask a more detailed question (at least 5 characters).\n"
                "Try again:"
            )
            return SUPPORT_QUERY
        
        # Try to auto-respond
        auto_response = self.support_system.auto_respond_to_query(user_message, user_telegram_id)
        
        if auto_response and auto_response['confidence'] == 'high':
            # High confidence auto-response
            response_text = f"""
🤖 **I can help with that!**

{auto_response['response']}

**Was this helpful?**
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("👍 Yes, thank you!", callback_data="auto_response_helpful"),
                    InlineKeyboardButton("👎 Not quite", callback_data="auto_response_not_helpful")
                ],
                [InlineKeyboardButton("🎫 Create Support Ticket", callback_data="create_ticket")],
                [InlineKeyboardButton("❓ Ask Another Question", callback_data="ask_question")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(response_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
            
        elif auto_response and auto_response['confidence'] == 'medium':
            # Medium confidence - show suggestion
            response_text = f"""
💭 **I think this might help:**

{auto_response['response']}

**Is this what you were looking for?**
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Yes, that helps!", callback_data="auto_response_helpful"),
                    InlineKeyboardButton("❌ No, I need more help", callback_data="need_more_help")
                ],
                [InlineKeyboardButton("🎫 Create Support Ticket", callback_data="create_ticket")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(response_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
        
        else:
            # No good auto-response found
            # Search FAQs and show suggestions
            faq_suggestions = self.support_system.suggest_faqs_for_query(user_message)
            
            response_text = """
🤔 **I'm not sure about that specific question.**

Let me suggest some related topics that might help:
            """
            
            keyboard = []
            if faq_suggestions:
                for i, suggestion in enumerate(faq_suggestions):
                    keyboard.append([InlineKeyboardButton(
                        f"💡 {suggestion[:40]}...",
                        callback_data=f"search_faq_{i}"
                    )])
                
                # Store suggestions in context for callback handling
                context.user_data['faq_suggestions'] = faq_suggestions
                context.user_data['user_query'] = user_message
            
            keyboard.extend([
                [InlineKeyboardButton("🎫 Create Support Ticket", callback_data="create_ticket")],
                [InlineKeyboardButton("📞 Contact Human Support", callback_data="contact_info")],
                [InlineKeyboardButton("❓ Try Different Question", callback_data="ask_question")]
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(response_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
    
    async def create_support_ticket(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start support ticket creation"""
        query = update.callback_query
        await query.answer()
        
        text = """
🎫 **Create Support Ticket**

I'll help you create a support ticket for our team to assist you personally.

**Step 1: Subject**
Please enter a brief subject/title for your issue:

**Examples:**
• "Payment not confirmed after 24 hours"
• "Wrong item received in order #12345"  
• "Cannot access my account"
• "Delivery address change request"

What's the subject of your ticket?
        """
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="help_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return TICKET_SUBJECT
    
    async def get_ticket_subject(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get ticket subject from user"""
        subject = update.message.text.strip()
        
        if len(subject) < 5 or len(subject) > 100:
            await update.message.reply_text(
                "❌ Subject must be 5-100 characters long. Please try again:\n\n"
                "**Examples:**\n"
                "• Payment not confirmed\n"
                "• Wrong item received\n"
                "• Delivery issue"
            )
            return TICKET_SUBJECT
        
        context.user_data['ticket_subject'] = subject
        
        text = f"""
✅ **Subject saved:** {subject}

**Step 2: Detailed Message**
Please describe your issue in detail. Include any relevant information:

**Helpful Details:**
• Order numbers (if applicable)
• Payment reference numbers  
• Error messages you received
• What you expected vs what happened
• Steps you've already tried

The more details you provide, the faster we can help!
        """
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="help_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return TICKET_MESSAGE
    
    async def get_ticket_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get detailed ticket message"""
        message = update.message.text.strip()
        
        if len(message) < 20:
            await update.message.reply_text(
                "❌ Please provide more details (at least 20 characters).\n"
                "The more information you provide, the better we can help you!"
            )
            return TICKET_MESSAGE
        
        if len(message) > 1000:
            await update.message.reply_text(
                "❌ Message is too long (max 1000 characters).\n"
                "Please summarize your issue:"
            )
            return TICKET_MESSAGE
        
        context.user_data['ticket_message'] = message
        
        # Show priority selection
        text = f"""
✅ **Message saved!**

**Step 3: Priority Level**
How urgent is your issue?

**Priority Levels:**
• 🟢 **Low** - General questions, non-urgent
• 🟡 **Medium** - Order issues, account problems  
• 🟠 **High** - Payment issues, wrong orders
• 🔴 **Urgent** - Account security, urgent delivery issues

**Your Issue:**
{context.user_data['ticket_subject']}
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🟢 Low", callback_data="priority_low"),
                InlineKeyboardButton("🟡 Medium", callback_data="priority_medium")
            ],
            [
                InlineKeyboardButton("🟠 High", callback_data="priority_high"),
                InlineKeyboardButton("🔴 Urgent", callback_data="priority_urgent")
            ],
            [InlineKeyboardButton("❌ Cancel", callback_data="help_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return TICKET_PRIORITY
    
    async def set_ticket_priority(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set ticket priority and create ticket"""
        query = update.callback_query
        await query.answer()
        
        priority_map = {
            "priority_low": SupportTicketPriority.LOW,
            "priority_medium": SupportTicketPriority.MEDIUM,
            "priority_high": SupportTicketPriority.HIGH,
            "priority_urgent": SupportTicketPriority.URGENT
        }
        
        priority = priority_map.get(query.data, SupportTicketPriority.MEDIUM)
        user_telegram_id = str(update.effective_user.id)
        
        # Create the support ticket
        result = self.support_system.create_support_ticket(
            user_telegram_id=user_telegram_id,
            subject=context.user_data['ticket_subject'],
            message=context.user_data['ticket_message'],
            priority=priority
        )
        
        if result['success']:
            ticket = result['ticket']
            
            success_text = f"""
🎉 **Support Ticket Created!**

**Ticket Number:** #{ticket['ticket_number']}
**Subject:** {ticket['subject']}
**Priority:** {priority.title()}
**Status:** Open

📧 **What happens next:**
• Our team will review your ticket
• You'll receive a response within 24 hours
• Updates will be sent to this chat
• Use /support to view ticket status

**Response Time:**
• 🔴 Urgent: Within 4 hours
• 🟠 High: Within 8 hours  
• 🟡 Medium: Within 24 hours
• 🟢 Low: Within 48 hours

Thank you for contacting us! We'll help resolve this quickly. 🤝
            """
            
            keyboard = [
                [InlineKeyboardButton("📄 View My Tickets", callback_data="view_my_tickets")],
                [InlineKeyboardButton("❓ More Help", callback_data="help_menu")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(success_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            
            # Send notifications
            await self.support_notifications.notify_ticket_created(user_telegram_id, ticket)
            await self.support_notifications.notify_admin_new_ticket(ticket)
            
        else:
            await query.edit_message_text(f"❌ **Error creating ticket:**\n\n{result['message']}")
        
        # Clear context
        context.user_data.clear()
        return ConversationHandler.END
    
    async def show_contact_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show contact information"""
        query = update.callback_query
        await query.answer()
        
        text = """
📞 **Contact Information**

**Customer Support:**
• 📧 Email: support@yourstore.com
• 📱 Phone: +63 (2) 123-4567
• 💬 Live Chat: Available in this bot 24/7

**Business Hours:**
• Monday - Friday: 9:00 AM - 6:00 PM
• Saturday: 9:00 AM - 5:00 PM  
• Sunday: Closed

**Response Times:**
• Bot responses: Instant 🤖
• Live chat: Within 30 minutes ⚡
• Email/tickets: Within 24 hours 📧
• Phone: Immediate during business hours ☎️

**Emergency Contact:**
For urgent order issues outside business hours, create a high-priority support ticket and we'll respond ASAP!

**Social Media:**
• Facebook: @YourStore
• Instagram: @yourstore_official

We're here to help make your shopping experience amazing! 🌟
        """
        
        keyboard = [
            [InlineKeyboardButton("🎫 Create Support Ticket", callback_data="create_ticket")],
            [InlineKeyboardButton("📚 Browse FAQs", callback_data="browse_faqs")],
            [InlineKeyboardButton("🔙 Back to Help", callback_data="help_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    def _is_admin(self, user_id):
        """Check if user is admin"""
        admin_ids = [123456789]  # Replace with actual admin IDs
        return user_id in admin_ids
    
    async def cancel_support_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel support action"""
        if update.callback_query:
            await update.callback_query.edit_message_text("❌ Action cancelled.")
        else:
            await update.message.reply_text("❌ Action cancelled.")
        
        context.user_data.clear()
        return ConversationHandler.END

class AdminSupportCommands:
    """Admin commands for managing support system"""
    
    def __init__(self):
        self.support_system = CustomerSupportSystem()
        self.data_manager = AdvancedDataManager()
    
    async def admin_support_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show support management menu for admins"""
        user_id = update.effective_user.id
        
        # Check admin permissions  
        if not self._is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        # Get support analytics
        analytics = self.support_system.get_support_analytics()
        pending_tickets = self.support_system.get_pending_tickets()
        
        menu_text = f"""
🎫 **Support Management**

**Current Status:**
• Open Tickets: {len(pending_tickets)}
• Total Tickets: {analytics['total_tickets']}
• Resolution Rate: {analytics['resolution_rate']:.1f}%
• Avg Response Time: {analytics['avg_response_time']}

**Recent Activity:**
• New Tickets (7 days): {analytics['recent_tickets']}

**Quick Actions:**
• Review pending tickets
• Manage FAQ database
• View support analytics
• Update quick responses

Choose an option below:
        """
        
        keyboard = [
            [InlineKeyboardButton(f"🔓 Open Tickets ({len(pending_tickets)})", callback_data="admin_open_tickets")],
            [InlineKeyboardButton("📊 Support Analytics", callback_data="admin_support_analytics")],
            [InlineKeyboardButton("📚 Manage FAQs", callback_data="admin_manage_faqs")],
            [InlineKeyboardButton("⚙️ Support Settings", callback_data="admin_support_settings")],
            [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    def _is_admin(self, user_id):
        """Check if user is admin"""
        admin_ids = [123456789]  # Replace with actual admin IDs
        return user_id in admin_ids

def get_support_conversation_handler(bot_token):
    """Get conversation handler for support system"""
    support_commands = SupportCommands(bot_token)
    
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(support_commands.create_support_ticket, pattern="^create_ticket$"),
            CallbackQueryHandler(support_commands.ask_question, pattern="^ask_question$")
        ],
        states={
            TICKET_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, support_commands.get_ticket_subject)],
            TICKET_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, support_commands.get_ticket_message)],
            TICKET_PRIORITY: [CallbackQueryHandler(support_commands.set_ticket_priority, pattern="^priority_")],
            SUPPORT_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, support_commands.handle_user_question)]
        },
        fallbacks=[
            CallbackQueryHandler(support_commands.cancel_support_action, pattern="^help_menu$"),
            CommandHandler('cancel', support_commands.cancel_support_action)
        ],
        per_message=False
    )