#!/usr/bin/env python3
"""
Skrypt do naprawy szablonów przypomnień o wydarzeniach.
Dodaje tylko brakującą zmienną {{event_url}} do istniejących szablonów.
"""

from app import create_app
from app.models import db, EmailTemplate
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


def fix_reminder_templates():
    """Naprawia szablony przypomnień o wydarzeniach"""
    
    app = create_app()
    with app.app_context():
        print('🔧 Naprawianie szablonów przypomnień o wydarzeniach...')
        
        # Załaduj style CSS
        css_content = load_css_styles()
        if css_content:
            print('✅ Załadowano style CSS')
        else:
            print('⚠️ Nie udało się załadować stylów CSS')
        
        # Lista szablonów do naprawy
        reminder_types = ['24h', '1h', '5min']
        updated_count = 0
        
        for reminder_type in reminder_types:
            template_name = f'event_reminder_{reminder_type}'
            
            # Znajdź szablon
            template = EmailTemplate.query.filter_by(name=template_name).first()
            
            if not template:
                print(f'❌ Szablon {template_name} nie znaleziony')
                continue
            
            print(f'📝 Naprawiam szablon: {template_name}')
            
            # Pobierz obecną zawartość
            current_html = template.html_content
            
            # Dodaj style CSS jeśli brakuje
            if css_content:
                current_html = add_css_styles_to_template(current_html, css_content)
            
            # Dodaj {{event_url}} jeśli brakuje
            current_html = add_event_url_to_template(current_html, reminder_type)
            
            # Sprawdź czy coś się zmieniło
            if current_html != template.html_content:
                # Aktualizuj szablon
                template.html_content = current_html
                template.updated_at = db.func.now()
                updated_count += 1
                print(f'   - ✅ Zaktualizowano szablon {template_name}')
            else:
                print(f'   - ⏭️ Szablon {template_name} nie wymagał zmian')
        
        # Zatwierdź zmiany
        if updated_count > 0:
            db.session.commit()
            print(f'✅ Pomyślnie zaktualizowano {updated_count} szablonów!')
        else:
            print('ℹ️ Żaden szablon nie wymagał aktualizacji')


def check_reminder_templates():
    """Sprawdza szablony przypomnień"""
    
    app = create_app()
    with app.app_context():
        print('🔍 Sprawdzanie szablonów przypomnień...')
        
        reminder_types = ['24h', '1h', '5min']
        
        for reminder_type in reminder_types:
            template_name = f'event_reminder_{reminder_type}'
            
            template = EmailTemplate.query.filter_by(name=template_name).first()
            
            if template:
                print(f'\\n📋 {template_name}:')
                print(f'   - ID: {template.id}')
                print(f'   - Temat: {template.subject}')
                print(f'   - Aktywny: {template.is_active}')
                
                # Sprawdź zmienne
                has_event_url = '{{event_url}}' in template.html_content
                has_user_name = '{{user_name}}' in template.html_content
                has_event_title = '{{event_title}}' in template.html_content
                has_event_date = '{{event_date}}' in template.html_content
                has_event_time = '{{event_time}}' in template.html_content
                has_event_location = '{{event_location}}' in template.html_content
                has_unsubscribe_url = '{{unsubscribe_url}}' in template.html_content
                has_delete_account_url = '{{delete_account_url}}' in template.html_content
                has_styles = '<style>' in template.html_content
                
                print(f'   - {{event_url}}: {has_event_url}')
                print(f'   - {{user_name}}: {has_user_name}')
                print(f'   - {{event_title}}: {has_event_title}')
                print(f'   - {{event_date}}: {has_event_date}')
                print(f'   - {{event_time}}: {has_event_time}')
                print(f'   - {{event_location}}: {has_event_location}')
                print(f'   - {{unsubscribe_url}}: {has_unsubscribe_url}')
                print(f'   - {{delete_account_url}}: {has_delete_account_url}')
                print(f'   - Style CSS: {has_styles}')
                
                if has_event_url and has_user_name and has_event_title:
                    print(f'   - ✅ Szablon ma wszystkie wymagane zmienne')
                else:
                    print(f'   - ❌ Szablon nie ma wszystkich wymaganych zmiennych')
            else:
                print(f'❌ Szablon {template_name} nie znaleziony')


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'check':
            check_reminder_templates()
        elif sys.argv[1] == 'fix':
            fix_reminder_templates()
        else:
            print('❌ Nieznana komenda.')
            print('Dostępne komendy:')
            print('  - python fix_reminder_templates.py check    # Sprawdza szablony')
            print('  - python fix_reminder_templates.py fix     # Naprawia szablony')
    else:
        check_reminder_templates()
