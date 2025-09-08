from datetime import datetime
import json
import os
import uuid
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_, or_, desc, asc
from database_models import (
    DatabaseManager, User, Product, Order, OrderItem, Voucher, 
    Payment, Broadcast, Settings, CustomerSupport, init_database
)

class AdvancedDataManager:
    def __init__(self):
        self.db_manager = init_database()
        
    def get_session(self):
        """Get database session"""
        return self.db_manager.get_session()
    
    # ===== USER MANAGEMENT =====
    def get_or_create_user(self, telegram_id, first_name, last_name="", username=""):
        """Get existing user or create new one"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == str(telegram_id)).first()
            if not user:
                user = User(
                    telegram_id=str(telegram_id),
                    first_name=first_name,
                    last_name=last_name,
                    username=username
                )
                session.add(user)
                session.commit()
                session.refresh(user)
            else:
                # Update user info if changed
                user.first_name = first_name
                user.last_name = last_name or user.last_name
                user.username = username or user.username
                user.last_activity = datetime.utcnow()
                session.commit()
            
            return user.to_dict()
        finally:
            session.close()
    
    def get_users(self, is_admin=None, is_banned=None):
        """Get all users with optional filters"""
        session = self.get_session()
        try:
            query = session.query(User)
            if is_admin is not None:
                query = query.filter(User.is_admin == is_admin)
            if is_banned is not None:
                query = query.filter(User.is_banned == is_banned)
            
            users = query.order_by(desc(User.created_at)).all()
            return [user.to_dict() for user in users]
        finally:
            session.close()
    
    def update_user(self, telegram_id, update_data):
        """Update user information"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == str(telegram_id)).first()
            if user:
                for key, value in update_data.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                session.commit()
                return user.to_dict()
            return None
        finally:
            session.close()
    
    # ===== PRODUCT MANAGEMENT =====
    def get_products(self, is_active=True, category=None):
        """Get products with optional filters"""
        session = self.get_session()
        try:
            query = session.query(Product)
            if is_active is not None:
                query = query.filter(Product.is_active == is_active)
            if category:
                query = query.filter(Product.category == category)
            
            products = query.order_by(asc(Product.name)).all()
            return [product.to_dict() for product in products]
        finally:
            session.close()
    
    def get_product(self, product_id):
        """Get single product by ID"""
        session = self.get_session()
        try:
            product = session.query(Product).filter(Product.id == product_id).first()
            return product.to_dict() if product else None
        finally:
            session.close()
    
    def add_product(self, name, description, price, category, image_url="", stock=0, **kwargs):
        """Add new product"""
        session = self.get_session()
        try:
            product = Product(
                name=name,
                description=description,
                price=price,
                category=category,
                image_url=image_url,
                stock=stock,
                is_active=kwargs.get('is_active', True),
                is_featured=kwargs.get('is_featured', False),
                tags=kwargs.get('tags', []),
                specifications=kwargs.get('specifications', {})
            )
            session.add(product)
            session.commit()
            session.refresh(product)
            return product.to_dict()
        finally:
            session.close()
    
    def update_product(self, product_id, update_data):
        """Update product"""
        session = self.get_session()
        try:
            product = session.query(Product).filter(Product.id == product_id).first()
            if product:
                for key, value in update_data.items():
                    if hasattr(product, key):
                        setattr(product, key, value)
                product.updated_at = datetime.utcnow()
                session.commit()
                return product.to_dict()
            return None
        finally:
            session.close()
    
    def delete_product(self, product_id):
        """Delete product"""
        session = self.get_session()
        try:
            product = session.query(Product).filter(Product.id == product_id).first()
            if product:
                session.delete(product)
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def get_categories(self):
        """Get all product categories"""
        session = self.get_session()
        try:
            categories = session.query(Product.category).filter(Product.is_active == True).distinct().all()
            return [cat[0] for cat in categories]
        finally:
            session.close()
    
    # ===== ORDER MANAGEMENT =====
    def create_order(self, user_telegram_id, items, shipping_address="", notes="", voucher_code=""):
        """Create new order"""
        session = self.get_session()
        try:
            # Get user
            user = session.query(User).filter(User.telegram_id == str(user_telegram_id)).first()
            if not user:
                return None
            
            # Generate order number
            order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            # Create order
            order = Order(
                order_number=order_number,
                user_id=user.id,
                shipping_address=shipping_address,
                notes=notes,
                voucher_code=voucher_code
            )
            session.add(order)
            session.flush()  # Get order ID
            
            # Add order items and calculate totals
            subtotal = 0
            for product_id, item_data in items.items():
                product = session.query(Product).filter(Product.id == int(product_id)).first()
                if product and product.stock >= item_data['quantity']:
                    # Create order item
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=item_data['quantity'],
                        price=product.price,
                        total=product.price * item_data['quantity']
                    )
                    session.add(order_item)
                    
                    # Update product stock
                    product.stock -= item_data['quantity']
                    
                    subtotal += order_item.total
            
            # Apply voucher discount if applicable
            discount = 0
            if voucher_code:
                voucher = session.query(Voucher).filter(
                    and_(
                        Voucher.code == voucher_code,
                        Voucher.is_active == True,
                        or_(Voucher.valid_until.is_(None), Voucher.valid_until > datetime.utcnow()),
                        Voucher.minimum_order <= subtotal,
                        or_(Voucher.usage_limit == 0, Voucher.usage_count < Voucher.usage_limit)
                    )
                ).first()
                
                if voucher:
                    if voucher.discount_type == 'percentage':
                        discount = subtotal * (voucher.discount_value / 100)
                        if voucher.maximum_discount > 0:
                            discount = min(discount, voucher.maximum_discount)
                    else:  # fixed_amount
                        discount = voucher.discount_value
                    
                    # Update voucher usage
                    voucher.usage_count += 1
            
            # Calculate totals
            order.subtotal = subtotal
            order.discount = discount
            order.total = subtotal - discount
            
            # Update user stats
            user.order_count += 1
            user.total_spent += order.total
            
            session.commit()
            session.refresh(order)
            
            return order.to_dict()
        finally:
            session.close()
    
    def get_orders(self, user_telegram_id=None, status=None, limit=None):
        """Get orders with optional filters"""
        session = self.get_session()
        try:
            query = session.query(Order)
            
            if user_telegram_id:
                user = session.query(User).filter(User.telegram_id == str(user_telegram_id)).first()
                if user:
                    query = query.filter(Order.user_id == user.id)
                else:
                    return []
            
            if status:
                query = query.filter(Order.status == status)
            
            query = query.order_by(desc(Order.created_at))
            if limit:
                query = query.limit(limit)
            
            orders = query.all()
            return [order.to_dict() for order in orders]
        finally:
            session.close()
    
    def get_order(self, order_id):
        """Get single order by ID"""
        session = self.get_session()
        try:
            order = session.query(Order).filter(Order.id == order_id).first()
            return order.to_dict() if order else None
        finally:
            session.close()
    
    def update_order_status(self, order_id, status):
        """Update order status"""
        session = self.get_session()
        try:
            order = session.query(Order).filter(Order.id == order_id).first()
            if order:
                order.status = status
                order.updated_at = datetime.utcnow()
                session.commit()
                return order.to_dict()
            return None
        finally:
            session.close()
    
    def get_user_orders(self, user_telegram_id):
        """Get orders for specific user"""
        return self.get_orders(user_telegram_id=user_telegram_id)
    
    # ===== VOUCHER MANAGEMENT =====
    def create_voucher(self, code, name, discount_type, discount_value, **kwargs):
        """Create new voucher"""
        session = self.get_session()
        try:
            voucher = Voucher(
                code=code.upper(),
                name=name,
                description=kwargs.get('description', ''),
                discount_type=discount_type,
                discount_value=discount_value,
                minimum_order=kwargs.get('minimum_order', 0),
                maximum_discount=kwargs.get('maximum_discount', 0),
                usage_limit=kwargs.get('usage_limit', 0),
                valid_from=kwargs.get('valid_from', datetime.utcnow()),
                valid_until=kwargs.get('valid_until')
            )
            session.add(voucher)
            session.commit()
            session.refresh(voucher)
            return voucher.to_dict()
        finally:
            session.close()
    
    def get_vouchers(self, is_active=None):
        """Get vouchers"""
        session = self.get_session()
        try:
            query = session.query(Voucher)
            if is_active is not None:
                query = query.filter(Voucher.is_active == is_active)
            
            vouchers = query.order_by(desc(Voucher.created_at)).all()
            return [voucher.to_dict() for voucher in vouchers]
        finally:
            session.close()
    
    def validate_voucher(self, code, order_total):
        """Validate voucher code"""
        session = self.get_session()
        try:
            voucher = session.query(Voucher).filter(
                and_(
                    Voucher.code == code.upper(),
                    Voucher.is_active == True,
                    or_(Voucher.valid_until.is_(None), Voucher.valid_until > datetime.utcnow()),
                    Voucher.minimum_order <= order_total,
                    or_(Voucher.usage_limit == 0, Voucher.usage_count < Voucher.usage_limit)
                )
            ).first()
            
            if voucher:
                # Calculate discount
                if voucher.discount_type == 'percentage':
                    discount = order_total * (voucher.discount_value / 100)
                    if voucher.maximum_discount > 0:
                        discount = min(discount, voucher.maximum_discount)
                else:  # fixed_amount
                    discount = voucher.discount_value
                
                return {
                    'valid': True,
                    'voucher': voucher.to_dict(),
                    'discount_amount': discount
                }
            
            return {'valid': False, 'message': 'Invalid or expired voucher code'}
        finally:
            session.close()
    
    # ===== PAYMENT MANAGEMENT =====
    def create_payment(self, user_telegram_id, amount, payment_method, **kwargs):
        """Create payment record"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == str(user_telegram_id)).first()
            if not user:
                return None
            
            transaction_id = f"PAY-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            payment = Payment(
                transaction_id=transaction_id,
                user_id=user.id,
                order_id=kwargs.get('order_id'),
                amount=amount,
                currency=kwargs.get('currency', 'PHP'),
                payment_method=payment_method,
                reference_number=kwargs.get('reference_number', ''),
                notes=kwargs.get('notes', ''),
                proof_image=kwargs.get('proof_image', '')
            )
            session.add(payment)
            session.commit()
            session.refresh(payment)
            return payment.to_dict()
        finally:
            session.close()
    
    def get_payments(self, user_telegram_id=None, status=None):
        """Get payments"""
        session = self.get_session()
        try:
            query = session.query(Payment)
            
            if user_telegram_id:
                user = session.query(User).filter(User.telegram_id == str(user_telegram_id)).first()
                if user:
                    query = query.filter(Payment.user_id == user.id)
                else:
                    return []
            
            if status:
                query = query.filter(Payment.status == status)
            
            payments = query.order_by(desc(Payment.created_at)).all()
            return [payment.to_dict() for payment in payments]
        finally:
            session.close()
    
    def verify_payment(self, payment_id, verified_by):
        """Mark payment as verified"""
        session = self.get_session()
        try:
            payment = session.query(Payment).filter(Payment.id == payment_id).first()
            if payment:
                payment.status = 'completed'
                payment.verified_at = datetime.utcnow()
                payment.verified_by = verified_by
                
                # Update related order if exists
                if payment.order_id:
                    order = session.query(Order).filter(Order.id == payment.order_id).first()
                    if order:
                        order.payment_status = 'paid'
                        order.status = 'confirmed'
                
                session.commit()
                return payment.to_dict()
            return None
        finally:
            session.close()
    
    # ===== BROADCAST MANAGEMENT =====
    def create_broadcast(self, title, message, created_by, **kwargs):
        """Create broadcast"""
        session = self.get_session()
        try:
            broadcast = Broadcast(
                title=title,
                message=message,
                image_url=kwargs.get('image_url', ''),
                target_users=kwargs.get('target_users', 'all'),
                scheduled_at=kwargs.get('scheduled_at'),
                created_by=created_by
            )
            session.add(broadcast)
            session.commit()
            session.refresh(broadcast)
            return broadcast.to_dict()
        finally:
            session.close()
    
    def get_broadcasts(self, status=None):
        """Get broadcasts"""
        session = self.get_session()
        try:
            query = session.query(Broadcast)
            if status:
                query = query.filter(Broadcast.status == status)
            
            broadcasts = query.order_by(desc(Broadcast.created_at)).all()
            return [broadcast.to_dict() for broadcast in broadcasts]
        finally:
            session.close()
    
    def update_broadcast_status(self, broadcast_id, status, sent_count=0, failed_count=0):
        """Update broadcast status"""
        session = self.get_session()
        try:
            broadcast = session.query(Broadcast).filter(Broadcast.id == broadcast_id).first()
            if broadcast:
                broadcast.status = status
                broadcast.sent_count = sent_count
                broadcast.failed_count = failed_count
                if status == 'sent':
                    broadcast.sent_at = datetime.utcnow()
                session.commit()
                return broadcast.to_dict()
            return None
        finally:
            session.close()
    
    # ===== SETTINGS MANAGEMENT =====
    def get_setting(self, key, default=None):
        """Get setting value"""
        session = self.get_session()
        try:
            setting = session.query(Settings).filter(Settings.key == key).first()
            return setting.value if setting else default
        finally:
            session.close()
    
    def set_setting(self, key, value, description=""):
        """Set setting value"""
        session = self.get_session()
        try:
            setting = session.query(Settings).filter(Settings.key == key).first()
            if setting:
                setting.value = value
                setting.updated_at = datetime.utcnow()
                if description:
                    setting.description = description
            else:
                setting = Settings(key=key, value=value, description=description)
                session.add(setting)
            
            session.commit()
            return setting.to_dict()
        finally:
            session.close()
    
    def get_all_settings(self):
        """Get all settings"""
        session = self.get_session()
        try:
            settings = session.query(Settings).all()
            return {setting.key: setting.value for setting in settings}
        finally:
            session.close()
    
    # ===== CUSTOMER SUPPORT =====
    def create_support_ticket(self, user_telegram_id, subject, message, category="general"):
        """Create customer support ticket"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == str(user_telegram_id)).first()
            if not user:
                return None
            
            ticket = CustomerSupport(
                user_id=user.id,
                subject=subject,
                message=message,
                category=category
            )
            session.add(ticket)
            session.commit()
            session.refresh(ticket)
            return ticket.to_dict()
        finally:
            session.close()
    
    def get_support_tickets(self, status=None):
        """Get support tickets"""
        session = self.get_session()
        try:
            query = session.query(CustomerSupport)
            if status:
                query = query.filter(CustomerSupport.status == status)
            
            tickets = query.order_by(desc(CustomerSupport.created_at)).all()
            return [ticket.to_dict() for ticket in tickets]
        finally:
            session.close()
    
    # ===== ANALYTICS =====
    def get_analytics(self):
        """Get store analytics"""
        session = self.get_session()
        try:
            # Basic counts
            total_users = session.query(User).count()
            total_orders = session.query(Order).count()
            total_products = session.query(Product).filter(Product.is_active == True).count()
            
            # Revenue
            total_revenue = session.query(Order).filter(Order.payment_status == 'paid').with_entities(
                session.query(Order.total).scalar_subquery()
            ).scalar() or 0
            
            # Recent stats
            from datetime import timedelta
            week_ago = datetime.utcnow() - timedelta(days=7)
            weekly_orders = session.query(Order).filter(Order.created_at >= week_ago).count()
            weekly_revenue = session.query(Order).filter(
                and_(Order.created_at >= week_ago, Order.payment_status == 'paid')
            ).with_entities(session.query(Order.total).scalar_subquery()).scalar() or 0
            
            return {
                'total_users': total_users,
                'total_orders': total_orders,
                'total_products': total_products,
                'total_revenue': total_revenue,
                'weekly_orders': weekly_orders,
                'weekly_revenue': weekly_revenue
            }
        finally:
            session.close()
    
    # ===== MIGRATION UTILITIES =====
    def migrate_from_json(self, json_data_manager):
        """Migrate data from JSON-based system"""
        session = self.get_session()
        try:
            # Migrate products
            products = json_data_manager.get_products()
            for product_data in products:
                existing = session.query(Product).filter(Product.id == product_data['id']).first()
                if not existing:
                    product = Product(
                        id=product_data['id'],
                        name=product_data['name'],
                        description=product_data['description'],
                        price=product_data['price'],
                        category=product_data['category'],
                        image_url=product_data.get('image_url', ''),
                        stock=product_data.get('stock', 0)
                    )
                    session.add(product)
            
            # Migrate users and orders
            orders = json_data_manager.get_orders()
            for order_data in orders:
                # Create user if doesn't exist
                user = session.query(User).filter(User.telegram_id == str(order_data['user_id'])).first()
                if not user:
                    user = User(
                        telegram_id=str(order_data['user_id']),
                        first_name=order_data.get('user_name', 'Unknown'),
                        username=order_data.get('username', '')
                    )
                    session.add(user)
                    session.flush()
                
                # Create order if doesn't exist
                existing_order = session.query(Order).filter(Order.id == order_data['id']).first()
                if not existing_order:
                    order = Order(
                        id=order_data['id'],
                        order_number=f"ORD-MIGRATED-{order_data['id']}",
                        user_id=user.id,
                        status=order_data.get('status', 'pending'),
                        shipping_address=order_data.get('shipping_info', ''),
                        total=sum(item['product']['price'] * item['quantity'] for item in order_data['items'].values())
                    )
                    session.add(order)
                    session.flush()
                    
                    # Add order items
                    for product_id, item in order_data['items'].items():
                        order_item = OrderItem(
                            order_id=order.id,
                            product_id=int(product_id),
                            quantity=item['quantity'],
                            price=item['product']['price'],
                            total=item['product']['price'] * item['quantity']
                        )
                        session.add(order_item)
            
            session.commit()
            print("✅ Successfully migrated data to PostgreSQL!")
        except Exception as e:
            session.rollback()
            print(f"❌ Error migrating data: {e}")
            raise
        finally:
            session.close()