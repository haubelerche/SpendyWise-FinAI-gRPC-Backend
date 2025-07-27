from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, Literal
from datetime import datetime
from decimal import Decimal
import uuid
from app.core.constants import ConversationContext, AIResponseType, AI_RESPONSE_MAX_LENGTH






class AIConversation(BaseModel):
    """AI conversations table for chat history with financial advisor"""

    conversation_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    context = Column(String, default='general', nullable=False)
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    response_type = Column(String, default='advice', nullable=False)
    
    # AI metadata (updated with constants thresholds)
    model_version = Column(Text, default='1.0')
    confidence_score = Column(DECIMAL(3, 2))
    processing_time_ms = Column(Integer)
    
    # Context data used by AI
    financial_context = Column(JSON)  # Recent transactions, budgets, goals
    user_profile_context = Column(JSON)  # User preferences, education level
    
    # Feedback
    user_rating = Column(Integer)
    was_helpful = Column(Boolean)
    user_feedback = Column(Text)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AIConversationBase(BaseModel):
    """Base schema for AI conversations"""
    context: ConversationContext = Field(default=ConversationContext.GENERAL, description="Conversation context")
    user_message: str = Field(..., min_length=1, max_length=1000, description="User's message")
    response_type: AIResponseType = Field(default=AIResponseType.ADVICE, description="Type of AI response")


class AIConversationCreate(AIConversationBase):
    """Schema for creating AI conversations"""
    ai_response: str = Field(..., min_length=1, max_length=AI_RESPONSE_MAX_LENGTH, description="AI's response")
    model_version: str = Field(default='1.0', description="AI model version")
    confidence_score: Optional[float] = Field(default=None, ge=0, le=1, description="Response confidence")
    processing_time_ms: Optional[int] = Field(default=None, ge=0, description="Processing time in milliseconds")
    financial_context: Optional[Dict[str, Any]] = Field(default=None, description="Financial context data")
    user_profile_context: Optional[Dict[str, Any]] = Field(default=None, description="User profile context")


class AIConversationUpdate(BaseModel):
    """Schema for updating AI conversations (mainly feedback)"""
    user_rating: Optional[int] = Field(default=None, ge=1, le=5, description="User rating (1-5)")
    was_helpful: Optional[bool] = Field(default=None, description="Whether response was helpful")
    user_feedback: Optional[str] = Field(default=None, max_length=500, description="User feedback text")


class AIConversationResponse(AIConversationBase):
    """Schema for AI conversation responses"""
    conversation_id: UUID = Field(..., description="Conversation unique identifier")
    user_id: UUID = Field(..., description="User identifier")
    ai_response: str = Field(..., description="AI's response")
    model_version: str = Field(..., description="AI model version")
    confidence_score: Optional[float] = Field(default=None, description="Response confidence")
    processing_time_ms: Optional[int] = Field(default=None, description="Processing time in milliseconds")
    financial_context: Optional[Dict[str, Any]] = Field(default=None)
    user_profile_context: Optional[Dict[str, Any]] = Field(default=None)
    user_rating: Optional[int] = Field(default=None, description="User rating")
    was_helpful: Optional[bool] = Field(default=None, description="Helpfulness feedback")
    user_feedback: Optional[str] = Field(default=None, description="User feedback")
    created_at: datetime = Field(..., description="Creation timestamp")
    has_feedback: bool = Field(..., description="Whether conversation has feedback")
    is_positive_feedback: bool = Field(..., description="Whether feedback is positive")

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    """Schema for individual chat messages"""
    message: str = Field(..., min_length=1, max_length=1000, description="Chat message")
    context: ConversationContext = Field(default=ConversationContext.GENERAL)
    financial_context: Optional[Dict[str, Any]] = Field(default=None)


class ChatResponse(BaseModel):
    """Schema for chat response"""
    conversation_id: UUID = Field(..., description="Conversation identifier")
    message: str = Field(..., description="AI response message")
    suggestions: List[str] = Field(default=[], description="Follow-up suggestions")
    context: ConversationContext = Field(..., description="Conversation context")
    confidence_score: Optional[float] = Field(default=None)
    processing_time_ms: Optional[int] = Field(default=None)
    timestamp: datetime = Field(..., description="Response timestamp")


class ConversationSummaryRequest(BaseModel):
    """Schema for conversation summary requests"""
    days_back: int = Field(default=7, ge=1, le=30, description="Days of conversation history")
    include_context: bool = Field(default=True, description="Include financial context")


class ConversationSummary(BaseModel):
    """Schema for conversation summary"""
    user_id: UUID = Field(..., description="User identifier")
    summary: str = Field(..., description="Conversation summary")
    key_topics: List[str] = Field(default=[], description="Main topics discussed")
    recommendations_given: List[str] = Field(default=[], description="Recommendations provided")
    total_conversations: int = Field(..., description="Number of conversations")
    avg_rating: Optional[float] = Field(default=None, description="Average user rating")
    follow_up_needed: bool = Field(default=False, description="Whether follow-up is needed")
    period_start: datetime = Field(..., description="Summary period start")
    period_end: datetime = Field(..., description="Summary period end")


class ConversationAnalytics(BaseModel):
    """Schema for conversation analytics"""
    total_conversations: int = Field(..., description="Total number of conversations")
    avg_confidence_score: Optional[float] = Field(default=None)
    avg_processing_time_ms: Optional[float] = Field(default=None)
    avg_user_rating: Optional[float] = Field(default=None)
    helpfulness_rate: Optional[float] = Field(default=None, description="Percentage of helpful responses")
    most_common_contexts: List[str] = Field(default=[], description="Most common conversation contexts")
    improvement_areas: List[str] = Field(default=[], description="Areas needing improvement")
    response_type_distribution: Dict[str, int] = Field(default={}, description="Distribution of response types")


class FeedbackRequest(BaseModel):
    """Schema for providing feedback on AI responses"""
    conversation_id: UUID = Field(..., description="Conversation to provide feedback for")
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="Rating (1-5)")
    was_helpful: Optional[bool] = Field(default=None, description="Whether response was helpful")
    feedback_text: Optional[str] = Field(default=None, max_length=500, description="Additional feedback")

    @field_validator('rating', 'was_helpful')
    def at_least_one_feedback(cls, v, values):
        """Ensure at least one type of feedback is provided"""
        if not v and 'rating' not in values and 'was_helpful' not in values:
            raise ValueError('At least one form of feedback must be provided')
        return v


class ConversationListResponse(BaseModel):
    """Schema for paginated conversation list"""
    conversations: List[AIConversationResponse] = Field(..., description="List of conversations")
    total_count: int = Field(..., description="Total number of conversations")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    has_next: bool = Field(..., description="Whether there are more pages")

