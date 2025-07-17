# Authentication dependencies
import os
import grpc
from typing import Optional, Dict, Any, Callable
from functools import wraps
from datetime import datetime, timedelta
from supabase import create_client, Client
from jose import JWTError, jwt as jose_jwt
import logging

from app.core.settings import get_settings
from app.core.exceptions import AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)
settings = get_settings()


class SupabaseAuth:
    """Supabase authentication handler for gRPC services"""
    
    def __init__(self):
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        self.jwt_secret = settings.SUPABASE_KEY
        self.algorithm = settings.ALGORITHM
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify Supabase JWT token and extract user information
        
        Args:
            token: JWT token from client
            
        Returns:
            Dict containing user information
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Decode the JWT token
            payload = jose_jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.algorithm],
                options={"verify_aud": False}  # Supabase doesn't use standard aud claim
            )
            
            # Extract user information
            user_id = payload.get('sub')
            email = payload.get('email')
            role = payload.get('role', 'authenticated')
            
            if not user_id:
                raise AuthenticationError("Invalid token: missing user ID")
                
            # Check if token is expired
            exp = payload.get('exp')
            if exp and datetime.now().timestamp() > exp:
                raise AuthenticationError("Token has expired")
            
            return {
                'user_id': user_id,
                'email': email,
                'role': role,
                'raw_payload': payload
            }
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {str(e)}")
            raise AuthenticationError("Invalid or expired token")
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {str(e)}")
            raise AuthenticationError("Authentication failed")
    
    def get_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get full user information from Supabase using token
        
        Args:
            token: JWT token from client
            
        Returns:
            User data from Supabase or None if not found
        """
        try:
            user_info = self.verify_token(token)
            
            # Get additional user data from Supabase
            response = self.supabase.auth.get_user(token)
            
            if response.user:
                return {
                    'id': response.user.id,
                    'email': response.user.email,
                    'phone': response.user.phone,
                    'created_at': response.user.created_at,
                    'updated_at': response.user.updated_at,
                    'email_confirmed_at': response.user.email_confirmed_at,
                    'phone_confirmed_at': response.user.phone_confirmed_at,
                    'last_sign_in_at': response.user.last_sign_in_at,
                    'app_metadata': response.user.app_metadata,
                    'user_metadata': response.user.user_metadata,
                    'role': user_info.get('role', 'authenticated')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user from token: {str(e)}")
            return None
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Refresh token from client
            
        Returns:
            New access and refresh tokens or None if failed
        """
        try:
            response = self.supabase.auth.refresh_session(refresh_token)
            
            if response.session:
                return {
                    'access_token': response.session.access_token,
                    'refresh_token': response.session.refresh_token,
                    'expires_at': response.session.expires_at,
                    'token_type': response.session.token_type
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to refresh token: {str(e)}")
            return None


# Global auth instance
_auth_instance: Optional[SupabaseAuth] = None


def get_auth() -> SupabaseAuth:
    """Get or create authentication instance"""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = SupabaseAuth()
    return _auth_instance


def extract_token_from_metadata(context: grpc.ServicerContext) -> Optional[str]:
    """
    Extract JWT token from gRPC metadata
    
    Args:
        context: gRPC service context
        
    Returns:
        JWT token or None if not found
    """
    metadata = dict(context.invocation_metadata())
    
    # Try different header names
    token = (
        metadata.get('authorization') or
        metadata.get('Authorization') or
        metadata.get('bearer') or
        metadata.get('Bearer') or
        metadata.get('x-access-token') or
        metadata.get('X-Access-Token')
    )
    
    if token and token.startswith('Bearer '):
        return token[7:]  # Remove 'Bearer ' prefix
    
    return token


def require_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication for gRPC service methods
    
    Usage:
        @require_auth
        def CreateTransaction(self, request, context):
            user = context.user  # Access authenticated user
            # ... service logic
    """
    @wraps(func)
    def wrapper(self, request, context: grpc.ServicerContext):
        try:
            # Extract token from metadata
            token = extract_token_from_metadata(context)
            
            if not token:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Missing authentication token")
                return
            
            # Verify token and get user info
            auth = get_auth()
            user_info = auth.verify_token(token)
            
            # Add user info to context for use in service method
            context.user = user_info
            context.user_id = user_info['user_id']
            context.user_email = user_info['email']
            context.user_role = user_info['role']
            
            # Call the original service method
            return func(self, request, context)
            
        except AuthenticationError as e:
            logger.warning(f"Authentication failed: {str(e)}")
            context.abort(grpc.StatusCode.UNAUTHENTICATED, str(e))
        except Exception as e:
            logger.error(f"Unexpected error in auth decorator: {str(e)}")
            context.abort(grpc.StatusCode.INTERNAL, "Authentication service unavailable")
    
    return wrapper


def require_role(required_role: str) -> Callable:
    """
    Decorator to require specific role for gRPC service methods
    
    Args:
        required_role: Required user role (e.g., 'admin', 'premium_user')
    
    Usage:
        @require_role('admin')
        def DeleteUser(self, request, context):
            # Only admin users can access this method
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, request, context: grpc.ServicerContext):
            try:
                # First check authentication
                token = extract_token_from_metadata(context)
                
                if not token:
                    context.abort(grpc.StatusCode.UNAUTHENTICATED, "Missing authentication token")
                    return
                
                # Verify token and get user info
                auth = get_auth()
                user_info = auth.verify_token(token)
                
                # Check role
                user_role = user_info.get('role', 'authenticated')
                if user_role != required_role and user_role != 'admin':  # Admin can access everything
                    context.abort(
                        grpc.StatusCode.PERMISSION_DENIED,
                        f"Insufficient permissions. Required role: {required_role}"
                    )
                    return
                
                # Add user info to context
                context.user = user_info
                context.user_id = user_info['user_id']
                context.user_email = user_info['email']
                context.user_role = user_role
                
                # Call the original service method
                return func(self, request, context)
                
            except AuthenticationError as e:
                logger.warning(f"Authentication failed: {str(e)}")
                context.abort(grpc.StatusCode.UNAUTHENTICATED, str(e))
            except Exception as e:
                logger.error(f"Unexpected error in role decorator: {str(e)}")
                context.abort(grpc.StatusCode.INTERNAL, "Authorization service unavailable")
        
        return wrapper
    return decorator


def optional_auth(func: Callable) -> Callable:
    """
    Decorator for methods that can work with or without authentication
    If token is provided, user info will be available in context
    If no token, context.user will be None
    
    Usage:
        @optional_auth
        def GetPublicData(self, request, context):
            if hasattr(context, 'user') and context.user:
                # Provide personalized data
            else:
                # Provide public data
    """
    @wraps(func)
    def wrapper(self, request, context: grpc.ServicerContext):
        try:
            # Try to extract token
            token = extract_token_from_metadata(context)
            
            if token:
                try:
                    # Verify token and add user info to context
                    auth = get_auth()
                    user_info = auth.verify_token(token)
                    
                    context.user = user_info
                    context.user_id = user_info['user_id']
                    context.user_email = user_info['email']
                    context.user_role = user_info['role']
                    
                except AuthenticationError:
                    # Invalid token, but that's okay for optional auth
                    context.user = None
            else:
                context.user = None
            
            # Call the original service method
            return func(self, request, context)
            
        except Exception as e:
            logger.error(f"Unexpected error in optional auth decorator: {str(e)}")
            # For optional auth, we don't abort on errors, just set user to None
            context.user = None
            return func(self, request, context)
    
    return wrapper


# Helper functions for service methods
def get_current_user_id(context: grpc.ServicerContext) -> str:
    """Get current user ID from context (must be used with @require_auth)"""
    if not hasattr(context, 'user_id'):
        raise AuthenticationError("No authenticated user in context")
    return context.user_id


def get_current_user(context: grpc.ServicerContext) -> Dict[str, Any]:
    """Get current user info from context (must be used with @require_auth)"""
    if not hasattr(context, 'user'):
        raise AuthenticationError("No authenticated user in context")
    return context.user


def is_admin(context: grpc.ServicerContext) -> bool:
    """Check if current user is admin"""
    if not hasattr(context, 'user_role'):
        return False
    return context.user_role == 'admin'


def can_access_resource(context: grpc.ServicerContext, resource_user_id: str) -> bool:
    """
    Check if current user can access a resource
    Users can access their own resources, admins can access everything
    """
    if not hasattr(context, 'user_id'):
        return False
    
    current_user_id = context.user_id
    user_role = getattr(context, 'user_role', 'authenticated')
    
    # Admin can access everything
    if user_role == 'admin':
        return True
    
    # Users can access their own resources
    return current_user_id == resource_user_id
