# Authentication dependencies
import os
import jwt
import httpx
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timezone
import asyncio
from functools import lru_cache

# Get Supabase configuration from environment
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://zeywyexydsncslgodffz.supabase.co")
SUPABASE_PROJECT_ID = SUPABASE_URL.split("//")[1].split(".")[0]  # Extract project ID
SUPABASE_JWKS_URL = f"{SUPABASE_URL}/auth/v1/keys"

# Security scheme
security = HTTPBearer()

# Cache for public keys (refresh every hour)
_jwks_cache = {"keys": None, "expires": 0}


async def get_supabase_public_keys() -> list:
    """Fetch Supabase public keys with caching"""
    current_time = datetime.now(timezone.utc).timestamp()

    # Check if cache is still valid (1 hour)
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
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to fetch authentication keys"
        )


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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: Key not found"
            )

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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    payload = await verify_supabase_jwt(token)

    # Extract user information
    user_info = {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role", "authenticated"),
        "aud": payload.get("aud"),
        "exp": payload.get("exp"),
        "iat": payload.get("iat"),
        "iss": payload.get("iss"),
        "user_metadata": payload.get("user_metadata", {}),
        "app_metadata": payload.get("app_metadata", {})
    }

    return user_info


async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[
    Dict[str, Any]]:
    """Optional authentication - returns None if no token provided"""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


# For role-based access
def require_role(required_role: str):
    """Decorator for role-based access control"""

    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_role = current_user.get("role", "authenticated")
        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        return current_user

    return role_checker


# Admin role dependency
get_admin_user = require_role("service_role")