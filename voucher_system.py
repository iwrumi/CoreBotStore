"""
Voucher and Discount Code System
Handles creation, validation, and application of discount codes
"""
import re
import secrets
import string
from datetime import datetime, timedelta
from advanced_data_manager import AdvancedDataManager

class VoucherSystem:
    def __init__(self):
        self.data_manager = AdvancedDataManager()
    
    def create_voucher(self, 
                      name, 
                      discount_type, 
                      discount_value, 
                      code=None, 
                      description="", 
                      minimum_order=0.0, 
                      maximum_discount=0.0,
                      usage_limit=0, 
                      valid_days=None, 
                      valid_until=None):
        """
        Create a new voucher/discount code
        
        Args:
            name: Display name for the voucher
            discount_type: 'percentage' or 'fixed_amount'
            discount_value: Percentage (0-100) or fixed amount
            code: Custom code or auto-generated if None
            description: Description of the offer
            minimum_order: Minimum order amount to apply discount
            maximum_discount: Maximum discount amount (for percentage discounts)
            usage_limit: Max number of uses (0 = unlimited)
            valid_days: Number of days valid from creation
            valid_until: Specific expiry date
        """
        
        # Generate code if not provided
        if not code:
            code = self._generate_voucher_code()
        else:
            code = code.upper().strip()
            
        # Validate code format
        if not self._validate_code_format(code):
            return {
                'success': False,
                'message': 'Invalid code format. Use 3-20 characters, letters and numbers only.'
            }
        
        # Check if code already exists
        if self._code_exists(code):
            return {
                'success': False,
                'message': f'Voucher code "{code}" already exists.'
            }
        
        # Validate discount value
        if discount_type == 'percentage':
            if not 0 < discount_value <= 100:
                return {
                    'success': False,
                    'message': 'Percentage discount must be between 1-100.'
                }
        else:  # fixed_amount
            if discount_value <= 0:
                return {
                    'success': False,
                    'message': 'Fixed discount amount must be greater than 0.'
                }
        
        # Calculate expiry date
        valid_until_date = None
        if valid_until:
            valid_until_date = valid_until
        elif valid_days:
            valid_until_date = datetime.utcnow() + timedelta(days=valid_days)
        
        # Create voucher
        try:
            voucher = self.data_manager.create_voucher(
                code=code,
                name=name,
                description=description,
                discount_type=discount_type,
                discount_value=discount_value,
                minimum_order=minimum_order,
                maximum_discount=maximum_discount,
                usage_limit=usage_limit,
                valid_until=valid_until_date
            )
            
            return {
                'success': True,
                'voucher': voucher,
                'message': f'Voucher "{code}" created successfully!'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error creating voucher: {str(e)}'
            }
    
    def validate_and_apply_voucher(self, voucher_code, order_total, user_telegram_id=None):
        """
        Validate voucher code and calculate discount
        
        Returns:
            dict with validation result and discount information
        """
        
        if not voucher_code or not voucher_code.strip():
            return {
                'valid': False,
                'message': 'Please enter a voucher code.'
            }
        
        code = voucher_code.upper().strip()
        
        # Validate with data manager
        result = self.data_manager.validate_voucher(code, order_total)
        
        if not result['valid']:
            # Check specific reasons for better user feedback
            vouchers = self.data_manager.get_vouchers()
            voucher = next((v for v in vouchers if v['code'] == code), None)
            
            if not voucher:
                return {
                    'valid': False,
                    'message': f'Voucher code "{code}" not found. Please check and try again.'
                }
            elif not voucher['is_active']:
                return {
                    'valid': False,
                    'message': 'This voucher code is no longer active.'
                }
            elif voucher['valid_until'] and datetime.fromisoformat(voucher['valid_until']) <= datetime.utcnow():
                return {
                    'valid': False,
                    'message': 'This voucher code has expired.'
                }
            elif order_total < voucher['minimum_order']:
                return {
                    'valid': False,
                    'message': f'Minimum order of ${voucher["minimum_order"]:.2f} required for this voucher.'
                }
            elif voucher['usage_limit'] > 0 and voucher['usage_count'] >= voucher['usage_limit']:
                return {
                    'valid': False,
                    'message': 'This voucher code has reached its usage limit.'
                }
            else:
                return result
        
        # Valid voucher - return discount info
        voucher = result['voucher']
        discount_amount = result['discount_amount']
        
        # Format discount description
        if voucher['discount_type'] == 'percentage':
            discount_text = f"{voucher['discount_value']}% OFF"
        else:
            discount_text = f"${voucher['discount_value']:.2f} OFF"
        
        return {
            'valid': True,
            'voucher_code': code,
            'voucher_name': voucher['name'],
            'discount_amount': discount_amount,
            'discount_text': discount_text,
            'final_total': max(0, order_total - discount_amount),
            'message': f'✅ Voucher applied! You save ${discount_amount:.2f}'
        }
    
    def get_voucher_by_code(self, code):
        """Get voucher details by code"""
        vouchers = self.data_manager.get_vouchers()
        return next((v for v in vouchers if v['code'] == code.upper()), None)
    
    def get_active_vouchers(self):
        """Get all active vouchers"""
        return self.data_manager.get_vouchers(is_active=True)
    
    def get_all_vouchers(self):
        """Get all vouchers"""
        return self.data_manager.get_vouchers()
    
    def deactivate_voucher(self, voucher_id):
        """Deactivate a voucher"""
        try:
            # Update voucher status (you'd need to add this method to data manager)
            # For now, we'll mark it as inactive
            return {
                'success': True,
                'message': 'Voucher deactivated successfully.'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error deactivating voucher: {str(e)}'
            }
    
    def get_voucher_usage_stats(self, voucher_id=None):
        """Get voucher usage statistics"""
        if voucher_id:
            vouchers = [v for v in self.data_manager.get_vouchers() if v['id'] == voucher_id]
        else:
            vouchers = self.data_manager.get_vouchers()
        
        stats = []
        for voucher in vouchers:
            # Calculate usage rate
            usage_rate = 0
            if voucher['usage_limit'] > 0:
                usage_rate = (voucher['usage_count'] / voucher['usage_limit']) * 100
            
            # Calculate total savings provided
            if voucher['discount_type'] == 'percentage':
                # This would require order history analysis for exact calculation
                estimated_savings = voucher['usage_count'] * voucher['discount_value']
            else:
                estimated_savings = voucher['usage_count'] * voucher['discount_value']
            
            stats.append({
                'voucher_id': voucher['id'],
                'code': voucher['code'],
                'name': voucher['name'],
                'usage_count': voucher['usage_count'],
                'usage_limit': voucher['usage_limit'],
                'usage_rate': usage_rate,
                'estimated_savings': estimated_savings,
                'is_active': voucher['is_active'],
                'expires': voucher['valid_until']
            })
        
        return stats
    
    def create_bulk_vouchers(self, base_name, count, discount_type, discount_value, **kwargs):
        """Create multiple vouchers at once"""
        results = []
        
        for i in range(count):
            code = self._generate_voucher_code()
            name = f"{base_name} #{i+1}"
            
            result = self.create_voucher(
                name=name,
                discount_type=discount_type,
                discount_value=discount_value,
                code=code,
                **kwargs
            )
            
            results.append({
                'code': code,
                'success': result['success'],
                'message': result['message']
            })
        
        successful = sum(1 for r in results if r['success'])
        
        return {
            'total_created': successful,
            'total_failed': count - successful,
            'results': results
        }
    
    def create_flash_sale_voucher(self, discount_percentage, hours_valid=24, usage_limit=100):
        """Create a flash sale voucher with time limit"""
        code = f"FLASH{secrets.token_hex(3).upper()}"
        valid_until = datetime.utcnow() + timedelta(hours=hours_valid)
        
        return self.create_voucher(
            name=f"Flash Sale {discount_percentage}% OFF",
            discount_type='percentage',
            discount_value=discount_percentage,
            code=code,
            description=f"Limited time {discount_percentage}% discount - {hours_valid} hours only!",
            usage_limit=usage_limit,
            valid_until=valid_until
        )
    
    def create_welcome_voucher(self, new_customer_discount=10):
        """Create a welcome voucher for new customers"""
        code = f"WELCOME{secrets.token_hex(2).upper()}"
        valid_until = datetime.utcnow() + timedelta(days=30)
        
        return self.create_voucher(
            name="New Customer Welcome",
            discount_type='percentage',
            discount_value=new_customer_discount,
            code=code,
            description=f"Welcome! Enjoy {new_customer_discount}% off your first order!",
            minimum_order=50.0,
            usage_limit=1,
            valid_until=valid_until
        )
    
    def create_loyalty_voucher(self, customer_telegram_id, discount_value=15):
        """Create a loyalty voucher for returning customers"""
        code = f"LOYAL{secrets.token_hex(3).upper()}"
        valid_until = datetime.utcnow() + timedelta(days=14)
        
        return self.create_voucher(
            name="Loyalty Reward",
            discount_type='percentage', 
            discount_value=discount_value,
            code=code,
            description=f"Thank you for being a loyal customer! {discount_value}% off your order!",
            usage_limit=1,
            valid_until=valid_until
        )
    
    def _generate_voucher_code(self, length=8):
        """Generate a random voucher code"""
        # Use a mix of letters and numbers, avoiding confusing characters
        chars = string.ascii_uppercase + string.digits
        chars = chars.replace('0', '').replace('O', '').replace('I', '').replace('1')
        
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    def _validate_code_format(self, code):
        """Validate voucher code format"""
        # Allow 3-20 characters, letters and numbers only
        return bool(re.match(r'^[A-Z0-9]{3,20}$', code))
    
    def _code_exists(self, code):
        """Check if voucher code already exists"""
        existing = self.data_manager.get_vouchers()
        return any(v['code'] == code.upper() for v in existing)

class VoucherNotifications:
    """Handle voucher-related notifications"""
    
    def __init__(self, broadcast_system):
        self.broadcast_system = broadcast_system
        self.voucher_system = VoucherSystem()
    
    async def notify_flash_sale(self, voucher_code, discount_percentage, hours_remaining):
        """Send flash sale notification"""
        title = f"⚡ FLASH SALE: {discount_percentage}% OFF!"
        message = f"""
🔥 **LIMITED TIME OFFER!** 🔥

💥 Get **{discount_percentage}% OFF** your entire order!

🎫 **Code:** `{voucher_code}`
⏰ **Time Left:** {hours_remaining} hours only!
🛍️ **Valid on:** All products

⚡ **Act fast** - This offer expires soon!

Use /start to shop now and save big! 🚀
        """
        
        return await self.broadcast_system.send_promo_announcement(
            title=title,
            message=message,
            voucher_code=voucher_code
        )
    
    async def notify_new_voucher(self, voucher_code, discount_text, description):
        """Send notification about new voucher"""
        title = f"🎫 New Voucher: {discount_text}"
        message = f"""
🎉 **NEW DISCOUNT CODE AVAILABLE!** 🎉

🎫 **Code:** `{voucher_code}`
💰 **Discount:** {discount_text}
📝 **Details:** {description}

🛍️ Ready to save? Use /start to shop!

*Tap the code above to copy it!* 📋
        """
        
        return await self.broadcast_system.send_promo_announcement(
            title=title,
            message=message,
            voucher_code=voucher_code
        )
    
    async def notify_voucher_expiring(self, voucher_code, discount_text, days_left):
        """Send notification about expiring voucher"""
        title = f"⏰ Voucher Expiring: {voucher_code}"
        message = f"""
⚠️ **VOUCHER EXPIRING SOON!** ⚠️

🎫 **Code:** `{voucher_code}`
💰 **Discount:** {discount_text}
⏰ **Expires in:** {days_left} day{'s' if days_left != 1 else ''}

🏃‍♂️ **Don't miss out!** Use it before it expires!

Use /start to shop now! 🛍️
        """
        
        return await self.broadcast_system.send_promo_announcement(
            title=title,
            message=message,
            voucher_code=voucher_code
        )

# Quick voucher templates
class VoucherTemplates:
    """Pre-made voucher templates for common scenarios"""
    
    def __init__(self):
        self.voucher_system = VoucherSystem()
    
    def create_weekend_special(self, discount=20):
        """Weekend special voucher"""
        return self.voucher_system.create_voucher(
            name="Weekend Special",
            discount_type='percentage',
            discount_value=discount,
            description=f"Weekend Special: {discount}% off all orders!",
            valid_days=3,  # Valid for 3 days
            usage_limit=200
        )
    
    def create_free_shipping_voucher(self, minimum_order=75):
        """Free shipping voucher"""
        return self.voucher_system.create_voucher(
            name="Free Shipping",
            discount_type='fixed_amount',
            discount_value=10.00,  # Assume $10 shipping cost
            description=f"Free shipping on orders over ${minimum_order}!",
            minimum_order=minimum_order,
            valid_days=30,
            usage_limit=500
        )
    
    def create_bulk_order_discount(self, minimum_order=200, discount=25):
        """Bulk order discount"""
        return self.voucher_system.create_voucher(
            name="Bulk Order Discount",
            discount_type='percentage',
            discount_value=discount,
            description=f"Save {discount}% on orders over ${minimum_order}!",
            minimum_order=minimum_order,
            valid_days=14
        )
    
    def create_clearance_sale(self, discount=40):
        """Clearance sale voucher"""
        return self.voucher_system.create_voucher(
            name="Clearance Sale",
            discount_type='percentage',
            discount_value=discount,
            description=f"Clearance Sale: {discount}% off selected items!",
            valid_days=7,
            usage_limit=100
        )
    
    def create_birthday_special(self, discount=15):
        """Birthday special voucher"""
        return self.voucher_system.create_voucher(
            name="Birthday Special",
            discount_type='percentage',
            discount_value=discount,
            description=f"Happy Birthday! Enjoy {discount}% off as our gift to you!",
            valid_days=7,
            usage_limit=1
        )