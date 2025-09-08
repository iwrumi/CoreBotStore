"""
Financial Dashboard and Payment History Tracking System
Comprehensive financial analytics and reporting for store management
"""
import calendar
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from advanced_data_manager import AdvancedDataManager

class FinancialSystem:
    def __init__(self):
        self.data_manager = AdvancedDataManager()
    
    def get_dashboard_overview(self, days: int = 30) -> Dict:
        """Get comprehensive financial overview for dashboard"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all relevant data
        payments = self.data_manager.get_payments()
        orders = self.data_manager.get_orders()
        users = self.data_manager.get_users()
        
        # Filter by date range
        recent_payments = [
            p for p in payments 
            if datetime.fromisoformat(p['created_at']) >= start_date
        ]
        recent_orders = [
            o for o in orders
            if datetime.fromisoformat(o['created_at']) >= start_date
        ]
        
        # Calculate key metrics
        total_revenue = sum(p['amount'] for p in payments if p['status'] == 'completed')
        recent_revenue = sum(p['amount'] for p in recent_payments if p['status'] == 'completed')
        pending_revenue = sum(p['amount'] for p in payments if p['status'] == 'pending')
        
        total_orders = len(orders)
        recent_orders_count = len(recent_orders)
        
        # Calculate growth rates
        prev_start = start_date - timedelta(days=days)
        prev_payments = [
            p for p in payments
            if prev_start <= datetime.fromisoformat(p['created_at']) < start_date
        ]
        prev_revenue = sum(p['amount'] for p in prev_payments if p['status'] == 'completed')
        
        revenue_growth = 0
        if prev_revenue > 0:
            revenue_growth = ((recent_revenue - prev_revenue) / prev_revenue) * 100
        
        # Customer metrics
        active_customers = len(set(o['user_telegram_id'] for o in recent_orders))
        total_customers = len(users)
        
        # Average order value
        completed_orders = [o for o in orders if o['status'] in ['completed', 'delivered']]
        avg_order_value = sum(o['total'] for o in completed_orders) / len(completed_orders) if completed_orders else 0
        
        return {
            'period_days': days,
            'total_revenue': total_revenue,
            'recent_revenue': recent_revenue,
            'pending_revenue': pending_revenue,
            'revenue_growth': revenue_growth,
            'total_orders': total_orders,
            'recent_orders': recent_orders_count,
            'active_customers': active_customers,
            'total_customers': total_customers,
            'avg_order_value': avg_order_value,
            'conversion_rate': (recent_orders_count / active_customers * 100) if active_customers > 0 else 0
        }
    
    def get_revenue_analytics(self, period: str = 'monthly') -> Dict:
        """Get detailed revenue analytics by period"""
        
        payments = self.data_manager.get_payments()
        completed_payments = [p for p in payments if p['status'] == 'completed']
        
        if period == 'daily':
            return self._get_daily_revenue(completed_payments)
        elif period == 'weekly':
            return self._get_weekly_revenue(completed_payments)
        elif period == 'monthly':
            return self._get_monthly_revenue(completed_payments)
        elif period == 'yearly':
            return self._get_yearly_revenue(completed_payments)
        else:
            return {'error': 'Invalid period'}
    
    def _get_daily_revenue(self, payments: List[Dict], days: int = 30) -> Dict:
        """Get daily revenue for the last N days"""
        
        end_date = datetime.utcnow().date()
        revenue_by_day = {}
        
        # Initialize all days with 0
        for i in range(days):
            date = end_date - timedelta(days=i)
            revenue_by_day[date.isoformat()] = 0
        
        # Calculate actual revenue
        for payment in payments:
            payment_date = datetime.fromisoformat(payment['created_at']).date()
            if payment_date >= (end_date - timedelta(days=days)):
                date_key = payment_date.isoformat()
                revenue_by_day[date_key] += payment['amount']
        
        # Sort by date
        sorted_data = sorted(revenue_by_day.items())
        
        return {
            'period': 'daily',
            'data': sorted_data,
            'total_revenue': sum(revenue_by_day.values()),
            'average_daily': sum(revenue_by_day.values()) / len(revenue_by_day) if revenue_by_day else 0,
            'best_day': max(revenue_by_day.items(), key=lambda x: x[1]) if revenue_by_day else None,
            'days_analyzed': days
        }
    
    def _get_monthly_revenue(self, payments: List[Dict], months: int = 12) -> Dict:
        """Get monthly revenue for the last N months"""
        
        end_date = datetime.utcnow()
        revenue_by_month = {}
        
        # Initialize months with 0
        for i in range(months):
            date = end_date - timedelta(days=30*i)
            month_key = date.strftime('%Y-%m')
            revenue_by_month[month_key] = 0
        
        # Calculate actual revenue
        for payment in payments:
            payment_date = datetime.fromisoformat(payment['created_at'])
            month_key = payment_date.strftime('%Y-%m')
            if month_key in revenue_by_month:
                revenue_by_month[month_key] += payment['amount']
        
        # Sort by date
        sorted_data = sorted(revenue_by_month.items())
        
        return {
            'period': 'monthly',
            'data': sorted_data,
            'total_revenue': sum(revenue_by_month.values()),
            'average_monthly': sum(revenue_by_month.values()) / len(revenue_by_month) if revenue_by_month else 0,
            'best_month': max(revenue_by_month.items(), key=lambda x: x[1]) if revenue_by_month else None,
            'months_analyzed': months
        }
    
    def get_payment_method_analytics(self) -> Dict:
        """Get analytics by payment method"""
        
        payments = self.data_manager.get_payments()
        completed_payments = [p for p in payments if p['status'] == 'completed']
        
        method_stats = {}
        total_revenue = 0
        
        for payment in completed_payments:
            method = payment['payment_method']
            amount = payment['amount']
            
            if method not in method_stats:
                method_stats[method] = {
                    'count': 0,
                    'revenue': 0,
                    'avg_amount': 0
                }
            
            method_stats[method]['count'] += 1
            method_stats[method]['revenue'] += amount
            total_revenue += amount
        
        # Calculate percentages and averages
        for method in method_stats:
            stats = method_stats[method]
            stats['avg_amount'] = stats['revenue'] / stats['count']
            stats['revenue_percentage'] = (stats['revenue'] / total_revenue * 100) if total_revenue > 0 else 0
            stats['count_percentage'] = (stats['count'] / len(completed_payments) * 100) if completed_payments else 0
        
        # Sort by revenue
        sorted_methods = sorted(method_stats.items(), key=lambda x: x[1]['revenue'], reverse=True)
        
        return {
            'total_payments': len(completed_payments),
            'total_revenue': total_revenue,
            'methods': dict(sorted_methods),
            'most_popular': sorted_methods[0] if sorted_methods else None,
            'highest_revenue': sorted_methods[0] if sorted_methods else None
        }
    
    def get_customer_spending_analytics(self) -> Dict:
        """Get customer spending behavior analytics"""
        
        users = self.data_manager.get_users()
        orders = self.data_manager.get_orders()
        
        customer_stats = {}
        
        for user in users:
            user_id = user['telegram_id']
            user_orders = [o for o in orders if o['user_telegram_id'] == user_id]
            completed_orders = [o for o in user_orders if o['status'] in ['completed', 'delivered']]
            
            if completed_orders:
                total_spent = sum(o['total'] for o in completed_orders)
                avg_order = total_spent / len(completed_orders)
                
                customer_stats[user_id] = {
                    'first_name': user.get('first_name', 'Unknown'),
                    'total_orders': len(completed_orders),
                    'total_spent': total_spent,
                    'avg_order_value': avg_order,
                    'first_order': min(o['created_at'] for o in completed_orders),
                    'last_order': max(o['created_at'] for o in completed_orders)
                }
        
        # Categorize customers
        vip_customers = {k: v for k, v in customer_stats.items() if v['total_spent'] > 1000}
        regular_customers = {k: v for k, v in customer_stats.items() if 100 <= v['total_spent'] <= 1000}
        new_customers = {k: v for k, v in customer_stats.items() if v['total_spent'] < 100}
        
        # Top spenders
        top_spenders = sorted(customer_stats.items(), key=lambda x: x[1]['total_spent'], reverse=True)[:10]
        
        # Calculate averages
        all_spending = [v['total_spent'] for v in customer_stats.values()]
        avg_customer_value = sum(all_spending) / len(all_spending) if all_spending else 0
        
        return {
            'total_customers': len(customer_stats),
            'vip_customers': len(vip_customers),
            'regular_customers': len(regular_customers),
            'new_customers': len(new_customers),
            'avg_customer_value': avg_customer_value,
            'top_spenders': top_spenders,
            'customer_distribution': {
                'vip': len(vip_customers),
                'regular': len(regular_customers),
                'new': len(new_customers)
            }
        }
    
    def get_financial_trends(self, days: int = 90) -> Dict:
        """Get financial trends and insights"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        payments = self.data_manager.get_payments()
        orders = self.data_manager.get_orders()
        
        # Filter by date range
        recent_payments = [
            p for p in payments
            if datetime.fromisoformat(p['created_at']) >= start_date
        ]
        recent_orders = [
            o for o in orders
            if datetime.fromisoformat(o['created_at']) >= start_date
        ]
        
        # Weekly trends
        weekly_revenue = []
        weekly_orders = []
        
        for i in range(0, days, 7):
            week_start = start_date + timedelta(days=i)
            week_end = week_start + timedelta(days=7)
            
            week_payments = [
                p for p in recent_payments
                if week_start <= datetime.fromisoformat(p['created_at']) < week_end and p['status'] == 'completed'
            ]
            week_orders_count = len([
                o for o in recent_orders
                if week_start <= datetime.fromisoformat(o['created_at']) < week_end
            ])
            
            week_revenue = sum(p['amount'] for p in week_payments)
            
            weekly_revenue.append({
                'week': week_start.strftime('%Y-%m-%d'),
                'revenue': week_revenue
            })
            weekly_orders.append({
                'week': week_start.strftime('%Y-%m-%d'),
                'orders': week_orders_count
            })
        
        # Calculate trends
        recent_weeks = weekly_revenue[-4:] if len(weekly_revenue) >= 4 else weekly_revenue
        avg_recent_revenue = sum(w['revenue'] for w in recent_weeks) / len(recent_weeks) if recent_weeks else 0
        
        earlier_weeks = weekly_revenue[-8:-4] if len(weekly_revenue) >= 8 else weekly_revenue[:-4]
        avg_earlier_revenue = sum(w['revenue'] for w in earlier_weeks) / len(earlier_weeks) if earlier_weeks else 0
        
        revenue_trend = 'stable'
        if avg_recent_revenue > avg_earlier_revenue * 1.1:
            revenue_trend = 'growing'
        elif avg_recent_revenue < avg_earlier_revenue * 0.9:
            revenue_trend = 'declining'
        
        return {
            'period_analyzed': days,
            'weekly_revenue': weekly_revenue,
            'weekly_orders': weekly_orders,
            'revenue_trend': revenue_trend,
            'avg_weekly_revenue': sum(w['revenue'] for w in weekly_revenue) / len(weekly_revenue) if weekly_revenue else 0,
            'peak_week': max(weekly_revenue, key=lambda x: x['revenue']) if weekly_revenue else None,
            'insights': self._generate_financial_insights(weekly_revenue, weekly_orders)
        }
    
    def _generate_financial_insights(self, weekly_revenue: List[Dict], weekly_orders: List[Dict]) -> List[str]:
        """Generate actionable financial insights"""
        
        insights = []
        
        if not weekly_revenue:
            return ["Insufficient data for insights"]
        
        # Revenue trend analysis
        recent_revenue = sum(w['revenue'] for w in weekly_revenue[-4:]) if len(weekly_revenue) >= 4 else 0
        earlier_revenue = sum(w['revenue'] for w in weekly_revenue[-8:-4]) if len(weekly_revenue) >= 8 else 0
        
        if recent_revenue > earlier_revenue * 1.2:
            insights.append("🚀 Revenue is growing strongly! Consider scaling marketing efforts.")
        elif recent_revenue > earlier_revenue * 1.05:
            insights.append("📈 Revenue is showing positive growth. Keep up the good work!")
        elif recent_revenue < earlier_revenue * 0.8:
            insights.append("⚠️ Revenue is declining. Consider promotional campaigns or reviewing pricing.")
        
        # Order volume analysis
        if weekly_orders:
            recent_orders = sum(w['orders'] for w in weekly_orders[-4:]) if len(weekly_orders) >= 4 else 0
            avg_order_value = recent_revenue / recent_orders if recent_orders > 0 else 0
            
            if avg_order_value > 200:
                insights.append("💰 High average order value indicates premium customer base.")
            elif avg_order_value < 50:
                insights.append("💡 Consider upselling strategies to increase average order value.")
        
        # Consistency analysis
        revenues = [w['revenue'] for w in weekly_revenue]
        if revenues:
            import statistics
            std_dev = statistics.stdev(revenues) if len(revenues) > 1 else 0
            mean_revenue = statistics.mean(revenues)
            
            if std_dev < mean_revenue * 0.3:
                insights.append("🎯 Revenue is consistent, indicating stable business performance.")
            else:
                insights.append("📊 Revenue varies significantly. Consider analyzing seasonal patterns.")
        
        return insights[:3]  # Return top 3 insights
    
    def get_payment_history_detailed(self, 
                                   user_telegram_id: Optional[str] = None,
                                   start_date: Optional[datetime] = None,
                                   end_date: Optional[datetime] = None,
                                   status: Optional[str] = None,
                                   payment_method: Optional[str] = None,
                                   limit: int = 100) -> Dict:
        """Get detailed payment history with filters"""
        
        payments = self.data_manager.get_payments()
        
        # Apply filters
        if user_telegram_id:
            payments = [p for p in payments if p['user_telegram_id'] == user_telegram_id]
        
        if start_date:
            payments = [p for p in payments if datetime.fromisoformat(p['created_at']) >= start_date]
        
        if end_date:
            payments = [p for p in payments if datetime.fromisoformat(p['created_at']) <= end_date]
        
        if status:
            payments = [p for p in payments if p['status'] == status]
        
        if payment_method:
            payments = [p for p in payments if p['payment_method'] == payment_method]
        
        # Sort by date (newest first) and limit
        payments.sort(key=lambda x: x['created_at'], reverse=True)
        payments = payments[:limit]
        
        # Calculate summary
        total_amount = sum(p['amount'] for p in payments)
        completed_amount = sum(p['amount'] for p in payments if p['status'] == 'completed')
        pending_amount = sum(p['amount'] for p in payments if p['status'] == 'pending')
        
        return {
            'payments': payments,
            'count': len(payments),
            'total_amount': total_amount,
            'completed_amount': completed_amount,
            'pending_amount': pending_amount,
            'filters_applied': {
                'user_telegram_id': user_telegram_id,
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
                'status': status,
                'payment_method': payment_method,
                'limit': limit
            }
        }
    
    def export_financial_data(self, format: str = 'summary', period: str = 'monthly') -> Dict:
        """Export financial data for external analysis"""
        
        if format == 'summary':
            return {
                'dashboard': self.get_dashboard_overview(),
                'revenue_analytics': self.get_revenue_analytics(period),
                'payment_methods': self.get_payment_method_analytics(),
                'customer_analytics': self.get_customer_spending_analytics(),
                'trends': self.get_financial_trends(),
                'exported_at': datetime.utcnow().isoformat()
            }
        
        elif format == 'detailed':
            return {
                'all_payments': self.get_payment_history_detailed(limit=1000),
                'revenue_breakdown': self.get_revenue_analytics(period),
                'customer_details': self.get_customer_spending_analytics(),
                'exported_at': datetime.utcnow().isoformat()
            }
        
        else:
            return {'error': 'Invalid export format'}
    
    def get_profit_analysis(self) -> Dict:
        """Get profit analysis (simplified - would need cost data in real implementation)"""
        
        dashboard = self.get_dashboard_overview()
        payment_analytics = self.get_payment_method_analytics()
        
        # Simplified profit calculation (assumes 30% profit margin)
        # In real implementation, you'd have product costs, shipping costs, etc.
        estimated_profit_margin = 0.30
        total_revenue = dashboard['total_revenue']
        estimated_profit = total_revenue * estimated_profit_margin
        
        # Calculate fees (simplified)
        payment_fees = 0
        for method, stats in payment_analytics['methods'].items():
            if method == 'gcash':
                payment_fees += stats['revenue'] * 0.02  # 2% fee
            elif method == 'paymaya':
                payment_fees += stats['revenue'] * 0.025  # 2.5% fee
            elif method == 'cod':
                payment_fees += stats['count'] * 50  # ₱50 per COD
        
        net_profit = estimated_profit - payment_fees
        
        return {
            'total_revenue': total_revenue,
            'estimated_gross_profit': estimated_profit,
            'payment_fees': payment_fees,
            'estimated_net_profit': net_profit,
            'profit_margin': (net_profit / total_revenue * 100) if total_revenue > 0 else 0,
            'cost_breakdown': {
                'payment_fees': payment_fees,
                'estimated_cogs': total_revenue * 0.70  # 70% cost assumption
            },
            'note': 'Profit analysis is estimated. Add actual product costs for accurate calculations.'
        }

class FinancialReporting:
    """Generate financial reports for different stakeholders"""
    
    def __init__(self):
        self.financial_system = FinancialSystem()
    
    def generate_daily_report(self) -> str:
        """Generate daily financial summary report"""
        
        dashboard = self.financial_system.get_dashboard_overview(days=1)
        yesterday_dashboard = self.financial_system.get_dashboard_overview(days=2)
        
        # Calculate daily changes
        revenue_change = dashboard['recent_revenue'] - (yesterday_dashboard['recent_revenue'] - dashboard['recent_revenue'])
        orders_change = dashboard['recent_orders'] - (yesterday_dashboard['recent_orders'] - dashboard['recent_orders'])
        
        report = f"""
📊 **Daily Financial Report - {datetime.utcnow().strftime('%Y-%m-%d')}**

**Today's Performance:**
💰 Revenue: ₱{dashboard['recent_revenue']:,.2f}
📦 Orders: {dashboard['recent_orders']}
👥 Active Customers: {dashboard['active_customers']}

**Daily Change:**
{'📈' if revenue_change >= 0 else '📉'} Revenue: ₱{revenue_change:+,.2f}
{'📈' if orders_change >= 0 else '📉'} Orders: {orders_change:+d}

**Key Metrics:**
💵 Avg Order Value: ₱{dashboard['avg_order_value']:.2f}
⏳ Pending Revenue: ₱{dashboard['pending_revenue']:,.2f}
📊 Total Customers: {dashboard['total_customers']:,}

**Status:** {'🟢 Good' if dashboard['recent_revenue'] > 0 else '🟡 Monitor'}
        """
        
        return report.strip()
    
    def generate_weekly_report(self) -> str:
        """Generate weekly financial summary report"""
        
        dashboard = self.financial_system.get_dashboard_overview(days=7)
        trends = self.financial_system.get_financial_trends(days=21)
        payment_analytics = self.financial_system.get_payment_method_analytics()
        
        report = f"""
📈 **Weekly Financial Report - {datetime.utcnow().strftime('Week of %Y-%m-%d')}**

**Week Summary:**
💰 Total Revenue: ₱{dashboard['recent_revenue']:,.2f}
📦 Total Orders: {dashboard['recent_orders']}
📊 Growth Rate: {dashboard['revenue_growth']:+.1f}%
💵 Avg Order Value: ₱{dashboard['avg_order_value']:.2f}

**Trends:**
📊 Revenue Trend: {trends['revenue_trend'].title()}
⭐ Peak Week: ₱{trends['peak_week']['revenue']:,.2f} if trends['peak_week'] else 'N/A'}

**Payment Methods:**
"""
        
        for method, stats in list(payment_analytics['methods'].items())[:3]:
            report += f"• {method.title()}: ₱{stats['revenue']:,.2f} ({stats['revenue_percentage']:.1f}%)\n"
        
        report += f"""
**Insights:**
"""
        for insight in trends['insights']:
            report += f"• {insight}\n"
        
        return report.strip()
    
    def generate_monthly_report(self) -> str:
        """Generate comprehensive monthly financial report"""
        
        dashboard = self.financial_system.get_dashboard_overview(days=30)
        revenue_analytics = self.financial_system.get_revenue_analytics('monthly')
        customer_analytics = self.financial_system.get_customer_spending_analytics()
        profit_analysis = self.financial_system.get_profit_analysis()
        
        current_month = datetime.utcnow().strftime('%B %Y')
        
        report = f"""
📈 **Monthly Financial Report - {current_month}**

**Revenue Overview:**
💰 Total Revenue: ₱{dashboard['recent_revenue']:,.2f}
📊 Growth Rate: {dashboard['revenue_growth']:+.1f}%
💵 Avg Order Value: ₱{dashboard['avg_order_value']:.2f}
📦 Total Orders: {dashboard['recent_orders']:,}

**Customer Analytics:**
👥 Total Customers: {customer_analytics['total_customers']:,}
👑 VIP Customers: {customer_analytics['vip_customers']}
💎 Avg Customer Value: ₱{customer_analytics['avg_customer_value']:.2f}

**Profitability:**
💰 Gross Profit: ₱{profit_analysis['estimated_gross_profit']:,.2f}
💳 Payment Fees: ₱{profit_analysis['payment_fees']:,.2f}
📊 Net Profit: ₱{profit_analysis['estimated_net_profit']:,.2f}
📈 Profit Margin: {profit_analysis['profit_margin']:.1f}%

**Top Performers:**
"""
        
        for i, (customer_id, data) in enumerate(customer_analytics['top_spenders'][:3], 1):
            report += f"{i}. {data['first_name']}: ₱{data['total_spent']:,.2f}\n"
        
        report += f"""
**Monthly Targets:**
{'✅ Revenue Target Met' if dashboard['recent_revenue'] > 50000 else '⚠️ Revenue Below Target'}
{'✅ Order Target Met' if dashboard['recent_orders'] > 100 else '⚠️ Order Target Below Expected'}

**Recommendations:**
• Focus on customer retention programs
• Optimize payment methods for lower fees
• Implement upselling strategies
• Monitor cash flow closely
        """
        
        return report.strip()