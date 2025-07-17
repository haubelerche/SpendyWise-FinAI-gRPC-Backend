"""
Financial Calculations Utility
Core financial math functions for the AI advisor
"""
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP


class FinancialCalculator:
    """
    Comprehensive financial calculations for AI advisor recommendations
    """
    
    @staticmethod
    def calculate_emergency_fund_target(monthly_expenses: float, months: int = 6) -> float:
        """Calculate recommended emergency fund amount"""
        return monthly_expenses * months
    
    @staticmethod
    def debt_snowball_plan(debts: List[Dict]) -> List[Dict]:
        """
        Calculate debt payoff using snowball method (smallest balance first)
        
        Args:
            debts: List of dicts with 'balance', 'minimum_payment', 'name', 'interest_rate'
        """
        # Sort by balance (smallest first)
        sorted_debts = sorted(debts, key=lambda x: x['balance'])
        
        plan = []
        for i, debt in enumerate(sorted_debts):
            plan.append({
                'name': debt['name'],
                'balance': debt['balance'],
                'minimum_payment': debt['minimum_payment'],
                'order': i + 1,
                'strategy': 'snowball'
            })
        
        return plan
    
    @staticmethod
    def debt_avalanche_plan(debts: List[Dict]) -> List[Dict]:
        """
        Calculate debt payoff using avalanche method (highest interest first)
        
        Args:
            debts: List of dicts with 'balance', 'minimum_payment', 'name', 'interest_rate'
        """
        # Sort by interest rate (highest first)
        sorted_debts = sorted(debts, key=lambda x: x['interest_rate'], reverse=True)
        
        plan = []
        for i, debt in enumerate(sorted_debts):
            plan.append({
                'name': debt['name'],
                'balance': debt['balance'],
                'minimum_payment': debt['minimum_payment'],
                'interest_rate': debt['interest_rate'],
                'order': i + 1,
                'strategy': 'avalanche'
            })
        
        return plan
    
    @staticmethod
    def calculate_debt_payoff_time(
        balance: float, 
        payment: float, 
        interest_rate: float
    ) -> Tuple[int, float]:
        """
        Calculate months to pay off debt and total interest paid
        
        Returns:
            (months_to_payoff, total_interest_paid)
        """
        if payment <= 0 or balance <= 0:
            return 0, 0.0
        
        monthly_rate = interest_rate / 100 / 12
        
        if monthly_rate == 0:
            months = math.ceil(balance / payment)
            return months, 0.0
        
        if payment <= balance * monthly_rate:
            # Payment too small - will never pay off
            return float('inf'), float('inf')
        
        months = math.ceil(
            -math.log(1 - (balance * monthly_rate) / payment) / math.log(1 + monthly_rate)
        )
        
        total_paid = payment * months
        total_interest = total_paid - balance
        
        return months, total_interest
    
    @staticmethod
    def calculate_savings_goal_timeline(
        current_savings: float,
        goal_amount: float,
        monthly_contribution: float,
        annual_interest_rate: float = 0.02
    ) -> Dict:
        """
        Calculate timeline to reach savings goal with compound interest
        """
        if monthly_contribution <= 0:
            return {"error": "Monthly contribution must be positive"}
        
        remaining_amount = goal_amount - current_savings
        if remaining_amount <= 0:
            return {"status": "goal_already_met", "months": 0}
        
        monthly_rate = annual_interest_rate / 12
        
        if monthly_rate == 0:
            months = math.ceil(remaining_amount / monthly_contribution)
        else:
            # Future value of annuity formula
            months = math.ceil(
                math.log(1 + (goal_amount * monthly_rate) / monthly_contribution) / 
                math.log(1 + monthly_rate)
            )
        
        return {
            "months_to_goal": months,
            "years_to_goal": round(months / 12, 1),
            "total_contributions": monthly_contribution * months,
            "interest_earned": goal_amount - current_savings - (monthly_contribution * months)
        }
    
    @staticmethod
    def calculate_budget_percentages(monthly_income: float) -> Dict[str, float]:
        """
        Calculate recommended budget percentages based on 50/30/20 rule
        """
        return {
            "needs": monthly_income * 0.50,
            "wants": monthly_income * 0.30,
            "savings_debt": monthly_income * 0.20,
            "breakdown": {
                "housing": monthly_income * 0.25,
                "food": monthly_income * 0.10,
                "transportation": monthly_income * 0.15,
                "utilities": monthly_income * 0.05,
                "entertainment": monthly_income * 0.10,
                "personal": monthly_income * 0.05,
                "shopping": monthly_income * 0.10,
                "emergency_fund": monthly_income * 0.10,
                "retirement": monthly_income * 0.10
            }
        }
    
    @staticmethod
    def calculate_financial_health_score(financial_data: Dict) -> int:
        """
        Calculate financial health score (0-100)
        """
        score = 0
        
        # Emergency fund (25 points max)
        emergency_fund = financial_data.get('emergency_fund', 0)
        monthly_expenses = financial_data.get('monthly_expenses', 1)
        emergency_months = emergency_fund / monthly_expenses if monthly_expenses > 0 else 0
        
        if emergency_months >= 6:
            score += 25
        elif emergency_months >= 3:
            score += 20
        elif emergency_months >= 1:
            score += 15
        elif emergency_months > 0:
            score += 10
        
        # Debt-to-income ratio (25 points max)
        debt_to_income = financial_data.get('debt_to_income_ratio', 0)
        if debt_to_income <= 0.1:
            score += 25
        elif debt_to_income <= 0.2:
            score += 20
        elif debt_to_income <= 0.3:
            score += 15
        elif debt_to_income <= 0.4:
            score += 10
        elif debt_to_income <= 0.5:
            score += 5
        
        # Savings rate (25 points max)
        savings_rate = financial_data.get('savings_rate', 0)
        if savings_rate >= 0.2:
            score += 25
        elif savings_rate >= 0.15:
            score += 20
        elif savings_rate >= 0.1:
            score += 15
        elif savings_rate >= 0.05:
            score += 10
        elif savings_rate > 0:
            score += 5
        
        # Budget adherence (25 points max)
        budget_adherence = financial_data.get('budget_adherence', 0.5)
        if budget_adherence >= 0.95:
            score += 25
        elif budget_adherence >= 0.9:
            score += 20
        elif budget_adherence >= 0.8:
            score += 15
        elif budget_adherence >= 0.7:
            score += 10
        elif budget_adherence >= 0.6:
            score += 5
        
        return min(100, max(0, score))
    
    @staticmethod
    def compound_interest_calculator(
        principal: float,
        annual_rate: float,
        years: int,
        compounds_per_year: int = 12
    ) -> Dict:
        """
        Calculate compound interest growth
        """
        rate_per_period = annual_rate / compounds_per_year
        total_periods = years * compounds_per_year
        
        final_amount = principal * (1 + rate_per_period) ** total_periods
        interest_earned = final_amount - principal
        
        return {
            "final_amount": round(final_amount, 2),
            "interest_earned": round(interest_earned, 2),
            "principal": principal,
            "growth_factor": round(final_amount / principal, 2)
        }
    
    @staticmethod
    def investment_return_calculator(
        monthly_investment: float,
        annual_return: float,
        years: int
    ) -> Dict:
        """
        Calculate investment returns with monthly contributions
        """
        monthly_rate = annual_return / 12
        months = years * 12
        
        if monthly_rate == 0:
            final_amount = monthly_investment * months
            return {
                "final_amount": final_amount,
                "total_contributions": final_amount,
                "investment_gains": 0
            }
        
        # Future value of ordinary annuity
        final_amount = monthly_investment * (
            ((1 + monthly_rate) ** months - 1) / monthly_rate
        )
        
        total_contributions = monthly_investment * months
        investment_gains = final_amount - total_contributions
        
        return {
            "final_amount": round(final_amount, 2),
            "total_contributions": round(total_contributions, 2),
            "investment_gains": round(investment_gains, 2),
            "return_multiple": round(final_amount / total_contributions, 2)
        }
    
    @staticmethod
    def retirement_calculator(
        current_age: int,
        retirement_age: int,
        current_savings: float,
        monthly_contribution: float,
        expected_return: float = 0.07
    ) -> Dict:
        """
        Calculate retirement savings projection
        """
        years_to_retirement = retirement_age - current_age
        
        if years_to_retirement <= 0:
            return {"error": "Already at or past retirement age"}
        
        # Growth of current savings
        current_savings_growth = FinancialCalculator.compound_interest_calculator(
            current_savings, expected_return, years_to_retirement
        )
        
        # Growth of monthly contributions
        if monthly_contribution > 0:
            contribution_growth = FinancialCalculator.investment_return_calculator(
                monthly_contribution, expected_return, years_to_retirement
            )
        else:
            contribution_growth = {
                "final_amount": 0,
                "total_contributions": 0,
                "investment_gains": 0
            }
        
        total_retirement_savings = (
            current_savings_growth["final_amount"] + 
            contribution_growth["final_amount"]
        )
        
        # Rule of thumb: need 25x annual expenses for retirement
        recommended_savings = 25 * (monthly_contribution * 12 * 10)  # Rough estimate
        
        return {
            "projected_retirement_savings": round(total_retirement_savings, 2),
            "current_savings_growth": current_savings_growth,
            "contribution_growth": contribution_growth,
            "years_to_retirement": years_to_retirement,
            "on_track": total_retirement_savings >= recommended_savings,
            "monthly_shortfall": max(0, (recommended_savings - total_retirement_savings) / (years_to_retirement * 12))
        }
    
    @staticmethod
    def loan_affordability_calculator(
        monthly_income: float,
        monthly_debt_payments: float,
        interest_rate: float,
        loan_term_years: int,
        debt_to_income_limit: float = 0.28
    ) -> Dict:
        """
        Calculate maximum affordable loan amount
        """
        available_for_debt = monthly_income * debt_to_income_limit
        available_for_new_loan = available_for_debt - monthly_debt_payments
        
        if available_for_new_loan <= 0:
            return {
                "max_loan_amount": 0,
                "monthly_payment": 0,
                "error": "Current debt too high for additional loans"
            }
        
        monthly_rate = interest_rate / 100 / 12
        total_payments = loan_term_years * 12
        
        if monthly_rate == 0:
            max_loan = available_for_new_loan * total_payments
        else:
            # Present value of annuity formula
            max_loan = available_for_new_loan * (
                (1 - (1 + monthly_rate) ** -total_payments) / monthly_rate
            )
        
        return {
            "max_loan_amount": round(max_loan, 2),
            "monthly_payment": round(available_for_new_loan, 2),
            "debt_to_income_ratio": round((monthly_debt_payments + available_for_new_loan) / monthly_income, 3)
        }
