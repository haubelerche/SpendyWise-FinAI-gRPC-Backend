import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from decimal import Decimal

from pydantic import BaseModel, Field, UUID4


class UserAchievement(BaseModel):
    user_achievement_id: UUID4 = Field(default_factory=uuid.uuid4, description="Unique achievement instance ID")
    user_id: UUID4 = Field(..., description="User ID (foreign key to users.user_id)")
    achievement_id: UUID4 = Field(..., description="Achievement ID")

    # Progress tracking
    progress: Dict[str, Any] = Field(default_factory=dict, description="Custom progress data")
    current_amount: Decimal = Field(default=Decimal('0'), ge=0,
                                    description="Current progress amount for financial goals")
    current_count: int = Field(default=0, ge=0, description="Current progress count for habit tracking")
    current_streak: int = Field(default=0, ge=0, description="Current streak count for habit tracking")
    is_completed: bool = Field(default=False, description="Completion status")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

    # Google Play Games sync
    synced_to_google_play: bool = Field(default=False, description="Sync status with Google Play Games")
    google_play_sync_at: Optional[datetime] = Field(None, description="Last sync timestamp with Google Play Games")

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc),
                                           description="Last update timestamp")

    @property
    def progress_percentage(self) -> float:
        try:
            target_amount = getattr(self, '_target_amount', None)
            target_count = getattr(self, '_target_count', None)

            if target_amount and target_amount > 0:
                return min(100.0, (float(self.current_amount) / float(target_amount)) * 100)
            elif target_count and target_count > 0:
                return min(100.0, (self.current_count / target_count) * 100)
            return 100.0 if self.is_completed else 0.0
        except AttributeError:
            return 0.0

    def update_progress(self, amount: Optional[Decimal] = None, count: Optional[int] = None,
                        streak: Optional[int] = None, progress_data: Optional[Dict[str, Any]] = None) -> bool:
        """Update achievement progress and check for completion"""
        updated = False

        if amount is not None and amount >= 0:
            self.current_amount = amount
            updated = True

        if count is not None and count >= 0:
            self.current_count = count
            updated = True

        if streak is not None and streak >= 0:
            self.current_streak = streak
            updated = True

        if progress_data:
            self.progress.update(progress_data)
            updated = True

        if updated:
            self.updated_at = datetime.now(timezone.utc)
            if self._check_completion():
                self.is_completed = True
                self.completed_at = datetime.now(timezone.utc)

        return updated

    def _check_completion(self) -> bool:
        """Check if achievement is completed based on requirements"""
        if self.is_completed:
            return True

        try:
            target_amount = getattr(self, '_target_amount', None)
            target_count = getattr(self, '_target_count', None)

            if target_amount and self.current_amount >= target_amount:
                return True
            if target_count and self.current_count >= target_count:
                return True
            return False
        except AttributeError:
            return False

    def sync_to_google_play(self) -> None:
        """Mark achievement as synced to Google Play Games"""
        if not self.synced_to_google_play:
            self.synced_to_google_play = True
            self.google_play_sync_at = datetime.now(timezone.utc)
            self.updated_at = datetime.now(timezone.utc)

    def reset_streak(self) -> None:
        """Reset the current streak to zero"""
        if self.current_streak > 0:
            self.current_streak = 0
            self.updated_at = datetime.now(timezone.utc)

    def get_detailed_progress(self) -> Dict[str, Any]:
        """Get detailed progress information including streak and sync status"""
        return {
            'current_amount': float(self.current_amount),
            'current_count': self.current_count,
            'current_streak': self.current_streak,
            'progress_percentage': self.progress_percentage,
            'progress': self.progress,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'synced_to_google_play': self.synced_to_google_play,
            'google_play_sync_at': self.google_play_sync_at.isoformat() if self.google_play_sync_at else None
        }


class UserAchievementCreate(BaseModel):
    """Schema for creating user achievement
    Note: user_id is a foreign key referencing users.user_id in the database
    """
    achievement_id: UUID4 = Field(..., description="Achievement ID")
    user_id: UUID4 = Field(..., description="User ID (foreign key to users.user_id)")
    progress: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom progress data")
    current_amount: Optional[Decimal] = Field(default=Decimal('0'), ge=0, description="Initial progress amount")
    current_count: Optional[int] = Field(default=0, ge=0, description="Initial progress count")
    current_streak: Optional[int] = Field(default=0, ge=0, description="Initial streak count")
    synced_to_google_play: Optional[bool] = Field(default=False, description="Initial sync status")


class UserAchievementResponse(BaseModel):
    """Schema for user achievement response"""
    user_achievement_id: UUID4
    user_id: UUID4
    achievement_id: UUID4
    progress: Dict[str, Any]
    current_amount: Decimal
    current_count: int
    current_streak: int
    is_completed: bool
    completed_at: Optional[datetime]
    synced_to_google_play: bool
    google_play_sync_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    progress_percentage: float


class UserAchievementListResponse(BaseModel):
    """Response for listing user achievements"""
    achievements: list[UserAchievementResponse]
    total_count: int
    page: int = 1
    page_size: int = 20