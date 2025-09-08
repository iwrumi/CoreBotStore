import asyncio
import logging
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from advanced_data_manager import AdvancedDataManager

logger = logging.getLogger(__name__)

class BroadcastSystem:
    def __init__(self, bot_token):
        self.bot = Bot(token=bot_token)
        self.data_manager = AdvancedDataManager()
        
    async def send_broadcast(self, broadcast_id, max_concurrent=10):
        """Send broadcast to all target users"""
        broadcast = self.data_manager.get_broadcasts(status='scheduled')
        broadcast = next((b for b in broadcast if b['id'] == broadcast_id), None)
        
        if not broadcast:
            logger.error(f"Broadcast {broadcast_id} not found or not scheduled")
            return False
        
        # Update status to sending
        self.data_manager.update_broadcast_status(broadcast_id, 'sending')
        
        # Get target users
        target_users = self._get_target_users(broadcast['target_users'])
        
        if not target_users:
            logger.error("No target users found for broadcast")
            self.data_manager.update_broadcast_status(broadcast_id, 'failed')
            return False
        
        # Send messages in batches
        sent_count = 0
        failed_count = 0
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def send_to_user(user):
            async with semaphore:
                try:
                    await self._send_message_to_user(user, broadcast)
                    return True
                except Exception as e:
                    logger.error(f"Failed to send to user {user['telegram_id']}: {e}")
                    return False
        
        # Create tasks for all users
        tasks = [send_to_user(user) for user in target_users]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count results
        for result in results:
            if result is True:
                sent_count += 1
            else:
                failed_count += 1
        
        # Update broadcast status
        self.data_manager.update_broadcast_status(
            broadcast_id, 
            'sent' if sent_count > 0 else 'failed',
            sent_count,
            failed_count
        )
        
        logger.info(f"Broadcast {broadcast_id} completed: {sent_count} sent, {failed_count} failed")
        return True
    
    def _get_target_users(self, target_type):
        """Get users based on target type"""
        if target_type == 'all':
            return self.data_manager.get_users(is_banned=False)
        elif target_type == 'active':
            # Users who made an order in the last 30 days
            return self._get_active_users()
        elif target_type == 'inactive':
            # Users who haven't ordered in 30+ days
            return self._get_inactive_users()
        elif target_type == 'vip':
            # Users with high total spending
            return self._get_vip_users()
        else:
            return self.data_manager.get_users(is_banned=False)
    
    def _get_active_users(self):
        """Get users who were active in the last 30 days"""
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # Get all users with recent orders
        orders = self.data_manager.get_orders()
        active_user_ids = set()
        
        for order in orders:
            order_date = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
            if order_date >= cutoff_date:
                active_user_ids.add(order['user_id'])
        
        users = self.data_manager.get_users(is_banned=False)
        return [user for user in users if user['id'] in active_user_ids]
    
    def _get_inactive_users(self):
        """Get users who haven't been active in 30+ days"""
        active_users = self._get_active_users()
        active_user_ids = {user['id'] for user in active_users}
        
        all_users = self.data_manager.get_users(is_banned=False)
        return [user for user in all_users if user['id'] not in active_user_ids]
    
    def _get_vip_users(self):
        """Get VIP users (high spending customers)"""
        users = self.data_manager.get_users(is_banned=False)
        # VIP users are those who spent more than 1000
        return [user for user in users if user['total_spent'] > 1000]
    
    async def _send_message_to_user(self, user, broadcast):
        """Send broadcast message to a specific user"""
        try:
            message = broadcast['message']
            
            # Add user's name if available
            if user['first_name']:
                message = f"Hi {user['first_name']}! 👋\n\n{message}"
            
            # Send message
            if broadcast['image_url']:
                await self.bot.send_photo(
                    chat_id=user['telegram_id'],
                    photo=broadcast['image_url'],
                    caption=message,
                    parse_mode='Markdown'
                )
            else:
                await self.bot.send_message(
                    chat_id=user['telegram_id'],
                    text=message,
                    parse_mode='Markdown'
                )
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
            
        except TelegramError as e:
            if "bot was blocked" in str(e) or "user deactivated" in str(e):
                # User blocked the bot or deactivated account
                logger.info(f"User {user['telegram_id']} blocked the bot or deactivated account")
                # Could mark user as inactive here
            else:
                logger.error(f"Telegram error sending to {user['telegram_id']}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending to {user['telegram_id']}: {e}")
            raise
    
    async def send_stock_alert(self, product_id, stock_level):
        """Send stock alert for a specific product"""
        product = self.data_manager.get_product(product_id)
        if not product:
            return False
        
        # Create broadcast for stock alert
        message = f"🔥 **STOCK ALERT!** 🔥\n\n"
        message += f"📦 **{product['name']}** is back in stock!\n"
        message += f"💰 **Price:** ${product['price']:.2f}\n"
        message += f"📊 **Available:** {stock_level} units\n\n"
        message += f"⏰ Limited stock - order now before it's gone!\n"
        message += f"Use /start to browse and order!"
        
        broadcast_data = self.data_manager.create_broadcast(
            title=f"Stock Alert: {product['name']}",
            message=message,
            created_by='system',
            target_users='all',
            image_url=product.get('image_url', '')
        )
        
        # Send immediately
        self.data_manager.update_broadcast_status(broadcast_data['id'], 'scheduled')
        return await self.send_broadcast(broadcast_data['id'])
    
    async def send_promo_announcement(self, title, message, voucher_code=None, image_url=""):
        """Send promotional announcement"""
        promo_message = f"🎉 **{title}** 🎉\n\n{message}"
        
        if voucher_code:
            promo_message += f"\n\n🎫 **Voucher Code:** `{voucher_code}`"
            promo_message += f"\n💡 Tap the code to copy it!"
        
        promo_message += f"\n\n🛍️ Use /start to shop now!"
        
        broadcast_data = self.data_manager.create_broadcast(
            title=title,
            message=promo_message,
            created_by='admin',
            target_users='all',
            image_url=image_url
        )
        
        # Send immediately
        self.data_manager.update_broadcast_status(broadcast_data['id'], 'scheduled')
        return await self.send_broadcast(broadcast_data['id'])
    
    async def send_order_status_update(self, user_telegram_id, order_id, new_status):
        """Send order status update to specific user"""
        try:
            order = self.data_manager.get_order(order_id)
            if not order:
                return False
            
            status_messages = {
                'confirmed': '✅ Your order has been confirmed!',
                'processing': '⚙️ Your order is being processed',
                'shipped': '🚚 Your order has been shipped!',
                'delivered': '📦 Your order has been delivered!',
                'cancelled': '❌ Your order has been cancelled'
            }
            
            status_emojis = {
                'confirmed': '✅',
                'processing': '⚙️', 
                'shipped': '🚚',
                'delivered': '📦',
                'cancelled': '❌'
            }
            
            message = f"{status_emojis.get(new_status, '📋')} **Order Status Update**\n\n"
            message += f"**Order:** #{order['order_number']}\n"
            message += f"**Status:** {status_messages.get(new_status, new_status.title())}\n"
            message += f"**Total:** ${order['total']:.2f}\n\n"
            
            if new_status == 'shipped':
                message += "🔍 Track your package and expect delivery soon!\n"
            elif new_status == 'delivered':
                message += "🎉 Thank you for shopping with us!\n"
                message += "📝 We'd love your feedback on your purchase.\n"
            
            message += "\n🛍️ Use /orders to view all your orders"
            
            await self.bot.send_message(
                chat_id=user_telegram_id,
                text=message,
                parse_mode='Markdown'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send order update to {user_telegram_id}: {e}")
            return False
    
    def schedule_broadcast(self, title, message, scheduled_time, target_users='all', image_url=""):
        """Schedule a broadcast for later sending"""
        return self.data_manager.create_broadcast(
            title=title,
            message=message,
            created_by='admin',
            target_users=target_users,
            scheduled_at=scheduled_time,
            image_url=image_url
        )
    
    def get_broadcast_analytics(self, broadcast_id):
        """Get analytics for a specific broadcast"""
        broadcasts = self.data_manager.get_broadcasts()
        broadcast = next((b for b in broadcasts if b['id'] == broadcast_id), None)
        
        if not broadcast:
            return None
        
        total_users = len(self._get_target_users(broadcast['target_users']))
        
        return {
            'broadcast_id': broadcast_id,
            'title': broadcast['title'],
            'status': broadcast['status'],
            'target_users': broadcast['target_users'],
            'total_targeted': total_users,
            'sent_count': broadcast['sent_count'],
            'failed_count': broadcast['failed_count'],
            'success_rate': (broadcast['sent_count'] / total_users * 100) if total_users > 0 else 0,
            'created_at': broadcast['created_at'],
            'sent_at': broadcast['sent_at']
        }

# Utility function for admin use
async def send_broadcast_now(bot_token, title, message, target_users='all', image_url=""):
    """Quick function to send broadcast immediately"""
    broadcast_system = BroadcastSystem(bot_token)
    
    # Create broadcast
    data_manager = AdvancedDataManager()
    broadcast_data = data_manager.create_broadcast(
        title=title,
        message=message,
        created_by='admin',
        target_users=target_users,
        image_url=image_url
    )
    
    # Schedule and send
    data_manager.update_broadcast_status(broadcast_data['id'], 'scheduled')
    return await broadcast_system.send_broadcast(broadcast_data['id'])

# Background task for scheduled broadcasts
async def process_scheduled_broadcasts(bot_token):
    """Process any scheduled broadcasts that are ready to send"""
    data_manager = AdvancedDataManager()
    broadcast_system = BroadcastSystem(bot_token)
    
    # Get broadcasts scheduled for now or earlier
    broadcasts = data_manager.get_broadcasts(status='scheduled')
    current_time = datetime.utcnow()
    
    for broadcast in broadcasts:
        if not broadcast['scheduled_at']:
            # No schedule time, send immediately
            await broadcast_system.send_broadcast(broadcast['id'])
        else:
            scheduled_time = datetime.fromisoformat(broadcast['scheduled_at'])
            if scheduled_time <= current_time:
                await broadcast_system.send_broadcast(broadcast['id'])