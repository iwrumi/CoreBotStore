from datetime import datetime
import json

class Product:
    def __init__(self, id, name, description, price, category, image_url="", stock=0):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.category = category
        self.image_url = image_url
        self.stock = stock
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'category': self.category,
            'image_url': self.image_url,
            'stock': self.stock,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        product = cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            price=data['price'],
            category=data['category'],
            image_url=data.get('image_url', ''),
            stock=data.get('stock', 0)
        )
        product.created_at = data.get('created_at', datetime.now().isoformat())
        return product

class Order:
    def __init__(self, id, user_id, user_name, username, items, shipping_info, status="pending"):
        self.id = id
        self.user_id = user_id
        self.user_name = user_name
        self.username = username
        self.items = items
        self.shipping_info = shipping_info
        self.status = status
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'username': self.username,
            'items': self.items,
            'shipping_info': self.shipping_info,
            'status': self.status,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        order = cls(
            id=data['id'],
            user_id=data['user_id'],
            user_name=data['user_name'],
            username=data.get('username', ''),
            items=data['items'],
            shipping_info=data['shipping_info'],
            status=data.get('status', 'pending')
        )
        order.created_at = data.get('created_at', datetime.now().isoformat())
        return order

class User:
    def __init__(self, user_id, first_name, username="", last_name=""):
        self.user_id = user_id
        self.first_name = first_name
        self.username = username
        self.last_name = last_name
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'first_name': self.first_name,
            'username': self.username,
            'last_name': self.last_name,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        user = cls(
            user_id=data['user_id'],
            first_name=data['first_name'],
            username=data.get('username', ''),
            last_name=data.get('last_name', '')
        )
        user.created_at = data.get('created_at', datetime.now().isoformat())
        return user
