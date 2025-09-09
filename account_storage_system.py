"""
Account Storage System for Premium Store Bot
Stores actual account credentials for delivery to customers
"""
import json
import os
from datetime import datetime

def ensure_accounts_file():
    """Create accounts.json if it doesn't exist"""
    if not os.path.exists('data/accounts.json'):
        if not os.path.exists('data'):
            os.makedirs('data')
        with open('data/accounts.json', 'w') as f:
            json.dump({}, f)

def add_account(product_id, account_details, added_by):
    """Add account credentials for a product"""
    ensure_accounts_file()
    
    try:
        with open('data/accounts.json', 'r') as f:
            accounts = json.load(f)
    except:
        accounts = {}
    
    if product_id not in accounts:
        accounts[product_id] = []
    
    account = {
        'id': len(accounts[product_id]) + 1,
        'details': account_details,
        'status': 'available',
        'added_by': added_by,
        'added_at': datetime.utcnow().isoformat(),
        'sold_at': None,
        'sold_to': None
    }
    
    accounts[product_id].append(account)
    
    with open('data/accounts.json', 'w') as f:
        json.dump(accounts, f, indent=2)
    
    return True

def get_available_accounts(product_id):
    """Get available accounts for a product"""
    ensure_accounts_file()
    
    try:
        with open('data/accounts.json', 'r') as f:
            accounts = json.load(f)
        
        product_accounts = accounts.get(product_id, [])
        available = [acc for acc in product_accounts if acc['status'] == 'available']
        return available
    except:
        return []

def sell_account(product_id, user_id):
    """Mark an account as sold and return the details"""
    ensure_accounts_file()
    
    try:
        with open('data/accounts.json', 'r') as f:
            accounts = json.load(f)
        
        product_accounts = accounts.get(product_id, [])
        
        for account in product_accounts:
            if account['status'] == 'available':
                account['status'] = 'sold'
                account['sold_at'] = datetime.utcnow().isoformat()
                account['sold_to'] = user_id
                
                with open('data/accounts.json', 'w') as f:
                    json.dump(accounts, f, indent=2)
                
                return account['details']
        
        return None
    except:
        return None

def get_stock_count(product_id):
    """Get available stock count for a product"""
    available = get_available_accounts(product_id)
    return len(available)