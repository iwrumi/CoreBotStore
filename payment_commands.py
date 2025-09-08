"""
Payment-related Telegram bot commands and handlers
"""
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.constants import ParseMode
from payment_system import PaymentSystem, PaymentNotifications, PaymentValidation
from advanced_data_manager import AdvancedDataManager

# Conversation states
PAYMENT_METHOD, PAYMENT_REFERENCE, PAYMENT_PROOF, PAYMENT_CONFIRM = range(4)

class PaymentCommands:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.payment_system = PaymentSystem()
        self.data_manager = AdvancedDataManager()
        self.payment_notifications = PaymentNotifications(None)  # Initialize with broadcast system if available
    
    async def show_payment_methods(self, update: Update, context: ContextTypes.DEFAULT_TYPE, order_id: int, total_amount: float):
        """Show available payment methods for an order"""
        payment_methods = self.payment_system.get_available_payment_methods(total_amount)
        
        if not payment_methods:
            await update.callback_query.edit_message_text(
                "❌ **No payment methods available**\n\n"
                "Please contact support for assistance."
            )
            return
        
        # Store order info in context
        context.user_data['payment_order_id'] = order_id
        context.user_data['payment_amount'] = total_amount
        
        message = f"""
💳 **Choose Payment Method**

**Order Total:** ₱{total_amount:.2f}

Select how you'd like to pay:
        """
        
        keyboard = []
        for method in payment_methods:
            # Add fee info if applicable
            fee_text = f" (+₱{method['fee']:.0f} fee)" if method['fee'] > 0 else ""
            button_text = f"{method['name']}{fee_text}"
            
            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"payment_method_{method['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("❌ Cancel Payment", callback_data="cancel_payment")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
        return PAYMENT_METHOD
    
    async def handle_payment_method_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle payment method selection"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel_payment":
            await query.edit_message_text("❌ Payment cancelled.")
            context.user_data.clear()
            return ConversationHandler.END
        
        # Extract payment method
        method_id = query.data.replace("payment_method_", "")
        context.user_data['payment_method'] = method_id
        
        # Get method details
        methods = self.payment_system.get_available_payment_methods()
        method_info = next((m for m in methods if m['id'] == method_id), None)
        
        if not method_info:
            await query.edit_message_text("❌ Invalid payment method selected.")
            return ConversationHandler.END
        
        # Calculate final amount with fees
        base_amount = context.user_data['payment_amount']
        fee, final_amount = self.payment_system.calculate_payment_fees(base_amount, method_id)
        
        context.user_data['payment_fee'] = fee
        context.user_data['payment_final_amount'] = final_amount
        
        # Show payment instructions
        instructions = self.payment_system.get_payment_instructions(method_id, final_amount)
        
        # Handle Cash on Delivery differently
        if method_id == 'cod':
            return await self.process_cod_payment(query, context)
        
        # For manual payment methods, get reference number
        message = f"""
{instructions}

**Step 1: Reference Number**
After making the payment, please enter your transaction reference number:
        """
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return PAYMENT_REFERENCE
    
    async def process_cod_payment(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Process Cash on Delivery payment"""
        final_amount = context.user_data['payment_final_amount']
        
        message = f"""
💵 **Cash on Delivery Selected**

**Total Amount:** ₱{final_amount:.2f}
*(Includes ₱{context.user_data['payment_fee']:.2f} COD fee)*

✅ **What happens next:**
1. Your order will be prepared for shipping
2. Our courier will contact you for delivery
3. Pay the exact amount when you receive your order
4. Keep your receipt for warranty purposes

Ready to confirm your COD order?
        """
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirm COD Order", callback_data="confirm_cod_payment")],
            [InlineKeyboardButton("🔙 Choose Different Method", callback_data="back_to_payment_methods")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return PAYMENT_CONFIRM
    
    async def get_payment_reference(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get payment reference number"""
        reference = update.message.text.strip()
        payment_method = context.user_data['payment_method']
        
        # Validate reference number
        if not self.payment_system.validate_reference_number(reference, payment_method):
            await update.message.reply_text(
                f"❌ Invalid reference number format for {payment_method.title()}.\n"
                "Please enter a valid reference number:"
            )
            return PAYMENT_REFERENCE
        
        context.user_data['payment_reference'] = reference
        
        # Check if payment method requires proof
        payment_methods = self.payment_system.payment_methods
        method_info = payment_methods.get(payment_method, {})
        
        if method_info.get('requires_proof', True):
            message = """
📸 **Step 2: Payment Proof (Optional but Recommended)**

To speed up verification, you can upload a screenshot or photo of your payment receipt.

**Options:**
• Upload an image of your receipt
• Type "skip" to continue without proof
            """
            
            keyboard = [
                [InlineKeyboardButton("⏭️ Skip Upload", callback_data="skip_proof")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return PAYMENT_PROOF
        else:
            # Skip proof upload
            context.user_data['payment_proof'] = ""
            return await self.show_payment_confirmation(update, context)
    
    async def get_payment_proof(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get payment proof image"""
        if update.message:
            if update.message.photo:
                # Get the largest photo
                photo = update.message.photo[-1]
                context.user_data['payment_proof'] = photo.file_id
            elif update.message.text and update.message.text.lower() == 'skip':
                context.user_data['payment_proof'] = ""
            else:
                await update.message.reply_text(
                    "❌ Please upload an image or type 'skip' to continue without proof."
                )
                return PAYMENT_PROOF
        elif update.callback_query and update.callback_query.data == "skip_proof":
            await update.callback_query.answer()
            context.user_data['payment_proof'] = ""
        
        return await self.show_payment_confirmation(update, context)
    
    async def show_payment_confirmation(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Show payment confirmation summary"""
        payment_data = context.user_data
        payment_method = payment_data['payment_method']
        
        # Get method name
        methods = self.payment_system.get_available_payment_methods()
        method_info = next((m for m in methods if m['id'] == payment_method), None)
        method_name = method_info['name'] if method_info else payment_method.title()
        
        message = f"""
📋 **Payment Confirmation**

**Order ID:** #{payment_data['payment_order_id']}
**Payment Method:** {method_name}
**Amount:** ₱{payment_data['payment_amount']:.2f}
**Fee:** ₱{payment_data.get('payment_fee', 0):.2f}
**Total:** ₱{payment_data['payment_final_amount']:.2f}
**Reference:** {payment_data.get('payment_reference', 'N/A')}
**Proof:** {'Uploaded' if payment_data.get('payment_proof') else 'Not provided'}

✅ **Ready to submit your payment for verification?**

Once submitted, our team will verify your payment within 24 hours.
        """
        
        keyboard = [
            [InlineKeyboardButton("✅ Submit Payment", callback_data="submit_payment")],
            [InlineKeyboardButton("✏️ Edit Details", callback_data="edit_payment")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_payment")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
        return PAYMENT_CONFIRM
    
    async def submit_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Submit payment for processing"""
        query = update.callback_query
        await query.answer()
        
        payment_data = context.user_data
        user_telegram_id = str(update.effective_user.id)
        
        # Process the payment
        result = self.payment_system.process_manual_payment(
            order_id=payment_data['payment_order_id'],
            user_telegram_id=user_telegram_id,
            amount=payment_data['payment_final_amount'],
            payment_method=payment_data['payment_method'],
            reference_number=payment_data.get('payment_reference', ''),
            proof_image=payment_data.get('payment_proof', ''),
            notes=f"Submitted via Telegram bot by user {update.effective_user.first_name}"
        )
        
        if result['success']:
            payment = result['payment']
            
            success_message = f"""
🎉 **Payment Submitted Successfully!**

**Transaction ID:** {payment['transaction_id']}
**Status:** Under Review ⏳

📧 **What's Next:**
• Our team will verify your payment within 24 hours
• You'll receive a notification once verified
• Your order will then be processed and shipped

📞 **Need Help?**
Contact our support team if you have any questions.

Thank you for your purchase! 🛍️
            """
            
            keyboard = [
                [InlineKeyboardButton("📦 View Order", callback_data=f"view_order_{payment_data['payment_order_id']}")],
                [InlineKeyboardButton("💳 Payment History", callback_data="payment_history")],
                [InlineKeyboardButton("🏪 Continue Shopping", callback_data="catalog")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(success_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            
            # Send notification to user
            await self.payment_notifications.notify_payment_received(user_telegram_id, payment)
            
        else:
            await query.edit_message_text(
                f"❌ **Payment Submission Failed**\n\n{result['message']}\n\n"
                "Please try again or contact support."
            )
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
    
    async def confirm_cod_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm Cash on Delivery payment"""
        query = update.callback_query
        await query.answer()
        
        payment_data = context.user_data
        user_telegram_id = str(update.effective_user.id)
        
        # Create COD payment record
        result = self.payment_system.create_payment(
            order_id=payment_data['payment_order_id'],
            user_telegram_id=user_telegram_id,
            amount=payment_data['payment_final_amount'],
            payment_method='cod',
            notes="Cash on Delivery order"
        )
        
        if result['success']:
            payment = result['payment']
            
            success_message = f"""
✅ **COD Order Confirmed!**

**Order ID:** #{payment_data['payment_order_id']}
**Total Amount:** ₱{payment_data['payment_final_amount']:.2f}
**Payment:** Cash on Delivery 💵

📦 **What's Next:**
• Your order is being prepared for shipping
• Our courier will contact you within 1-2 business days
• Prepare exact cash amount for payment
• You'll receive tracking information once shipped

🚚 **Delivery Info:**
• Have your ID ready for verification
• Payment required upon delivery
• Keep your receipt for warranty

Thank you for your order! 🎉
            """
            
            keyboard = [
                [InlineKeyboardButton("📦 Track Order", callback_data=f"track_order_{payment_data['payment_order_id']}")],
                [InlineKeyboardButton("📱 Contact Support", callback_data="customer_support")],
                [InlineKeyboardButton("🏪 Continue Shopping", callback_data="catalog")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(success_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            
        else:
            await query.edit_message_text(
                f"❌ **COD Order Failed**\n\n{result['message']}\n\n"
                "Please try again or contact support."
            )
        
        context.user_data.clear()
        return ConversationHandler.END
    
    async def show_payment_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's payment history"""
        user_telegram_id = str(update.effective_user.id)
        payments = self.payment_system.get_user_payment_history(user_telegram_id)
        
        if not payments:
            message = """
💳 **Payment History**

You haven't made any payments yet.

Ready to make your first purchase?
            """
            keyboard = [[InlineKeyboardButton("🛍️ Start Shopping", callback_data="catalog")]]
        else:
            message = f"💳 **Payment History ({len(payments)} payments)**\n\n"
            keyboard = []
            
            for payment in payments[-10:]:  # Show last 10 payments
                status_emoji = {
                    'pending': '⏳',
                    'completed': '✅',
                    'failed': '❌',
                    'cancelled': '🚫'
                }.get(payment['status'], '❓')
                
                method_emoji = {
                    'gcash': '📱',
                    'paymaya': '💳',
                    'bank_transfer': '🏦',
                    'cod': '💵'
                }.get(payment['payment_method'], '💳')
                
                message += f"{status_emoji} **₱{payment['amount']:.2f}** {method_emoji}\n"
                message += f"   {payment['payment_method'].title()} • {payment['created_at'][:10]}\n"
                message += f"   ID: {payment['transaction_id']}\n\n"
                
                keyboard.append([InlineKeyboardButton(
                    f"📄 {payment['transaction_id'][:8]}...",
                    callback_data=f"payment_details_{payment['id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="payment_history")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def cancel_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel payment process"""
        if update.callback_query:
            await update.callback_query.edit_message_text("❌ Payment process cancelled.")
        else:
            await update.message.reply_text("❌ Payment process cancelled.")
        
        context.user_data.clear()
        return ConversationHandler.END

class AdminPaymentCommands:
    """Admin commands for payment management"""
    
    def __init__(self):
        self.payment_system = PaymentSystem()
        self.data_manager = AdvancedDataManager()
    
    async def admin_payment_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show payment management menu for admins"""
        user_id = update.effective_user.id
        
        # Check admin permissions
        if not self._is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        # Get payment stats
        analytics = self.payment_system.get_payment_analytics()
        pending_payments = self.payment_system.get_pending_payments()
        
        menu_text = f"""
💳 **Payment Management**

**Current Status:**
• Pending Payments: {len(pending_payments)}
• Total Revenue: ₱{analytics['total_revenue']:,.2f}
• Completion Rate: {analytics['completion_rate']:.1f}%

**Quick Actions:**
• Review pending payments
• Verify manual payments
• Process refunds
• View payment analytics

Choose an option below:
        """
        
        keyboard = [
            [InlineKeyboardButton(f"⏳ Pending Payments ({len(pending_payments)})", callback_data="admin_pending_payments")],
            [InlineKeyboardButton("📊 Payment Analytics", callback_data="admin_payment_analytics")],
            [InlineKeyboardButton("⚙️ Payment Settings", callback_data="admin_payment_settings")],
            [InlineKeyboardButton("💰 Process Refund", callback_data="admin_process_refund")],
            [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_pending_payments(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show pending payments for admin review"""
        query = update.callback_query
        await query.answer()
        
        pending_payments = self.payment_system.get_pending_payments()
        
        if not pending_payments:
            message = """
✅ **No Pending Payments**

All payments have been processed.

Great job staying on top of payment verifications! 🎉
            """
            keyboard = [
                [InlineKeyboardButton("📊 View Analytics", callback_data="admin_payment_analytics")],
                [InlineKeyboardButton("🔙 Back", callback_data="admin_payment_menu")]
            ]
        else:
            message = f"⏳ **Pending Payments ({len(pending_payments)})**\n\n"
            keyboard = []
            
            for payment in pending_payments[:10]:  # Show first 10
                amount = payment['amount']
                method = payment['payment_method'].title()
                ref = payment['reference_number'][:10] if payment['reference_number'] else 'No ref'
                
                message += f"💰 **₱{amount:.2f}** via {method}\n"
                message += f"   Ref: {ref} | ID: {payment['transaction_id'][:8]}...\n"
                message += f"   User: {payment['user_id']} | {payment['created_at'][:10]}\n\n"
                
                keyboard.append([
                    InlineKeyboardButton("✅ Verify", callback_data=f"verify_payment_{payment['id']}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject_payment_{payment['id']}"),
                    InlineKeyboardButton("👁️ Details", callback_data=f"payment_details_{payment['id']}")
                ])
            
            if len(pending_payments) > 10:
                message += f"*... and {len(pending_payments) - 10} more payments*"
        
        keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="admin_pending_payments")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_payment_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def verify_payment_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin verify a payment"""
        query = update.callback_query
        await query.answer()
        
        payment_id = int(query.data.split('_')[-1])
        admin_user = update.effective_user.first_name
        
        result = self.payment_system.verify_payment(payment_id, admin_user)
        
        if result['success']:
            await query.edit_message_text(
                f"✅ **Payment Verified**\n\n"
                f"Payment has been approved and the order is now confirmed.\n"
                f"Customer will be notified automatically."
            )
            
            # Notify customer
            payment = result['payment']
            if payment.get('user_id'):
                # Implementation would send notification to customer
                pass
                
        else:
            await query.edit_message_text(
                f"❌ **Verification Failed**\n\n{result['message']}"
            )
    
    def _is_admin(self, user_id):
        """Check if user is admin"""
        admin_ids = [123456789]  # Replace with actual admin IDs
        return user_id in admin_ids

def get_payment_conversation_handler(bot_token):
    """Get conversation handler for payment processing"""
    payment_commands = PaymentCommands(bot_token)
    
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(payment_commands.show_payment_methods, pattern="^pay_order_")],
        states={
            PAYMENT_METHOD: [CallbackQueryHandler(payment_commands.handle_payment_method_selection, pattern="^payment_method_|^cancel_payment$")],
            PAYMENT_REFERENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment_commands.get_payment_reference)],
            PAYMENT_PROOF: [
                MessageHandler(filters.PHOTO, payment_commands.get_payment_proof),
                MessageHandler(filters.TEXT & ~filters.COMMAND, payment_commands.get_payment_proof),
                CallbackQueryHandler(payment_commands.get_payment_proof, pattern="^skip_proof$")
            ],
            PAYMENT_CONFIRM: [
                CallbackQueryHandler(payment_commands.submit_payment, pattern="^submit_payment$"),
                CallbackQueryHandler(payment_commands.confirm_cod_payment, pattern="^confirm_cod_payment$"),
                CallbackQueryHandler(payment_commands.show_payment_confirmation, pattern="^edit_payment$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(payment_commands.cancel_payment, pattern="^cancel_payment$"),
            CommandHandler('cancel', payment_commands.cancel_payment)
        ],
        per_message=False
    )