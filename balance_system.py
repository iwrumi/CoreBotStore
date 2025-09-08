"""
User Balance and Credit System
Handles user deposits, balance management, and spending tracking
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from advanced_data_manager import AdvancedDataManager

class BalanceSystem:
    def __init__(self):
        self.data_manager = AdvancedDataManager()
    
    def get_user_balance(self, user_telegram_id: str) -> Dict:
        """Get user's current balance and spending history"""
        user = self.data_manager.get_or_create_user(user_telegram_id)
        
        return {
            'balance': user.get('balance', 0.0),
            'total_deposited': user.get('total_deposited', 0.0),
            'total_spent': user.get('total_spent', 0.0),
            'pending_deposits': self._get_pending_deposits(user_telegram_id)
        }
    
    def create_manual_deposit(self, 
                            user_telegram_id: str, 
                            amount: float, 
                            payment_method: str = 'gcash') -> Dict:
        """Create a manual deposit request"""
        
        if amount < 20:
            return {
                'success': False,
                'message': 'Minimum deposit is ₱20'
            }
        
        if amount > 10000:
            return {
                'success': False,
                'message': 'Maximum deposit is ₱10,000'
            }
        
        try:
            # Generate deposit ID
            deposit_id = len(self.data_manager.get_deposits()) + 1
            
            # Create deposit record
            deposit = self.data_manager.create_deposit(
                user_telegram_id=user_telegram_id,
                deposit_id=str(deposit_id),
                amount=amount,
                payment_method=payment_method,
                status='pending'
            )
            
            if deposit:
                return {
                    'success': True,
                    'deposit': deposit,
                    'qr_code_data': self._generate_payment_qr(amount, deposit_id, payment_method),
                    'message': f'Manual deposit #{deposit_id} created successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to create deposit'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error creating deposit: {str(e)}'
            }
    
    def _generate_payment_qr(self, amount: float, deposit_id: int, method: str) -> Dict:
        """Generate payment QR code data"""
        
        # In real implementation, integrate with actual payment providers
        qr_data = {
            'method': method,
            'amount': amount,
            'deposit_id': deposit_id,
            'reference': f"DEP{deposit_id:04d}",
            'instructions': self._get_payment_instructions(method, amount)
        }
        
        return qr_data
    
    def _get_payment_instructions(self, method: str, amount: float) -> str:
        """Get payment instructions for different methods"""
        
        instructions = {
            'gcash': f"""
**GCash Payment Instructions:**

1. Open your GCash app
2. Scan the QR code above
3. Pay exactly ₱{amount:.2f}
4. Take a screenshot of the receipt
5. Upload the proof using the button below

**Important:**
• Pay the EXACT amount shown
• Take a clear screenshot
• Upload within 30 minutes
            """,
            'paymaya': f"""
**PayMaya Payment Instructions:**

1. Open your PayMaya app
2. Scan the QR code above
3. Pay exactly ₱{amount:.2f}
4. Screenshot the confirmation
5. Upload proof using the button below

**Note:** Processing takes 1-5 minutes
            """,
            'instapay': f"""
**InstaPay Instructions:**

1. Use any InstaPay-enabled app
2. Scan the QR code
3. Send exactly ₱{amount:.2f}
4. Save the transaction receipt
5. Upload proof below

**Supported Apps:**
• GCash • PayMaya • UnionBank • BPI • etc.
            """
        }
        
        return instructions.get(method, f"Pay exactly ₱{amount:.2f} and upload proof")
    
    def submit_deposit_proof(self, deposit_id: str, user_telegram_id: str) -> Dict:
        """Process deposit proof submission"""
        
        try:
            # Update deposit status to proof_submitted
            result = self.data_manager.update_deposit_status(
                deposit_id, 
                'proof_submitted',
                f'Proof submitted by user {user_telegram_id}'
            )
            
            if result:
                # In real implementation, this would trigger admin notification
                return {
                    'success': True,
                    'message': f'Proof submitted for deposit #{deposit_id}. Your deposit is being verified and will be processed within 5 minutes.',
                    'estimated_time': '5 minutes'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to submit proof'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error submitting proof: {str(e)}'
            }
    
    def approve_deposit(self, deposit_id: str, admin_user: str) -> Dict:
        """Approve a deposit and add to user balance"""
        
        try:
            # Get deposit details
            deposits = self.data_manager.get_deposits()
            deposit = next((d for d in deposits if d['deposit_id'] == deposit_id), None)
            
            if not deposit:
                return {
                    'success': False,
                    'message': 'Deposit not found'
                }
            
            if deposit['status'] == 'completed':
                return {
                    'success': False,
                    'message': 'Deposit already approved'
                }
            
            # Update deposit status
            self.data_manager.update_deposit_status(
                deposit_id,
                'completed',
                f'Approved by {admin_user}'
            )
            
            # Add to user balance
            user_telegram_id = deposit['user_telegram_id']
            amount = float(deposit['amount'])
            
            # Update user balance and totals
            user = self.data_manager.get_or_create_user(user_telegram_id)
            current_balance = user.get('balance', 0.0)
            total_deposited = user.get('total_deposited', 0.0)
            
            self.data_manager.update_user_balance(
                user_telegram_id,
                current_balance + amount,
                total_deposited + amount
            )
            
            return {
                'success': True,
                'message': f'Deposit #{deposit_id} approved. ₱{amount:.2f} added to user balance.',
                'new_balance': current_balance + amount,
                'deposit': deposit
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error approving deposit: {str(e)}'
            }
    
    def spend_balance(self, user_telegram_id: str, amount: float, description: str = 'Purchase') -> Dict:
        """Spend from user balance"""
        
        try:
            user = self.data_manager.get_or_create_user(user_telegram_id)
            current_balance = user.get('balance', 0.0)
            
            if current_balance < amount:
                return {
                    'success': False,
                    'message': f'Insufficient balance. You have ₱{current_balance:.2f}, need ₱{amount:.2f}',
                    'current_balance': current_balance,
                    'required': amount,
                    'shortfall': amount - current_balance
                }
            
            # Deduct from balance
            new_balance = current_balance - amount
            total_spent = user.get('total_spent', 0.0) + amount
            
            # Update user
            self.data_manager.update_user_spending(
                user_telegram_id,
                new_balance,
                total_spent
            )
            
            # Record transaction
            self.data_manager.create_balance_transaction(
                user_telegram_id=user_telegram_id,
                amount=-amount,
                transaction_type='spend',
                description=description,
                balance_after=new_balance
            )
            
            return {
                'success': True,
                'message': f'₱{amount:.2f} spent successfully',
                'new_balance': new_balance,
                'amount_spent': amount
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error spending balance: {str(e)}'
            }
    
    def get_deposit_history(self, user_telegram_id: str, limit: int = 10) -> List[Dict]:
        """Get user's deposit history"""
        
        all_deposits = self.data_manager.get_deposits()
        user_deposits = [
            d for d in all_deposits 
            if d['user_telegram_id'] == user_telegram_id
        ]
        
        # Sort by date (newest first)
        user_deposits.sort(key=lambda x: x['created_at'], reverse=True)
        
        return user_deposits[:limit]
    
    def get_transaction_history(self, user_telegram_id: str, limit: int = 20) -> List[Dict]:
        """Get user's balance transaction history"""
        
        transactions = self.data_manager.get_balance_transactions(user_telegram_id)
        
        # Sort by date (newest first)
        transactions.sort(key=lambda x: x['created_at'], reverse=True)
        
        return transactions[:limit]
    
    def _get_pending_deposits(self, user_telegram_id: str) -> List[Dict]:
        """Get user's pending deposits"""
        
        all_deposits = self.data_manager.get_deposits()
        pending = [
            d for d in all_deposits 
            if d['user_telegram_id'] == user_telegram_id 
            and d['status'] in ['pending', 'proof_submitted']
        ]
        
        return pending
    
    def get_balance_analytics(self) -> Dict:
        """Get balance system analytics for admin"""
        
        deposits = self.data_manager.get_deposits()
        users = self.data_manager.get_users()
        
        # Calculate metrics
        total_deposits = sum(float(d['amount']) for d in deposits if d['status'] == 'completed')
        pending_deposits = [d for d in deposits if d['status'] in ['pending', 'proof_submitted']]
        pending_amount = sum(float(d['amount']) for d in pending_deposits)
        
        # User balance stats
        total_user_balance = sum(float(u.get('balance', 0)) for u in users)
        avg_user_balance = total_user_balance / len(users) if users else 0
        
        # Top users by balance
        top_users = sorted(users, key=lambda x: x.get('balance', 0), reverse=True)[:10]
        
        return {
            'total_deposits': total_deposits,
            'pending_deposits_count': len(pending_deposits),
            'pending_deposits_amount': pending_amount,
            'total_user_balance': total_user_balance,
            'avg_user_balance': avg_user_balance,
            'active_users_with_balance': len([u for u in users if u.get('balance', 0) > 0]),
            'top_users': [{
                'telegram_id': u['telegram_id'],
                'first_name': u.get('first_name', 'Unknown'),
                'balance': u.get('balance', 0),
                'total_deposited': u.get('total_deposited', 0)
            } for u in top_users[:5]]
        }
    
    def get_suggested_amounts(self) -> List[int]:
        """Get suggested top-up amounts"""
        return [20, 50, 100, 200, 500, 1000]
    
    def validate_deposit_amount(self, amount: float) -> Dict:
        """Validate deposit amount"""
        
        if amount < 20:
            return {
                'valid': False,
                'message': 'Minimum deposit is ₱20'
            }
        
        if amount > 10000:
            return {
                'valid': False,
                'message': 'Maximum deposit is ₱10,000'
            }
        
        if amount % 1 != 0:
            return {
                'valid': False,
                'message': 'Please enter whole numbers only'
            }
        
        return {
            'valid': True,
            'message': 'Amount is valid'
        }

class DepositNotifications:
    """Handle deposit-related notifications"""
    
    def __init__(self, bot_token):
        self.bot_token = bot_token
    
    async def notify_deposit_created(self, user_telegram_id: str, deposit: Dict):
        """Notify user about deposit creation"""
        try:
            from telegram import Bot
            bot = Bot(token=self.bot_token)
            
            message = f"""
💳 **Manual Deposit Created**

**Deposit ID:** #{deposit['deposit_id']}
**Amount:** ₱{deposit['amount']:.2f}
**Method:** {deposit['payment_method'].title()}
**Status:** Pending Payment

⏰ **Next Steps:**
1. Make payment using the QR code
2. Upload payment proof
3. Wait for verification (5 minutes)

**Important:** Upload proof within 30 minutes to avoid cancellation.
            """
            
            await bot.send_message(
                chat_id=user_telegram_id,
                text=message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            print(f"Error sending deposit notification: {e}")
    
    async def notify_deposit_approved(self, user_telegram_id: str, deposit: Dict, new_balance: float):
        """Notify user about deposit approval"""
        try:
            from telegram import Bot
            bot = Bot(token=self.bot_token)
            
            message = f"""
✅ **Deposit Approved!**

**Deposit #{deposit['deposit_id']} has been approved.**

💰 **Balance Updated:**
• Deposited: ₱{deposit['amount']:.2f}
• New Balance: ₱{new_balance:.2f}

🛍️ You can now use your balance to make purchases!

Thank you for your deposit! 🙏
            """
            
            await bot.send_message(
                chat_id=user_telegram_id,
                text=message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            print(f"Error sending approval notification: {e}")
    
    async def notify_admin_new_deposit(self, deposit: Dict):
        """Notify admin about new deposit needing verification"""
        # This would send to admin channel or specific admin users
        admin_message = f"""
🔔 **New Deposit Proof Submitted**

**Deposit ID:** #{deposit['deposit_id']}
**User:** {deposit['user_telegram_id']}
**Amount:** ₱{deposit['amount']:.2f}
**Method:** {deposit['payment_method'].title()}
**Status:** Proof Submitted

Please verify and approve the deposit.
        """
        
        # Implementation would send to admin notification system
        print(f"Admin notification: {admin_message}")
        return True