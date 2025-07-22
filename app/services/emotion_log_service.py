"""
Emotion Log Service
Handles emotion tracking and mental health insights
"""
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta, date
from uuid import UUID
import asyncio

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.models.emotion_log import EmotionLog
from app.schemas.emotion_log import EmotionLogCreate, EmotionLogUpdate
from app.core.constants import EmotionCheckin, EmotionTrigger
from app.db.session import get_db

logger = logging.getLogger(__name__)


class EmotionLogService:
    """Service for managing emotion logs and mental health tracking"""
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
    
    def create_emotion_log(self, user_id: UUID, emotion_data: EmotionLogCreate) -> EmotionLog:
        """Create a new emotion log entry"""
        try:
            db_emotion_log = EmotionLog(
                user_id=user_id,
                **emotion_data.dict()
            )
            self.db.add(db_emotion_log)
            self.db.commit()
            self.db.refresh(db_emotion_log)
            
            logger.info(f"Created emotion log {db_emotion_log.emotion_log_id} for user {user_id}")
            return db_emotion_log
            
        except Exception as e:
            logger.error(f"Error creating emotion log for user {user_id}: {str(e)}")
            self.db.rollback()
            raise
    
    def get_emotion_log(self, user_id: UUID, emotion_log_id: UUID) -> Optional[EmotionLog]:
        """Get a specific emotion log"""
        return self.db.query(EmotionLog).filter(
            and_(
                EmotionLog.user_id == user_id,
                EmotionLog.emotion_log_id == emotion_log_id
            )
        ).first()
    
    def list_user_emotion_logs(self, user_id: UUID, page: int = 1, page_size: int = 20,
                             start_date: Optional[date] = None, end_date: Optional[date] = None) -> tuple[List[EmotionLog], int]:
        """List emotion logs for a user with optional date filtering"""
        query = self.db.query(EmotionLog).filter(EmotionLog.user_id == user_id)
        
        # Apply date filters if provided
        if start_date:
            query = query.filter(EmotionLog.logged_at >= start_date)
        if end_date:
            query = query.filter(EmotionLog.logged_at <= end_date + timedelta(days=1))
        
        total_count = query.count()
        
        emotions = query.order_by(desc(EmotionLog.logged_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return emotions, total_count
    
    def get_recent_emotions(self, user_id: UUID, days: int = 7) -> List[EmotionLog]:
        """Get recent emotion logs for a user"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return self.db.query(EmotionLog).filter(
            and_(
                EmotionLog.user_id == user_id,
                EmotionLog.logged_at >= cutoff_date
            )
        ).order_by(desc(EmotionLog.logged_at)).all()
    
    def get_emotion_stats(self, user_id: UUID, days: int = 30) -> Dict[str, Any]:
        """Get emotion statistics for a user"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        emotions = self.db.query(EmotionLog).filter(
            and_(
                EmotionLog.user_id == user_id,
                EmotionLog.logged_at >= cutoff_date
            )
        ).all()
        
        if not emotions:
            return {
                "total_logs": 0,
                "emotion_distribution": {},
                "trigger_distribution": {},
                "average_intensity": 0,
                "positive_emotion_percentage": 0,
                "negative_emotion_percentage": 0,
                "most_common_emotion": None,
                "most_common_trigger": None
            }
        
        # Calculate distributions
        emotion_counts = {}
        trigger_counts = {}
        intensities = []
        positive_count = 0
        negative_count = 0
        
        for emotion in emotions:
            # Emotion distribution
            emotion_type = emotion.emotion_checkin
            emotion_counts[emotion_type] = emotion_counts.get(emotion_type, 0) + 1
            
            # Trigger distribution
            if emotion.emotion_trigger:
                trigger_counts[emotion.emotion_trigger] = trigger_counts.get(emotion.emotion_trigger, 0) + 1
            
            # Intensity
            if emotion.intensity:
                intensities.append(emotion.intensity)
            
            # Positive/negative classification
            if emotion.is_positive_emotion:
                positive_count += 1
            elif emotion.is_negative_emotion:
                negative_count += 1
        
        total_logs = len(emotions)
        
        return {
            "total_logs": total_logs,
            "emotion_distribution": emotion_counts,
            "trigger_distribution": trigger_counts,
            "average_intensity": sum(intensities) / len(intensities) if intensities else 0,
            "positive_emotion_percentage": (positive_count / total_logs * 100) if total_logs > 0 else 0,
            "negative_emotion_percentage": (negative_count / total_logs * 100) if total_logs > 0 else 0,
            "most_common_emotion": max(emotion_counts, key=emotion_counts.get) if emotion_counts else None,
            "most_common_trigger": max(trigger_counts, key=trigger_counts.get) if trigger_counts else None,
            "period_days": days
        }
    
    def get_money_related_emotions(self, user_id: UUID, days: int = 30) -> List[EmotionLog]:
        """Get emotion logs related to money/finance"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return self.db.query(EmotionLog).filter(
            and_(
                EmotionLog.user_id == user_id,
                EmotionLog.logged_at >= cutoff_date,
                or_(
                    EmotionLog.emotion_trigger == EmotionTrigger.MONEY.value,
                    EmotionLog.transaction_id.isnot(None)
                )
            )
        ).order_by(desc(EmotionLog.logged_at)).all()
    
    def analyze_spending_emotions(self, user_id: UUID, days: int = 30) -> Dict[str, Any]:
        """Analyze emotions related to spending patterns"""
        money_emotions = self.get_money_related_emotions(user_id, days)
        
        if not money_emotions:
            return {
                "total_money_emotions": 0,
                "spending_linked_emotions": 0,
                "emotional_spending_risk": "low",
                "recommendations": ["Continue tracking emotions to build insights"]
            }
        
        spending_emotions = [e for e in money_emotions if e.transaction_id]
        negative_money_emotions = [e for e in money_emotions if e.is_negative_emotion]
        
        # Calculate emotional spending risk
        negative_percentage = (len(negative_money_emotions) / len(money_emotions)) * 100 if money_emotions else 0
        
        if negative_percentage > 60:
            risk_level = "high"
            recommendations = [
                "Consider implementing a cooling-off period before large purchases",
                "Practice mindfulness before spending decisions",
                "Seek support if financial stress is overwhelming"
            ]
        elif negative_percentage > 30:
            risk_level = "moderate"
            recommendations = [
                "Try to identify emotional spending triggers",
                "Consider budgeting techniques to reduce financial stress",
                "Practice emotional regulation techniques"
            ]
        else:
            risk_level = "low"
            recommendations = [
                "Continue monitoring emotional patterns",
                "Maintain healthy spending habits"
            ]
        
        return {
            "total_money_emotions": len(money_emotions),
            "spending_linked_emotions": len(spending_emotions),
            "negative_money_emotions": len(negative_money_emotions),
            "negative_percentage": round(negative_percentage, 1),
            "emotional_spending_risk": risk_level,
            "recommendations": recommendations,
            "period_days": days
        }
    
    def get_emotion_trends(self, user_id: UUID, days: int = 30) -> Dict[str, Any]:
        """Get emotion trends over time"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        emotions = self.db.query(EmotionLog).filter(
            and_(
                EmotionLog.user_id == user_id,
                EmotionLog.logged_at >= cutoff_date
            )
        ).order_by(EmotionLog.logged_at).all()
        
        if not emotions:
            return {"trend": "no_data", "weekly_breakdown": {}}
        
        # Group by week
        weekly_breakdown = {}
        
        for emotion in emotions:
            week_start = emotion.logged_at.date() - timedelta(days=emotion.logged_at.weekday())
            week_key = week_start.isoformat()
            
            if week_key not in weekly_breakdown:
                weekly_breakdown[week_key] = {
                    "positive_count": 0,
                    "negative_count": 0,
                    "neutral_count": 0,
                    "total_count": 0,
                    "average_intensity": 0,
                    "intensities": []
                }
            
            weekly_breakdown[week_key]["total_count"] += 1
            
            if emotion.is_positive_emotion:
                weekly_breakdown[week_key]["positive_count"] += 1
            elif emotion.is_negative_emotion:
                weekly_breakdown[week_key]["negative_count"] += 1
            else:
                weekly_breakdown[week_key]["neutral_count"] += 1
            
            if emotion.intensity:
                weekly_breakdown[week_key]["intensities"].append(emotion.intensity)
        
        # Calculate average intensities
        for week_data in weekly_breakdown.values():
            if week_data["intensities"]:
                week_data["average_intensity"] = sum(week_data["intensities"]) / len(week_data["intensities"])
            del week_data["intensities"]  # Remove raw intensities from response
        
        # Determine overall trend
        weeks = sorted(weekly_breakdown.keys())
        if len(weeks) >= 2:
            recent_positive_rate = weekly_breakdown[weeks[-1]]["positive_count"] / max(1, weekly_breakdown[weeks[-1]]["total_count"])
            earlier_positive_rate = weekly_breakdown[weeks[0]]["positive_count"] / max(1, weekly_breakdown[weeks[0]]["total_count"])
            
            if recent_positive_rate > earlier_positive_rate + 0.1:
                trend = "improving"
            elif recent_positive_rate < earlier_positive_rate - 0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "trend": trend,
            "weekly_breakdown": weekly_breakdown,
            "total_weeks": len(weeks),
            "period_days": days
        }
    
    def update_emotion_log(self, user_id: UUID, emotion_log_id: UUID, update_data: EmotionLogUpdate) -> Optional[EmotionLog]:
        """Update an emotion log entry"""
        emotion_log = self.get_emotion_log(user_id, emotion_log_id)
        if not emotion_log:
            return None
        
        try:
            for field, value in update_data.dict(exclude_unset=True).items():
                setattr(emotion_log, field, value)
            
            self.db.commit()
            self.db.refresh(emotion_log)
            
            logger.info(f"Updated emotion log {emotion_log_id} for user {user_id}")
            return emotion_log
            
        except Exception as e:
            logger.error(f"Error updating emotion log {emotion_log_id}: {str(e)}")
            self.db.rollback()
            raise
    
    def delete_emotion_log(self, user_id: UUID, emotion_log_id: UUID) -> bool:
        """Delete an emotion log entry"""
        emotion_log = self.get_emotion_log(user_id, emotion_log_id)
        if not emotion_log:
            return False
        
        self.db.delete(emotion_log)
        self.db.commit()
        logger.info(f"Deleted emotion log {emotion_log_id} for user {user_id}")
        return True
    
    def get_emotion_insights_for_ai(self, user_id: UUID, days: int = 14) -> Dict[str, Any]:
        """Get emotion insights formatted for AI advisor context"""
        emotion_stats = self.get_emotion_stats(user_id, days)
        spending_emotions = self.analyze_spending_emotions(user_id, days)
        trends = self.get_emotion_trends(user_id, days)
        
        return {
            "emotional_state_summary": {
                "dominant_emotion": emotion_stats.get("most_common_emotion"),
                "positive_percentage": emotion_stats.get("positive_emotion_percentage", 0),
                "average_intensity": emotion_stats.get("average_intensity", 0),
                "trend": trends.get("trend", "unknown")
            },
            "financial_emotional_health": {
                "money_related_emotions": spending_emotions.get("total_money_emotions", 0),
                "emotional_spending_risk": spending_emotions.get("emotional_spending_risk", "low"),
                "negative_money_emotions_percentage": spending_emotions.get("negative_percentage", 0)
            },
            "recommendations": spending_emotions.get("recommendations", []),
            "data_quality": {
                "total_logs": emotion_stats.get("total_logs", 0),
                "tracking_consistency": "good" if emotion_stats.get("total_logs", 0) > days * 0.3 else "needs_improvement"
            }
        }
