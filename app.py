import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.middleware.proxy_fix import ProxyFix
import threading
import time
from bot import TelegramStoreBot
from data_manager import DataManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize data manager
data_manager = DataManager()

# Initialize bot
bot_token = os.environ.get("BOT_TOKEN")
if not bot_token:
    logger.error("BOT_TOKEN environment variable not set!")
    bot = None
    bot_status = "Not configured"
else:
    try:
        bot = TelegramStoreBot(bot_token, data_manager)
        bot_status = "Running"
        logger.info("Bot initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize bot: {e}")
        bot = None
        bot_status = "Error"

@app.route('/')
def index():
    """Main page showing bot status and basic info"""
    return render_template('admin.html', 
                         products=data_manager.get_products(),
                         orders=data_manager.get_orders(),
                         bot_status=bot_status)

@app.route('/admin')
def admin():
    """Admin panel for managing products and orders"""
    return render_template('admin.html', 
                         products=data_manager.get_products(),
                         orders=data_manager.get_orders(),
                         bot_status=bot_status)

@app.route('/orders')
def orders():
    """View all orders"""
    return render_template('orders.html', orders=data_manager.get_orders())

@app.route('/api/products', methods=['GET', 'POST'])
def api_products():
    """API endpoint for products"""
    if request.method == 'GET':
        return jsonify(data_manager.get_products())
    
    elif request.method == 'POST':
        product_data = request.json
        if not product_data:
            return jsonify({'error': 'No data provided'}), 400
        
        required_fields = ['name', 'description', 'price', 'category']
        if not all(field in product_data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        product = data_manager.add_product(
            name=product_data['name'],
            description=product_data['description'],
            price=float(product_data['price']),
            category=product_data['category'],
            image_url=product_data.get('image_url', ''),
            stock=int(product_data.get('stock', 0))
        )
        return jsonify(product), 201

@app.route('/api/products/<int:product_id>', methods=['PUT', 'DELETE'])
def api_product_detail(product_id):
    """API endpoint for individual product operations"""
    if request.method == 'PUT':
        product_data = request.json
        if not product_data:
            return jsonify({'error': 'No data provided'}), 400
        
        updated_product = data_manager.update_product(product_id, product_data)
        if updated_product:
            return jsonify(updated_product)
        else:
            return jsonify({'error': 'Product not found'}), 404
    
    elif request.method == 'DELETE':
        if data_manager.delete_product(product_id):
            return jsonify({'message': 'Product deleted successfully'})
        else:
            return jsonify({'error': 'Product not found'}), 404

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update order status"""
    status_data = request.json
    if not status_data or 'status' not in status_data:
        return jsonify({'error': 'Status not provided'}), 400
    
    updated_order = data_manager.update_order_status(order_id, status_data['status'])
    if updated_order:
        # Notify customer via bot if available
        if bot:
            try:
                bot.notify_order_status_update(updated_order)
            except Exception as e:
                logger.error(f"Failed to notify customer: {e}")
        
        return jsonify(updated_order)
    else:
        return jsonify({'error': 'Order not found'}), 404

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint for Telegram bot"""
    if not bot:
        return "Bot not configured", 400
    
    try:
        update_data = request.get_json()
        if update_data:
            bot.process_update(update_data)
        return "OK"
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Error", 500

# Note: Bot will work via webhook when deployed to Replit
# For local development, you would need to run the bot separately
if bot:
    logger.info("Bot is ready to receive webhooks")
