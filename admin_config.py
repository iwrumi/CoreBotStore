"""
Admin Configuration System
Configure your Premium Store Bot settings
"""
import json
import os
from simple_data_manager import SimpleDataManager

class BotConfig:
    def __init__(self):
        self.data_manager = SimpleDataManager()
        self.setup_initial_config()
    
    def setup_initial_config(self):
        """Set up initial bot configuration"""
        
        # Admin settings
        admin_settings = {
            "admin_users": [
                "YOUR_TELEGRAM_ID_HERE"  # Replace with your Telegram ID
            ],
            "store_name": "Premium Store",
            "welcome_message": "👋 Welcome to Premium Store!\n\nYour one-stop shop for premium accounts and services.",
            "support_username": "@YourSupportBot",
            "min_deposit": 20.0,
            "max_deposit": 10000.0
        }
        
        # Payment methods with QR codes
        payment_methods = {
            "gcash": {
                "name": "GCash",
                "number": "09123456789",
                "qr_code_url": "https://your-domain.com/gcash-qr.png",
                "instructions": "Send payment to GCash number above and upload screenshot"
            },
            "paymaya": {
                "name": "PayMaya", 
                "number": "09987654321",
                "qr_code_url": "https://your-domain.com/paymaya-qr.png",
                "instructions": "Send payment to PayMaya number above and upload screenshot"
            },
            "bank": {
                "name": "Bank Transfer",
                "account_name": "Your Name",
                "account_number": "1234567890",
                "bank_name": "BPI",
                "instructions": "Transfer to bank account above and upload receipt"
            }
        }
        
        # Product categories
        categories = [
            {
                "id": "streaming",
                "name": "📺 Streaming Services",
                "emoji": "📺",
                "description": "Netflix, Spotify, Disney+, etc."
            },
            {
                "id": "gaming", 
                "name": "🎮 Gaming Accounts",
                "emoji": "🎮",
                "description": "Steam, Epic Games, console accounts"
            },
            {
                "id": "productivity",
                "name": "💼 Productivity Tools",
                "emoji": "💼", 
                "description": "Microsoft Office, Adobe, Canva Pro"
            },
            {
                "id": "vpn",
                "name": "🔒 VPN Services",
                "emoji": "🔒",
                "description": "Nord VPN, Express VPN, etc."
            }
        ]
        
        # Sample products
        products = {
            "netflix_1m": {
                "id": "netflix_1m",
                "name": "Netflix Premium",
                "category_id": "streaming",
                "description": "1 Month Netflix Premium Account",
                "variants": [
                    {
                        "id": 1,
                        "name": "1 Month",
                        "price": 150.0,
                        "stock": 25,
                        "features": ["4K Quality", "4 Screens", "Downloads"]
                    },
                    {
                        "id": 2, 
                        "name": "3 Months",
                        "price": 400.0,
                        "stock": 15,
                        "features": ["4K Quality", "4 Screens", "Downloads", "3 Month Warranty"]
                    }
                ],
                "emoji": "📺",
                "auto_delivery": True
            },
            "spotify_1m": {
                "id": "spotify_1m", 
                "name": "Spotify Premium",
                "category_id": "streaming",
                "description": "1 Month Spotify Premium",
                "variants": [
                    {
                        "id": 1,
                        "name": "Individual",
                        "price": 120.0,
                        "stock": 30,
                        "features": ["No Ads", "Download Music", "High Quality"]
                    },
                    {
                        "id": 2,
                        "name": "Family",
                        "price": 180.0,
                        "stock": 10, 
                        "features": ["6 Accounts", "No Ads", "Download Music"]
                    }
                ],
                "emoji": "🎵",
                "auto_delivery": True
            }
        }
        
        # Save configurations
        config_dir = "config"
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        configs = {
            "admin_settings.json": admin_settings,
            "payment_methods.json": payment_methods, 
            "categories.json": categories,
            "sample_products.json": products
        }
        
        for filename, config_data in configs.items():
            filepath = os.path.join(config_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(config_data, f, indent=2)
        
        print("✅ Initial configuration files created in 'config/' directory")
        print("\n📝 Next steps:")
        print("1. Edit config/admin_settings.json - Add your Telegram ID")
        print("2. Edit config/payment_methods.json - Add your payment details")
        print("3. Edit config/sample_products.json - Add your products")
        print("4. Upload your QR code images")

    def add_admin_user(self, telegram_id):
        """Add admin user"""
        config_file = "config/admin_settings.json"
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                settings = json.load(f)
            
            if telegram_id not in settings["admin_users"]:
                settings["admin_users"].append(str(telegram_id))
                
                with open(config_file, 'w') as f:
                    json.dump(settings, f, indent=2)
                
                print(f"✅ Added admin user: {telegram_id}")
            else:
                print(f"ℹ️ User {telegram_id} is already an admin")
        else:
            print("❌ Admin settings file not found")

    def update_payment_method(self, method_id, details):
        """Update payment method details"""
        config_file = "config/payment_methods.json"
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                methods = json.load(f)
            
            if method_id in methods:
                methods[method_id].update(details)
                
                with open(config_file, 'w') as f:
                    json.dump(methods, f, indent=2)
                
                print(f"✅ Updated payment method: {method_id}")
            else:
                print(f"❌ Payment method {method_id} not found")
        else:
            print("❌ Payment methods file not found")

    def add_product(self, product_data):
        """Add new product"""
        config_file = "config/sample_products.json"
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                products = json.load(f)
            
            products[product_data["id"]] = product_data
            
            with open(config_file, 'w') as f:
                json.dump(products, f, indent=2)
            
            print(f"✅ Added product: {product_data['name']}")
        else:
            print("❌ Products file not found")

if __name__ == "__main__":
    config = BotConfig()
    
    print("\n🤖 Premium Store Bot Configuration")
    print("=" * 50)
    
    choice = input("\nWhat would you like to do?\n1. Setup initial config\n2. Add admin user\n3. Update payment method\n4. Add product\n\nChoice (1-4): ")
    
    if choice == "1":
        config.setup_initial_config()
    
    elif choice == "2":
        telegram_id = input("Enter Telegram ID: ")
        config.add_admin_user(telegram_id)
    
    elif choice == "3":
        method_id = input("Payment method (gcash/paymaya/bank): ")
        print("Enter new details (press Enter to skip):")
        name = input("Name: ") or None
        number = input("Number/Account: ") or None
        qr_url = input("QR Code URL: ") or None
        
        details = {k: v for k, v in {
            "name": name, "number": number, "qr_code_url": qr_url
        }.items() if v}
        
        config.update_payment_method(method_id, details)
    
    elif choice == "4":
        print("Add new product:")
        product_id = input("Product ID: ")
        name = input("Product name: ")
        category = input("Category (streaming/gaming/productivity/vpn): ")
        price = float(input("Price: "))
        stock = int(input("Stock: "))
        
        product_data = {
            "id": product_id,
            "name": name,
            "category_id": category,
            "description": f"{name} - Premium account",
            "variants": [
                {
                    "id": 1,
                    "name": "Standard",
                    "price": price,
                    "stock": stock,
                    "features": ["Premium Access"]
                }
            ],
            "emoji": "⭐",
            "auto_delivery": True
        }
        
        config.add_product(product_data)