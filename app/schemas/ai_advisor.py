"""
AI Advisor Pydantic Schemas for gRPC Message Validation
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ConversationContext(str, Enum):
    """Types of conversation context"""
    GENERAL = "general"
    BUDGETING = "budgeting"
    SPENDING_ANALYSIS = "spending_analysis"
    DEBT_MANAGEMENT = "debt_management"
    SAVINGS_GOALS = "savings_goals"
    INVESTMENT_ADVICE = "investment_advice"


class ChatRequest(BaseModel):
    """Request schema for chat messages"""
    user_id: str = Field(..., description="User identifier")
    message: str = Field(..., min_length=1, max_length=1000, description="User message")
    context: Optional[ConversationContext] = Field(default=ConversationContext.GENERAL)
    financial_context: Optional[Dict[str, Any]] = Field(default=None, description="Additional financial data")
    session_id: Optional[str] = Field(default=None, description="Conversation session ID")


class ChatResponse(BaseModel):
    """Response schema for chat messages"""
    message: str = Field(..., description="AI advisor response")
    suggestions: List[str] = Field(default=[], description="Follow-up suggestions")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    conversation_id: str = Field(..., description="Conversation identifier")
    context: Optional[ConversationContext] = Field(default=None)
    confidence_score: Optional[float] = Field(default=None, ge=0, le=1)


class FinancialAdviceRequest(BaseModel):
    """Request for comprehensive financial advice"""
    user_id: str = Field(..., description="User identifier")
    goals: List[str] = Field(default=[], description="User's financial goals")
    time_horizon: Optional[str] = Field(default="short_term", description="Planning horizon")
    risk_tolerance: Optional[str] = Field(default="moderate", description="Risk tolerance level")
    focus_areas: List[str] = Field(default=[], description="Specific areas of interest")


class FinancialAdviceResponse(BaseModel):
    """Response with comprehensive financial advice"""
    advice: str = Field(..., description="Detailed financial advice")
    action_items: List[str] = Field(default=[], description="Specific action items")
    financial_health_score: int = Field(..., ge=0, le=100, description="Financial health score")
    analysis: Dict[str, Any] = Field(default={}, description="Financial analysis data")
    recommendations: List[str] = Field(default=[], description="Key recommendations")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SpendingInsight(BaseModel):
    """Spending pattern insights"""
    category: str = Field(..., description="Spending category")
    amount: float = Field(..., description="Amount spent")
    percentage_of_income: Optional[float] = Field(default=None, ge=0, le=100)
    trend: str = Field(..., description="Spending trend")
    recommendation: Optional[str] = Field(default=None)


class BudgetRecommendation(BaseModel):
    """Budget optimization recommendations"""
    category: str = Field(..., description="Budget category")
    current_allocation: float = Field(..., description="Current budget allocation")
    recommended_allocation: float = Field(..., description="Recommended allocation")
    reasoning: str = Field(..., description="Reason for recommendation")
    potential_savings: Optional[float] = Field(default=None)


class ConversationSummary(BaseModel):
    """Summary of user's conversation"""
    user_id: str = Field(..., description="User identifier")
    summary: str = Field(..., description="Conversation summary")
    key_topics: List[str] = Field(default=[], description="Main topics discussed")
    recommendations_given: List[str] = Field(default=[], description="Recommendations provided")
    follow_up_needed: bool = Field(default=False, description="Whether follow-up is needed")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AITrainingData(BaseModel):
    """Schema for AI model training data"""
    user_message: str = Field(..., description="User input message")
    ai_response: str = Field(..., description="AI response")
    context: Dict[str, Any] = Field(default={}, description="Conversation context")
    feedback_score: Optional[int] = Field(default=None, ge=1, le=5, description="User feedback score")
    financial_outcome: Optional[str] = Field(default=None, description="Actual financial outcome")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ModelPerformanceMetrics(BaseModel):
    """Metrics for AI model performance"""
    accuracy_score: float = Field(..., ge=0, le=1)
    user_satisfaction: float = Field(..., ge=0, le=5)
    response_time_ms: int = Field(..., ge=0)
    context_relevance: float = Field(..., ge=0, le=1)
    advice_effectiveness: Optional[float] = Field(default=None, ge=0, le=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatbotTrainingRequest(BaseModel):
    """Request to update chatbot training"""
    training_data: List[AITrainingData] = Field(..., min_items=1)
    model_version: str = Field(..., description="Model version identifier")
    training_type: str = Field(default="incremental", description="Type of training")


class FinancialGoal(BaseModel):
    """User's financial goal for AI context"""
    goal_type: str = Field(..., description="Type of financial goal")
    target_amount: Optional[float] = Field(default=None, ge=0)
    target_date: Optional[datetime] = Field(default=None)
    priority: int = Field(default=1, ge=1, le=5, description="Goal priority")
    progress: Optional[float] = Field(default=0, ge=0, le=100, description="Progress percentage")


class EmotionalContext(BaseModel):
    """Emotional context for personalized responses"""
    mood: str = Field(..., description="User's current mood")
    stress_level: int = Field(default=1, ge=1, le=5, description="Financial stress level")
    confidence_level: int = Field(default=3, ge=1, le=5, description="Financial confidence")
    motivation_level: int = Field(default=3, ge=1, le=5, description="Motivation to change")
