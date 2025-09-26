#!/usr/bin/env python3
"""
Skrypt do zapisania aktualnych szablonów jako domyślne.
Uruchom po ręcznej edycji szablonów.
"""

from app import create_app, db
from app.models.email_model import EmailTemplate, DefaultEmailTemplate
import json
import datetime


def save_templates_as_default():
    """Zapisuje wszystkie aktualne szablony jako domyślne"""
    
    app = create_app()
    with app.app_context():
        print('💾 Zapisywanie szablonów jako domyślne...')
        
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
            
            default_template.subject = template.subject
            default_template.html_content = template.html_content
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
    
    if len(sys.argv) > 1 and sys.argv[1] == 'restore':
        if len(sys.argv) > 2:
            restore_templates_from_backup(sys.argv[2])
        else:
            print('❌ Podaj ścieżkę do pliku backup.')
            print('Użycie: python save_templates_as_default.py restore backup_file.json')
    else:
        save_templates_as_default()

