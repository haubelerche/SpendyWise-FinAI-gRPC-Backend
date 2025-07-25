
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from supabase import Client
from app.db.supabase_client import get_supabase_client, get_supabase_admin_client, health_check
import logging

logger = logging.getLogger(__name__)

def get_db() -> Client:
    """Get standard Supabase client"""
    return get_supabase_client()

def get_admin_db() -> Client:
    """Get admin Supabase client"""
    return get_supabase_admin_client()

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[Client, None]:
    """Get database session with automatic cleanup"""
    client = get_db()
    try:
        yield client
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise
    finally:
        # Supabase handles connection cleanup automatically
        pass

def check_db_health() -> bool:
    """Check database connection health"""
    return health_check()

class DatabaseManager:
    """Database connection manager for production use"""
    
    def __init__(self):
        self._client = None
        self._admin_client = None
    
    def get_client(self) -> Client:
        if self._client is None:
            self._client = get_db()
        return self._client
    
    def get_admin_client(self) -> Client:
        if self._admin_client is None:
            self._admin_client = get_admin_db()
        return self._admin_client
    
    def reset(self):
        """Reset connections"""
        self._client = None
        self._admin_client = None

# Global instance
db_manager = DatabaseManager()
