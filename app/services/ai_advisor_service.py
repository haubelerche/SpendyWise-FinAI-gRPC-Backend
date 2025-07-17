"""
AI Advisor Service - Chatbot Training & Financial Advice
Handles conversation management, context, and financial recommendations
"""
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json

from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.settings import get_settings
from app.db.repositories import TransactionRepository, BudgetRepository
from app.models.user import User
from app.schemas.ai_advisor import ChatRequest, ChatResponse, FinancialAdviceRequest
from app.utils.financial_calculations import FinancialCalculator

logger = logging.getLogger(__name__)
settings = get_settings()


class AIAdvisorService:
    """
    AI Financial Advisor with conversation memory and personalized recommendations
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Conversation memory per user (limited window for mobile efficiency)
        self.user_memories: Dict[str, ConversationBufferWindowMemory] = {}
        
        # Financial context embeddings for better responses
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Financial advisor prompt template
        self.chat_prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{user_input}")
        ])
        
        self.financial_calculator = FinancialCalculator()
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI financial advisor"""
        return """You are SpendyWise, an expert AI financial advisor and personal finance coach.
        
Your personality:
- Friendly, encouraging, and supportive
- Clear and practical in explanations
- Focused on actionable advice
- Empathetic to financial struggles
- Celebrates financial wins

Your expertise:
- Personal budgeting and expense tracking
- Debt management and payoff strategies
- Savings goals and emergency funds
- Investment basics for beginners
- Financial habit formation
- Spending psychology and behavior change

Response guidelines:
- Keep responses concise (mobile-friendly)
- Use emojis sparingly but effectively
- Provide specific, actionable steps
- Reference user's actual financial data when available
- Ask clarifying questions when needed
- Encourage positive financial behaviors

Always prioritize:
1. Emergency fund building
2. Debt reduction
3. Consistent saving habits
4. Mindful spending
5. Long-term financial health"""

    async def chat_with_user(
        self, 
        user_id: str, 
        message: str,
        financial_context: Optional[Dict] = None
    ) -> ChatResponse:
        """
        Process a chat message from user with financial context
        """
        try:
            # Get or create conversation memory for user
            memory = self._get_user_memory(user_id)
            
            # Add financial context if available
            enhanced_message = await self._enhance_message_with_context(
                message, financial_context
            )
            
            # Generate response using conversation chain
            response = await self._generate_response(
                user_id, enhanced_message, memory
            )
            
            # Store conversation in memory
            memory.chat_memory.add_user_message(message)
            memory.chat_memory.add_ai_message(response)
            
            # Generate suggested follow-up questions
            suggestions = await self._generate_suggestions(response, financial_context)
            
            return ChatResponse(
                message=response,
                suggestions=suggestions,
                timestamp=datetime.utcnow(),
                conversation_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error in chat_with_user: {str(e)}")
            return ChatResponse(
                message="I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
                suggestions=["Check my spending", "Budget help", "Savings tips"],
                timestamp=datetime.utcnow(),
                conversation_id=user_id
            )
    
    async def get_financial_advice(
        self, 
        user: User,
        request: FinancialAdviceRequest
    ) -> Dict[str, Any]:
        """
        Generate comprehensive financial advice based on user's data
        """
        try:
            # Gather user's financial data
            financial_data = await self._gather_financial_data(user.id)
            
            # Analyze spending patterns
            spending_analysis = await self._analyze_spending_patterns(financial_data)
            
            # Generate personalized recommendations
            recommendations = await self._generate_recommendations(
                user, financial_data, spending_analysis, request
            )
            
            return {
                "advice": recommendations,
                "analysis": spending_analysis,
                "action_items": await self._generate_action_items(recommendations),
                "financial_health_score": await self._calculate_financial_health_score(financial_data)
            }
            
        except Exception as e:
            logger.error(f"Error generating financial advice: {str(e)}")
            raise
    
    def _get_user_memory(self, user_id: str) -> ConversationBufferWindowMemory:
        """Get or create conversation memory for user (mobile-optimized)"""
        if user_id not in self.user_memories:
            self.user_memories[user_id] = ConversationBufferWindowMemory(
                k=10,  # Keep last 10 messages for mobile efficiency
                return_messages=True,
                memory_key="chat_history"
            )
        return self.user_memories[user_id]
    
    async def _enhance_message_with_context(
        self, 
        message: str, 
        financial_context: Optional[Dict]
    ) -> str:
        """Add relevant financial context to user message"""
        if not financial_context:
            return message
        
        context_parts = []
        
        if financial_context.get("recent_transactions"):
            context_parts.append(f"Recent spending: {financial_context['recent_transactions']}")
        
        if financial_context.get("budget_status"):
            context_parts.append(f"Budget status: {financial_context['budget_status']}")
        
        if financial_context.get("account_balance"):
            context_parts.append(f"Account balance: ${financial_context['account_balance']}")
        
        if context_parts:
            enhanced = f"{message}\n\nFinancial context: {'; '.join(context_parts)}"
            return enhanced
        
        return message
    
    async def _generate_response(
        self, 
        user_id: str, 
        message: str, 
        memory: ConversationBufferWindowMemory
    ) -> str:
        """Generate AI response using conversation chain"""
        
        # Get chat history from memory
        chat_history = memory.chat_memory.messages
        
        # Create the conversation chain
        chain = self.chat_prompt | self.llm
        
        # Generate response
        response = await chain.ainvoke({
            "user_input": message,
            "chat_history": chat_history
        })
        
        return response.content
    
    async def _generate_suggestions(
        self, 
        response: str, 
        financial_context: Optional[Dict]
    ) -> List[str]:
        """Generate contextual follow-up suggestions"""
        base_suggestions = [
            "How can I save more money?",
            "Help me create a budget",
            "Show my spending trends"
        ]
        
        # Add context-specific suggestions
        if financial_context:
            if financial_context.get("overspent_categories"):
                base_suggestions.insert(0, "How to reduce overspending?")
            
            if financial_context.get("savings_goal"):
                base_suggestions.insert(0, "Track my savings goal")
        
        return base_suggestions[:3]  # Keep mobile-friendly
    
    async def _gather_financial_data(self, user_id: str) -> Dict[str, Any]:
        """Gather comprehensive financial data for analysis"""
        # This would integrate with your repositories
        # Implementation depends on your database structure
        return {
            "transactions": [],
            "budgets": [],
            "savings_goals": [],
            "debts": []
        }
    
    async def _analyze_spending_patterns(self, financial_data: Dict) -> Dict[str, Any]:
        """Analyze user's spending patterns using pandas/numpy"""
        if not financial_data.get("transactions"):
            return {"status": "insufficient_data"}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(financial_data["transactions"])
        
        analysis = {
            "total_spending": df["amount"].sum(),
            "avg_daily_spending": df["amount"].mean(),
            "spending_by_category": df.groupby("category")["amount"].sum().to_dict(),
            "spending_trend": self._calculate_trend(df),
            "unusual_spending": self._detect_unusual_spending(df)
        }
        
        return analysis
    
    def _calculate_trend(self, df: pd.DataFrame) -> str:
        """Calculate spending trend over time"""
        if len(df) < 7:
            return "insufficient_data"
        
        # Simple trend calculation
        recent_avg = df.tail(7)["amount"].mean()
        older_avg = df.head(7)["amount"].mean()
        
        if recent_avg > older_avg * 1.1:
            return "increasing"
        elif recent_avg < older_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    def _detect_unusual_spending(self, df: pd.DataFrame) -> List[Dict]:
        """Detect unusual spending patterns"""
        if len(df) < 10:
            return []
        
        # Statistical outlier detection
        mean_amount = df["amount"].mean()
        std_amount = df["amount"].std()
        threshold = mean_amount + (2 * std_amount)
        
        unusual = df[df["amount"] > threshold]
        return unusual.to_dict("records")
    
    async def _generate_recommendations(
        self, 
        user: User,
        financial_data: Dict,
        analysis: Dict,
        request: FinancialAdviceRequest
    ) -> str:
        """Generate personalized financial recommendations"""
        
        prompt = f"""
        Generate personalized financial advice for a user with the following profile:
        
        User Goals: {request.goals if hasattr(request, 'goals') else 'General financial health'}
        Financial Analysis: {json.dumps(analysis, indent=2)}
        
        Provide specific, actionable advice focusing on:
        1. Most important immediate actions
        2. Budget optimization suggestions
        3. Savings opportunities
        4. Debt management (if applicable)
        5. Long-term financial planning
        
        Keep advice practical and motivating. Limit to 300 words for mobile readability.
        """
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content
    
    async def _generate_action_items(self, recommendations: str) -> List[str]:
        """Extract actionable items from recommendations"""
        prompt = f"""
        Extract 3-5 specific, actionable items from this financial advice:
        
        {recommendations}
        
        Format as a simple list of concrete actions the user can take this week.
        Each item should start with an action verb and be achievable.
        """
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        
        # Parse response into list
        actions = [
            line.strip() 
            for line in response.content.split('\n') 
            if line.strip() and (line.strip().startswith('-') or line.strip().startswith('•'))
        ]
        
        return actions[:5]  # Limit for mobile display
    
    async def _calculate_financial_health_score(self, financial_data: Dict) -> int:
        """Calculate a simple financial health score (0-100)"""
        score = 50  # Base score
        
        # Add points for positive behaviors
        if financial_data.get("emergency_fund", 0) > 0:
            score += 15
        
        if financial_data.get("savings_rate", 0) > 0.1:  # 10% savings rate
            score += 20
        
        if financial_data.get("debt_to_income", 1) < 0.3:  # Low debt ratio
            score += 15
        
        # Ensure score stays within bounds
        return max(0, min(100, score))
    
    async def clear_user_memory(self, user_id: str):
        """Clear conversation memory for user"""
        if user_id in self.user_memories:
            del self.user_memories[user_id]
    
    async def get_conversation_summary(self, user_id: str) -> Optional[str]:
        """Get a summary of the user's conversation"""
        memory = self.user_memories.get(user_id)
        if not memory or not memory.chat_memory.messages:
            return None
        
        # Generate summary using AI
        messages_text = "\n".join([
            f"{'User' if isinstance(msg, HumanMessage) else 'AI'}: {msg.content}"
            for msg in memory.chat_memory.messages
        ])
        
        prompt = f"""
        Summarize this financial conversation in 2-3 sentences:
        
        {messages_text}
        
        Focus on the user's main concerns and the advice given.
        """
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content
