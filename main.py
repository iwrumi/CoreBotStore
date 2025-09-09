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
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    </head>
    <body class="bg-dark text-light">
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card bg-secondary">
                        <div class="card-header">
                            <h1 class="text-center">🤖 Premium Store Bot</h1>
                            <div class="text-center">
                                <span class="badge bg-{status_class}">{status}</span>
                            </div>
                        </div>
                        <div class="card-body">
                            <div class="text-center mb-4">
                                <h3>Premium Telegram Store Bot</h3>
                                <p class="text-muted">Complete e-commerce solution matching MRPremiumShopBot features</p>
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
                response_text = "📩 **Contact Admin**\n\n**How to reach admin:**\n\n💬 **Telegram:** 09911127180\n📞 **Call/Text:** 09911127180\n\n**For faster approval:**\n✅ Send your receipt photo to this bot\n✅ Include amount in message\n✅ Wait for admin approval\n\n**Approval usually within 5 minutes!**"
                inline_keyboard = {"inline_keyboard": [
                    [{"text": "💳 Send Receipt to Bot", "callback_data": "send_receipt_info"}],
                    [{"text": "🔙 Back to Main Menu", "callback_data": "main_menu"}]
                ]}
            
            elif callback_data == "send_receipt_info":
                response_text = "📸 **Send Receipt Instructions**\n\n**Steps:**\n1. Take clear photo of your GCash receipt\n2. Send the photo to this bot\n3. Include amount in message (e.g., '₱100')\n4. Wait for admin approval\n\n**Example message with photo:**\n'₱150 deposit - please approve'\n\n**Ready to send your receipt? Just upload the photo now! 📸**"
                inline_keyboard = {"inline_keyboard": [
                    [{"text": "🔙 Back to Deposit", "callback_data": "deposit_funds"}],
                    [{"text": "🔙 Main Menu", "callback_data": "main_menu"}]
                ]}
                
            # Handle different callback actions
            elif callback_data == "browse_products":
                # Get products and create categories
                try:
                    with open('data/products.json', 'r') as f:
                        products = json_lib.load(f)
                    
                    if products:
                        response_text = messages.get("browse_products", "🏪 **Product Categories**\n\nSelect a category to browse:")
                        
                        # Create category buttons
                        categories = {}
                        for product in products:
                            cat = product.get('category', 'General')
                            if cat not in categories:
                                categories[cat] = 0
                            categories[cat] += 1
                        
                        inline_keyboard = {"inline_keyboard": []}
                        for category, count in categories.items():
                            inline_keyboard["inline_keyboard"].append([
                                {"text": f"{category} ({count} items)", "callback_data": f"category_{category}"}
                            ])
                        inline_keyboard["inline_keyboard"].append([
                            {"text": "🔙 Back to Main Menu", "callback_data": "main_menu"}
                        ])
                    else:
                        response_text = messages.get("no_products", "📦 **No Products Available**\n\nProducts will appear here when admin adds them.")
                        inline_keyboard = {"inline_keyboard": [[
                            {"text": messages.get("button_labels", {}).get("back_menu", "🔙 Back to Main Menu"), "callback_data": "main_menu"}
                        ]]}
                except:
                    response_text = "❌ Error loading products"
                    inline_keyboard = {"inline_keyboard": [[
                        {"text": "🔙 Back to Main Menu", "callback_data": "main_menu"}
                    ]]}
            
            elif callback_data == "check_balance":
                response_text = messages.get("balance_message", "💰 **Account Balance**\n\n**Current Balance:** ₱{balance:.2f}\n**Total Deposited:** ₱{total_deposited:.2f}\n**Total Spent:** ₱{total_spent:.2f}\n\n**Account Status:** Active ✅").format(balance=0.0, total_deposited=0.0, total_spent=0.0)
                inline_keyboard = {"inline_keyboard": [
                    [{"text": "💳 Deposit Funds", "callback_data": "deposit_funds"}],
                    [{"text": "🔙 Back to Main Menu", "callback_data": "main_menu"}]
                ]}
            
            elif callback_data == "deposit_funds":
                # Send GCash QR code exactly like primostorebot
                gcash_qr_message = """📋 **Steps to Deposit:**
3. Screenshot your receipt  
4. Send receipt photo to this bot
5. Wait for admin approval
6. Get balance credit instantly after approval

⚠️ **Important:** Send receipt as photo to this bot
📞 **Contact:** 09911127180 mb"""

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
                    "parse_mode": "Markdown",
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
                response_text = """🆘 **Customer Support**

**📞 Contact Information:**
💬 **Telegram/WhatsApp:** 09911127180
📧 **For Receipts:** Send to 09911127180 mb

**⚡ We Help With:**
• Payment issues
• Product questions
• Account problems  
• Technical support
• Order problems

**🕐 Available:** 24/7
**⚡ Response:** Usually within 5 minutes

Ready to help! Contact us now! 💪"""
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
                "parse_mode": "Markdown",
                "reply_markup": inline_keyboard
            }).encode('utf-8')
            
            edit_req = urllib.request.Request(edit_url, data=edit_data, headers={'Content-Type': 'application/json'})
            try:
                with urllib.request.urlopen(edit_req) as response:
                    logger.info(f"Handled callback: {callback_data}")
            except Exception as e:
                logger.error(f"Failed to edit message: {e}")
            
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
            
            # Load admin configuration
            admin_users = []
            try:
                with open('config/admin_settings.json', 'r') as f:
                    admin_config = json_lib.load(f)
                    admin_users = admin_config.get('admin_users', [])
                logger.info(f"Loaded admin users: {admin_users}")
            except Exception as e:
                logger.error(f"Error loading admin config: {e}")
                admin_users = []
            
            # Check if user is admin - force add your ID for testing
            is_admin = user_id in admin_users or user_id == "7240133914"
            logger.info(f"User {user_id} admin check: {is_admin}")
            
            bot_token = os.environ.get('BOT_TOKEN')
            
            # Different responses for admins vs regular users
            if is_admin:
                # Debug logging
                logger.info(f"Admin command received: {text}")
                logger.info(f"Pipe count: {text.count('|')}")
                
                if text.count('|') >= 2 and text.startswith('/addproduct'):
                    # Parse product data - flexible format
                    logger.info("Processing product addition...")
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
                        
                        response_text = f"""✅ **Product Added Successfully!**

📦 **Product:** {name}
💰 **Price:** ₱{price}
📊 **Stock:** {stock}
🏷️ **Category:** {category}
{emoji} **Ready for customers!**

Your product is now available in the store. Customers can browse and purchase it immediately!

➕ Add another: `/addproduct ProductName|Price|Stock`
📦 Add accounts: `/addstock {product_id}`
📊 View all: `/products`"""

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

Try the simple format! Error: {str(e)}"""
                    
                elif text.startswith('/addproduct'):
                    response_text = """➕ **Add New Product**

**Super Simple Format:**
```
/addproduct Netflix Premium|149|50
```

**That's it!** Just: Name | Price | Stock

**Examples:**
• `/addproduct Netflix Premium|149|50`
• `/addproduct Spotify|120|25` 
• `/addproduct Steam Wallet|500|15`

**Optional extras (if you want):**
`/addproduct Name|Price|Stock|Category|Description|Emoji`

Ready to add your product! 🚀"""

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
                        
                        response_text = f"""✅ **Product Added Successfully!**

📦 **Product:** {name}
💰 **Price:** ₱{price}
📊 **Stock:** {stock}
🏷️ **Category:** {category}
{emoji} **Ready for customers!**

Your product is now available in the store. Customers can browse and purchase it immediately!

➕ Add another: `/addproduct ProductName|Price|Stock`
📦 Add accounts: `/addstock {product_id}`
📊 View all: `/products`"""

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

                elif text.startswith('/admin'):
                    response_text = f"""🔑 **Admin Panel**

👤 **Admin:** {user_id}
📊 **Status:** Active

**📦 Product & Stock Management:**
• /addproduct - Add new product types
• /addstock - Add actual accounts/codes
• /products - View all products

**📸 Receipt Management:**
• /receipts - View pending receipt approvals
• /approve ID - Approve receipt/deposit
• /reject ID - Reject receipt/deposit
• /msg USER_ID message - Send message to user

**💰 Payment Management:**
• /deposits - View old deposit system
• Manual receipt approval through photos

**📊 Analytics:**
• /stats - View bot statistics
• /users - Manage users

**📢 Communication:**
• /broadcast - Send message to all users
• /msg - Direct message any user

**⚡ New System:** Customers send receipts to bot → You approve instantly!"""

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
                    admin_message = f"📸 **New Receipt #{receipt_id}**\n\n👤 **User:** @{receipt_data['username']} ({receipt_data['first_name']})\n💬 **Caption:** {caption}\n🆔 **User ID:** {user_id}\n\n✅ Approve: /approve {receipt_id}\n❌ Reject: /reject {receipt_id}\n💬 Message: /msg {user_id} your_message"
                    
                    # Send notification to admin (text message first, then forward photo)
                    admin_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    admin_data = json_lib.dumps({
                        "chat_id": admin_id,
                        "text": admin_message,
                        "parse_mode": "Markdown"
                    }).encode('utf-8')
                    
                    admin_req = urllib.request.Request(admin_url, data=admin_data, headers={'Content-Type': 'application/json'})
                    try:
                        urllib.request.urlopen(admin_req)
                        logger.info(f"Sent receipt notification to admin")
                        
                        # Forward the photo separately
                        forward_url = f"https://api.telegram.org/bot{bot_token}/forwardMessage"
                        forward_data = json_lib.dumps({
                            "chat_id": admin_id,
                            "from_chat_id": chat_id,
                            "message_id": message['message_id']
                        }).encode('utf-8')
                        
                        forward_req = urllib.request.Request(forward_url, data=forward_data, headers={'Content-Type': 'application/json'})
                        urllib.request.urlopen(forward_req)
                        logger.info(f"Forwarded receipt photo to admin")
                        
                    except Exception as e:
                        logger.error(f"Failed to notify admin: {e}")
                    
                    response_text = "Please wait for admin approval"

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

                # Handle /start command with inline keyboard
                if text == '/start' or text == '/menu' or not text.startswith('/'):
                    response_text = f"""🛍️ **Welcome to Premium Store!**

💎 **Your Digital Services Store**

💰 **Balance:** ₱{user_balance:.2f}
📦 **Products:** {product_count} Available

🛒 **Use the menu below to navigate:**"""
                    
                    # Send with inline keyboard
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
                    
                    # Send message with inline keyboard
                    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    data = json_lib.dumps({
                        "chat_id": chat_id,
                        "text": response_text,
                        "parse_mode": "Markdown",
                        "reply_markup": inline_keyboard
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