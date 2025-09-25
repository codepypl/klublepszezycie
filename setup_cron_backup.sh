#!/bin/bash
# Skrypt do ustawienia cron job jako backup dla systemu mailingowego

echo "🔧 Ustawianie cron job jako backup dla systemu mailingowego..."

# Sprawdź czy jesteś w odpowiednim katalogu
if [ ! -f "app.py" ]; then
    echo "❌ Błąd: Uruchom skrypt z katalogu głównego aplikacji"
    exit 1
fi

# Utwórz skrypt do przetwarzania kolejki
cat > process_email_queue.sh << 'EOF'
#!/bin/bash
# Skrypt do przetwarzania kolejki emaili
cd /apps/klublepszezycie
source .venv/bin/activate
export FLASK_APP=app
export FLASK_ENV=production

# Przetwórz kolejkę emaili
python -c "
from app import create_app
from app.services.email_service import EmailService
app = create_app()
with app.app_context():
    email_service = EmailService()
    stats = email_service.process_queue(50)
    print(f'[{$(date)}] Przetworzono {stats[\"processed\"]} emaili: {stats[\"success\"]} sukces, {stats[\"failed\"]} błąd')
" >> /var/log/email_queue.log 2>&1
EOF

# Ustaw uprawnienia
chmod +x process_email_queue.sh

# Dodaj do crontab
echo "📅 Dodawanie do crontab..."
(crontab -l 2>/dev/null; echo "# Email queue processing - co 2 minuty") | crontab -
(crontab -l 2>/dev/null; echo "*/2 * * * * /apps/klublepszezycie/process_email_queue.sh") | crontab -

echo "✅ Cron job ustawiony!"
echo "📋 Sprawdź crontab:"
crontab -l | grep email

echo ""
echo "📊 Sprawdź logi:"
echo "tail -f /var/log/email_queue.log"
