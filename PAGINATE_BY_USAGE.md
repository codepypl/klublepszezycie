# PAGINATE_BY - Przewodnik użytkowania

## Opis
Stała `PAGINATE_BY` określa domyślną ilość wierszy na stronie dla wszystkich tabel w panelu administratora.

## Konfiguracja

### W pliku .env
```env
PAGINATE_BY=15
```

### W kodzie (domyślnie)
```python
PAGINATE_BY = 10  # Domyślna wartość
```

## Użycie w API

### Przykład 1: Kampanie emailowe
```python
@email_bp.route('/email/campaigns', methods=['GET'])
@login_required
def email_campaigns():
    try:
        from app.config.config import get_config
        config = get_config()
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', config.PAGINATE_BY, type=int)
        
        # Reszta kodu...
```

### Przykład 2: Użytkownicy
```python
@users_bp.route('/users', methods=['GET'])
@login_required
def users():
    try:
        from app.config.config import get_config
        config = get_config()
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', config.PAGINATE_BY, type=int)
        
        # Reszta kodu...
```

## Użycie w szablonach

### Przekazanie konfiguracji do szablonu
```python
@admin_bp.route('/email-campaigns')
@login_required
def email_campaigns():
    from app.config.config import get_config
    config = get_config()
    return render_template('admin/email_campaigns.html', config=config)
```

### W szablonie HTML
```html
<!-- Pagination -->
<div id="pagination" class="mt-3 pagination-container" 
     data-show-info="true" 
     data-show-per-page="true" 
     data-default-per-page="{{ config.PAGINATE_BY }}" 
     data-max-visible-pages="5"></div>
```

## Użycie w JavaScript

### Automatyczne aktualizowanie z serwera
```javascript
.then(data => {
    if (data.success) {
        displayItems(data.items);
        if (data.pagination) {
            // Update currentPerPage from server response
            currentPerPage = data.pagination.per_page;
            updatePagination(data.pagination);
        }
    }
})
```

## Migracja istniejących tabel

### 1. Zaktualizuj API
```python
# Przed
per_page = request.args.get('per_page', 10, type=int)

# Po
from app.config.config import get_config
config = get_config()
per_page = request.args.get('per_page', config.PAGINATE_BY, type=int)
```

### 2. Zaktualizuj routing
```python
# Przed
return render_template('admin/table.html')

# Po
from app.config.config import get_config
config = get_config()
return render_template('admin/table.html', config=config)
```

### 3. Zaktualizuj szablon
```html
<!-- Przed -->
data-default-per-page="10"

<!-- Po -->
data-default-per-page="{{ config.PAGINATE_BY }}"
```

## Tabele do zaktualizowania

- [x] **Kampanie emailowe** - ✅ Zaktualizowane
- [ ] **Użytkownicy** - Do zaktualizowania
- [ ] **Wydarzenia** - Do zaktualizowania
- [ ] **Logi emaili** - Do zaktualizowania
- [ ] **Szablony emaili** - Do zaktualizowania
- [ ] **Grupy użytkowników** - Do zaktualizowania
- [ ] **Kolejka emaili** - Do zaktualizowania
- [ ] **Sekcje** - Do zaktualizowania
- [ ] **FAQ** - Do zaktualizowania
- [ ] **Opinie** - Do zaktualizowania
- [ ] **Menu** - Do zaktualizowania
- [ ] **Korzyści** - Do zaktualizowania

## Korzyści

1. **Centralna konfiguracja** - Jedna stała dla wszystkich tabel
2. **Łatwa zmiana** - Zmiana w .env wpływa na wszystkie tabele
3. **Spójność** - Wszystkie tabele mają tę samą domyślną paginację
4. **Elastyczność** - Użytkownik nadal może zmienić ilość na stronie

## Przykład konfiguracji

### .env
```env
# Pagination
PAGINATE_BY=15

# Inne ustawienia...
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://...
```

### Wynik
- Wszystkie tabele będą domyślnie pokazywać 15 wierszy na stronie
- Użytkownik może zmienić to w interfejsie
- Ustawienie jest zapisywane w localStorage
