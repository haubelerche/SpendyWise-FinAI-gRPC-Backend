from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, Literal, List
from datetime import datetime, timezone
import uuid
from app.core.constants import ConversationContext, AIResponseType, AI_RESPONSE_MAX_LENGTH
from supabase import Client
from app.db.supabase_client import get_supabase_client
import re

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
    created_at: datetime = Field(default=datetime.now(timezone.utc), description="Creation timestamp")

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True  # Handle Decimal and datetime
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


class AIConversationUpdate(AIConversationBase):
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
    created_at: datetime = Field(default=datetime.now(timezone.utc), description="Creation timestamp")


class ConversationAnalytics(AIConversationBase):
    """Schema for conversation analytics"""
    total_conversations: int = Field(..., description="Total number of conversations")
    avg_confidence_score: Optional[float] = Field(default=None)
    avg_user_rating: Optional[float] = Field(default=None)
    helpfulness_rate: Optional[float] = Field(default=None, description="Percentage of helpful responses")
    most_common_contexts: List[str] = Field(default=[], description="Most common conversation contexts")
    improvement_areas: List[str] = Field(default=[], description="Areas needing improvement")
    response_type_distribution: Dict[str, int] = Field(default={}, description="Distribution of response types")


supabase: Client = get_supabase_client()
def create_conversation(conversation_data: AIConversationCreate, user_id: uuid.UUID):
    """Create a new conversation in the ai_conversations table."""
    data = conversation_data.model_dump(exclude_unset=True)
    data["conversation_id"] = str(uuid.uuid4())
    data["user_id"] = str(user_id)
    data["created_at"] = datetime.now(timezone.utc)
    response = supabase.table("ai_conversations").insert(data).execute()
    if not response.data:
        raise ValueError("Failed to create conversation.")
    return response

def get_conversation(conversation_id: uuid.UUID):
    """Fetch a single conversation by ID."""
    response = supabase.table("ai_conversations").select("*").eq("conversation_id", str(conversation_id)).execute()
    if not response.data:
        raise ValueError("Conversation not found.")
    return response

def update_conversation_feedback(conversation_id: uuid.UUID, feedback: AIConversationUpdate):
    """Update feedback for a conversation."""
    data = feedback.model_dump(exclude_unset=True)
    response = supabase.table("ai_conversations").update(data).eq("conversation_id", str(conversation_id)).execute()
    if not response.data:
        raise ValueError("Failed to update conversation feedback.")
    return response


def extract_and_record_expense(user_message: str, conversation_id: uuid.UUID, supabase: Client, user_id: str) -> Dict:
    """
    Extracts expense details from user message, records them in Supabase, and returns a response.

    Args:
        user_message (str): User's input (e.g., "I spent $30 on groceries")
        conversation_id (uuid.UUID): Unique ID for the conversation
        supabase (Client): Supabase client instance
        user_id (str): User's ID for associating expenses

    Returns:
        Dict: Response with status and message
    """
    try:
        # Basic regex to extract amount, category, and description
        amount_match = re.search(r'\$?(\d+\.?\d*)', user_message)
        category_match = re.search(r'(food|grocery|transport|entertainment|other)', user_message.lower())
        description = user_message[:100]  # Truncate description for brevity

        # Validate extracted data
        if not amount_match:
            return {"status": "error",
                    "message": "Could not identify expense amount. Please clarify (e.g., 'I spent $30 on groceries')."}

        amount = float(amount_match.group(1))
        category = category_match.group(1) if category_match else "other"

        # Record expense in a dedicated 'expenses' table
        expense = {
            "user_id": user_id,
            "amount": amount,
            "category": category,
            "description": description,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "conversation_id": str(conversation_id)
        }

        # Insert expense into Supabase
        expense_response = supabase.table("expenses").insert(expense).single()

        if not expense_response.data:
            return {"status": "error", "message": "Failed to record expense. Please try again."}

        # Update conversation with AI response
        ai_response = f"Recorded expense: ${amount} on {category} ({description}). Anything else you'd like to share about your day or spending?"
        conversation_response = supabase.table("ai_conversations").update({
            "ai_response": ai_response
        }).eq("conversation_id", str(conversation_id)).single()

        # Check for emotional context (simplified example)
        emotional_keywords = ["stressed", "upset", "impulse", "bad mood"]
        emotional_advice = ""
        if any(keyword in user_message.lower() for keyword in emotional_keywords):
            emotional_advice = "It sounds like you might be feeling stressed. Try taking a moment to breathe deeply or reflect before making more purchases. Would you like tips to manage impulse spending?"

        return {
            "status": "success",
            "message": ai_response + " " + emotional_advice,
            "expense": expense
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error processing expense: {str(e)}. Please try again."
        }
