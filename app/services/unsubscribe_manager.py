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
            self.base_url = f'https://{self.base_url}'
    
    def generate_token(self, email: str, action: str) -> str:
        """
        Generuje token zawierający zaszyfrowany email i akcję
        Format: base64(json({email, action, expires_at, random}):hmac_signature)
        """
        try:
            # Zaszyfruj email używając prostego szyfrowania
            encrypted_email = self._encrypt_email(email)
            
            # Utwórz payload
            expires_at = datetime.utcnow() + timedelta(days=self.token_expiry_days)
            payload = {
                'email': encrypted_email,
                'action': action,
                'expires_at': expires_at.isoformat(),
                'random': secrets.token_hex(16)
            }
            
            # Serializuj do JSON
            payload_json = json.dumps(payload, sort_keys=True)
            
            # Wygeneruj HMAC signature
            signature = hmac.new(
                self.secret_key.encode('utf-8'),
                payload_json.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Połącz payload z signature
            token_data = f"{payload_json}:{signature}"
            
            # Encode do base64 URL-safe
            token = base64.urlsafe_b64encode(token_data.encode('utf-8')).decode('ascii')
            
            print(f"🔑 Generated {action} token for {email}")
            print(f"   Expires: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Token: {token[:50]}...")
            
            return token
            
        except Exception as e:
            print(f"❌ Error generating token: {e}")
            return None
    
    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Weryfikuje token i zwraca dane użytkownika
        Returns: (is_valid, user_data)
        """
        try:
            # Decode base64
            token_data = base64.urlsafe_b64decode(token.encode('ascii')).decode('utf-8')
            
            # Podziel na payload i signature
            if ':' not in token_data:
                return False, None
            
            payload_json, signature = token_data.rsplit(':', 1)
            
            # Weryfikuj HMAC signature
            expected_signature = hmac.new(
                self.secret_key.encode('utf-8'),
                payload_json.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                print(f"❌ Invalid token signature")
                return False, None
            
            # Parsuj payload
            payload = json.loads(payload_json)
            
            # Sprawdź czy token nie wygasł
            expires_at = datetime.fromisoformat(payload['expires_at'])
            if datetime.utcnow() > expires_at:
                print(f"❌ Token expired at {expires_at}")
                return False, None
            
            # Odszyfruj email
            email = self._decrypt_email(payload['email'])
            if not email:
                print(f"❌ Failed to decrypt email")
                return False, None
            
            # Znajdź użytkownika
            user = User.query.filter_by(email=email).first()
            if not user:
                print(f"❌ User not found: {email}")
                return False, None
            
            print(f"✅ Valid {payload['action']} token for {email}")
            print(f"   Expires: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            return True, {
                'user': user,
                'email': email,
                'action': payload['action'],
                'expires_at': expires_at
            }
            
        except Exception as e:
            print(f"❌ Error verifying token: {e}")
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
        return f"{self.base_url}/remove-account/{token}"
    
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
    
    def _encrypt_email(self, email: str) -> str:
        """Proste szyfrowanie emaila"""
        try:
            # Użyj HMAC jako prostego szyfrowania
            encrypted = hmac.new(
                self.secret_key.encode('utf-8'),
                email.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            return encrypted
        except Exception as e:
            print(f"❌ Error encrypting email: {e}")
            return None
    
    def _decrypt_email(self, encrypted_email: str) -> Optional[str]:
        """Odszyfrowanie emaila - wymaga sprawdzenia w bazie danych"""
        try:
            # Znajdź użytkownika którego zaszyfrowany email pasuje
            users = User.query.all()
            for user in users:
                if self._encrypt_email(user.email) == encrypted_email:
                    return user.email
            return None
        except Exception as e:
            print(f"❌ Error decrypting email: {e}")
            return None


# Global instance
unsubscribe_manager = UnsubscribeManager()
