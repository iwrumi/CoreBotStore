"""
Customer Support System
Handles FAQs, help commands, support tickets, and automated assistance
"""
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from advanced_data_manager import AdvancedDataManager

class SupportTicketStatus:
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class SupportTicketPriority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class CustomerSupportSystem:
    def __init__(self):
        self.data_manager = AdvancedDataManager()
        self.faqs = self._load_default_faqs()
        self.quick_responses = self._load_quick_responses()
    
    def _load_default_faqs(self) -> Dict:
        """Load default FAQ categories and questions"""
        return {
            "ordering": {
                "category": "📦 Orders & Shopping",
                "icon": "📦",
                "questions": [
                    {
                        "q": "How do I place an order?",
                        "a": """
**Placing an order is easy!** 🛍️

1. Browse our catalog by tapping 'Browse Products'
2. Tap on items to view details
3. Click 'Add to Cart' for items you want
4. Go to your cart and review items
5. Proceed to checkout
6. Choose your payment method
7. Complete payment and wait for confirmation

Need help with any step? Just ask! 😊
                        """,
                        "keywords": ["order", "place order", "buy", "purchase", "how to order"]
                    },
                    {
                        "q": "Can I modify or cancel my order?",
                        "a": """
**Order Changes & Cancellations** ✏️

**Before Payment:**
• You can modify or cancel freely
• Just go back to your cart and make changes

**After Payment (within 1 hour):**
• Contact us immediately for changes
• We'll try our best to accommodate

**After Processing:**
• Orders being prepared cannot be modified
• Cancellation may incur fees
• Contact support for assistance

**Need help?** Use our support chat anytime! 💬
                        """,
                        "keywords": ["modify order", "cancel order", "change order", "edit order"]
                    },
                    {
                        "q": "How can I track my order?",
                        "a": """
**Order Tracking** 📍

**To track your order:**
1. Tap 'My Orders' from the main menu
2. Find your order and tap 'Track'
3. View real-time status updates

**Order Status Meanings:**
• 🔄 **Processing** - We're preparing your order
• 📦 **Packed** - Ready for pickup by courier
• 🚚 **Shipped** - On the way to you
• ✅ **Delivered** - Successfully delivered

**Delivery Time:**
• Metro Manila: 1-2 business days
• Provincial: 2-5 business days

Questions? We're here to help! 🤝
                        """,
                        "keywords": ["track", "tracking", "where is my order", "delivery", "shipping"]
                    }
                ]
            },
            "payments": {
                "category": "💳 Payments & Billing",
                "icon": "💳",
                "questions": [
                    {
                        "q": "What payment methods do you accept?",
                        "a": """
**Payment Methods We Accept** 💳

**Digital Wallets:**
• 📱 GCash
• 💳 PayMaya

**Bank Transfer:**
• 🏦 Direct bank transfer
• All major Philippine banks

**Cash Payment:**
• 💵 Cash on Delivery (COD)
• ₱50 COD fee applies

**Payment is Safe & Secure:**
• All transactions are encrypted
• Your financial data is protected
• Payment confirmation within 24 hours

Ready to pay? Choose what's convenient for you! ✅
                        """,
                        "keywords": ["payment", "pay", "gcash", "paymaya", "bank", "cod", "cash on delivery"]
                    },
                    {
                        "q": "How long does payment verification take?",
                        "a": """
**Payment Verification Times** ⏰

**Automatic (Instant):**
• Cash on Delivery orders
• Some supported payment methods

**Manual Verification:**
• GCash/PayMaya: 1-24 hours
• Bank Transfer: 1-24 hours
• Peak times may take longer

**To Speed Up Verification:**
• Upload clear payment receipt
• Include correct reference number
• Send during business hours (9 AM - 6 PM)

**Payment Confirmed?**
You'll get a notification immediately when verified! 🎉

**Questions?** Our support team is always ready to help! 💬
                        """,
                        "keywords": ["verification", "verify payment", "how long", "payment confirmation"]
                    }
                ]
            },
            "shipping": {
                "category": "🚚 Shipping & Delivery",
                "icon": "🚚",
                "questions": [
                    {
                        "q": "What are your delivery areas and rates?",
                        "a": """
**Delivery Coverage & Rates** 🚚

**Metro Manila:**
• Delivery: ₱80-120
• Time: 1-2 business days
• Free delivery on orders over ₱1,500

**Luzon:**
• Delivery: ₱120-200
• Time: 2-4 business days
• Free delivery on orders over ₱2,000

**Visayas & Mindanao:**
• Delivery: ₱150-300
• Time: 3-5 business days
• Free delivery on orders over ₱2,500

**Special Areas:**
• Remote locations may have additional fees
• Contact us for specific rates

**Free Delivery Promos Available!** 🎉
Check our current promotions for free shipping deals!
                        """,
                        "keywords": ["delivery", "shipping", "rates", "areas", "coverage", "free delivery"]
                    },
                    {
                        "q": "What if I'm not available during delivery?",
                        "a": """
**Missed Delivery? No Problem!** 📦

**Our Delivery Process:**
• Courier will call you before delivery
• You can reschedule if not available
• Safe drop-off options available

**Rescheduling:**
• Free reschedule within 3 days
• Just contact the courier directly
• Or message us for assistance

**Alternative Recipients:**
• You can authorize someone else
• Just inform us beforehand
• Valid ID required for verification

**Delivery Attempts:**
• We try 3 times to deliver
• After that, item returns to warehouse
• Reshipping fee may apply

**Need to reschedule?** Contact us anytime! 📞
                        """,
                        "keywords": ["missed delivery", "reschedule", "not available", "alternative recipient"]
                    }
                ]
            },
            "account": {
                "category": "👤 Account & Profile",
                "icon": "👤", 
                "questions": [
                    {
                        "q": "How do I update my delivery address?",
                        "a": """
**Update Delivery Address** 📍

**For Future Orders:**
• Tap 'Profile' or 'Account Settings'
• Select 'Delivery Address'
• Add or edit your addresses
• Set a default address

**For Current Orders:**
• Contact us immediately if not yet shipped
• Address changes after shipping not possible
• We'll help redirect if possible

**Multiple Addresses:**
• Save home, office, and other addresses
• Choose different address per order
• Label addresses for easy selection

**Address Format:**
Please include complete details:
• Full name of recipient
• Complete address with landmarks
• Contact number
• Special delivery instructions

Need help updating? We're here! 🤝
                        """,
                        "keywords": ["address", "delivery address", "update address", "change address"]
                    }
                ]
            },
            "general": {
                "category": "❓ General Information",
                "icon": "❓",
                "questions": [
                    {
                        "q": "What are your business hours?",
                        "a": """
**Business Hours** 🕐

**Customer Support:**
• Monday - Friday: 9:00 AM - 6:00 PM
• Saturday: 9:00 AM - 5:00 PM
• Sunday: Closed

**Order Processing:**
• Monday - Friday: Orders processed daily
• Saturday: Limited processing
• Sunday: No processing (orders queue for Monday)

**Payment Verification:**
• Automated: 24/7
• Manual verification: Business hours only

**Bot Available 24/7!** 🤖
This bot is always here to help you shop, even outside business hours!

**Need Urgent Help?**
For urgent concerns outside business hours, send a message and we'll respond first thing in the morning! 🌅
                        """,
                        "keywords": ["hours", "business hours", "operating hours", "when open"]
                    },
                    {
                        "q": "Do you offer returns and exchanges?",
                        "a": """
**Returns & Exchange Policy** 🔄

**Return Period:**
• 7 days from delivery
• Items must be unused and in original packaging
• Return shipping fee applies

**What Can Be Returned:**
✅ Defective or damaged items
✅ Wrong items sent
✅ Items not as described

**What Cannot Be Returned:**
❌ Used or opened items (unless defective)
❌ Custom/personalized items
❌ Items damaged by customer

**Return Process:**
1. Contact support within 7 days
2. Provide photos if claiming defect
3. Get return authorization number
4. Ship item back (or we'll arrange pickup)
5. Refund processed after inspection

**Exchanges:**
• Available for size/color variations
• Subject to stock availability
• Same return period applies

**Questions about returns?** Contact our support team! 💬
                        """,
                        "keywords": ["return", "exchange", "refund", "defective", "wrong item"]
                    }
                ]
            }
        }
    
    def _load_quick_responses(self) -> Dict:
        """Load quick response templates"""
        return {
            "greeting": [
                "👋 Hi there! How can I help you today?",
                "Hello! 😊 What can I assist you with?",
                "Hey! Thanks for reaching out. What's up?",
                "Hi! I'm here to help. What do you need?"
            ],
            "order_status": "To check your order status, please use the 'My Orders' option from the main menu or provide me your order number.",
            "payment_issue": "I understand payment issues can be frustrating. Let me help you resolve this quickly. Can you provide your payment reference number?",
            "delivery_delay": "I apologize for any delivery delays. Let me check the status of your order and provide you with an update.",
            "product_inquiry": "I'd be happy to help you with product information! Which item are you interested in?",
            "contact_human": "I'll connect you with our human support team. They'll get back to you within a few hours during business hours.",
            "thank_you": [
                "Thank you! Is there anything else I can help you with? 😊",
                "You're welcome! Let me know if you need anything else!",
                "Glad I could help! Feel free to ask if you have more questions.",
                "Anytime! I'm here whenever you need assistance! 🤝"
            ]
        }
    
    def search_faq(self, query: str, limit: int = 5) -> List[Dict]:
        """Search FAQ based on user query"""
        query_lower = query.lower()
        results = []
        
        for category_id, category_data in self.faqs.items():
            for faq in category_data["questions"]:
                # Check if query matches question, answer, or keywords
                score = 0
                
                # Check question title
                if query_lower in faq["q"].lower():
                    score += 10
                
                # Check keywords
                for keyword in faq["keywords"]:
                    if keyword.lower() in query_lower or query_lower in keyword.lower():
                        score += 5
                
                # Check answer content (lower weight)
                if query_lower in faq["a"].lower():
                    score += 2
                
                if score > 0:
                    results.append({
                        "category": category_data["category"],
                        "category_id": category_id,
                        "question": faq["q"],
                        "answer": faq["a"],
                        "score": score,
                        "keywords": faq["keywords"]
                    })
        
        # Sort by relevance score and return top results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def get_faq_categories(self) -> List[Dict]:
        """Get all FAQ categories"""
        categories = []
        for category_id, category_data in self.faqs.items():
            categories.append({
                "id": category_id,
                "name": category_data["category"],
                "icon": category_data["icon"],
                "question_count": len(category_data["questions"])
            })
        return categories
    
    def get_category_faqs(self, category_id: str) -> Optional[Dict]:
        """Get all FAQs in a specific category"""
        return self.faqs.get(category_id)
    
    def create_support_ticket(self, 
                            user_telegram_id: str,
                            subject: str,
                            message: str,
                            priority: str = SupportTicketPriority.MEDIUM,
                            category: str = "general") -> Dict:
        """Create a new support ticket"""
        
        try:
            # Generate ticket number
            ticket_number = f"TK{datetime.utcnow().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            
            # Create ticket record
            ticket = self.data_manager.create_support_ticket(
                user_telegram_id=user_telegram_id,
                ticket_number=ticket_number,
                subject=subject,
                message=message,
                priority=priority,
                category=category
            )
            
            if ticket:
                return {
                    'success': True,
                    'ticket': ticket,
                    'message': f'Support ticket #{ticket_number} created successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to create support ticket'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error creating support ticket: {str(e)}'
            }
    
    def get_user_tickets(self, user_telegram_id: str) -> List[Dict]:
        """Get all tickets for a user"""
        return self.data_manager.get_support_tickets(user_telegram_id=user_telegram_id)
    
    def get_pending_tickets(self) -> List[Dict]:
        """Get all pending support tickets for admin"""
        return self.data_manager.get_support_tickets(status=SupportTicketStatus.OPEN)
    
    def respond_to_ticket(self, ticket_id: int, response: str, admin_user: str) -> Dict:
        """Add admin response to support ticket"""
        
        try:
            result = self.data_manager.add_ticket_response(
                ticket_id=ticket_id,
                response=response,
                admin_user=admin_user
            )
            
            if result:
                return {
                    'success': True,
                    'message': 'Response added successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to add response'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error adding response: {str(e)}'
            }
    
    def update_ticket_status(self, ticket_id: int, status: str, admin_user: str) -> Dict:
        """Update support ticket status"""
        
        valid_statuses = [
            SupportTicketStatus.OPEN,
            SupportTicketStatus.IN_PROGRESS,
            SupportTicketStatus.RESOLVED,
            SupportTicketStatus.CLOSED
        ]
        
        if status not in valid_statuses:
            return {
                'success': False,
                'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }
        
        try:
            result = self.data_manager.update_ticket_status(
                ticket_id=ticket_id,
                status=status,
                updated_by=admin_user
            )
            
            if result:
                return {
                    'success': True,
                    'message': f'Ticket status updated to {status}'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to update ticket status'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error updating status: {str(e)}'
            }
    
    def get_support_analytics(self) -> Dict:
        """Get support system analytics"""
        
        all_tickets = self.data_manager.get_support_tickets()
        
        # Calculate stats
        total_tickets = len(all_tickets)
        open_tickets = [t for t in all_tickets if t['status'] == SupportTicketStatus.OPEN]
        resolved_tickets = [t for t in all_tickets if t['status'] == SupportTicketStatus.RESOLVED]
        
        # Category breakdown
        category_stats = {}
        priority_stats = {}
        
        for ticket in all_tickets:
            category = ticket.get('category', 'general')
            priority = ticket.get('priority', 'medium')
            
            category_stats[category] = category_stats.get(category, 0) + 1
            priority_stats[priority] = priority_stats.get(priority, 0) + 1
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_tickets = [
            t for t in all_tickets
            if datetime.fromisoformat(t['created_at']) >= week_ago
        ]
        
        # Response time analysis (simplified)
        avg_response_time = "< 24 hours"  # Would calculate from actual data
        
        return {
            'total_tickets': total_tickets,
            'open_tickets': len(open_tickets),
            'resolved_tickets': len(resolved_tickets),
            'resolution_rate': (len(resolved_tickets) / total_tickets * 100) if total_tickets > 0 else 0,
            'recent_tickets': len(recent_tickets),
            'category_breakdown': category_stats,
            'priority_breakdown': priority_stats,
            'avg_response_time': avg_response_time
        }
    
    def auto_respond_to_query(self, user_message: str, user_telegram_id: str) -> Optional[Dict]:
        """Attempt to automatically respond to common queries"""
        
        message_lower = user_message.lower()
        
        # Define patterns and responses
        auto_responses = {
            # Greeting patterns
            r'\b(hi|hello|hey|good morning|good afternoon|good evening)\b': {
                'response_type': 'greeting',
                'confidence': 'high'
            },
            
            # Order status patterns  
            r'\b(order status|track|tracking|where.*order|order.*status)\b': {
                'response_type': 'order_status',
                'confidence': 'high'
            },
            
            # Payment patterns
            r'\b(payment|pay|gcash|paymaya|bank transfer|cod|cash on delivery)\b': {
                'response_type': 'payment_issue',
                'confidence': 'medium'
            },
            
            # Delivery patterns
            r'\b(delivery|shipping|deliver|when.*arrive|how long)\b': {
                'response_type': 'delivery_delay',
                'confidence': 'medium'
            },
            
            # Product inquiry patterns
            r'\b(product|item|available|stock|price|cost|how much)\b': {
                'response_type': 'product_inquiry',
                'confidence': 'medium'
            },
            
            # Human support patterns
            r'\b(human|agent|representative|talk to|speak to|contact|help me)\b': {
                'response_type': 'contact_human',
                'confidence': 'high'
            }
        }
        
        # Check for pattern matches
        for pattern, response_info in auto_responses.items():
            if re.search(pattern, message_lower):
                response_text = self._get_response_text(response_info['response_type'])
                
                return {
                    'auto_response': True,
                    'response': response_text,
                    'confidence': response_info['confidence'],
                    'type': response_info['response_type']
                }
        
        # Try FAQ search if no pattern match
        faq_results = self.search_faq(user_message, limit=1)
        if faq_results and faq_results[0]['score'] > 5:
            return {
                'auto_response': True,
                'response': f"I found this information that might help:\n\n**{faq_results[0]['question']}**\n\n{faq_results[0]['answer']}",
                'confidence': 'medium',
                'type': 'faq_match',
                'faq_result': faq_results[0]
            }
        
        return None
    
    def _get_response_text(self, response_type: str) -> str:
        """Get response text for auto-response type"""
        
        quick_response = self.quick_responses.get(response_type)
        
        if isinstance(quick_response, list):
            import random
            return random.choice(quick_response)
        elif isinstance(quick_response, str):
            return quick_response
        else:
            return "I'm here to help! How can I assist you today?"
    
    def add_custom_faq(self, category: str, question: str, answer: str, keywords: List[str]) -> Dict:
        """Add custom FAQ (admin function)"""
        
        if category not in self.faqs:
            return {
                'success': False,
                'message': f'Invalid category. Available: {", ".join(self.faqs.keys())}'
            }
        
        if len(question) < 5 or len(answer) < 10:
            return {
                'success': False,
                'message': 'Question must be at least 5 characters, answer at least 10 characters'
            }
        
        try:
            # Add to FAQ database (in real implementation, save to database)
            new_faq = {
                'q': question,
                'a': answer,
                'keywords': keywords
            }
            
            self.faqs[category]['questions'].append(new_faq)
            
            return {
                'success': True,
                'message': 'FAQ added successfully',
                'faq': new_faq
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error adding FAQ: {str(e)}'
            }
    
    def suggest_faqs_for_query(self, query: str) -> List[str]:
        """Suggest FAQ questions that might help with the query"""
        results = self.search_faq(query, limit=3)
        return [result['question'] for result in results]

class SupportNotifications:
    """Handle support-related notifications"""
    
    def __init__(self, broadcast_system=None):
        self.broadcast_system = broadcast_system
        self.support_system = CustomerSupportSystem()
    
    async def notify_ticket_created(self, user_telegram_id: str, ticket: Dict):
        """Notify user that their support ticket was created"""
        try:
            from telegram import Bot
            import os
            bot = Bot(token=os.environ.get('BOT_TOKEN'))
            
            message = f"""
🎫 **Support Ticket Created**

**Ticket #:** {ticket['ticket_number']}
**Subject:** {ticket['subject']}
**Priority:** {ticket['priority'].title()}
**Status:** Open

📋 **Your Message:**
{ticket['message'][:200]}{'...' if len(ticket['message']) > 200 else ''}

⏰ **Response Time:**
Our team will respond within 24 hours during business hours.

🔍 **Track Your Ticket:**
Use /support to view all your tickets and responses.

Thank you for contacting us! 🤝
            """
            
            await bot.send_message(
                chat_id=user_telegram_id,
                text=message,
                parse_mode='Markdown'
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending ticket notification: {e}")
            return False
    
    async def notify_admin_new_ticket(self, ticket: Dict):
        """Notify admin about new support ticket"""
        # This would send to admin channel or specific admin users
        admin_message = f"""
🆘 **New Support Ticket**

**Ticket:** {ticket['ticket_number']}
**User:** {ticket['user_id']}
**Priority:** {ticket['priority'].upper()}
**Category:** {ticket['category']}

**Subject:** {ticket['subject']}

**Message:**
{ticket['message']}

**Created:** {ticket['created_at']}

Please respond promptly to maintain customer satisfaction.
        """
        
        # Implementation would send to admin notification system
        print(f"Admin notification: {admin_message}")
        return True
    
    async def notify_ticket_response(self, user_telegram_id: str, ticket: Dict, response: str):
        """Notify user about response to their ticket"""
        try:
            from telegram import Bot
            import os
            bot = Bot(token=os.environ.get('BOT_TOKEN'))
            
            message = f"""
💬 **New Response to Your Ticket**

**Ticket #:** {ticket['ticket_number']}
**Subject:** {ticket['subject']}
**Status:** {ticket['status'].title()}

**Our Response:**
{response}

🎫 **Need More Help?**
Reply to this ticket or create a new one if you need additional assistance.

Use /support to view your ticket history.

Thanks for your patience! 😊
            """
            
            await bot.send_message(
                chat_id=user_telegram_id,
                text=message,
                parse_mode='Markdown'
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending response notification: {e}")
            return False