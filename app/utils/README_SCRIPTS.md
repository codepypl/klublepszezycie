# Skrypty narzędziowe dla systemu emaili

## 1. check_email_status.py
Sprawdza kto otrzymał email z danego szablonu dla danego wydarzenia.

### Użycie:
```bash
python app/utils/check_email_status.py <template_id> <event_id>
```

### Przykład:
```bash
python app/utils/check_email_status.py 502 61
```

### Funkcje:
- ✅ Sprawdza szablon i wydarzenie
- ✅ Listuje członków klubu
- ✅ Pokazuje kto otrzymał email
- ✅ Pokazuje kto NIE otrzymał email
- ✅ Sprawdza kolejkę emaili
- ✅ Wyświetla statystyki

---

## 2. send_manual_emails.py
Wysyła emaile ręcznie do określonych użytkowników.

### Użycie:
```bash
python app/utils/send_manual_emails.py <template_id> <user_id1> [user_id2] ... [event_id]
```

### Przykłady:
```bash
# Wysłać do użytkowników 1, 2, 3, 4 z szablonu 502
python app/utils/send_manual_emails.py 502 1 2 3 4

# Wysłać do użytkowników 1, 2, 3, 4 z szablonu 502 dla wydarzenia 61
python app/utils/send_manual_emails.py 502 1 2 3 4 61

# Wysłać do użytkowników z listy (oddzielone przecinkami)
python app/utils/send_manual_emails.py 502 1,2,3,4 61
```

### Funkcje:
- ✅ Sprawdza szablon
- ✅ Pobiera użytkowników po ID
- ✅ Dodaje kontekst wydarzenia (opcjonalnie)
- ✅ Wysyła emaile przez kolejkę
- ✅ Pokazuje statystyki wysyłania

---

## 3. restart_celery.py
Restartuje Celery - czyści kolejkę, wyłącza, usuwa bazę i włącza ponownie.

### Użycie:
```bash
python app/utils/restart_celery.py
```

### Funkcje:
- ✅ Czyści kolejkę emaili w bazie danych
- ✅ Zatrzymuje wszystkie procesy Celery
- ✅ Czyści bazę danych Celery (Redis)
- ✅ Uruchamia procesy Celery ponownie
- ✅ Weryfikuje status po restarcie
- ✅ Wymaga potwierdzenia przed wykonaniem

### ⚠️ UWAGA:
Ten skrypt zatrzyma wszystkie procesy Celery i wyczyści kolejkę!
Upewnij się, że nie ma ważnych zadań w trakcie wykonywania.

---

## Przykłady użycia w praktyce:

### Sprawdzenie statusu emaili:
```bash
# Sprawdź kto otrzymał pierwszy reminder (24h) dla wydarzenia 61
python app/utils/check_email_status.py 502 61

# Sprawdź kto otrzymał drugi reminder (1h) dla wydarzenia 61
python app/utils/check_email_status.py 503 61
```

### Wysłanie brakujących emaili:
```bash
# Wyślij do użytkowników którzy nie otrzymali maila
python app/utils/send_manual_emails.py 502 1,2,3,4,5 61
```

### Restart Celery w przypadku problemów:
```bash
# Pełny restart Celery
python app/utils/restart_celery.py
```

---

## Wymagania:
- Python 3.7+
- Dostęp do bazy danych aplikacji
- Dostęp do Redis (dla restart_celery.py)
- Uprawnienia do zarządzania procesami (dla restart_celery.py)

## Bezpieczeństwo:
- Wszystkie skrypty wymagają uruchomienia z poziomu katalogu głównego aplikacji
- `restart_celery.py` wymaga potwierdzenia przed wykonaniem
- Skrypty logują wszystkie operacje
- Błędy są wyświetlane z opisem problemu
