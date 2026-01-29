"""
Encryption utilities for sensitive credentials.
Uses Fernet symmetric encryption from the cryptography library.
"""
from cryptography.fernet import Fernet
import os

# Get encryption key from environment variable
CREDENTIALS_ENCRYPTION_KEY = os.getenv("CREDENTIALS_ENCRYPTION_KEY")

if not CREDENTIALS_ENCRYPTION_KEY:
    raise ValueError(
        "CREDENTIALS_ENCRYPTION_KEY environment variable must be set. "
        "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    )

cipher = Fernet(CREDENTIALS_ENCRYPTION_KEY.encode())


def encrypt_credential(plaintext: str) -> str:
    """
    Encrypt a plaintext string.

    Args:
        plaintext: The string to encrypt

    Returns:
        Base64-encoded encrypted string
    """
    if not plaintext:
        return ""
    return cipher.encrypt(plaintext.encode()).decode()


def decrypt_credential(ciphertext: str) -> str:
    """
    Decrypt an encrypted string.

    Args:
        ciphertext: Base64-encoded encrypted string

    Returns:
        Decrypted plaintext string
    """
    if not ciphertext:
        return ""
    return cipher.decrypt(ciphertext.encode()).decode()
