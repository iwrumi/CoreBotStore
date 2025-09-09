# Premium Store Bot Configuration Guide

## 🚀 Quick Setup Steps

### 1. Get Your Telegram ID
Send `/start` to @userinfobot on Telegram to get your ID, then:

```bash
python admin_config.py
```
Choose option 1 to create initial config, then edit `config/admin_settings.json`:
```json
{
  "admin_users": ["YOUR_TELEGRAM_ID_HERE"]
}
```

### 2. Configure Payment Methods
Edit `config/payment_methods.json` with your payment details:

```json
{
  "gcash": {
    "name": "GCash",
    "number": "09123456789", 
    "qr_code_url": "https://your-qr-image.com/gcash.png"
  }
}
```

### 3. Add Your Products
Edit `config/sample_products.json` or run:
```bash
python admin_config.py
```
Choose option 4 to add products.

### 4. Upload QR Code Images
- Upload your payment QR codes to an image hosting service
- Update the `qr_code_url` in payment methods

## 📝 Bot Commands

**User Commands:**
- `/start` - Welcome message
- `/balance` - Check balance
- `/deposit` - Add balance
- `/products` - Browse store

**Admin Commands (add to bot later):**
- `/admin` - Admin panel
- `/stats` - View statistics
- `/broadcast` - Send message to all users

## 🔧 Advanced Configuration

### Custom Categories
Add new categories in `config/categories.json`:
```json
{
  "id": "education",
  "name": "📚 Education", 
  "emoji": "📚",
  "description": "Online courses and certifications"
}
```

### Product Variants
Each product can have multiple variants (durations, types):
```json
{
  "variants": [
    {
      "id": 1,
      "name": "1 Month",
      "price": 150.0,
      "stock": 25
    },
    {
      "id": 2,
      "name": "3 Months", 
      "price": 400.0,
      "stock": 15
    }
  ]
}
```

### Auto-Reply Messages
Customize messages in `config/admin_settings.json`:
```json
{
  "welcome_message": "Your custom welcome message",
  "support_username": "@YourSupport",
  "min_deposit": 20.0,
  "max_deposit": 10000.0
}
```

## 🎯 Next Steps

1. **Test the bot**: Send messages and check responses
2. **Add products**: Use the admin config tool
3. **Upload payment QRs**: Host your QR code images
4. **Set admin ID**: Add your Telegram ID to admin list
5. **Customize messages**: Edit welcome and support messages

Your bot is now ready to serve customers! 🎉