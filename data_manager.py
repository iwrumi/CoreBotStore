import json
import os
from datetime import datetime
from models import Product, Order, User

class DataManager:
    def __init__(self):
        self.data_dir = "data"
        self.products_file = os.path.join(self.data_dir, "products.json")
        self.orders_file = os.path.join(self.data_dir, "orders.json")
        self.users_file = os.path.join(self.data_dir, "users.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        self.init_files()
    
    def init_files(self):
        """Initialize data files with default data if they don't exist"""
        if not os.path.exists(self.products_file):
            default_products = [
                {
                    "id": 1,
                    "name": "Wireless Headphones",
                    "description": "High-quality wireless headphones with noise cancellation",
                    "price": 99.99,
                    "category": "Electronics",
                    "image_url": "",
                    "stock": 10,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": 2,
                    "name": "Coffee Mug",
                    "description": "Ceramic coffee mug with beautiful design",
                    "price": 15.99,
                    "category": "Home & Kitchen",
                    "image_url": "",
                    "stock": 25,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": 3,
                    "name": "Smartphone Case",
                    "description": "Protective case for your smartphone",
                    "price": 24.99,
                    "category": "Electronics",
                    "image_url": "",
                    "stock": 15,
                    "created_at": datetime.now().isoformat()
                }
            ]
            self.save_json(self.products_file, default_products)
        
        if not os.path.exists(self.orders_file):
            self.save_json(self.orders_file, [])
        
        if not os.path.exists(self.users_file):
            self.save_json(self.users_file, [])
    
    def load_json(self, filename):
        """Load data from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_json(self, filename, data):
        """Save data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_products(self):
        """Get all products"""
        return self.load_json(self.products_file)
    
    def get_product(self, product_id):
        """Get a specific product by ID"""
        products = self.get_products()
        return next((p for p in products if p['id'] == product_id), None)
    
    def add_product(self, name, description, price, category, image_url="", stock=0):
        """Add a new product"""
        products = self.get_products()
        
        # Generate new ID
        max_id = max([p['id'] for p in products], default=0)
        new_id = max_id + 1
        
        product = Product(new_id, name, description, price, category, image_url, stock)
        products.append(product.to_dict())
        
        self.save_json(self.products_file, products)
        return product.to_dict()
    
    def update_product(self, product_id, update_data):
        """Update an existing product"""
        products = self.get_products()
        
        for i, product in enumerate(products):
            if product['id'] == product_id:
                # Update fields
                for key, value in update_data.items():
                    if key in ['name', 'description', 'price', 'category', 'image_url', 'stock']:
                        products[i][key] = value
                
                self.save_json(self.products_file, products)
                return products[i]
        
        return None
    
    def delete_product(self, product_id):
        """Delete a product"""
        products = self.get_products()
        initial_length = len(products)
        
        products = [p for p in products if p['id'] != product_id]
        
        if len(products) < initial_length:
            self.save_json(self.products_file, products)
            return True
        
        return False
    
    def get_orders(self):
        """Get all orders"""
        return self.load_json(self.orders_file)
    
    def get_order(self, order_id):
        """Get a specific order by ID"""
        orders = self.get_orders()
        return next((o for o in orders if o['id'] == order_id), None)
    
    def get_user_orders(self, user_id):
        """Get all orders for a specific user"""
        orders = self.get_orders()
        return [o for o in orders if o['user_id'] == user_id]
    
    def create_order(self, order_data):
        """Create a new order"""
        orders = self.get_orders()
        
        # Generate new ID
        max_id = max([o['id'] for o in orders], default=0)
        new_id = max_id + 1
        
        order = Order(
            id=new_id,
            user_id=order_data['user_id'],
            user_name=order_data['user_name'],
            username=order_data.get('username', ''),
            items=order_data['items'],
            shipping_info=order_data['shipping_info'],
            status=order_data.get('status', 'pending')
        )
        
        orders.append(order.to_dict())
        self.save_json(self.orders_file, orders)
        
        # Update stock
        self.update_stock_for_order(order_data['items'])
        
        return order.to_dict()
    
    def update_order_status(self, order_id, new_status):
        """Update order status"""
        orders = self.get_orders()
        
        for i, order in enumerate(orders):
            if order['id'] == order_id:
                orders[i]['status'] = new_status
                self.save_json(self.orders_file, orders)
                return orders[i]
        
        return None
    
    def update_stock_for_order(self, items):
        """Update product stock after order is placed"""
        products = self.get_products()
        
        for product_id_str, item in items.items():
            product_id = int(product_id_str)
            quantity = item['quantity']
            
            for i, product in enumerate(products):
                if product['id'] == product_id:
                    products[i]['stock'] = max(0, products[i]['stock'] - quantity)
                    break
        
        self.save_json(self.products_file, products)
    
    def get_users(self):
        """Get all users"""
        return self.load_json(self.users_file)
    
    def add_user(self, user_data):
        """Add or update user"""
        users = self.get_users()
        user_id = user_data['user_id']
        
        # Check if user already exists
        for i, user in enumerate(users):
            if user['user_id'] == user_id:
                # Update existing user
                users[i].update(user_data)
                self.save_json(self.users_file, users)
                return users[i]
        
        # Add new user
        user = User(
            user_id=user_data['user_id'],
            first_name=user_data['first_name'],
            username=user_data.get('username', ''),
            last_name=user_data.get('last_name', '')
        )
        
        users.append(user.to_dict())
        self.save_json(self.users_file, users)
        return user.to_dict()
