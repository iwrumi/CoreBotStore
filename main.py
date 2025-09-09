"""
Main Flask Application Entry Point
Premium Store Bot - Complete System
"""
import os
import logging
from flask import Flask, request, jsonify, render_template_string
from telegram import Update
from werkzeug.middleware.proxy_fix import ProxyFix

# Import the complete bot
try:
    from complete_bot import PremiumStoreBot
    bot_import_success = True
except ImportError as e:
    logging.error(f"Failed to import complete bot: {e}")
    bot_import_success = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Bot instance
premium_bot = None
bot_app = None

# Initialize bot if import was successful
if bot_import_success:
    bot_token = os.environ.get('BOT_TOKEN')
    if bot_token:
        try:
            premium_bot = PremiumStoreBot(bot_token)
            bot_app = premium_bot.application
            logger.info("Bot initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
    else:
        logger.error("BOT_TOKEN not found in environment variables")
else:
    logger.warning("Bot not initialized due to import failure")

@app.route('/')
def index():
    """Home page with bot status"""
    status = "✅ Active" if premium_bot else "❌ Error"
    status_class = "success" if premium_bot else "danger"
    
    return render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Premium Store Bot</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card bg-white border">
                        <div class="card-header">
                            <h1 class="text-center">🤖 Premium Store Bot</h1>
                            <div class="text-center">
                                <span class="badge bg-{status_class}">{status}</span>
                            </div>
                        </div>
                        <div class="card-body">
                            <div class="text-center mb-4">
                                <h3>Premium Telegram Store Bot</h3>
                                <p class="text-secondary">Professional Telegram Store Bot</p>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6">
                                    <h5>🏪 Store Features:</h5>
                                    <ul>
                                        <li>💰 Balance System with QR Deposits</li>
                                        <li>🛒 Product Catalog with Variants</li>
                                        <li>📊 User Statistics & Leaderboard</li>
                                        <li>🎁 Daily Bonus System</li>
                                        <li>💳 Multiple Payment Methods</li>
                                        <li>👤 Customer Support</li>
                                    </ul>
                                </div>
                                <div class="col-md-6">
                                    <h5>⚙️ Admin Features:</h5>
                                    <ul>
                                        <li>📝 Product Management</li>
                                        <li>📈 Sales Analytics</li>
                                        <li>💸 Deposit Management</li>
                                        <li>👥 User Management</li>
                                        <li>📊 Financial Dashboard</li>
                                        <li>📢 Broadcast Messages</li>
                                    </ul>
                                </div>
                            </div>
                            
                            <div class="text-center mt-4">
                                <p><strong>Status:</strong> <span class="badge bg-{status_class}">{status}</span></p>
                                <p><strong>Version:</strong> v2.0 (Complete Premium)</p>
                                {'<p class="text-success">Bot is ready to receive messages!</p>' if premium_bot else '<p class="text-danger">Bot initialization failed - check logs</p>'}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Telegram webhook updates"""
    try:
        update_data = request.get_json(force=True)
        
        # Handle callback queries (inline keyboard button presses)
        if update_data and 'callback_query' in update_data:
            import urllib.request
            import json as json_lib
            
            # Get bot token
            bot_token = os.environ.get('BOT_TOKEN')
            if not bot_token:
                logger.error("BOT_TOKEN not found")
                return jsonify({'error': 'BOT_TOKEN not configured'}), 500
            
            # Load editable messages
            try:
                with open('bot_messages.json', 'r') as f:
                    messages = json_lib.load(f)
            except:
                messages = {}
                
            callback_query = update_data['callback_query']
            query_id = callback_query['id']
            chat_id = str(callback_query['message']['chat']['id'])
            user_id = str(callback_query['from']['id'])
            callback_data = callback_query['data']
            message_id = callback_query['message']['message_id']
            
            # Answer callback query first
            answer_url = f"https://api.telegram.org/bot{bot_token}/answerCallbackQuery"
            answer_data = json_lib.dumps({"callback_query_id": query_id}).encode('utf-8')
            answer_req = urllib.request.Request(answer_url, data=answer_data, headers={'Content-Type': 'application/json'})
            
            try:
                urllib.request.urlopen(answer_req)
            except:
                pass
            
            # Handle message_admin callback
            if callback_data == "message_admin":
                response_text = "📩 Contact Admin\n\nHow to reach admin:\n\n💬 Telegram: 09911127180\n📞 Call/Text: 09911127180\n\nFor faster approval:\n✅ Send your receipt photo to this bot\n✅ Include amount in message\n✅ Wait for admin approval\n\nApproval usually within 5 minutes!"
                inline_keyboard = {"inline_keyboard": [
                    [{"text": "💳 Send Receipt to Bot", "callback_data": "send_receipt_info"}],
                    [{"text": "🔙 Back to Main Menu", "callback_data": "main_menu"}]
                ]}
            
            elif callback_data == "send_receipt_info":
                response_text = "📸 Send Receipt Instructions\n\nSteps:\n1. Take clear photo of your GCash receipt\n2. Send the photo to this bot\n3. Include amount in message (e.g., '₱100')\n4. Wait for admin approval\n\nExample message with photo:\n'₱150 deposit - please approve'\n\nReady to send your receipt? Just upload the photo now! 📸"
                inline_keyboard = {"inline_keyboard": [
                    [{"text": "🔙 Back to Deposit", "callback_data": "deposit_funds"}],
                    [{"text": "🔙 Main Menu", "callback_data": "main_menu"}]
                ]}
                
            # Handle different callback actions
            elif callback_data == "browse_products":
                logger.info(f"WEBHOOK: browse_products clicked by user {user_id}")
                # ULTRA MINIMAL TEST - just return basic text
                response_text = "Products available"
                inline_keyboard = {"inline_keyboard": [[
                    {"text": "Back", "callback_data": "main_menu"}
                ]]}
                logger.info(f"WEBHOOK: Prepared response for browse_products")
            
            elif callback_data == "check_balance":
                # Load actual user data
                try:
                    with open('data/users.json', 'r') as f:
                        users = json_lib.load(f)
                    user_data = users.get(str(user_id), {})
                    balance = user_data.get('balance', 0)
                    total_deposited = user_data.get('total_deposited', 0)
                    total_spent = user_data.get('total_spent', 0)
                except:
                    balance = total_deposited = total_spent = 0
                
                response_text = f"💰 Account Balance\n\nCurrent Balance: ₱{balance:.2f}\nTotal Deposited: ₱{total_deposited:.2f}\nTotal Spent: ₱{total_spent:.2f}\n\nAccount Status: Active ✅"
                inline_keyboard = {"inline_keyboard": [
                    [{"text": "💳 Deposit Funds", "callback_data": "deposit_funds"}],
                    [{"text": "🔙 Back to Main Menu", "callback_data": "main_menu"}]
                ]}
            
            elif callback_data == "deposit_funds":
                # Send GCash QR code exactly like primostorebot
                gcash_qr_message = "📋 Steps to Deposit:\n3. Screenshot your receipt\n4. Send receipt photo here\n5. Wait for admin approval\n6. Get balance credit instantly after approval\n\n⚠️ Important: Receipt will be sent to admin automatically\n📞 Contact: 09911127180 mb"

                # Your GCash QR code for 09911127180
                qr_code_url = "https://i.ibb.co/QcTNbMW/gcash-qr-09911127180.png"
                
                inline_keyboard = {"inline_keyboard": [
                    [{"text": "📩 Message Admin for Approval", "callback_data": "message_admin"}],
                    [{"text": "💰 Check Balance", "callback_data": "check_balance"}],
                    [{"text": "🔙 Back to Main Menu", "callback_data": "main_menu"}]
                ]}
                
                # Try to send photo with QR code
                photo_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
                photo_data = json_lib.dumps({
                    "chat_id": chat_id,
                    "photo": qr_code_url,
                    "caption": gcash_qr_message,
                    "reply_markup": inline_keyboard
                }).encode('utf-8')
                
                photo_req = urllib.request.Request(photo_url, data=photo_data, headers={'Content-Type': 'application/json'})
                try:
                    with urllib.request.urlopen(photo_req) as response:
                        logger.info(f"Sent GCash QR code to chat {chat_id}")
                    return jsonify({'status': 'ok'})
                except Exception as e:
                    logger.error(f"Failed to send QR code: {e}")
                    # Fallback to text message
                    response_text = gcash_qr_message
                    inline_keyboard = {"inline_keyboard": [
                        [{"text": "📩 Message Admin for Approval", "callback_data": "message_admin"}],
                        [{"text": "💰 Check Balance", "callback_data": "check_balance"}],
                        [{"text": "🔙 Back to Main Menu", "callback_data": "main_menu"}]
                    ]}
            
            elif callback_data == "view_cart":
                response_text = messages.get("cart_empty", "🛒 **Shopping Cart**\n\nYour cart is empty.\n\n**To add items:**\n1. Browse Products\n2. Select items \n3. Add to cart\n4. Checkout when ready")
                inline_keyboard = {"inline_keyboard": [
                    [{"text": "🏪 Browse Products", "callback_data": "browse_products"}],
                    [{"text": "🔙 Back to Main Menu", "callback_data": "main_menu"}]
                ]}
            
            elif callback_data == "my_orders":
                response_text = messages.get("orders_empty", "📦 **Order History**\n\nNo orders found.\n\n**When you make purchases:**\n• Orders will appear here\n• Track delivery status\n• View order details\n• Reorder items")
                inline_keyboard = {"inline_keyboard": [
                    [{"text": "🏪 Browse Products", "callback_data": "browse_products"}],
                    [{"text": "🔙 Back to Main Menu", "callback_data": "main_menu"}]
                ]}
            
            elif callback_data == "support":
                response_text = "🆘 Customer Support\n\n📞 Contact Information:\n💬 Telegram/WhatsApp: 09911127180\n📧 For Receipts: Send to 09911127180 mb\n👤 Support: @tiramisucakekyo\n\n⚡ We Help With:\n• Payment issues\n• Product questions\n• Account problems\n• Technical support\n• Order problems\n\n🕐 Available: 24/7\n⚡ Response: Usually within 5 minutes\n\nReady to help! Contact us now! 💪"
                inline_keyboard = {"inline_keyboard": [
                    [{"text": "💳 Payment Help", "callback_data": "deposit_funds"}],
                    [{"text": "🔙 Back to Main Menu", "callback_data": "main_menu"}]
                ]}
            
            elif callback_data == "main_menu":
                user_balance = 0.0
                product_count = 0
                try:
                    with open('data/products.json', 'r') as f:
                        products = json_lib.load(f)
                        product_count = len(products)
                except:
                    product_count = 0

                response_text = f"""🛍️ **Welcome to Premium Store!**

💎 **Your Digital Services Store**

💰 **Balance:** ₱{user_balance:.2f}
📦 **Products:** {product_count} Available

🛒 **Use the menu below to navigate:**"""
                
                inline_keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": "🏪 Browse Products", "callback_data": "browse_products"},
                            {"text": "💰 My Balance", "callback_data": "check_balance"}
                        ],
                        [
                            {"text": "💳 Deposit Funds", "callback_data": "deposit_funds"},
                            {"text": "🛒 My Cart", "callback_data": "view_cart"}
                        ],
                        [
                            {"text": "📦 My Orders", "callback_data": "my_orders"},
                            {"text": "🆘 Support", "callback_data": "support"}
                        ]
                    ]
                }
            
            elif callback_data.startswith("category_"):
                # Show products in selected category
                category = callback_data.replace("category_", "")
                try:
                    with open('data/products.json', 'r') as f:
                        products = json_lib.load(f)
                    
                    category_products = [p for p in products if p.get('category') == category]
                    
                    if category_products:
                        response_text = f"🏪 {category.title()} Products\n\nSelect a product:"
                        inline_keyboard = {"inline_keyboard": []}
                        
                        for product in category_products:
                            stock_text = f"({product['stock']} left)" if product['stock'] > 0 else "(Out of Stock)"
                            button_text = f"📦 {product['name']} - ₱{product['price']} {stock_text}"
                            inline_keyboard["inline_keyboard"].append([
                                {"text": button_text, "callback_data": f"product_{product['id']}"}
                            ])
                        
                        inline_keyboard["inline_keyboard"].append([
                            {"text": "🔙 Back to Categories", "callback_data": "browse_products"}
                        ])
                    else:
                        response_text = f"📦 {category.title()}\n\nNo products available in this category."
                        inline_keyboard = {"inline_keyboard": [[
                            {"text": "🔙 Back to Categories", "callback_data": "browse_products"}
                        ]]}
                except:
                    response_text = "❌ Error loading category products"
                    inline_keyboard = {"inline_keyboard": [[
                        {"text": "🔙 Back to Categories", "callback_data": "browse_products"}
                    ]]}
            
            elif callback_data.startswith("product_"):
                # Show individual product with quantity selection
                product_id = int(callback_data.replace("product_", ""))
                logger.info(f"User {user_id} clicked product {product_id}")
                try:
                    with open('data/products.json', 'r') as f:
                        products = json_lib.load(f)
                    
                    product = next((p for p in products if p['id'] == product_id), None)
                    
                    if product:
                        stock = product['stock']
                        stock_status = "✅ In Stock" if stock > 0 else "❌ Out of Stock"
                        
                        response_text = f"📦 {product['name']}\n\n💰 Price: ₱{product['price']} each\n📊 Stock: {stock_status} ({stock} available)\n\nSelect quantity:"
                        
                        inline_keyboard = {"inline_keyboard": []}
                        
                        if stock > 0:
                            # Add quantity buttons (1-5 or max stock)
                            qty_buttons = []
                            max_qty = min(5, stock)
                            for qty in range(1, max_qty + 1):
                                total = product['price'] * qty
                                qty_buttons.append({
                                    "text": f"{qty}x (₱{total})", 
                                    "callback_data": f"buy_{product_id}_{qty}"
                                })
                            
                            # Add quantity buttons in rows of 2
                            for i in range(0, len(qty_buttons), 2):
                                row = qty_buttons[i:i+2]
                                inline_keyboard["inline_keyboard"].append(row)
                            
                            # Always add custom quantity option
                            inline_keyboard["inline_keyboard"].append([
                                {"text": f"➕ Custom (Max {stock})", "callback_data": f"custom_qty_{product_id}"}
                            ])
                        
                        inline_keyboard["inline_keyboard"].append([
                            {"text": "🔙 Back to Category", "callback_data": f"category_{product['category']}"}
                        ])
                    else:
                        response_text = "❌ Product not found"
                        inline_keyboard = {"inline_keyboard": [[
                            {"text": "🔙 Back to Categories", "callback_data": "browse_products"}
                        ]]}
                except:
                    response_text = "❌ Error loading product"
                    inline_keyboard = {"inline_keyboard": [[
                        {"text": "🔙 Back to Categories", "callback_data": "browse_products"}
                    ]]}
            
            elif callback_data.startswith("buy_"):
                # Show purchase confirmation
                parts = callback_data.replace("buy_", "").split("_")
                product_id = int(parts[0])
                quantity = int(parts[1])
                
                try:
                    # Load product and user data
                    with open('data/products.json', 'r') as f:
                        products = json_lib.load(f)
                    with open('data/users.json', 'r') as f:
                        users = json_lib.load(f)
                    
                    product = next((p for p in products if p['id'] == product_id), None)
                    user_balance = users.get(user_id, {}).get('balance', 0)
                    
                    if not product:
                        response_text = "❌ Product not found"
                        inline_keyboard = {"inline_keyboard": [[
                            {"text": "🔙 Back to Categories", "callback_data": "browse_products"}
                        ]]}
                    elif product['stock'] < quantity:
                        response_text = f"❌ **Insufficient Stock**\n\nOnly {product['stock']} items available.\nYou tried to buy {quantity} items."
                        inline_keyboard = {"inline_keyboard": [[
                            {"text": "🔙 Back to Product", "callback_data": f"product_{product_id}"}
                        ]]}
                    else:
                        total_cost = product['price'] * quantity
                        
                        # Show confirmation instead of immediate purchase
                        response_text = f"🛒 **Purchase Confirmation**\n\n📦 **Product:** {product['name'].title()}\n🔢 **Quantity:** {quantity}\n💰 **Price per item:** ₱{product['price']}\n💸 **Total Cost:** ₱{total_cost}\n\n💳 **Your Balance:** ₱{user_balance}\n💰 **After Purchase:** ₱{user_balance - total_cost}\n\n❓ **Are you sure you want to buy this?**"
                        
                        if user_balance < total_cost:
                            response_text += f"\n\n❌ **Insufficient Balance!**\nYou need ₱{total_cost - user_balance} more to complete this purchase."
                            inline_keyboard = {"inline_keyboard": [
                                [{"text": "💰 Add Balance", "callback_data": "add_balance"}],
                                [{"text": "🔙 Back to Product", "callback_data": f"product_{product_id}"}]
                            ]}
                        else:
                            inline_keyboard = {"inline_keyboard": [
                                [{"text": "✅ Yes, Buy Now!", "callback_data": f"confirm_buy_{product_id}_{quantity}"}],
                                [{"text": "❌ Cancel", "callback_data": f"product_{product_id}"}]
                            ]}
                except:
                    response_text = "❌ Error loading purchase details"
                    inline_keyboard = {"inline_keyboard": [[
                        {"text": "🔙 Back to Categories", "callback_data": "browse_products"}
                    ]]}
            
            elif callback_data.startswith("confirm_buy_"):
                # Process actual purchase after confirmation
                parts = callback_data.replace("confirm_buy_", "").split("_")
                product_id = int(parts[0])
                quantity = int(parts[1])
                
                try:
                    # Load product and user data
                    with open('data/products.json', 'r') as f:
                        products = json_lib.load(f)
                    with open('data/users.json', 'r') as f:
                        users = json_lib.load(f)
                    
                    product = next((p for p in products if p['id'] == product_id), None)
                    user_balance = users.get(user_id, {}).get('balance', 0)
                    
                    if not product:
                        response_text = "❌ Product not found"
                        inline_keyboard = {"inline_keyboard": [[
                            {"text": "🔙 Back to Categories", "callback_data": "browse_products"}
                        ]]}
                    elif product['stock'] < quantity:
                        response_text = f"❌ **Insufficient Stock**\n\nOnly {product['stock']} items available.\nYou tried to buy {quantity} items."
                        inline_keyboard = {"inline_keyboard": [[
                            {"text": "🔙 Back to Product", "callback_data": f"product_{product_id}"}
                        ]]}
                    else:
                        total_cost = product['price'] * quantity
                        
                        if user_balance < total_cost:
                            response_text = f"""❌ **Insufficient Balance**

💰 **Your Balance:** ₱{user_balance}
💸 **Required:** ₱{total_cost}
💔 **Short:** ₱{total_cost - user_balance}

Please deposit more funds to complete this purchase."""
                            inline_keyboard = {"inline_keyboard": [
                                [{"text": "💳 Deposit Funds", "callback_data": "deposit_funds"}],
                                [{"text": "🔙 Back to Product", "callback_data": f"product_{product_id}"}]
                            ]}
                        else:
                            # Process successful purchase
                            # Update user balance
                            if user_id not in users:
                                users[user_id] = {"balance": 0, "total_spent": 0}
                            users[user_id]["balance"] = user_balance - total_cost
                            users[user_id]["total_spent"] = users[user_id].get("total_spent", 0) + total_cost
                            
                            # Update product stock
                            for p in products:
                                if p['id'] == product_id:
                                    p['stock'] -= quantity
                                    break
                            
                            # Save updates
                            with open('data/users.json', 'w') as f:
                                json_lib.dump(users, f, indent=2)
                            with open('data/products.json', 'w') as f:
                                json_lib.dump(products, f, indent=2)
                            
                            response_text = f"""✅ **Purchase Successful!**

🛍️ **Product:** {product['name']}
📦 **Quantity:** {quantity}x
💰 **Total Paid:** ₱{total_cost}
💳 **Remaining Balance:** ₱{users[user_id]['balance']}

📋 **Your purchase details will be sent shortly!**

Thank you for shopping with us! 🎉"""
                            
                            inline_keyboard = {"inline_keyboard": [
                                [{"text": "🏪 Buy More", "callback_data": "browse_products"}],
                                [{"text": "📦 My Orders", "callback_data": "my_orders"}],
                                [{"text": "🏠 Main Menu", "callback_data": "main_menu"}]
                            ]}
                            
                            # Send product files/accounts to user
                            try:
                                with open('data/product_files.json', 'r') as f:
                                    product_files = json_lib.load(f)
                                
                                if str(product_id) in product_files:
                                    available_files = [f for f in product_files[str(product_id)] if f['status'] == 'available']
                                    
                                    if available_files and len(available_files) >= quantity:
                                        # Send account details to customer
                                        for i in range(quantity):
                                            file_data = available_files[i]
                                            file_data['status'] = 'sold'
                                            file_data['sold_to'] = user_id
                                            file_data['sold_at'] = json_lib.dumps({"timestamp": "now"})
                                            
                                            # NOTIFY ADMIN OF SALE
                                            try:
                                                admin_notification = f"""🎉 NEW SALE!

👤 Customer: {user_id}
📦 Product: {product['name']}
💰 Price: ₱{product['price']}
🔢 Quantity: {quantity}
💸 Total: ₱{product['price'] * quantity}

🔐 Account Details:
📧 Email: {file_data['details']['email']}
🔑 Password: {file_data['details']['password']}

💳 Account delivered automatically!"""
                                                
                                                admin_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                                                admin_req = urllib.request.Request(admin_url, 
                                                    data=json_lib.dumps({
                                                        'chat_id': '7240133914',
                                                        'text': admin_notification
                                                    }).encode('utf-8'),
                                                    headers={'Content-Type': 'application/json'})
                                                urllib.request.urlopen(admin_req)
                                            except Exception as e:
                                                logger.error(f"Failed to notify admin of sale: {e}")
                                            
                                            # Send account details
                                            if file_data['type'] == 'account':
                                                account_message = f"""📦 Your {product['name']} Account #{i+1}

🔐 Login Credentials:
📧 Email: {file_data['details']['email']}
🔑 Password: {file_data['details']['password']}
💎 Subscription: {file_data['details'].get('subscription', 'Premium Access')}

📋 Instructions:
{file_data['details'].get('instructions', 'Login with these credentials')}

🛡️ WARRANTY ACTIVATION:
Vouch @tiramisucakekyo within 24 hours to activate warranty.
DM him with the vouch!

⚠️ Important: Keep these credentials safe!"""
                                                
                                                # Send account details to customer (no markdown to avoid errors)
                                                account_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                                                account_data = json_lib.dumps({
                                                    "chat_id": user_id,
                                                    "text": account_message
                                                }).encode('utf-8')
                                                account_req = urllib.request.Request(account_url, data=account_data, headers={'Content-Type': 'application/json'})
                                                urllib.request.urlopen(account_req)
                                        
                                        # Save updated product files
                                        with open('data/product_files.json', 'w') as f:
                                            json_lib.dump(product_files, f, indent=2)
                                    else:
                                        # Not enough files - alert admin
                                        admin_alert = f"⚠️ ALERT: {product['name']} sold but only {len(available_files)} accounts available for {quantity} requested!"
                                        admin_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                                        admin_data = json_lib.dumps({
                                            "chat_id": "7240133914",
                                            "text": admin_alert
                                        }).encode('utf-8')
                                        admin_req = urllib.request.Request(admin_url, data=admin_data, headers={'Content-Type': 'application/json'})
                                        urllib.request.urlopen(admin_req)
                            except Exception as e:
                                # Send error to admin
                                error_msg = f"❌ File delivery error for {product['name']}: {str(e)}"
                                admin_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                                admin_data = json_lib.dumps({
                                    "chat_id": "7240133914",
                                    "text": error_msg
                                }).encode('utf-8')
                                admin_req = urllib.request.Request(admin_url, data=admin_data, headers={'Content-Type': 'application/json'})
                                urllib.request.urlopen(admin_req)
                            
                except Exception as e:
                    response_text = f"❌ Purchase failed: {str(e)}"
                    inline_keyboard = {"inline_keyboard": [[
                        {"text": "🔙 Back to Product", "callback_data": f"product_{product_id}"}
                    ]]}
            
            elif callback_data == "add_balance":
                # Show balance deposit instructions
                response_text = """💳 **Deposit Funds**

**📋 Steps to Deposit:**
1. Send to GCash: 09911127180
2. Screenshot your receipt  
3. Send receipt photo here
4. Wait for admin approval
5. Get balance credit instantly after approval

⚠️ **Important:** Send receipt as photo to this bot
📞 **Contact:** 09911127180 mb"""
                
                inline_keyboard = {"inline_keyboard": [[
                    {"text": "🔙 Back to Main Menu", "callback_data": "main_menu"}
                ]]}

            elif callback_data.startswith("custom_qty_"):
                # Handle custom quantity selection
                product_id = int(callback_data.replace("custom_qty_", ""))
                try:
                    with open('data/products.json', 'r') as f:
                        products = json_lib.load(f)
                    
                    product = next((p for p in products if p['id'] == product_id), None)
                    if product:
                        response_text = f"""📦 {product['name']} - Custom Quantity

💰 Price: ₱{product['price']} each
📊 Available: {product['stock']} items

Please send the quantity you want to order.

Example: Type "5" to order 5 items

Max quantity: {product['stock']}"""
                        
                        inline_keyboard = {"inline_keyboard": [
                            [{"text": "🔙 Back to Product", "callback_data": f"product_{product_id}"}]
                        ]}
                    else:
                        response_text = "❌ Product not found"
                        inline_keyboard = {"inline_keyboard": [[
                            {"text": "🔙 Back to Categories", "callback_data": "browse_products"}
                        ]]}
                except:
                    response_text = "❌ Error loading product"
                    inline_keyboard = {"inline_keyboard": [[
                        {"text": "🔙 Back to Categories", "callback_data": "browse_products"}
                    ]]}
            
            elif callback_data.startswith("approve_receipt_"):
                receipt_id = callback_data.replace("approve_receipt_", "")
                # Approve receipt logic
                try:
                    with open('data/pending_receipts.json', 'r') as f:
                        receipts = json_lib.load(f)
                    
                    # Find and update receipt
                    for receipt in receipts:
                        if str(receipt.get('receipt_id')) == receipt_id:
                            receipt['status'] = 'approved'
                            user_chat_id = receipt['chat_id']
                            user_name = receipt.get('first_name', 'Customer')
                            
                            # Save updated receipts
                            with open('data/pending_receipts.json', 'w') as f:
                                json_lib.dump(receipts, f, indent=2)
                            
                            # Notify customer
                            customer_message = f"✅ Receipt Approved!\n\n💰 Your deposit has been approved\n🎉 Balance will be credited shortly\n\nThank you for your payment! 💙"
                            
                            customer_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                            customer_data = json_lib.dumps({
                                "chat_id": user_chat_id,
                                "text": customer_message
                            }).encode('utf-8')
                            
                            customer_req = urllib.request.Request(customer_url, data=customer_data, headers={'Content-Type': 'application/json'})
                            urllib.request.urlopen(customer_req)
                            
                            response_text = f"✅ Receipt #{receipt_id} Approved!\n\nCustomer {user_name} has been notified."
                            break
                    else:
                        response_text = f"❌ Receipt #{receipt_id} not found"
                        
                except Exception as e:
                    response_text = f"❌ Error approving receipt: {str(e)}"
                
                inline_keyboard = {"inline_keyboard": []}
                
            elif callback_data.startswith("reject_receipt_"):
                receipt_id = callback_data.replace("reject_receipt_", "")
                # Reject receipt logic
                try:
                    with open('data/pending_receipts.json', 'r') as f:
                        receipts = json_lib.load(f)
                    
                    # Find and update receipt
                    for receipt in receipts:
                        if str(receipt.get('receipt_id')) == receipt_id:
                            receipt['status'] = 'rejected'
                            user_chat_id = receipt['chat_id']
                            user_name = receipt.get('first_name', 'Customer')
                            
                            # Save updated receipts
                            with open('data/pending_receipts.json', 'w') as f:
                                json_lib.dump(receipts, f, indent=2)
                            
                            # Notify customer
                            customer_message = f"❌ Receipt Rejected\n\nYour receipt was not approved. Please contact support if you believe this is an error.\n\n📞 Contact: 09911127180"
                            
                            customer_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                            customer_data = json_lib.dumps({
                                "chat_id": user_chat_id,
                                "text": customer_message
                            }).encode('utf-8')
                            
                            customer_req = urllib.request.Request(customer_url, data=customer_data, headers={'Content-Type': 'application/json'})
                            urllib.request.urlopen(customer_req)
                            
                            response_text = f"❌ Receipt #{receipt_id} Rejected\n\nCustomer {user_name} has been notified."
                            break
                    else:
                        response_text = f"❌ Receipt #{receipt_id} not found"
                        
                except Exception as e:
                    response_text = f"❌ Error rejecting receipt: {str(e)}"
                
                inline_keyboard = {"inline_keyboard": []}
                
            else:
                response_text = "❌ Unknown action"
                inline_keyboard = {"inline_keyboard": [[
                    {"text": "🔙 Back to Main Menu", "callback_data": "main_menu"}
                ]]}
            
            # Edit the message with new content
            edit_url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
            edit_data = json_lib.dumps({
                "chat_id": chat_id,
                "message_id": message_id,
                "text": response_text,
                "reply_markup": inline_keyboard
            }).encode('utf-8')
            
            # DEBUG: Log the request details
            logger.info(f"MAIN.PY HANDLER: Processing callback {callback_data} for user {user_id}")
            logger.info(f"DEBUG: chat_id={chat_id}, message_id={message_id}")
            logger.info(f"DEBUG: text='{response_text}'")
            logger.info(f"DEBUG: keyboard={inline_keyboard}")
            
            edit_req = urllib.request.Request(edit_url, data=edit_data, headers={'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(edit_req) as response:
                    logger.info(f"SUCCESS: Handled callback: {callback_data}")
            except Exception as e:
                logger.error(f"FAILED to edit message for user {user_id}: {e}")
                logger.error(f"FAILED request data: {edit_data.decode('utf-8')}")
                
                # Try alternative: send new message instead of editing
                try:
                    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    send_data = json_lib.dumps({
                        "chat_id": chat_id,
                        "text": response_text,
                        "reply_markup": inline_keyboard
                    }).encode('utf-8')
                    send_req = urllib.request.Request(send_url, data=send_data, headers={'Content-Type': 'application/json'})
                    with urllib.request.urlopen(send_req) as response:
                        logger.info(f"FALLBACK SUCCESS: Sent new message for {callback_data}")
                except Exception as e2:
                    logger.error(f"FALLBACK FAILED: {e2}")
            
            return jsonify({'status': 'ok'})

        # Handle incoming messages
        elif update_data and 'message' in update_data:
            import urllib.request
            import json as json_lib
            from datetime import datetime
            
            message = update_data['message']
            chat_id = str(message['chat']['id'])
            user_id = str(message['from']['id'])
            text = message.get('text', '')
            
            # Load admin configuration - SECURE & PROTECTED
            admin_users = []
            try:
                with open('config/admin_settings.json', 'r') as f:
                    admin_config = json_lib.load(f)
                    admin_users = admin_config.get('admin_users', [])
                    # Security: Protect against unauthorized admin changes
                    if not admin_config.get('protected', True):
                        admin_config['protected'] = True
                        with open('config/admin_settings.json', 'w') as f:
                            json_lib.dump(admin_config, f, indent=2)
                logger.info(f"Loaded admin users: {admin_users}")
            except Exception as e:
                logger.error(f"Error loading admin config: {e}")
                admin_users = ['7240133914']  # Fallback to your ID only
            
            # Check if user is admin - HARDCODED SECURITY
            is_admin = str(user_id) in [str(x) for x in admin_users] or user_id == "7240133914"
            logger.info(f"User {user_id} admin check: {is_admin}")
            
            bot_token = os.environ.get('BOT_TOKEN')
            
            # Different responses for admins vs regular users
            if is_admin:
                # Debug logging
                logger.info(f"Admin command received: {text}")
                logger.info(f"Pipe count: {text.count('|')}")
                logger.info(f"Command type check - /addacc: {text.startswith('/addacc')}")
                
                if text.startswith('/add ') and not text.startswith('/addacc'):
                    # SUPER SIMPLE product addition - just "/add ProductName Price Stock"
                    logger.info("Processing simple product addition...")
                    try:
                        parts = text.replace('/add ', '').split()
                        
                        if len(parts) >= 3:
                            # Get name (everything except last 2 parts)
                            name = ' '.join(parts[:-2])
                            price = float(parts[-2])
                            stock = int(parts[-1])
                        else:
                            raise ValueError("Need at least name, price, and stock")
                        
                        # Auto-fill everything else
                        category = 'digital'
                        description = f"{name} - Premium Digital Service"
                        emoji = '⭐'
                        
                        # Load existing products
                        products = []
                        try:
                            with open('data/products.json', 'r') as f:
                                products = json_lib.load(f)
                        except:
                            pass
                        
                        # Generate new ID
                        max_id = max([p['id'] for p in products], default=0) if products else 0
                        new_id = max_id + 1
                        
                        # Add new product in the format the old system expects
                        new_product = {
                            "id": new_id,
                            "name": name,
                            "description": description,
                            "price": price,
                            "category": category,
                            "stock": stock,
                            "image_url": "",
                            "created_at": datetime.now().isoformat()
                        }
                        
                        products.append(new_product)
                        
                        # Save products to the file that data_manager reads
                        with open('data/products.json', 'w') as f:
                            json_lib.dump(products, f, indent=2)
                        
                        response_text = f"""✅ Product Added!

📦 {name}
💰 ₱{price}
📊 {stock} available

➕ Add another: /add ProductName Price Stock
📊 View all: /products"""

                    except Exception as e:
                        response_text = f"""❌ Error Adding Product

Super Simple Format:
/add ProductName Price Stock

Examples:
• /add Netflix Premium 149 50
• /add Spotify 120 25
• /add Steam Wallet 500 15

Error: {str(e)}"""
                    
                elif text.startswith('/history '):
                    # Show balance history for a user: /history UserID
                    try:
                        user_id_to_check = text.replace('/history ', '').strip()
                        
                        if not user_id_to_check:
                            response_text = "❌ Format: /history UserID\n\nExample: /history 123456789"
                        else:
                            # Load balance history
                            try:
                                with open('data/balance_history.json', 'r') as f:
                                    history_data = json_lib.load(f)
                            except:
                                history_data = {}
                            
                            user_history = history_data.get(user_id_to_check, [])
                            
                            if not user_history:
                                response_text = f"📜 **Balance History**\n\nNo balance history found for user {user_id_to_check}"
                            else:
                                response_text = f"📜 **Balance History for User {user_id_to_check}**\n\n"
                                
                                # Show last 10 transactions
                                for transaction in user_history[-10:]:
                                    action = transaction.get('action', 'Unknown')
                                    amount = transaction.get('amount', 0)
                                    new_balance = transaction.get('new_balance', 0)
                                    timestamp = transaction.get('timestamp', 'Unknown')
                                    
                                    # Format action emoji
                                    if action == 'added':
                                        emoji = "💰 +"
                                        color = "✅"
                                    elif action == 'removed':
                                        emoji = "💸 -"
                                        color = "❌"
                                    elif action == 'spent':
                                        emoji = "🛒 -"
                                        color = "🔴"
                                    else:
                                        emoji = "📝"
                                        color = "ℹ️"
                                    
                                    response_text += f"{color} **{action.title()}** {emoji}₱{amount}\n"
                                    response_text += f"💳 New Balance: ₱{new_balance}\n"
                                    response_text += f"🕐 {timestamp}\n\n"
                                
                                if len(user_history) > 10:
                                    response_text += f"... and {len(user_history) - 10} more transactions"
                    except Exception as e:
                        response_text = f"❌ Error getting history: {str(e)}\n\nFormat: /history UserID"

                elif text.startswith('/addbalance '):
                    # Add balance to user: /addbalance UserID Amount
                    try:
                        parts = text.replace('/addbalance ', '').split()
                        if len(parts) >= 2:
                            target_user_id = parts[0]
                            amount = float(parts[1])
                            
                            # Load users
                            users = {}
                            try:
                                with open('data/users.json', 'r') as f:
                                    users = json_lib.load(f)
                            except:
                                pass
                            
                            # Add balance
                            if target_user_id not in users:
                                users[target_user_id] = {"balance": 0, "total_deposited": 0, "total_spent": 0}
                            
                            old_balance = users[target_user_id].get("balance", 0)
                            users[target_user_id]["balance"] = old_balance + amount
                            users[target_user_id]["total_deposited"] = users[target_user_id].get("total_deposited", 0) + amount
                            new_balance = users[target_user_id]["balance"]
                            
                            # Save users
                            with open('data/users.json', 'w') as f:
                                json_lib.dump(users, f, indent=2)
                            
                            # Track balance history
                            try:
                                from datetime import datetime
                                with open('data/balance_history.json', 'r') as f:
                                    history = json_lib.load(f)
                            except:
                                history = {}
                            
                            if target_user_id not in history:
                                history[target_user_id] = []
                            
                            history[target_user_id].append({
                                "action": "added",
                                "amount": amount,
                                "old_balance": old_balance,
                                "new_balance": new_balance,
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "admin_id": user_id
                            })
                            
                            with open('data/balance_history.json', 'w') as f:
                                json_lib.dump(history, f, indent=2)
                            
                            # Notify user
                            user_message = f"💰 Balance Added!\n\n✅ +₱{amount} added to your account\n💳 New Balance: ₱{users[target_user_id]['balance']}\n\nYou can now shop! 🎉"
                            
                            user_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                            user_data = json_lib.dumps({
                                "chat_id": target_user_id,
                                "text": user_message
                            }).encode('utf-8')
                            
                            user_req = urllib.request.Request(user_url, data=user_data, headers={'Content-Type': 'application/json'})
                            try:
                                urllib.request.urlopen(user_req)
                            except:
                                pass
                            
                            response_text = f"✅ Balance Added!\n\n💰 Added ₱{amount} to user {target_user_id}\n💳 New Balance: ₱{users[target_user_id]['balance']}\n\nUser has been notified! 🎉"
                        else:
                            response_text = "❌ Format: /addbalance UserID Amount\n\nExample: /addbalance 123456789 100"
                    except Exception as e:
                        response_text = f"❌ Error adding balance: {str(e)}\n\nFormat: /addbalance UserID Amount"
                
                elif text.startswith('/removebalance '):
                    # Remove balance from user: /removebalance UserID Amount
                    try:
                        parts = text.replace('/removebalance ', '').split()
                        if len(parts) >= 2:
                            target_user_id = parts[0]
                            amount = float(parts[1])
                            
                            # Load users
                            users = {}
                            try:
                                with open('data/users.json', 'r') as f:
                                    users = json_lib.load(f)
                            except:
                                pass
                            
                            # Check if user exists
                            if target_user_id not in users:
                                response_text = f"❌ User {target_user_id} not found in system"
                            else:
                                current_balance = users[target_user_id].get("balance", 0)
                                
                                if current_balance < amount:
                                    response_text = f"❌ Insufficient Balance!\n\n💰 Current Balance: ₱{current_balance}\n💸 Requested Deduction: ₱{amount}\n📉 Short: ₱{amount - current_balance}\n\nCannot deduct more than available balance."
                                else:
                                    # Deduct balance
                                    users[target_user_id]["balance"] = current_balance - amount
                                    new_balance = users[target_user_id]["balance"]
                                    
                                    # Save users
                                    with open('data/users.json', 'w') as f:
                                        json_lib.dump(users, f, indent=2)
                                    
                                    # Track balance history
                                    try:
                                        from datetime import datetime
                                        with open('data/balance_history.json', 'r') as f:
                                            history = json_lib.load(f)
                                    except:
                                        history = {}
                                    
                                    if target_user_id not in history:
                                        history[target_user_id] = []
                                    
                                    history[target_user_id].append({
                                        "action": "removed",
                                        "amount": amount,
                                        "old_balance": current_balance,
                                        "new_balance": new_balance,
                                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "admin_id": user_id
                                    })
                                    
                                    with open('data/balance_history.json', 'w') as f:
                                        json_lib.dump(history, f, indent=2)
                                    
                                    # Notify user about deduction
                                    user_message = f"💸 Balance Deducted!\n\n❌ -₱{amount} removed from your account\n💳 New Balance: ₱{users[target_user_id]['balance']}\n\nContact admin if this is incorrect."
                                    
                                    user_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                                    user_data = json_lib.dumps({
                                        "chat_id": target_user_id,
                                        "text": user_message
                                    }).encode('utf-8')
                                    
                                    user_req = urllib.request.Request(user_url, data=user_data, headers={'Content-Type': 'application/json'})
                                    try:
                                        urllib.request.urlopen(user_req)
                                    except:
                                        pass
                                    
                                    response_text = f"✅ Balance Deducted!\n\n💸 Removed ₱{amount} from user {target_user_id}\n💳 New Balance: ₱{users[target_user_id]['balance']}\n\nUser has been notified! 📢"
                        else:
                            response_text = "❌ Format: /removebalance UserID Amount\n\nExample: /removebalance 123456789 50"
                    except Exception as e:
                        response_text = f"❌ Error removing balance: {str(e)}\n\nFormat: /removebalance UserID Amount"
                
                elif text.startswith('/removestock '):
                    # Remove specific amount of stock: /removestock product amount
                    try:
                        parts = text.replace('/removestock ', '').split()
                        if len(parts) >= 2:
                            product_name = parts[0].lower()
                            amount = int(parts[1])
                            
                            # Product mapping
                            product_map = {
                                'capcut': "1", 'spotify': "2", 'disney_shared': "3", 'quizlet': "4", 
                                'chatgpt': "5", 'studocu': "6", 'perplexity': "7", 'canva': "8", 
                                'picsart': "9", 'surfshark': "10", 'youtube_1m': "11", 'youtube_3m': "12",
                                'disney_solo': "13", 'capcut_7d': "14",
                                # Alternative names
                                'disney': "3", 'disney+': "3", 'disneyplus': "3", 'disney-shared': "3", 'disneyshared': "3",
                                'disney+solo': "13", 'disney-solo': "13", 'disneyplus-solo': "13", 'disneyplussolo': "13", 'disneysolo': "13",
                                'gpt': "5", 'chat-gpt': "5", 'syudocu': "6", 'studycu': "6", 'studecu': "6",
                                'perplexity-ai': "7", 'canva-pro': "8", 'picsart-gold': "9",
                                'surf-shark': "10", 'surfshark-vpn': "10",
                                'youtube1m': "11", 'yt1m': "11", 'yt1': "11", 'youtube1': "11",
                                'youtube3m': "12", 'yt3m': "12", 'yt3': "12", 'youtube3': "12"
                            }
                            product_id = product_map.get(product_name, None)
                            
                            if not product_id:
                                response_text = f"❌ Unknown product: {product_name}\n\nAvailable: capcut, capcut_7d, spotify, disney_shared, disney_solo, quizlet, chatgpt, studocu, perplexity, canva, picsart, surfshark, youtube_1m, youtube_3m"
                            else:
                                # Load product files
                                try:
                                    with open('data/product_files.json', 'r') as f:
                                        product_files = json_lib.load(f)
                                except:
                                    product_files = {}
                                
                                if product_id in product_files:
                                    available = [acc for acc in product_files[product_id] if acc['status'] == 'available']
                                    if len(available) >= amount:
                                        # Remove the requested amount
                                        removed = 0
                                        for acc in available[:amount]:
                                            acc['status'] = 'removed_by_admin'
                                            acc['removed_at'] = datetime.now().isoformat()
                                            removed += 1
                                        
                                        # Save updated files
                                        with open('data/product_files.json', 'w') as f:
                                            json_lib.dump(product_files, f, indent=2)
                                        
                                        # Update product stock
                                        try:
                                            with open('data/products.json', 'r') as f:
                                                products = json_lib.load(f)
                                            
                                            for product in products:
                                                if product['id'] == int(product_id):
                                                    new_stock = len([acc for acc in product_files[product_id] if acc['status'] == 'available'])
                                                    product['stock'] = new_stock
                                                    break
                                            
                                            with open('data/products.json', 'w') as f:
                                                json_lib.dump(products, f, indent=2)
                                        except:
                                            pass
                                        
                                        remaining = len([acc for acc in product_files[product_id] if acc['status'] == 'available'])
                                        response_text = f"✅ **Stock Removed!**\n\n📦 **Product:** {product_name.title()}\n❌ **Removed:** {removed} accounts\n📊 **Remaining:** {remaining} accounts"
                                    else:
                                        response_text = f"❌ Not enough stock!\n\n📦 Available: {len(available)}\n🔢 Requested: {amount}"
                                else:
                                    response_text = f"❌ No accounts found for {product_name}"
                        else:
                            response_text = "❌ Format: /removestock ProductName Amount\n\nExample: /removestock canva 5"
                    except Exception as e:
                        response_text = f"❌ Error removing stock: {str(e)}"

                elif text.startswith('/leaderboard'):
                    # Show top users by spending (ADMIN VERSION - shows balance)
                    try:
                        with open('data/users.json', 'r') as f:
                            users_data = json_lib.load(f)
                    except:
                        users_data = {}
                    
                    if not users_data:
                        response_text = "📊 **Leaderboard**\n\nNo users found yet!"
                    else:
                        # Sort users by total spent (descending)
                        sorted_users = sorted(users_data.items(), key=lambda x: x[1].get('total_spent', 0), reverse=True)
                        
                        response_text = "🏆 **Top Spenders Leaderboard** (Admin View)\n\n"
                        
                        for i, (user_id_key, user_info) in enumerate(sorted_users[:10], 1):
                            total_spent = user_info.get('total_spent', 0)
                            balance = user_info.get('balance', 0)
                            
                            # Get user info - try multiple sources
                            username = "Unknown User"
                            try:
                                # First try to get from stored user data
                                if 'username' in user_info:
                                    username = f"@{user_info['username']}"
                                elif 'first_name' in user_info:
                                    username = user_info['first_name']
                                else:
                                    # Last resort: try Telegram API
                                    user_chat = application.bot.get_chat(user_id_key)
                                    username = f"@{user_chat.username}" if user_chat.username else user_chat.first_name or f"User{user_id_key[-4:]}"
                            except:
                                username = f"User{user_id_key[-4:]}"
                            
                            # Add medal emojis for top 3
                            if i == 1:
                                medal = "🥇"
                            elif i == 2:
                                medal = "🥈"
                            elif i == 3:
                                medal = "🥉"
                            else:
                                medal = f"{i}."
                            
                            response_text += f"{medal} **{username}**\n"
                            response_text += f"💸 Spent: ₱{total_spent} | 💰 Balance: ₱{balance}\n\n"
                        
                        if len(sorted_users) > 10:
                            response_text += f"... and {len(sorted_users) - 10} more users"

                elif text.startswith('/stock'):
                    # Show current stock levels for all products (ADMIN VERSION - detailed)
                    try:
                        with open('data/products.json', 'r') as f:
                            products = json_lib.load(f)
                    except:
                        products = []
                    
                    if not products:
                        response_text = "📦 **Stock Levels**\n\nNo products found!"
                    else:
                        response_text = "📦 **Current Stock Levels** (Admin View)\n\n"
                        
                        for product in products:
                            name = product.get('name', 'Unknown')
                            stock = product.get('stock', 0)
                            price = product.get('price', 0)
                            
                            # Stock status indicator
                            if stock == 0:
                                status = "❌ Out of Stock"
                            elif stock <= 5:
                                status = "⚠️ Low Stock"
                            else:
                                status = "✅ In Stock"
                            
                            response_text += f"**{name.title()}**\n"
                            response_text += f"📊 Stock: {stock} | 💰 Price: ₱{price}\n"
                            response_text += f"Status: {status}\n\n"

                elif text.startswith('/broadcast '):
                    # Broadcast message to all users: /broadcast Your message here
                    try:
                        broadcast_message = text.replace('/broadcast ', '', 1)
                        
                        if not broadcast_message.strip():
                            response_text = "❌ Format: /broadcast Your message here\n\nExample: /broadcast 🎉 New products added to store!"
                        else:
                            # Load all users
                            try:
                                with open('data/users.json', 'r') as f:
                                    users_data = json_lib.load(f)
                            except:
                                users_data = {}
                            
                            if not users_data:
                                response_text = "❌ No users found to broadcast to!"
                            else:
                                success_count = 0
                                failed_count = 0
                                total_users = len(users_data)
                                
                                # Send message to each user
                                for user_id_key in users_data.keys():
                                    try:
                                        broadcast_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                                        broadcast_data = json_lib.dumps({
                                            "chat_id": user_id_key,
                                            "text": f"📢 **ANNOUNCEMENT**\n\n**{broadcast_message}**\n\n━━━━━━━━━━━━━━━━\nMessage from admin: @tiramisucakekyo",
                                            "parse_mode": "Markdown"
                                        }).encode('utf-8')
                                        
                                        broadcast_req = urllib.request.Request(broadcast_url, data=broadcast_data, headers={'Content-Type': 'application/json'})
                                        urllib.request.urlopen(broadcast_req, timeout=10)
                                        success_count += 1
                                    except Exception as e:
                                        failed_count += 1
                                        continue
                                
                                # Results summary
                                response_text = f"📢 **Broadcast Complete!**\n\n✅ Successfully sent to: {success_count} users\n❌ Failed to send to: {failed_count} users\n👥 Total users: {total_users}\n\n📝 **Message sent:**\n{broadcast_message}"
                    except Exception as e:
                        response_text = f"❌ Error broadcasting message: {str(e)}\n\nFormat: /broadcast Your message here"
                
                elif text.startswith('/clearstock '):
                    # Clear all stock for a product: /clearstock product
                    try:
                        product_name = text.replace('/clearstock ', '').strip().lower()
                        
                        # Product mapping
                        product_map = {
                            'capcut': "1", 'spotify': "2", 'disney_shared': "3", 'quizlet': "4", 
                            'chatgpt': "5", 'studocu': "6", 'perplexity': "7", 'canva': "8", 
                            'picsart': "9", 'surfshark': "10", 'youtube_1m': "11", 'youtube_3m': "12",
                            'disney_solo': "13", 'capcut_7d': "14",
                            # Alternative names
                            'disney': "3", 'disney+': "3", 'disneyplus': "3", 'disney-shared': "3", 'disneyshared': "3",
                            'disney+solo': "13", 'disney-solo': "13", 'disneyplus-solo': "13", 'disneyplussolo': "13", 'disneysolo': "13",
                            'gpt': "5", 'chat-gpt': "5", 'syudocu': "6", 'studycu': "6", 'studecu': "6",
                            'perplexity-ai': "7", 'canva-pro': "8", 'picsart-gold': "9",
                            'surf-shark': "10", 'surfshark-vpn': "10",
                            'youtube1m': "11", 'yt1m': "11", 'yt1': "11", 'youtube1': "11",
                            'youtube3m': "12", 'yt3m': "12", 'yt3': "12", 'youtube3': "12"
                        }
                        product_id = product_map.get(product_name, None)
                        
                        if not product_id:
                            response_text = f"❌ Unknown product: {product_name}\n\nAvailable: capcut, capcut_7d, spotify, disney_shared, disney_solo, quizlet, chatgpt, studocu, perplexity, canva, picsart, surfshark, youtube_1m, youtube_3m"
                        else:
                            # Load product files
                            try:
                                with open('data/product_files.json', 'r') as f:
                                    product_files = json_lib.load(f)
                            except:
                                product_files = {}
                            
                            if product_id in product_files:
                                available = [acc for acc in product_files[product_id] if acc['status'] == 'available']
                                cleared_count = len(available)
                                
                                # Mark all as cleared
                                for acc in available:
                                    acc['status'] = 'cleared_by_admin'
                                    acc['cleared_at'] = datetime.now().isoformat()
                                
                                # Save updated files
                                with open('data/product_files.json', 'w') as f:
                                    json_lib.dump(product_files, f, indent=2)
                                
                                # Update product stock to 0
                                try:
                                    with open('data/products.json', 'r') as f:
                                        products = json_lib.load(f)
                                    
                                    for product in products:
                                        if product['id'] == int(product_id):
                                            product['stock'] = 0
                                            break
                                    
                                    with open('data/products.json', 'w') as f:
                                        json_lib.dump(products, f, indent=2)
                                except:
                                    pass
                                
                                response_text = f"✅ **Stock Cleared!**\n\n📦 **Product:** {product_name.title()}\n❌ **Cleared:** {cleared_count} accounts\n📊 **Stock:** 0"
                            else:
                                response_text = f"✅ **Already Clear!**\n\n📦 **Product:** {product_name.title()}\n📊 **Stock:** 0"
                    except Exception as e:
                        response_text = f"❌ Error clearing stock: {str(e)}"

                elif text.startswith('/addacc'):
                    # DIRECT /addacc HANDLER - MOVED TO PREVENT /add CONFLICT
                    logger.info("🚀 PROCESSING /addacc COMMAND DIRECTLY!")
                    logger.info(f"Line count check: {len(text.split(chr(10)))}")
                    
                    if len(text.split('\n')) < 3:
                        response_text = """📦 **Add Accounts to Products:**

**Format:**
```
/addacc [product]
email1@domain.com
email2@domain.com  
pass: password123
```

**Available Products:**
• capcut - CapCut Pro video editor
• capcut_7d - CapCut Pro (7 days)
• spotify - Spotify Premium music
• disney_shared - Disney+ Shared (4-6 users)
• disney_solo - Disney+ Solo (1 user only)
• quizlet - Quizlet Plus study tools
• chatgpt - ChatGPT Plus AI assistant  
• studocu - StudoCu Premium documents
• perplexity - Perplexity AI Pro search
• canva - Canva Pro design tools
• picsart - PicsArt Gold photo editor
• surfshark - Surfshark VPN security
• youtube_1m - YouTube Premium (1 month)
• youtube_3m - YouTube Premium (3 months)

**Examples:**
```
/addacc spotify
user@gmail.com
pass: mypass123
```"""
                    else:
                        try:
                            # Split by lines and clean
                            lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
                            logger.info(f"Direct handler - parsed {len(lines)} lines")
                            
                            # Extract product name
                            product_name = lines[0].split()[1].lower()
                            logger.info(f"Direct handler - product: {product_name}")
                            
                            # Extract emails and password
                            emails = []
                            password = "defaultpass123"
                            
                            for line in lines[1:]:
                                if '@' in line and 'pass' not in line.lower():
                                    emails.append(line.strip())
                                elif 'pass:' in line.lower():
                                    password = line.split(':', 1)[1].strip()
                                elif not '@' in line and line and not line.startswith('/'):
                                    password = line.strip()
                            
                            logger.info(f"Direct handler - found {len(emails)} emails, password: {password}")
                            
                            if emails:
                                # Load product files
                                try:
                                    with open('data/product_files.json', 'r') as f:
                                        product_files = json_lib.load(f)
                                except:
                                    product_files = {}
                                
                                # Complete product mapping for all products
                                product_map = {
                                    'capcut': "1", 'spotify': "2", 'disney_shared': "3", 'quizlet': "4", 
                                    'chatgpt': "5", 'studocu': "6", 'perplexity': "7", 'canva': "8", 
                                    'picsart': "9", 'surfshark': "10", 'youtube_1m': "11", 'youtube_3m': "12",
                                    'disney_solo': "13", 'capcut_7d': "14",
                                    # Alternative names and spellings
                                    'disney': "3", 'disney+': "3", 'disneyplus': "3", 'disney-shared': "3", 'disneyshared': "3",
                                    'disney+solo': "13", 'disney-solo': "13", 'disneyplus-solo': "13", 'disneyplussolo': "13", 'disneysolo': "13",
                                    'gpt': "5", 'chat-gpt': "5", 'chatgpt-plus': "5",
                                    'syudocu': "6", 'studycu': "6", 'studecu': "6", 'studocu-premium': "6",
                                    'perplexity-ai': "7", 'perplexity-pro': "7",
                                    'canva-pro': "8", 'canva-premium': "8",
                                    'picsart-gold': "9", 'pics-art': "9",
                                    'surf-shark': "10", 'surfshark-vpn': "10",
                                'youtube1m': "11", 'yt1m': "11", 'yt1': "11", 'youtube1': "11",
                                'youtube3m': "12", 'yt3m': "12", 'yt3': "12", 'youtube3': "12",
                                'capcut-7d': "14", 'capcut7d': "14", 'capcut_7': "14", 'capcut7': "14"
                                }
                                product_id = product_map.get(product_name, "1")
                                
                                if product_id not in product_files:
                                    product_files[product_id] = []
                                
                                # Check for duplicates and add accounts
                                added = 0
                                duplicates = []
                                
                                # Check if this is a shared product (allows duplicates)
                                is_shared_product = "shared" in product_name.lower()
                                
                                for email in emails:
                                    should_skip = False
                                    existing_product = ""
                                    
                                    # Only check for duplicates if NOT a shared product
                                    if not is_shared_product:
                                        for pid, accounts in product_files.items():
                                            for account in accounts:
                                                if account.get('details', {}).get('email', '').lower() == email.lower():
                                                    should_skip = True
                                                    # Get product name
                                                    for pname, p_id in product_map.items():
                                                        if p_id == pid:
                                                            existing_product = pname.title()
                                                            break
                                                    break
                                            if should_skip:
                                                break
                                    
                                    if should_skip:
                                        duplicates.append(f"{email} (already in {existing_product})")
                                    else:
                                        # Add the account (duplicates allowed for shared products)
                                        account = {
                                            "id": len(product_files[product_id]) + 1,
                                            "type": "account",
                                            "details": {
                                                "email": email,
                                                "password": password,
                                                "subscription": f"{product_name.title()} Premium - 1 Month",
                                                "instructions": "Login with these credentials. Do not change password for 24 hours."
                                            },
                                            "status": "available",
                                            "added_at": datetime.now().isoformat()
                                        }
                                        product_files[product_id].append(account)
                                        added += 1
                                
                                # Save product files
                                with open('data/product_files.json', 'w') as f:
                                    json_lib.dump(product_files, f, indent=2)
                                
                                # Update stock count
                                try:
                                    with open('data/products.json', 'r') as f:
                                        products = json_lib.load(f)
                                    
                                    for product in products:
                                        if product['id'] == int(product_id):
                                            new_stock = len([acc for acc in product_files[product_id] if acc['status'] == 'available'])
                                            product['stock'] = new_stock
                                            break
                                    
                                    with open('data/products.json', 'w') as f:
                                        json_lib.dump(products, f, indent=2)
                                except Exception as e:
                                    logger.error(f"Error updating stock: {e}")
                                
                                # Create response message based on results
                                if added > 0 and not duplicates:
                                    response_text = f"✅ SUCCESS! Added {added} {product_name} accounts!\n\n🔑 Password: {password}\n📦 Product: {product_name.title()}\n📊 Stock: {len(product_files[product_id])} accounts"
                                elif added > 0 and duplicates:
                                    dup_list = '\n'.join([f"• {dup}" for dup in duplicates[:3]])  # Limit to 3 to keep message short
                                    response_text = f"⚠️ PARTIAL SUCCESS! Added {added} {product_name} accounts!\n\n🔑 Password: {password}\n📦 Product: {product_name.title()}\n📊 Stock: {len(product_files[product_id])}\n\n❌ Duplicates skipped:\n{dup_list}"
                                elif duplicates and added == 0:
                                    dup_list = '\n'.join([f"• {dup}" for dup in duplicates[:3]])  # Limit to 3 
                                    response_text = f"❌ NO ACCOUNTS ADDED! All emails are duplicates.\n\n🚫 Duplicates found:\n{dup_list}\n\n💡 Use unique email addresses."
                                else:
                                    response_text = "❌ No valid emails found! Make sure to include email addresses."
                            else:
                                response_text = "❌ No valid emails found! Make sure to include email addresses."
                        except Exception as e:
                            logger.error(f"Error in direct /addacc handler: {e}")
                            response_text = f"❌ Error processing accounts: {str(e)}"
                
                elif text.startswith('/add'):
                    response_text = """➕ Add New Product

Super Simple Format:
/add ProductName Price Stock

Examples:
• /add Netflix Premium 149 50
• /add Spotify 120 25
• /add Steam Wallet 500 15

That's it! No complicated symbols needed."""

                elif text.count('|') >= 2 and text.startswith('/addproduct'):
                    # Parse product data - flexible format
                    try:
                        parts = text.replace('/addproduct ', '').split('|')
                        
                        # Required fields
                        name = parts[0].strip()
                        price = float(parts[1].strip())
                        stock = int(parts[2].strip())
                        
                        # Optional fields with defaults
                        category = parts[3].strip() if len(parts) > 3 and parts[3].strip() else 'general'
                        description = parts[4].strip() if len(parts) > 4 and parts[4].strip() else f"{name} - Premium Service"
                        emoji = parts[5].strip() if len(parts) > 5 and parts[5].strip() else '⭐'
                        
                        # Load existing products
                        products = []
                        try:
                            with open('data/products.json', 'r') as f:
                                products = json_lib.load(f)
                        except:
                            pass
                        
                        # Generate new ID
                        max_id = max([p['id'] for p in products], default=0) if products else 0
                        new_id = max_id + 1
                        
                        # Add new product in the format the old system expects
                        new_product = {
                            "id": new_id,
                            "name": name,
                            "description": description,
                            "price": price,
                            "category": category,
                            "stock": stock,
                            "image_url": "",
                            "created_at": datetime.now().isoformat()
                        }
                        
                        products.append(new_product)
                        
                        # Save products to the file that data_manager reads
                        with open('data/products.json', 'w') as f:
                            json_lib.dump(products, f, indent=2)
                        
                        response_text = f"""✅ Product Added!

📦 {name}
💰 ₱{price}
📊 {stock} available

➕ Add another: /add ProductName Price Stock
📊 View all: /products"""

                    except Exception as e:
                        response_text = f"""❌ **Error Adding Product**

**Simple Format:**
`/addproduct ProductName|Price|Stock`

**Examples:**
• `/addproduct Netflix Premium|149|50`
• `/addproduct Spotify|120|25`
• `/addproduct Steam Wallet|500|15`

**Optional extras:**
`/addproduct Name|Price|Stock|Category|Description|Emoji`

Try the simple format!"""

                elif text.startswith('/products'):
                    # Show existing products
                    try:
                        with open('config/sample_products.json', 'r') as f:
                            products = json_lib.load(f)
                        
                        if products:
                            product_list = "📦 **Your Products:**\n\n"
                            for pid, product in products.items():
                                variant = product['variants'][0] if product['variants'] else {}
                                price = variant.get('price', 0)
                                stock = variant.get('stock', 0)
                                product_list += f"{product.get('emoji', '⭐')} **{product['name']}**\n"
                                product_list += f"   💰 ₱{price} | 📊 Stock: {stock}\n"
                                product_list += f"   🏷️ {product.get('category_id', 'general')}\n\n"
                            
                            product_list += "➕ **Add New Product:** /addproduct\n"
                            product_list += "🔄 **Update Stock:** /updatestock ProductName NewAmount"
                            response_text = product_list
                        else:
                            response_text = """📦 **No Products Yet**

➕ Add your first product:
`/addproduct Netflix Premium|streaming|149|50|1 Month Netflix Premium|📺`

**Popular categories:**
• streaming - Netflix, Spotify, Disney+
• gaming - Steam, Epic Games
• productivity - Office, Adobe
• vpn - Nord VPN, Express VPN"""

                    except:
                        response_text = "❌ Error loading products. Try again!"

                elif text.startswith('/stats'):
                    try:
                        with open('config/sample_products.json', 'r') as f:
                            products = json_lib.load(f)
                        product_count = len(products)
                    except:
                        product_count = 0
                    
                    response_text = f"""📊 **Bot Statistics**

👥 **Users:** 1 registered
📦 **Products:** {product_count} available
💰 **Deposits:** 0 pending
📈 **Orders:** 0 completed

🔧 **Quick Actions:**
➕ Add Product: /addproduct
📦 View Products: /products  
👥 Manage Users: /users
💸 View Deposits: /deposits"""

                elif text.startswith('/addacc'):
                    logger.info("✅ ENTERING /addacc HANDLER NOW!")
                    # BULLETPROOF WORKING VERSION  
                    logger.info(f"PROCESSING /addacc command for admin {user_id}")
                    logger.info(f"Raw text received: {repr(text)}")
                    
                    try:
                        # Split by lines and clean
                        lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
                        logger.info(f"Parsed {len(lines)} lines from /addacc command")
                        
                        if len(lines) < 3:
                            response_text = """📦 **Add Accounts:**

**Format:**
```
/addacc spotify
email1@domain.com
email2@domain.com  
pass: password123
```

**Products:** capcut, spotify, disney, quizlet, chatgpt, studocu, perplexity, canva, picsart, surfshark"""
                        else:
                            # Extract product name
                            try:
                                product_name = lines[0].split()[1].lower()
                                logger.info(f"Product name: {product_name}")
                                
                                # Extract emails and password
                                emails = []
                                password = "defaultpass123"
                                
                                for line in lines[1:]:
                                    if '@' in line and 'pass' not in line.lower():
                                        emails.append(line.strip())
                                    elif 'pass:' in line.lower():
                                        password = line.split(':', 1)[1].strip()
                                    elif not '@' in line and line and not line.startswith('/'):
                                        # If it's not an email and not empty, treat as password
                                        password = line.strip()
                                
                                # Remove duplicates
                                emails = list(dict.fromkeys(emails))
                                logger.info(f"Found {len(emails)} unique emails, password: {password}")
                                
                                if emails:
                                    # Load product files
                                    try:
                                        with open('data/product_files.json', 'r') as f:
                                            product_files = json_lib.load(f)
                                    except:
                                        product_files = {}
                                    
                                    # Complete product mapping for all 10 products (CONSISTENT)
                                    product_map = {
                                        'capcut': "1", 'spotify': "2", 'disney': "3", 'quizlet': "4", 
                                        'chatgpt': "5", 'studocu': "6", 'perplexity': "7", 'canva': "8", 
                                        'picsart': "9", 'surfshark': "10", 'youtube_1m': "11", 'youtube_3m': "12",
                                        # Alternative names and spellings
                                        'disney+': "3", 'disneyplus': "3",
                                        'gpt': "5", 'chat-gpt': "5", 'chatgpt-plus': "5",
                                        'syudocu': "6", 'studycu': "6", 'studecu': "6", 'studocu-premium': "6",
                                        'perplexity-ai': "7", 'perplexity-pro': "7",
                                        'canva-pro': "8", 'canva-premium': "8",
                                        'picsart-gold': "9", 'pics-art': "9",
                                        'surf-shark': "10", 'surfshark-vpn': "10",
                                'youtube1m': "11", 'yt1m': "11", 'yt1': "11", 'youtube1': "11",
                                'youtube3m': "12", 'yt3m': "12", 'yt3': "12", 'youtube3': "12",
                                'capcut-7d': "14", 'capcut7d': "14", 'capcut_7': "14", 'capcut7': "14"
                                    }
                                    product_id = product_map.get(product_name, "1")
                                    
                                    if product_id not in product_files:
                                        product_files[product_id] = []
                                    
                                    # Add accounts
                                    added = 0
                                    for email in emails:
                                        account = {
                                            "id": len(product_files[product_id]) + 1,
                                            "type": "account",
                                            "details": {
                                                "email": email,
                                                "password": password,
                                                "subscription": f"{product_name.title()} Premium - 1 Month",
                                                "instructions": "Login with these credentials. Do not change password for 24 hours."
                                            },
                                            "status": "available",
                                            "added_at": datetime.now().isoformat()
                                        }
                                        product_files[product_id].append(account)
                                        added += 1
                                    
                                    # Save product files
                                    with open('data/product_files.json', 'w') as f:
                                        json_lib.dump(product_files, f, indent=2)
                                    logger.info(f"Saved {added} accounts to product_files.json")
                                    
                                    # Update stock count
                                    try:
                                        with open('data/products.json', 'r') as f:
                                            products = json_lib.load(f)
                                        
                                        for product in products:
                                            if product['id'] == int(product_id):
                                                new_stock = len([acc for acc in product_files[product_id] if acc['status'] == 'available'])
                                                product['stock'] = new_stock
                                                logger.info(f"Updated {product['name']} stock to {new_stock}")
                                                break
                                        
                                        with open('data/products.json', 'w') as f:
                                            json_lib.dump(products, f, indent=2)
                                    except Exception as e:
                                        logger.error(f"Error updating stock: {e}")
                                    
                                    response_text = f"""✅ **SUCCESS!** Added {added} {product_name} accounts!

🔑 **Password:** {password}
📦 **Product:** {product_name.title()}
📊 **Total Stock:** {len(product_files[product_id])} accounts

Ready for customers! 🛍️"""
                                else:
                                    response_text = "❌ No valid emails found! Make sure to include email addresses."
                            except:
                                response_text = "❌ Invalid format. Use: /addacc [product_name]"
                    except Exception as e:
                        logger.error(f"Error in /addacc: {e}")
                        response_text = f"❌ Error processing accounts: {str(e)}"

                elif text.startswith('/addstock'):
                    if len(text.split()) == 1:
                        response_text = """📦 **Add Account/Stock**

To add actual accounts for delivery:

**Format:**
`/addstock ProductName`

**Example:**
`/addstock netflix_premium`

This will let you add actual login details that customers receive after purchase.

📋 **Available Products:**
• Use `/products` to see your product list
• Product names are in lowercase with underscores"""

                    else:
                        product_name = text.replace('/addstock ', '').strip().lower().replace(' ', '_')
                        response_text = f"""📦 **Adding Stock for {product_name}**

Now send the account details in this format:

**For Login Accounts:**
```
Email: user@example.com
Password: password123
Notes: Any special instructions
```

**For Gift Cards/Codes:**
```
Code: XXXX-XXXX-XXXX-XXXX
Amount: $50
Notes: Gift card code
```

**For Other Services:**
Just send the details customers need to access the service.

Send the account details in your next message!"""

                        # Store the current product for next message
                        try:
                            with open('data/pending_stock.json', 'w') as f:
                                json_lib.dump({'user_id': user_id, 'product': product_name}, f)
                        except:
                            pass

                elif text.startswith('/deposits'):
                    # Show pending deposits for manual approval
                    try:
                        with open('data/deposits.json', 'r') as f:
                            deposits = json_lib.load(f)
                        
                        pending = [d for d in deposits.values() if d.get('status') == 'pending']
                        
                        if pending:
                            deposit_list = "💰 **Pending Deposits - Need Your Approval**\n\n"
                            for deposit in pending[:10]:  # Show latest 10
                                amount = deposit.get('amount', 0)
                                method = deposit.get('payment_method', 'unknown')
                                user = deposit.get('user_telegram_id', 'unknown')
                                dep_id = deposit.get('deposit_id', 'unknown')
                                
                                deposit_list += f"💸 **#{dep_id}**\n"
                                deposit_list += f"   💰 Amount: ₱{amount}\n"
                                deposit_list += f"   💳 Method: {method}\n" 
                                deposit_list += f"   👤 User: {user}\n"
                                deposit_list += f"   ✅ Approve: `/approve {dep_id}`\n"
                                deposit_list += f"   ❌ Reject: `/reject {dep_id}`\n\n"
                            
                            response_text = deposit_list
                        else:
                            response_text = """💰 **No Pending Deposits**

All deposits have been processed!

When customers send payment proof, they'll appear here for your manual approval.

🔄 **How it works:**
1. Customer sends `/deposit` and uploads payment proof
2. Deposit shows up here as "pending"  
3. You approve or reject manually
4. Balance is added automatically after approval"""

                    except:
                        response_text = "💰 **No deposits found**\n\nDeposits will appear here when customers make payments."

                elif text.startswith('/approve '):
                    deposit_id = text.replace('/approve ', '').strip()
                    # Approve deposit logic
                    response_text = f"✅ **Deposit #{deposit_id} Approved!**\n\nBalance has been added to user account."

                elif text.startswith('/reject '):
                    deposit_id = text.replace('/reject ', '').strip()
                    response_text = f"❌ **Deposit #{deposit_id} Rejected**\n\nUser has been notified."

                elif text.startswith('/receipts'):
                    # Show pending receipt approvals
                    try:
                        with open('data/pending_receipts.json', 'r') as f:
                            receipts = json_lib.load(f)
                        
                        pending = [r for r in receipts if r.get('status') == 'pending']
                        
                        if pending:
                            receipt_list = "📸 **Pending Receipt Approvals**\n\n"
                            for receipt in pending[-10:]:  # Show latest 10
                                rid = receipt.get('receipt_id', 'unknown')
                                user = receipt.get('first_name', 'Unknown')
                                username = receipt.get('username', 'No username')
                                caption = receipt.get('caption', 'No caption')
                                timestamp = receipt.get('timestamp', '')
                                
                                receipt_list += f"📸 **#{rid}**\n"
                                receipt_list += f"   👤 **User:** @{username} ({user})\n"
                                receipt_list += f"   💬 **Caption:** {caption}\n"
                                receipt_list += f"   ⏰ **Time:** {timestamp[:10]}\n"
                                receipt_list += f"   ✅ **Approve:** `/approve {rid}`\n"
                                receipt_list += f"   ❌ **Reject:** `/reject {rid}`\n"
                                receipt_list += f"   💬 **Message:** `/msg {receipt['user_id']} your_message`\n\n"
                            
                            response_text = receipt_list
                        else:
                            response_text = """📸 **No Pending Receipts**\n\nAll receipts processed!\n\n**How it works:**\n1. Customers send receipt photos to bot\n2. You get instant notification\n3. Use /approve or /reject\n4. Customer gets notified automatically"""
                    
                    except:
                        response_text = "📸 **No receipts found**\n\nReceipts will appear here when customers send payment proof."

                elif text.startswith('/approve '):
                    receipt_id = text.replace('/approve ', '').strip()
                    # Approve receipt logic
                    try:
                        with open('data/pending_receipts.json', 'r') as f:
                            receipts = json_lib.load(f)
                        
                        # Find and update receipt
                        for receipt in receipts:
                            if str(receipt.get('receipt_id')) == receipt_id:
                                receipt['status'] = 'approved'
                                user_chat_id = receipt['chat_id']
                                user_name = receipt.get('first_name', 'Customer')
                                
                                # Save updated receipts
                                with open('data/pending_receipts.json', 'w') as f:
                                    json_lib.dump(receipts, f, indent=2)
                                
                                # Notify customer
                                customer_message = f"✅ **Receipt Approved!**\n\n💰 **Your deposit has been approved**\n🎉 **Balance will be credited shortly**\n\nThank you for your payment! 💙"
                                
                                customer_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                                customer_data = json_lib.dumps({
                                    "chat_id": user_chat_id,
                                    "text": customer_message,
                                    "parse_mode": "Markdown"
                                }).encode('utf-8')
                                
                                customer_req = urllib.request.Request(customer_url, data=customer_data, headers={'Content-Type': 'application/json'})
                                urllib.request.urlopen(customer_req)
                                
                                response_text = f"✅ **Receipt #{receipt_id} Approved!**\n\n👤 **Customer:** {user_name}\n✅ **Status:** Approved\n📩 **Customer notified:** Yes\n💰 **Action:** Balance credited"
                                break
                        else:
                            response_text = f"❌ **Receipt #{receipt_id} not found**"
                    
                    except Exception as e:
                        response_text = f"❌ **Error approving receipt:** {str(e)}"

                elif text.startswith('/reject '):
                    receipt_id = text.replace('/reject ', '').strip()
                    try:
                        with open('data/pending_receipts.json', 'r') as f:
                            receipts = json_lib.load(f)
                        
                        # Find and update receipt
                        for receipt in receipts:
                            if str(receipt.get('receipt_id')) == receipt_id:
                                receipt['status'] = 'rejected'
                                user_chat_id = receipt['chat_id']
                                user_name = receipt.get('first_name', 'Customer')
                                
                                # Save updated receipts
                                with open('data/pending_receipts.json', 'w') as f:
                                    json_lib.dump(receipts, f, indent=2)
                                
                                # Notify customer
                                customer_message = f"❌ **Receipt Rejected**\n\n📸 **Your receipt was not approved**\n💬 **Reason:** Please contact admin for clarification\n📞 **Contact:** 09911127180\n\n**Please try again with a clearer receipt or contact us for help.**"
                                
                                customer_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                                customer_data = json_lib.dumps({
                                    "chat_id": user_chat_id,
                                    "text": customer_message,
                                    "parse_mode": "Markdown"
                                }).encode('utf-8')
                                
                                customer_req = urllib.request.Request(customer_url, data=customer_data, headers={'Content-Type': 'application/json'})
                                urllib.request.urlopen(customer_req)
                                
                                response_text = f"❌ **Receipt #{receipt_id} Rejected**\n\n👤 **Customer:** {user_name}\n❌ **Status:** Rejected\n📩 **Customer notified:** Yes"
                                break
                        else:
                            response_text = f"❌ **Receipt #{receipt_id} not found**"
                    
                    except Exception as e:
                        response_text = f"❌ **Error rejecting receipt:** {str(e)}"

                elif text.startswith('/msg '):
                    # Message a user: /msg 123456789 your message here
                    parts = text.replace('/msg ', '').split(' ', 1)
                    if len(parts) >= 2:
                        target_user_id = parts[0].strip()
                        message_text = parts[1].strip()
                        
                        try:
                            # Send message to user
                            message_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                            message_data = json_lib.dumps({
                                "chat_id": target_user_id,
                                "text": f"💬 **Message from Admin:**\n\n{message_text}\n\n📞 **Contact:** 09911127180",
                                "parse_mode": "Markdown"
                            }).encode('utf-8')
                            
                            message_req = urllib.request.Request(message_url, data=message_data, headers={'Content-Type': 'application/json'})
                            urllib.request.urlopen(message_req)
                            
                            response_text = f"✅ **Message Sent!**\n\n👤 **To User:** {target_user_id}\n💬 **Message:** {message_text}\n📩 **Status:** Delivered"
                        
                        except Exception as e:
                            response_text = f"❌ **Failed to send message:** {str(e)}"
                    else:
                        response_text = "❌ **Usage:** `/msg USER_ID your message here`\n\n**Example:** `/msg 123456789 Your receipt has been processed!`"

                elif text.startswith('/help'):
                    response_text = f"""🔧 Admin Help

👤 Admin ID: {user_id}

📦 Product Commands:
/add ProductName Price Stock - Add products
/products - View all products  
/addacc capcut - Add accounts to products

📸 Receipt Commands:
/receipts - View pending receipts
/approve ID - Approve deposit
/reject ID - Reject deposit  

💰 User Commands:
/addbalance UserID Amount - Add balance
/msg UserID message - Message user

📊 System Commands:
/admin - Admin panel
/stats - Statistics

💡 Quick Tips:
- Send email:password to add accounts
- Receipt photos come with ✅/❌ buttons
- System is silent like primostorebot"""

                elif text.startswith('/users'):
                    try:
                        with open('data/users.json', 'r') as f:
                            users_data = json_lib.load(f)
                    except:
                        users_data = {}
                    
                    if not users_data:
                        response_text = "👥 **All Users**\n\nNo users found"
                    else:
                        response_text = f"👥 **All Users** ({len(users_data)} total)\n\n"
                        for user_id_key, user_info in users_data.items():
                            balance = user_info.get('balance', 0)
                            total_deposited = user_info.get('total_deposited', 0)
                            total_spent = user_info.get('total_spent', 0)
                            
                            # Get user info - try multiple sources
                            username = "Unknown User"
                            try:
                                # First try to get from stored user data
                                if 'username' in user_info:
                                    username = f"@{user_info['username']}"
                                elif 'first_name' in user_info:
                                    username = user_info['first_name']
                                else:
                                    # Last resort: try Telegram API
                                    user_chat = application.bot.get_chat(user_id_key)
                                    username = f"@{user_chat.username}" if user_chat.username else user_chat.first_name or f"User{user_id_key[-4:]}"
                            except:
                                username = f"User{user_id_key[-4:]}"
                            
                            response_text += f"👤 **{username}** (ID: {user_id_key})\n"
                            response_text += f"💰 Balance: ₱{balance}\n"
                            response_text += f"📊 Deposited: ₱{total_deposited}\n"
                            response_text += f"🛒 Spent: ₱{total_spent}\n\n"

                elif text.startswith('/admin'):
                    response_text = f"Admin Panel\n\nAdmin ID: {user_id}\nStatus: Active\n\nCommands:\n/add ProductName Price Stock\n/products - View products\n/addacc capcut - Add accounts to products\n/receipts - View receipts\n/users - View all users\n/stats - Statistics\n\nSystem ready!"

                elif text.isdigit() and not text.startswith('/'):
                    # Handle custom quantity input from customer 
                    quantity = int(text)
                    
                    # Simple approach - assume capcut (product ID 1) for custom quantity
                    product_id = 1
                    
                    try:
                        # Load product and user data
                        with open('data/products.json', 'r') as f:
                            products = json_lib.load(f)
                        with open('data/users.json', 'r') as f:
                            users = json_lib.load(f)
                        
                        product = next((p for p in products if p['id'] == product_id), None)
                        user_balance = users.get(user_id, {}).get('balance', 0)
                        
                        if not product:
                            response_text = "❌ Product not found. Use /start to browse products."
                        elif quantity <= 0:
                            response_text = "❌ Quantity must be greater than 0"
                        elif product['stock'] < quantity:
                            response_text = f"❌ Not enough stock!\n\n📦 Available: {product['stock']}\n🔢 Requested: {quantity}\n\nPlease choose a smaller quantity."
                        else:
                            total_cost = product['price'] * quantity
                            
                            if user_balance < total_cost:
                                response_text = f"""❌ Insufficient Balance

💰 Your Balance: ₱{user_balance}
💸 Required: ₱{total_cost}
📦 Product: {product['name']} × {quantity}
💔 Short: ₱{total_cost - user_balance}

Please deposit more funds to complete this purchase."""
                            else:
                                # Process the custom quantity purchase immediately
                                # Update user balance
                                if user_id not in users:
                                    users[user_id] = {"balance": 0, "total_spent": 0}
                                users[user_id]["balance"] = user_balance - total_cost
                                users[user_id]["total_spent"] = users[user_id].get("total_spent", 0) + total_cost
                                
                                # Update product stock
                                for p in products:
                                    if p['id'] == product_id:
                                        p['stock'] -= quantity
                                        break
                                
                                # Save updates
                                with open('data/users.json', 'w') as f:
                                    json_lib.dump(users, f, indent=2)
                                with open('data/products.json', 'w') as f:
                                    json_lib.dump(products, f, indent=2)
                                
                                response_text = f"""✅ Purchase Successful!

🛍️ Product: {product['name']}
📦 Quantity: {quantity}x
💰 Total Paid: ₱{total_cost}
💳 Remaining Balance: ₱{users[user_id]['balance']}

📋 Your accounts will be sent shortly!

Thank you for shopping with us! 🎉"""
                                
                                # Send accounts instantly (reusing existing logic)
                                try:
                                    with open('data/product_files.json', 'r') as f:
                                        product_files = json_lib.load(f)
                                    
                                    if str(product_id) in product_files:
                                        available_files = [f for f in product_files[str(product_id)] if f['status'] == 'available']
                                        
                                        if available_files and len(available_files) >= quantity:
                                            # Send accounts for custom quantity
                                            for i in range(quantity):
                                                file_data = available_files[i]
                                                file_data['status'] = 'sold'
                                                file_data['sold_to'] = user_id
                                                file_data['sold_at'] = datetime.now().isoformat()
                                                
                                                account_message = f"""📦 Your {product['name']} Account #{i+1}

🔐 Login Credentials:
📧 Email: {file_data['details']['email']}
🔑 Password: {file_data['details']['password']}
💎 Subscription: {file_data['details'].get('subscription', 'Premium Access')}

📋 Instructions:
{file_data['details'].get('instructions', 'Login with these credentials')}

🛡️ WARRANTY ACTIVATION:
Vouch @tiramisucakekyo within 24 hours to activate warranty.
DM him with the vouch!

⚠️ Important: Keep these credentials safe!"""
                                                
                                                # Send account details to customer
                                                account_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                                                account_data = json_lib.dumps({
                                                    "chat_id": user_id,
                                                    "text": account_message
                                                }).encode('utf-8')
                                                account_req = urllib.request.Request(account_url, data=account_data, headers={'Content-Type': 'application/json'})
                                                urllib.request.urlopen(account_req)
                                            
                                            # Save updated product files
                                            with open('data/product_files.json', 'w') as f:
                                                json_lib.dump(product_files, f, indent=2)
                                except:
                                    pass
                                
                    except Exception as e:
                        response_text = f"❌ Error processing order: {str(e)}"

# REMOVED DUPLICATE /addacc HANDLER - MOVED TO PROPER POSITION

                elif ((':' in text or '|' in text) and '@' in text and not text.startswith('/')):
                    # Handle account additions in email:password or email|password format
                    if '|' in text:
                        parts = text.split('|')
                    else:
                        parts = text.split(':')
                        
                    if len(parts) >= 2:
                        email = parts[0].strip()
                        if '|' in text:
                            password = '|'.join(parts[1:]).strip()
                        else:
                            password = ':'.join(parts[1:]).strip()
                        
                        try:
                            # Load or create product files (default to product ID 1 - capcut)
                            try:
                                with open('data/product_files.json', 'r') as f:
                                    product_files = json_lib.load(f)
                            except:
                                product_files = {}
                            
                            product_id = "1"  # Default to capcut
                            if product_id not in product_files:
                                product_files[product_id] = []
                            
                            # Check for duplicate email before adding
                            email_exists = False
                            existing_product = ""
                            
                            for pid, accounts in product_files.items():
                                for account in accounts:
                                    if account.get('details', {}).get('email', '').lower() == email.lower():
                                        email_exists = True
                                        existing_product = f"Product ID {pid}"
                                        break
                                if email_exists:
                                    break
                            
                            if email_exists:
                                response_text = f"""❌ **DUPLICATE EMAIL DETECTED!**

🚫 **Email:** {email}
📦 **Already exists in:** {existing_product}

💡 **Tip:** Use a unique email address that hasn't been added before."""
                            else:
                                # Add new account
                                new_account = {
                                    "id": len(product_files[product_id]) + 1,
                                    "type": "account",
                                    "details": {
                                        "email": email,
                                        "password": password,
                                        "subscription": "CapCut Pro - 1 Month",
                                        "instructions": "Login with these credentials. Do not change password for 24 hours."
                                    },
                                    "status": "available",
                                    "added_at": datetime.now().isoformat()
                                }
                                
                                product_files[product_id].append(new_account)
                            
                            # Save updated files
                            with open('data/product_files.json', 'w') as f:
                                json_lib.dump(product_files, f, indent=2)
                            
                            # AUTOMATICALLY UPDATE PRODUCT STOCK TO MATCH ACCOUNT COUNT
                            available_accounts = [acc for acc in product_files[product_id] if acc['status'] == 'available']
                            total_available = len(available_accounts)
                            
                            # Update capcut product stock
                            try:
                                with open('data/products.json', 'r') as f:
                                    products = json_lib.load(f)
                                
                                for product in products:
                                    if product['id'] == 1:  # capcut
                                        product['stock'] = total_available
                                        break
                                
                                with open('data/products.json', 'w') as f:
                                    json_lib.dump(products, f, indent=2)
                                    
                            except:
                                pass
                            
                            response_text = f"""✅ Account Added to CapCut!

📧 Email: {email}
🔑 Password: {password}
📊 Available Accounts: {total_available}
📦 Product Stock Updated: {total_available}

Send more accounts to automatically increase stock!"""
                            
                        except Exception as e:
                            response_text = f"❌ Error adding account: {str(e)}"
                    else:
                        response_text = "❌ Invalid format. Use: email@example.com:password123 OR email@example.com|password123"

                else:
                    response_text = f"""👋 **Welcome Back, Admin!**

🔑 **Admin Access Confirmed**
🆔 **Your ID:** {user_id}

**Quick Actions:**
➕ Add Product: `/addproduct`  
📦 View Products: `/products`
📊 Statistics: `/stats`
🔧 Full Panel: `/admin`

**Add Product Format:**
`/addproduct Name|Category|Price|Stock|Description|Emoji`

**Example:**
`/addproduct Netflix Premium|streaming|149|50|1 Month Netflix|📺`

Ready to manage your store!"""

            else:
                # Load users data for all regular user interactions
                try:
                    with open('data/users.json', 'r') as f:
                        users = json_lib.load(f)
                except:
                    users = {}
                
                # Handle photo messages (receipts) from regular users
                if 'photo' in message:
                    # Customer sent a receipt photo
                    photo = message['photo'][-1]  # Get highest resolution
                    caption = message.get('caption', '').strip()
                    
                    # Save receipt for admin approval
                    receipt_data = {
                        "user_id": user_id,
                        "chat_id": chat_id,
                        "photo_file_id": photo['file_id'],
                        "caption": caption,
                        "timestamp": datetime.now().isoformat(),
                        "status": "pending",
                        "username": message['from'].get('username', 'No username'),
                        "first_name": message['from'].get('first_name', 'Unknown')
                    }
                    
                    # Load existing receipts
                    receipts = []
                    try:
                        with open('data/pending_receipts.json', 'r') as f:
                            receipts = json_lib.load(f)
                    except:
                        receipts = []
                    
                    # Add new receipt
                    receipt_id = len(receipts) + 1
                    receipt_data["receipt_id"] = receipt_id
                    receipts.append(receipt_data)
                    
                    # Save receipts
                    with open('data/pending_receipts.json', 'w') as f:
                        json_lib.dump(receipts, f, indent=2)
                    
                    # Notify admin
                    admin_id = "7240133914"  # Your admin ID
                    admin_message = f"📸 New Receipt #{receipt_id}\n\n👤 User: @{receipt_data['username']} ({receipt_data['first_name']})\n💬 Caption: {caption}\n🆔 User ID: {user_id}\n\nClick buttons below to approve or reject:"
                    
                    # Send photo notification to admin with approve/reject buttons
                    admin_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
                    
                    # Create approve/reject buttons
                    admin_keyboard = {
                        "inline_keyboard": [
                            [
                                {"text": "✅ Approve", "callback_data": f"approve_receipt_{receipt_id}"},
                                {"text": "❌ Reject", "callback_data": f"reject_receipt_{receipt_id}"}
                            ],
                            [
                                {"text": "💬 Message User", "callback_data": f"msg_user_{user_id}"}
                            ]
                        ]
                    }
                    
                    admin_data = json_lib.dumps({
                        "chat_id": admin_id,
                        "photo": photo['file_id'],
                        "caption": admin_message,
                        "reply_markup": admin_keyboard
                    }).encode('utf-8')
                    
                    admin_req = urllib.request.Request(admin_url, data=admin_data, headers={'Content-Type': 'application/json'})
                    try:
                        urllib.request.urlopen(admin_req)
                        logger.info(f"Sent receipt photo with buttons to admin")
                        
                    except Exception as e:
                        logger.error(f"Failed to notify admin: {e}")
                    
                    # Send confirmation message to customer
                    try:
                        confirmation_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                        confirmation_data = json_lib.dumps({
                            'chat_id': user_id,
                            'text': "✅ Receipt received! Your funds will be added within 5 minutes. If not, contact @tiramisucakekyo",
                            'parse_mode': 'HTML'
                        }).encode('utf-8')
                        
                        confirmation_req = urllib.request.Request(confirmation_url, data=confirmation_data, headers={'Content-Type': 'application/json'})
                        urllib.request.urlopen(confirmation_req)
                        logger.info(f"Sent receipt confirmation to user {user_id}")
                        
                    except Exception as e:
                        logger.error(f"Failed to send confirmation: {e}")
                    return jsonify({'status': 'ok'})

                # Professional Store Bot Interface with Inline Keyboards
                # Get user data
                user_balance = 0.0
                product_count = 0
                try:
                    with open('data/products.json', 'r') as f:
                        products = json_lib.load(f)
                        product_count = len(products)
                except:
                    product_count = 0

                # Handle custom keyboard button presses (from primostorebot-style interface)
                if text == "💰 Deposit Balance":
                    response_text = "💳 Deposit Funds\n\n📋 Steps to Deposit:\n1. Send to GCash: 09911127180\n2. Screenshot your receipt\n3. Send receipt photo here\n4. Wait for admin approval\n5. Get balance credit instantly after approval\n\n⚠️ Important: Send receipt as photo to this bot\n📞 Contact: 09911127180 mb"
                    
                elif text == "🛒 Browse Products":
                    # Show products directly with stock counts
                    try:
                        with open('data/products.json', 'r') as f:
                            products = json_lib.load(f)
                        
                        if products:
                            response_text = "🛒 Available Products\n\nSelect a product to purchase:\n\n"
                            
                            # Generate inline keyboard for direct product selection
                            inline_keyboard = {"inline_keyboard": []}
                            
                            for product in products:
                                if product.get('stock', 0) > 0:  # Only show products with stock
                                    category_emoji = {
                                        'video': '🎬',
                                        'music': '🎵', 
                                        'streaming': '📺',
                                        'education': '📚'
                                    }.get(product.get('category', ''), '📦')
                                    
                                    button_text = f"{category_emoji} {product['name'].title()} - ₱{product['price']} (Stock: {product['stock']})"
                                    inline_keyboard["inline_keyboard"].append([{"text": button_text, "callback_data": f"product_{product['id']}"}])
                                    
                                    response_text += f"{category_emoji} {product['name'].title()}\n"
                                    response_text += f"💰 Price: ₱{product['price']}\n"
                                    response_text += f"📦 Stock: {product['stock']} available\n\n"
                            
                            if not inline_keyboard["inline_keyboard"]:
                                response_text = "📦 No Products Available\n\nAll products are out of stock. Check back later!"
                                inline_keyboard = {"inline_keyboard": [[{"text": "🔙 Back to Main Menu", "callback_data": "main_menu"}]]}
                            else:
                                inline_keyboard["inline_keyboard"].append([{"text": "🔙 Back to Main Menu", "callback_data": "main_menu"}])
                        else:
                            response_text = "📦 No Products Available\n\nProducts will appear here when admin adds them."
                            inline_keyboard = {"inline_keyboard": [[{"text": "🔙 Back to Main Menu", "callback_data": "main_menu"}]]}
                    except Exception as e:
                        response_text = f"❌ Error loading products: {str(e)}"
                        inline_keyboard = {"inline_keyboard": [[{"text": "🔙 Back to Main Menu", "callback_data": "main_menu"}]]}
                        
                elif text == "👑 Customer Service":
                    response_text = "🆘 Customer Support\n\n📞 Contact Information:\n💬 Telegram/WhatsApp: 09911127180\n📧 For Receipts: Send to 09911127180 mb\n👤 Support: @tiramisucakekyo\n\n⚡ We Help With:\n• Payment issues\n• Product questions\n• Account problems\n• Technical support\n• Order problems\n\n🕐 Available: 24/7\n⚡ Response: Usually within 5 minutes\n\nReady to help! Contact us now! 💪"
                    
                elif text == "❓ How to order":
                    response_text = "❓ How to Order\n\n📋 Simple Steps:\n1️⃣ Browse Products (🛒 button)\n2️⃣ Select what you want\n3️⃣ Add to cart\n4️⃣ Make sure you have balance\n5️⃣ Complete purchase\n6️⃣ Get your account instantly!\n\n💰 Need Balance?\n• Use 💰 Deposit Balance button\n• Send GCash receipt to 09911127180\n• Get approved and start shopping!\n\nReady to order! 🛍️"
                    
                # Handle user commands (available to all users)
                elif text.startswith('/leaderboard'):
                    # Show top users by spending (USER VERSION - no balance shown)
                    try:
                        with open('data/users.json', 'r') as f:
                            users_data = json_lib.load(f)
                    except:
                        users_data = {}
                    
                    if not users_data:
                        response_text = "📊 **Leaderboard**\n\nNo users found yet!"
                    else:
                        # Sort users by total spent (descending)
                        sorted_users = sorted(users_data.items(), key=lambda x: x[1].get('total_spent', 0), reverse=True)
                        
                        response_text = "🏆 **Top Spenders Leaderboard**\n\n"
                        
                        for i, (user_id_key, user_info) in enumerate(sorted_users[:10], 1):
                            total_spent = user_info.get('total_spent', 0)
                            
                            # Get user info - try multiple sources
                            username = "Unknown User"
                            try:
                                # First try to get from stored user data
                                if 'username' in user_info:
                                    username = f"@{user_info['username']}"
                                elif 'first_name' in user_info:
                                    username = user_info['first_name']
                                else:
                                    # Last resort: try Telegram API
                                    user_chat = application.bot.get_chat(user_id_key)
                                    username = f"@{user_chat.username}" if user_chat.username else user_chat.first_name or f"User{user_id_key[-4:]}"
                            except:
                                username = f"User{user_id_key[-4:]}"
                            
                            # Add medal emojis for top 3
                            if i == 1:
                                medal = "🥇"
                            elif i == 2:
                                medal = "🥈"
                            elif i == 3:
                                medal = "🥉"
                            else:
                                medal = f"{i}."
                            
                            response_text += f"{medal} **{username}**\n"
                            response_text += f"💸 Total Spent: ₱{total_spent}\n\n"
                        
                        if len(sorted_users) > 10:
                            response_text += f"... and {len(sorted_users) - 10} more users"

                elif text.startswith('/stock'):
                    # Show current stock levels (USER VERSION - simplified)
                    try:
                        with open('data/products.json', 'r') as f:
                            products = json_lib.load(f)
                    except:
                        products = []
                    
                    if not products:
                        response_text = "📦 Stock Status\n\nNo products found!"
                    else:
                        response_text = "📦 Available Products:\n\n"
                        
                        # Group products by status to keep message short
                        in_stock = []
                        low_stock = []
                        out_of_stock = []
                        
                        for product in products:
                            name = product.get('name', 'Unknown')
                            stock = product.get('stock', 0)
                            price = product.get('price', 0)
                            
                            item = f"{name} (₱{price}) - {stock} left"
                            
                            if stock == 0:
                                out_of_stock.append(item)
                            elif stock <= 5:
                                low_stock.append(item)
                            else:
                                in_stock.append(item)
                        
                        # Build compact response
                        if in_stock:
                            response_text += "✅ IN STOCK:\n"
                            response_text += "\n".join([f"• {item}" for item in in_stock[:8]]) + "\n\n"  # Limit to 8 items
                        
                        if low_stock:
                            response_text += "⚠️ LOW STOCK:\n"
                            response_text += "\n".join([f"• {item}" for item in low_stock[:5]]) + "\n\n"  # Limit to 5 items
                        
                        if out_of_stock:
                            response_text += "❌ OUT OF STOCK:\n"
                            response_text += "\n".join([f"• {item}" for item in out_of_stock[:5]]) + "\n\n"  # Limit to 5 items

                # Handle /start command with inline keyboard ONLY if no photo was sent
                elif (text == '/start' or text == '/menu' or (not text.startswith('/') and not message.get('photo'))):
                    # Don't send welcome if photo was already processed
                    if 'photo' in message:
                        return jsonify({'status': 'ok'})
                    
                    # Users data already loaded above
                        
                    # EXACT primostorebot interface
                    current_time = datetime.now().strftime("%d/%m/%Y - %I:%M:%S %p")
                    first_name = message['from'].get('first_name', 'User')
                    username = first_name if first_name else "User"
                    
                    # Calculate bot statistics 
                    total_users = len(users) if users else 1
                    
                    # Count total accounts sold across all products
                    products_sold = 0
                    try:
                        with open('data/product_files.json', 'r') as f:
                            product_files = json_lib.load(f)
                        for product_id, accounts in product_files.items():
                            products_sold += len([acc for acc in accounts if acc.get('status') == 'sold'])
                    except:
                        products_sold = 0
                    
                    # Load actual user spending data AND BALANCE
                    try:
                        with open('data/users.json', 'r') as f:
                            users = json_lib.load(f)
                        user_data = users.get(str(user_id), {})
                        user_balance = user_data.get('balance', 0)  # LOAD FRESH BALANCE
                        total_spent = user_data.get('total_spent', 0)
                    except:
                        user_balance = 0
                        total_spent = 0
                    
                    response_text = f"""👋 — Hello @{username}
{current_time}

User Details :
└ ID : {user_id}
└ Name : {username}
└ Balance : ₱{user_balance}
└ Total Spent : ₱{total_spent:.2f}

BOT Statistics :
└ Products Sold : {products_sold} Accounts
└ Total Users : {total_users}

SHORTCUT :
/start - Show main menu
/stock - Check available stocks
/bonus - Claim your daily bonus
/leaderboard - View top users"""
                    
                    # EXACT primostorebot keyboard layout with custom buttons  
                    inline_keyboard = {
                        "inline_keyboard": [
                            [
                                {"text": "APPS STREAMING", "callback_data": "category_streaming"},
                                {"text": "EDITING PREMI..", "callback_data": "category_video"}
                            ],
                            [
                                {"text": "Other Categories", "callback_data": "browse_products"}
                            ]
                        ]
                    }
                    
                    # Custom keyboard (the bottom buttons like primostorebot)
                    keyboard = {
                        "keyboard": [
                            [
                                {"text": "💰 Deposit Balance"},
                                {"text": "🛒 Browse Products"}
                            ],
                            [
                                {"text": "👑 Customer Service"}
                            ],
                            [
                                {"text": "❓ How to order"}
                            ]
                        ],
                        "resize_keyboard": True,
                        "one_time_keyboard": False
                    }
                    
                    # Send message with BOTH inline and custom keyboard like primostorebot
                    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    data = json_lib.dumps({
                        "chat_id": chat_id,
                        "text": response_text,
                        "reply_markup": keyboard  # Use custom keyboard for bottom buttons
                    }).encode('utf-8')
                    
                    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
                    try:
                        with urllib.request.urlopen(req) as response:
                            logger.info(f"Sent inline menu to chat {chat_id}")
                        return jsonify({'status': 'ok'})
                    except Exception as e:
                        logger.error(f"Failed to send inline menu: {e}")
                
                # Handle old text commands for compatibility
                elif text == '/products':
                    response_text = """🏪 **Product Catalog**

Use the main menu button for better experience!
Type /start to see the interactive menu.

📱 **Quick Commands:**
• /start - Interactive menu
• /balance - Check balance
• /deposit - Add funds"""
                
                elif text == '/help':
                    response_text = f"""💡 Customer Help

👋 Welcome to Premium Store!

🛍️ Shopping Commands:
/start - Main menu with buttons
/products - Browse products
/balance - Check your balance
/deposit - Add funds to account

💳 Payment Methods:
📱 GCash: 09911127180
💰 Send receipt photo for approval

📞 Support:
Contact: 09911127180 mb

💡 How to Shop:
1. Add funds via GCash
2. Send receipt photo (silent approval)
3. Browse products with /start
4. Buy with quantity selection!"""

                elif text == '/balance':
                    response_text = f"""💰 **Account Balance**

**Current Balance:** ₱{user_balance:.2f}
**Status:** Active

📱 **Use /start for interactive menu**
💳 **Use /deposit to add funds**"""
                
                elif text == '/deposit':
                    response_text = """💳 **Deposit Funds**

📱 **For better experience, use /start**

**Payment Methods:**
🟢 **GCash:** 09911127180
🔵 **PayMaya:** 09911127180

**Steps:**
1. Send payment
2. Screenshot receipt
3. Send to: 09911127180 mb
4. Wait for confirmation

⚠️ **No receipt = No processing**"""
                
                else:
                    # Redirect to main menu
                    response_text = """👋 **Welcome to Premium Store!**

📱 **Use /start for interactive menu**

**Quick Commands:**
• /start - Main menu
• /products - Browse
• /balance - Check funds
• /deposit - Add money

Ready to shop! 🛍️"""

            # Send message using urllib
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            # For admin commands, don't use markdown to avoid 400 errors
            if is_admin and text.startswith('/admin'):
                data = json_lib.dumps({
                    "chat_id": chat_id, 
                    "text": response_text
                }).encode('utf-8')
            else:
                # Check if we have inline keyboard to send (for custom button responses)
                if 'inline_keyboard' in locals() and inline_keyboard:
                    data = json_lib.dumps({
                        "chat_id": chat_id, 
                        "text": response_text,
                        "parse_mode": "Markdown",
                        "reply_markup": inline_keyboard
                    }).encode('utf-8')
                else:
                    data = json_lib.dumps({
                        "chat_id": chat_id, 
                        "text": response_text,
                        "parse_mode": "Markdown"
                    }).encode('utf-8')
            
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(req) as response:
                    logger.info(f"Sent {'admin' if is_admin else 'user'} message to chat {chat_id}")
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
        
        return jsonify({'status': 'ok'})
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy' if premium_bot else 'error',
        'bot': 'Premium Store Bot',
        'version': '2.0',
        'initialized': premium_bot is not None
    })

# Set webhook on startup
if premium_bot:
    try:
        webhook_domain = os.environ.get('REPLIT_DEV_DOMAIN')
        if webhook_domain:
            webhook_url = f"https://{{webhook_domain}}/webhook"
            # Note: Webhook will be set via bot commands or admin panel
            logger.info(f"Webhook URL would be: {{webhook_url}}")
    except Exception as e:
        logger.error(f"Webhook setup error: {{e}}")

if __name__ == '__main__':
    logger.info("🚀 Starting Premium Store Bot Flask App")
    app.run(host='0.0.0.0', port=5000, debug=False)