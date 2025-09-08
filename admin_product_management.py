"""
Admin Product Management Commands
Handle product creation, stock management, and inventory control
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, CommandHandler
from telegram.constants import ParseMode
from product_catalog_system import ProductCatalogSystem, StockManagement
from advanced_data_manager import AdvancedDataManager

# Conversation states
ADD_PRODUCT_NAME, ADD_PRODUCT_DESCRIPTION, ADD_PRODUCT_CATEGORY, ADD_VARIANT_NAME, ADD_VARIANT_PRICE, ADD_VARIANT_STOCK, UPDATE_STOCK_AMOUNT = range(7)

class AdminProductManagement:
    def __init__(self):
        self.catalog_system = ProductCatalogSystem()
        self.stock_management = StockManagement()
        self.data_manager = AdvancedDataManager()
    
    async def admin_product_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main product management menu"""
        user_id = update.effective_user.id
        
        if not self._is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        # Get catalog statistics
        stats = self.catalog_system.get_catalog_stats()
        low_stock = self.catalog_system.get_low_stock_alerts(threshold=10)
        
        text = f"""
📦 **Product Management**

**Inventory Overview:**
• Total Products: {stats['total_products']}
• Active Products: {stats['active_products']}
• Total Variants: {stats['total_variants']}
• In Stock: {stats['in_stock_variants']}
• Out of Stock: {stats['out_of_stock_variants']}

**Alerts:**
• Low Stock Items: {len(low_stock)}
• Inventory Value: ₱{stats['total_inventory_value']:,.2f}

**Quick Actions:**
• Add new products and variants
• Update stock levels
• Manage product categories
• View sales analytics

Choose an option:
        """
        
        keyboard = [
            [
                InlineKeyboardButton("➕ Add Product", callback_data="add_product"),
                InlineKeyboardButton("📦 Manage Stock", callback_data="manage_stock")
            ],
            [
                InlineKeyboardButton("📊 Product Analytics", callback_data="product_analytics"),
                InlineKeyboardButton("⚠️ Low Stock Alerts", callback_data="low_stock_alerts")
            ],
            [
                InlineKeyboardButton("🏷️ Manage Categories", callback_data="manage_categories"),
                InlineKeyboardButton("📋 All Products", callback_data="admin_all_products")
            ],
            [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_add_product_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show add product menu"""
        query = update.callback_query
        await query.answer()
        
        text = """
➕ **Add New Product**

Create a new product with variants:

**Steps:**
1. Choose product category
2. Enter product name
3. Add description
4. Create variants with pricing
5. Set initial stock

**Product Types:**
• Single variant (one price, one option)
• Multiple variants (different durations, features)
• Service tiers (basic, premium, pro)

Choose a category for your new product:
        """
        
        categories = self.catalog_system.get_categories()
        keyboard = []
        
        for category in categories:
            keyboard.append([InlineKeyboardButton(
                f"{category['emoji']} {category['name']}",
                callback_data=f"newprod_cat_{category['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_product_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def start_add_product(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start product creation process"""
        query = update.callback_query
        await query.answer()
        
        category_id = query.data.replace("newprod_cat_", "")
        category = self.catalog_system.get_category(category_id)
        
        if not category:
            await query.edit_message_text("❌ Invalid category selected.")
            return ConversationHandler.END
        
        context.user_data['new_product'] = {'category_id': category_id}
        
        text = f"""
➕ **Add Product - Step 1/4**

**Category:** {category['emoji']} {category['name']}

**Enter Product Name:**

Examples for {category['name']}:
• "NETFLIX PREMIUM ACCOUNTS"
• "30D AUTO PLUG SERVICE"
• "SPOTIFY FAMILY PLAN"

Type the product name:
        """
        
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="admin_product_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return ADD_PRODUCT_NAME
    
    async def get_product_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get product name"""
        product_name = update.message.text.strip()
        
        if len(product_name) < 5:
            await update.message.reply_text("❌ Product name must be at least 5 characters. Try again:")
            return ADD_PRODUCT_NAME
        
        if len(product_name) > 100:
            await update.message.reply_text("❌ Product name too long (max 100 characters). Try again:")
            return ADD_PRODUCT_NAME
        
        context.user_data['new_product']['name'] = product_name
        
        text = f"""
➕ **Add Product - Step 2/4**

**Product Name:** {product_name}

**Enter Product Description:**

Write a clear description that explains what this product offers:

**Examples:**
• "Premium Netflix accounts with 4K streaming, 4 simultaneous screens, and download feature."
• "24/7 automated plug service with instant delivery and lifetime support."
• "Professional Spotify Family plan for up to 6 users with ad-free music."

Type the product description:
        """
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        return ADD_PRODUCT_DESCRIPTION
    
    async def get_product_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get product description"""
        description = update.message.text.strip()
        
        if len(description) < 20:
            await update.message.reply_text("❌ Description must be at least 20 characters. Try again:")
            return ADD_PRODUCT_DESCRIPTION
        
        context.user_data['new_product']['description'] = description
        
        text = f"""
✅ **Product Information Complete**

**Name:** {context.user_data['new_product']['name']}
**Description:** {description[:100]}{'...' if len(description) > 100 else ''}

**Now let's add variants:**

Variants are different options for your product (e.g., 1 month, 3 months, lifetime).

**Enter first variant name:**

**Examples:**
• "1 Month Premium"
• "01D NONSTOP PLUG"
• "Basic Plan"
• "Lifetime License"

Type the variant name:
        """
        
        context.user_data['new_product']['variants'] = []
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        return ADD_VARIANT_NAME
    
    async def get_variant_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get variant name"""
        variant_name = update.message.text.strip()
        
        if len(variant_name) < 3:
            await update.message.reply_text("❌ Variant name must be at least 3 characters. Try again:")
            return ADD_VARIANT_NAME
        
        context.user_data['current_variant'] = {'name': variant_name}
        
        text = f"""
💰 **Variant: {variant_name}**

**Enter the price for this variant:**

**Price Guidelines:**
• Enter numbers only (e.g., 150)
• Minimum: ₱1
• Maximum: ₱50,000
• No decimal places

Type the price in pesos:
        """
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        return ADD_VARIANT_PRICE
    
    async def get_variant_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get variant price"""
        try:
            price = float(update.message.text.strip())
            
            if price < 1:
                await update.message.reply_text("❌ Price must be at least ₱1. Try again:")
                return ADD_VARIANT_PRICE
            
            if price > 50000:
                await update.message.reply_text("❌ Price too high (max ₱50,000). Try again:")
                return ADD_VARIANT_PRICE
            
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number. Try again:")
            return ADD_VARIANT_PRICE
        
        context.user_data['current_variant']['price'] = price
        
        text = f"""
📦 **Stock Level**

**Variant:** {context.user_data['current_variant']['name']}
**Price:** ₱{price:.2f}

**Enter initial stock quantity:**

**Stock Guidelines:**
• Enter whole numbers only
• 0 = Out of stock
• Maximum: 10,000 units

How many units do you have in stock?
        """
        
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        return ADD_VARIANT_STOCK
    
    async def get_variant_stock(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get variant stock and create product"""
        try:
            stock = int(update.message.text.strip())
            
            if stock < 0:
                await update.message.reply_text("❌ Stock cannot be negative. Try again:")
                return ADD_VARIANT_STOCK
            
            if stock > 10000:
                await update.message.reply_text("❌ Stock too high (max 10,000). Try again:")
                return ADD_VARIANT_STOCK
            
        except ValueError:
            await update.message.reply_text("❌ Please enter a whole number. Try again:")
            return ADD_VARIANT_STOCK
        
        # Complete variant
        variant = context.user_data['current_variant']
        variant['stock'] = stock
        variant['features'] = ['High quality', 'Instant delivery', 'Customer support']
        variant['duration'] = 'As specified'
        
        # Add to product
        context.user_data['new_product']['variants'].append(variant)
        
        # Create the product
        result = self._create_new_product(context.user_data['new_product'])
        
        if result['success']:
            text = f"""
🎉 **Product Created Successfully!**

✅ **{result['product']['name']}** has been added to your store.

**Product Details:**
• Category: {result['category']['name']}
• Variants: {len(result['product']['variants'])}
• Initial Stock: {stock} units

**First Variant:**
• Name: {variant['name']}
• Price: ₱{variant['price']:.2f}
• Stock: {stock}

**Next Steps:**
• Add more variants if needed
• Update product images
• Set up promotional campaigns
• Monitor sales performance

Your product is now live and ready for customers! 🛍️
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("➕ Add Another Product", callback_data="add_product"),
                    InlineKeyboardButton("📦 Manage Stock", callback_data="manage_stock")
                ],
                [
                    InlineKeyboardButton("📊 Product Analytics", callback_data="product_analytics"),
                    InlineKeyboardButton("🏠 Admin Menu", callback_data="admin_menu")
                ]
            ]
        else:
            text = f"❌ **Failed to create product:**\n\n{result['message']}"
            keyboard = [
                [InlineKeyboardButton("🔄 Try Again", callback_data="add_product")],
                [InlineKeyboardButton("🏠 Admin Menu", callback_data="admin_menu")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
        context.user_data.clear()
        return ConversationHandler.END
    
    async def show_manage_stock(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show stock management interface"""
        query = update.callback_query
        await query.answer()
        
        # Get all products with stock info
        categories = self.catalog_system.get_categories()
        low_stock = self.catalog_system.get_low_stock_alerts(threshold=10)
        
        text = f"""
📦 **Stock Management**

**Stock Overview:**
• Low Stock Items: {len(low_stock)}
• Categories: {len(categories)}

**Quick Actions:**
• Update stock levels for existing products
• View products running low on stock
• Bulk stock updates

Choose how to manage stock:
        """
        
        keyboard = [
            [
                InlineKeyboardButton("⚠️ Low Stock Items", callback_data="view_low_stock"),
                InlineKeyboardButton("📋 All Products", callback_data="stock_all_products")
            ],
            [
                InlineKeyboardButton("🏷️ By Category", callback_data="stock_by_category"),
                InlineKeyboardButton("🔍 Search Product", callback_data="stock_search")
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_product_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_low_stock_alerts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show low stock alerts"""
        query = update.callback_query
        await query.answer()
        
        low_stock = self.catalog_system.get_low_stock_alerts(threshold=10)
        
        if not low_stock:
            text = """
✅ **All Stock Levels Good!**

No products are running low on stock.

**Current Threshold:** 10 units
**Recommendation:** Keep monitoring daily

Great job maintaining your inventory! 👍
            """
            keyboard = [[InlineKeyboardButton("📦 Manage Stock", callback_data="manage_stock")]]
        else:
            text = f"""
⚠️ **Low Stock Alerts ({len(low_stock)} items)**

The following products need restocking:

"""
            keyboard = []
            
            for item in low_stock[:10]:  # Show top 10
                stock_emoji = "🔴" if item['current_stock'] <= 3 else "🟡"
                text += f"{stock_emoji} **{item['variant_name']}**\n"
                text += f"   Stock: {item['current_stock']} units\n"
                text += f"   Price: ₱{item['price']:.2f}\n"
                text += f"   Category: {item['category']}\n\n"
                
                # Add quick restock button
                keyboard.append([InlineKeyboardButton(
                    f"📦 Restock {item['variant_name']}",
                    callback_data=f"restock_{item['variant_name'][:20]}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="manage_stock")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_stock_by_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show stock management by category"""
        query = update.callback_query
        await query.answer()
        
        categories = self.catalog_system.get_categories()
        
        text = """
🏷️ **Stock by Category**

Choose a category to manage stock:
        """
        
        keyboard = []
        for category in categories:
            products = self.catalog_system.get_products_by_category(category['id'])
            keyboard.append([InlineKeyboardButton(
                f"{category['emoji']} {category['name']} ({len(products)} products)",
                callback_data=f"stock_cat_{category['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="manage_stock")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    def _create_new_product(self, product_data: dict) -> dict:
        """Create new product in database"""
        try:
            # Generate product ID
            import uuid
            product_id = f"product_{uuid.uuid4().hex[:8]}"
            
            # Assign variant IDs
            for i, variant in enumerate(product_data['variants'], 1):
                variant['id'] = i
                variant['popular'] = False
            
            # Create product record
            new_product = {
                'id': product_id,
                'category_id': product_data['category_id'],
                'name': product_data['name'],
                'description': product_data['description'],
                'base_price': product_data['variants'][0]['price'],
                'active': True,
                'variants': product_data['variants'],
                'created_at': __import__('datetime').datetime.utcnow().isoformat()
            }
            
            # In real implementation, save to database
            # self.data_manager.create_product(new_product)
            
            # Get category info
            category = self.catalog_system.get_category(product_data['category_id'])
            
            return {
                'success': True,
                'product': new_product,
                'category': category
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error creating product: {str(e)}'
            }
    
    def _is_admin(self, user_id):
        """Check if user is admin"""
        admin_ids = [123456789]  # Replace with actual admin IDs
        return user_id in admin_ids
    
    async def cancel_product_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel product creation"""
        if update.callback_query:
            await update.callback_query.edit_message_text("❌ Product creation cancelled.")
        else:
            await update.message.reply_text("❌ Product creation cancelled.")
        
        context.user_data.clear()
        return ConversationHandler.END

def get_admin_product_conversation_handler():
    """Get conversation handler for admin product management"""
    admin_product = AdminProductManagement()
    
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_product.start_add_product, pattern="^newprod_cat_")
        ],
        states={
            ADD_PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_product.get_product_name)],
            ADD_PRODUCT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_product.get_product_description)],
            ADD_VARIANT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_product.get_variant_name)],
            ADD_VARIANT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_product.get_variant_price)],
            ADD_VARIANT_STOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_product.get_variant_stock)]
        },
        fallbacks=[
            CallbackQueryHandler(admin_product.cancel_product_creation, pattern="^admin_product_menu$"),
            CommandHandler('cancel', admin_product.cancel_product_creation)
        ],
        per_message=False
    )

def get_admin_product_handlers():
    """Get admin product management handlers"""
    admin_product = AdminProductManagement()
    
    return [
        CallbackQueryHandler(admin_product.admin_product_menu, pattern="^admin_product_menu$"),
        CallbackQueryHandler(admin_product.show_add_product_menu, pattern="^add_product$"),
        CallbackQueryHandler(admin_product.show_manage_stock, pattern="^manage_stock$"),
        CallbackQueryHandler(admin_product.show_low_stock_alerts, pattern="^low_stock_alerts$"),
        CallbackQueryHandler(admin_product.show_stock_by_category, pattern="^stock_by_category$")
    ]