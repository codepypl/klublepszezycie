# System CRM - Zarządzanie połączeniami telefonicznymi

## Struktura folderów

```
crm/
├── admin/                    # Moduły administracyjne CRM
│   ├── ankieter.py          # Blueprint dla ankieterów
│   └── templates/           # Szablony dla ankieterów
│       └── ankieter/
├── basic_scripts/           # Skrypty pomocnicze
│   ├── add_role_column.py   # Migracja bazy danych
│   └── create_ankieter.py   # Tworzenie użytkownika ankietera
└── data/                    # Dane systemu CRM
    ├── import/              # Pliki do importu (CSV/XLSX)
    └── export/              # Pliki eksportowane
```

## Funkcjonalności

### Ankieter
- Dashboard z statystykami
- Zarządzanie połączeniami
- Import kontaktów z plików CSV/XLSX
- Kolejka połączeń z priorytetami
- Formularz zapisywania wyników rozmów

### Role użytkowników
- **admin** - Pełny dostęp do systemu
- **ankieter** - Dostęp do panelu ankietera
- **user** - Podstawowy użytkownik

## Użycie

### Tworzenie użytkownika ankietera
```bash
python crm/basic_scripts/create_ankieter.py
```

### Migracja bazy danych
```bash
python crm/basic_scripts/add_role_column.py
```

## Dostęp
- Panel ankietera: `/ankieter/`
- Login: `ankieter@lepszezycie.pl`
- Hasło: `ankieter123`
