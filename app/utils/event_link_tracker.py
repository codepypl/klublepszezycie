"""
Event Link Tracker - generuje i weryfikuje linki śledzące dla wydarzeń
"""
import hmac
import hashlib
import secrets
import base64
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from app.models.user_model import User
from app.models.events_model import EventSchedule

class EventLinkTracker:
    """Manager do generowania i weryfikacji linków śledzących dla wydarzeń"""
    
    def __init__(self):
        self.secret_key = os.getenv('SECRET_KEY', 'default-secret-key-for-development')
        self.token_expiry_days = 90  # Token ważny przez 90 dni
        self.base_url = os.getenv('BASE_URL', 'https://klublepszezycie.pl')
        
        # Ensure URL has protocol
        if self.base_url and not self.base_url.startswith(('http://', 'https://')):
            self.base_url = f'https://{self.base_url}'
    
    def generate_tracking_token(self, user_id: int, event_id: int) -> str:
        """
        Generuje token śledzący używając HMAC (stateless, bezpieczny)
        
        Format: {user_id}.{event_id}.{expires_timestamp}.{random_salt}.{hmac_signature}
        """
        try:
            # Utwórz token payload
            expires_at = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now() + timedelta(days=self.token_expiry_days)
            expires_timestamp = int(expires_at.timestamp())
            
            # Dodaj losowy salt dla unikalności (8 znaków)
            random_salt = secrets.token_urlsafe(6)[:8]
            
            # Payload: user_id.event_id.expires_timestamp.random_salt
            payload = f"{user_id}.{event_id}.{expires_timestamp}.{random_salt}"
            
            # Wygeneruj HMAC signature (16 znaków dla krótkości)
            signature = hmac.new(
                self.secret_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()[:16]
            
            # Token format: user_id.event_id.expires_timestamp.random_salt.signature
            token = f"{user_id}.{event_id}.{expires_timestamp}.{random_salt}.{signature}"
            
            # Encode to base64 URL-safe dla bezpieczeństwa w URL
            token_b64 = base64.urlsafe_b64encode(token.encode('utf-8')).decode('utf-8')
            
            return token_b64
            
        except Exception as e:
            print(f"❌ Error generating tracking token: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def verify_tracking_token(self, token_b64: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Weryfikuje token śledzący i zwraca dane użytkownika i wydarzenia
        Returns: (is_valid, data_dict)
        """
        try:
            # Decode from base64
            try:
                token = base64.urlsafe_b64decode(token_b64.encode('utf-8')).decode('utf-8')
            except Exception as e:
                print(f"❌ Invalid token base64: {e}")
                return False, None
            
            # Podziel token na części
            parts = token.split('.')
            if len(parts) != 5:
                print(f"❌ Invalid token format: {len(parts)} parts (expected 5)")
                return False, None
            
            user_id_str, event_id_str, expires_timestamp_str, random_salt, signature = parts
            
            # Konwertuj ID i timestamp
            try:
                user_id = int(user_id_str)
                event_id = int(event_id_str)
                expires_timestamp = int(expires_timestamp_str)
            except ValueError:
                print(f"❌ Invalid token: non-numeric user_id, event_id or timestamp")
                return False, None
            
            # Sprawdź czy token nie wygasł
            from app.utils.timezone_utils import get_local_now
            expires_at = datetime.fromtimestamp(expires_timestamp)
            now = get_local_now().replace(tzinfo=None)  # Remove timezone for comparison
            if now > expires_at:
                print(f"❌ Token expired at {expires_at}")
                return False, None
            
            # Weryfikuj HMAC signature
            payload = f"{user_id}.{event_id}.{expires_timestamp}.{random_salt}"
            expected_signature = hmac.new(
                self.secret_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()[:16]
            
            if not hmac.compare_digest(signature, expected_signature):
                print(f"❌ Invalid token signature")
                return False, None
            
            # Znajdź użytkownika i wydarzenie
            user = User.query.get(user_id)
            if not user:
                print(f"❌ User not found: ID {user_id}")
                return False, None
            
            event = EventSchedule.query.get(event_id)
            if not event:
                print(f"❌ Event not found: ID {event_id}")
                return False, None
            
            print(f"✅ Valid tracking token for user {user.email} and event {event.title}")
            
            return True, {
                'user': user,
                'user_id': user_id,
                'event': event,
                'event_id': event_id,
                'expires_at': expires_at,
                'token': token  # Raw token (bez base64) dla zapisu w bazie
            }
            
        except Exception as e:
            print(f"❌ Error verifying tracking token: {e}")
            import traceback
            traceback.print_exc()
            return False, None
    
    def get_tracking_url(self, user_id: int, event_id: int, original_url: str = None) -> str:
        """
        Generuje URL śledzący dla wydarzenia
        
        Args:
            user_id: ID użytkownika
            event_id: ID wydarzenia
            original_url: Oryginalny URL wydarzenia (jeśli None, użyje get_event_url())
        
        Returns:
            str: URL śledzący
        """
        token = self.generate_tracking_token(user_id, event_id)
        if not token:
            # Fallback do oryginalnego URL jeśli nie udało się wygenerować tokenu
            if original_url:
                return original_url
            event = EventSchedule.query.get(event_id)
            if event:
                return event.get_event_url()
            return None
        
        # Jeśli nie podano oryginalnego URL, pobierz z wydarzenia
        if not original_url:
            event = EventSchedule.query.get(event_id)
            if event:
                original_url = event.get_event_url()
            else:
                original_url = f"{self.base_url}/events/{event_id}"
        
        # Zwróć URL śledzący
        return f"{self.base_url}/event-track/{token}?redirect={base64.urlsafe_b64encode(original_url.encode('utf-8')).decode('utf-8')}"


# Global instance
event_link_tracker = EventLinkTracker()


