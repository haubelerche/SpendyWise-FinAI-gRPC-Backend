from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, Literal, List
from datetime import datetime, timezone
import uuid
from app.core.constants import ConversationContext, AIResponseType, AI_RESPONSE_MAX_LENGTH
from supabase import Client
from app.db.supabase_client import get_supabase_client

class AIConversation(BaseModel):
    conversation_id: uuid.UUID = Field(..., description="Conversation unique identifier")
    user_id: uuid.UUID = Field(..., description="User identifier")
    context: Optional[ConversationContext] = Field(default=None, description="Conversation context")
    user_message: str = Field(..., min_length=1, max_length=1000, description="User's message")
    ai_response: str = Field(..., min_length=1, max_length=AI_RESPONSE_MAX_LENGTH, description="AI's response")
    response_type: Optional[AIResponseType] = Field(default=None, description="Type of AI response")
    user_rating: Optional[int] = Field(default=None, ge=1, le=5, description="User rating (1-5)")
    was_helpful: Optional[bool] = Field(default=None, description="Whether response was helpful")
    confidence_score: Optional[float] = Field(default=None, description="Response confidence")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(), 
            uuid.UUID: str,  
        }


class AIConversationBase(BaseModel):
    """Base schema for AI conversations"""
    context: ConversationContext = Field(default=ConversationContext.GENERAL, description="Conversation context")
    user_message: str = Field(..., min_length=1, max_length=1000, description="User's message")
    response_type: AIResponseType = Field(default=AIResponseType.ADVICE, description="Type of AI response")


class AIConversationCreate(AIConversationBase):
    """Schema for creating AI conversations"""
    ai_response: str = Field(..., min_length=1, max_length=AI_RESPONSE_MAX_LENGTH, description="AI's response")


class AIConversationUpdate(BaseModel):
    """Schema for updating AI conversations (mainly feedback)"""
    user_rating: Optional[int] = Field(default=None, ge=1, le=5, description="User rating (1-5)")
    was_helpful: Optional[bool] = Field(default=None, description="Whether response was helpful")


class AIConversationResponse(AIConversationBase):
    """Schema for AI conversation responses"""
    conversation_id: uuid.UUID = Field(..., description="Conversation unique identifier")
    user_id: uuid.UUID = Field(..., description="User identifier")
    ai_response: str = Field(..., description="AI's response")
    user_rating: Optional[int] = Field(default=None, description="User rating")
    was_helpful: Optional[bool] = Field(default=None, description="Helpfulness feedback")
    confidence_score: Optional[float] = Field(default=None, description="Response confidence")
    created_at: datetime = Field(..., description="Creation timestamp")


class ChatMessage(BaseModel):
    """Schema for individual chat messages"""
    message: str = Field(..., min_length=1, max_length=1000, description="Chat message")
    context: ConversationContext = Field(default=ConversationContext.GENERAL)
    financial_context: Optional[Dict[str, Any]] = Field(default=None)


class ChatResponse(BaseModel):
    """Schema for chat response"""
    conversation_id: uuid.UUID = Field(..., description="Conversation identifier")
    message: str = Field(..., description="AI response message")
    suggestions: List[str] = Field(default=[], description="Follow-up suggestions")
    context: ConversationContext = Field(..., description="Conversation context")
    confidence_score: Optional[float] = Field(default=None)
    timestamp: datetime = Field(..., description="Response timestamp")


class ConversationSummaryRequest(BaseModel):
    """Schema for conversation summary requests"""
    days_back: int = Field(default=7, ge=1, le=30, description="Days of conversation history")
    include_context: bool = Field(default=True, description="Include financial context")


class ConversationSummary(BaseModel):
    """Schema for conversation summary"""
    user_id: uuid.UUID = Field(..., description="User identifier")
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
    avg_user_rating: Optional[float] = Field(default=None)
    helpfulness_rate: Optional[float] = Field(default=None, description="Percentage of helpful responses")
    most_common_contexts: List[str] = Field(default=[], description="Most common conversation contexts")
    improvement_areas: List[str] = Field(default=[], description="Areas needing improvement")
    response_type_distribution: Dict[str, int] = Field(default={}, description="Distribution of response types")


class FeedbackRequest(BaseModel):
    """Schema for providing feedback on AI responses"""
    conversation_id: uuid.UUID = Field(..., description="Conversation to provide feedback for")
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="Rating (1-5)")
    was_helpful: Optional[bool] = Field(default=None, description="Whether response was helpful")
    feedback_text: Optional[str] = Field(default=None, max_length=500, description="Additional feedback")

    @field_validator('rating', 'was_helpful', 'feedback_text')
    def at_least_one_feedback(self , v, info):
        """Ensure at least one type of feedback is provided"""
        values = info.data
        if not any([values.get('rating'), values.get('was_helpful'), values.get('feedback_text')]):
            raise ValueError('At least one form of feedback must be provided')
        return v


class ConversationListResponse(BaseModel):
    """Schema for paginated conversation list"""
    conversations: List[AIConversationResponse] = Field(..., description="List of conversations")
    total_count: int = Field(..., description="Total number of conversations")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    has_next: bool = Field(..., description="Whether there are more pages")





supabase: Client = get_supabase_client()
def create_conversation(conversation_data: AIConversationCreate, user_id: uuid.UUID):
    """Create a new conversation in the ai_conversations table."""
    data = conversation_data.model_dump(exclude_unset=True)
    data["conversation_id"] = str(uuid.uuid4())
    data["user_id"] = str(user_id)
    data["created_at"] =  datetime.now(timezone.utc)
    return supabase.table("ai_conversations").insert(data).execute()

def get_conversation(conversation_id: uuid.UUID):
    """Fetch a single conversation by ID."""
    return supabase.table("ai_conversations").select("*").eq("conversation_id", str(conversation_id)).execute()

def update_conversation_feedback(conversation_id: uuid.UUID, feedback: AIConversationUpdate):
    """Update feedback for a conversation."""
    data = feedback.model_dump(exclude_unset=True)
    return supabase.table("ai_conversations").update(data).eq("conversation_id", str(conversation_id)).execute()
def extract_and_record_expense(user_message: str, conversation_id: uuid.UUID):
    expense = {"amount": 50.0, "category": "food", "description": "Lunch"}  # Example parsing
    # If financial_context were in the table, update it here
    return supabase.table("ai_conversations").update({"ai_response": f"Recorded expense: {expense}"}).eq("conversation_id", str(conversation_id)).execute()

