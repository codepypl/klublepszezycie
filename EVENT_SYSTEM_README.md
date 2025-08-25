# 🎯 System Zapisów na Wydarzenia - Dokumentacja

## 📋 Przegląd

System zapisów na wydarzenia umożliwia użytkownikom rejestrację na konkretne wydarzenia z automatycznymi powiadomieniami email. System integruje się z istniejącym harmonogramem emaili i szablonami.

## 🚀 Funkcjonalności

### ✅ **Zapisy na Wydarzenia**
- Formularz zapisu z danymi użytkownika
- Pytanie o dołączenie do klubu
- Automatyczne tworzenie grup odbiorców
- Sprawdzanie duplikatów zapisów

### 📧 **Automatyczne Powiadomienia**
- **24h przed** - przypomnienie o wydarzeniu
- **1h przed** - ostatnie przypomnienie
- **5min przed** - link do spotkania

### 🎨 **Frontend**
- Modal zapisów w sekcji HERO
- Przyciski zapisu w timeline wydarzeń
- Responsywny design
- Walidacja formularza

## 🗄️ Struktura Bazy Danych

### **event_registrations**
```sql
- id (PK)
- event_id (FK -> event_schedule)
- name, email, phone
- status (confirmed, attended, cancelled)
- wants_club_news (boolean)
- notification_preferences (JSON)
- created_at, updated_at
```

### **event_notifications**
```sql
- id (PK)
- event_id (FK -> event_schedule)
- notification_type (24h_before, 1h_before, 5min_before)
- status (pending, sent, failed)
- scheduled_at, sent_at
- subject, template_name
- recipient_count
```

### **event_recipient_groups**
```sql
- id (PK)
- event_id (FK -> event_schedule)
- name, description
- group_type (event_registrations, declined_club, custom)
- criteria_config (JSON)
- member_count
- is_active
```

## 🔧 Instalacja i Konfiguracja

### **1. Migracja Bazy Danych**
```bash
# Uruchom skrypt migracyjny
python migrate_event_system.py

# W przypadku problemów - cofnij migrację
python migrate_event_system.py --rollback
```

### **2. Utworzenie Szablonów Email**
1. Zaloguj się do panelu admina
2. Przejdź do **Szablony E-mail**
3. Kliknij **"Utwórz Domyślne Szablony"**
4. To utworzy:
   - `event_reminder_24h_before`
   - `event_reminder_1h_before`
   - `event_reminder_5min_before`
   - `event_registration_confirmation`

### **3. Utworzenie Harmonogramów**
1. Przejdź do **Harmonogram E-maili**
2. Kliknij **"Utwórz Harmonogramy Wydarzeń"**
3. To utworzy automatyczne harmonogramy dla:
   - Przypomnienie 24h przed wydarzeniem
   - Przypomnienie 1h przed wydarzeniem
   - Link do spotkania 5min przed wydarzeniem

## 📱 Użycie

### **Dla Użytkowników**
1. **Zapisy na wydarzenia:**
   - Kliknij "Zarezerwuj miejsce" w sekcji HERO
   - Wypełnij formularz (imię, email, telefon)
   - Zaznacz czy chcesz dołączyć do klubu
   - Kliknij "Zarezerwuj miejsce"

2. **Powiadomienia:**
   - Otrzymasz potwierdzenie zapisu
   - Automatyczne przypomnienia 24h i 1h przed
   - Link do spotkania 5min przed startem

### **Dla Administratorów**
1. **Zarządzanie zapisami:**
   - Wszystkie zapisy są widoczne w bazie danych
   - Możliwość zarządzania grupami odbiorców

2. **Harmonogramy:**
   - Automatyczne uruchamianie powiadomień
   - Możliwość ręcznego uruchomienia
   - Monitoring statusu wysyłania

3. **Szablony:**
   - Edycja treści powiadomień
   - Personalizacja wiadomości
   - Zmienne dostępne w szablonach

## 🔄 API Endpoints

### **Zapisy na Wydarzenia**
```http
POST /register-event/{event_id}
Content-Type: application/x-www-form-urlencoded

name=Jan Kowalski&email=jan@example.com&phone=123456789&wants_club_news=true
```

### **Tworzenie Harmonogramów**
```http
POST /admin/api/create-event-schedules
Authorization: Required (Admin)
```

### **Tworzenie Szablonów**
```http
POST /admin/api/create-default-templates
Authorization: Required (Admin)
```

## 📧 Szablony Email

### **Dostępne Zmienne**
- `{{name}}` - imię użytkownika
- `{{email}}` - email użytkownika
- `{{event_title}}` - tytuł wydarzenia
- `{{event_date}}` - data wydarzenia
- `{{event_time}}` - godzina wydarzenia
- `{{event_type}}` - typ wydarzenia
- `{{event_location}}` - lokalizacja
- `{{event_meeting_link}}` - link do spotkania
- `{{event_description}}` - opis wydarzenia
- `{{unsubscribe_url}}` - link do rezygnacji
- `{{delete_account_url}}` - link do usunięcia konta

### **Typy Szablonów**
1. **event_reminder_24h_before** - Przypomnienie 24h przed
2. **event_reminder_1h_before** - Przypomnienie 1h przed
3. **event_reminder_5min_before** - Link do spotkania
4. **event_registration_confirmation** - Potwierdzenie zapisu

## 🎨 Styling

### **CSS Klasy**
- `.countdown-timer` - licznik odliczający
- `.timeline-container` - kontener timeline
- `.timeline-item` - element timeline
- `.event-registration-modal` - modal zapisów

### **Responsywność**
- Mobile-first design
- Breakpointy Bootstrap 5
- Adaptive timeline layout

## 🔍 Debugowanie

### **Logi**
- Sprawdź konsolę przeglądarki
- Logi serwera Flask
- Błędy bazy danych

### **Typowe Problemy**
1. **Brak szablonów email:**
   - Uruchom "Utwórz Domyślne Szablony"

2. **Brak harmonogramów:**
   - Uruchom "Utwórz Harmonogramy Wydarzeń"

3. **Błędy bazy danych:**
   - Sprawdź czy migracja została wykonana

4. **Powiadomienia nie działają:**
   - Sprawdź status harmonogramów
   - Uruchom ręcznie "Sprawdź Harmonogramy"

## 🚀 Rozszerzenia

### **Możliwe Ulepszenia**
1. **Integracja z kalendarzami** (Google, Outlook)
2. **SMS notifications**
3. **Push notifications**
4. **Analytics i raporty**
5. **Automatyczne follow-up**
6. **Integracja z płatnościami**

### **Dodatkowe Typy Wydarzeń**
1. **Webinary** - z linkami do rejestracji
2. **Warsztaty** - z limitem uczestników
3. **Konferencje** - z wieloma sesjami
4. **Spotkania networkingowe** - z matchmakingiem

## 📚 Zasoby

### **Dokumentacja**
- [Flask SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
- [Bootstrap 5](https://getbootstrap.com/docs/5.3/)
- [Font Awesome](https://fontawesome.com/)

### **Wsparcie**
- Sprawdź logi aplikacji
- Użyj trybu debug Flask
- Sprawdź status bazy danych

---

**Wersja:** 1.0.0  
**Data:** 2024  
**Autor:** System Administrator
