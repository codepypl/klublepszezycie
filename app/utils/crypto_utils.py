"""
Crypto utilities for encrypting/decrypting sensitive data in URLs
Uses AES-128 encryption for email addresses and other sensitive parameters
"""

import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

class CryptoManager:
    """Manager for encryption/decryption operations"""
    
    def __init__(self):
        """Initialize crypto manager with secret key"""
        self.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key-for-development')
        self.salt = os.environ.get('CRYPTO_SALT', 'klub-lepsze-zycie-salt-2024').encode()
        self._fernet = None
        
    def _get_fernet(self):
        """Get or create Fernet instance for encryption"""
        if self._fernet is None:
            # Derive key from secret key and salt using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self.salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.secret_key.encode()))
            self._fernet = Fernet(key)
        return self._fernet
    
    def encrypt_email(self, email):
        """
        Encrypt email address for use in URLs
        
        Args:
            email (str): Email address to encrypt
            
        Returns:
            str: Base64-encoded encrypted email safe for URLs
        """
        try:
            if not email or not isinstance(email, str):
                logger.error(f"Invalid email for encryption: {email}")
                return None
                
            fernet = self._get_fernet()
            encrypted_data = fernet.encrypt(email.encode('utf-8'))
            # Use URL-safe base64 encoding
            encrypted_b64 = base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
            
            logger.debug(f"Successfully encrypted email: {email[:3]}***")
            return encrypted_b64
            
        except Exception as e:
            logger.error(f"Failed to encrypt email: {str(e)}")
            return None
    
    def decrypt_email(self, encrypted_email):
        """
        Decrypt email address from URL parameter
        
        Args:
            encrypted_email (str): Base64-encoded encrypted email
            
        Returns:
            str: Decrypted email address or None if failed
        """
        try:
            if not encrypted_email or not isinstance(encrypted_email, str):
                logger.error(f"Invalid encrypted email: {encrypted_email}")
                return None
                
            fernet = self._get_fernet()
            
            # Decode from URL-safe base64
            encrypted_data = base64.urlsafe_b64decode(encrypted_email.encode('utf-8'))
            
            # Decrypt
            decrypted_data = fernet.decrypt(encrypted_data)
            email = decrypted_data.decode('utf-8')
            
            logger.debug(f"Successfully decrypted email: {email[:3]}***")
            return email
            
        except Exception as e:
            logger.error(f"Failed to decrypt email: {str(e)}")
            return None
    
    def encrypt_data(self, data):
        """
        Encrypt arbitrary data for use in URLs
        
        Args:
            data (str): Data to encrypt
            
        Returns:
            str: Base64-encoded encrypted data safe for URLs
        """
        try:
            if not data or not isinstance(data, str):
                logger.error(f"Invalid data for encryption: {data}")
                return None
                
            fernet = self._get_fernet()
            encrypted_data = fernet.encrypt(data.encode('utf-8'))
            encrypted_b64 = base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
            
            logger.debug("Successfully encrypted data")
            return encrypted_b64
            
        except Exception as e:
            logger.error(f"Failed to encrypt data: {str(e)}")
            return None
    
    def decrypt_data(self, encrypted_data):
        """
        Decrypt arbitrary data from URL parameter
        
        Args:
            encrypted_data (str): Base64-encoded encrypted data
            
        Returns:
            str: Decrypted data or None if failed
        """
        try:
            if not encrypted_data or not isinstance(encrypted_data, str):
                logger.error(f"Invalid encrypted data: {encrypted_data}")
                return None
                
            fernet = self._get_fernet()
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_bytes = fernet.decrypt(encrypted_bytes)
            data = decrypted_bytes.decode('utf-8')
            
            logger.debug("Successfully decrypted data")
            return data
            
        except Exception as e:
            logger.error(f"Failed to decrypt data: {str(e)}")
            return None

# Global instance
crypto_manager = CryptoManager()

def encrypt_email(email):
    """Convenience function to encrypt email"""
    return crypto_manager.encrypt_email(email)

def decrypt_email(encrypted_email):
    """Convenience function to decrypt email"""
    return crypto_manager.decrypt_email(encrypted_email)

def encrypt_data(data):
    """Convenience function to encrypt arbitrary data"""
    return crypto_manager.encrypt_data(data)

def decrypt_data(encrypted_data):
    """Convenience function to decrypt arbitrary data"""
    return crypto_manager.decrypt_data(encrypted_data)

def encrypt_text(text):
    """Convenience function to encrypt text (alias for encrypt_data)"""
    return crypto_manager.encrypt_data(text)

def decrypt_text(encrypted_text):
    """Convenience function to decrypt text (alias for decrypt_data)"""
    return crypto_manager.decrypt_data(encrypted_text)
