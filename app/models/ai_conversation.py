from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime, timezone
import uuid
import re
from supabase import Client, PostgrestAPIError
from app.core.constants import ConversationContext, AIResponseType, AI_RESPONSE_MAX_LENGTH
from app.db.supabase_client import get_supabase_client

supabase: Client = get_supabase_client()

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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")  # Added

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: str,
        }

class AIConversationBase(BaseModel):
    context: ConversationContext = Field(default=ConversationContext.GENERAL)
    user_message: str = Field(..., min_length=1, max_length=1000)
    response_type: AIResponseType = Field(default=AIResponseType.ADVICE)

class AIConversationCreate(AIConversationBase):
    ai_response: str = Field(..., min_length=1, max_length=AI_RESPONSE_MAX_LENGTH)

class AIConversationUpdate(AIConversationBase):
    user_rating: Optional[int] = Field(default=None, ge=1, le=5)
    was_helpful: Optional[bool] = Field(default=None)

class AIConversationResponse(AIConversationBase):
    conversation_id: uuid.UUID = Field(...)
    user_id: uuid.UUID = Field(...)
    ai_response: str = Field(...)
    user_rating: Optional[int] = Field(default=None)
    was_helpful: Optional[bool] = Field(default=None)
    confidence_score: Optional[float] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)  # Added

class ConversationAnalytics(AIConversationBase):
    total_conversations: int = Field(...)
    avg_confidence_score: Optional[float] = Field(default=None)
    avg_user_rating: Optional[float] = Field(default=None)
    helpfulness_rate: Optional[float] = Field(default=None)
    most_common_contexts: List[str] = Field(default=[])
    improvement_areas: List[str] = Field(default=[])
    response_type_distribution: Dict[str, int] = Field(default={})

class AIConversationModel:
    @staticmethod
    def create_conversation(data: AIConversationCreate, user_id: uuid.UUID) -> AIConversation:
        """Create a new conversation in the ai_conversations table."""
        try:
            conversation_data = data.model_dump(exclude_unset=True)
            conversation_data["conversation_id"] = str(uuid.uuid4())
            conversation_data["user_id"] = str(user_id)
            conversation_data["created_at"] = datetime.now(timezone.utc).isoformat()
            conversation_data["updated_at"] = datetime.now(timezone.utc).isoformat()

            response = supabase.table("ai_conversations").insert(conversation_data).execute()
            if not response.data:
                raise ValueError("Failed to create conversation")
            return AIConversation(**response.data[0])
        except PostgrestAPIError as e:
            raise ValueError(f"Database error creating conversation: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error creating conversation: {str(e)}")

    @staticmethod
    def get_conversation(conversation_id: uuid.UUID) -> Optional[AIConversation]:
        """Fetch a single conversation by ID."""
        try:
            response = supabase.table("ai_conversations").select("*").eq("conversation_id", str(conversation_id)).single().execute()
            if response.data:
                return AIConversation(**response.data)
            return None
        except PostgrestAPIError as e:
            if "single" in str(e).lower() and "0 rows" in str(e).lower():
                return None
            raise ValueError(f"Database error fetching conversation: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error fetching conversation: {str(e)}")

    @staticmethod
    def update_conversation_feedback(conversation_id: uuid.UUID, feedback: AIConversationUpdate) -> AIConversation:
        """Update feedback for a conversation."""
        try:
            update_data = feedback.model_dump(exclude_unset=True, exclude_none=True)
            if not update_data:
                raise ValueError("No feedback provided")
            update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

            response = supabase.table("ai_conversations").update(update_data).eq("conversation_id", str(conversation_id)).execute()
            if not response.data:
                raise ValueError(f"Conversation with ID {conversation_id} not found")
            return AIConversation(**response.data[0])
        except PostgrestAPIError as e:
            raise ValueError(f"Database error updating feedback: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error updating feedback: {str(e)}")

    @staticmethod
    def extract_and_record_expense(user_message: str, conversation_id: uuid.UUID, user_id: str) -> Dict:
        """Extracts expense details from user message, records them in Supabase, and updates conversation."""
        try:
            # Basic regex to extract amount, category, and description
            amount_match = re.search(r'\$?(\d+\.?\d*)', user_message)
            category_match = re.search(r'(food|grocery|transport|entertainment|other)', user_message.lower())
            description = user_message[:100]

            if not amount_match:
                return {
                    "status": "error",
                    "message": "Could not identify expense amount. Please clarify (e.g., 'I spent $30 on groceries')."
                }

            amount = float(amount_match.group(1))
            category = category_match.group(1) if category_match else "other"

            # Record expense in 'expenses' table
            expense = {
                "user_id": user_id,
                "amount": amount,
                "category": category,
                "description": description,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "conversation_id": str(conversation_id)
            }
            expense_response = supabase.table("expenses").insert(expense).execute()

            if not expense_response.data:
                return {"status": "error", "message": "Failed to record expense. Please try again."}

            # Update conversation with AI response
            ai_response = f"Recorded expense: ${amount} on {category} ({description}). Anything else you'd like to share about your day or spending?"
            conversation_update = {
                "ai_response": ai_response,
                "response_type": AIResponseType.ADVICE.value,
                "context": ConversationContext.FINANCIAL.value,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            conversation_response = supabase.table("ai_conversations").update(conversation_update).eq("conversation_id", str(conversation_id)).execute()

            if not conversation_response.data:
                return {"status": "error", "message": "Failed to update conversation. Expense recorded, but response not saved."}

            # Check for emotional context
            emotional_keywords = ["stressed", "upset", "impulse", "bad mood"]
            emotional_advice = ""
            if any(keyword in user_message.lower() for keyword in emotional_keywords):
                emotional_advice = (
                    "It sounds like you might be feeling stressed. Try taking a moment to breathe deeply or "
                    "reflect before making more purchases. Would you like tips to manage impulse spending?"
                )

            return {
                "status": "success",
                "message": ai_response + " " + emotional_advice,
                "expense": expense
            }
        except PostgrestAPIError as e:
            return {"status": "error", "message": f"Database error processing expense: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error processing expense: {str(e)}"}

    @staticmethod
    def get_conversation_analytics(user_id: uuid.UUID) -> ConversationAnalytics:
        """Compute analytics for a user's conversations."""
        try:
            response = supabase.table("ai_conversations").select("*").eq("user_id", str(user_id)).execute()
            conversations = response.data or []
            total_conversations = len(conversations)

            if not conversations:
                return ConversationAnalytics(
                    total_conversations=0,
                    user_message="",
                    response_type=AIResponseType.ADVICE,
                    context=ConversationContext.GENERAL
                )

            confidence_scores = [c["confidence_score"] for c in conversations if c["confidence_score"] is not None]
            user_ratings = [c["user_rating"] for c in conversations if c["user_rating"] is not None]
            helpful_responses = [c for c in conversations if c["was_helpful"] is True]
            contexts = [c["context"] for c in conversations if c["context"] is not None]
            response_types = [c["response_type"] for c in conversations if c["response_type"] is not None]

            avg_confidence_score = sum(confidence_scores) / len(confidence_scores) if confidence_scores else None
            avg_user_rating = sum(user_ratings) / len(user_ratings) if user_ratings else None
            helpfulness_rate = len(helpful_responses) / total_conversations if total_conversations else None
            most_common_contexts = list(set(contexts))[:3]  # Top 3 contexts
            response_type_distribution = {rt: response_types.count(rt) for rt in set(response_types)}

            return ConversationAnalytics(
                total_conversations=total_conversations,
                avg_confidence_score=avg_confidence_score,
                avg_user_rating=avg_user_rating,
                helpfulness_rate=helpfulness_rate,
                most_common_contexts=most_common_contexts,
                response_type_distribution=response_type_distribution,
                user_message="Analytics computed",
                response_type=AIResponseType.ANALYTICS,
                context=ConversationContext.GENERAL
            )
        except PostgrestAPIError as e:
            raise ValueError(f"Database error computing analytics: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error computing analytics: {str(e)}")