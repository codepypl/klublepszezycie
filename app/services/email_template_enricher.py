"""
Serwis automatycznego dodawania linków unsubscribe i delete account do szablonów email
"""
import re
from typing import Optional, Dict, Any
from app.models.email_model import EmailTemplate, DefaultEmailTemplate

class EmailTemplateEnricher:
    """Serwis dodawania linków unsubscribe/delete do szablonów email"""
    
    # Szablony które NIE powinny mieć linków unsubscribe (notyfikacje admin)
    EXCLUDED_TEMPLATES = {
        'admin_notification',
        'security_alert'
        # admin_message - może mieć linki unsubscribe
        # password_reset - może mieć linki unsubscribe
    }
    
    def __init__(self):
        self.unsubscribe_manager = None  # Będzie ustawiony przy pierwszym użyciu
    
    def should_add_links(self, template_name: str) -> bool:
        """Sprawdza czy szablon powinien mieć linki unsubscribe"""
        return template_name not in self.EXCLUDED_TEMPLATES
    
    def enrich_template_content(self, html_content: str, text_content: str, 
                              user_email: Optional[str] = None) -> Dict[str, str]:
        """
        Dodaje linki unsubscribe i delete account do treści szablonu
        """
        if user_email:
            # Sprawdź czy użytkownik jest członkiem klubu
            is_club_member = self._is_user_club_member(user_email)
            
            # Generuj rzeczywiste URL
            unsubscribe_url = self._get_unsubscribe_manager().get_unsubscribe_url(user_email) if is_club_member else None
            delete_account_url = self._get_unsubscribe_manager().get_delete_account_url(user_email)
        else:
            # Użyj placeholderów
            unsubscribe_url = "{{unsubscribe_url}}"
            delete_account_url = "{{delete_account_url}}"
        
        # Dodaj linki do HTML
        enriched_html = self._add_links_to_html(html_content, unsubscribe_url, delete_account_url)
        
        # Dodaj linki do tekstu
        enriched_text = self._add_links_to_text(text_content, unsubscribe_url, delete_account_url)
        
        return {
            'html_content': enriched_html,
            'text_content': enriched_text
        }
    
    def _add_links_to_html(self, html_content: str, unsubscribe_url: str, delete_account_url: str) -> str:
        """Dodaje linki unsubscribe do HTML"""
        
        # Zastąp placeholdery lub usuń linki unsubscribe jeśli użytkownik nie jest członkiem klubu
        # Obsługa obu formatów: {{unsubscribe_url}} i {{ unsubscribe_url }}
        if unsubscribe_url:
            html_content = html_content.replace('{{unsubscribe_url}}', unsubscribe_url)
            html_content = html_content.replace('{{ unsubscribe_url }}', unsubscribe_url)
        else:
            # Usuń link unsubscribe jeśli użytkownik nie jest członkiem klubu
            html_content = html_content.replace('<a href="{{unsubscribe_url}}" target="_blank">Wypisz się z klubu</a> | ', '')
            html_content = html_content.replace(' | <a href="{{unsubscribe_url}}" target="_blank">Wypisz się z klubu</a>', '')
            html_content = html_content.replace('<a href="{{unsubscribe_url}}" target="_blank">Wypisz się z klubu</a>', '')
            html_content = html_content.replace('<a href="{{ unsubscribe_url }}" target="_blank">Wypisz się z klubu</a> | ', '')
            html_content = html_content.replace(' | <a href="{{ unsubscribe_url }}" target="_blank">Wypisz się z klubu</a>', '')
            html_content = html_content.replace('<a href="{{ unsubscribe_url }}" target="_blank">Wypisz się z klubu</a>', '')
        
        # Zawsze zastąp delete_account_url (oba formaty)
        if delete_account_url:
            html_content = html_content.replace('{{delete_account_url}}', delete_account_url)
            html_content = html_content.replace('{{ delete_account_url }}', delete_account_url)
        
        # Sprawdź czy linki już istnieją (po zastąpieniu placeholderów)
        if 'Zrezygnuj z członkostwa w klubie' in html_content or 'Usuń konto' in html_content:
            return html_content
        
        # Buduj linki dynamicznie
        links_html = []
        
        # Dodaj link unsubscribe tylko jeśli użytkownik jest członkiem klubu
        if unsubscribe_url:
            links_html.append(f'<a href="{unsubscribe_url}" target="_blank" style="color: #6c757d; text-decoration: underline;">Zrezygnuj z członkostwa w klubie</a>')
        
        # Zawsze dodaj link do usunięcia konta
        if delete_account_url:
            links_html.append(f'<a href="{delete_account_url}" target="_blank" style="color: #dc3545; text-decoration: underline;">Usuń konto</a>')
        
        # Jeśli nie ma żadnych linków, nie dodawaj footera
        if not links_html:
            return html_content
        
        # HTML z linkami
        footer_html = f'''
<div style="margin-top: 40px; padding: 20px; background-color: #f8f9fa; border-top: 1px solid #dee2e6; text-align: center; font-size: 12px; color: #6c757d;">
    <p style="margin: 0 0 10px 0;">
        {' | '.join(links_html)}
    </p>
    <p style="margin: 0; font-size: 11px;">
        Te linki są ważne przez 30 dni. Jeśli nie chcesz otrzymywać naszych emaili, możesz wypisać się z klubu lub całkowicie usunąć swoje konto.
    </p>
</div>'''
        
        # Dodaj przed zamknięciem </body> lub na końcu
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', f'{footer_html}</body>')
        else:
            html_content += footer_html
        
        return html_content
    
    def _add_links_to_text(self, text_content: str, unsubscribe_url: str, delete_account_url: str) -> str:
        """Dodaje linki unsubscribe do tekstu"""
        
        # Zastąp placeholdery lub usuń linki unsubscribe jeśli użytkownik nie jest członkiem klubu
        # Obsługa obu formatów: {{unsubscribe_url}} i {{ unsubscribe_url }}
        if unsubscribe_url:
            text_content = text_content.replace('{{unsubscribe_url}}', unsubscribe_url)
            text_content = text_content.replace('{{ unsubscribe_url }}', unsubscribe_url)
        else:
            # Usuń link unsubscribe jeśli użytkownik nie jest członkiem klubu
            text_content = text_content.replace('{{unsubscribe_url}}\n', '')
            text_content = text_content.replace('\n{{unsubscribe_url}}', '')
            text_content = text_content.replace('{{unsubscribe_url}}', '')
            text_content = text_content.replace('{{ unsubscribe_url }}\n', '')
            text_content = text_content.replace('\n{{ unsubscribe_url }}', '')
            text_content = text_content.replace('{{ unsubscribe_url }}', '')
        
        # Zawsze zastąp delete_account_url (oba formaty)
        if delete_account_url:
            text_content = text_content.replace('{{delete_account_url}}', delete_account_url)
            text_content = text_content.replace('{{ delete_account_url }}', delete_account_url)
        
        # Sprawdź czy linki już istnieją (po zastąpieniu placeholderów)
        if 'Zrezygnuj z członkostwa w klubie' in text_content or 'Usuń konto:' in text_content:
            return text_content
        
        # Buduj linki dynamicznie
        links_text = []
        
        # Dodaj link unsubscribe tylko jeśli użytkownik jest członkiem klubu
        if unsubscribe_url:
            links_text.append(f'Zrezygnuj z członkostwa w klubie: {unsubscribe_url}')
        
        # Zawsze dodaj link do usunięcia konta
        if delete_account_url:
            links_text.append(f'Usuń konto: {delete_account_url}')
        
        # Jeśli nie ma żadnych linków, nie dodawaj footera
        if not links_text:
            return text_content
        
        # Tekst z linkami
        footer_text = f'''

---
{chr(10).join(links_text)}

Te linki są ważne przez 30 dni. Jeśli nie chcesz otrzymywać naszych emaili, możesz wypisać się z klubu lub całkowicie usunąć swoje konto.'''
        
        # Dodaj na końcu
        return text_content + footer_text
    
    def get_template_variables(self) -> Dict[str, str]:
        """Zwraca zmienne szablonu dla unsubscribe"""
        return {
            'unsubscribe_url': 'URL do wypisania się z klubu',
            'delete_account_url': 'URL do usunięcia konta'
        }
    
    def process_template(self, template_name: str, html_content: str, text_content: str,
                       user_email: Optional[str] = None) -> Dict[str, str]:
        """
        Przetwarza szablon i dodaje linki unsubscribe jeśli odpowiednie
        """
        if not self.should_add_links(template_name):
            return {
                'html_content': html_content,
                'text_content': text_content
            }
        
        return self.enrich_template_content(html_content, text_content, user_email)
    
    def update_existing_templates(self):
        """Aktualizuje wszystkie istniejące szablony z linkami unsubscribe"""
        from app import db
        
        try:
            # Aktualizuj EmailTemplate
            templates = EmailTemplate.query.filter_by(is_active=True).all()
            updated_count = 0
            
            for template in templates:
                if self.should_add_links(template.name):
                    enriched = self.enrich_template_content(
                        template.html_content or '', 
                        template.text_content or ''
                    )
                    
                    template.html_content = enriched['html_content']
                    template.text_content = enriched['text_content']
                    
                    # Dodaj zmienne do template variables
                    self._add_variables_to_template(template)
                    updated_count += 1
            
            # Aktualizuj DefaultEmailTemplate
            default_templates = DefaultEmailTemplate.query.filter_by(is_active=True).all()
            default_updated_count = 0
            
            for template in default_templates:
                if self.should_add_links(template.name):
                    enriched = self.enrich_template_content(
                        template.html_content or '', 
                        template.text_content or ''
                    )
                    
                    template.html_content = enriched['html_content']
                    template.text_content = enriched['text_content']
                    
                    # Dodaj zmienne do template variables
                    self._add_variables_to_template(template)
                    default_updated_count += 1
            
            db.session.commit()
            
            print(f"✅ Zaktualizowano {updated_count} szablonów EmailTemplate")
            print(f"✅ Zaktualizowano {default_updated_count} szablonów DefaultEmailTemplate")
            return True, f"Zaktualizowano {updated_count + default_updated_count} szablonów"
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Błąd aktualizacji szablonów: {e}")
            return False, f"Błąd: {str(e)}"
    
    def _add_variables_to_template(self, template):
        """Dodaje zmienne unsubscribe do szablonu"""
        import json
        
        if template.variables:
            try:
                variables = json.loads(template.variables)
            except:
                variables = {}
        else:
            variables = {}
        
        # Dodaj zmienne unsubscribe
        variables.update(self.get_template_variables())
        template.variables = json.dumps(variables)
    
    def _is_user_club_member(self, user_email: str) -> bool:
        """Sprawdza czy użytkownik jest członkiem klubu"""
        try:
            from app.models.user_model import User
            user = User.query.filter_by(email=user_email).first()
            if user:
                return user.club_member
            return False
        except Exception as e:
            print(f"❌ Błąd sprawdzania członkostwa dla {user_email}: {e}")
            return False
    
    def _get_unsubscribe_manager(self):
        """Lazy loading unsubscribe manager"""
        if not self.unsubscribe_manager:
            from app.services.unsubscribe_manager import unsubscribe_manager
            self.unsubscribe_manager = unsubscribe_manager
        return self.unsubscribe_manager


# Global instance
email_template_enricher = EmailTemplateEnricher()
