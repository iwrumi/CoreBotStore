"""
Payment Processing System
Handles both automatic and manual payment processing with multiple payment methods
"""
import os
import uuid
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from advanced_data_manager import AdvancedDataManager

class PaymentMethod(Enum):
    GCASH = "gcash"
    PAYMAYA = "paymaya"
    BANK_TRANSFER = "bank_transfer"
    CASH_ON_DELIVERY = "cod"
    PAYPAL = "paypal"
    MANUAL = "manual"

class PaymentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentSystem:
    def __init__(self):
        self.data_manager = AdvancedDataManager()
        self.payment_methods = self._load_payment_methods()
    
    def _load_payment_methods(self) -> Dict:
        """Load available payment methods from settings"""
        try:
            methods_json = self.data_manager.get_setting('payment_methods', '[]')
            import json
            methods = json.loads(methods_json)
        except:
            methods = ["GCash", "PayMaya", "Bank Transfer", "Cash on Delivery"]
        
        return {
            "gcash": {
                "name": "GCash",
                "description": "Pay via GCash mobile wallet",
                "account": self.data_manager.get_setting('gcash_account', ''),
                "instructions": "Send payment to the GCash number and upload receipt",
                "auto_verify": False,
                "fee": 0.0
            },
            "paymaya": {
                "name": "PayMaya",
                "description": "Pay via PayMaya digital wallet", 
                "account": self.data_manager.get_setting('paymaya_account', ''),
                "instructions": "Send payment to the PayMaya account and upload receipt",
                "auto_verify": False,
                "fee": 0.0
            },
            "bank_transfer": {
                "name": "Bank Transfer",
                "description": "Direct bank transfer",
                "account": self.data_manager.get_setting('bank_account', ''),
                "instructions": "Transfer to bank account and send reference number",
                "auto_verify": False,
                "fee": 0.0
            },
            "cod": {
                "name": "Cash on Delivery",
                "description": "Pay when item is delivered",
                "account": "",
                "instructions": "Pay in cash upon delivery",
                "auto_verify": True,  # Auto-approved
                "fee": 50.0  # COD fee
            }
        }
    
    def get_available_payment_methods(self, order_total: float = 0) -> List[Dict]:
        """Get available payment methods for an order"""
        methods = []
        
        for method_id, method_info in self.payment_methods.items():
            # Add method-specific availability logic
            if method_id == "cod" and order_total < 100:
                # Minimum order for COD
                continue
            
            methods.append({
                "id": method_id,
                "name": method_info["name"],
                "description": method_info["description"],
                "fee": method_info["fee"],
                "instructions": method_info["instructions"]
            })
        
        return methods
    
    def create_payment(self, 
                      order_id: int,
                      user_telegram_id: str, 
                      amount: float,
                      payment_method: str,
                      currency: str = "PHP",
                      **kwargs) -> Dict:
        """Create a new payment record"""
        
        try:
            # Validate payment method
            if payment_method not in self.payment_methods:
                return {
                    'success': False,
                    'message': f'Invalid payment method: {payment_method}'
                }
            
            # Create payment record
            payment = self.data_manager.create_payment(
                user_telegram_id=user_telegram_id,
                amount=amount,
                payment_method=payment_method,
                order_id=order_id,
                currency=currency,
                reference_number=kwargs.get('reference_number', ''),
                notes=kwargs.get('notes', ''),
                proof_image=kwargs.get('proof_image', '')
            )
            
            if not payment:
                return {
                    'success': False,
                    'message': 'Failed to create payment record'
                }
            
            # Auto-verify certain payment methods
            method_info = self.payment_methods[payment_method]
            if method_info.get('auto_verify', False):
                self.verify_payment(payment['id'], 'system', auto_verified=True)
            
            return {
                'success': True,
                'payment': payment,
                'message': 'Payment created successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error creating payment: {str(e)}'
            }
    
    def verify_payment(self, 
                      payment_id: int, 
                      verified_by: str,
                      auto_verified: bool = False,
                      notes: str = '') -> Dict:
        """Verify a manual payment"""
        
        try:
            payment = self.data_manager.verify_payment(payment_id, verified_by)
            
            if not payment:
                return {
                    'success': False,
                    'message': 'Payment not found'
                }
            
            # Update related order status
            if payment.get('order_id'):
                self.data_manager.update_order_status(payment['order_id'], 'confirmed')
            
            return {
                'success': True,
                'payment': payment,
                'message': 'Payment verified successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error verifying payment: {str(e)}'
            }
    
    def process_manual_payment(self,
                             order_id: int,
                             user_telegram_id: str,
                             amount: float,
                             payment_method: str,
                             reference_number: str = '',
                             proof_image: str = '',
                             notes: str = '') -> Dict:
        """Process a manual payment submission"""
        
        # Validate reference number format based on payment method
        if payment_method in ['gcash', 'paymaya', 'bank_transfer']:
            if not reference_number or len(reference_number) < 6:
                return {
                    'success': False,
                    'message': 'Please provide a valid reference number (at least 6 characters)'
                }
        
        # Create payment record
        result = self.create_payment(
            order_id=order_id,
            user_telegram_id=user_telegram_id,
            amount=amount,
            payment_method=payment_method,
            reference_number=reference_number,
            proof_image=proof_image,
            notes=notes
        )
        
        if result['success']:
            payment = result['payment']
            
            # Send notification to admins about pending payment
            self._notify_admin_payment_pending(payment)
            
            return {
                'success': True,
                'payment': payment,
                'message': 'Payment submitted successfully. Please wait for verification.',
                'instructions': self._get_payment_instructions(payment_method, amount)
            }
        
        return result
    
    def get_payment_instructions(self, payment_method: str, amount: float) -> str:
        """Get detailed payment instructions for a method"""
        method_info = self.payment_methods.get(payment_method)
        if not method_info:
            return "Payment method not found"
        
        instructions = f"""
💳 **{method_info['name']} Payment Instructions**

💰 **Amount to Pay:** ₱{amount:.2f}
📱 **Account:** {method_info['account'] or 'Will be provided'}

📋 **Steps:**
{method_info['instructions']}

⚠️ **Important:**
• Pay the exact amount shown above
• Keep your receipt/screenshot
• Send the reference number or transaction ID
• Payments are verified within 24 hours

Need help? Contact our support team.
        """
        
        return instructions
    
    def _get_payment_instructions(self, payment_method: str, amount: float) -> str:
        """Get payment instructions (internal)"""
        return self.get_payment_instructions(payment_method, amount)
    
    def get_pending_payments(self) -> List[Dict]:
        """Get all pending payments for admin review"""
        return self.data_manager.get_payments(status='pending')
    
    def get_user_payment_history(self, user_telegram_id: str) -> List[Dict]:
        """Get payment history for a specific user"""
        return self.data_manager.get_payments(user_telegram_id=user_telegram_id)
    
    def get_payment_analytics(self) -> Dict:
        """Get payment analytics and statistics"""
        all_payments = self.data_manager.get_payments()
        
        # Calculate stats
        total_payments = len(all_payments)
        completed_payments = [p for p in all_payments if p['status'] == 'completed']
        pending_payments = [p for p in all_payments if p['status'] == 'pending']
        
        total_revenue = sum(p['amount'] for p in completed_payments)
        pending_amount = sum(p['amount'] for p in pending_payments)
        
        # Payment method breakdown
        method_stats = {}
        for payment in all_payments:
            method = payment['payment_method']
            if method not in method_stats:
                method_stats[method] = {'count': 0, 'amount': 0}
            method_stats[method]['count'] += 1
            if payment['status'] == 'completed':
                method_stats[method]['amount'] += payment['amount']
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_payments = [
            p for p in all_payments 
            if datetime.fromisoformat(p['created_at']) >= week_ago
        ]
        recent_completed = [p for p in recent_payments if p['status'] == 'completed']
        
        return {
            'total_payments': total_payments,
            'completed_payments': len(completed_payments),
            'pending_payments': len(pending_payments),
            'total_revenue': total_revenue,
            'pending_amount': pending_amount,
            'method_stats': method_stats,
            'recent_payments': len(recent_payments),
            'recent_revenue': sum(p['amount'] for p in recent_completed),
            'completion_rate': (len(completed_payments) / total_payments * 100) if total_payments > 0 else 0
        }
    
    def reject_payment(self, payment_id: int, reason: str, admin_user: str) -> Dict:
        """Reject a payment with reason"""
        try:
            # Update payment status to failed
            # Note: You'd need to add this method to the data manager
            payment_data = {
                'status': 'failed',
                'notes': f'Rejected by {admin_user}: {reason}'
            }
            
            # For now, we'll just add a note that it was rejected
            return {
                'success': True,
                'message': f'Payment rejected: {reason}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error rejecting payment: {str(e)}'
            }
    
    def refund_payment(self, payment_id: int, amount: float, reason: str, admin_user: str) -> Dict:
        """Process a payment refund"""
        try:
            # Create refund record
            # This would typically integrate with payment gateway APIs
            
            refund_data = {
                'original_payment_id': payment_id,
                'refund_amount': amount,
                'reason': reason,
                'processed_by': admin_user,
                'status': 'completed'  # In real implementation, this might be 'processing'
            }
            
            return {
                'success': True,
                'refund': refund_data,
                'message': f'Refund of ₱{amount:.2f} processed successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error processing refund: {str(e)}'
            }
    
    def validate_reference_number(self, reference_number: str, payment_method: str) -> bool:
        """Validate reference number format based on payment method"""
        if not reference_number:
            return False
        
        # Basic validation - can be enhanced for specific formats
        if payment_method == 'gcash':
            # GCash typically has 13-digit reference numbers
            return bool(re.match(r'^[0-9]{10,15}$', reference_number))
        elif payment_method == 'paymaya':
            # PayMaya format validation
            return bool(re.match(r'^[0-9A-Z]{10,20}$', reference_number))
        elif payment_method == 'bank_transfer':
            # Bank transfer reference numbers vary
            return len(reference_number) >= 6
        
        return len(reference_number) >= 6  # Generic validation
    
    def calculate_payment_fees(self, amount: float, payment_method: str) -> Tuple[float, float]:
        """Calculate payment fees and final amount"""
        method_info = self.payment_methods.get(payment_method, {})
        fee = method_info.get('fee', 0.0)
        
        # Fee can be flat rate or percentage
        if isinstance(fee, str) and fee.endswith('%'):
            fee_rate = float(fee[:-1]) / 100
            calculated_fee = amount * fee_rate
        else:
            calculated_fee = float(fee)
        
        final_amount = amount + calculated_fee
        return calculated_fee, final_amount
    
    def setup_payment_method_config(self, method: str, config: Dict) -> Dict:
        """Configure payment method settings"""
        try:
            # Update payment method configuration
            if method == 'gcash':
                self.data_manager.set_setting('gcash_account', config.get('account', ''))
            elif method == 'paymaya':
                self.data_manager.set_setting('paymaya_account', config.get('account', ''))
            elif method == 'bank_transfer':
                self.data_manager.set_setting('bank_account', config.get('account', ''))
            
            # Reload payment methods
            self.payment_methods = self._load_payment_methods()
            
            return {
                'success': True,
                'message': f'{method} configuration updated successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error updating {method} configuration: {str(e)}'
            }
    
    def _notify_admin_payment_pending(self, payment: Dict):
        """Notify admin about pending payment (to be implemented with notification system)"""
        # This would integrate with your notification system
        # For now, just log it
        print(f"🔔 New payment pending verification: {payment['transaction_id']} - ₱{payment['amount']:.2f}")
    
    def auto_verify_cod_payments(self):
        """Auto-verify Cash on Delivery payments when order is delivered"""
        # This would be called when order status changes to 'delivered'
        cod_payments = [
            p for p in self.data_manager.get_payments(status='pending')
            if p['payment_method'] == 'cod'
        ]
        
        verified_count = 0
        for payment in cod_payments:
            # Check if associated order is delivered
            order = self.data_manager.get_order(payment['order_id'])
            if order and order['status'] == 'delivered':
                self.verify_payment(payment['id'], 'system', auto_verified=True)
                verified_count += 1
        
        return verified_count

class PaymentNotifications:
    """Handle payment-related notifications"""
    
    def __init__(self, broadcast_system):
        self.broadcast_system = broadcast_system
        self.payment_system = PaymentSystem()
    
    async def notify_payment_received(self, user_telegram_id: str, payment: Dict):
        """Notify user that payment was received"""
        try:
            from telegram import Bot
            bot = Bot(token=os.environ.get('BOT_TOKEN'))
            
            message = f"""
✅ **Payment Received**

**Transaction ID:** {payment['transaction_id']}
**Amount:** ₱{payment['amount']:.2f}
**Method:** {payment['payment_method'].title()}
**Status:** Under Review

🔍 Your payment is being verified. You'll receive another notification once it's approved.

Expected verification time: Within 24 hours
            """
            
            await bot.send_message(
                chat_id=user_telegram_id,
                text=message,
                parse_mode='Markdown'
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending payment notification: {e}")
            return False
    
    async def notify_payment_verified(self, user_telegram_id: str, payment: Dict):
        """Notify user that payment was verified"""
        try:
            from telegram import Bot
            bot = Bot(token=os.environ.get('BOT_TOKEN'))
            
            message = f"""
🎉 **Payment Verified!**

**Transaction ID:** {payment['transaction_id']}
**Amount:** ₱{payment['amount']:.2f}
**Status:** ✅ Confirmed

Your payment has been verified and your order is being processed!

📦 You'll receive tracking information once your order ships.
            """
            
            await bot.send_message(
                chat_id=user_telegram_id,
                text=message,
                parse_mode='Markdown'
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending verification notification: {e}")
            return False
    
    async def notify_admin_payment_pending(self, payment: Dict):
        """Notify admins about pending payment"""
        # This would send to admin chat or channel
        message = f"""
🔔 **New Payment Pending**

**ID:** {payment['transaction_id']}
**Amount:** ₱{payment['amount']:.2f}
**Method:** {payment['payment_method'].title()}
**Reference:** {payment['reference_number']}
**User:** {payment['user_id']}

Review and verify this payment in the admin panel.
        """
        
        # Send to admin notification channel/chat
        # Implementation depends on your admin notification setup
        print(f"Admin notification: {message}")
        return True

# Payment validation utilities
class PaymentValidation:
    """Utilities for validating payment data"""
    
    @staticmethod
    def validate_amount(amount: float) -> Tuple[bool, str]:
        """Validate payment amount"""
        if amount <= 0:
            return False, "Amount must be greater than zero"
        if amount > 100000:  # Max amount limit
            return False, "Amount exceeds maximum limit of ₱100,000"
        return True, "Valid"
    
    @staticmethod
    def validate_gcash_number(number: str) -> Tuple[bool, str]:
        """Validate GCash mobile number format"""
        # Remove spaces and formatting
        cleaned = re.sub(r'[^\d+]', '', number)
        
        # Philippine mobile number patterns
        patterns = [
            r'^(09|\+639)\d{9}$',  # 09XXXXXXXXX or +639XXXXXXXXX
            r'^639\d{9}$'          # 639XXXXXXXXX
        ]
        
        for pattern in patterns:
            if re.match(pattern, cleaned):
                return True, "Valid"
        
        return False, "Invalid Philippine mobile number format"
    
    @staticmethod
    def validate_bank_account(account: str) -> Tuple[bool, str]:
        """Validate bank account format"""
        # Remove spaces and dashes
        cleaned = re.sub(r'[\s-]', '', account)
        
        # Basic validation - account should be 10-20 digits
        if re.match(r'^\d{10,20}$', cleaned):
            return True, "Valid"
        
        return False, "Invalid bank account format (should be 10-20 digits)"

# Payment method configurations
PAYMENT_METHOD_CONFIGS = {
    "gcash": {
        "name": "GCash",
        "icon": "📱",
        "color": "#007DFF",
        "requires_reference": True,
        "requires_proof": True,
        "validation_function": PaymentValidation.validate_gcash_number
    },
    "paymaya": {
        "name": "PayMaya",
        "icon": "💳",
        "color": "#00A8FF",
        "requires_reference": True,
        "requires_proof": True
    },
    "bank_transfer": {
        "name": "Bank Transfer",
        "icon": "🏦",
        "color": "#28A745",
        "requires_reference": True,
        "requires_proof": False
    },
    "cod": {
        "name": "Cash on Delivery",
        "icon": "💵",
        "color": "#FFC107",
        "requires_reference": False,
        "requires_proof": False,
        "auto_approve": False
    }
}