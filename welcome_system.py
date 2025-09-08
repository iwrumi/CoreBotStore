"""
Customizable Welcome Message System
Allows admins to customize bot start messages and user experience
"""
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from advanced_data_manager import AdvancedDataManager

class WelcomeMessageSystem:
    def __init__(self):
        self.data_manager = AdvancedDataManager()
        self.default_templates = self._load_default_templates()
    
    def _load_default_templates(self) -> Dict:
        """Load default welcome message templates"""
        return {
            "professional": {
                "name": "Professional Store",
                "message": """
🛍️ **Welcome to {store_name}, {user_name}!**

Your one-stop shop for quality products at great prices.

**What we offer:**
• Wide selection of products
• Fast and reliable shipping
• Secure payment options
• Excellent customer service

Ready to start shopping?
                """,
                "buttons": [
                    {"text": "🏪 Browse Catalog", "action": "catalog"},
                    {"text": "🛒 View Cart", "action": "cart"},
                    {"text": "📦 My Orders", "action": "orders"},
                    {"text": "❓ Help & Support", "action": "help"}
                ]
            },
            "friendly": {
                "name": "Friendly Shop",
                "message": """
👋 **Hi there, {user_name}!**

Welcome to {store_name} - we're so excited you're here! 🎉

We've got amazing products waiting for you, and our team is here to make your shopping experience absolutely fantastic!

**Why you'll love shopping with us:**
• ✨ Handpicked quality products
• 🚀 Lightning-fast delivery  
• 💝 Special offers just for you
• 🤝 Personal customer care

Let's find something perfect for you! 💫
                """,
                "buttons": [
                    {"text": "🌟 Featured Products", "action": "featured"},
                    {"text": "🎯 Shop by Category", "action": "catalog"},
                    {"text": "🛒 My Cart", "action": "cart"},
                    {"text": "💬 Chat with Us", "action": "support"}
                ]
            },
            "minimal": {
                "name": "Clean & Simple",
                "message": """
**{store_name}**

Welcome, {user_name}.

Browse our products and place your orders seamlessly.
                """,
                "buttons": [
                    {"text": "Shop", "action": "catalog"},
                    {"text": "Cart", "action": "cart"},
                    {"text": "Orders", "action": "orders"}
                ]
            },
            "promotional": {
                "name": "Sales-Focused",
                "message": """
🔥 **WELCOME {user_name}!** 🔥

**{store_name}** - Your Premium Shopping Destination!

🎊 **SPECIAL OFFERS JUST FOR YOU:**
• 🏷️ Up to 50% OFF selected items
• 🚚 FREE shipping on orders over $50
• 🎁 Exclusive member discounts

**Limited time offers - Shop now!** ⏰

Don't miss out on these incredible deals! 💨
                """,
                "buttons": [
                    {"text": "🔥 Hot Deals", "action": "deals"},
                    {"text": "🛍️ Shop All", "action": "catalog"},
                    {"text": "🎁 Special Offers", "action": "offers"},
                    {"text": "⚡ Flash Sales", "action": "flash_sales"}
                ]
            }
        }
    
    def get_welcome_message(self, user_telegram_id: str, user_name: str = "there") -> Dict:
        """Get personalized welcome message for a user"""
        
        # Get user info for personalization
        user_info = self.data_manager.get_or_create_user(
            telegram_id=user_telegram_id,
            first_name=user_name
        )
        
        # Check if user has custom welcome settings
        is_returning = user_info.get('order_count', 0) > 0
        is_vip = user_info.get('total_spent', 0) > 1000
        
        # Get appropriate welcome message
        if is_vip:
            welcome_config = self._get_vip_welcome()
        elif is_returning:
            welcome_config = self._get_returning_welcome()
        else:
            welcome_config = self._get_new_user_welcome()
        
        # Apply personalization
        personalized_message = self._personalize_message(
            welcome_config['message'],
            user_info,
            user_name
        )
        
        return {
            'message': personalized_message,
            'buttons': welcome_config.get('buttons', []),
            'template_name': welcome_config.get('name', 'Custom'),
            'user_type': self._get_user_type(user_info)
        }
    
    def _get_new_user_welcome(self) -> Dict:
        """Get welcome message for new users"""
        template_name = self.data_manager.get_setting('new_user_template', 'professional')
        custom_message = self.data_manager.get_setting('custom_new_user_message', '')
        
        if custom_message:
            return self._parse_custom_message(custom_message)
        
        return self.default_templates.get(template_name, self.default_templates['professional'])
    
    def _get_returning_welcome(self) -> Dict:
        """Get welcome message for returning users"""
        template_name = self.data_manager.get_setting('returning_user_template', 'friendly')
        custom_message = self.data_manager.get_setting('custom_returning_message', '')
        
        if custom_message:
            return self._parse_custom_message(custom_message)
        
        # Modify friendly template for returning users
        template = self.default_templates.get(template_name, self.default_templates['friendly'])
        template = template.copy()
        template['message'] = template['message'].replace(
            "Welcome to {store_name}",
            "Welcome back to {store_name}"
        )
        
        return template
    
    def _get_vip_welcome(self) -> Dict:
        """Get welcome message for VIP users"""
        custom_message = self.data_manager.get_setting('custom_vip_message', '')
        
        if custom_message:
            return self._parse_custom_message(custom_message)
        
        return {
            "name": "VIP Customer",
            "message": """
👑 **Welcome back, {user_name}!** 👑

As one of our **VIP customers**, you get exclusive access to:

🌟 **VIP Benefits:**
• 🎁 Exclusive member-only discounts
• 🚚 FREE priority shipping
• 📞 Direct VIP customer support
• 🔔 First access to new products

Total orders: {order_count} | Lifetime value: ${total_spent:.2f}

Thank you for being such a valued customer! ✨
            """,
            "buttons": [
                {"text": "👑 VIP Deals", "action": "vip_deals"},
                {"text": "🆕 New Arrivals", "action": "new_arrivals"},
                {"text": "🛒 Quick Reorder", "action": "reorder"},
                {"text": "📞 VIP Support", "action": "vip_support"}
            ]
        }
    
    def _personalize_message(self, message: str, user_info: Dict, user_name: str) -> str:
        """Apply personalization to message"""
        
        # Get store settings
        store_name = self.data_manager.get_setting('store_name', 'Our Store')
        
        # Replace placeholders
        replacements = {
            '{user_name}': user_name or user_info.get('first_name', 'there'),
            '{store_name}': store_name,
            '{order_count}': str(user_info.get('order_count', 0)),
            '{total_spent}': f"{user_info.get('total_spent', 0):.2f}",
            '{user_type}': self._get_user_type(user_info)
        }
        
        personalized = message
        for placeholder, value in replacements.items():
            personalized = personalized.replace(placeholder, value)
        
        # Add dynamic content based on time
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            time_greeting = "Good morning"
        elif 12 <= current_hour < 17:
            time_greeting = "Good afternoon"
        else:
            time_greeting = "Good evening"
        
        # Add time-based greeting if not present
        if "Good morning" not in personalized and "Good afternoon" not in personalized and "Good evening" not in personalized:
            personalized = f"{time_greeting}! " + personalized
        
        return personalized.strip()
    
    def _get_user_type(self, user_info: Dict) -> str:
        """Determine user type based on history"""
        total_spent = user_info.get('total_spent', 0)
        order_count = user_info.get('order_count', 0)
        
        if total_spent > 1000:
            return "VIP"
        elif order_count > 0:
            return "Returning"
        else:
            return "New"
    
    def _parse_custom_message(self, custom_message: str) -> Dict:
        """Parse custom message format"""
        try:
            # Assume custom message is JSON format with message and buttons
            parsed = json.loads(custom_message)
            return parsed
        except:
            # Fallback to text-only message
            return {
                "name": "Custom",
                "message": custom_message,
                "buttons": [
                    {"text": "🏪 Browse Products", "action": "catalog"},
                    {"text": "🛒 View Cart", "action": "cart"},
                    {"text": "❓ Help", "action": "help"}
                ]
            }
    
    def create_custom_welcome(self, user_type: str, message: str, buttons: List[Dict]) -> Dict:
        """Create custom welcome message"""
        
        # Validate user type
        valid_types = ['new_user', 'returning', 'vip']
        if user_type not in valid_types:
            return {
                'success': False,
                'message': f'Invalid user type. Must be one of: {", ".join(valid_types)}'
            }
        
        # Validate message
        if not message or len(message.strip()) < 10:
            return {
                'success': False,
                'message': 'Message must be at least 10 characters long'
            }
        
        # Validate buttons
        if len(buttons) > 8:
            return {
                'success': False,
                'message': 'Maximum 8 buttons allowed'
            }
        
        for button in buttons:
            if not button.get('text') or not button.get('action'):
                return {
                    'success': False,
                    'message': 'Each button must have text and action'
                }
        
        # Create custom welcome config
        custom_config = {
            'name': f'Custom {user_type.title()}',
            'message': message.strip(),
            'buttons': buttons,
            'created_at': datetime.utcnow().isoformat()
        }
        
        try:
            # Save to settings
            setting_key = f'custom_{user_type}_message'
            self.data_manager.set_setting(
                setting_key,
                json.dumps(custom_config),
                f'Custom welcome message for {user_type} users'
            )
            
            return {
                'success': True,
                'message': f'Custom welcome message for {user_type} users saved successfully',
                'config': custom_config
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error saving custom message: {str(e)}'
            }
    
    def get_available_templates(self) -> List[Dict]:
        """Get all available welcome templates"""
        templates = []
        
        for template_id, template_data in self.default_templates.items():
            templates.append({
                'id': template_id,
                'name': template_data['name'],
                'preview': template_data['message'][:100] + '...',
                'button_count': len(template_data.get('buttons', []))
            })
        
        return templates
    
    def apply_template(self, user_type: str, template_id: str) -> Dict:
        """Apply a template to a user type"""
        
        if template_id not in self.default_templates:
            return {
                'success': False,
                'message': f'Template "{template_id}" not found'
            }
        
        if user_type not in ['new_user', 'returning', 'vip']:
            return {
                'success': False,
                'message': 'Invalid user type'
            }
        
        try:
            setting_key = f'{user_type}_template'
            self.data_manager.set_setting(
                setting_key,
                template_id,
                f'Welcome template for {user_type} users'
            )
            
            return {
                'success': True,
                'message': f'Template "{self.default_templates[template_id]["name"]}" applied to {user_type} users',
                'template': self.default_templates[template_id]
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error applying template: {str(e)}'
            }
    
    def get_welcome_analytics(self) -> Dict:
        """Get analytics about welcome message effectiveness"""
        
        # Get user stats
        all_users = self.data_manager.get_users()
        new_users = [u for u in all_users if u.get('order_count', 0) == 0]
        returning_users = [u for u in all_users if 0 < u.get('order_count', 0) < 5]
        vip_users = [u for u in all_users if u.get('total_spent', 0) > 1000]
        
        # Calculate conversion rates
        total_users = len(all_users)
        converted_users = [u for u in all_users if u.get('order_count', 0) > 0]
        conversion_rate = (len(converted_users) / total_users * 100) if total_users > 0 else 0
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_users = [
            u for u in all_users 
            if datetime.fromisoformat(u.get('created_at', '1970-01-01')) >= week_ago
        ]
        
        return {
            'total_users': total_users,
            'new_users': len(new_users),
            'returning_users': len(returning_users),
            'vip_users': len(vip_users),
            'conversion_rate': conversion_rate,
            'recent_new_users': len(recent_users),
            'user_distribution': {
                'new': len(new_users),
                'returning': len(returning_users),
                'vip': len(vip_users)
            }
        }
    
    def test_welcome_message(self, user_type: str, test_user_name: str = "Test User") -> Dict:
        """Test welcome message for a user type"""
        
        # Create mock user data
        mock_user_data = {
            'telegram_id': '123456789',
            'first_name': test_user_name,
            'order_count': 0,
            'total_spent': 0
        }
        
        if user_type == 'returning':
            mock_user_data['order_count'] = 3
            mock_user_data['total_spent'] = 250.0
        elif user_type == 'vip':
            mock_user_data['order_count'] = 15
            mock_user_data['total_spent'] = 1500.0
        
        # Get appropriate welcome
        if user_type == 'new':
            config = self._get_new_user_welcome()
        elif user_type == 'returning':
            config = self._get_returning_welcome()
        elif user_type == 'vip':
            config = self._get_vip_welcome()
        else:
            return {'success': False, 'message': 'Invalid user type'}
        
        # Apply personalization
        personalized_message = self._personalize_message(
            config['message'],
            mock_user_data,
            test_user_name
        )
        
        return {
            'success': True,
            'preview': {
                'message': personalized_message,
                'buttons': config.get('buttons', []),
                'template_name': config.get('name', 'Custom'),
                'user_type': user_type
            }
        }
    
    def schedule_welcome_update(self, message: str, schedule_time: datetime, user_types: List[str] = None) -> Dict:
        """Schedule a welcome message update"""
        
        if user_types is None:
            user_types = ['new_user', 'returning', 'vip']
        
        # Validate schedule time
        if schedule_time <= datetime.utcnow():
            return {
                'success': False,
                'message': 'Schedule time must be in the future'
            }
        
        try:
            # Create scheduled update record
            schedule_data = {
                'message': message,
                'user_types': user_types,
                'schedule_time': schedule_time.isoformat(),
                'status': 'scheduled',
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Save to settings (in real implementation, you'd use a proper scheduler)
            schedule_key = f'scheduled_welcome_{int(datetime.utcnow().timestamp())}'
            self.data_manager.set_setting(
                schedule_key,
                json.dumps(schedule_data),
                'Scheduled welcome message update'
            )
            
            return {
                'success': True,
                'message': f'Welcome message update scheduled for {schedule_time.strftime("%Y-%m-%d %H:%M")}',
                'schedule_id': schedule_key
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error scheduling update: {str(e)}'
            }

class WelcomeMessageVariables:
    """Available variables for welcome message personalization"""
    
    VARIABLES = {
        '{user_name}': 'User\'s first name',
        '{store_name}': 'Store name from settings',
        '{order_count}': 'Number of orders placed by user',
        '{total_spent}': 'Total amount spent by user',
        '{user_type}': 'User type (New/Returning/VIP)',
        '{current_date}': 'Current date',
        '{current_time}': 'Current time',
        '{day_greeting}': 'Time-based greeting (Good morning/afternoon/evening)'
    }
    
    @classmethod
    def get_help_text(cls) -> str:
        """Get help text for variables"""
        help_text = "📝 **Available Variables:**\n\n"
        
        for variable, description in cls.VARIABLES.items():
            help_text += f"`{variable}` - {description}\n"
        
        help_text += "\n💡 **Example:**\n"
        help_text += "`Hello {user_name}! Welcome to {store_name}.`"
        
        return help_text
    
    @classmethod
    def validate_message(cls, message: str) -> Dict:
        """Validate message for proper variable usage"""
        
        # Find all variables in message
        import re
        found_variables = re.findall(r'\{[^}]+\}', message)
        invalid_variables = []
        
        for var in found_variables:
            if var not in cls.VARIABLES:
                invalid_variables.append(var)
        
        if invalid_variables:
            return {
                'valid': False,
                'message': f'Invalid variables found: {", ".join(invalid_variables)}',
                'invalid_variables': invalid_variables
            }
        
        return {
            'valid': True,
            'message': 'All variables are valid',
            'used_variables': found_variables
        }