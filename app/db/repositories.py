
from typing import List, Optional, Dict, Any
from supabase import Client
from app.db.session import get_db
from app.db.base import (
    prepare_record_for_insert, 
    prepare_record_for_update, 
    handle_supabase_error,
    validate_uuid,
    RecordNotFoundError
)
from app.schemas.mobile_models import (
    MobileUser, MobileTransaction, MobileBudget, 
    MobileCategory, AIConversation
)
import logging

logger = logging.getLogger(__name__)


class MobileUserRepository:
    def __init__(self):
        self.db: Client = get_db()
    
    @handle_supabase_error
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        record = prepare_record_for_insert(user_data)
        result = self.db.table('users').insert(record).execute()
        if not result.data:
            raise RecordNotFoundError("Failed to create user")
        return result.data[0]
    
    @handle_supabase_error
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        user_id = validate_uuid(user_id)
        result = self.db.table('users').select('*').eq('id', user_id).execute()
        return result.data[0] if result.data else None
    
    @handle_supabase_error
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        user_id = validate_uuid(user_id)
        record = prepare_record_for_update(user_data)
        result = self.db.table('users').update(record).eq('id', user_id).execute()
        return result.data[0] if result.data else None
    
    @handle_supabase_error
    async def delete_user(self, user_id: str) -> bool:
        user_id = validate_uuid(user_id)
        result = self.db.table('users').delete().eq('id', user_id).execute()
        return len(result.data) > 0

class MobileTransactionRepository:
    def __init__(self):
        self.db: Client = get_db()
    
    @handle_supabase_error
    async def create_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        record = prepare_record_for_insert(transaction_data)
        result = self.db.table('transactions').insert(record).execute()
        if not result.data:
            raise RecordNotFoundError("Failed to create transaction")
        return result.data[0]
    
    @handle_supabase_error
    async def get_user_transactions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        user_id = validate_uuid(user_id)
        result = (self.db.table('transactions')
                 .select('*')
                 .eq('user_id', user_id)
                 .order('created_at', desc=True)
                 .limit(limit)
                 .execute())
        return result.data or []
    
    @handle_supabase_error
    async def update_transaction(self, transaction_id: str, transaction_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        transaction_id = validate_uuid(transaction_id)
        record = prepare_record_for_update(transaction_data)
        result = self.db.table('transactions').update(record).eq('id', transaction_id).execute()
        return result.data[0] if result.data else None
    
    @handle_supabase_error
    async def delete_transaction(self, transaction_id: str) -> bool:
        transaction_id = validate_uuid(transaction_id)
        result = self.db.table('transactions').delete().eq('id', transaction_id).execute()
        return len(result.data) > 0

class AIConversationRepository:
    def __init__(self):
        self.db: Client = get_db()
    
    @handle_supabase_error
    async def create_conversation(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        record = prepare_record_for_insert(conversation_data)
        result = self.db.table('ai_conversations').insert(record).execute()
        if not result.data:
            raise RecordNotFoundError("Failed to create conversation")
        return result.data[0]
    
    @handle_supabase_error
    async def get_user_conversations(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        user_id = validate_uuid(user_id)
        result = (self.db.table('ai_conversations')
                 .select('*')
                 .eq('user_id', user_id)
                 .order('created_at', desc=True)
                 .limit(limit)
                 .execute())
        return result.data or []
    
    @handle_supabase_error
    async def update_conversation(self, conversation_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        conversation_id = validate_uuid(conversation_id)
        record = prepare_record_for_update(updates)
        result = self.db.table('ai_conversations').update(record).eq('id', conversation_id).execute()
        return result.data[0] if result.data else None


# Add missing repositories for production completeness
class MobileBudgetRepository:
    def __init__(self):
        self.db: Client = get_db()
    
    @handle_supabase_error
    async def create_budget(self, budget_data: Dict[str, Any]) -> Dict[str, Any]:
        record = prepare_record_for_insert(budget_data)
        result = self.db.table('budgets').insert(record).execute()
        if not result.data:
            raise RecordNotFoundError("Failed to create budget")
        return result.data[0]
    
    @handle_supabase_error
    async def get_user_budgets(self, user_id: str) -> List[Dict[str, Any]]:
        user_id = validate_uuid(user_id)
        result = (self.db.table('budgets')
                 .select('*')
                 .eq('user_id', user_id)
                 .execute())
        return result.data or []
    
    @handle_supabase_error
    async def update_budget(self, budget_id: str, budget_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        budget_id = validate_uuid(budget_id)
        record = prepare_record_for_update(budget_data)
        result = self.db.table('budgets').update(record).eq('id', budget_id).execute()
        return result.data[0] if result.data else None


class MobileCategoryRepository:
    def __init__(self):
        self.db: Client = get_db()
    
    @handle_supabase_error
    async def create_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        record = prepare_record_for_insert(category_data)
        result = self.db.table('categories').insert(record).execute()
        if not result.data:
            raise RecordNotFoundError("Failed to create category")
        return result.data[0]
    
    @handle_supabase_error
    async def get_user_categories(self, user_id: str) -> List[Dict[str, Any]]:
        user_id = validate_uuid(user_id)
        result = (self.db.table('categories')
                 .select('*')
                 .eq('user_id', user_id)
                 .execute())
        return result.data or []
    
    @handle_supabase_error
    async def get_all_categories(self) -> List[Dict[str, Any]]:
        result = self.db.table('categories').select('*').execute()
        return result.data or []
