# Skrypt Resetu Systemu Emaili

## Opis
Skrypt `reset_email_system.py` służy do całkowitego resetowania systemu emaili w aplikacji Klub Lepsze Życie. Usuwa wszystkie istniejące harmonogramy i szablony emaili, a następnie tworzy je na nowo z domyślnymi ustawieniami.

## Funkcjonalności

### Co usuwa:
- ✅ Wszystkie harmonogramy emaili dla wydarzeń (`EventEmailSchedule`)
- ✅ Wszystkie szablony emaili (`EmailTemplate`)
- ✅ Wszystkie harmonogramy emaili (`EmailSchedule`)
- ✅ Wszystkie automatyzacje emaili (`EmailAutomation`)
- ✅ Wszystkie kampanie emaili (`EmailCampaign`)
- ✅ Wszystkie logi emaili (`EmailLog`)

### Co tworzy na nowo:
- ✅ Domyślne szablony emaili (7 typów)
- ✅ Harmonogramy emaili dla istniejących wydarzeń
- ✅ Automatyczne powiadomienia o wydarzeniach

## Szablony emaili

Skrypt tworzy następujące szablony:

1. **Email Powitalny** (`welcome`) - wysyłany nowym użytkownikom
2. **Przypomnienie o Wydarzeniu** (`reminder`) - ogólne przypomnienia
3. **Nowa osoba dołączyła do klubu** (`admin_notification`) - powiadomienia dla administratorów
4. **Przypomnienie 24h przed wydarzeniem** (`event_reminder_24h_before`)
5. **Przypomnienie 1h przed wydarzeniem** (`event_reminder_1h_before`)
6. **Link do spotkania 5min przed wydarzeniem** (`event_reminder_5min_before`)
7. **Potwierdzenie zapisu na wydarzenie** (`event_registration`)

## Użycie

### Uruchomienie skryptu:
```bash
cd /Volumes/Dane/Projekty/devs/klublepszezycie
source .venv/bin/activate
python reset_email_system.py
```

### Proces:
1. Skrypt wyświetli ostrzeżenie o usunięciu wszystkich danych emaili
2. Poprosi o potwierdzenie (wpisz `tak` aby kontynuować)
3. Usunie wszystkie dane emaili z bazy danych
4. Utworzy nowe domyślne szablony
5. Utworzy harmonogramy dla istniejących wydarzeń
6. Wyświetli podsumowanie operacji

### Przykład wyjścia:
```
🚀 Uruchamianie skryptu resetu systemu emaili...
⚠️  UWAGA: Ten skrypt usunie WSZYSTKIE dane emaili z systemu!

Czy na pewno chcesz kontynuować? (tak/nie): tak

🔄 Rozpoczynam reset systemu emaili...
==================================================
1. Usuwanie harmonogramów emaili dla wydarzeń...
   ✅ Usunięto 3 harmonogramów wydarzeń
2. Usuwanie szablonów emaili...
   ✅ Usunięto 7 szablonów emaili
3. Usuwanie harmonogramów emaili...
   ✅ Usunięto 0 harmonogramów emaili
4. Usuwanie automatyzacji emaili...
   ✅ Usunięto 0 automatyzacji emaili
5. Usuwanie kampanii emaili...
   ✅ Usunięto 0 kampanii emaili
6. Usuwanie logów emaili...
   ✅ Usunięto 0 logów emaili

🧹 Wszystkie dane emaili zostały usunięte!
==================================================
7. Tworzenie domyślnych szablonów emaili...
   ✅ Utworzono 7 szablonów emaili
8. Tworzenie harmonogramów dla istniejących wydarzeń...
   📅 Wydarzenie 'Test Event': 1 harmonogramów
   ✅ Utworzono łącznie 1 harmonogramów wydarzeń

🎉 Reset systemu emaili zakończony pomyślnie!
==================================================
✅ Wszystkie harmonogramy i szablony zostały odtworzone
```

## Bezpieczeństwo

- ⚠️ **UWAGA**: Skrypt usuwa WSZYSTKIE dane emaili z systemu
- ✅ Przed uruchomieniem wymaga potwierdzenia użytkownika
- ✅ W przypadku błędu wykonuje rollback transakcji
- ✅ Nie wpływa na inne dane systemu (użytkownicy, wydarzenia, itp.)

## Wymagania

- Python 3.13+
- Aktywne środowisko wirtualne (.venv)
- Dostęp do bazy danych PostgreSQL
- Uprawnienia do modyfikacji tabel emaili

## Rozwiązywanie problemów

### Błąd: "duplicate key value violates unique constraint"
- Skrypt sprawdza czy szablony już istnieją przed ich utworzeniem
- Jeśli nadal występuje błąd, uruchom skrypt ponownie

### Błąd: "Failed to create email schedules"
- Sprawdź czy istnieją wydarzenia w systemie
- Sprawdź czy szablony emaili zostały utworzone poprawnie

### Błąd połączenia z bazą danych
- Sprawdź czy aplikacja działa poprawnie
- Sprawdź konfigurację bazy danych w pliku `.env`

## Autor
Utworzone przez AI Assistant dla Klubu Lepsze Życie
