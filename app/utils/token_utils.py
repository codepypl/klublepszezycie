"""
Token utilities for generating and verifying unsubscribe tokens
"""
import os
import hmac
import hashlib
import time
from app.utils.crypto_utils import encrypt_email

def generate_unsubscribe_token(email, action):
    """Generate unsubscribe token for email with expiration"""
    try:
        secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')
        
        # Generate token with current timestamp (30 days from now)
        current_time = int(time.time())
        expiration_timestamp = current_time + (30 * 24 * 60 * 60)  # 30 days from now
        
        # Create message with email, action, and expiration timestamp
        message = f"{email}:{action}:{expiration_timestamp}"
        
        # Generate HMAC-SHA256 token
        token = hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        print(f"🔑 Generated token for {email}:{action} - expires in 30 days")
        print(f"   Token: {token}")
        print(f"   Generated at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))}")
        print(f"   Expires at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expiration_timestamp))}")
        return token
    except Exception as e:
        print(f"❌ Error generating token: {e}")
        return None

def verify_unsubscribe_token(email, action, token):
    """Verify unsubscribe token with proper expiration check"""
    try:
        secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')
        current_time = int(time.time())
        
        # Try to verify token for different expiration times (up to 30 days)
        for days_back in range(30):
            expiration_timestamp = current_time + (days_back * 24 * 60 * 60)
            message = f"{email}:{action}:{expiration_timestamp}"
            
            expected_token = hmac.new(
                secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if hmac.compare_digest(token, expected_token):
                # Check if token is still valid (not expired)
                if expiration_timestamp > current_time:
                    print(f"✅ Token verified for {email}:{action} - valid until {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expiration_timestamp))}")
                    return True
                else:
                    print(f"❌ Token expired for {email}:{action}")
                    return False
        
        print(f"❌ Invalid token for {email}:{action}")
        return False
        
    except Exception as e:
        print(f"❌ Error verifying token: {e}")
        return False
