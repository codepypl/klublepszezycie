"""
Silnik szablonów e-maili - renderowanie i cache
"""
import logging
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from app.models import EmailTemplate

class EmailTemplateEngine:
    """
    Silnik szablonów e-maili
    
    Funkcje:
    1. Renderowanie szablonów z kontekstem
    2. Cache szablonów dla wydajności
    3. Walidacja szablonów
    4. Obsługa zmiennych
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.template_cache = {}
        self.cache_ttl = 3600  # 1 godzina
    
    def render_template(self, template_name: str, context: Dict[str, Any] = None) -> Tuple[str, str, str]:
        """
        Renderuje szablon e-maila
        
        Args:
            template_name: Nazwa szablonu
            context: Kontekst dla zmiennych
            
        Returns:
            Tuple[str, str, str]: (subject, html_content, text_content)
        """
        try:
            # Pobierz szablon
            template = self._get_template(template_name)
            if not template:
                return "", "", ""
            
            # Renderuj z kontekstem
            subject = self._render_content(template.subject, context or {})
            html_content = self._render_content(template.html_content, context or {})
            text_content = self._render_content(template.text_content, context or {})
            
            return subject, html_content, text_content
            
        except Exception as e:
            self.logger.error(f"❌ Błąd renderowania szablonu {template_name}: {e}")
            return "", "", ""
    
    def render_custom_template(self, subject: str, html_content: str = None, 
                              text_content: str = None, context: Dict[str, Any] = None) -> Tuple[str, str, str]:
        """
        Renderuje niestandardowy szablon
        
        Args:
            subject: Temat e-maila
            html_content: Treść HTML
            text_content: Treść tekstowa
            context: Kontekst dla zmiennych
            
        Returns:
            Tuple[str, str, str]: (subject, html_content, text_content)
        """
        try:
            rendered_subject = self._render_content(subject, context or {})
            rendered_html = self._render_content(html_content or "", context or {})
            rendered_text = self._render_content(text_content or "", context or {})
            
            return rendered_subject, rendered_html, rendered_text
            
        except Exception as e:
            self.logger.error(f"❌ Błąd renderowania niestandardowego szablonu: {e}")
            return subject, html_content or "", text_content or ""
    
    def validate_template(self, template_name: str) -> Tuple[bool, str]:
        """
        Waliduje szablon
        
        Args:
            template_name: Nazwa szablonu
            
        Returns:
            Tuple[bool, str]: (valid, message)
        """
        try:
            template = self._get_template(template_name)
            if not template:
                return False, f"Szablon '{template_name}' nie został znaleziony"
            
            if not template.is_active:
                return False, f"Szablon '{template_name}' jest nieaktywny"
            
            if not template.subject:
                return False, f"Szablon '{template_name}' nie ma tematu"
            
            if not template.html_content and not template.text_content:
                return False, f"Szablon '{template_name}' nie ma treści"
            
            return True, "Szablon jest poprawny"
            
        except Exception as e:
            return False, f"Błąd walidacji szablonu: {str(e)}"
    
    def get_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Pobiera dostępne szablony
        
        Returns:
            Dict[str, Dict[str, Any]]: Słownik szablonów
        """
        try:
            templates = EmailTemplate.query.filter_by(is_active=True).all()
            
            result = {}
            for template in templates:
                result[template.name] = {
                    'id': template.id,
                    'name': template.name,
                    'subject': template.subject,
                    'description': template.description,
                    'has_html': bool(template.html_content),
                    'has_text': bool(template.text_content),
                    'created_at': template.created_at.isoformat() if template.created_at else None
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Błąd pobierania szablonów: {e}")
            return {}
    
    def _get_template(self, template_name: str) -> Optional[EmailTemplate]:
        """Pobiera szablon z cache lub bazy danych"""
        try:
            # Sprawdź cache
            if template_name in self.template_cache:
                template, timestamp = self.template_cache[template_name]
                if (datetime.now().timestamp() - timestamp) < self.cache_ttl:
                    return template
            
            # Pobierz z bazy danych
            template = EmailTemplate.query.filter_by(
                name=template_name,
                is_active=True
            ).first()
            
            if template:
                # Dodaj do cache
                self.template_cache[template_name] = (template, datetime.now().timestamp())
            
            return template
            
        except Exception as e:
            self.logger.error(f"❌ Błąd pobierania szablonu {template_name}: {e}")
            return None
    
    def _render_content(self, content: str, context: Dict[str, Any]) -> str:
        """Renderuje treść z kontekstem"""
        try:
            if not content:
                return ""
            
            rendered = content
            
            # Zastąp zmienne
            for key, value in context.items():
                placeholder = f"{{{{{key}}}}}"
                rendered = rendered.replace(placeholder, str(value))
            
            # Dodaj domyślne zmienne
            default_vars = {
                'site_name': 'Klub Lepszego Życia',
                'site_url': 'https://klublepszezycie.pl',
                'current_year': datetime.now().year
            }
            
            for key, value in default_vars.items():
                placeholder = f"{{{{{key}}}}}"
                rendered = rendered.replace(placeholder, str(value))
            
            return rendered
            
        except Exception as e:
            self.logger.error(f"❌ Błąd renderowania treści: {e}")
            return content or ""
    
    def clear_cache(self):
        """Czyści cache szablonów"""
        self.template_cache.clear()
        self.logger.info("🗑️ Cache szablonów wyczyszczony")
