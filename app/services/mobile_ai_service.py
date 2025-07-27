"""
Lightweight AI service for mobile transaction processing
Processes user input and extracts transaction data
"""
import json
import re
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal
import openai
from app.core.settings import get_settings
from app.db.repositories import AIConversationRepository, MobileTransactionRepository
from app.schemas.mobile_models import TransactionType, ExpenseCategory, IncomeCategory

settings = get_settings()
openai.api_key = settings.OPENAI_API_KEY

class MobileAIService:
    def __init__(self):
        self.conversation_repo = AIConversationRepository()
        self.transaction_repo = MobileTransactionRepository()
    
    async def process_user_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Process user message and extract transaction data
        Returns conversation record with extracted data
        """
        try:
            # Create conversation record
            conversation_data = {
                'user_id': user_id,
                'message': message,
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Extract transaction data using AI
            extracted_data = await self._extract_transaction_data(message)
            
            if extracted_data and extracted_data.get('has_transaction'):
                conversation_data['extracted_data'] = extracted_data
                conversation_data['response'] = f"I found a {extracted_data['transaction_type']} of ${extracted_data['amount']} for {extracted_data['description']}. Should I record this?"
            else:
                conversation_data['response'] = "I couldn't find transaction information in your message. Could you tell me the amount and what it was for?"
            
            # Save conversation
            conversation = await self.conversation_repo.create_conversation(conversation_data)
            return conversation
            
        except Exception as e:
            return {
                'user_id': user_id,
                'message': message,
                'response': f"Sorry, I had trouble processing your message. Please try again.",
                'error': str(e)
            }
    
    async def confirm_and_create_transaction(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Create transaction from confirmed conversation
        """
        try:
            # Get conversation with extracted data
            conversations = await self.conversation_repo.get_user_conversations(
                user_id="", limit=1  # We'll need to modify this to get by ID
            )
            
            if not conversations:
                return None
                
            conversation = conversations[0]
            extracted_data = conversation.get('extracted_data', {})
            
            if not extracted_data.get('has_transaction'):
                return None
            
            # Create transaction
            transaction_data = {
                'user_id': conversation['user_id'],
                'amount': extracted_data['amount'],
                'transaction_type': extracted_data['transaction_type'],
                'category': extracted_data.get('category'),
                'description': extracted_data['description'],
                'transaction_date': extracted_data.get('date', date.today().isoformat()),
                'ai_extracted': True,
                'ai_confidence': extracted_data.get('confidence', 0.8),
                'raw_input': conversation['message']
            }
            
            transaction = await self.transaction_repo.create_transaction(transaction_data)
            
            # Update conversation
            await self.conversation_repo.update_conversation(
                conversation_id,
                {
                    'transaction_created': True,
                    'transaction_id': transaction['id']
                }
            )
            
            return transaction
            
        except Exception as e:
            return None
    
    async def _extract_transaction_data(self, message: str) -> Dict[str, Any]:
        """
        Extract transaction data from user message using OpenAI
        """
        try:
            prompt = f"""
            Extract transaction information from this message: "{message}"
            
            Return JSON with:
            - has_transaction: boolean (true if transaction info found)
            - amount: number (extract dollar amount)
            - transaction_type: "income" or "expense"
            - description: string (what the transaction was for)
            - category: string (food, transport, shopping, bills, etc.)
            - confidence: number (0-1, how confident you are)
            
            Examples:
            "I spent $15 on lunch" -> {{"has_transaction": true, "amount": 15, "transaction_type": "expense", "description": "lunch", "category": "food", "confidence": 0.9}}
            "Got paid $500" -> {{"has_transaction": true, "amount": 500, "transaction_type": "income", "description": "payment", "category": "salary", "confidence": 0.8}}
            """
            
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            return json.loads(result)
            
        except Exception as e:
            # Fallback: simple regex extraction
            return self._simple_extract(message)
    
    def _simple_extract(self, message: str) -> Dict[str, Any]:
        """
        Simple fallback extraction using regex
        """
        # Look for dollar amounts
        amount_match = re.search(r'\$?(\d+(?:\.\d{2})?)', message.lower())
        
        # Look for expense keywords
        expense_keywords = ['spent', 'bought', 'paid', 'cost', 'expense']
        income_keywords = ['got', 'received', 'earned', 'paid', 'income']
        
        message_lower = message.lower()
        
        if amount_match:
            amount = float(amount_match.group(1))
            
            # Determine transaction type
            transaction_type = "expense"
            if any(keyword in message_lower for keyword in income_keywords):
                transaction_type = "income"
            
            return {
                'has_transaction': True,
                'amount': amount,
                'transaction_type': transaction_type,
                'description': message,
                'category': 'other',
                'confidence': 0.6
            }
        
        return {'has_transaction': False}
