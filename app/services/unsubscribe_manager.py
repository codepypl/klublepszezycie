"""
Nowy system zarządzania wypisywaniem z klubu i usuwaniem konta
Tokeny zawierają zaszyfrowany email i mają określoną ważność
"""
import hmac
import hashlib
import secrets
import base64
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from app import db
from app.models.user_model import User

class UnsubscribeManager:
    """Nowy manager dla unsubscribe i delete account z tokenami zawierającymi email"""
    
    def __init__(self):
        self.secret_key = 'klublepszezycie_unsubscribe_v2_2024'  # Fixed secret key
        self.token_expiry_days = 30
        self.base_url = os.getenv('BASE_URL', 'https://klublepszezycie.pl')
        
        # Ensure URL has protocol
        if self.base_url and not self.base_url.startswith(('http://', 'https://')):
            self.base_url = f'http://{self.base_url}'
    
    def generate_token(self, email: str, action: str) -> str:
        """
        Generuje KRÓTKI token używając ID użytkownika
        Format: {user_id}.{expires_timestamp}.{hmac_signature}
        """
        try:
            # Znajdź użytkownika
            user = User.query.filter_by(email=email).first()
            if not user:
                print(f"❌ User not found: {email}")
                return None
            
            # Utwórz krótki payload
            expires_at = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now() + timedelta(days=self.token_expiry_days)
            expires_timestamp = int(expires_at.timestamp())
            
            # Payload to tylko: user_id.expires_timestamp.action
            payload = f"{user.id}.{expires_timestamp}.{action}"
            
            # Wygeneruj HMAC signature (tylko pierwsze 16 znaków dla krótkości)
            signature = hmac.new(
                self.secret_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()[:16]
            
            # Token format: user_id.expires_timestamp.action.signature
            token = f"{user.id}.{expires_timestamp}.{action}.{signature}"
            
            print(f"🔑 Generated SHORT {action} token for {email}")
            print(f"   Expires: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Token: {token} (length: {len(token)})")
            
            return token
            
        except Exception as e:
            print(f"❌ Error generating token: {e}")
            return None
    
    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Weryfikuje KRÓTKI token i zwraca dane użytkownika
        Format: {user_id}.{expires_timestamp}.{action}.{hmac_signature}
        Returns: (is_valid, user_data)
        """
        try:
            # Podziel token na części
            parts = token.split('.')
            if len(parts) != 4:
                print(f"❌ Invalid token format: {len(parts)} parts (expected 4)")
                return False, None
            
            user_id_str, expires_timestamp_str, action, signature = parts
            
            # Konwertuj ID i timestamp
            try:
                user_id = int(user_id_str)
                expires_timestamp = int(expires_timestamp_str)
            except ValueError:
                print(f"❌ Invalid token: non-numeric user_id or timestamp")
                return False, None
            
            # Sprawdź czy token nie wygasł
            from app.utils.timezone_utils import get_local_now
            expires_at = datetime.fromtimestamp(expires_timestamp)
            now = get_local_now().replace(tzinfo=None)  # Remove timezone for comparison
            if now > expires_at:
                print(f"❌ Token expired at {expires_at}")
                return False, None
            
            # Weryfikuj HMAC signature
            payload = f"{user_id}.{expires_timestamp}.{action}"
            expected_signature = hmac.new(
                self.secret_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()[:16]
            
            if not hmac.compare_digest(signature, expected_signature):
                print(f"❌ Invalid token signature")
                return False, None
            
            # Znajdź użytkownika
            user = User.query.get(user_id)
            if not user:
                print(f"❌ User not found: ID {user_id}")
                return False, None
            
            print(f"✅ Valid {action} token for {user.email}")
            print(f"   Expires: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            return True, {
                'user': user,
                'email': user.email,
                'action': action,
                'expires_at': expires_at
            }
            
        except Exception as e:
            print(f"❌ Error verifying token: {e}")
            import traceback
            traceback.print_exc()
            return False, None
    
    def get_unsubscribe_url(self, email: str) -> str:
        """Generuje URL do wypisania się z klubu"""
        token = self.generate_token(email, 'unsubscribe')
        if not token:
            return None
        return f"{self.base_url}/unsubscribe/{token}"
    
    def get_delete_account_url(self, email: str) -> str:
        """Generuje URL do usunięcia konta"""
        token = self.generate_token(email, 'delete_account')
        if not token:
            return None
        return f"{self.base_url}/delete-account/{token}"
    
    def process_unsubscribe(self, user: User) -> Tuple[bool, str]:
        """Przetwarza wypisanie użytkownika z klubu"""
        try:
            # Usuń z klubu
            user.club_member = False
            
            # Usuń z grupy członków klubu
            from app.models import UserGroup, UserGroupMember
            club_group = UserGroup.query.filter_by(group_type='club_members').first()
            if club_group:
                member = UserGroupMember.query.filter_by(
                    user_id=user.id, group_id=club_group.id
                ).first()
                if member:
                    db.session.delete(member)
            
            db.session.commit()
            
            print(f"✅ User {user.email} unsubscribed from club")
            return True, f"Zostałeś wypisany z klubu"
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error processing unsubscribe: {e}")
            return False, f"Błąd: {str(e)}"
    
    def process_account_deletion(self, user: User) -> Tuple[bool, str]:
        """Przetwarza usunięcie konta użytkownika"""
        try:
            user_email = user.email
            
            # Usuń użytkownika
            db.session.delete(user)
            db.session.commit()
            
            print(f"✅ Account {user_email} deleted")
            return True, f"Konto zostało usunięte"
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error processing account deletion: {e}")
            return False, f"Błąd: {str(e)}"
    


# Global instance
unsubscribe_manager = UnsubscribeManager()
