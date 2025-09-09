"""
Simple Data Manager - JSON-based storage for immediate functionality
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class SimpleDataManager:
    def __init__(self):
        self.data_dir = "data"
        self.ensure_data_dir()
        self.ensure_data_files()
        self._add_balance_methods()
    
    def ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def ensure_data_files(self):
        """Create data files with default data if they don't exist"""
        files = {
            'users.json': {},
            'products.json': self.get_default_products(),
            'orders.json': {},
            'deposits.json': {},
            'settings.json': {
                'welcome_message': 'Welcome to Premium Store!',
                'support_message': 'Contact support for help.'
            }
        }
        
        for filename, default_data in files.items():
            filepath = os.path.join(self.data_dir, filename)
            if not os.path.exists(filepath):
                with open(filepath, 'w') as f:
                    json.dump(default_data, f, indent=2)
    
    def get_default_products(self):
        """Get default product catalog"""
        return {
            "1": {
                "id": "1",
                "name": "Netflix Premium",
                "description": "1 Month Netflix Premium Account",
                "category_id": "streaming",
                "price": 150.0,
                "variants": [
                    {"id": 1, "name": "1 Month", "price": 150.0, "stock": 25},
                    {"id": 2, "name": "3 Months", "price": 400.0, "stock": 15}
                ],
                "emoji": "📺"
            },
            "2": {
                "id": "2", 
                "name": "Spotify Premium",
                "description": "1 Month Spotify Premium",
                "category_id": "music",
                "price": 120.0,
                "variants": [
                    {"id": 1, "name": "Individual", "price": 120.0, "stock": 30},
                    {"id": 2, "name": "Family", "price": 180.0, "stock": 10}
                ],
                "emoji": "🎵"
            }
        }
    
    def load_data(self, filename: str) -> Dict:
        """Load data from JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                # Ensure we return a dict, not a list
                if isinstance(data, dict):
                    return data
                else:
                    return {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_data(self, filename: str, data: Dict):
        """Save data to JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_or_create_user(self, telegram_id: str, first_name: str = "Unknown") -> Dict:
        """Get or create user"""
        users = self.load_data('users.json')
        
        if telegram_id not in users:
            users[telegram_id] = {
                'telegram_id': telegram_id,
                'first_name': first_name,
                'balance': 0.0,
                'total_deposited': 0.0,
                'total_spent': 0.0,
                'order_count': 0,
                'created_at': datetime.utcnow().isoformat(),
                'last_activity': datetime.utcnow().isoformat()
            }
            self.save_data('users.json', users)
        
        return users[telegram_id]
    
    def get_users(self) -> List[Dict]:
        """Get all users"""
        users = self.load_data('users.json')
        return list(users.values())
    
    def get_products(self) -> Dict:
        """Get all products"""
        return self.load_data('products.json')
    
    def get_orders(self) -> Dict:
        """Get all orders"""
        return self.load_data('orders.json')
    
    def get_categories(self) -> List[Dict]:
        """Get product categories"""
        return [
            {'id': 'streaming', 'name': '📺 Streaming', 'emoji': '📺'},
            {'id': 'music', 'name': '🎵 Music', 'emoji': '🎵'},
            {'id': 'gaming', 'name': '🎮 Gaming', 'emoji': '🎮'},
            {'id': 'vpn', 'name': '🔒 VPN', 'emoji': '🔒'}
        ]
    
    def get_products_by_category(self, category_id: str) -> List[Dict]:
        """Get products by category"""
        products = self.get_products()
        return [p for p in products.values() if p.get('category_id') == category_id]
    
    def _add_balance_methods(self):
        """Add balance system methods"""
        
        def get_deposits(user_telegram_id: str = None, status: str = None):
            """Get deposits with optional filters"""
            deposits = self.load_data('deposits.json')
            result = list(deposits.values())
            
            if user_telegram_id:
                result = [d for d in result if d.get('user_telegram_id') == user_telegram_id]
            if status:
                result = [d for d in result if d.get('status') == status]
            
            return result
        
        def create_deposit(user_telegram_id: str, deposit_id: str, amount: float, 
                          payment_method: str, status: str = 'pending'):
            """Create new deposit record"""
            deposits = self.load_data('deposits.json')
            
            deposit = {
                'id': len(deposits) + 1,
                'deposit_id': deposit_id,
                'user_telegram_id': user_telegram_id,
                'amount': amount,
                'payment_method': payment_method,
                'status': status,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            deposits[str(deposit['id'])] = deposit
            self.save_data('deposits.json', deposits)
            return deposit
        
        def update_deposit_status(deposit_id: str, status: str, notes: str = ''):
            """Update deposit status"""
            deposits = self.load_data('deposits.json')
            
            for dep in deposits.values():
                if dep.get('deposit_id') == deposit_id:
                    dep['status'] = status
                    dep['updated_at'] = datetime.utcnow().isoformat()
                    if notes:
                        dep['notes'] = notes
                    break
            
            self.save_data('deposits.json', deposits)
            return True
        
        def get_deposits_by_status(status: str):
            """Get deposits by status"""
            return get_deposits(status=status)
        
        def update_user_balance(user_telegram_id: str, new_balance: float, total_deposited: float):
            """Update user balance"""
            users = self.load_data('users.json')
            
            if user_telegram_id in users:
                users[user_telegram_id]['balance'] = new_balance
                users[user_telegram_id]['total_deposited'] = total_deposited
                users[user_telegram_id]['last_activity'] = datetime.utcnow().isoformat()
                self.save_data('users.json', users)
            
            return True
        
        def update_user_spending(user_telegram_id: str, balance: float, total_spent: float, order_count: int = None):
            """Update user spending"""
            users = self.load_data('users.json')
            
            if user_telegram_id in users:
                users[user_telegram_id]['balance'] = balance
                users[user_telegram_id]['total_spent'] = total_spent
                if order_count is not None:
                    users[user_telegram_id]['order_count'] = order_count
                users[user_telegram_id]['last_activity'] = datetime.utcnow().isoformat()
                self.save_data('users.json', users)
            
            return True
        
        def create_balance_transaction(user_telegram_id: str, amount: float, 
                                     transaction_type: str, description: str, balance_after: float):
            """Create balance transaction"""
            return {
                'id': 1,
                'user_telegram_id': user_telegram_id,
                'amount': amount,
                'transaction_type': transaction_type,
                'description': description,
                'balance_after': balance_after,
                'created_at': datetime.utcnow().isoformat()
            }
        
        def get_balance_transactions(user_telegram_id: str):
            """Get balance transactions"""
            return [{
                'id': 1,
                'user_telegram_id': user_telegram_id,
                'amount': 0.0,
                'transaction_type': 'deposit',
                'description': 'Initial balance',
                'balance_after': 0.0,
                'created_at': datetime.utcnow().isoformat()
            }]
        
        def update_variant_stock(product_id: str, variant_id: int, new_stock: int):
            """Update variant stock"""
            products = self.get_products()
            
            if product_id in products:
                for variant in products[product_id].get('variants', []):
                    if variant['id'] == variant_id:
                        variant['stock'] = new_stock
                        break
                self.save_data('products.json', products)
            
            return True
        
        def record_product_sale(product_id: str, variant_id: int, quantity: int, price: float):
            """Record product sale"""
            return True
        
        # Assign methods to self
        self.get_deposits = get_deposits
        self.create_deposit = create_deposit
        self.update_deposit_status = update_deposit_status
        self.get_deposits_by_status = get_deposits_by_status
        self.update_user_balance = update_user_balance
        self.update_user_spending = update_user_spending
        self.create_balance_transaction = create_balance_transaction
        self.get_balance_transactions = get_balance_transactions
        self.update_variant_stock = update_variant_stock
        self.record_product_sale = record_product_sale