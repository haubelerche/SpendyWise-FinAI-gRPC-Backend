"""
User Achievement Schemas
Pydantic schemas for user achievement data validation and serialization
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, validator


class UserAchievementBase(BaseModel):
    """Base user achievement schema"""
    progress: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom progress data")
    current_amount: Optional[Decimal] = Field(default=Decimal('0'), ge=0, description="Current progress amount")
    current_count: Optional[int] = Field(default=0, ge=0, description="Current progress count")
    current_streak: Optional[int] = Field(default=0, ge=0, description="Current streak count")


class UserAchievementCreate(UserAchievementBase):
    """Schema for creating user achievement"""
    achievement_id: UUID = Field(..., description="Achievement ID")


class UserAchievementUpdate(UserAchievementBase):
    """Schema for updating user achievement"""
    is_completed: Optional[bool] = Field(None, description="Completion status")
    synced_to_google_play: Optional[bool] = Field(None, description="Google Play sync status")


class UserAchievementProgressUpdate(BaseModel):
    """Schema for updating achievement progress"""
    amount_increment: Optional[Decimal] = Field(None, ge=0, description="Amount to add to progress")
    count_increment: Optional[int] = Field(None, ge=0, description="Count to add to progress")
    streak_value: Optional[int] = Field(None, ge=0, description="Set streak value")
    progress_data: Optional[Dict[str, Any]] = Field(None, description="Custom progress data to merge")
    force_complete: Optional[bool] = Field(False, description="Force mark as completed")


class UserAchievementResponse(UserAchievementBase):
    """Schema for user achievement response"""
    user_achievement_id: UUID
    user_id: UUID
    achievement_id: UUID
    is_completed: bool
    completed_at: Optional[datetime]
    synced_to_google_play: bool
    google_play_sync_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Computed fields
    progress_percentage: float = Field(..., description="Progress percentage (0-100)")
    remaining_amount: Optional[Decimal] = Field(None, description="Remaining amount to complete")
    remaining_count: Optional[int] = Field(None, description="Remaining count to complete")
    
    class Config:
        from_attributes = True


class UserAchievementWithDetails(UserAchievementResponse):
    """User achievement with achievement details"""
    achievement: Optional[Dict[str, Any]] = Field(None, description="Achievement details")
    
    class Config:
        from_attributes = True


class UserAchievementSummary(BaseModel):
    """Summary of user achievements"""
    total_achievements: int = Field(..., description="Total number of achievements available")
    completed_achievements: int = Field(..., description="Number of completed achievements")
    in_progress_achievements: int = Field(..., description="Number of achievements in progress")
    completion_percentage: float = Field(..., description="Overall completion percentage")
    recent_completions: List[UserAchievementResponse] = Field(default_factory=list, description="Recently completed achievements")
    
    @validator('completion_percentage')
    def validate_completion_percentage(cls, v):
        return max(0.0, min(100.0, v))


class UserAchievementAnalytics(BaseModel):
    """Analytics for user achievements"""
    total_achievements: int
    completed_count: int
    in_progress_count: int
    completion_rate: float
    average_completion_time_days: Optional[float]
    most_recent_completion: Optional[datetime]
    achievements_by_category: Dict[str, int]
    achievements_by_difficulty: Dict[str, int]
    monthly_completions: Dict[str, int]  # month -> count


class UserAchievementFilter(BaseModel):
    """Filter for user achievements"""
    is_completed: Optional[bool] = Field(None, description="Filter by completion status")
    achievement_category: Optional[str] = Field(None, description="Filter by achievement category")
    achievement_difficulty: Optional[str] = Field(None, description="Filter by achievement difficulty")
    synced_to_google_play: Optional[bool] = Field(None, description="Filter by Google Play sync status")
    completed_after: Optional[datetime] = Field(None, description="Filter achievements completed after date")
    completed_before: Optional[datetime] = Field(None, description="Filter achievements completed before date")


class UserAchievementPagination(BaseModel):
    """Pagination for user achievements"""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: str = Field("desc", regex="^(asc|desc)$", description="Sort order")


class UserAchievementListResponse(BaseModel):
    """Response for listing user achievements"""
    achievements: List[UserAchievementWithDetails]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    
    @validator('total_pages', pre=True, always=True)
    def calculate_total_pages(cls, v, values):
        total_count = values.get('total_count', 0)
        page_size = values.get('page_size', 20)
        return max(1, (total_count + page_size - 1) // page_size)


class GooglePlaySync(BaseModel):
    """Schema for Google Play Games sync"""
    achievement_ids: List[UUID] = Field(..., description="Achievement IDs to sync")
    force_sync: bool = Field(False, description="Force sync even if already synced")


class GooglePlaySyncResponse(BaseModel):
    """Response for Google Play Games sync"""
    synced_count: int = Field(..., description="Number of achievements synced")
    failed_count: int = Field(..., description="Number of achievements that failed to sync")
    already_synced_count: int = Field(..., description="Number of achievements already synced")
    errors: List[str] = Field(default_factory=list, description="Sync errors")


class AchievementLeaderboard(BaseModel):
    """Leaderboard entry for achievements"""
    user_id: UUID
    username: Optional[str]
    completed_achievements: int
    total_points: int
    completion_percentage: float
    most_recent_achievement: Optional[str]
    most_recent_completion: Optional[datetime]


class AchievementLeaderboardResponse(BaseModel):
    """Response for achievement leaderboard"""
    leaderboard: List[AchievementLeaderboard]
    user_rank: Optional[int] = Field(None, description="Current user's rank")
    total_users: int = Field(..., description="Total number of users on leaderboard")
