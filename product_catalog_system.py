"""
Product Catalog System with Variants and Categories
Handles products, categories, variants, and inventory management
"""
from datetime import datetime
from typing import Dict, List, Optional
from simple_data_manager import SimpleDataManager

class ProductCatalogSystem:
    def __init__(self):
        self.data_manager = SimpleDataManager()
        self.default_categories = self._load_default_categories()
        self.sample_products = self._load_sample_products()
    
    def _load_default_categories(self) -> List[Dict]:
        """Load default product categories"""
        return [
            {
                'id': 'apps_streaming',
                'name': 'APPS STREAMING',
                'emoji': '📺',
                'description': 'Netflix, Spotify, Disney+, and more streaming accounts',
                'active': True
            },
            {
                'id': 'editing_premium',
                'name': 'EDITING PREMIUM',
                'emoji': '🎬',
                'description': 'Adobe Creative Suite, Canva Pro, and editing software',
                'active': True
            },
            {
                'id': 'gaming_accounts',
                'name': 'GAMING ACCOUNTS',
                'emoji': '🎮',
                'description': 'Gaming accounts and in-game currencies',
                'active': True
            },
            {
                'id': 'productivity',
                'name': 'PRODUCTIVITY',
                'emoji': '💼',
                'description': 'Microsoft Office, Google Workspace, productivity tools',
                'active': True
            },
            {
                'id': 'vpn_security',
                'name': 'VPN & SECURITY',
                'emoji': '🔒',
                'description': 'VPN services, antivirus, and security software',
                'active': True
            },
            {
                'id': 'auto_services',
                'name': 'AUTO SERVICES',
                'emoji': '⚙️',
                'description': 'Automated services and plug solutions',
                'active': True
            }
        ]
    
    def _load_sample_products(self) -> List[Dict]:
        """Load sample products with variants"""
        return [
            {
                'id': 'auto_plug_service',
                'category_id': 'auto_services',
                'name': 'AUTO PLUG SERVICE',
                'description': 'Automated plug service with multiple tier options.',
                'image_url': None,
                'base_price': 80.0,
                'active': True,
                'variants': [
                    {
                        'id': 1,
                        'name': '01D NONSTOP PLUG',
                        'price': 80.0,
                        'duration': '1 day',
                        'features': ['24/7 automated service', 'Basic support'],
                        'stock': 19,
                        'popular': False
                    },
                    {
                        'id': 2,
                        'name': '02D NONSTOP PLUG',
                        'price': 150.0,
                        'duration': '2 days',
                        'features': ['48/7 automated service', 'Priority support'],
                        'stock': 21,
                        'popular': False
                    },
                    {
                        'id': 3,
                        'name': '05D NONSTOP PLUG',
                        'price': 350.0,
                        'duration': '5 days',
                        'features': ['120/7 automated service', 'Premium support'],
                        'stock': 21,
                        'popular': True
                    },
                    {
                        'id': 4,
                        'name': '30D NONSTOP PLUG',
                        'price': 1500.0,
                        'duration': '30 days',
                        'features': ['720/7 automated service', 'VIP support', 'Custom config'],
                        'stock': 10,
                        'popular': False
                    }
                ],
                'created_at': datetime.utcnow().isoformat()
            },
            {
                'id': 'netflix_premium',
                'category_id': 'apps_streaming',
                'name': 'NETFLIX PREMIUM',
                'description': 'Netflix Premium accounts with 4K streaming.',
                'image_url': None,
                'base_price': 100.0,
                'active': True,
                'variants': [
                    {
                        'id': 1,
                        'name': '1 Month Netflix Premium',
                        'price': 100.0,
                        'duration': '30 days',
                        'features': ['4K Ultra HD', '4 screens', 'Download feature'],
                        'stock': 50,
                        'popular': False
                    },
                    {
                        'id': 2,
                        'name': '3 Month Netflix Premium',
                        'price': 280.0,
                        'duration': '90 days',
                        'features': ['4K Ultra HD', '4 screens', 'Download feature', '7% discount'],
                        'stock': 30,
                        'popular': True
                    },
                    {
                        'id': 3,
                        'name': '6 Month Netflix Premium',
                        'price': 500.0,
                        'duration': '180 days',
                        'features': ['4K Ultra HD', '4 screens', 'Download feature', '17% discount'],
                        'stock': 15,
                        'popular': False
                    }
                ],
                'created_at': datetime.utcnow().isoformat()
            },
            {
                'id': 'spotify_premium',
                'category_id': 'apps_streaming',
                'name': 'SPOTIFY PREMIUM',
                'description': 'Spotify Premium accounts with ad-free music.',
                'image_url': None,
                'base_price': 60.0,
                'active': True,
                'variants': [
                    {
                        'id': 1,
                        'name': '1 Month Spotify Premium',
                        'price': 60.0,
                        'duration': '30 days',
                        'features': ['Ad-free music', 'Offline downloads', 'High quality audio'],
                        'stock': 100,
                        'popular': False
                    },
                    {
                        'id': 2,
                        'name': '3 Month Spotify Premium',
                        'price': 160.0,
                        'duration': '90 days',
                        'features': ['Ad-free music', 'Offline downloads', 'High quality audio', '11% discount'],
                        'stock': 50,
                        'popular': True
                    }
                ],
                'created_at': datetime.utcnow().isoformat()
            }
        ]
    
    def get_categories(self, active_only: bool = True) -> List[Dict]:
        """Get all product categories"""
        categories = self.default_categories.copy()
        
        if active_only:
            categories = [cat for cat in categories if cat.get('active', True)]
        
        # Add product counts
        for category in categories:
            category['product_count'] = len(self.get_products_by_category(category['id']))
        
        return categories
    
    def get_category(self, category_id: str) -> Optional[Dict]:
        """Get specific category by ID"""
        for category in self.default_categories:
            if category['id'] == category_id:
                return category
        return None
    
    def get_products_by_category(self, category_id: str, active_only: bool = True) -> List[Dict]:
        """Get all products in a category"""
        products = [p for p in self.sample_products if p['category_id'] == category_id]
        
        if active_only:
            products = [p for p in products if p.get('active', True)]
        
        return products
    
    def get_product(self, product_id: str) -> Optional[Dict]:
        """Get specific product by ID"""
        for product in self.sample_products:
            if product['id'] == product_id:
                return product
        return None
    
    def get_product_variant(self, product_id: str, variant_id: int) -> Optional[Dict]:
        """Get specific product variant"""
        product = self.get_product(product_id)
        if not product:
            return None
        
        for variant in product.get('variants', []):
            if variant['id'] == variant_id:
                # Add product info to variant
                variant['product_name'] = product['name']
                variant['product_description'] = product['description']
                variant['category_id'] = product['category_id']
                return variant
        
        return None
    
    def get_popular_products(self, limit: int = 10) -> List[Dict]:
        """Get popular products across all categories"""
        popular_variants = []
        
        for product in self.sample_products:
            for variant in product.get('variants', []):
                if variant.get('popular', False):
                    popular_variants.append({
                        'product_id': product['id'],
                        'product_name': product['name'],
                        'variant': variant,
                        'category': self.get_category(product['category_id'])
                    })
        
        return popular_variants[:limit]
    
    def search_products(self, query: str, limit: int = 20) -> List[Dict]:
        """Search products by name or description"""
        query_lower = query.lower()
        results = []
        
        for product in self.sample_products:
            # Check product name and description
            if (query_lower in product['name'].lower() or 
                query_lower in product.get('description', '').lower()):
                
                results.append({
                    'product': product,
                    'category': self.get_category(product['category_id']),
                    'match_type': 'product'
                })
            
            # Check variant names
            for variant in product.get('variants', []):
                if query_lower in variant['name'].lower():
                    results.append({
                        'product': product,
                        'variant': variant,
                        'category': self.get_category(product['category_id']),
                        'match_type': 'variant'
                    })
        
        return results[:limit]
    
    def check_stock(self, product_id: str, variant_id: int) -> Dict:
        """Check stock availability for a product variant"""
        variant = self.get_product_variant(product_id, variant_id)
        
        if not variant:
            return {
                'available': False,
                'stock': 0,
                'message': 'Product variant not found'
            }
        
        stock = variant.get('stock', 0)
        
        return {
            'available': stock > 0,
            'stock': stock,
            'message': f"{stock} units available" if stock > 0 else "Out of stock"
        }
    
    def reserve_stock(self, product_id: str, variant_id: int, quantity: int = 1) -> Dict:
        """Reserve stock for purchase"""
        variant = self.get_product_variant(product_id, variant_id)
        
        if not variant:
            return {
                'success': False,
                'message': 'Product variant not found'
            }
        
        current_stock = variant.get('stock', 0)
        
        if current_stock < quantity:
            return {
                'success': False,
                'message': f'Insufficient stock. Only {current_stock} available.'
            }
        
        # In real implementation, this would update database
        # For now, we'll simulate stock reservation
        return {
            'success': True,
            'message': f'Stock reserved successfully',
            'reserved_quantity': quantity,
            'remaining_stock': current_stock - quantity
        }
    
    def get_catalog_stats(self) -> Dict:
        """Get catalog statistics for admin"""
        total_products = len(self.sample_products)
        active_products = len([p for p in self.sample_products if p.get('active', True)])
        
        total_variants = sum(len(p.get('variants', [])) for p in self.sample_products)
        in_stock_variants = sum(
            1 for p in self.sample_products 
            for v in p.get('variants', []) 
            if v.get('stock', 0) > 0
        )
        
        categories_with_products = len([
            cat for cat in self.default_categories 
            if len(self.get_products_by_category(cat['id'])) > 0
        ])
        
        # Calculate total inventory value
        total_value = sum(
            v.get('price', 0) * v.get('stock', 0)
            for p in self.sample_products
            for v in p.get('variants', [])
        )
        
        return {
            'total_products': total_products,
            'active_products': active_products,
            'total_variants': total_variants,
            'in_stock_variants': in_stock_variants,
            'out_of_stock_variants': total_variants - in_stock_variants,
            'categories_count': len(self.default_categories),
            'categories_with_products': categories_with_products,
            'total_inventory_value': total_value
        }
    
    def get_low_stock_alerts(self, threshold: int = 10) -> List[Dict]:
        """Get products with low stock"""
        low_stock = []
        
        for product in self.sample_products:
            for variant in product.get('variants', []):
                stock = variant.get('stock', 0)
                if 0 < stock <= threshold:
                    low_stock.append({
                        'product_name': product['name'],
                        'variant_name': variant['name'],
                        'current_stock': stock,
                        'price': variant.get('price', 0),
                        'category': self.get_category(product['category_id'])['name']
                    })
        
        return sorted(low_stock, key=lambda x: x['current_stock'])
    
    def calculate_variant_price(self, product_id: str, variant_id: int, quantity: int = 1) -> Dict:
        """Calculate total price for variant purchase"""
        variant = self.get_product_variant(product_id, variant_id)
        
        if not variant:
            return {
                'success': False,
                'message': 'Product variant not found'
            }
        
        unit_price = variant.get('price', 0)
        subtotal = unit_price * quantity
        
        # Apply quantity discounts
        discount_percent = 0
        if quantity >= 10:
            discount_percent = 10
        elif quantity >= 5:
            discount_percent = 5
        
        discount_amount = subtotal * (discount_percent / 100)
        total = subtotal - discount_amount
        
        return {
            'success': True,
            'unit_price': unit_price,
            'quantity': quantity,
            'subtotal': subtotal,
            'discount_percent': discount_percent,
            'discount_amount': discount_amount,
            'total': total,
            'variant_name': variant['name'],
            'features': variant.get('features', [])
        }

class StockManagement:
    """Handle stock management operations"""
    
    def __init__(self):
        self.data_manager = SimpleDataManager()
    
    def update_stock(self, product_id: str, variant_id: int, new_stock: int, admin_user: str) -> Dict:
        """Update stock level for a product variant"""
        try:
            # In real implementation, update database
            result = self.data_manager.update_variant_stock(product_id, variant_id, new_stock)
            
            if result:
                return {
                    'success': True,
                    'message': f'Stock updated to {new_stock} units',
                    'new_stock': new_stock
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to update stock'
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Error updating stock: {str(e)}'
            }
    
    def add_stock(self, product_id: str, variant_id: int, add_quantity: int, admin_user: str) -> Dict:
        """Add stock to existing inventory"""
        # Get current stock
        catalog = ProductCatalogSystem()
        variant = catalog.get_product_variant(product_id, variant_id)
        
        if not variant:
            return {
                'success': False,
                'message': 'Product variant not found'
            }
        
        current_stock = variant.get('stock', 0)
        new_stock = current_stock + add_quantity
        
        return self.update_stock(product_id, variant_id, new_stock, admin_user)
    
    def process_sale(self, product_id: str, variant_id: int, quantity: int = 1) -> Dict:
        """Process a sale and reduce stock"""
        try:
            catalog = ProductCatalogSystem()
            variant = catalog.get_product_variant(product_id, variant_id)
            
            if not variant:
                return {
                    'success': False,
                    'message': 'Product variant not found'
                }
            
            current_stock = variant.get('stock', 0)
            
            if current_stock < quantity:
                return {
                    'success': False,
                    'message': f'Insufficient stock. Only {current_stock} available.'
                }
            
            new_stock = current_stock - quantity
            
            # Update stock (in real implementation)
            result = self.data_manager.update_variant_stock(product_id, variant_id, new_stock)
            
            if result:
                # Record sale
                self.data_manager.record_product_sale(
                    product_id=product_id,
                    variant_id=variant_id,
                    quantity=quantity,
                    price=variant.get('price', 0)
                )
                
                return {
                    'success': True,
                    'message': f'Sale processed. Stock reduced by {quantity}',
                    'new_stock': new_stock,
                    'sold_quantity': quantity
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to update stock'
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Error processing sale: {str(e)}'
            }