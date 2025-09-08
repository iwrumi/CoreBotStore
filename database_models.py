from datetime import datetime, timezone
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, default='')
    username = Column(String, default='')
    phone = Column(String, default='')
    email = Column(String, default='')
    is_admin = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    total_spent = Column(Float, default=0.0)
    order_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = relationship("Order", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    
    def to_dict(self):
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'username': self.username,
            'phone': self.phone,
            'email': self.email,
            'is_admin': self.is_admin,
            'is_banned': self.is_banned,
            'total_spent': self.total_spent,
            'order_count': self.order_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None
        }

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default='')
    price = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    image_url = Column(String, default='')
    stock = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    tags = Column(JSON, default=[])
    specifications = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="product")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'category': self.category,
            'image_url': self.image_url,
            'stock': self.stock,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'tags': self.tags,
            'specifications': self.specifications,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String, default='pending')  # pending, confirmed, processing, shipped, delivered, cancelled
    subtotal = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    shipping_cost = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    payment_status = Column(String, default='pending')  # pending, paid, failed, refunded
    payment_method = Column(String, default='')
    shipping_address = Column(Text, default='')
    notes = Column(Text, default='')
    voucher_code = Column(String, default='')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order")
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'user_id': self.user_id,
            'status': self.status,
            'subtotal': self.subtotal,
            'discount': self.discount,
            'tax': self.tax,
            'shipping_cost': self.shipping_cost,
            'total': self.total,
            'payment_status': self.payment_status,
            'payment_method': self.payment_method,
            'shipping_address': self.shipping_address,
            'notes': self.notes,
            'voucher_code': self.voucher_code,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items': [item.to_dict() for item in self.items] if self.items else []
        }

class OrderItem(Base):
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # Price at time of order
    total = Column(Float, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price': self.price,
            'total': self.total,
            'product': self.product.to_dict() if self.product else None
        }

class Voucher(Base):
    __tablename__ = 'vouchers'
    
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, default='')
    discount_type = Column(String, nullable=False)  # percentage, fixed_amount
    discount_value = Column(Float, nullable=False)
    minimum_order = Column(Float, default=0.0)
    maximum_discount = Column(Float, default=0.0)  # For percentage discounts
    usage_limit = Column(Integer, default=0)  # 0 = unlimited
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': self.discount_value,
            'minimum_order': self.minimum_order,
            'maximum_discount': self.maximum_discount,
            'usage_limit': self.usage_limit,
            'usage_count': self.usage_count,
            'is_active': self.is_active,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Payment(Base):
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    transaction_id = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default='USD')
    payment_method = Column(String, nullable=False)  # gcash, paymaya, bank, manual
    status = Column(String, default='pending')  # pending, completed, failed, cancelled
    reference_number = Column(String, default='')
    notes = Column(Text, default='')
    proof_image = Column(String, default='')
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(String, default='')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="payments")
    order = relationship("Order", back_populates="payments")
    
    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'user_id': self.user_id,
            'order_id': self.order_id,
            'amount': self.amount,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'status': self.status,
            'reference_number': self.reference_number,
            'notes': self.notes,
            'proof_image': self.proof_image,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'verified_by': self.verified_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Broadcast(Base):
    __tablename__ = 'broadcasts'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    image_url = Column(String, default='')
    target_users = Column(String, default='all')  # all, active, inactive, vip
    status = Column(String, default='draft')  # draft, scheduled, sending, sent, failed
    scheduled_at = Column(DateTime, nullable=True)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'image_url': self.image_url,
            'target_users': self.target_users,
            'status': self.status,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'sent_count': self.sent_count,
            'failed_count': self.failed_count,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None
        }

class Settings(Base):
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text, default='')
    description = Column(Text, default='')
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class CustomerSupport(Base):
    __tablename__ = 'customer_support'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    subject = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String, default='open')  # open, pending, resolved, closed
    priority = Column(String, default='normal')  # low, normal, high, urgent
    category = Column(String, default='general')  # general, order, payment, technical
    response = Column(Text, default='')
    responded_by = Column(String, default='')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subject': self.subject,
            'message': self.message,
            'status': self.status,
            'priority': self.priority,
            'category': self.category,
            'response': self.response,
            'responded_by': self.responded_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Database utility functions
class DatabaseManager:
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
        
    def init_default_settings(self):
        """Initialize default settings"""
        session = self.get_session()
        try:
            default_settings = [
                {
                    'key': 'welcome_message',
                    'value': '🛍️ Welcome to our store! Browse our products and place your orders easily.',
                    'description': 'Welcome message shown when users start the bot'
                },
                {
                    'key': 'store_name',
                    'value': 'My Telegram Store',
                    'description': 'Name of the store'
                },
                {
                    'key': 'contact_info',
                    'value': 'Contact us for support and inquiries.',
                    'description': 'Store contact information'
                },
                {
                    'key': 'auto_confirm_orders',
                    'value': 'false',
                    'description': 'Automatically confirm orders without manual approval'
                },
                {
                    'key': 'require_payment_proof',
                    'value': 'true',
                    'description': 'Require customers to upload payment proof'
                },
                {
                    'key': 'payment_methods',
                    'value': '["GCash", "PayMaya", "Bank Transfer", "Cash on Delivery"]',
                    'description': 'Available payment methods (JSON array)'
                }
            ]
            
            for setting_data in default_settings:
                existing = session.query(Settings).filter(Settings.key == setting_data['key']).first()
                if not existing:
                    setting = Settings(**setting_data)
                    session.add(setting)
            
            session.commit()
        finally:
            session.close()

def init_database():
    """Initialize database with tables and default data"""
    db_manager = DatabaseManager()
    db_manager.create_tables()
    db_manager.init_default_settings()
    return db_manager