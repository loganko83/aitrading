"""TOTP (Time-based One-Time Password) service for 2FA authentication"""

import pyotp
import qrcode
from io import BytesIO
import base64
from typing import Optional
from cryptography.fernet import Fernet
from app.core.config import settings

# Encryption cipher for TOTP secrets
cipher = Fernet(settings.ENCRYPTION_KEY.encode())

def generate_totp_secret() -> str:
    """
    Generate a new TOTP secret key

    Returns:
        Base32-encoded TOTP secret string

    Example:
        >>> secret = generate_totp_secret()
        >>> print(secret)
        JBSWY3DPEHPK3PXP
    """
    return pyotp.random_base32()

def encrypt_totp_secret(secret: str) -> str:
    """
    Encrypt TOTP secret for secure database storage

    Args:
        secret: Plain text TOTP secret

    Returns:
        Encrypted TOTP secret (Fernet encrypted, base64 encoded)

    Example:
        >>> encrypted = encrypt_totp_secret("JBSWY3DPEHPK3PXP")
        >>> print(encrypted)
        gAAAAABh3xY2...
    """
    return cipher.encrypt(secret.encode()).decode()

def decrypt_totp_secret(encrypted_secret: str) -> str:
    """
    Decrypt TOTP secret from database

    Args:
        encrypted_secret: Encrypted TOTP secret from database

    Returns:
        Decrypted plain text TOTP secret

    Example:
        >>> secret = decrypt_totp_secret("gAAAAABh3xY2...")
        >>> print(secret)
        JBSWY3DPEHPK3PXP
    """
    return cipher.decrypt(encrypted_secret.encode()).decode()

def generate_qr_code_uri(user_email: str, totp_secret: str, issuer_name: str = "TradingBot AI") -> str:
    """
    Generate provisioning URI for TOTP (used in QR codes)

    Args:
        user_email: User's email address (shown in authenticator app)
        totp_secret: TOTP secret key
        issuer_name: Application name (shown in authenticator app)

    Returns:
        TOTP provisioning URI

    Example:
        >>> uri = generate_qr_code_uri("user@example.com", "JBSWY3DPEHPK3PXP")
        >>> print(uri)
        otpauth://totp/TradingBot%20AI:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=TradingBot%20AI
    """
    totp = pyotp.TOTP(totp_secret)
    return totp.provisioning_uri(name=user_email, issuer_name=issuer_name)

def generate_qr_code_base64(user_email: str, totp_secret: str, issuer_name: str = "TradingBot AI") -> str:
    """
    Generate QR code image as base64 string for 2FA setup

    Args:
        user_email: User's email address
        totp_secret: TOTP secret key
        issuer_name: Application name

    Returns:
        Base64-encoded QR code image (PNG)

    Example:
        >>> qr_base64 = generate_qr_code_base64("user@example.com", "JBSWY3DPEHPK3PXP")
        >>> # Use in HTML: <img src="data:image/png;base64,{qr_base64}" />
    """
    # Generate provisioning URI
    uri = generate_qr_code_uri(user_email, totp_secret, issuer_name)

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return img_str

def verify_totp_token(totp_secret: str, token: str, valid_window: int = 1) -> bool:
    """
    Verify a TOTP token against the secret

    Args:
        totp_secret: TOTP secret key (decrypted)
        token: 6-digit TOTP code from user's authenticator app
        valid_window: Number of time windows to check (1 = ±30 seconds tolerance)

    Returns:
        True if token is valid, False otherwise

    Example:
        >>> is_valid = verify_totp_token("JBSWY3DPEHPK3PXP", "123456")
        >>> if is_valid:
        >>>     print("2FA verification successful")
        >>> else:
        >>>     print("Invalid 2FA code")
    """
    totp = pyotp.TOTP(totp_secret)
    return totp.verify(token, valid_window=valid_window)

def get_current_totp_token(totp_secret: str) -> str:
    """
    Get the current TOTP token (for testing/debugging only)

    WARNING: This should only be used in development/testing environments.
    In production, users generate tokens from their authenticator apps.

    Args:
        totp_secret: TOTP secret key

    Returns:
        Current 6-digit TOTP code

    Example:
        >>> token = get_current_totp_token("JBSWY3DPEHPK3PXP")
        >>> print(f"Current TOTP: {token}")
        Current TOTP: 123456
    """
    totp = pyotp.TOTP(totp_secret)
    return totp.now()

# Complete 2FA Setup Workflow
def setup_2fa_for_user(user_email: str) -> dict:
    """
    Complete 2FA setup workflow for a user

    This is a convenience function that combines all steps needed to enable 2FA.

    Args:
        user_email: User's email address

    Returns:
        Dictionary containing:
        - secret: Plain text TOTP secret (to be encrypted before storing)
        - encrypted_secret: Encrypted TOTP secret (store this in database)
        - qr_code_base64: Base64-encoded QR code image
        - provisioning_uri: TOTP URI (alternative to QR code)

    Example:
        >>> setup_data = setup_2fa_for_user("user@example.com")
        >>> # Store setup_data['encrypted_secret'] in user.totp_secret
        >>> # Return setup_data['qr_code_base64'] to frontend
        >>> # User scans QR code with authenticator app
        >>> # User submits TOTP code to verify setup
    """
    # Generate new TOTP secret
    secret = generate_totp_secret()

    # Encrypt secret for database storage
    encrypted_secret = encrypt_totp_secret(secret)

    # Generate QR code
    qr_code_base64 = generate_qr_code_base64(user_email, secret)

    # Generate provisioning URI (alternative to QR code)
    provisioning_uri = generate_qr_code_uri(user_email, secret)

    return {
        "secret": secret,  # Plain text (don't store this, only for immediate verification)
        "encrypted_secret": encrypted_secret,  # Store this in database
        "qr_code_base64": qr_code_base64,  # Return to frontend for display
        "provisioning_uri": provisioning_uri  # Optional: for manual entry
    }

def verify_2fa_setup(encrypted_secret: str, verification_token: str) -> bool:
    """
    Verify that user successfully scanned QR code and can generate valid TOTP codes

    This should be called during 2FA setup to confirm the user's authenticator app is working.

    Args:
        encrypted_secret: Encrypted TOTP secret from database
        verification_token: 6-digit TOTP code from user's authenticator app

    Returns:
        True if verification successful, False otherwise

    Example:
        >>> # After user scans QR code and enters TOTP code
        >>> success = verify_2fa_setup(user.totp_secret, "123456")
        >>> if success:
        >>>     user.is_2fa_enabled = True
        >>>     # Save user to database
    """
    try:
        # Decrypt secret
        secret = decrypt_totp_secret(encrypted_secret)

        # Verify token with wider window during setup (2 = ±1 minute tolerance)
        return verify_totp_token(secret, verification_token, valid_window=2)
    except Exception:
        return False

def verify_2fa_login(encrypted_secret: str, login_token: str) -> bool:
    """
    Verify TOTP code during login

    This should be called during login after password verification succeeds.

    Args:
        encrypted_secret: Encrypted TOTP secret from database
        login_token: 6-digit TOTP code from user's authenticator app

    Returns:
        True if login verification successful, False otherwise

    Example:
        >>> # After successful password verification
        >>> if user.is_2fa_enabled:
        >>>     totp_valid = verify_2fa_login(user.totp_secret, "123456")
        >>>     if not totp_valid:
        >>>         raise HTTPException(status_code=401, detail="Invalid 2FA code")
    """
    try:
        # Decrypt secret
        secret = decrypt_totp_secret(encrypted_secret)

        # Verify token with standard window (1 = ±30 seconds tolerance)
        return verify_totp_token(secret, login_token, valid_window=1)
    except Exception:
        return False
