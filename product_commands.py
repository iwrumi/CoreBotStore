"""
Product Catalog Commands for Telegram Bot
Handles product browsing, variants, and purchasing
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from telegram.constants import ParseMode
from product_catalog_system import ProductCatalogSystem, StockManagement
from balance_system import BalanceSystem
from advanced_data_manager import AdvancedDataManager

# Conversation states
PRODUCT_SEARCH = range(1)

class ProductCommands:
    def __init__(self):
        self.catalog_system = ProductCatalogSystem()
        self.balance_system = BalanceSystem()
        self.stock_management = StockManagement()
        self.data_manager = AdvancedDataManager()
    
    async def browse_products_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Browse products by category"""
        categories = self.catalog_system.get_categories()
        
        text = """
🛒 **Browse Products**

Choose a category to explore our products:

**Available Categories:**
"""
        
        keyboard = []
        for category in categories:
            text += f"• {category['emoji']} {category['name']} ({category['product_count']} products)\n"
            keyboard.append([InlineKeyboardButton(
                f"{category['emoji']} {category['name']} ({category['product_count']})",
                callback_data=f"category_{category['id']}"
            )])
        
        text += "\n🔍 You can also search for specific products."
        
        keyboard.extend([
            [InlineKeyboardButton("🔍 Search Products", callback_data="search_products")],
            [InlineKeyboardButton("⭐ Popular Products", callback_data="popular_products")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_category_products(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show products in a specific category"""
        query = update.callback_query
        await query.answer()
        
        category_id = query.data.replace("category_", "")
        category = self.catalog_system.get_category(category_id)
        products = self.catalog_system.get_products_by_category(category_id)
        
        if not category:
            await query.edit_message_text("❌ Category not found.")
            return
        
        text = f"""
{category['emoji']} **{category['name']}**

{category['description']}

**Available Products ({len(products)}):**
"""
        
        keyboard = []
        
        for product in products:
            # Get cheapest variant price
            min_price = min(v['price'] for v in product.get('variants', []))
            max_price = max(v['price'] for v in product.get('variants', []))
            
            if min_price == max_price:
                price_text = f"₱{min_price:.0f}"
            else:
                price_text = f"₱{min_price:.0f}-₱{max_price:.0f}"
            
            # Count available variants
            available_variants = len([v for v in product.get('variants', []) if v.get('stock', 0) > 0])
            
            text += f"• **{product['name']}** - {price_text} ({available_variants} variants)\n"
            
            keyboard.append([InlineKeyboardButton(
                f"📦 {product['name']} - {price_text}",
                callback_data=f"product_{product['id']}"
            )])
        
        keyboard.extend([
            [InlineKeyboardButton("🔍 Search in Category", callback_data=f"search_category_{category_id}")],
            [InlineKeyboardButton("🔙 Back to Categories", callback_data="browse_products")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_product_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show detailed product information with variants"""
        query = update.callback_query
        await query.answer()
        
        product_id = query.data.replace("product_", "")
        product = self.catalog_system.get_product(product_id)
        
        if not product:
            await query.edit_message_text("❌ Product not found.")
            return
        
        category = self.catalog_system.get_category(product['category_id'])
        
        # Format like the premium bot's product display
        text = f"""
{category['emoji']} **{product['name']}**

{product['description']}

**Variants:**
"""
        
        keyboard = []
        
        for i, variant in enumerate(product.get('variants', []), 1):
            stock_text = f"₱{variant['price']:.0f} | {variant['stock']}X" if variant.get('stock', 0) > 0 else "OUT OF STOCK"
            
            text += f"[{i}] {variant['name']} — {stock_text}\n"
            
            if variant.get('stock', 0) > 0:
                # Create button for available variants
                keyboard.append([InlineKeyboardButton(
                    f"[{i}]",
                    callback_data=f"variant_{product_id}_{variant['id']}"
                )])
        
        # Add variant selection buttons in rows
        if len(keyboard) > 0:
            text += "\n**Select a variant to purchase:**"
            
            # Group buttons in rows of 4
            button_rows = []
            for i in range(0, len(keyboard), 4):
                row = [btn[0] for btn in keyboard[i:i+4]]
                button_rows.append(row)
            
            button_rows.append([InlineKeyboardButton("🔙 Back", callback_data=f"category_{product['category_id']}")])
        else:
            text += "\n❌ **All variants are currently out of stock.**"
            button_rows = [[InlineKeyboardButton("🔙 Back", callback_data=f"category_{product['category_id']}")]]
        
        reply_markup = InlineKeyboardMarkup(button_rows)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_variant_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show variant details and purchase options"""
        query = update.callback_query
        await query.answer()
        
        # Parse callback data: variant_productid_variantid
        parts = query.data.split('_')
        product_id = parts[1]
        variant_id = int(parts[2])
        
        user_telegram_id = str(update.effective_user.id)
        
        variant = self.catalog_system.get_product_variant(product_id, variant_id)
        if not variant:
            await query.edit_message_text("❌ Variant not found.")
            return
        
        # Get user balance
        balance_info = self.balance_system.get_user_balance(user_telegram_id)
        user_balance = balance_info['balance']
        
        # Check stock
        stock_info = self.catalog_system.check_stock(product_id, variant_id)
        
        text = f"""
📦 **{variant['product_name']}**
🎯 **{variant['name']}**

💰 **Price:** ₱{variant['price']:.2f}
⏱️ **Duration:** {variant.get('duration', 'Lifetime')}
📦 **Stock:** {stock_info['stock']} available

**Features:**
"""
        
        for feature in variant.get('features', []):
            text += f"• {feature}\n"
        
        text += f"\n💳 **Your Balance:** ₱{user_balance:.2f}"
        
        # Check if user can afford
        can_afford = user_balance >= variant['price']
        
        keyboard = []
        
        if stock_info['available'] and can_afford:
            text += "\n✅ **Ready to purchase!**"
            keyboard.append([InlineKeyboardButton("💰 Buy Now", callback_data=f"buy_{product_id}_{variant_id}")])
        elif not stock_info['available']:
            text += "\n❌ **Out of stock**"
        elif not can_afford:
            needed = variant['price'] - user_balance
            text += f"\n⚠️ **Insufficient balance**\nYou need ₱{needed:.2f} more to purchase this item."
            keyboard.append([InlineKeyboardButton("💳 Top Up Balance", callback_data="deposit_balance")])
        
        keyboard.extend([
            [InlineKeyboardButton("🔙 Back to Product", callback_data=f"product_{product_id}")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def process_purchase(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process variant purchase using balance"""
        query = update.callback_query
        await query.answer()
        
        # Parse callback data: buy_productid_variantid
        parts = query.data.split('_')
        product_id = parts[1]
        variant_id = int(parts[2])
        
        user_telegram_id = str(update.effective_user.id)
        
        variant = self.catalog_system.get_product_variant(product_id, variant_id)
        if not variant:
            await query.edit_message_text("❌ Product variant not found.")
            return
        
        # Check stock availability
        stock_info = self.catalog_system.check_stock(product_id, variant_id)
        if not stock_info['available']:
            await query.edit_message_text("❌ Sorry, this item is now out of stock.")
            return
        
        # Process payment from balance
        spend_result = self.balance_system.spend_balance(
            user_telegram_id,
            variant['price'],
            f"Purchase: {variant['name']}"
        )
        
        if not spend_result['success']:
            text = f"""
❌ **Purchase Failed**

{spend_result['message']}

💳 Current Balance: ₱{spend_result.get('current_balance', 0):.2f}
💰 Required: ₱{spend_result.get('required', variant['price']):.2f}
📉 Shortfall: ₱{spend_result.get('shortfall', 0):.2f}
            """
            
            keyboard = [
                [InlineKeyboardButton("💳 Top Up Balance", callback_data="deposit_balance")],
                [InlineKeyboardButton("🔙 Back", callback_data=f"variant_{product_id}_{variant_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return
        
        # Process stock reduction
        stock_result = self.stock_management.process_sale(product_id, variant_id, 1)
        
        if not stock_result['success']:
            # Refund the balance since stock update failed
            await query.edit_message_text(f"❌ Purchase failed: {stock_result['message']}")
            return
        
        # Create order record
        from datetime import datetime
        order = {
            'id': len(self.data_manager.get_orders()) + 1,
            'user_telegram_id': user_telegram_id,
            'product_name': variant['name'],
            'total': variant['price'],
            'status': 'completed',
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Success message
        text = f"""
🎉 **Purchase Successful!**

✅ **Product:** {variant['name']}
💰 **Paid:** ₱{variant['price']:.2f}
💳 **New Balance:** ₱{spend_result['new_balance']:.2f}
📦 **Order ID:** #{order.get('id', 'N/A')}

**Product Details:**
📦 Your {variant['name']} is now active!
⏱️ Duration: {variant.get('duration', 'Lifetime')}

**Next Steps:**
• Check your orders for details
• Contact support if you need help
• Leave feedback about your purchase

Thank you for your purchase! 🙏
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📦 My Orders", callback_data="my_orders"),
                InlineKeyboardButton("💬 Customer Service", callback_data="customer_service")
            ],
            [
                InlineKeyboardButton("🛒 Buy More", callback_data="browse_products"),
                InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
        # Update user statistics
        await self._update_user_stats(user_telegram_id, variant['price'])
    
    async def _update_user_stats(self, user_telegram_id: str, amount: float):
        """Update user statistics after purchase"""
        user = self.data_manager.get_or_create_user(user_telegram_id)
        
        current_spent = user.get('total_spent', 0)
        order_count = user.get('order_count', 0)
        
        self.data_manager.update_user_spending(
            user_telegram_id,
            user.get('balance', 0),  # Balance already updated by balance system
            current_spent + amount,
            order_count + 1
        )
    
    async def search_products(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start product search"""
        query = update.callback_query
        await query.answer()
        
        text = """
🔍 **Search Products**

Type the name of the product you're looking for:

**Search Tips:**
• Enter product names (e.g., "Netflix", "Spotify")
• Use keywords (e.g., "streaming", "premium")
• Search by category (e.g., "editing", "gaming")

What are you looking for?
        """
        
        keyboard = [
            [InlineKeyboardButton("❌ Cancel", callback_data="browse_products")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return PRODUCT_SEARCH
    
    async def handle_product_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle product search query"""
        search_query = update.message.text.strip()
        
        if len(search_query) < 2:
            await update.message.reply_text(
                "❌ Please enter at least 2 characters to search."
            )
            return PRODUCT_SEARCH
        
        # Search products
        results = self.catalog_system.search_products(search_query, limit=10)
        
        if not results:
            text = f"""
🔍 **Search Results for "{search_query}"**

❌ No products found matching your search.

**Suggestions:**
• Try different keywords
• Check spelling
• Browse categories instead
            """
            
            keyboard = [
                [InlineKeyboardButton("🛒 Browse Categories", callback_data="browse_products")],
                [InlineKeyboardButton("🔍 Search Again", callback_data="search_products")]
            ]
        else:
            text = f"""
🔍 **Search Results for "{search_query}"**

Found {len(results)} result(s):
"""
            
            keyboard = []
            
            for result in results:
                product = result['product']
                
                if result['match_type'] == 'variant':
                    # Specific variant match
                    variant = result['variant']
                    text += f"• **{variant['name']}** - ₱{variant['price']:.0f}\n"
                    keyboard.append([InlineKeyboardButton(
                        f"📦 {variant['name']} - ₱{variant['price']:.0f}",
                        callback_data=f"variant_{product['id']}_{variant['id']}"
                    )])
                else:
                    # Product match
                    min_price = min(v['price'] for v in product.get('variants', []))
                    text += f"• **{product['name']}** - from ₱{min_price:.0f}\n"
                    keyboard.append([InlineKeyboardButton(
                        f"📦 {product['name']} - from ₱{min_price:.0f}",
                        callback_data=f"product_{product['id']}"
                    )])
            
            keyboard.extend([
                [InlineKeyboardButton("🔍 New Search", callback_data="search_products")],
                [InlineKeyboardButton("🛒 Browse Categories", callback_data="browse_products")]
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END
    
    async def show_popular_products(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show popular products"""
        query = update.callback_query
        await query.answer()
        
        popular = self.catalog_system.get_popular_products()
        
        text = """
⭐ **Popular Products**

Our most popular items:
"""
        
        keyboard = []
        
        for item in popular:
            variant = item['variant']
            text += f"• **{variant['name']}** - ₱{variant['price']:.0f} ⭐\n"
            
            keyboard.append([InlineKeyboardButton(
                f"⭐ {variant['name']} - ₱{variant['price']:.0f}",
                callback_data=f"variant_{item['product_id']}_{variant['id']}"
            )])
        
        keyboard.extend([
            [InlineKeyboardButton("🛒 Browse All", callback_data="browse_products")],
            [InlineKeyboardButton("🔍 Search", callback_data="search_products")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def cancel_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel product search"""
        if update.callback_query:
            await update.callback_query.edit_message_text("❌ Search cancelled.")
        else:
            await update.message.reply_text("❌ Search cancelled.")
        
        return ConversationHandler.END

def get_product_conversation_handler():
    """Get conversation handler for product system"""
    product_commands = ProductCommands()
    
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(product_commands.search_products, pattern="^search_products$")
        ],
        states={
            PRODUCT_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_commands.handle_product_search)]
        },
        fallbacks=[
            CallbackQueryHandler(product_commands.cancel_search, pattern="^browse_products$"),
            CommandHandler('cancel', product_commands.cancel_search)
        ],
        per_message=False
    )

def get_product_callback_handlers():
    """Get product system callback handlers"""
    product_commands = ProductCommands()
    
    return [
        CallbackQueryHandler(product_commands.browse_products_command, pattern="^browse_products$"),
        CallbackQueryHandler(product_commands.show_category_products, pattern="^category_"),
        CallbackQueryHandler(product_commands.show_product_details, pattern="^product_"),
        CallbackQueryHandler(product_commands.show_variant_details, pattern="^variant_"),
        CallbackQueryHandler(product_commands.process_purchase, pattern="^buy_"),
        CallbackQueryHandler(product_commands.show_popular_products, pattern="^popular_products$")
    ]