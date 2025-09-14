"""
Configuration for CRM system
"""

# Call statuses
CALL_STATUSES = {
    'lead': 'Pozyskany lead',
    'rejection': 'Odmowa',
    'callback': 'Przeplanowane połączenie',
    'no_answer': 'Nie odebrał',
    'busy': 'Zajęty',
    'wrong_number': 'Błędny numer'
}

# Call priorities
CALL_PRIORITIES = {
    'high': 'Wysoki',      # Przeplanowane połączenia
    'medium': 'Średni',    # Potencjały
    'low': 'Niski'         # Nowe rekordy
}

# File upload settings
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# CSV column mappings
CSV_COLUMNS = {
    'name': ['imię', 'nazwisko', 'imie', 'nazwisko', 'name', 'full_name'],
    'phone': ['telefon', 'phone', 'mobile', 'tel', 'numer'],
    'email': ['email', 'e-mail', 'mail'],
    'company': ['firma', 'company', 'organizacja', 'organization'],
    'notes': ['notatki', 'notes', 'uwagi', 'comments']
}

# Pagination
ITEMS_PER_PAGE = 20

# Call attempt settings
DEFAULT_MAX_CALL_ATTEMPTS = 3  # Default max attempts before blacklisting

# Queue types
QUEUE_TYPES = {
    'new': 'Nowy kontakt',
    'callback': 'Przeplanowane połączenie',
    'retry': 'Ponowne połączenie'
}

# Blacklist reasons
BLACKLIST_REASONS = {
    'rejection': 'Odmowa',
    'max_attempts': 'Przekroczono limit prób',
    'wrong_number': 'Błędny numer',
    'manual': 'Ręczne dodanie'
}
