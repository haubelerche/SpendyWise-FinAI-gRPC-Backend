from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime
from decimal import Decimal
import uuid

# Achievement type enum values
AchievementType = Literal[
    'rookie_starter', 'ready_to_be_the_saver', 'saving_sage', 'savings_champion',
    'savings_pro', 'savings_master', 'savings_guru', 'savings_god', 'the_billionaire',
    'budget_wizard', 'budget_sensei', 'budget_pro', 'budget_master', 'budget_guru',
    'spending_wizard', 'spending_sensei', 'spending_pro', 'spending_master', 'spending_guru',
    'debt_newbie', 'debt_slave', 'deep_in_debt', 'wrestler_with_debt', 'fall_into_debt_spiral',
    'debt_veteran', 'debt_warrior', 'no_longer_miserable', 'financial_guru', 'financial_master',
    'money_god', 'unbeatable_money_saver'
]

class Achievement(BaseModel):
    achievement_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    achievement_type: AchievementType
    description: str
    category: str
    criteria: Dict[str, Any] = Field(...)  # NOT NULL, matches SQL JSONB NOT NULL
    points: int = 0
    threshold_amount: Optional[Decimal] = Field(default=None, ge=0)  # Non-negative
    threshold_count: Optional[int] = Field(default=None, ge=0)  # Non-negative
    threshold_duration: Optional[int] = Field(default=None, ge=0)  # Non-negative
    google_play_achievement_id: Optional[str] = None
    is_locked: bool = True
    created_at: Optional[datetime] = None  # Default from Supabase
    updated_at: Optional[datetime] = None  # Default from Supabase

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Handle Decimal and datetime

class AchievementCreate(BaseModel):
    achievement_type: AchievementType
    description: str
    category: str
    criteria: Dict[str, Any] = Field(...)  # NOT NULL
    points: int = 0
    threshold_amount: Optional[Decimal] = Field(default=None, ge=0)
    threshold_count: Optional[int] = Field(default=None, ge=0)
    threshold_duration: Optional[int] = Field(default=None, ge=0)
    google_play_achievement_id: Optional[str] = None
    is_locked: bool = True
    sort_order: int = 0

class AchievementUpdate(BaseModel):
    achievement_type: Optional[AchievementType] = None
    description: Optional[str] = None
    category: Optional[str] = None
    criteria: Optional[Dict[str, Any]] = None
    points: Optional[int] = None
    threshold_amount: Optional[Decimal] = Field(default=None, ge=0)
    threshold_count: Optional[int] = Field(default=None, ge=0)
    threshold_duration: Optional[int] = Field(default=None, ge=0)
    google_play_achievement_id: Optional[str] = None
    is_locked: Optional[bool] = None
    sort_order: Optional[int] = None

class AchievementResponse(Achievement):
    pass