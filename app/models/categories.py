from pydantic import BaseModel, Field, field_validator
import uuid
from datetime import timezone, datetime

from pydantic import BaseModel

from app.core.constants import TransactionType, SubCategories


class Category(BaseModel):
    category_id: uuid.UUID=Field(default_factory=uuid.uuid4, description="Unique category ID")
    name: str= Field(..., min_length=1, max_length=100, description="Category name")
    type: TransactionType=Field(..., description="Category type")
    sub_categories: SubCategories= Field(..., description="Subcategories for the category")
    created_at: datetime=Field(default=datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: datetime=Field(default=datetime.now(timezone.utc), description="Last update timestamp")

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Handle Decimal and datetime
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: str,
        }

