"""
Template Manager - zarządzanie szablonami emaili z bazy danych
"""
import json
import logging
from datetime import datetime
from app.models import db, EmailTemplate, DefaultEmailTemplate

class TemplateManager:
    """Menedżer szablonów emaili - używa bazy danych jako źródła prawdy"""
    
    def get_default_templates(self):
        """Pobiera domyślne szablony z bazy danych"""
        try:
            return DefaultEmailTemplate.query.filter_by(is_active=True).all()
        except Exception as e:
            logging.error(f"Błąd pobierania domyślnych szablonów: {str(e)}")
            return []
    
    def sync_templates_from_defaults(self):
        """Synchronizuje szablony z domyślnych w bazie danych"""
        try:
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
                    existing.updated_at = datetime.utcnow()
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
            # Najpierw usuń referencje w tabelach, które używają template_id
            from app.models import EmailLog, EmailQueue, EmailCampaign
            
            # Ustaw template_id na NULL we wszystkich tabelach
            EmailLog.query.filter(EmailLog.template_id.isnot(None)).update({'template_id': None})
            EmailQueue.query.filter(EmailQueue.template_id.isnot(None)).update({'template_id': None})
            EmailCampaign.query.filter(EmailCampaign.template_id.isnot(None)).update({'template_id': None})
            db.session.commit()
            
            # Usuń wszystkie istniejące szablony
            EmailTemplate.query.delete()
            db.session.commit()
            
            # Dodaj domyślne szablony z bazy
            default_templates = self.get_default_templates()
            
            for default_template in default_templates:
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
            
            db.session.commit()
            return True, f"Zresetowano do {len(default_templates)} domyślnych szablonów"
            
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
            default_template.updated_at = datetime.utcnow()
            
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
            
            default_template.updated_at = datetime.utcnow()
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