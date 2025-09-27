#!/usr/bin/env python3
"""
Skrypt do naprawy szablonów na serwerze produkcyjnym.
Dodaje event_url do variables i poprawia style.
"""

from app import create_app
from app.models import db, EmailTemplate
import json
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


def update_template_variables(template):
    """Aktualizuje zmienne szablonu, dodając event_url jeśli brakuje"""
    
    # Domyślne zmienne dla szablonów przypomnień
    default_variables = {
        "user_name": "Imię użytkownika",
        "event_title": "Tytuł wydarzenia", 
        "event_date": "Data wydarzenia",
        "event_time": "Godzina wydarzenia",
        "event_location": "Lokalizacja wydarzenia",
        "event_url": "Link do wydarzenia",
        "unsubscribe_url": "URL do wypisania się z klubu",
        "delete_account_url": "URL do usunięcia konta"
    }
    
    # Sprawdź czy to szablon przypomnienia
    if not template.name.startswith('event_reminder_'):
        return False
    
    # Pobierz obecne zmienne
    current_variables = {}
    if template.variables:
        try:
            current_variables = json.loads(template.variables) if isinstance(template.variables, str) else template.variables
        except:
            current_variables = {}
    
    # Sprawdź czy event_url jest w zmiennych
    if 'event_url' not in current_variables:
        print(f'   - ⚠️ Brak event_url w variables, dodaję...')
        
        # Dodaj brakujące zmienne
        for key, value in default_variables.items():
            if key not in current_variables:
                current_variables[key] = value
        
        # Zaktualizuj zmienne
        template.variables = json.dumps(current_variables, ensure_ascii=False)
        return True
    else:
        print(f'   - ✅ event_url już jest w variables')
        return False


def add_css_styles_to_template(html_content, css_content):
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
    
    print('   - Dodano style CSS')
    return styled_content


def add_event_url_to_template(html_content, reminder_type):
    """Dodaje zmienną {{event_url}} do szablonu HTML"""
    
    # Sprawdź czy już ma event_url
    if '{{event_url}}' in html_content:
        print('   - Szablon już ma {{event_url}}, pomijam')
        return html_content
    
    # Sprawdź czy ma przycisk lub link
    if '<a href=' in html_content:
        # Znajdź link i zamień href na {{event_url}}
        import re
        # Zamień href="#" na href="{{event_url}}"
        html_content = re.sub(r'href="[^"]*"', 'href="{{event_url}}"', html_content)
        print('   - Dodano {{event_url}} do istniejącego linku')
    else:
        # Dodaj przycisk z {{event_url}}
        button_html = '''
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{event_url}}" class="button" style="background-color: #1e3a8a; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                🎯 Dołącz do wydarzenia
            </a>
        </div>'''
        
        # Wstaw przycisk przed końcem content
        if '</div>' in html_content:
            # Znajdź ostatni </div> w content
            content_end = html_content.rfind('</div>')
            if content_end != -1:
                html_content = html_content[:content_end] + button_html + '\n    ' + html_content[content_end:]
                print('   - Dodano przycisk z {{event_url}}')
            else:
                html_content += button_html
                print('   - Dodano przycisk z {{event_url}} na końcu')
        else:
            html_content += button_html
            print('   - Dodano przycisk z {{event_url}} na końcu')
    
    return html_content


def fix_production_templates():
    """Naprawia szablony na serwerze produkcyjnym"""
    
    app = create_app()
    with app.app_context():
        print('🔧 Naprawianie szablonów na serwerze produkcyjnym...')
        
        # Załaduj style CSS
        css_content = load_css_styles()
        if css_content:
            print('✅ Załadowano style CSS')
        else:
            print('⚠️ Nie udało się załadować stylów CSS')
        
        # Pobierz szablony przypomnień
        reminder_templates = EmailTemplate.query.filter(
            EmailTemplate.name.like('event_reminder_%')
        ).all()
        
        if not reminder_templates:
            print('❌ Nie znaleziono szablonów przypomnień')
            return
        
        updated_count = 0
        
        for template in reminder_templates:
            print(f'\\n📝 Naprawiam szablon: {template.name}')
            
            template_updated = False
            
            # 1. Aktualizuj zmienne
            if update_template_variables(template):
                template_updated = True
            
            # 2. Dodaj style CSS
            if css_content:
                new_html = add_css_styles_to_template(template.html_content, css_content)
                if new_html != template.html_content:
                    template.html_content = new_html
                    template_updated = True
            
            # 3. Dodaj {{event_url}} do HTML
            reminder_type = template.name.replace('event_reminder_', '')
            new_html = add_event_url_to_template(template.html_content, reminder_type)
            if new_html != template.html_content:
                template.html_content = new_html
                template_updated = True
            
            if template_updated:
                template.updated_at = db.func.now()
                updated_count += 1
                print(f'   - ✅ Zaktualizowano szablon {template.name}')
            else:
                print(f'   - ⏭️ Szablon {template.name} nie wymagał zmian')
        
        # Zatwierdź zmiany
        if updated_count > 0:
            db.session.commit()
            print(f'\\n✅ Pomyślnie zaktualizowano {updated_count} szablonów!')
        else:
            print('\\nℹ️ Żaden szablon nie wymagał aktualizacji')


def check_production_templates():
    """Sprawdza szablony na serwerze produkcyjnym"""
    
    app = create_app()
    with app.app_context():
        print('🔍 Sprawdzanie szablonów na serwerze produkcyjnym...')
        
        reminder_templates = EmailTemplate.query.filter(
            EmailTemplate.name.like('event_reminder_%')
        ).all()
        
        for template in reminder_templates:
            print(f'\\n📋 {template.name}:')
            print(f'   - ID: {template.id}')
            print(f'   - Temat: {template.subject}')
            print(f'   - Aktywny: {template.is_active}')
            
            # Sprawdź zmienne
            has_event_url_in_variables = False
            if template.variables:
                try:
                    variables = json.loads(template.variables) if isinstance(template.variables, str) else template.variables
                    has_event_url_in_variables = 'event_url' in variables
                except:
                    pass
            
            has_event_url_in_html = '{{event_url}}' in template.html_content
            has_user_name = '{{user_name}}' in template.html_content
            has_event_title = '{{event_title}}' in template.html_content
            has_styles = '<style>' in template.html_content
            
            print(f'   - event_url w variables: {has_event_url_in_variables}')
            print(f'   - {{event_url}} w HTML: {has_event_url_in_html}')
            print(f'   - {{user_name}} w HTML: {has_user_name}')
            print(f'   - {{event_title}} w HTML: {has_event_title}')
            print(f'   - Style CSS: {has_styles}')
            
            if has_event_url_in_variables and has_event_url_in_html and has_user_name and has_event_title:
                print(f'   - ✅ Szablon jest poprawny')
            else:
                print(f'   - ❌ Szablon wymaga naprawy')


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'check':
            check_production_templates()
        elif sys.argv[1] == 'fix':
            fix_production_templates()
        else:
            print('❌ Nieznana komenda.')
            print('Dostępne komendy:')
            print('  - python fix_production_templates.py check    # Sprawdza szablony')
            print('  - python fix_production_templates.py fix     # Naprawia szablony')
    else:
        check_production_templates()
