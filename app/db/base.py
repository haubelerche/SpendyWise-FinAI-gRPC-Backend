"""
Database base utilities for Supabase
"""
from typing import Dict, Any, Optional, Union
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Base database error"""
    pass

class RecordNotFoundError(DatabaseError):
    """Record not found in database"""
    pass

class ValidationError(DatabaseError):
    """Data validation error"""
    pass

def generate_uuid() -> str:
    """Generate a new UUID for database records"""
    return str(uuid.uuid4())

def validate_uuid(value: Union[str, uuid.UUID]) -> str:
    """Validate and convert UUID"""
    if isinstance(value, uuid.UUID):
        return str(value)
    try:
        uuid.UUID(value)
        return value
    except ValueError:
        raise ValidationError(f"Invalid UUID format: {value}")

def prepare_record_for_insert(data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a record for insertion into Supabase"""
    if not isinstance(data, dict):
        raise ValidationError("Data must be a dictionary")
    
    record = data.copy()
    if 'id' not in record:
        record['id'] = generate_uuid()
    if 'created_at' not in record:
        record['created_at'] = datetime.now(timezone.utc).isoformat()
    if 'updated_at' not in record:
        record['updated_at'] = datetime.now(timezone.utc).isoformat()
    return record

def prepare_record_for_update(data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a record for update in Supabase"""
    if not isinstance(data, dict):
        raise ValidationError("Data must be a dictionary")
    
    record = data.copy()
    record['updated_at'] = datetime.now(timezone.utc).isoformat()
    # Remove id from updates to prevent conflicts
    record.pop('id', None)
    record.pop('created_at', None)
    return record

def handle_supabase_error(func):
    """Decorator to handle Supabase errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database error in {func.__name__}: {e}")
            if "duplicate key" in str(e).lower():
                raise DatabaseError(f"Record already exists: {e}")
            elif "not found" in str(e).lower():
                raise RecordNotFoundError(f"Record not found: {e}")
            else:
                raise DatabaseError(f"Database operation failed: {e}")
    return wrapper
