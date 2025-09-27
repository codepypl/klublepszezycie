# Instrukcje aktualizacji szablonów e-mail na produkcji

## Krok 1: Przejdź do katalogu projektu
```bash
cd /apps/klublepszezycie
```

## Krok 2: Aktywuj środowisko wirtualne
```bash
source .venv/bin/activate
```

## Krok 3: Uruchom skrypt aktualizacji
```bash
uv run update_templates_klub_style.py
```

## Co robi skrypt:
1. ✅ Wczytuje style CSS z `static/css/email_templates_klub.css`
2. ✅ Aktualizuje wszystkie aktywne szablony e-mail
3. ✅ Dodaje nowy wygląd zgodny ze stroną klublepszezycie.pl
4. ✅ Zapewnia poprawne linki unsubscribe/delete account
5. ✅ Zastępuje starą stylistykę nową

## Sprawdzenie po aktualizacji:
```bash
uv run python -c "
from app import create_app
from app.models import EmailTemplate

app = create_app()
with app.app_context():
    templates = EmailTemplate.query.filter_by(is_active=True).all()
    print(f'✅ Zaktualizowano {len(templates)} szablonów')
    for template in templates:
        print(f'   - {template.name}: {template.subject}')
"
```

## Test wysyłania e-maila:
```bash
uv run send_test_email.py event_reminder_1h codeitpy@gmail.com
```

## Uwagi:
- Skrypt aktualizuje tylko aktywne szablony (`is_active=True`)
- Nie usuwa istniejących szablonów
- Zachowuje wszystkie zmienne szablonu
- Dodaje nowe style CSS inline do każdego szablonu
