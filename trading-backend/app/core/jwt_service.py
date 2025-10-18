"""JWT token service for access and refresh tokens"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from app.core.config import settings


# Token configuration
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Dictionary of claims to encode in the token (e.g., {"sub": user_id, "email": user_email})
        expires_delta: Optional custom expiration time. Defaults to ACCESS_TOKEN_EXPIRE_MINUTES

    Returns:
        Encoded JWT access token string

    Example:
        >>> token = create_access_token({"sub": "user123", "email": "user@example.com"})
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token with longer expiration

    Args:
        data: Dictionary of claims to encode in the token (typically just {"sub": user_id})

    Returns:
        Encoded JWT refresh token string

    Example:
        >>> token = create_refresh_token({"sub": "user123"})
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token

    Args:
        token: JWT token string to verify
        token_type: Expected token type ("access" or "refresh")

    Returns:
        Decoded token payload if valid, None if invalid

    Raises:
        JWTError: If token is invalid, expired, or signature verification fails

    Example:
        >>> payload = verify_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        >>> print(payload)
        {'sub': 'user123', 'email': 'user@example.com', 'exp': 1234567890, ...}
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Verify token type matches expected type
        if payload.get("type") != token_type:
            return None

        return payload

    except JWTError:
        return None


def refresh_access_token(refresh_token: str) -> Optional[str]:
    """
    Generate a new access token using a valid refresh token

    Args:
        refresh_token: Valid JWT refresh token

    Returns:
        New access token string if refresh token is valid, None otherwise

    Example:
        >>> new_access_token = refresh_access_token(refresh_token)
        >>> if new_access_token:
        >>>     print("New access token created")
    """
    payload = verify_token(refresh_token, token_type="refresh")

    if not payload:
        return None

    # Extract user ID from refresh token and create new access token
    user_id = payload.get("sub")
    if not user_id:
        return None

    # Create new access token with minimal claims (more can be added by the endpoint)
    new_access_token = create_access_token({"sub": user_id})
    return new_access_token


def decode_token_without_verification(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode a token without verifying signature (for debugging/inspection only)

    WARNING: Only use this for debugging. Always use verify_token() in production.

    Args:
        token: JWT token string to decode

    Returns:
        Decoded token payload (unverified)

    Example:
        >>> payload = decode_token_without_verification(token)
        >>> print(f"Token expires at: {payload['exp']}")
    """
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except JWTError:
        return None
