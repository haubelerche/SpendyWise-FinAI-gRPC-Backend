from supabase import create_client, Client
from app.core.settings import get_settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

_supabase_client: Optional[Client] = None
_supabase_admin_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """Get or create Supabase client instance with connection reuse"""
    global _supabase_client
    if _supabase_client is None:
        try:
            _supabase_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    return _supabase_client

def get_supabase_admin_client() -> Client:
    """Get Supabase client with service role key for admin operations"""
    global _supabase_admin_client
    if _supabase_admin_client is None:
        try:
            _supabase_admin_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY
            )
            logger.info("Supabase admin client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase admin client: {e}")
            raise
    return _supabase_admin_client

def health_check() -> bool:
    """Check if Supabase connection is healthy"""
    try:
        client = get_supabase_client()
        # Simple query to test connection
        result = client.table('user').select('user_id').limit(1).execute()
        return True
    except Exception as e:
        logger.error(f"Supabase health check failed: {e}")
        return False

def reset_connections():
    """Reset connection instances (useful for testing)"""
    global _supabase_client, _supabase_admin_client
    _supabase_client = None
    _supabase_admin_client = None
