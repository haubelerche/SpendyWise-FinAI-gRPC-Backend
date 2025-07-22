"""
User Achievement Model
Junction table between users and achievements with progress tracking
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, DECIMAL, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class UserAchievement(BaseModel):
    """User's progress on specific achievements"""
    
    __tablename__ = "user_achievements"
    
    # Primary key
    user_achievement_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey('achievements.achievement_id', ondelete='CASCADE'), nullable=False)
    
    # Progress tracking (enhanced for detailed tracking)
    progress = Column(JSONB, default=dict)  # Current progress towards achievement
    current_amount = Column(DECIMAL(15, 2), default=0)  # Current progress amount
    current_count = Column(Integer, default=0)  # Current progress count
    current_streak = Column(Integer, default=0)  # Current streak (for time-based achievements)
    
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    
    # Google Play Games sync
    synced_to_google_play = Column(Boolean, default=False)
    google_play_sync_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'achievement_id', name='user_achievements_unique'),
    )
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage based on achievement requirements"""
        if not self.achievement:
            return 0.0
        
        target_amount = self.achievement.target_amount
        target_count = self.achievement.target_count
        
        if target_amount and target_amount > 0:
            return min(100.0, (float(self.current_amount) / float(target_amount)) * 100)
        elif target_count and target_count > 0:
            return min(100.0, (self.current_count / target_count) * 100)
        
        return 100.0 if self.is_completed else 0.0
    
    @property
    def remaining_amount(self) -> Optional[Decimal]:
        """Calculate remaining amount to complete achievement"""
        if not self.achievement or not self.achievement.target_amount:
            return None
        return max(Decimal('0'), self.achievement.target_amount - self.current_amount)
    
    @property
    def remaining_count(self) -> Optional[int]:
        """Calculate remaining count to complete achievement"""
        if not self.achievement or not self.achievement.target_count:
            return None
        return max(0, self.achievement.target_count - self.current_count)
    
    def update_progress(self, amount: Decimal = None, count: int = None, 
                       streak: int = None, progress_data: Dict[str, Any] = None) -> bool:
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
            if not self.progress:
                self.progress = {}
            self.progress.update(progress_data)
            updated = True
        
        if updated:
            self.updated_at = datetime.utcnow()
            
            # Check for completion
            if self._check_completion():
                self.mark_completed()
        
        return updated
    
    def increment_progress(self, amount: Decimal = None, count: int = None,
                          progress_data: Dict[str, Any] = None) -> bool:
        """Increment achievement progress"""
        if amount is not None and amount > 0:
            self.current_amount += amount
        
        if count is not None and count > 0:
            self.current_count += count
        
        if progress_data:
            if not self.progress:
                self.progress = {}
            # Merge progress data intelligently
            for key, value in progress_data.items():
                if key in self.progress and isinstance(self.progress[key], (int, float)) and isinstance(value, (int, float)):
                    self.progress[key] += value
                else:
                    self.progress[key] = value
        
        self.updated_at = datetime.utcnow()
        
        # Check for completion
        if self._check_completion():
            self.mark_completed()
            return True
        
        return False
    
    def _check_completion(self) -> bool:
        """Check if achievement is completed based on requirements"""
        if self.is_completed or not self.achievement:
            return self.is_completed
        
        # Check amount-based completion
        if (self.achievement.target_amount and 
            self.current_amount >= self.achievement.target_amount):
            return True
        
        # Check count-based completion
        if (self.achievement.target_count and 
            self.current_count >= self.achievement.target_count):
            return True
        
        # Check streak-based completion
        if (self.achievement.required_streak and 
            self.current_streak >= self.achievement.required_streak):
            return True
        
        # Check custom completion criteria in progress
        if self.progress and self.progress.get('completed', False):
            return True
        
        return False
    
    def mark_completed(self) -> None:
        """Mark achievement as completed"""
        if not self.is_completed:
            self.is_completed = True
            self.completed_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
    
    def reset_progress(self) -> None:
        """Reset achievement progress"""
        self.current_amount = Decimal('0')
        self.current_count = 0
        self.current_streak = 0
        self.progress = {}
        self.is_completed = False
        self.completed_at = None
        self.updated_at = datetime.utcnow()
    
    def sync_to_google_play(self) -> None:
        """Mark as synced to Google Play Games"""
        self.synced_to_google_play = True
        self.google_play_sync_at = datetime.utcnow()
    
    def get_detailed_progress(self) -> Dict[str, Any]:
        """Get detailed progress information"""
        return {
            'current_amount': float(self.current_amount) if self.current_amount else 0,
            'current_count': self.current_count,
            'current_streak': self.current_streak,
            'progress_percentage': self.progress_percentage,
            'remaining_amount': float(self.remaining_amount) if self.remaining_amount else None,
            'remaining_count': self.remaining_count,
            'custom_progress': self.progress or {},
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user achievement to dictionary"""
        return {
            'user_achievement_id': str(self.user_achievement_id),
            'user_id': str(self.user_id),
            'achievement_id': str(self.achievement_id),
            'progress': self.progress or {},
            'current_amount': float(self.current_amount) if self.current_amount else 0,
            'current_count': self.current_count,
            'current_streak': self.current_streak,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'synced_to_google_play': self.synced_to_google_play,
            'google_play_sync_at': self.google_play_sync_at.isoformat() if self.google_play_sync_at else None,
            'progress_percentage': self.progress_percentage,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
