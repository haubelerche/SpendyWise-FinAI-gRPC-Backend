"""
đặc biệt chú ý
Transaction Extraction Service
Trích xuất thông tin giao dịch tài chính từ cuộc trò chuyện AI
"""
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
from decimal import Decimal

from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

from app.core.settings import get_settings
from app.core.constants import (
    ExpenseCategory, IncomeCategory, TransactionType,
    MIN_TRANSACTION_AMOUNT, MAX_TRANSACTION_AMOUNT,
    DEFAULT_CURRENCY, SUPPORTED_CURRENCIES
)

logger = logging.getLogger(__name__)
settings = get_settings()


class TransactionExtractionService:
    """
    Service để trích xuất thông tin giao dịch từ tin nhắn tự nhiên
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview", #TODO: nhớ thay model
            temperature=0.1,  # Low temperature for precise extraction
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Patterns để nhận diện số tiền tiếng Việt
        self.money_patterns = [
            r'(\d{1,3}(?:[,\.]\d{3})*)\s*(?:k|nghìn|ngàn)',  # 100k, 500 nghìn
            r'(\d{1,3}(?:[,\.]\d{3})*)\s*(?:tr|triệu)',      # 1tr, 2 triệu  
            r'(\d{1,3}(?:[,\.]\d{3})*)\s*(?:tỷ|tỉ)',        # 1 tỷ
            r'(\d{1,3}(?:[,\.]\d{3})*)\s*(?:đồng|vnd|₫)',   # 50000 đồng
            r'(\d{1,3}(?:[,\.]\d{3})*)\s*(?:usd|\$)',        # 100 USD
        ]
        
        # Keywords cho expense categories
        self.category_keywords = {
            ExpenseCategory.FOOD_DINING: ['ăn', 'cơm', 'phở', 'bún', 'nhà hàng', 'quán', 'đồ ăn', 'thức ăn', 'food'],
            ExpenseCategory.GROCERIES: ['chợ', 'siêu thị', 'mua sắm', 'thực phẩm', 'rau củ', 'thịt cá'],
            ExpenseCategory.TRANSPORTATION: ['xe', 'taxi', 'grab', 'xăng', 'vé xe', 'di chuyển', 'đi lại'],
            ExpenseCategory.SHOPPING: ['mua', 'shop', 'shopping', 'quần áo', 'giày', 'túi', 'đồ dùng'],
            ExpenseCategory.ENTERTAINMENT: ['xem phim', 'karaoke', 'game', 'vui chơi', 'giải trí', 'concert'],
            ExpenseCategory.BILLS_UTILITIES: ['điện', 'nước', 'gas', 'internet', 'điện thoại', 'hóa đơn'],
            ExpenseCategory.HEALTHCARE: ['bác sĩ', 'thuốc', 'khám', 'bệnh viện', 'y tế', 'sức khỏe'],
            ExpenseCategory.EDUCATION: ['học', 'sách', 'khóa học', 'học phí', 'giáo dục'],
            ExpenseCategory.TRAVEL: ['du lịch', 'travel', 'khách sạn', 'vé máy bay', 'tour'],
        }
        
        # Keywords cho spending verbs  
        self.spending_verbs = ['chi', 'tiêu', 'mua', 'trả', 'thanh toán', 'đóng', 'nạp', 'spent', 'paid', 'bought']
        self.income_verbs = ['nhận', 'được', 'kiếm', 'thu', 'lương', 'thưởng', 'received', 'earned']

    async def extract_financial_data_from_message(self, message: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Trích xuất thông tin giao dịch từ tin nhắn
        
        Returns:
            Dict với các field: amount, category, transaction_type, description, date
        """
        try:
            # Step 1: Detect if message contains financial information
            if not self._contains_financial_intent(message):
                return None
            
            # Step 2: Extract amount
            amount = self._extract_amount(message)
            if not amount or amount < MIN_TRANSACTION_AMOUNT:
                return None
                
            # Step 3: Determine transaction type và category
            transaction_type, category = self._classify_transaction(message)
            
            # Step 4: Extract description và date
            description = self._extract_description(message)
            transaction_date = self._extract_date(message)
            
            # Step 5: Validate với AI nếu cần
            validated_data = await self._validate_with_ai(message, {
                'amount': amount,
                'transaction_type': transaction_type,
                'category': category,
                'description': description,
                'date': transaction_date
            })
            
            if validated_data:
                validated_data['user_id'] = user_id
                validated_data['currency'] = DEFAULT_CURRENCY
                validated_data['extracted_from_chat'] = True
                
            return validated_data
            
        except Exception as e:
            logger.error(f"Error extracting financial data: {str(e)}")
            return None

    def _contains_financial_intent(self, message: str) -> bool:
        """Kiểm tra xem tin nhắn có chứa ý định tài chính không"""
        message_lower = message.lower()
        
        # Check for money amounts
        for pattern in self.money_patterns:
            if re.search(pattern, message_lower):
                return True
        
        # Check for spending/income verbs
        for verb in self.spending_verbs + self.income_verbs:
            if verb in message_lower:
                return True
                
        return False

    def _extract_amount(self, message: str) -> Optional[float]:
        """Trích xuất số tiền từ tin nhắn"""
        message_lower = message.lower()
        
        # Try different patterns
        for pattern in self.money_patterns:
            matches = re.findall(pattern, message_lower)
            if matches:
                try:
                    amount_str = matches[0].replace(',', '').replace('.', '')
                    base_amount = float(amount_str)
                    
                    # Apply multipliers
                    if any(unit in message_lower for unit in ['k', 'nghìn', 'ngàn']):
                        return base_amount * 1000
                    elif any(unit in message_lower for unit in ['tr', 'triệu']):
                        return base_amount * 1000000
                    elif any(unit in message_lower for unit in ['tỷ', 'tỉ']):
                        return base_amount * 1000000000
                    elif any(unit in message_lower for unit in ['usd', '$']):
                        return base_amount * 24000  # Rough USD to VND conversion
                    else:
                        return base_amount
                        
                except (ValueError, IndexError):
                    continue
                    
        return None

    def _classify_transaction(self, message: str) -> Tuple[str, str]:
        """Phân loại transaction type và category"""
        message_lower = message.lower()
        
        # Determine transaction type
        has_spending_verb = any(verb in message_lower for verb in self.spending_verbs)
        has_income_verb = any(verb in message_lower for verb in self.income_verbs)
        
        if has_income_verb and not has_spending_verb:
            transaction_type = TransactionType.INCOME.value
            category = IncomeCategory.OTHER.value  # Default income category
        else:
            transaction_type = TransactionType.EXPENSE.value
            
            # Classify expense category
            category = ExpenseCategory.OTHER.value  # Default
            max_matches = 0
            
            for cat, keywords in self.category_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in message_lower)
                if matches > max_matches:
                    max_matches = matches
                    category = cat.value
        
        return transaction_type, category

    def _extract_description(self, message: str) -> str:
        """Tạo description từ tin nhắn gốc"""
        # Clean up message để làm description
        description = message.strip()
        
        # Limit length
        if len(description) > 200:
            description = description[:197] + "..."
            
        return description

    def _extract_date(self, message: str) -> date:
        """Trích xuất ngày từ tin nhắn, default là hôm nay"""
        message_lower = message.lower()
        
        # Simple date extraction cho tiếng Việt
        if any(word in message_lower for word in ['hôm qua', 'yesterday']):
            from datetime import timedelta
            return date.today() - timedelta(days=1)
        elif any(word in message_lower for word in ['hôm nay', 'today']):
            return date.today()
        else:
            # Default to today
            return date.today()

    async def _validate_with_ai(self, original_message: str, extracted_data: Dict) -> Optional[Dict]:
        """Validate extraction results với AI"""
        try:
            validation_prompt = f"""
            Analyze this Vietnamese message and validate the extracted financial data:
            
            Original message: "{original_message}"
            
            Extracted data:
            - Amount: {extracted_data['amount']} VND
            - Type: {extracted_data['transaction_type']}
            - Category: {extracted_data['category']}
            - Description: {extracted_data['description']}
            
            Questions:
            1. Is this a valid financial transaction? (yes/no)
            2. Is the amount reasonable? (yes/no)
            3. Is the category appropriate? (yes/no)
            4. Any corrections needed?
            
            Respond in JSON format:
            {{
                "is_valid": true/false,
                "amount_correct": true/false,
                "category_correct": true/false,
                "suggested_corrections": {{}}
            }}
            """
            
            response = await self.llm.ainvoke([HumanMessage(content=validation_prompt)])
            
            # Parse AI response (simplified validation)
            if "is_valid\": true" in response.content and "amount_correct\": true" in response.content:
                return extracted_data
            else:
                logger.warning(f"AI validation failed for message: {original_message}")
                return None
                
        except Exception as e:
            logger.error(f"AI validation error: {str(e)}")
            # If AI validation fails, return original data với confidence score thấp
            extracted_data['confidence_score'] = 0.5
            return extracted_data

    def get_extraction_confidence(self, message: str, extracted_data: Dict) -> float:
        """Tính confidence score cho extraction"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence based on clear indicators
        message_lower = message.lower()
        
        # Clear amount pattern
        if any(re.search(pattern, message_lower) for pattern in self.money_patterns):
            confidence += 0.2
            
        # Clear spending verb
        if any(verb in message_lower for verb in self.spending_verbs):
            confidence += 0.2
            
        # Clear category keywords
        category = extracted_data.get('category', '')
        if category in self.category_keywords:
            category_keywords = self.category_keywords[ExpenseCategory(category)]
            if any(keyword in message_lower for keyword in category_keywords):
                confidence += 0.1
        
        return min(confidence, 1.0)

    async def extract_multiple_transactions(self, message: str, user_id: str) -> List[Dict[str, Any]]:
        """Trích xuất nhiều giao dịch từ một tin nhắn"""
        transactions = []
        
        # Split message if it contains multiple transactions
        # This is a simplified implementation
        base_transaction = await self.extract_financial_data_from_message(message, user_id)
        if base_transaction:
            transactions.append(base_transaction)
            
        return transactions
