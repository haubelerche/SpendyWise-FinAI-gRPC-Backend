from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List
from app.core.constants import RecurrenceFrequency, BudgetStatus, BudgetPeriod
from supabase import Client
from app.db.supabase_client import get_supabase_client
import uuid

supabase: Client = get_supabase_client()

class Budget(BaseModel):
    budget_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique budget identifier")
    user_id: uuid.UUID = Field(..., description="User identifier (foreign key to users.user_id)")
    name: str = Field(..., min_length=1, max_length=100, description="Budget name")
    amount: Decimal = Field(..., ge=0, description="Budget amount")
    spent_amount: Decimal = Field(default=Decimal('0'), description="Amount spent so far")
    start_date: date = Field(..., description="Start date of the budget period")
    end_date: Optional[date] = Field(default=None, description="End date of the budget period")
    status: BudgetStatus = Field(default=BudgetStatus.ACTIVE, description="Budget status")
    alert_threshold: int = Field(default=80, ge=0, le=100, description="Alert threshold percentage")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    category_id: Optional[uuid.UUID] = Field(default=None, description="Expense category ID (foreign key to categories.category_id)")

    @classmethod
    def from_supabase(cls, data: dict) -> 'Budget':
        """Convert Supabase data to Budget model instance."""
        from dateutil.parser import parse
        return cls(
            budget_id=uuid.UUID(data['budget_id']),
            user_id=uuid.UUID(data['user_id']),
            name=data['name'],
            amount=Decimal(str(data['amount'])),
            spent_amount=Decimal(str(data.get('spent_amount', '0'))),
            start_date=parse(data['start_date']).date() if data.get('start_date') else None,
            end_date=parse(data['end_date']).date() if data.get('end_date') else None,
            status=BudgetStatus(data['status']),
            alert_threshold=data.get('alert_threshold', 80),
            created_at=parse(data['created_at']) if data.get('created_at') else None,
            updated_at=parse(data['updated_at']) if data.get('updated_at') else None,
            category_id=uuid.UUID(data.get('category_id')) if data.get('category_id') else None
        )

    def save_to_supabase(self) -> bool:
        """Create or update budget data in Supabase."""
        data = self.model_dump(exclude_unset=True)
        data['amount'] = str(data['amount'])
        data['spent_amount'] = str(data['spent_amount'])
        data['start_date'] = data['start_date'].isoformat()
        data['end_date'] = data['end_date'].isoformat() if data['end_date'] else None
        data['created_at'] = data['created_at'].isoformat()
        data['updated_at'] = datetime.utcnow().isoformat()

        if self.budget_id:
            response = supabase.table('budgets').update(data).eq('budget_id', str(self.budget_id)).execute()
        else:
            response = supabase.table('budgets').insert(data).execute()
            self.budget_id = uuid.UUID(response.data[0]['budget_id'])

        return response.status_code == 200 or response.status_code == 201