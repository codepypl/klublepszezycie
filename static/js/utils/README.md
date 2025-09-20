# Utils - Universal JavaScript Utilities

## Tooltip Manager

Uniwersalny menedżer tooltipów Bootstrap dla całej aplikacji.

### Użycie

#### 1. Automatyczne inicjalizowanie
Tooltips są automatycznie inicjalizowane dla wszystkich elementów z `data-bs-toggle="tooltip"`:

```html
<span data-bs-toggle="tooltip" 
      data-bs-placement="top" 
      title="Nazwa kategorii">
    ID: 123
</span>
```

#### 2. Programatyczne zarządzanie

```javascript
// Inicjalizuj tooltips w kontenerze
window.tooltipManager.reinitializeTooltips('#myContainer');

// Zaktualizuj treść tooltip
window.tooltipManager.updateTooltipContent('#myElement', 'Nowa treść');

// Pokaż/ukryj tooltip
window.tooltipManager.showTooltip('#myElement');
window.tooltipManager.hideTooltip('#myElement');

// Zniszcz tooltip
window.tooltipManager.destroyTooltip('#myElement');
```

#### 3. Opcje konfiguracji

```html
<span data-bs-toggle="tooltip" 
      data-bs-placement="bottom" 
      data-bs-delay="500"
      title="Tooltip z opóźnieniem">
    Element z tooltip
</span>
```

### Funkcje

- ✅ Automatyczna inicjalizacja
- ✅ Obsługa dynamicznych elementów
- ✅ Debouncing dla wydajności
- ✅ Zarządzanie cyklem życia
- ✅ API do programatycznego kontrolowania
- ✅ Obsługa błędów
- ✅ Kompatybilność z Bootstrap 5

### Przykłady użycia

#### Tabela z tooltipami
```html
<td>
    {% for category in post.categories %}
        <span class="badge" 
              data-bs-toggle="tooltip" 
              data-bs-placement="top" 
              title="{{ category.title }}">
            {{ category.id }}
        </span>
    {% endfor %}
</td>
```

#### Dynamiczne dodawanie
```javascript
// Po dodaniu nowego elementu do DOM
const newElement = document.createElement('span');
newElement.setAttribute('data-bs-toggle', 'tooltip');
newElement.setAttribute('title', 'Nowy tooltip');
document.body.appendChild(newElement);

// Tooltip zostanie automatycznie zainicjalizowany
```

### Wymagania

- Bootstrap 5
- Nowoczesna przeglądarka z obsługą ES6+
