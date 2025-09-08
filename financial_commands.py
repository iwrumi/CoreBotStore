"""
Financial dashboard commands for admin interface
"""
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
from financial_system import FinancialSystem, FinancialReporting
from advanced_data_manager import AdvancedDataManager

class FinancialCommands:
    def __init__(self):
        self.financial_system = FinancialSystem()
        self.financial_reporting = FinancialReporting()
        self.data_manager = AdvancedDataManager()
    
    async def admin_financial_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show financial dashboard menu for admins"""
        user_id = update.effective_user.id
        
        # Check admin permissions
        if not self._is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        # Get dashboard overview
        dashboard = self.financial_system.get_dashboard_overview()
        
        # Format growth indicator
        growth_indicator = "📈" if dashboard['revenue_growth'] > 0 else "📉" if dashboard['revenue_growth'] < 0 else "➡️"
        
        menu_text = f"""
💰 **Financial Dashboard**

**Revenue Overview (30 days):**
• Total Revenue: ₱{dashboard['total_revenue']:,.2f}
• Recent Revenue: ₱{dashboard['recent_revenue']:,.2f}
• {growth_indicator} Growth: {dashboard['revenue_growth']:+.1f}%
• Pending: ₱{dashboard['pending_revenue']:,.2f}

**Business Metrics:**
• Total Orders: {dashboard['total_orders']:,}
• Active Customers: {dashboard['active_customers']:,}
• Avg Order Value: ₱{dashboard['avg_order_value']:.2f}

**Quick Actions:**
• View detailed analytics
• Generate financial reports
• Track payment history
• Monitor customer spending

Choose what to analyze:
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 Revenue Analytics", callback_data="revenue_analytics")],
            [InlineKeyboardButton("💳 Payment Analytics", callback_data="payment_analytics")],
            [InlineKeyboardButton("👥 Customer Analytics", callback_data="customer_analytics")],
            [InlineKeyboardButton("📈 Trends & Insights", callback_data="financial_trends")],
            [InlineKeyboardButton("📋 Generate Reports", callback_data="financial_reports")],
            [InlineKeyboardButton("💰 Profit Analysis", callback_data="profit_analysis")],
            [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_revenue_analytics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show detailed revenue analytics"""
        query = update.callback_query
        await query.answer()
        
        text = """
📊 **Revenue Analytics**

Choose the time period you want to analyze:

**Available Periods:**
• **Daily** - Last 30 days breakdown
• **Weekly** - Weekly performance trends  
• **Monthly** - Monthly revenue comparison
• **Custom** - Choose your own date range

What period would you like to analyze?
        """
        
        keyboard = [
            [InlineKeyboardButton("📅 Daily (30 days)", callback_data="revenue_daily")],
            [InlineKeyboardButton("📅 Weekly (12 weeks)", callback_data="revenue_weekly")],
            [InlineKeyboardButton("📅 Monthly (12 months)", callback_data="revenue_monthly")],
            [InlineKeyboardButton("🎯 Custom Range", callback_data="revenue_custom")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_financial_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_daily_revenue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show daily revenue analytics"""
        query = update.callback_query
        await query.answer()
        
        analytics = self.financial_system.get_revenue_analytics('daily')
        
        text = f"""
📅 **Daily Revenue Analytics (Last 30 Days)**

**Summary:**
• Total Revenue: ₱{analytics['total_revenue']:,.2f}
• Average Daily: ₱{analytics['average_daily']:,.2f}
• Best Day: {analytics['best_day'][0]} (₱{analytics['best_day'][1]:,.2f})

**Recent Performance (Last 7 Days):**
"""
        
        # Show last 7 days
        recent_data = analytics['data'][-7:]
        for date, revenue in recent_data:
            day_name = datetime.fromisoformat(date).strftime('%a')
            text += f"• {day_name} {date}: ₱{revenue:,.2f}\n"
        
        text += f"""

**Insights:**
• {'🟢 Strong' if analytics['average_daily'] > 1000 else '🟡 Moderate' if analytics['average_daily'] > 500 else '🔴 Low'} daily performance
• Best performing day: {datetime.fromisoformat(analytics['best_day'][0]).strftime('%A')}
• Revenue consistency: {'High' if max(dict(analytics['data']).values()) / analytics['average_daily'] < 2 else 'Variable'}

**Recommendations:**
• Focus marketing on low-revenue days
• Analyze best day patterns for replication
• Consider daily promotions to boost consistency
        """
        
        keyboard = [
            [InlineKeyboardButton("📈 Weekly View", callback_data="revenue_weekly")],
            [InlineKeyboardButton("📊 Monthly View", callback_data="revenue_monthly")],
            [InlineKeyboardButton("📋 Export Data", callback_data="export_daily_revenue")],
            [InlineKeyboardButton("🔙 Back", callback_data="revenue_analytics")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_monthly_revenue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show monthly revenue analytics"""
        query = update.callback_query
        await query.answer()
        
        analytics = self.financial_system.get_revenue_analytics('monthly')
        
        text = f"""
📊 **Monthly Revenue Analytics**

**Summary:**
• Total Revenue: ₱{analytics['total_revenue']:,.2f}
• Average Monthly: ₱{analytics['average_monthly']:,.2f}
• Best Month: {analytics['best_month'][0]} (₱{analytics['best_month'][1]:,.2f})

**Monthly Breakdown:**
"""
        
        # Show last 6 months
        recent_months = analytics['data'][-6:]
        for month, revenue in recent_months:
            month_name = datetime.strptime(month, '%Y-%m').strftime('%B %Y')
            text += f"• {month_name}: ₱{revenue:,.2f}\n"
        
        # Calculate month-over-month growth
        if len(recent_months) >= 2:
            current_month = recent_months[-1][1]
            previous_month = recent_months[-2][1]
            growth_rate = ((current_month - previous_month) / previous_month * 100) if previous_month > 0 else 0
            text += f"\n**Month-over-Month Growth:** {growth_rate:+.1f}%\n"
        
        text += f"""
**Performance Analysis:**
• {'🚀 Excellent' if analytics['average_monthly'] > 20000 else '📈 Good' if analytics['average_monthly'] > 10000 else '💪 Building'} monthly performance
• Peak season: {datetime.strptime(analytics['best_month'][0], '%Y-%m').strftime('%B')}
• Revenue trend: {'Growing' if growth_rate > 5 else 'Stable' if growth_rate > -5 else 'Declining'}

**Strategic Insights:**
• Plan inventory for peak months
• Analyze seasonal patterns
• Set realistic monthly targets
        """
        
        keyboard = [
            [InlineKeyboardButton("📅 Daily View", callback_data="revenue_daily")],
            [InlineKeyboardButton("📈 Trends Analysis", callback_data="financial_trends")],
            [InlineKeyboardButton("📋 Monthly Report", callback_data="generate_monthly_report")],
            [InlineKeyboardButton("🔙 Back", callback_data="revenue_analytics")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_payment_analytics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show payment method analytics"""
        query = update.callback_query
        await query.answer()
        
        analytics = self.financial_system.get_payment_method_analytics()
        
        text = f"""
💳 **Payment Method Analytics**

**Overview:**
• Total Payments: {analytics['total_payments']:,}
• Total Revenue: ₱{analytics['total_revenue']:,.2f}
• Most Popular: {analytics['most_popular'][0].title() if analytics['most_popular'] else 'N/A'}

**Method Breakdown:**
"""
        
        # Show each payment method
        for method, stats in analytics['methods'].items():
            method_emoji = {
                'gcash': '📱',
                'paymaya': '💳',
                'bank_transfer': '🏦',
                'cod': '💵'
            }.get(method, '💰')
            
            text += f"""
{method_emoji} **{method.replace('_', ' ').title()}:**
• Count: {stats['count']:,} payments ({stats['count_percentage']:.1f}%)
• Revenue: ₱{stats['revenue']:,.2f} ({stats['revenue_percentage']:.1f}%)
• Avg Amount: ₱{stats['avg_amount']:,.2f}
"""
        
        text += f"""
**Insights:**
• Digital payments: {sum(stats['count'] for method, stats in analytics['methods'].items() if method in ['gcash', 'paymaya'])} transactions
• Cash payments: {analytics['methods'].get('cod', {}).get('count', 0)} transactions
• Average digital amount: Higher convenience, faster processing
• COD usage: Good for customer trust building

**Recommendations:**
• Incentivize digital payments to reduce COD fees
• Optimize popular payment methods
• Consider adding more digital options
• Monitor payment success rates
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 Payment History", callback_data="payment_history")],
            [InlineKeyboardButton("💰 Fee Analysis", callback_data="payment_fees")],
            [InlineKeyboardButton("📈 Payment Trends", callback_data="payment_trends")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_financial_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_customer_analytics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show customer spending analytics"""
        query = update.callback_query
        await query.answer()
        
        analytics = self.financial_system.get_customer_spending_analytics()
        
        text = f"""
👥 **Customer Spending Analytics**

**Customer Segments:**
• 👑 VIP Customers: {analytics['vip_customers']} (₱1,000+)
• 🔄 Regular Customers: {analytics['regular_customers']} (₱100-1,000)
• 🆕 New Customers: {analytics['new_customers']} (<₱100)

**Key Metrics:**
• Total Active Customers: {analytics['total_customers']:,}
• Average Customer Value: ₱{analytics['avg_customer_value']:,.2f}

**Top 5 Customers:**
"""
        
        for i, (customer_id, data) in enumerate(analytics['top_spenders'][:5], 1):
            text += f"{i}. {data['first_name']}: ₱{data['total_spent']:,.2f} ({data['total_orders']} orders)\n"
        
        text += f"""

**Customer Distribution:**
• VIP: {analytics['vip_customers']/analytics['total_customers']*100:.1f}% of customers
• Regular: {analytics['regular_customers']/analytics['total_customers']*100:.1f}% of customers  
• New: {analytics['new_customers']/analytics['total_customers']*100:.1f}% of customers

**Business Health:**
• Customer Lifetime Value: ₱{analytics['avg_customer_value']:,.2f}
• VIP Customer Impact: Critical for revenue stability
• Growth Potential: {analytics['new_customers']} customers to convert

**Action Items:**
• Focus on converting new customers to regular
• Implement VIP loyalty programs
• Re-engage inactive customers
• Increase average customer value through upselling
        """
        
        keyboard = [
            [InlineKeyboardButton("👑 VIP Analysis", callback_data="vip_customer_analysis")],
            [InlineKeyboardButton("🆕 New Customer Trends", callback_data="new_customer_trends")],
            [InlineKeyboardButton("📊 Customer Lifetime Value", callback_data="customer_ltv")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_financial_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_financial_trends(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show financial trends and insights"""
        query = update.callback_query
        await query.answer()
        
        trends = self.financial_system.get_financial_trends()
        
        text = f"""
📈 **Financial Trends & Insights ({trends['period_analyzed']} days)**

**Revenue Trend:** {trends['revenue_trend'].title()} {'🚀' if trends['revenue_trend'] == 'growing' else '📊' if trends['revenue_trend'] == 'stable' else '⚠️'}

**Weekly Performance:**
• Average Weekly Revenue: ₱{trends['avg_weekly_revenue']:,.2f}
• Peak Week: ₱{trends['peak_week']['revenue']:,.2f} ({trends['peak_week']['week']})

**Recent Weekly Revenue:**
"""
        
        # Show last 4 weeks
        recent_weeks = trends['weekly_revenue'][-4:]
        for week_data in recent_weeks:
            text += f"• {week_data['week']}: ₱{week_data['revenue']:,.2f}\n"
        
        text += f"""

**AI-Generated Insights:**
"""
        for insight in trends['insights']:
            text += f"• {insight}\n"
        
        text += f"""

**Trend Analysis:**
• Business momentum: {'Strong' if trends['revenue_trend'] == 'growing' else 'Stable' if trends['revenue_trend'] == 'stable' else 'Needs attention'}
• Consistency: {'High' if trends['avg_weekly_revenue'] > 0 else 'Variable'}
• Growth opportunity: {'Excellent' if trends['revenue_trend'] == 'growing' else 'Good' if trends['revenue_trend'] == 'stable' else 'Action needed'}

**Recommendations:**
• {'Continue current strategies' if trends['revenue_trend'] == 'growing' else 'Maintain stability focus' if trends['revenue_trend'] == 'stable' else 'Implement growth initiatives'}
• Monitor weekly patterns for optimization
• Plan inventory based on peak periods
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 Detailed Analytics", callback_data="detailed_trends")],
            [InlineKeyboardButton("📈 Growth Strategies", callback_data="growth_strategies")],
            [InlineKeyboardButton("📋 Trend Report", callback_data="generate_trend_report")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_financial_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_profit_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show profit analysis"""
        query = update.callback_query
        await query.answer()
        
        analysis = self.financial_system.get_profit_analysis()
        
        text = f"""
💰 **Profit Analysis**

**Revenue Breakdown:**
• Total Revenue: ₱{analysis['total_revenue']:,.2f}
• Estimated Gross Profit: ₱{analysis['estimated_gross_profit']:,.2f}
• Payment Processing Fees: ₱{analysis['payment_fees']:,.2f}
• **Net Profit: ₱{analysis['estimated_net_profit']:,.2f}**

**Profitability Metrics:**
• Gross Profit Margin: 30.0% (estimated)
• Net Profit Margin: {analysis['profit_margin']:.1f}%
• Revenue after Fees: {(1 - analysis['payment_fees']/analysis['total_revenue'])*100:.1f}%

**Cost Analysis:**
• Payment Processing: ₱{analysis['cost_breakdown']['payment_fees']:,.2f}
• Cost of Goods (est.): ₱{analysis['cost_breakdown']['estimated_cogs']:,.2f}
• Total Costs: ₱{analysis['cost_breakdown']['payment_fees'] + analysis['cost_breakdown']['estimated_cogs']:,.2f}

**Performance Indicators:**
• {'🟢 Excellent' if analysis['profit_margin'] > 25 else '🟡 Good' if analysis['profit_margin'] > 15 else '🔴 Needs attention'} profit margin
• Payment efficiency: {'High' if analysis['payment_fees']/analysis['total_revenue'] < 0.03 else 'Moderate'}
• Business health: {'Strong' if analysis['estimated_net_profit'] > 0 else 'Critical'}

**Action Items:**
• {'Maintain current pricing strategy' if analysis['profit_margin'] > 20 else 'Review pricing and cost optimization'}
• Consider payment method fees in pricing
• Track actual product costs for accurate analysis
• Monitor profit trends monthly

*Note: Analysis uses estimated costs. Add actual product and operational costs for precision.*
        """
        
        keyboard = [
            [InlineKeyboardButton("💳 Payment Fee Details", callback_data="payment_fees_detail")],
            [InlineKeyboardButton("📊 Cost Optimization", callback_data="cost_optimization")],
            [InlineKeyboardButton("📈 Profit Trends", callback_data="profit_trends")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_financial_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_financial_reports(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show financial reports menu"""
        query = update.callback_query
        await query.answer()
        
        text = """
📋 **Financial Reports**

Generate comprehensive reports for different time periods:

**Available Reports:**
• **Daily Report** - Today's performance summary
• **Weekly Report** - 7-day analysis with trends  
• **Monthly Report** - Comprehensive monthly analysis
• **Custom Report** - Choose your own parameters

**Report Features:**
• Revenue and order analytics
• Customer behavior insights
• Payment method breakdown
• Growth trends and forecasts
• Actionable recommendations

Which report would you like to generate?
        """
        
        keyboard = [
            [InlineKeyboardButton("📅 Daily Report", callback_data="generate_daily_report")],
            [InlineKeyboardButton("📊 Weekly Report", callback_data="generate_weekly_report")],
            [InlineKeyboardButton("📈 Monthly Report", callback_data="generate_monthly_report")],
            [InlineKeyboardButton("🎯 Custom Report", callback_data="generate_custom_report")],
            [InlineKeyboardButton("📤 Export Data", callback_data="export_financial_data")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_financial_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def generate_daily_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate and show daily report"""
        query = update.callback_query
        await query.answer()
        
        report = self.financial_reporting.generate_daily_report()
        
        keyboard = [
            [InlineKeyboardButton("📊 Weekly Report", callback_data="generate_weekly_report")],
            [InlineKeyboardButton("📈 Monthly Report", callback_data="generate_monthly_report")],
            [InlineKeyboardButton("📤 Export Report", callback_data="export_daily_report")],
            [InlineKeyboardButton("🔙 Back", callback_data="financial_reports")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(report, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def generate_weekly_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate and show weekly report"""
        query = update.callback_query
        await query.answer()
        
        report = self.financial_reporting.generate_weekly_report()
        
        keyboard = [
            [InlineKeyboardButton("📅 Daily Report", callback_data="generate_daily_report")],
            [InlineKeyboardButton("📈 Monthly Report", callback_data="generate_monthly_report")],
            [InlineKeyboardButton("📤 Export Report", callback_data="export_weekly_report")],
            [InlineKeyboardButton("🔙 Back", callback_data="financial_reports")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(report, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def generate_monthly_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate and show monthly report"""
        query = update.callback_query
        await query.answer()
        
        report = self.financial_reporting.generate_monthly_report()
        
        keyboard = [
            [InlineKeyboardButton("📅 Daily Report", callback_data="generate_daily_report")],
            [InlineKeyboardButton("📊 Weekly Report", callback_data="generate_weekly_report")],
            [InlineKeyboardButton("📤 Export Report", callback_data="export_monthly_report")],
            [InlineKeyboardButton("🔙 Back", callback_data="financial_reports")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(report, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    def _is_admin(self, user_id):
        """Check if user is admin"""
        admin_ids = [123456789]  # Replace with actual admin IDs
        return user_id in admin_ids

# Callback query handlers for financial commands
def get_financial_callback_handlers():
    """Get all callback query handlers for financial commands"""
    financial_commands = FinancialCommands()
    
    return [
        CallbackQueryHandler(financial_commands.show_revenue_analytics, pattern="^revenue_analytics$"),
        CallbackQueryHandler(financial_commands.show_daily_revenue, pattern="^revenue_daily$"),
        CallbackQueryHandler(financial_commands.show_monthly_revenue, pattern="^revenue_monthly$"),
        CallbackQueryHandler(financial_commands.show_payment_analytics, pattern="^payment_analytics$"),
        CallbackQueryHandler(financial_commands.show_customer_analytics, pattern="^customer_analytics$"),
        CallbackQueryHandler(financial_commands.show_financial_trends, pattern="^financial_trends$"),
        CallbackQueryHandler(financial_commands.show_profit_analysis, pattern="^profit_analysis$"),
        CallbackQueryHandler(financial_commands.show_financial_reports, pattern="^financial_reports$"),
        CallbackQueryHandler(financial_commands.generate_daily_report, pattern="^generate_daily_report$"),
        CallbackQueryHandler(financial_commands.generate_weekly_report, pattern="^generate_weekly_report$"),
        CallbackQueryHandler(financial_commands.generate_monthly_report, pattern="^generate_monthly_report$")
    ]