# Kody Błędów Systemu

## Struktura Kodów Błędów

Format: `SE-XXX-NN`
- **SE** = System Error
- **XXX** = Kategoria błędu (3 litery)
- **NN** = Numer błędu (01, 02, 03...)

## Kategorie Błędów

### ITK - Invalid Token (Nieprawidłowy Token)
- **SE-ITK-01** - Nieprawidłowy lub wygasły token
  - Występuje gdy: token jest nieprawidłowy, wygasł lub został sfałszowany
  - Akcja: Sprawdź czy link został skopiowany w całości z emaila

### UNF - User Not Found (Użytkownik Nie Znaleziony)
- **SE-UNF-01** - Użytkownik nie został znaleziony
  - Występuje gdy: użytkownik z podanym emailem nie istnieje w bazie danych
  - Akcja: Sprawdź czy email jest prawidłowy lub czy konto nie zostało już usunięte

### ADP - Admin Protected (Konto Administratora Chronione)
- **SE-ADP-01** - Próba usunięcia konta administratora
  - Występuje gdy: próba usunięcia konta z rolą administratora
  - Akcja: Operacja niedozwolona ze względów bezpieczeństwa

### DBE - Database Error (Błąd Bazy Danych)
- **SE-DBE-01** - Błąd techniczny bazy danych
  - Występuje gdy: wystąpił błąd połączenia z bazą danych lub transakcji
  - Akcja: Spróbuj ponownie za kilka minut, jeśli problem się powtarza skontaktuj się z administratorem

## Przykłady Użycia

### Unsubscribe (Wypisanie z Newslettera)
```
SE-ITK-01 - Nieprawidłowy token w linku wypisania
SE-UNF-01 - Użytkownik nie znaleziony przy wypisywaniu
SE-DBE-01 - Błąd bazy danych podczas wypisywania
```

### Delete Account (Usuwanie Konta)
```
SE-ITK-01 - Nieprawidłowy token w linku usuwania
SE-ADP-01 - Próba usunięcia konta administratora
SE-UNF-01 - Użytkownik nie znaleziony przy usuwaniu
SE-DBE-01 - Błąd bazy danych podczas usuwania
```

## Monitorowanie Bezpieczeństwa

Kody błędów są monitorowane przez system bezpieczeństwa:

### Podejrzane Aktywności (Wysyłanie alertów do administratora)
- **SE-ITK-01** - Częste próby z nieprawidłowymi tokenami mogą wskazywać na atak
- **SE-ADP-01** - Próby usunięcia kont administratorów są zawsze podejrzane

### Normalne Błędy (Tylko logowanie)
- **SE-UNF-01** - Może być normalne (użytkownik już usunął konto)
- **SE-DBE-01** - Błędy techniczne, monitorowane przez system

## Implementacja

Kody błędów są zwracane w odpowiedziach API:

```json
{
  "success": false,
  "error": "Nieprawidłowy lub wygasły token",
  "error_code": "SE-ITK-01"
}
```

I wyświetlane użytkownikowi w szablonach HTML z odpowiednimi komunikatami.
