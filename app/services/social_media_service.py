"""
Social Media Publishing Service
Automatyczne publikowanie wpisów blogowych na mediach społecznościowych
"""
import logging
import requests
from typing import Dict, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SocialMediaService:
    """Service for publishing blog posts to social media platforms"""
    
    def __init__(self):
        self.facebook_enabled = False
        self.facebook_access_token = None
        self.facebook_page_id = None
        self._initialize_facebook()
    
    def _initialize_facebook(self):
        """Initialize Facebook API configuration"""
        import os
        
        self.facebook_access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        self.facebook_page_id = os.getenv('FACEBOOK_PAGE_ID')
        
        if self.facebook_access_token and self.facebook_page_id:
            self.facebook_enabled = True
            logger.info("✅ Facebook API zainicjalizowane")
        else:
            logger.warning("⚠️ Facebook API nie skonfigurowane - pomijam publikację")
    
    def publish_to_facebook(self, post_title: str, post_url: str, 
                           post_excerpt: str = None, post_image_url: str = None) -> Tuple[bool, str]:
        """
        Publikuje post na Facebooku
        
        Args:
            post_title: Tytuł posta
            post_url: URL posta na stronie
            post_excerpt: Opis posta (opcjonalny)
            post_image_url: URL obrazka (opcjonalny)
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if not self.facebook_enabled:
            return False, "Facebook API nie jest skonfigurowane"
        
        try:
            # Przygotuj wiadomość
            message = post_title
            if post_excerpt:
                message += f"\n\n{post_excerpt}"
            
            # Przygotuj parametry
            params = {
                'access_token': self.facebook_access_token,
                'message': message,
                'link': post_url
            }
            
            # Dodaj obraz jeśli dostępny
            if post_image_url:
                params['picture'] = post_image_url
            
            # Publikuj na stronie Facebook
            url = f"https://graph.facebook.com/v18.0/{self.facebook_page_id}/feed"
            
            response = requests.post(url, data=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                post_id = result.get('id', '')
                logger.info(f"✅ Post opublikowany na Facebooku: {post_id}")
                return True, f"Post opublikowany na Facebooku (ID: {post_id})"
            else:
                error_msg = f"Błąd publikacji na Facebooku: {response.status_code} - {response.text}"
                logger.error(f"❌ {error_msg}")
                return False, error_msg
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Błąd połączenia z Facebook API: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Błąd publikacji na Facebooku: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def publish_to_twitter(self, post_title: str, post_url: str, 
                         post_excerpt: str = None) -> Tuple[bool, str]:
        """
        Publikuje post na Twitterze (TODO: implementacja gdy będzie API key)
        
        Args:
            post_title: Tytuł posta
            post_url: URL posta na stronie
            post_excerpt: Opis posta (opcjonalny)
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        logger.info("📝 Twitter publishing not yet implemented")
        return False, "Twitter publishing not yet implemented"
    
    def publish_to_linkedin(self, post_title: str, post_url: str, 
                            post_excerpt: str = None) -> Tuple[bool, str]:
        """
        Publikuje post na LinkedIn (TODO: implementacja gdy będzie API key)
        
        Args:
            post_title: Tytuł posta
            post_url: URL posta na stronie
            post_excerpt: Opis posta (opcjonalny)
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        logger.info("📝 LinkedIn publishing not yet implemented")
        return False, "LinkedIn publishing not yet implemented"
    
    def auto_publish_post(self, post_data: Dict) -> Dict[str, Tuple[bool, str]]:
        """
        Automatycznie publikuje post na wszystkich włączonych platformach
        
        Args:
            post_data: Dane posta zawierające tytuł, URL, excerpt, image_url
        
        Returns:
            Dict[str, Tuple[bool, str]]: Wyniki publikacji dla każdej platformy
        """
        results = {}
        
        # Publikuj na Facebooku
        if post_data.get('social_facebook', False):
            success, message = self.publish_to_facebook(
                post_data.get('title'),
                post_data.get('url'),
                post_data.get('excerpt'),
                post_data.get('image_url')
            )
            results['facebook'] = (success, message)
        
        # Publikuj na Twitterze
        if post_data.get('social_twitter', False):
            success, message = self.publish_to_twitter(
                post_data.get('title'),
                post_data.get('url'),
                post_data.get('excerpt')
            )
            results['twitter'] = (success, message)
        
        # Publikuj na LinkedIn
        if post_data.get('social_linkedin', False):
            success, message = self.publish_to_linkedin(
                post_data.get('title'),
                post_data.get('url'),
                post_data.get('excerpt')
            )
            results['linkedin'] = (success, message)
        
        return results


# Singleton instance
social_media_service = SocialMediaService()


