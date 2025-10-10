"""
Flask Fixture Loader - podobny do Django fixtures
"""
import yaml
import os
import logging
from app.models import db, EmailTemplate

class FixtureLoader:
    """Loader dla fixtures w formacie YAML (podobny do Django)"""
    
    def __init__(self, fixtures_dir='app/fixtures'):
        self.fixtures_dir = fixtures_dir
    
    def load_fixtures(self, fixture_file, force_update=False):
        """Ładuje fixtures z pliku YAML"""
        try:
            fixture_path = os.path.join(self.fixtures_dir, fixture_file)
            
            if not os.path.exists(fixture_path):
                logging.error(f"Plik fixture nie istnieje: {fixture_path}")
                return False, f"Plik fixture nie istnieje: {fixture_path}"
            
            with open(fixture_path, 'r', encoding='utf-8') as f:
                fixtures = yaml.safe_load(f)
            
            if not fixtures:
                logging.warning(f"Plik fixture jest pusty: {fixture_path}")
                return False, f"Plik fixture jest pusty: {fixture_path}"
            
            loaded_count = 0
            updated_count = 0
            skipped_count = 0
            
            for fixture in fixtures:
                model_name = fixture.get('model')
                fields = fixture.get('fields', {})
                
                # DefaultEmailTemplate jest legacy - teraz używamy EmailTemplate
                if model_name == 'DefaultEmailTemplate' or model_name == 'EmailTemplate':
                    success = self._load_email_template(fields, force_update=force_update)
                    if success:
                        if force_update and EmailTemplate.query.filter_by(name=fields.get('name')).first():
                            updated_count += 1
                        else:
                            loaded_count += 1
                    else:
                        skipped_count += 1
                else:
                    logging.warning(f"Nieznany model: {model_name}")
                    skipped_count += 1
            
            if force_update:
                logging.info(f"Zaktualizowano {updated_count} fixtures, załadowano {loaded_count}, pominięto {skipped_count}")
                return True, f"Zaktualizowano {updated_count} fixtures, załadowano {loaded_count}, pominięto {skipped_count}"
            else:
                logging.info(f"Załadowano {loaded_count} fixtures, pominięto {skipped_count}")
                return True, f"Załadowano {loaded_count} fixtures, pominięto {skipped_count}"
            
        except Exception as e:
            logging.error(f"Błąd ładowania fixtures: {str(e)}")
            return False, f"Błąd ładowania fixtures: {str(e)}"
    
    def _load_email_template(self, fields, force_update=False):
        """Ładuje szablon email z fixture"""
        try:
            name = fields.get('name')
            if not name:
                logging.error("Brak nazwy szablonu w fixture")
                return False
            
            # Sprawdź czy szablon już istnieje w EmailTemplate
            existing = EmailTemplate.query.filter_by(name=name).first()
            if existing and not force_update:
                logging.info(f"Szablon {name} już istnieje, pomijam")
                return False
            
            if existing and force_update:
                # Aktualizuj istniejący szablon
                existing.template_type = fields.get('template_type', 'html')
                existing.subject = fields.get('subject', '')
                existing.html_content = fields.get('html_content', '')
                existing.text_content = fields.get('text_content', '')
                existing.variables = fields.get('variables', '{}')
                existing.description = fields.get('description', '')
                existing.is_active = fields.get('is_active', True)
                existing.is_default = True  # Szablony z fixtures są domyślne/systemowe
                
                db.session.commit()
                logging.info(f"Zaktualizowano szablon: {name}")
                return True
            else:
                # Utwórz nowy szablon w EmailTemplate
                template = EmailTemplate(
                    name=name,
                    template_type=fields.get('template_type', 'html'),
                    subject=fields.get('subject', ''),
                    html_content=fields.get('html_content', ''),
                    text_content=fields.get('text_content', ''),
                    variables=fields.get('variables', '{}'),
                    description=fields.get('description', ''),
                    is_active=fields.get('is_active', True),
                    is_default=True  # Szablony z fixtures są domyślne/systemowe
                )
                
                db.session.add(template)
                db.session.commit()
                
                logging.info(f"Załadowano szablon: {name}")
                return True
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Błąd ładowania szablonu {fields.get('name', 'unknown')}: {str(e)}")
            return False
    
    def load_all_fixtures(self):
        """Ładuje wszystkie pliki fixtures z katalogu"""
        try:
            if not os.path.exists(self.fixtures_dir):
                logging.warning(f"Katalog fixtures nie istnieje: {self.fixtures_dir}")
                return False, f"Katalog fixtures nie istnieje: {self.fixtures_dir}"
            
            total_loaded = 0
            total_skipped = 0
            
            for filename in os.listdir(self.fixtures_dir):
                if filename.endswith(('.yaml', '.yml')):
                    success, message = self.load_fixtures(filename)
                    if success:
                        # Parsuj message aby wyciągnąć liczby
                        if "Załadowano" in message:
                            loaded = int(message.split("Załadowano ")[1].split(" fixtures")[0])
                            total_loaded += loaded
                        if "pominięto" in message:
                            skipped = int(message.split("pominięto ")[1].split()[0])
                            total_skipped += skipped
            
            return True, f"Łącznie załadowano {total_loaded} fixtures, pominięto {total_skipped}"
            
        except Exception as e:
            logging.error(f"Błąd ładowania wszystkich fixtures: {str(e)}")
            return False, f"Błąd ładowania wszystkich fixtures: {str(e)}"

def load_email_templates_fixtures(force_update=False):
    """Funkcja pomocnicza do ładowania szablonów email z fixtures"""
    loader = FixtureLoader()
    return loader.load_fixtures('email_templates_complete.yaml', force_update=force_update)

def load_all_fixtures():
    """Funkcja pomocnicza do ładowania wszystkich fixtures"""
    loader = FixtureLoader()
    return loader.load_all_fixtures()
