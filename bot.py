import os
import logging
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from data_manager import DataManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Conversation states
SELECTING_CATEGORY, SELECTING_PRODUCT, VIEWING_CART, CHECKOUT = range(4)

class TelegramStoreBot:
    def __init__(self, token, data_manager):
        self.token = token
        self.data_manager = data_manager
        self.application = Application.builder().token(token).build()
        self.user_sessions = {}
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup bot command and callback handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("catalog", self.catalog_command))
        self.application.add_handler(CommandHandler("cart", self.cart_command))
        self.application.add_handler(CommandHandler("orders", self.orders_command))
        
        # Callback query handler for inline keyboards
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Conversation handler for checkout process
        conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_checkout, pattern="^checkout$")],
            states={
                CHECKOUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_checkout_info)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_checkout)]
        )
        self.application.add_handler(conv_handler)
    
    def get_user_session(self, user_id):
        """Get or create user session"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                'cart': {},
                'current_category': None,
                'current_product': None
            }
        return self.user_sessions[user_id]
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        welcome_message = f"""
🛍️ **Welcome to Our Store, {user.first_name}!**

I'm your personal shopping assistant. Here's what I can help you with:

🏪 **Browse Catalog** - View our product categories
🛒 **Shopping Cart** - Manage your selected items
📦 **Your Orders** - Track your order history
❓ **Help** - Get assistance

Use the menu below or type /help for more information.
        """
        
        keyboard = [
            [InlineKeyboardButton("🏪 Browse Catalog", callback_data="catalog")],
            [InlineKeyboardButton("🛒 View Cart", callback_data="cart")],
            [InlineKeyboardButton("📦 My Orders", callback_data="orders")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🆘 **Help & Commands**

**Available Commands:**
/start - Main menu
/catalog - Browse products
/cart - View your shopping cart
/orders - View your order history
/help - Show this help message

**How to Shop:**
1️⃣ Browse catalog by category
2️⃣ Select products and add to cart
3️⃣ Review your cart
4️⃣ Proceed to checkout
5️⃣ Provide shipping details
6️⃣ Confirm your order

**Need Help?**
Contact our support team or use the buttons below to navigate.
        """
        
        keyboard = [
            [InlineKeyboardButton("🏪 Browse Catalog", callback_data="catalog")],
            [InlineKeyboardButton("🛒 View Cart", callback_data="cart")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def catalog_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /catalog command"""
        await self.show_categories(update, context)
    
    async def cart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cart command"""
        await self.show_cart(update, context)
    
    async def orders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /orders command"""
        await self.show_user_orders(update, context)
    
    async def show_categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show product categories"""
        products = self.data_manager.get_products()
        categories = {}
        
        # Group products by category
        for product in products:
            category = product.get('category', 'Uncategorized')
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        if not categories:
            message = "🚫 **No products available at the moment.**\n\nPlease check back later!"
            keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data="catalog")]]
        else:
            message = "🏪 **Product Categories**\n\nSelect a category to browse products:"
            keyboard = []
            for category, count in categories.items():
                keyboard.append([InlineKeyboardButton(f"{category} ({count} items)", callback_data=f"category_{category}")])
            keyboard.append([InlineKeyboardButton("🛒 View Cart", callback_data="cart")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_products_in_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE, category):
        """Show products in a specific category"""
        products = self.data_manager.get_products()
        category_products = [p for p in products if p.get('category') == category]
        
        if not category_products:
            message = f"🚫 **No products in {category}**\n\nThis category is currently empty."
            keyboard = [[InlineKeyboardButton("⬅️ Back to Categories", callback_data="catalog")]]
        else:
            message = f"🏪 **{category}**\n\nSelect a product to view details:"
            keyboard = []
            for product in category_products:
                stock_info = f" (Stock: {product.get('stock', 0)})" if product.get('stock', 0) > 0 else " (Out of Stock)"
                keyboard.append([InlineKeyboardButton(f"{product['name']}{stock_info}", callback_data=f"product_{product['id']}")])
            keyboard.append([InlineKeyboardButton("⬅️ Back to Categories", callback_data="catalog")])
            keyboard.append([InlineKeyboardButton("🛒 View Cart", callback_data="cart")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_product_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE, product_id):
        """Show detailed product information"""
        products = self.data_manager.get_products()
        product = next((p for p in products if p['id'] == product_id), None)
        
        if not product:
            message = "🚫 **Product not found**\n\nThis product may have been removed."
            keyboard = [[InlineKeyboardButton("⬅️ Back to Catalog", callback_data="catalog")]]
        else:
            stock = product.get('stock', 0)
            stock_status = "✅ In Stock" if stock > 0 else "❌ Out of Stock"
            
            message = f"""
🛍️ **{product['name']}**

📝 **Description:**
{product['description']}

💰 **Price:** ${product['price']:.2f}
📦 **Stock:** {stock_status} ({stock} available)
🏷️ **Category:** {product.get('category', 'Uncategorized')}
            """
            
            keyboard = []
            if stock > 0:
                keyboard.append([InlineKeyboardButton("➕ Add to Cart", callback_data=f"add_to_cart_{product_id}")])
            keyboard.append([InlineKeyboardButton("⬅️ Back to Category", callback_data=f"category_{product.get('category', 'Uncategorized')}")])
            keyboard.append([InlineKeyboardButton("🛒 View Cart", callback_data="cart")])
            
            # Send product image if available
            if product.get('image_url'):
                try:
                    await update.callback_query.delete_message()
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=product['image_url'],
                        caption=message,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
                except Exception as e:
                    logger.error(f"Failed to send image: {e}")
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def add_to_cart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, product_id):
        """Add product to user's cart"""
        user_id = update.effective_user.id
        session = self.get_user_session(user_id)
        
        products = self.data_manager.get_products()
        product = next((p for p in products if p['id'] == product_id), None)
        
        if not product:
            await update.callback_query.answer("❌ Product not found!", show_alert=True)
            return
        
        if product.get('stock', 0) <= 0:
            await update.callback_query.answer("❌ Product out of stock!", show_alert=True)
            return
        
        # Check if already in cart
        if product_id in session['cart']:
            session['cart'][product_id]['quantity'] += 1
        else:
            session['cart'][product_id] = {
                'quantity': 1,
                'product': product
            }
        
        await update.callback_query.answer(f"✅ {product['name']} added to cart!", show_alert=False)
        
        # Show updated product details with cart info
        await self.show_product_details(update, context, product_id)
    
    async def show_cart(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's shopping cart"""
        user_id = update.effective_user.id
        session = self.get_user_session(user_id)
        cart = session['cart']
        
        if not cart:
            message = "🛒 **Your Cart is Empty**\n\nBrowse our catalog to add some products!"
            keyboard = [[InlineKeyboardButton("🏪 Browse Catalog", callback_data="catalog")]]
        else:
            message = "🛒 **Your Shopping Cart**\n\n"
            total = 0
            keyboard = []
            
            for product_id, item in cart.items():
                product = item['product']
                quantity = item['quantity']
                subtotal = product['price'] * quantity
                total += subtotal
                
                message += f"• **{product['name']}**\n"
                message += f"  Quantity: {quantity} × ${product['price']:.2f} = ${subtotal:.2f}\n\n"
                
                keyboard.append([
                    InlineKeyboardButton(f"➖ {product['name']}", callback_data=f"remove_from_cart_{product_id}"),
                    InlineKeyboardButton("➕", callback_data=f"add_to_cart_{product_id}")
                ])
            
            message += f"💰 **Total: ${total:.2f}**"
            keyboard.append([InlineKeyboardButton("🚮 Clear Cart", callback_data="clear_cart")])
            keyboard.append([InlineKeyboardButton("💳 Checkout", callback_data="checkout")])
            keyboard.append([InlineKeyboardButton("🏪 Continue Shopping", callback_data="catalog")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def remove_from_cart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, product_id):
        """Remove item from cart"""
        user_id = update.effective_user.id
        session = self.get_user_session(user_id)
        
        if product_id in session['cart']:
            session['cart'][product_id]['quantity'] -= 1
            if session['cart'][product_id]['quantity'] <= 0:
                del session['cart'][product_id]
        
        await update.callback_query.answer("🗑️ Item removed from cart")
        await self.show_cart(update, context)
    
    async def clear_cart(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clear user's cart"""
        user_id = update.effective_user.id
        session = self.get_user_session(user_id)
        session['cart'] = {}
        
        await update.callback_query.answer("🗑️ Cart cleared!")
        await self.show_cart(update, context)
    
    async def start_checkout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start checkout process"""
        user_id = update.effective_user.id
        session = self.get_user_session(user_id)
        
        if not session['cart']:
            await update.callback_query.answer("❌ Your cart is empty!", show_alert=True)
            return
        
        message = """
📋 **Checkout Process**

Please provide your shipping information in the following format:

**Full Name:**
**Phone Number:**
**Address:**
**City, State, ZIP:**
**Special Instructions (optional):**

Please send all information in a single message.
        """
        
        keyboard = [[InlineKeyboardButton("❌ Cancel Checkout", callback_data="cart")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return CHECKOUT
    
    async def process_checkout_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process checkout information and create order"""
        user_id = update.effective_user.id
        session = self.get_user_session(user_id)
        shipping_info = update.message.text
        
        # Create order
        order_data = {
            'user_id': user_id,
            'user_name': update.effective_user.first_name,
            'username': update.effective_user.username,
            'items': session['cart'],
            'shipping_info': shipping_info,
            'status': 'pending'
        }
        
        order = self.data_manager.create_order(order_data)
        
        # Clear cart
        session['cart'] = {}
        
        # Calculate total
        total = sum(item['product']['price'] * item['quantity'] for item in order['items'].values())
        
        confirmation_message = f"""
✅ **Order Confirmed!**

**Order ID:** #{order['id']}
**Total:** ${total:.2f}
**Status:** Pending

Your order has been received and will be processed soon. You'll receive updates about your order status.

Thank you for shopping with us! 🛍️
        """
        
        keyboard = [
            [InlineKeyboardButton("📦 Track Order", callback_data=f"order_{order['id']}")],
            [InlineKeyboardButton("🏪 Continue Shopping", callback_data="catalog")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(confirmation_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END
    
    async def cancel_checkout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel checkout process"""
        await update.message.reply_text("❌ Checkout cancelled.")
        await self.show_cart(update, context)
        return ConversationHandler.END
    
    async def show_user_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's order history"""
        user_id = update.effective_user.id
        orders = self.data_manager.get_user_orders(user_id)
        
        if not orders:
            message = "📦 **No Orders Found**\n\nYou haven't placed any orders yet."
            keyboard = [[InlineKeyboardButton("🏪 Start Shopping", callback_data="catalog")]]
        else:
            message = "📦 **Your Orders**\n\n"
            keyboard = []
            
            for order in orders[-5:]:  # Show last 5 orders
                total = sum(item['product']['price'] * item['quantity'] for item in order['items'].values())
                status_emoji = {
                    'pending': '⏳',
                    'confirmed': '✅',
                    'shipped': '🚚',
                    'delivered': '📦',
                    'cancelled': '❌'
                }.get(order['status'], '❓')
                
                message += f"{status_emoji} **Order #{order['id']}**\n"
                message += f"Total: ${total:.2f} | Status: {order['status'].title()}\n"
                message += f"Date: {order['created_at']}\n\n"
                
                keyboard.append([InlineKeyboardButton(f"Order #{order['id']}", callback_data=f"order_{order['id']}")])
            
            keyboard.append([InlineKeyboardButton("🏪 Continue Shopping", callback_data="catalog")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_order_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE, order_id):
        """Show detailed order information"""
        order = self.data_manager.get_order(order_id)
        
        if not order:
            await update.callback_query.answer("❌ Order not found!", show_alert=True)
            return
        
        # Check if user owns this order
        if order['user_id'] != update.effective_user.id:
            await update.callback_query.answer("❌ Access denied!", show_alert=True)
            return
        
        total = sum(item['product']['price'] * item['quantity'] for item in order['items'].values())
        status_emoji = {
            'pending': '⏳',
            'confirmed': '✅',
            'shipped': '🚚',
            'delivered': '📦',
            'cancelled': '❌'
        }.get(order['status'], '❓')
        
        message = f"""
📦 **Order Details**

**Order ID:** #{order['id']}
**Status:** {status_emoji} {order['status'].title()}
**Date:** {order['created_at']}
**Total:** ${total:.2f}

**Items:**
        """
        
        for item in order['items'].values():
            product = item['product']
            quantity = item['quantity']
            subtotal = product['price'] * quantity
            message += f"• {product['name']} × {quantity} = ${subtotal:.2f}\n"
        
        message += f"\n**Shipping Information:**\n{order['shipping_info']}"
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Back to Orders", callback_data="orders")],
            [InlineKeyboardButton("🏪 Continue Shopping", callback_data="catalog")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button presses"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "catalog":
            await self.show_categories(update, context)
        elif data == "cart":
            await self.show_cart(update, context)
        elif data == "orders":
            await self.show_user_orders(update, context)
        elif data == "help":
            await self.help_command(update, context)
        elif data.startswith("category_"):
            category = data.replace("category_", "")
            await self.show_products_in_category(update, context, category)
        elif data.startswith("product_"):
            product_id = int(data.replace("product_", ""))
            await self.show_product_details(update, context, product_id)
        elif data.startswith("add_to_cart_"):
            product_id = int(data.replace("add_to_cart_", ""))
            await self.add_to_cart(update, context, product_id)
        elif data.startswith("remove_from_cart_"):
            product_id = int(data.replace("remove_from_cart_", ""))
            await self.remove_from_cart(update, context, product_id)
        elif data == "clear_cart":
            await self.clear_cart(update, context)
        elif data.startswith("order_"):
            order_id = int(data.replace("order_", ""))
            await self.show_order_details(update, context, order_id)
    
    def notify_order_status_update(self, order):
        """Notify customer about order status update"""
        # This would be called from the Flask app when order status is updated
        try:
            status_emoji = {
                'pending': '⏳',
                'confirmed': '✅',
                'shipped': '🚚',
                'delivered': '📦',
                'cancelled': '❌'
            }.get(order['status'], '❓')
            
            message = f"""
📦 **Order Status Update**

**Order ID:** #{order['id']}
**New Status:** {status_emoji} {order['status'].title()}

Your order status has been updated. Use /orders to view all your orders.
            """
            
            # Send notification (this would need to be implemented with proper async handling)
            # For now, we'll log it
            logger.info(f"Would notify user {order['user_id']} about order {order['id']} status: {order['status']}")
        
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    def start_polling(self):
        """Start bot with polling"""
        self.application.run_polling()
    
    def set_webhook(self, webhook_url):
        """Set webhook for the bot"""
        import asyncio
        asyncio.run(self.application.bot.set_webhook(webhook_url))
    
    def process_update(self, update_data):
        """Process update from webhook"""
        from telegram import Update
        update = Update.de_json(update_data, self.application.bot)
        asyncio.run(self.application.process_update(update))
