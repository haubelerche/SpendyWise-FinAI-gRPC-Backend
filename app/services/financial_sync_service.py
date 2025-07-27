 """
Financial Sync Service
Handles silent background updates của financial data sau khi AI ghi chép transactions
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.db.session import get_db
from app.models.transactions import Transaction
from app.models.users import User
from app.models.budgets import Budget
from app.core.constants import TransactionType, BudgetStatus

logger = logging.getLogger(__name__)


class FinancialSyncService:
    """
    Service để đồng bộ và cập nhật financial data ngầm
    sau khi AI tự động tạo transactions
    """
    
    async def sync_user_financials_after_ai_transaction(
        self, 
        user_id: str, 
        transaction: Transaction,
        db: Session
    ) -> Dict[str, Any]:
        """
        Comprehensive sync sau khi AI tạo transaction
        
        Returns:
            Dict với summary của updates được thực hiện
        """
        sync_results = {
            'user_id': user_id,
            'transaction_id': str(transaction.transaction_id),
            'updates_performed': [],
            'alerts_generated': [],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            # 1. Update user balance
            balance_updated = await self._update_user_balance(user_id, transaction, db)
            if balance_updated:
                sync_results['updates_performed'].append('user_balance')
            
            # 2. Update budget spending
            budget_updates = await self._update_affected_budgets(user_id, transaction, db)
            if budget_updates:
                sync_results['updates_performed'].extend(budget_updates)
            
            # 3. Check for spending alerts
            alerts = await self._check_spending_alerts(user_id, transaction, db)
            if alerts:
                sync_results['alerts_generated'].extend(alerts)
            
            # 4. Update spending streaks and habits
            habits_updated = await self._update_spending_habits(user_id, transaction, db)
            if habits_updated:
                sync_results['updates_performed'].append('spending_habits')
            
            # 5. Recalculate financial health score
            health_score = await self._recalculate_financial_health(user_id, db)
            if health_score:
                sync_results['updates_performed'].append('financial_health_score')
                sync_results['new_health_score'] = health_score
            
            db.commit()
            logger.info(f"Financial sync completed for user {user_id}: {len(sync_results['updates_performed'])} updates")
            
        except Exception as e:
            logger.error(f"Error in financial sync: {str(e)}")
            db.rollback()
            sync_results['error'] = str(e)
        
        return sync_results

    async def _update_user_balance(self, user_id: str, transaction: Transaction, db: Session) -> bool:
        """Update user's current balance"""
        try:
            user = db.query(User).filter(User.user_id == UUID(user_id)).first()
            if not user:
                return False
            
            # Initialize balance if not exists
            if not hasattr(user, 'current_balance') or user.current_balance is None:
                user.current_balance = Decimal('0')
            
            # Update balance based on transaction type
            if transaction.is_expense:
                user.current_balance -= transaction.amount
            elif transaction.is_income:
                user.current_balance += transaction.amount
            
            # Update last transaction date
            if hasattr(user, 'last_transaction_date'):
                user.last_transaction_date = transaction.transaction_date
            
            # Update metadata
            if hasattr(user, 'metadata_'):
                if not user.metadata_:
                    user.metadata_ = {}
                user.metadata_['last_ai_transaction'] = {
                    'transaction_id': str(transaction.transaction_id),
                    'amount': float(transaction.amount),
                    'type': transaction.transaction_type,
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating user balance: {str(e)}")
            return False

    async def _update_affected_budgets(self, user_id: str, transaction: Transaction, db: Session) -> List[str]:
        """Update budgets affected by new transaction"""
        if not transaction.is_expense:
            return []
        
        updates_performed = []
        
        try:
            # Find budgets that apply to this transaction
            current_month = date.today().replace(day=1)
            
            # Category-specific budgets
            category_budgets = db.query(Budget).filter(
                and_(
                    Budget.user_id == UUID(user_id),
                    Budget.category_id == transaction.category,
                    Budget.status == BudgetStatus.ACTIVE.value,
                    Budget.start_date <= current_month
                )
            ).all()
            
            # Overall budgets
            overall_budgets = db.query(Budget).filter(
                and_(
                    Budget.user_id == UUID(user_id),
                    Budget.category_id.is_(None),
                    Budget.status == BudgetStatus.ACTIVE.value,
                    Budget.start_date <= current_month
                )
            ).all()
            
            all_budgets = category_budgets + overall_budgets
            
            for budget in all_budgets:
                # Update spent amount
                budget.spent_amount = (budget.spent_amount or Decimal('0')) + transaction.amount
                
                # Recalculate percentage
                if budget.budget_amount > 0:
                    budget.spending_percentage = float(budget.spent_amount / budget.budget_amount * 100)
                
                # Update status flags
                if budget.spent_amount > budget.budget_amount:
                    budget.is_over_budget = True
                    updates_performed.append(f'budget_overspent_{budget.budget_id}')
                elif budget.spending_percentage >= 90:
                    updates_performed.append(f'budget_warning_{budget.budget_id}')
                
                # Update metadata
                if hasattr(budget, 'metadata_'):
                    if not budget.metadata_:
                        budget.metadata_ = {}
                    budget.metadata_['last_ai_transaction'] = {
                        'transaction_id': str(transaction.transaction_id),
                        'amount': float(transaction.amount),
                        'new_total': float(budget.spent_amount),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                
                updates_performed.append(f'budget_updated_{budget.budget_id}')
            
        except Exception as e:
            logger.error(f"Error updating budgets: {str(e)}")
        
        return updates_performed

    async def _check_spending_alerts(self, user_id: str, transaction: Transaction, db: Session) -> List[Dict[str, Any]]:
        """Check for spending alerts based on new transaction"""
        alerts = []
        
        try:
            # Daily spending threshold
            today_start = datetime.combine(date.today(), datetime.min.time())
            today_spending = db.query(func.sum(Transaction.amount)).filter(
                and_(
                    Transaction.user_id == UUID(user_id),
                    Transaction.transaction_type == TransactionType.EXPENSE.value,
                    Transaction.created_at >= today_start
                )
            ).scalar() or Decimal('0')
            
            if today_spending > 1000000:  # 1M VND per day
                alerts.append({
                    'type': 'high_daily_spending',
                    'message': f'High daily spending detected: {today_spending:,.0f} VND',
                    'amount': float(today_spending),
                    'threshold': 1000000
                })
            
            # Unusual category spending
            if transaction.amount > 500000:  # 500k VND
                alerts.append({
                    'type': 'large_transaction',
                    'message': f'Large {transaction.category} expense: {transaction.amount:,.0f} VND',
                    'amount': float(transaction.amount),
                    'category': transaction.category
                })
            
            # Frequent spending in short time
            last_hour = datetime.utcnow() - timedelta(hours=1)
            recent_transactions = db.query(Transaction).filter(
                and_(
                    Transaction.user_id == UUID(user_id),
                    Transaction.transaction_type == TransactionType.EXPENSE.value,
                    Transaction.created_at >= last_hour
                )
            ).count()
            
            if recent_transactions >= 3:
                alerts.append({
                    'type': 'frequent_spending',
                    'message': f'{recent_transactions} transactions in the last hour',
                    'count': recent_transactions,
                    'timeframe': '1_hour'
                })
                
        except Exception as e:
            logger.error(f"Error checking spending alerts: {str(e)}")
        
        return alerts

    async def _update_spending_habits(self, user_id: str, transaction: Transaction, db: Session) -> bool:
        """Update user spending habits and patterns"""
        try:
            # This would update user spending habit tracking
            # For now, just update metadata
            user = db.query(User).filter(User.user_id == UUID(user_id)).first()
            if not user:
                return False
            
            if hasattr(user, 'metadata_'):
                if not user.metadata_:
                    user.metadata_ = {}
                
                # Update spending patterns
                habits = user.metadata_.get('spending_habits', {})
                category = transaction.category
                
                if category not in habits:
                    habits[category] = {
                        'total_amount': 0,
                        'transaction_count': 0,
                        'last_transaction': None
                    }
                
                habits[category]['total_amount'] += float(transaction.amount)
                habits[category]['transaction_count'] += 1
                habits[category]['last_transaction'] = datetime.utcnow().isoformat()
                
                user.metadata_['spending_habits'] = habits
                user.metadata_['last_habit_update'] = datetime.utcnow().isoformat()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating spending habits: {str(e)}")
            return False

    async def _recalculate_financial_health(self, user_id: str, db: Session) -> Optional[int]:
        """Recalculate user's financial health score"""
        try:
            # Get recent financial data
            last_30_days = date.today() - timedelta(days=30)
            
            # Total income and expenses
            income_total = db.query(func.sum(Transaction.amount)).filter(
                and_(
                    Transaction.user_id == UUID(user_id),
                    Transaction.transaction_type == TransactionType.INCOME.value,
                    Transaction.transaction_date >= last_30_days
                )
            ).scalar() or Decimal('0')
            
            expense_total = db.query(func.sum(Transaction.amount)).filter(
                and_(
                    Transaction.user_id == UUID(user_id),
                    Transaction.transaction_type == TransactionType.EXPENSE.value,
                    Transaction.transaction_date >= last_30_days
                )
            ).scalar() or Decimal('0')
            
            # Calculate basic health score
            health_score = 50  # Base score
            
            if income_total > 0:
                savings_rate = (income_total - expense_total) / income_total
                
                if savings_rate > 0.2:  # 20% savings rate
                    health_score += 30
                elif savings_rate > 0.1:  # 10% savings rate
                    health_score += 20
                elif savings_rate > 0:
                    health_score += 10
                else:
                    health_score -= 20  # Spending more than earning
            
            # Budget adherence bonus
            active_budgets = db.query(Budget).filter(
                and_(
                    Budget.user_id == UUID(user_id),
                    Budget.status == BudgetStatus.ACTIVE.value
                )
            ).all()
            
            if active_budgets:
                over_budget_count = len([b for b in active_budgets if b.is_over_budget])
                if over_budget_count == 0:
                    health_score += 20
                elif over_budget_count / len(active_budgets) < 0.5:
                    health_score += 10
            
            # Ensure score is within bounds
            health_score = max(0, min(100, health_score))
            
            # Update user record
            user = db.query(User).filter(User.user_id == UUID(user_id)).first()
            if user and hasattr(user, 'financial_health_score'):
                user.financial_health_score = health_score
                
            return health_score
            
        except Exception as e:
            logger.error(f"Error recalculating financial health: {str(e)}")
            return None

    async def get_sync_summary(self, user_id: str, days: int = 7, db: Session = None) -> Dict[str, Any]:
        """Get summary of AI-generated transactions và sync activities"""
        
        if not db:
            db = next(get_db())
        
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # AI-generated transactions
            ai_transactions = db.query(Transaction).filter(
                and_(
                    Transaction.user_id == UUID(user_id),
                    Transaction.is_ai_generated == True,
                    Transaction.transaction_date >= start_date
                )
            ).all()
            
            # Calculate summary
            total_ai_amount = sum(t.amount for t in ai_transactions)
            ai_expenses = [t for t in ai_transactions if t.is_expense]
            ai_income = [t for t in ai_transactions if t.is_income]
            
            return {
                'period_days': days,
                'ai_transactions_count': len(ai_transactions),
                'ai_expenses_count': len(ai_expenses),
                'ai_income_count': len(ai_income),
                'total_ai_amount': float(total_ai_amount),
                'average_confidence': sum(t.extraction_confidence for t in ai_transactions) / len(ai_transactions) if ai_transactions else 0,
                'categories_affected': list(set(t.category for t in ai_transactions)),
                'needs_review_count': len([t for t in ai_transactions if t.needs_review]),
                'verified_count': len([t for t in ai_transactions if t.is_verified])
            }
            
        except Exception as e:
            logger.error(f"Error getting sync summary: {str(e)}")
            return {'error': str(e)}
