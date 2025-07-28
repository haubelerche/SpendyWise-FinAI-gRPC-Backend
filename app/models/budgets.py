from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date, datetime, timezone
from typing import Optional
import uuid
from app.core.constants import BudgetStatus
from supabase import Client, PostgrestAPIError
from app.db.supabase_client import get_supabase_client

supabase: Client = get_supabase_client()

class Budget(BaseModel):
    budget_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique budget identifier")
    user_id: uuid.UUID = Field(..., description="User identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Budget name")
    amount: Decimal = Field(..., ge=0, description="Budget amount")
    spent_amount: Decimal = Field(default=Decimal('0'), description="Amount spent so far")
    start_date: date = Field(..., description="Start date of the budget period")
    end_date: Optional[date] = Field(default=None, description="End date of the budget period")
    status: BudgetStatus = Field(default=BudgetStatus.ACTIVE, description="Budget status")
    alert_threshold: int = Field(default=80, ge=0, le=100, description="Alert threshold percentage")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    category_id: Optional[uuid.UUID] = Field(default=None, description="Expense category ID")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: str,
            Decimal: str,
        }

class BudgetCreate(BaseModel):
    user_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=100)
    amount: Decimal = Field(..., ge=0)
    start_date: date = Field(...)
    end_date: Optional[date] = Field(default=None)
    status: BudgetStatus = Field(default=BudgetStatus.ACTIVE)
    alert_threshold: int = Field(default=80, ge=0, le=100)
    category_id: Optional[uuid.UUID] = Field(default=None)

class BudgetUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    amount: Optional[Decimal] = Field(default=None, ge=0)
    spent_amount: Optional[Decimal] = Field(default=None, ge=0)
    start_date: Optional[date] = Field(default=None)
    end_date: Optional[date] = Field(default=None)
    status: Optional[BudgetStatus] = Field(default=None)
    alert_threshold: Optional[int] = Field(default=None, ge=0, le=100)
    category_id: Optional[uuid.UUID] = Field(default=None)




class BudgetModel:
    @staticmethod
    def create_budget(data: BudgetCreate) -> Budget:
        """Create a new budget in the budgets table."""
        try:
            budget_data = data.model_dump(exclude_unset=True)
            budget_data["budget_id"] = str(uuid.uuid4())
            budget_data["created_at"] = datetime.now(timezone.utc).isoformat()
            budget_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            budget_data["amount"] = str(budget_data["amount"])
            budget_data["spent_amount"] = str(budget_data.get("spent_amount", "0"))
            budget_data["start_date"] = budget_data["start_date"].isoformat()
            budget_data["end_date"] = budget_data["end_date"].isoformat() if budget_data["end_date"] else None

            response = supabase.table("budgets").insert(budget_data).execute()
            if not response.data:
                raise ValueError("Failed to create budget")
            return Budget(**response.data[0])
        except PostgrestAPIError as e:
            raise ValueError(f"Database error creating budget: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error creating budget: {str(e)}")

    @staticmethod
    def update_budget(budget_id: uuid.UUID, data: BudgetUpdate) -> Budget:
        """Update an existing budget in the budgets table."""
        try:
            update_data = data.model_dump(exclude_unset=True, exclude_none=True)
            if not update_data:
                raise ValueError("No updates provided")
            update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            if "amount" in update_data:
                update_data["amount"] = str(update_data["amount"])
            if "spent_amount" in update_data:
                update_data["spent_amount"] = str(update_data["spent_amount"])
            if "start_date" in update_data:
                update_data["start_date"] = update_data["start_date"].isoformat()
            if "end_date" in update_data:
                update_data["end_date"] = update_data["end_date"].isoformat() if update_data["end_date"] else None

            response =  supabase.table("budgets").update(update_data).eq("budget_id", str(budget_id)).execute()
            if not response.data:
                raise ValueError(f"Budget with ID {budget_id} not found")
            return Budget(**response.data[0])
        except PostgrestAPIError as e:
            raise ValueError(f"Database error updating budget: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error updating budget: {str(e)}")

    @staticmethod
    def get_budget(budget_id: uuid.UUID) -> Optional[Budget]:
        """Fetch a budget by ID from the budgets table."""
        try:
            response = supabase.table("budgets").select("*").eq("budget_id", str(budget_id)).single().execute()
            if response.data:
                return Budget(**response.data)
            return None
        except PostgrestAPIError as e:
            if "single" in str(e).lower() and "0 rows" in str(e).lower():
                return None
            raise ValueError(f"Database error fetching budget: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error fetching budget: {str(e)}")

    @staticmethod
    def update_spent_amount(budget_id: uuid.UUID, user_id: uuid.UUID) -> Budget:
        """Update spent_amount based on expenses in the budgets' category and period."""
        try:
            budget = BudgetModel.get_budget(budget_id)
            if not budget:
                raise ValueError(f"Budget with ID {budget_id} not found")
            query = supabase.table("expenses").select("amount").eq("user_id", str(user_id))
            if budget.category_id:
                query = query.eq("category_id", str(budget.category_id))
            if budget.start_date:
                query = query.gte("created_at", budget.start_date.isoformat())
            if budget.end_date:
                query = query.lte("created_at", budget.end_date.isoformat())
            expenses = query.execute()
            spent_amount = sum(Decimal(str(exp["amount"])) for exp in expenses.data)
            update_data = {
                "spent_amount": str(spent_amount),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "status": BudgetStatus.OVERBUDGET.value if spent_amount > budget.amount else BudgetStatus.ACTIVE.value
            }
            response =  supabase.table("budgets").update(update_data).eq("budget_id", str(budget_id)).execute()
            if not response.data:
                raise ValueError(f"Failed to update spent_amount for budget {budget_id}")
            return Budget(**response.data[0])
        except PostgrestAPIError as e:
            raise ValueError(f"Database error updating spent_amount: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error updating spent_amount: {str(e)}")