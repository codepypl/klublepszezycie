# Better Life Club - Database Migration Tools

Zestaw narzędzi do migracji i synchronizacji bazy danych PostgreSQL dla projektu Better Life Club.

## 🚀 Dostępne narzędzia

### 1. `export_db.py` - Eksport bazy danych
Eksportuje bazę danych do pliku SQL.

**Użycie:**
```bash
python export_db.py
```

**Opcje:**
- Eksport pełnej bazy (z danymi)
- Eksport tylko struktury (schema)
- Eksport obu wersji

### 2. `import_db.py` - Import bazy danych
Importuje bazę danych z pliku SQL.

**Użycie:**
```bash
# Tryb interaktywny
python import_db.py

# Z linii komend
python import_db.py backup_file.sql [target_database]
```

### 3. `migrate_db.py` - Migracja struktury i danych
Główny skrypt migracji, który używa obecnej bazy jako szablonu.

**Użycie:**
```bash
python migrate_db.py
```

**Funkcjonalności:**
- Sprawdza zgodność struktury tabel
- Wykrywa różnice w kolumnach i ograniczeniach
- Migruje strukturę (Faza 1)
- Migruje dane (Faza 2)

### 4. `generate_migration_sql.py` - Generator SQL
Generuje pliki SQL dla migracji.

**Użycie:**
```bash
python generate_migration_sql.py
```

## 🔧 Jak to działa

### Faza 1: Migracja struktury
1. **Analiza tabel** - Porównuje strukturę tabel w bazie źródłowej i docelowej
2. **Wykrywanie różnic** - Identyfikuje:
   - Brakujące kolumny
   - Dodatkowe kolumny
   - Zmiany w typach danych
   - Zmiany w ograniczeniach
3. **Generowanie SQL** - Tworzy instrukcje ALTER TABLE
4. **Aplikowanie zmian** - Wykonuje zmiany struktury

### Faza 2: Migracja danych
1. **Analiza danych** - Sprawdza ilość danych w tabelach
2. **Wykrywanie potrzeb** - Identyfikuje tabele wymagające migracji danych
3. **Generowanie INSERT** - Tworzy instrukcje INSERT dla danych
4. **Migracja** - Przenosi dane do docelowej bazy

## 📋 Wymagania

### Zależności Python
```bash
pip install psycopg2-binary python-dotenv
```

### Narzędzia PostgreSQL
- `pg_dump` - do eksportu
- `psql` - do importu
- `createdb` - do tworzenia baz

**Instalacja na macOS:**
```bash
brew install postgresql
```

**Instalacja na Ubuntu:**
```bash
sudo apt-get install postgresql-client
```

## ⚙️ Konfiguracja

### Plik .env
```bash
# Baza źródłowa (szablon)
DATABASE_URL=postgresql://username@host:port/database

# Hasło do bazy (opcjonalne)
DATABASE_PASSWORD=your_password

# Baza docelowa (dla migracji)
TARGET_DATABASE_URL=postgresql://username@host:port/target_database
```

## 📖 Przykłady użycia

### 1. Eksport obecnej bazy jako szablonu
```bash
python export_db.py
# Wybierz opcję 1 (pełny eksport)
```

### 2. Sprawdzenie zgodności z inną bazą
```bash
python migrate_db.py
# Wprowadź URL bazy docelowej
```

### 3. Import bazy z pliku
```bash
python import_db.py backup_20241201_143022.sql
```

## 🛡️ Bezpieczeństwo

### Automatyczne backupy
- Skrypt migracji automatycznie tworzy backup przed zmianami
- Można pominąć backup (nie zalecane)

### Potwierdzenia
- Wszystkie zmiany wymagają potwierdzenia użytkownika
- Można pominąć poszczególne tabele

### Bezpieczne operacje
- Usuwanie kolumn jest domyślnie wyłączone (skomentowane)
- Sprawdzanie istnienia danych przed nadpisaniem

## 🔍 Diagnostyka

### Logi
Skrypt wyświetla szczegółowe informacje o:
- Strukturze tabel
- Wykrytych różnicach
- Wykonanych operacjach
- Błędach i ostrzeżeniach

### Pliki SQL
Generowane pliki SQL zawierają:
- Instrukcje ALTER TABLE
- Instrukcje INSERT
- Komentarze wyjaśniające zmiany

## ⚠️ Uwagi

### Przed migracją
1. **Backup** - Zawsze twórz backup bazy docelowej
2. **Test** - Przetestuj na kopii produkcyjnej
3. **Weryfikacja** - Sprawdź poprawność wygenerowanego SQL

### Podczas migracji
1. **Monitoring** - Obserwuj logi i błędy
2. **Stopniowo** - Migruj tabele pojedynczo jeśli to możliwe
3. **Weryfikacja** - Sprawdź dane po każdej fazie

### Po migracji
1. **Test funkcjonalności** - Sprawdź działanie aplikacji
2. **Weryfikacja danych** - Porównaj ilość rekordów
3. **Backup** - Utwórz backup zaktualizowanej bazy

## 🆘 Rozwiązywanie problemów

### Błąd połączenia
```bash
❌ Cannot connect to database
# Sprawdź DATABASE_URL w .env
# Sprawdź czy PostgreSQL działa
# Sprawdź uprawnienia użytkownika
```

### Błąd uprawnień
```bash
❌ Permission denied
# Sprawdź uprawnienia użytkownika bazy
# Upewnij się że użytkownik ma prawa CREATE, ALTER, INSERT
```

### Błąd typu danych
```bash
❌ Data type mismatch
# Sprawdź kompatybilność typów PostgreSQL
# Może wymagać ręcznej konwersji
```

## 📞 Wsparcie

W przypadku problemów:
1. Sprawdź logi błędów
2. Zweryfikuj konfigurację
3. Sprawdź uprawnienia bazy danych
4. Upewnij się że wszystkie zależności są zainstalowane

## 🔄 Aktualizacje

Skrypt automatycznie:
- Wykrywa nowe tabele w modelach
- Dodaje brakujące kolumny
- Aktualizuje typy danych
- Zachowuje istniejące dane

---

**Ważne:** Zawsze testuj migracje na środowisku deweloperskim przed zastosowaniem na produkcji!
