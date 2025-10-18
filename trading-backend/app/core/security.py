"""Security utilities for password hashing and verification"""

from passlib.context import CryptContext

# Configure bcrypt password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string

    Example:
        >>> hashed = hash_password("mySecurePassword123")
        >>> print(hashed)
        $2b$12$KIX...
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise

    Example:
        >>> hashed = hash_password("myPassword")
        >>> verify_password("myPassword", hashed)
        True
        >>> verify_password("wrongPassword", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)
