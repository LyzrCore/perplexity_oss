"""Authentication middleware for API compatibility layer."""

import os
from fastapi import Header, HTTPException, status


async def verify_api_key(authorization: str = Header(None)):
    """
    Verify Bearer token from Authorization header.

    Args:
        authorization: Authorization header value (should be "Bearer <token>")

    Returns:
        The validated token string

    Raises:
        HTTPException: If authentication fails
    """
    # Check if header is present
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if it's a Bearer token
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format. Use: Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token
    token = authorization.replace("Bearer ", "").strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get valid API keys from environment
    api_keys_str = os.getenv("API_KEYS", "")

    if not api_keys_str:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API keys not configured on server",
        )

    # Support comma-separated list of API keys
    valid_keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]

    # Verify token
    if token not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token
