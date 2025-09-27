#!/usr/bin/env python3
"""
Skrypt do zapisania aktualnych szablonów jako domyślne.
Uruchom po ręcznej edycji szablonów.
"""

from app import create_app, db
from app.models.email_model import EmailTemplate, DefaultEmailTemplate
import json
import datetime
import os


def load_css_styles():
    """Ładuje style CSS z pliku static/css/email_templates.css"""
    css_file = os.path.join(os.path.dirname(__file__), 'static', 'css', 'email_templates.css')
    
    try:
        with open(css_file, 'r', encoding='utf-8') as f:
            css_content = f.read()
        return css_content
    except FileNotFoundError:
        print(f'⚠️ Nie znaleziono pliku CSS: {css_file}')
        return None
    except Exception as e:
        print(f'❌ Błąd odczytu pliku CSS: {e}')
        return None


def apply_styles_to_template(html_content, css_content):
    """Dodaje style CSS do szablonu HTML"""
    if not css_content:
        return html_content
    
    # Sprawdź czy szablon już ma style
    if '<style>' in html_content:
        print('   - Szablon już ma style, pomijam dodawanie')
        return html_content
    
    # Dodaj style na początku szablonu
    styled_content = f"""<style>
{css_content}
</style>

{html_content}"""
    
    return styled_content


def ensure_reminder_template_variables(html_content, template_name):
    """Sprawdza i dodaje brakujące zmienne do szablonów przypomnień"""
    
    # Sprawdź czy to szablon przypomnienia
    if not template_name.startswith('event_reminder_'):
        return html_content
    
    # Wymagane zmienne dla szablonów przypomnień
    required_variables = [
        '{{event_url}}',
        '{{user_name}}',
        '{{event_title}}',
        '{{event_date}}',
        '{{event_time}}',
        '{{event_location}}',
        '{{unsubscribe_url}}',
        '{{delete_account_url}}'
    ]
    
    missing_variables = []
    for variable in required_variables:
        if variable not in html_content:
            missing_variables.append(variable)
    
    if missing_variables:
        print(f'   - ⚠️ Brakujące zmienne: {", ".join(missing_variables)}')
        # Nie modyfikujemy automatycznie - tylko informujemy
        return html_content
    else:
        print(f'   - ✅ Wszystkie wymagane zmienne są obecne')
        return html_content


def save_templates_as_default():
    """Zapisuje wszystkie aktualne szablony jako domyślne"""
    
    app = create_app()
    with app.app_context():
        print('💾 Zapisywanie szablonów jako domyślne...')
        
        # Załaduj style CSS
        css_content = load_css_styles()
        if css_content:
            print('✅ Załadowano style CSS')
        else:
            print('⚠️ Nie udało się załadować stylów CSS')
        
        # Pobierz wszystkie szablony
        templates = EmailTemplate.query.all()
        
        if not templates:
            print('❌ Nie znaleziono szablonów do zapisania.')
            return
        
        backup_data = {}
        updated_count = 0
        
        for template in templates:
            print(f'📝 Aktualizuję szablon: {template.name}')
            
            # Backup obecnego domyślnego szablonu
            default_template = DefaultEmailTemplate.query.filter_by(name=template.name).first()
            if default_template:
                backup_data[template.name] = {
                    'subject': default_template.subject,
                    'html_content': default_template.html_content,
                    'text_content': default_template.text_content,
                    'updated_at': default_template.updated_at.isoformat() if default_template.updated_at else None
                }
            
            # Aktualizuj lub utwórz domyślny szablon
            if not default_template:
                default_template = DefaultEmailTemplate(name=template.name)
                db.session.add(default_template)
            
            # Zastosuj style do szablonu HTML
            styled_html_content = apply_styles_to_template(template.html_content, css_content)
            
            # Sprawdź zmienne w szablonach przypomnień
            styled_html_content = ensure_reminder_template_variables(styled_html_content, template.name)
            
            default_template.subject = template.subject
            default_template.html_content = styled_html_content
            default_template.text_content = template.text_content
            default_template.updated_at = db.func.now()
            
            updated_count += 1
        
        # Zatwierdź zmiany
        db.session.commit()
        
        # Zapisz backup poprzednich domyślnych szablonów
        if backup_data:
            backup_filename = f'default_templates_backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(backup_filename, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            print(f'📦 Backup poprzednich domyślnych szablonów: {backup_filename}')
        
        print(f'✅ Pomyślnie zaktualizowano {updated_count} domyślnych szablonów!')
        print('🎉 Szablony zostały zapisane jako domyślne i będą przywracane przy resetowaniu.')


def update_templates_with_styles():
    """Aktualizuje wszystkie szablony w bazie danych, dodając style CSS"""
    
    app = create_app()
    with app.app_context():
        print('🎨 Aktualizowanie szablonów ze stylami CSS...')
        
        # Załaduj style CSS
        css_content = load_css_styles()
        if not css_content:
            print('❌ Nie udało się załadować stylów CSS')
            return
        
        print('✅ Załadowano style CSS')
        
        # Pobierz wszystkie szablony
        templates = EmailTemplate.query.all()
        
        if not templates:
            print('❌ Nie znaleziono szablonów do aktualizacji.')
            return
        
        updated_count = 0
        
        for template in templates:
            print(f'📝 Sprawdzam szablon: {template.name}')
            
            # Sprawdź czy szablon już ma style
            if '<style>' in template.html_content:
                print('   - Szablon już ma style, pomijam')
                continue
            
            # Zastosuj style do szablonu HTML
            styled_html_content = apply_styles_to_template(template.html_content, css_content)
            
            # Sprawdź zmienne w szablonach przypomnień
            styled_html_content = ensure_reminder_template_variables(styled_html_content, template.name)
            
            # Aktualizuj szablon w bazie danych
            template.html_content = styled_html_content
            template.updated_at = db.func.now()
            
            updated_count += 1
            print('   - ✅ Dodano style do szablonu')
        
        # Zatwierdź zmiany
        db.session.commit()
        
        print(f'✅ Pomyślnie zaktualizowano {updated_count} szablonów ze stylami!')
        print('🎉 Wszystkie szablony mają teraz style CSS.')


def restore_templates_from_backup(backup_file):
    """Przywraca szablony z pliku backup"""
    
    app = create_app()
    with app.app_context():
        print(f'🔄 Przywracanie szablonów z backup: {backup_file}')
        
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            restored_count = 0
            
            for template_name, template_data in backup_data.items():
                print(f'📝 Przywracam szablon: {template_name}')
                
                # Przywróć domyślny szablon
                default_template = DefaultEmailTemplate.query.filter_by(name=template_name).first()
                if not default_template:
                    default_template = DefaultEmailTemplate(name=template_name)
                    db.session.add(default_template)
                
                default_template.subject = template_data['subject']
                default_template.html_content = template_data['html_content']
                default_template.text_content = template_data['text_content']
                default_template.updated_at = datetime.datetime.fromisoformat(template_data['updated_at']) if template_data['updated_at'] else None
                
                restored_count += 1
            
            db.session.commit()
            print(f'✅ Pomyślnie przywrócono {restored_count} szablonów!')
            
        except FileNotFoundError:
            print(f'❌ Nie znaleziono pliku backup: {backup_file}')
        except json.JSONDecodeError:
            print(f'❌ Błąd odczytu pliku backup: {backup_file}')
        except Exception as e:
            print(f'❌ Błąd podczas przywracania: {e}')


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'restore':
            if len(sys.argv) > 2:
                restore_templates_from_backup(sys.argv[2])
            else:
                print('❌ Podaj ścieżkę do pliku backup.')
                print('Użycie: python save_templates_as_default.py restore backup_file.json')
        elif sys.argv[1] == 'update-styles':
            update_templates_with_styles()
        elif sys.argv[1] == 'save-defaults':
            save_templates_as_default()
        else:
            print('❌ Nieznana komenda.')
            print('Dostępne komendy:')
            print('  - python save_templates_as_default.py                    # Zapisuje szablony jako domyślne ze stylami')
            print('  - python save_templates_as_default.py save-defaults     # Zapisuje szablony jako domyślne ze stylami')
            print('  - python save_templates_as_default.py update-styles     # Aktualizuje szablony w bazie ze stylami')
            print('  - python save_templates_as_default.py restore backup.json # Przywraca szablony z backup')
    else:
        save_templates_as_default()

