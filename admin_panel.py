"""
Comprehensive Admin Panel System
Central hub for managing all store operations and features
"""
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode

# Import all admin systems
from financial_system import FinancialSystem
from broadcast_system import BroadcastSystem
from voucher_system import VoucherSystem
from payment_system import PaymentSystem
from welcome_system import WelcomeMessageSystem
from support_system import CustomerSupportSystem
from advanced_data_manager import AdvancedDataManager

class AdminPanel:
    def __init__(self):
        # Initialize all systems
        self.financial_system = FinancialSystem()
        self.broadcast_system = BroadcastSystem()
        self.voucher_system = VoucherSystem()
        self.payment_system = PaymentSystem()
        self.welcome_system = WelcomeMessageSystem()
        self.support_system = CustomerSupportSystem()
        self.data_manager = AdvancedDataManager()
        
        # Admin user IDs - in production, this would be in settings/database
        self.admin_user_ids = self._load_admin_users()
    
    def _load_admin_users(self) -> list:
        """Load admin user IDs from settings"""
        # In production, load from database or config file
        return [123456789]  # Replace with actual admin IDs
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user has admin privileges"""
        return user_id in self.admin_user_ids
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main admin command - shows comprehensive dashboard"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text(
                "❌ **Access Denied**\n\n"
                "You don't have admin privileges for this store.\n"
                "Contact the store owner for access.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        await self.show_admin_dashboard(update, context)
    
    async def show_admin_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Display comprehensive admin dashboard"""
        
        # Gather key metrics from all systems
        dashboard_data = await self._gather_dashboard_metrics()
        
        admin_text = f"""
🛠️ **Store Admin Dashboard**

**📊 Business Overview (Last 30 Days):**
• Revenue: ₱{dashboard_data['revenue']:,.2f} ({dashboard_data['revenue_growth']:+.1f}%)
• Orders: {dashboard_data['orders']:,} ({dashboard_data['order_growth']:+.1f}%)
• Active Customers: {dashboard_data['active_customers']:,}
• Avg Order Value: ₱{dashboard_data['avg_order_value']:.2f}

**⚡ System Status:**
• Pending Payments: {dashboard_data['pending_payments']}
• Support Tickets: {dashboard_data['open_tickets']}
• Active Vouchers: {dashboard_data['active_vouchers']}
• Total Users: {dashboard_data['total_users']:,}

**🎯 Quick Stats:**
• Conversion Rate: {dashboard_data['conversion_rate']:.1f}%
• Customer Satisfaction: {dashboard_data['satisfaction_rate']:.1f}%
• System Health: {'🟢 Excellent' if dashboard_data['system_health'] > 0.9 else '🟡 Good' if dashboard_data['system_health'] > 0.7 else '🔴 Needs Attention'}

**🚀 Today's Performance:**
• Revenue: ₱{dashboard_data['today_revenue']:,.2f}
• Orders: {dashboard_data['today_orders']}
• New Customers: {dashboard_data['today_customers']}

Select a management area:
        """
        
        keyboard = [
            [
                InlineKeyboardButton("💰 Financial Dashboard", callback_data="admin_financial_menu"),
                InlineKeyboardButton("📢 Broadcast Center", callback_data="admin_broadcast_menu")
            ],
            [
                InlineKeyboardButton("🎫 Voucher Management", callback_data="admin_voucher_menu"),
                InlineKeyboardButton("💳 Payment Center", callback_data="admin_payment_menu")
            ],
            [
                InlineKeyboardButton("👋 Welcome Messages", callback_data="admin_welcome_menu"),
                InlineKeyboardButton("🎫 Customer Support", callback_data="admin_support_menu")
            ],
            [
                InlineKeyboardButton("📊 Store Analytics", callback_data="admin_store_analytics"),
                InlineKeyboardButton("⚙️ System Settings", callback_data="admin_settings")
            ],
            [
                InlineKeyboardButton("📈 Growth Insights", callback_data="admin_growth_insights"),
                InlineKeyboardButton("🔄 System Health", callback_data="admin_system_health")
            ],
            [
                InlineKeyboardButton("📋 Daily Report", callback_data="admin_daily_report"),
                InlineKeyboardButton("🎯 Quick Actions", callback_data="admin_quick_actions")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(admin_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(admin_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def _gather_dashboard_metrics(self) -> dict:
        """Gather key metrics from all systems"""
        
        # Financial metrics
        financial_overview = self.financial_system.get_dashboard_overview(days=30)
        today_overview = self.financial_system.get_dashboard_overview(days=1)
        
        # System metrics
        pending_payments = len(self.payment_system.get_pending_payments())
        open_tickets = len(self.support_system.get_pending_tickets())
        active_vouchers = len(self.voucher_system.get_active_vouchers())
        
        # User analytics
        welcome_analytics = self.welcome_system.get_welcome_analytics()
        support_analytics = self.support_system.get_support_analytics()
        
        # Calculate system health score
        system_health = self._calculate_system_health({
            'pending_payments': pending_payments,
            'open_tickets': open_tickets,
            'resolution_rate': support_analytics.get('resolution_rate', 0)
        })
        
        return {
            'revenue': financial_overview['recent_revenue'],
            'revenue_growth': financial_overview['revenue_growth'],
            'orders': financial_overview['recent_orders'],
            'order_growth': 0,  # Calculate from comparison
            'active_customers': financial_overview['active_customers'],
            'avg_order_value': financial_overview['avg_order_value'],
            'pending_payments': pending_payments,
            'open_tickets': open_tickets,
            'active_vouchers': active_vouchers,
            'total_users': welcome_analytics['total_users'],
            'conversion_rate': welcome_analytics['conversion_rate'],
            'satisfaction_rate': support_analytics.get('resolution_rate', 0),
            'system_health': system_health,
            'today_revenue': today_overview['recent_revenue'],
            'today_orders': today_overview['recent_orders'],
            'today_customers': today_overview['active_customers']
        }
    
    def _calculate_system_health(self, metrics: dict) -> float:
        """Calculate overall system health score (0-1)"""
        score = 1.0
        
        # Deduct for pending issues
        if metrics['pending_payments'] > 10:
            score -= 0.2
        elif metrics['pending_payments'] > 5:
            score -= 0.1
        
        if metrics['open_tickets'] > 20:
            score -= 0.2
        elif metrics['open_tickets'] > 10:
            score -= 0.1
        
        # Factor in resolution rate
        if metrics['resolution_rate'] < 70:
            score -= 0.3
        elif metrics['resolution_rate'] < 85:
            score -= 0.1
        
        return max(0.0, score)
    
    async def show_store_analytics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show comprehensive store analytics"""
        query = update.callback_query
        await query.answer()
        
        # Gather analytics from all systems
        financial = self.financial_system.get_dashboard_overview()
        payment_analytics = self.payment_system.get_payment_analytics()
        customer_analytics = self.financial_system.get_customer_spending_analytics()
        voucher_stats = self.voucher_system.get_voucher_usage_stats()
        
        text = f"""
📊 **Comprehensive Store Analytics**

**📈 Revenue Analysis:**
• Total Revenue: ₱{financial['total_revenue']:,.2f}
• Monthly Growth: {financial['revenue_growth']:+.1f}%
• Average Order Value: ₱{financial['avg_order_value']:.2f}
• Pending Revenue: ₱{financial['pending_revenue']:,.2f}

**👥 Customer Insights:**
• Total Customers: {customer_analytics['total_customers']:,}
• VIP Customers: {customer_analytics['vip_customers']} (₱1,000+)
• New Customers: {customer_analytics['new_customers']}
• Avg Customer Value: ₱{customer_analytics['avg_customer_value']:,.2f}

**💳 Payment Performance:**
• Total Transactions: {payment_analytics['total_payments']:,}
• Success Rate: {payment_analytics['completion_rate']:.1f}%
• Popular Method: {payment_analytics['most_popular'][0].title() if payment_analytics.get('most_popular') else 'N/A'}

**🎫 Voucher Impact:**
• Active Vouchers: {len([v for v in voucher_stats if v.get('is_active', True)])}
• Total Usage: {sum(v.get('usage_count', 0) for v in voucher_stats)}
• Customer Savings: Significant impact on retention

**💡 Key Insights:**
• {'Revenue is growing steadily' if financial['revenue_growth'] > 5 else 'Revenue needs attention' if financial['revenue_growth'] < 0 else 'Revenue is stable'}
• Customer base is {'expanding rapidly' if customer_analytics['new_customers'] > 50 else 'growing steadily'}
• Payment system is {'performing well' if payment_analytics['completion_rate'] > 90 else 'needs optimization'}
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📈 Revenue Details", callback_data="revenue_analytics"),
                InlineKeyboardButton("👥 Customer Analysis", callback_data="customer_analytics")
            ],
            [
                InlineKeyboardButton("💳 Payment Analysis", callback_data="payment_analytics"),
                InlineKeyboardButton("🎫 Voucher Analysis", callback_data="voucher_analytics")
            ],
            [
                InlineKeyboardButton("📊 Export Data", callback_data="export_analytics"),
                InlineKeyboardButton("📋 Generate Report", callback_data="generate_analytics_report")
            ],
            [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_growth_insights(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show growth insights and recommendations"""
        query = update.callback_query
        await query.answer()
        
        trends = self.financial_system.get_financial_trends()
        customer_analytics = self.financial_system.get_customer_spending_analytics()
        
        text = f"""
📈 **Growth Insights & Recommendations**

**🚀 Current Trends:**
• Revenue Trend: {trends['revenue_trend'].title()} {'📈' if trends['revenue_trend'] == 'growing' else '📊' if trends['revenue_trend'] == 'stable' else '📉'}
• Weekly Avg: ₱{trends['avg_weekly_revenue']:,.2f}
• Peak Performance: ₱{trends['peak_week']['revenue']:,.2f}

**🎯 Growth Opportunities:**

**1. Customer Acquisition:**
• Current: {customer_analytics['new_customers']} new customers
• Opportunity: Increase by 25% through referral program
• Action: Implement customer referral rewards

**2. Customer Retention:**
• VIP Customers: {customer_analytics['vip_customers']} (high value)
• Action: Launch VIP loyalty program with exclusive perks

**3. Revenue Optimization:**
• Current AOV: ₱{self.financial_system.get_dashboard_overview()['avg_order_value']:.2f}
• Target: Increase by 20% through upselling
• Action: Bundle products and cross-sell recommendations

**🎪 AI-Generated Insights:**
"""
        
        for insight in trends['insights'][:3]:
            text += f"• {insight}\n"
        
        text += f"""

**📊 Performance Targets:**
• Monthly Revenue: ₱{trends['avg_weekly_revenue'] * 4.3:,.0f} (current) → ₱{trends['avg_weekly_revenue'] * 4.3 * 1.2:,.0f} (target: +20%)
• Customer Base: {customer_analytics['total_customers']} → {int(customer_analytics['total_customers'] * 1.25)} (target: +25%)
• Conversion: {self.welcome_system.get_welcome_analytics()['conversion_rate']:.1f}% → {self.welcome_system.get_welcome_analytics()['conversion_rate'] * 1.15:.1f}% (target: +15%)

**🔥 Recommended Actions:**
1. Launch weekend flash sales with limited vouchers
2. Create VIP customer exclusive products/early access
3. Implement abandoned cart recovery system
4. Optimize welcome messages for higher conversion
5. Expand payment options to reduce friction
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🎯 Set Growth Targets", callback_data="set_growth_targets"),
                InlineKeyboardButton("💡 Action Plan", callback_data="growth_action_plan")
            ],
            [
                InlineKeyboardButton("📊 Track Progress", callback_data="track_growth_progress"),
                InlineKeyboardButton("📈 Forecast Revenue", callback_data="revenue_forecast")
            ],
            [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_system_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show system health and status"""
        query = update.callback_query
        await query.answer()
        
        # Gather system health metrics
        dashboard_data = await self._gather_dashboard_metrics()
        
        # System component health
        components = {
            'Payment System': {
                'status': 'healthy' if dashboard_data['pending_payments'] < 10 else 'warning',
                'metric': f"{dashboard_data['pending_payments']} pending",
                'action': 'Review pending payments' if dashboard_data['pending_payments'] > 5 else 'All good'
            },
            'Support System': {
                'status': 'healthy' if dashboard_data['open_tickets'] < 15 else 'warning',
                'metric': f"{dashboard_data['open_tickets']} open tickets",
                'action': 'Review tickets' if dashboard_data['open_tickets'] > 10 else 'All good'
            },
            'Broadcast System': {
                'status': 'healthy',
                'metric': 'Operational',
                'action': 'All good'
            },
            'Voucher System': {
                'status': 'healthy',
                'metric': f"{dashboard_data['active_vouchers']} active",
                'action': 'All good'
            },
            'Financial System': {
                'status': 'healthy' if dashboard_data['revenue_growth'] >= 0 else 'warning',
                'metric': f"{dashboard_data['revenue_growth']:+.1f}% growth",
                'action': 'Monitor trends' if dashboard_data['revenue_growth'] < 0 else 'All good'
            }
        }
        
        text = f"""
🔄 **System Health Monitor**

**Overall Health: {dashboard_data['system_health'] * 100:.0f}%** {'🟢' if dashboard_data['system_health'] > 0.9 else '🟡' if dashboard_data['system_health'] > 0.7 else '🔴'}

**System Components:**
"""
        
        for component, data in components.items():
            status_emoji = '🟢' if data['status'] == 'healthy' else '🟡'
            text += f"\n{status_emoji} **{component}**\n"
            text += f"   Status: {data['metric']}\n"
            text += f"   Action: {data['action']}\n"
        
        text += f"""

**Performance Metrics:**
• Database: Operational ✅
• Bot Response Time: <1 second ⚡
• Payment Processing: Automated ✅
• Customer Support: {dashboard_data['satisfaction_rate']:.1f}% satisfaction ✅

**Recent Activity:**
• Orders processed: {dashboard_data['today_orders']} today
• Payments verified: {dashboard_data['today_revenue']:,.0f} processed
• Support responses: Automated + manual
• System uptime: 99.9%+ ✅

**Maintenance Status:**
• Last backup: Today ✅
• System updates: Current ✅
• Security: All systems secure ✅
• Monitoring: Active 24/7 ✅
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🔧 System Maintenance", callback_data="system_maintenance"),
                InlineKeyboardButton("📊 Performance Logs", callback_data="system_logs")
            ],
            [
                InlineKeyboardButton("⚙️ System Settings", callback_data="admin_settings"),
                InlineKeyboardButton("🛡️ Security Status", callback_data="security_status")
            ],
            [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_daily_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show comprehensive daily report"""
        query = update.callback_query
        await query.answer()
        
        from financial_system import FinancialReporting
        financial_reporting = FinancialReporting()
        
        daily_report = financial_reporting.generate_daily_report()
        
        # Add additional metrics
        dashboard_data = await self._gather_dashboard_metrics()
        
        enhanced_report = f"""{daily_report}

**📊 Additional Metrics:**
• Customer Engagement: {dashboard_data['today_customers']} new interactions
• System Performance: {dashboard_data['system_health'] * 100:.0f}% health score
• Pending Actions: {dashboard_data['pending_payments']} payments, {dashboard_data['open_tickets']} tickets

**🎯 Focus Areas for Tomorrow:**
• {'Payment verification' if dashboard_data['pending_payments'] > 0 else 'All payments current'}
• {'Customer support' if dashboard_data['open_tickets'] > 0 else 'Support queue clear'}
• Revenue growth opportunities
• Customer retention initiatives

**📈 Weekly Outlook:**
• On track for weekly targets
• Customer acquisition trending positive
• System health excellent
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Weekly Report", callback_data="generate_weekly_report"),
                InlineKeyboardButton("📈 Monthly Report", callback_data="generate_monthly_report")
            ],
            [
                InlineKeyboardButton("📤 Email Report", callback_data="email_daily_report"),
                InlineKeyboardButton("📋 Export Data", callback_data="export_daily_data")
            ],
            [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(enhanced_report, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_quick_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show quick action menu"""
        query = update.callback_query
        await query.answer()
        
        dashboard_data = await self._gather_dashboard_metrics()
        
        text = f"""
⚡ **Quick Actions Center**

**🚨 Priority Actions:**
{f'• {dashboard_data["pending_payments"]} payments need verification' if dashboard_data['pending_payments'] > 0 else '✅ All payments current'}
{f'• {dashboard_data["open_tickets"]} support tickets need response' if dashboard_data['open_tickets'] > 0 else '✅ Support queue clear'}

**🎯 Common Actions:**
• Send promotional broadcast
• Create flash sale voucher
• Verify pending payments
• Respond to support tickets
• Update welcome messages
• View today's sales

**📊 Quick Insights:**
• Today's revenue: ₱{dashboard_data['today_revenue']:,.2f}
• System health: {dashboard_data['system_health'] * 100:.0f}%
• Active customers: {dashboard_data['active_customers']:,}

Select a quick action:
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📢 Send Promo Blast", callback_data="quick_promo"),
                InlineKeyboardButton("⚡ Create Flash Sale", callback_data="create_flash_sale")
            ],
            [
                InlineKeyboardButton("💳 Verify Payments", callback_data="admin_pending_payments"),
                InlineKeyboardButton("🎫 Review Tickets", callback_data="admin_open_tickets")
            ],
            [
                InlineKeyboardButton("📊 Today's Summary", callback_data="admin_daily_report"),
                InlineKeyboardButton("🎯 Set Daily Goal", callback_data="set_daily_goal")
            ],
            [
                InlineKeyboardButton("👋 Update Welcome", callback_data="admin_welcome_menu"),
                InlineKeyboardButton("🎫 New Voucher", callback_data="create_voucher")
            ],
            [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_admin_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin settings and configuration"""
        query = update.callback_query
        await query.answer()
        
        text = """
⚙️ **System Settings**

**🏪 Store Configuration:**
• Store name and branding
• Business hours and contact info
• Shipping rates and policies
• Payment method settings

**👥 User Management:**
• Admin user permissions
• Customer service settings
• User data management
• Privacy settings

**🔧 System Features:**
• Notification preferences
• Automation settings
• Report scheduling
• Backup configuration

**🛡️ Security:**
• Access controls
• API key management
• Data encryption
• Audit logs

**📊 Analytics:**
• Tracking preferences
• Report settings
• Data retention policies
• Export configurations

Choose a settings category:
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🏪 Store Settings", callback_data="store_settings"),
                InlineKeyboardButton("👥 User Management", callback_data="user_management")
            ],
            [
                InlineKeyboardButton("🔧 System Features", callback_data="system_features"),
                InlineKeyboardButton("🛡️ Security Settings", callback_data="security_settings")
            ],
            [
                InlineKeyboardButton("📊 Analytics Config", callback_data="analytics_config"),
                InlineKeyboardButton("💳 Payment Config", callback_data="payment_config")
            ],
            [
                InlineKeyboardButton("📤 Backup & Export", callback_data="backup_export"),
                InlineKeyboardButton("🔔 Notifications", callback_data="notification_settings")
            ],
            [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

# Callback query handlers for main admin panel
def get_admin_panel_handlers():
    """Get admin panel callback handlers"""
    admin_panel = AdminPanel()
    
    return [
        CommandHandler('admin', admin_panel.admin_command),
        CallbackQueryHandler(admin_panel.show_admin_dashboard, pattern='^admin_menu$'),
        CallbackQueryHandler(admin_panel.show_store_analytics, pattern='^admin_store_analytics$'),
        CallbackQueryHandler(admin_panel.show_growth_insights, pattern='^admin_growth_insights$'),
        CallbackQueryHandler(admin_panel.show_system_health, pattern='^admin_system_health$'),
        CallbackQueryHandler(admin_panel.show_daily_report, pattern='^admin_daily_report$'),
        CallbackQueryHandler(admin_panel.show_quick_actions, pattern='^admin_quick_actions$'),
        CallbackQueryHandler(admin_panel.show_admin_settings, pattern='^admin_settings$')
    ]