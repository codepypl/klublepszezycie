# Konfiguracja Cron Job dla automatycznych przypomnień o wydarzeniach

## Problem
System automatycznych maili z przypomnieniami o wydarzeniach nie działa, ponieważ brakuje skonfigurowanego cron job na serwerze produkcyjnym.

## Rozwiązanie
Należy dodać cron job, który będzie uruchamiał skrypt `process_emails.py` co godzinę.

## Instrukcje konfiguracji

### 1. Sprawdź czy cron jest zainstalowany
```bash
which cron
```

### 2. Sprawdź aktualne cron joby
```bash
sudo crontab -l
```

### 3. Edytuj crontab
```bash
sudo crontab -e
```

### 4. Dodaj następującą linię
```bash
# Uruchamiaj przetwarzanie emaili co godzinę
0 * * * * cd /apps/klublepszezycie && source .venv/bin/activate && python process_emails.py >> logs/mail_queue.log 2>&1
```

### 5. Sprawdź czy cron job został dodany
```bash
sudo crontab -l
```

### 6. Sprawdź status cron service
```bash
sudo systemctl status cron
```

### 7. Uruchom cron service jeśli nie działa
```bash
sudo systemctl start cron
sudo systemctl enable cron
```

## Testowanie

### Ręczne uruchomienie skryptu
```bash
cd /apps/klublepszezycie
source .venv/bin/activate
python process_emails.py
```

### Sprawdzenie logów
```bash
tail -f logs/mail_queue.log
```

## Co robi system

System automatycznie:
1. **Wysyła przypomnienia 24h przed wydarzeniem** - do wszystkich członków klubu
2. **Wysyła przypomnienia 1h przed wydarzeniem** - do wszystkich członków klubu  
3. **Wysyła przypomnienia 5min przed wydarzeniem** - do wszystkich członków klubu (z linkiem do spotkania)

## Grupy docelowe

System wysyła przypomnienia do:
- **Zarejestrowanych uczestników** - osoby które zapisały się na konkretne wydarzenie
- **Członków klubu** - wszystkie osoby należące do grupy "Członkowie klubu" (33 osoby)

## Szablony emaili

Używane szablony:
- `event_reminder_24h` - przypomnienie za 24h
- `event_reminder_1h` - przypomnienie za 1h  
- `event_reminder_5min` - przypomnienie za 5min (z linkiem do spotkania)

## Monitoring

Sprawdź logi w:
- `logs/mail_queue.log` - logi przetwarzania emaili
- Panel administracyjny → Email → Kolejka emaili
