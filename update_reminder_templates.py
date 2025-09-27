#!/usr/bin/env python3
"""
Skrypt do aktualizacji szablonów przypomnień o wydarzeniach.
Dodaje zmienną {{event_url}} i przycisk do szablonów.
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


def create_reminder_template_content(reminder_type, css_content):
    """Tworzy zawartość szablonu przypomnienia"""
    
    # Różne kolory dla różnych typów przypomnień
    if reminder_type == '24h':
        header_color = '#1e3a8a'  # Niebieski
        button_color = '#1e3a8a'
        icon = '📅'
        urgency_text = 'Wydarzenie już jutro!'
    elif reminder_type == '1h':
        header_color = '#dc2626'  # Czerwony
        button_color = '#dc2626'
        icon = '🚨'
        urgency_text = 'Wydarzenie za 1 godzinę!'
    elif reminder_type == '5min':
        header_color = '#dc2626'  # Czerwony
        button_color = '#dc2626'
        icon = '⚡'
        urgency_text = 'Wydarzenie za 5 minut!'
    else:
        header_color = '#1e3a8a'
        button_color = '#1e3a8a'
        icon = '📅'
        urgency_text = 'Przypomnienie o wydarzeniu'
    
    html_content = f"""<style>
{css_content}
</style>

<div class="email-container">
    <div class="header" style="background-color: {header_color};">
        <h1>{icon} Przypomnienie o wydarzeniu</h1>
    </div>
    
    <div class="content">
        <h2>Cześć {{{{user_name}}}}!</h2>
        
        <p>Chcemy przypomnieć Ci o nadchodzącym wydarzeniu:</p>
        
        <div class="event-details">
            <h4>📅 Szczegóły wydarzenia:</h4>
            <div class="detail-row">
                <span class="detail-label">Tytuł:</span>
                <span class="detail-value">{{{{event_title}}}}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Data:</span>
                <span class="detail-value">{{{{event_date}}}}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Godzina:</span>
                <span class="detail-value">{{{{event_time}}}}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Lokalizacja:</span>
                <span class="detail-value">{{{{event_location}}}}</span>
            </div>
        </div>
        
        <div class="highlight-box">
            <p><strong>{urgency_text}</strong></p>
            <p>Nie zapomnij dołączyć do naszego spotkania!</p>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{{{event_url}}}}" class="button" style="background-color: {button_color}; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                🎯 Dołącz do wydarzenia
            </a>
        </div>
        
        <p>Jeśli masz pytania, skontaktuj się z nami.</p>
        
        <p>Pozdrawiamy,<br>
        Zespół Klub Lepsze Życie</p>
    </div>
    
    <div class="footer">
        <p>To jest automatyczne przypomnienie o wydarzeniu.</p>
        <div class="unsubscribe-links">
            <a href="{{{{unsubscribe_url}}}}">Wypisz się z powiadomień</a> |
            <a href="{{{{delete_account_url}}}}">Usuń konto</a>
        </div>
    </div>
</div>"""

    return html_content


def update_reminder_templates():
    """Aktualizuje szablony przypomnień o wydarzeniach"""
    
    app = create_app()
    with app.app_context():
        print('🎨 Aktualizowanie szablonów przypomnień o wydarzeniach...')
        
        # Załaduj style CSS
        css_content = load_css_styles()
        if not css_content:
            print('❌ Nie udało się załadować stylów CSS')
            return
        
        print('✅ Załadowano style CSS')
        
        # Lista szablonów do aktualizacji
        reminder_types = ['24h', '1h', '5min']
        updated_count = 0
        
        for reminder_type in reminder_types:
            template_name = f'event_reminder_{reminder_type}'
            
            # Znajdź szablon
            template = EmailTemplate.query.filter_by(name=template_name).first()
            
            if not template:
                print(f'❌ Szablon {template_name} nie znaleziony')
                continue
            
            print(f'📝 Aktualizuję szablon: {template_name}')
            
            # Utwórz nową zawartość
            new_html_content = create_reminder_template_content(reminder_type, css_content)
            
            # Aktualizuj szablon
            template.html_content = new_html_content
            template.updated_at = db.func.now()
            
            # Aktualizuj temat jeśli potrzebny
            if reminder_type == '24h':
                template.subject = 'Przypomnienie: {{event_title}} już jutro! 📅'
            elif reminder_type == '1h':
                template.subject = 'Przypomnienie: {{event_title}} za 1 godzinę! 🚨'
            elif reminder_type == '5min':
                template.subject = 'Przypomnienie: {{event_title}} za 5 minut! ⚡'
            
            updated_count += 1
            print(f'   - ✅ Zaktualizowano szablon {template_name}')
        
        # Zatwierdź zmiany
        db.session.commit()
        
        print(f'✅ Pomyślnie zaktualizowano {updated_count} szablonów przypomnień!')
        print('🎉 Wszystkie szablony mają teraz zmienną {{event_url}} i przycisk.')


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
                
                print(f'   - {{event_url}}: {has_event_url}')
                print(f'   - {{user_name}}: {has_user_name}')
                print(f'   - {{event_title}}: {has_event_title}')
                print(f'   - {{event_date}}: {has_event_date}')
                print(f'   - {{event_time}}: {has_event_time}')
                print(f'   - {{event_location}}: {has_event_location}')
                print(f'   - {{unsubscribe_url}}: {has_unsubscribe_url}')
                print(f'   - {{delete_account_url}}: {has_delete_account_url}')
                
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
        elif sys.argv[1] == 'update':
            update_reminder_templates()
        else:
            print('❌ Nieznana komenda.')
            print('Dostępne komendy:')
            print('  - python update_reminder_templates.py check    # Sprawdza szablony')
            print('  - python update_reminder_templates.py update  # Aktualizuje szablony')
    else:
        check_reminder_templates()
