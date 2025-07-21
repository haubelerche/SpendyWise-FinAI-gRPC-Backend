# Authentication dependencies
import os
import jwt
import httpx
import grpc
from typing import Optional, Dict, Any

from datetime import datetime, timezone
import asyncio
from functools import lru_cache

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://zeywyexydsncslgodffz.supabase.co")
SUPABASE_PROJECT_ID = SUPABASE_URL.split("//")[1].split(".")[0]  # Extract project ID
SUPABASE_JWKS_URL = f"{SUPABASE_URL}/auth/v1/keys"

# Cache public keys(refresh every hour)
_jwks_cache = {"keys": None, "expires": 0}


async def get_supabase_public_keys() -> list:
    """Fetch Supabase public keys with caching"""
    current_time = datetime.now(timezone.utc).timestamp()

    # Check if cache is still valid(1 hour)
    if _jwks_cache["keys"] and current_time < _jwks_cache["expires"]:
        return _jwks_cache["keys"]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(SUPABASE_JWKS_URL, timeout=10.0)
            response.raise_for_status()
            jwks_data = response.json()

            # Update cache
            _jwks_cache["keys"] = jwks_data.get("keys", [])
            _jwks_cache["expires"] = current_time + 3600  # Cache for 1 hour

            return _jwks_cache["keys"]
    except Exception as e:
        # If we have cached keys and fetch fails, use cached keys
        if _jwks_cache["keys"]:
            return _jwks_cache["keys"]
        raise Exception(f"Unable to fetch authentication keys: {str(e)}")


async def verify_supabase_jwt(token: str) -> Dict[str, Any]:
    """Verify Supabase JWT token and return payload"""
    try:
        # Get the header to find the key ID
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # Get public keys
        keys = await get_supabase_public_keys()

        # Find the right key
        public_key = None
        for key in keys:
            if key.get("kid") == kid:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                break

        if not public_key:
            raise Exception("Invalid token: Key not found")

        # Verify and decode the token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience="authenticated",  # Supabase audience
            issuer=SUPABASE_URL  # Supabase issuer
        )

        # Check if token is expired
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise Exception("Token has expired")

        return payload

    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError as e:
        raise Exception(f"Invalid token: {str(e)}")
    except Exception as e:
        raise Exception(f"Authentication failed: {str(e)}")


async def get_user_from_grpc_context(context) -> Dict[str, Any]:
    """Extract and verify user from gRPC metadata"""
    metadata = dict(context.invocation_metadata())
    auth_header = metadata.get("authorization", "")
    
    if not auth_header:
        raise grpc.RpcError(grpc.StatusCode.UNAUTHENTICATED, "Missing authorization header")
    
    if not auth_header.startswith("Bearer "):
        raise grpc.RpcError(grpc.StatusCode.UNAUTHENTICATED, "Invalid authorization format")
    
    token = auth_header.replace("Bearer ", "")
    
    try:
        payload = await verify_supabase_jwt(token)
        
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "authenticated"),
            "user_metadata": payload.get("user_metadata", {}),
            "app_metadata": payload.get("app_metadata", {}),
            "aud": payload.get("aud"),
            "exp": payload.get("exp"),
            "iat": payload.get("iat")
        }
    except Exception as e:
        raise grpc.RpcError(grpc.StatusCode.UNAUTHENTICATED, str(e))


def require_auth(func):
    """Decorator for gRPC methods that require authentication"""
    async def wrapper(self, request, context):
        try:
            current_user = await get_user_from_grpc_context(context)
            # Add user to context for use in the method
            context.user = current_user
            return await func(self, request, context)
        except grpc.RpcError:
            raise  # Re-raise gRPC errors
        except Exception as e:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details(f"Authentication failed: {str(e)}")
            return None
    return wrapper


def optional_auth(func):
    """Decorator for gRPC methods with optional authentication"""
    async def wrapper(self, request, context):
        try:
            current_user = await get_user_from_grpc_context(context)
            context.user = current_user
        except:
            context.user = None  # No user if auth fails
        
        return await func(self, request, context)
    return wrapper


def require_role(required_role: str):
    """Decorator for role-based access control"""
    def decorator(func):
        async def wrapper(self, request, context):
            try:
                current_user = await get_user_from_grpc_context(context)
                user_role = current_user.get("role", "authenticated")
                
                if user_role != required_role:
                    context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                    context.set_details(f"Insufficient permissions. Required role: {required_role}")
                    return None
                
                context.user = current_user
                return await func(self, request, context)
            except grpc.RpcError:
                raise
            except Exception as e:
                context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                context.set_details(f"Authentication failed: {str(e)}")
                return None
        return wrapper
    return decorator


def require_user_id(func):
    """Decorator to ensure user_id is available in context"""
    async def wrapper(self, request, context):
        current_user = await get_user_from_grpc_context(context)
        user_id = current_user.get("user_id")
        
        if not user_id:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details("User ID not found in token")
            return None
        
        # Add user info to context
        context.user = current_user
        context.user_id = user_id
        
        return await func(self, request, context)
    return wrapper


# Convenience decorators
require_admin = require_role("service_role")
require_authenticated = require_auth