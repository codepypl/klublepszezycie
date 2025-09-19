# 🔧 Instrukcje Naprawy Migracji na Serwerze Produkcyjnym

## 🚨 Problemy
1. **Migracja `af25e20522fc`** próbuje dodać kolumny do tabeli `user_history`, które już istnieją:
   ```
   psycopg2.errors.DuplicateColumn: column "registration_type" of relation "user_history" already exists
   ```

2. **Brakujące kolumny w tabeli `users`** powodują błędy aplikacji:
   ```
   sqlalchemy.exc.ProgrammingError: column users.account_type does not exist
   ```

## 🔍 Diagnoza
Na serwerze produkcyjnym struktura bazy danych różni się od lokalnej:
- Tabela `user_history` ma kolumny, ale migracja nie została oznaczona jako zastosowana
- Tabela `users` nie ma wymaganych kolumn `account_type`, `event_id`, `group_id`

## 🛠️ Rozwiązanie

### Krok 1: Sprawdzenie stanu migracji
```bash
# Na serwerze produkcyjnym
cd /apps/klublepszezycie
source .venv/bin/activate
python check_migrations.py
```

### Krok 2: Naprawa tabeli users
```bash
# Na serwerze produkcyjnym
python fix_users_table.py
```

### Krok 3: Sprawdzenie struktury tabeli user_history
```bash
# Na serwerze produkcyjnym
python check_table_structure.py
```

### Krok 4: Naprawa migracji user_history
```bash
# Na serwerze produkcyjnym
python fix_migration.py
```

**Uwaga:** Wszystkie skrypty automatycznie ładują zmienne środowiskowe z pliku `.env` dzięki `load_dotenv()`.

### Krok 5: Kontynuacja migracji
```bash
# Na serwerze produkcyjnym
flask db upgrade
```

## 📋 Co robi skrypt naprawczy

1. **Sprawdza istniejące kolumny** w tabeli `user_history`
2. **Identyfikuje brakujące kolumny** z migracji
3. **Dodaje brakujące kolumny** ręcznie (jeśli są)
4. **Sprawdza i dodaje constraint'y** (unique constraint, indeksy)
5. **Oznacza migrację jako zastosowaną** w tabeli `alembic_version`
6. **Pozwala na kontynuację** normalnego procesu migracji

## ⚠️ Uwagi Bezpieczeństwa

- **Backup bazy danych** przed uruchomieniem skryptów
- **Test na kopii** jeśli to możliwe
- **Monitorowanie logów** podczas naprawy
- **Sprawdzenie po naprawie** czy wszystko działa poprawnie

## 🔄 Alternatywne Rozwiązanie

Jeśli skrypty nie działają, można ręcznie:

1. **Sprawdzić obecną wersję migracji:**
   ```sql
   SELECT version_num FROM alembic_version;
   ```

2. **Oznaczyć migrację jako zastosowaną:**
   ```sql
   UPDATE alembic_version SET version_num = 'af25e20522fc';
   ```

3. **Kontynuować migrację:**
   ```bash
   flask db upgrade
   ```

## 📞 Wsparcie

W przypadku problemów:
1. Sprawdź logi aplikacji
2. Sprawdź strukturę tabeli `user_history`
3. Sprawdź tabelę `alembic_version`
4. Skontaktuj się z deweloperem
