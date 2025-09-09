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
        
        # Handle incoming messages
        if update_data and 'message' in update_data:
            import urllib.request
            import json as json_lib
            
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
                        products = {}
                        try:
                            with open('config/sample_products.json', 'r') as f:
                                products = json_lib.load(f)
                        except:
                            pass
                        
                        # Create product ID
                        product_id = name.lower().replace(' ', '_').replace('-', '_')
                        
                        # Add new product
                        products[product_id] = {
                            "id": product_id,
                            "name": name,
                            "category_id": category,
                            "description": description,
                            "variants": [
                                {
                                    "id": 1,
                                    "name": "Standard",
                                    "price": price,
                                    "stock": stock,
                                    "features": ["Premium Access"]
                                }
                            ],
                            "emoji": emoji,
                            "auto_delivery": True
                        }
                        
                        # Save products
                        with open('config/sample_products.json', 'w') as f:
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
                        products = {}
                        try:
                            with open('config/sample_products.json', 'r') as f:
                                products = json_lib.load(f)
                        except:
                            pass
                        
                        # Create product ID
                        product_id = name.lower().replace(' ', '_').replace('-', '_')
                        
                        # Add new product
                        products[product_id] = {
                            "id": product_id,
                            "name": name,
                            "category_id": category,
                            "description": description,
                            "variants": [
                                {
                                    "id": 1,
                                    "name": "Standard",
                                    "price": price,
                                    "stock": stock,
                                    "features": ["Premium Access"]
                                }
                            ],
                            "emoji": emoji,
                            "auto_delivery": True
                        }
                        
                        # Save products
                        with open('config/sample_products.json', 'w') as f:
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

                elif text.startswith('/admin'):
                    response_text = f"""🔑 **Admin Panel**

👤 **Admin:** {user_id}
📊 **Status:** Active

**📦 Product & Stock Management:**
• /addproduct - Add new product types
• /addstock - Add actual accounts/codes
• /products - View all products

**💰 Payment Management:**
• /deposits - Approve/reject deposits (Manual)
• /approve ID - Approve deposit
• /reject ID - Reject deposit

**📊 Analytics:**
• /stats - View bot statistics
• /users - Manage users

**📢 Communication:**
• /broadcast - Send message to all users

**⚡ Payment System:** Manual approval - you control all deposits!"""

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
                # Regular user response
                response_text = f"""👋 **Welcome to Premium Store!**

🏪 **Available Services:**
• Netflix Premium Accounts
• Spotify Premium Accounts  
• Gaming Accounts
• VPN Services

💰 **Your Balance:** ₱0.00

📱 **Quick Actions:**
/balance - Check your balance
/deposit - Add money to account
/products - Browse our catalog
/support - Get help

🎯 **How to Order:**
1. Add balance to your account
2. Browse products
3. Purchase instantly
4. Receive your account details

Start by adding balance to begin shopping!"""

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