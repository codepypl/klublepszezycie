# Instrukcje dodania kolumny 'target' do social_links (PostgreSQL)

## Problem
Błąd: `'target' is an invalid keyword argument for SocialLink`

## Przyczyna
Model `SocialLink` nie miał pola `target` w bazie danych PostgreSQL.

## Rozwiązanie

### 1. Model został zaktualizowany ✅
Dodano pole `target` do modelu `SocialLink` w `models.py`:
```python
target = db.Column(db.String(20), default='_blank')
```

### 2. JavaScript został naprawiony ✅
Dodano `target: formData.get('target')` do obu formularzy w `social.html`.

### 3. Baza danych PostgreSQL wymaga aktualizacji ⚠️

**Uruchom na serwerze:**

```bash
python add_target_column.py
```

### Co robi skrypt:
1. ✅ Ładuje konfigurację z pliku `.env`
2. ✅ Łączy się z PostgreSQL używając SQLAlchemy
3. ✅ Sprawdza czy kolumna `target` już istnieje w `information_schema.columns`
4. ➕ Dodaje kolumnę `target VARCHAR(20) DEFAULT '_blank'`
5. 📊 Sprawdza ile rekordów jest w tabeli
6. ✅ Weryfikuje strukturę tabeli i przykładowe dane

### Wymagania:
- ✅ Plik `.env` z `DATABASE_URL=postgresql://...`
- ✅ Zainstalowane: `sqlalchemy`, `python-dotenv`, `psycopg2`

### Po uruchomieniu skryptu:
- ✅ Błąd `'target' is an invalid keyword argument` zniknie
- ✅ Pole "Otwórz w" będzie działać w dodawaniu linków
- ✅ Pole "Otwórz w" będzie działać w edycji linków
- ✅ Nowe linki będą miały domyślną wartość `_blank`

### Opcje pola 'target':
- `_blank` - Nowej karcie/oknie (domyślne)
- `_self` - Tej samej karcie  
- `_parent` - Ramce nadrzędnej
- `_top` - Najwyższym oknie

## Sprawdzenie
Po uruchomieniu skryptu sprawdź:
1. Czy możesz dodać nowy social link z polem "Otwórz w"
2. Czy możesz edytować istniejący link z polem "Otwórz w"
3. Czy linki otwierają się w wybranej karcie/oknie

## Przykład URL PostgreSQL:
```
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
```
