"""
Template Manager - zarządzanie szablonami emaili z bazy danych
"""
import json
import logging
from datetime import datetime
from app.models import db, EmailTemplate

class TemplateManager:
    """Menedżer szablonów emaili - używa bazy danych jako źródła prawdy"""
    
    def get_default_templates(self):
        """Pobiera domyślne szablony z bazy danych (EmailTemplate z is_default=True)"""
        try:
            templates = EmailTemplate.query.filter_by(is_active=True, is_default=True).all()
            
            # Jeśli nie ma domyślnych szablonów, utwórz je automatycznie
            if not templates:
                logging.info("Brak domyślnych szablonów, inicjalizuję...")
                self.initialize_default_templates()
                templates = EmailTemplate.query.filter_by(is_active=True, is_default=True).all()
            
            return templates
        except Exception as e:
            logging.error(f"Błąd pobierania domyślnych szablonów: {str(e)}")
            return []
    
    def initialize_default_templates(self):
        """Inicjalizuje domyślne szablony w bazie danych"""
        try:
            # Użyj fixtures (jak Django) - to jest główna metoda
            from app.services.fixture_loader import load_email_templates_fixtures
            
            success, message = load_email_templates_fixtures()
            if success:
                logging.info(f"Załadowano domyślne szablony z fixtures: {message}")
                return True, f"Załadowano domyślne szablony z fixtures: {message}"
            
            # Fallback - utwórz podstawowe szablony programowo (tylko w przypadku błędu)
            logging.warning("Nie udało się załadować z fixtures, tworzę podstawowe szablony...")
            
            # Importuj funkcje tworzące szablony z create_professional_templates
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            
            from create_professional_templates import create_welcome_template, create_event_reminder_5min_template
            
            # Podstawowe szablony do inicjalizacji
            default_templates_data = [
                {
                    'name': 'welcome',
                    'template_type': 'html',
                    'subject': 'Witamy w Klubie Lepsze Życie!',
                    'html_content': create_welcome_template(),
                    'text_content': '''Witamy w Klubie Lepsze Życie! 🌟

Cześć {{user_name}}

Dziękujemy za dołączenie do Klubu Lepsze Życie!

🔑 Twoje dane logowania:
Email: {{user_email}}
Hasło tymczasowe: {{temporary_password}}

⚠️ Ważne: Zalecamy zmianę hasła po pierwszym zalogowaniu.

Zaloguj się: {{login_url}}

Jeśli masz jakiekolwiek pytania, nie wahaj się z nami skontaktować.

© 2025 Klub Lepsze Życie. Wszystkie prawa zastrzeżone.
Kontakt: kontakt@klublepszezycie.pl

Zrezygnuj z członkostwa: {{unsubscribe_url}}
Usuń konto: {{delete_account_url}}''',
                    'variables': '{"user_name": "Imię użytkownika", "user_email": "Email użytkownika", "temporary_password": "Tymczasowe hasło", "login_url": "URL logowania", "unsubscribe_url": "URL rezygnacji", "delete_account_url": "URL usunięcia konta"}',
                    'description': 'Szablon powitalny dla nowych członków klubu',
                    'is_active': True
                },
                {
                    'name': 'event_reminder_5min',
                    'template_type': 'html',
                    'subject': 'Przypomnienie: {{event_title}} za 5 minut! ⚡',
                    'html_content': create_event_reminder_5min_template(),
                    'text_content': '''Przypomnienie o wydarzeniu za 5 minut! ⚡

Cześć {{user_name}}!

Przypominamy o nadchodzącym wydarzeniu:

{{event_title}}
📅 Data: {{event_date}}
🕐 Godzina: {{event_time}}
📍 Lokalizacja: {{event_location}}

Dołącz do wydarzenia: {{event_url}}

Do zobaczenia na wydarzeniu!

Zespół Klub Lepsze Życie

Zrezygnuj z członkostwa: {{unsubscribe_url}}
Usuń konto: {{delete_account_url}}''',
                    'variables': '{"user_name": "Imię użytkownika", "event_title": "Tytuł wydarzenia", "event_date": "Data wydarzenia", "event_time": "Godzina wydarzenia", "event_location": "Lokalizacja wydarzenia", "event_url": "URL wydarzenia", "unsubscribe_url": "URL rezygnacji", "delete_account_url": "URL usunięcia konta"}',
                    'description': 'Przypomnienie o wydarzeniu 5 minut przed rozpoczęciem',
                    'is_active': True
                }
            ]
            
            created_count = 0
            for template_data in default_templates_data:
                # Sprawdź czy szablon już istnieje
                existing = DefaultEmailTemplate.query.filter_by(name=template_data['name']).first()
                if not existing:
                    default_template = DefaultEmailTemplate(**template_data)
                    db.session.add(default_template)
                    created_count += 1
                    logging.info(f"Utworzono domyślny szablon: {template_data['name']}")
            
            db.session.commit()
            logging.info(f"Inicjalizacja zakończona: utworzono {created_count} domyślnych szablonów")
            return True, f"Utworzono {created_count} domyślnych szablonów"
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Błąd inicjalizacji domyślnych szablonów: {str(e)}")
            return False, f"Błąd inicjalizacji: {str(e)}"
    
    def sync_templates_from_defaults(self, force_reload_fixtures=False):
        """Synchronizuje szablony z domyślnych w bazie danych"""
        try:
            # Jeśli wymagane, załaduj ponownie fixtures
            if force_reload_fixtures:
                from app.services.fixture_loader import load_email_templates_fixtures
                success, message = load_email_templates_fixtures(force_update=True)
                if not success:
                    logging.warning(f"Nie udało się załadować fixtures: {message}")
            
            default_templates = self.get_default_templates()
            
            if not default_templates:
                return False, "Brak domyślnych szablonów w bazie danych"
            
            # Pobierz istniejące szablony
            existing_templates = {t.name: t for t in EmailTemplate.query.all()}
            
            added_count = 0
            updated_count = 0
            
            for default_template in default_templates:
                if default_template.name in existing_templates:
                    # Aktualizuj istniejący szablon
                    existing = existing_templates[default_template.name]
                    existing.subject = default_template.subject
                    existing.html_content = default_template.html_content
                    existing.text_content = default_template.text_content
                    existing.variables = default_template.variables
                    existing.description = default_template.description
                    existing.template_type = default_template.template_type
                    existing.is_default = True
                    existing.updated_at = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now()
                    updated_count += 1
                    logging.info(f"🔄 Zaktualizowano szablon: {default_template.name}")
                else:
                    # Dodaj nowy szablon
                    new_template = EmailTemplate(
                        name=default_template.name,
                        template_type=default_template.template_type,
                        subject=default_template.subject,
                        html_content=default_template.html_content,
                        text_content=default_template.text_content,
                        variables=default_template.variables,
                        description=default_template.description,
                        is_default=True,
                        is_active=True
                    )
                    db.session.add(new_template)
                    added_count += 1
                    logging.info(f"✅ Dodano szablon: {default_template.name}")
            
            db.session.commit()
            return True, f"Zsynchronizowano {added_count} nowych szablonów, zaktualizowano {updated_count}"
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Błąd synchronizacji szablonów: {str(e)}")
            return False, f"Błąd synchronizacji: {str(e)}"
    
    def reset_templates_to_defaults(self):
        """Resetuje wszystkie szablony do domyślnych z bazy danych"""
        try:
            # Usuń referencje w tabelach, które używają template_id
            from app.models import EmailLog, EmailQueue, EmailCampaign
            
            # Ustaw template_id na NULL we wszystkich tabelach
            EmailLog.query.filter(EmailLog.template_id.isnot(None)).update({'template_id': None})
            EmailQueue.query.filter(EmailQueue.template_id.isnot(None)).update({'template_id': None})
            EmailCampaign.query.filter(EmailCampaign.template_id.isnot(None)).update({'template_id': None})
            db.session.commit()
            
            # Usuń wszystkie istniejące szablony - użyj delete() z synchronize_session=False dla pewności
            deleted_count = db.session.query(EmailTemplate).delete(synchronize_session=False)
            db.session.commit()
            # Odśwież sesję, aby upewnić się, że cache SQLAlchemy jest czysty
            db.session.expire_all()
            logging.info(f"Usunięto {deleted_count} istniejących szablonów")
            
            # Sprawdź czy wszystkie szablony zostały usunięte
            remaining = EmailTemplate.query.count()
            if remaining > 0:
                logging.warning(f"Ostrzeżenie: {remaining} szablonów nadal istnieje po usunięciu")
                # Wymuś usunięcie pozostałych szablonów
                EmailTemplate.query.delete()
                db.session.commit()
                db.session.expire_all()
            
            # Teraz załaduj fixtures - to utworzy nowe szablony domyślne
            from app.services.fixture_loader import load_email_templates_fixtures
            success, message = load_email_templates_fixtures(force_update=False)
            if not success:
                logging.error(f"Nie udało się załadować fixtures: {message}")
                return False, f"Nie udało się załadować fixtures: {message}"
            
            # Sprawdź ile szablonów zostało utworzonych
            created_templates = EmailTemplate.query.filter_by(is_default=True, is_active=True).all()
            logging.info(f"Utworzono {len(created_templates)} nowych domyślnych szablonów z fixtures")
            
            return True, f"Zresetowano do {len(created_templates)} domyślnych szablonów"
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Błąd resetowania szablonów: {str(e)}")
            return False, f"Błąd resetowania: {str(e)}"
    
    def set_template_as_default(self, template_id):
        """Oznacza szablon jako domyślny"""
        try:
            template = EmailTemplate.query.get(template_id)
            if not template:
                return False, "Szablon nie istnieje"
            
            template.is_default = True
            db.session.commit()
            
            # Dodaj/aktualizuj w tabeli domyślnych
            default_template = DefaultEmailTemplate.query.filter_by(name=template.name).first()
            if not default_template:
                default_template = DefaultEmailTemplate(name=template.name)
                db.session.add(default_template)
            
            default_template.template_type = template.template_type or 'custom'
            default_template.subject = template.subject
            default_template.html_content = template.html_content
            default_template.text_content = template.text_content
            default_template.variables = template.variables
            default_template.description = template.description
            default_template.is_active = template.is_active
            default_template.updated_at = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now()
            
            db.session.commit()
            return True, f"Szablon '{template.name}' oznaczono jako domyślny"
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Błąd ustawiania szablonu jako domyślnego: {str(e)}")
            return False, f"Błąd: {str(e)}"
    
    def remove_template_from_defaults(self, template_id):
        """Usuwa szablon z domyślnych"""
        try:
            template = EmailTemplate.query.get(template_id)
            if not template:
                return False, "Szablon nie istnieje"
            
            template.is_default = False
            db.session.commit()
            
            # Usuń z tabeli domyślnych
            default_template = DefaultEmailTemplate.query.filter_by(name=template.name).first()
            if default_template:
                db.session.delete(default_template)
                db.session.commit()
                return True, f"Szablon '{template.name}' usunięto z domyślnych"
            
            return True, f"Szablon '{template.name}' nie był w domyślnych"
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Błąd usuwania szablonu z domyślnych: {str(e)}")
            return False, f"Błąd: {str(e)}"
    
    def add_default_template(self, name, template_type, subject, html_content, text_content, variables, description):
        """Dodaje nowy domyślny szablon do bazy danych"""
        try:
            # Sprawdź czy już istnieje
            existing = DefaultEmailTemplate.query.filter_by(name=name).first()
            if existing:
                return False, f"Szablon '{name}' już istnieje"
            
            # Dodaj do tabeli domyślnych
            default_template = DefaultEmailTemplate(
                name=name,
                template_type=template_type,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                variables=json.dumps(variables) if isinstance(variables, dict) else variables,
                description=description,
                is_active=True
            )
            db.session.add(default_template)
            db.session.commit()
            
            return True, f"Szablon '{name}' dodano jako domyślny"
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Błąd dodawania domyślnego szablonu: {str(e)}")
            return False, f"Błąd: {str(e)}"
    
    def update_default_template(self, name, **kwargs):
        """Aktualizuje domyślny szablon w bazie danych"""
        try:
            default_template = DefaultEmailTemplate.query.filter_by(name=name).first()
            if not default_template:
                return False, f"Szablon '{name}' nie istnieje"
            
            for key, value in kwargs.items():
                if hasattr(default_template, key):
                    if key == 'variables' and isinstance(value, dict):
                        setattr(default_template, key, json.dumps(value))
                    else:
                        setattr(default_template, key, value)
            
            default_template.updated_at = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now()
            db.session.commit()
            
            return True, f"Szablon '{name}' zaktualizowano"
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Błąd aktualizacji domyślnego szablonu: {str(e)}")
            return False, f"Błąd: {str(e)}"
    
    def delete_default_template(self, name):
        """Usuwa domyślny szablon z bazy danych"""
        try:
            default_template = DefaultEmailTemplate.query.filter_by(name=name).first()
            if not default_template:
                return False, f"Szablon '{name}' nie istnieje"
            
            db.session.delete(default_template)
            db.session.commit()
            
            return True, f"Szablon '{name}' usunięto"
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Błąd usuwania domyślnego szablonu: {str(e)}")
            return False, f"Błąd: {str(e)}"
    
    def save_current_templates_as_defaults(self):
        """Zapisuje obecne szablony jako domyślne wzory"""
        try:
            # Pobierz wszystkie aktywne szablony
            current_templates = EmailTemplate.query.filter_by(is_active=True).all()
            
            if not current_templates:
                return False, "Brak aktywnych szablonów do zapisania"
            
            # Usuń wszystkie istniejące domyślne szablony
            DefaultEmailTemplate.query.delete()
            db.session.commit()
            
            saved_count = 0
            
            for template in current_templates:
                # Utwórz nowy domyślny szablon
                default_template = DefaultEmailTemplate(
                    name=template.name,
                    template_type=template.template_type,
                    subject=template.subject,
                    html_content=template.html_content,
                    text_content=template.text_content,
                    variables=template.variables,
                    description=template.description or f"Domyślny szablon {template.name}",
                    is_active=True
                )
                db.session.add(default_template)
                saved_count += 1
            
            db.session.commit()
            
            return True, f"Zapisano {saved_count} szablonów jako domyślne wzory"
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Błąd zapisywania szablonów jako domyślne: {str(e)}")
            return False, f"Błąd: {str(e)}"