from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime
from decimal import Decimal
import uuid
from app.core.constants import AchievementType
from supabase import Client
from app.db.supabase_client import get_supabase_client

supabase: Client = get_supabase_client()

class Achievement(BaseModel):
    """Achievement model representing user achievements."""
    achievement_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique identifier for the achievement")
    achievement_type: AchievementType = Field(..., description="Type of achievement")
    description: str = Field(..., description="Achievement description")
    category: str = Field(..., description="Achievement category")
    criteria: Dict[str, Any] = Field(..., description="Criteria for achieving the goal")
    points: Optional[int] = Field(default=0, description="Points awarded for the achievement")
    threshold_amount: Optional[Decimal] = Field(default=None, ge=0, description="Threshold amount for achievement")
    threshold_count: Optional[int] = Field(default=None, ge=0, description="Threshold count for achievement")
    threshold_duration: Optional[int] = Field(default=None, ge=0, description="Threshold duration for achievement")
    google_play_achievement_id: Optional[str] = Field(default=None, description="Google Play achievement ID")
    is_locked: Optional[bool] = Field(default=True, description="Whether the achievement is locked")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Handle Decimal and datetime
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: str,
        }

class AchievementCreate(BaseModel):
    """Schema for creating a new achievement."""
    achievement_type: AchievementType = Field(..., description="Type of achievement")
    description: str = Field(..., description="Achievement description")
    category: str = Field(..., description="Achievement category")
    criteria: Dict[str, Any] = Field(..., description="Criteria for achieving the goal")
    points: int = Field(default=0, description="Points awarded for the achievement")
    threshold_amount: Optional[Decimal] = Field(default=None, ge=0, description="Threshold amount")
    threshold_count: Optional[int] = Field(default=None, ge=0, description="Threshold count")
    threshold_duration: Optional[int] = Field(default=None, ge=0, description="Threshold duration")
    google_play_achievement_id: Optional[str] = Field(default=None, description="Google Play achievement ID")
    is_locked: bool = Field(default=True, description="Whether the achievement is locked")

class AchievementUpdate(BaseModel):
    """Schema for updating an existing achievement."""
    achievement_type: Optional[AchievementType] = Field(default=None, description="Type of achievement")
    description: Optional[str] = Field(default=None, description="Achievement description")
    category: Optional[str] = Field(default=None, description="Achievement category")
    criteria: Optional[Dict[str, Any]] = Field(default=None, description="Criteria for achieving the goal")
    points: Optional[int] = Field(default=None, description="Points awarded for the achievement")
    threshold_amount: Optional[Decimal] = Field(default=None, ge=0, description="Threshold amount")
    threshold_count: Optional[int] = Field(default=None, ge=0, description="Threshold count")
    threshold_duration: Optional[int] = Field(default=None, ge=0, description="Threshold duration")
    google_play_achievement_id: Optional[str] = Field(default=None, description="Google Play achievement ID")
    is_locked: Optional[bool] = Field(default=None, description="Whether the achievement is locked")

class AchievementResponse(Achievement):
    """Schema for achievement responses."""
    pass

class AchievementModel:
    @staticmethod
    def create_achievement(data: AchievementCreate) -> Achievement:
        """Create a new achievement in the achievements table."""
        achievement_data = data.model_dump(exclude_unset=True)
        if "achievement_id" not in achievement_data or achievement_data["achievement_id"] is None:
            achievement_data["achievement_id"] = str(uuid.uuid4())
        response = supabase.table("achievements").insert(achievement_data).execute()
        if response.data:
            return Achievement(**response.data[0])
        raise ValueError("Failed to create achievement")

    @staticmethod
    def update_achievement(achievement_id: uuid.UUID, data: AchievementUpdate) -> Achievement:
        """Update an existing achievement in the achievements table."""
        update_data = data.model_dump(exclude_unset=True, exclude_none=True)
        if not update_data:
            raise ValueError("No updates provided")
        response = supabase.table("achievements").update(update_data).eq("achievement_id", str(achievement_id)).execute()
        if response.data:
            return Achievement(**response.data[0])
        raise ValueError(f"Achievement with ID {achievement_id} not found")

    @staticmethod
    def get_achievement(achievement_id: uuid.UUID) -> Optional[AchievementResponse]:
        """Fetch an achievement by ID from the achievements table."""
        response = supabase.table("achievements").select("*").eq("achievement_id", str(achievement_id)).execute()
        if response.data and len(response.data) > 0:
            achievement_data = response.data[0]
            return AchievementResponse(**achievement_data)
        return None