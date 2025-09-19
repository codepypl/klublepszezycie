"""add_security_alert_template

Revision ID: d499b730d48a
Revises: 7b4dd244edb2
Create Date: 2025-09-19 07:02:17.390973

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd499b730d48a'
down_revision = '7b4dd244edb2'
branch_labels = None
depends_on = None


def upgrade():
    """Add security_alert template to default_email_templates"""
    # Get database connection
    connection = op.get_bind()
    
    print("🔄 Adding security_alert template to default_email_templates...")
    
    # Check if template already exists
    result = connection.execute(sa.text("""
        SELECT COUNT(*) FROM default_email_templates 
        WHERE name = 'security_alert'
    """))
    
    if result.fetchone()[0] > 0:
        print("✅ Security alert template already exists")
        return
    
    # Insert security alert template
    connection.execute(sa.text("""
        INSERT INTO default_email_templates (
            name, template_type, subject, html_content, text_content, 
            variables, description, is_active, created_at, updated_at
        ) VALUES (
            'security_alert',
            'security_alert',
            '🚨 Alert Bezpieczeństwa - {{ server_name }}',
            :html_content,
            :text_content,
            :variables,
            'Szablon alertu bezpieczeństwa wysyłany do administratora przy podejrzanej aktywności',
            true,
            NOW(),
            NOW()
        )
    """), {
        'html_content': '''<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alert Bezpieczeństwa - {{ server_name }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background-color: #dc3545;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }
        .content {
            background-color: #f8f9fa;
            padding: 20px;
            border: 1px solid #dee2e6;
            border-top: none;
        }
        .alert-box {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }
        .details {
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }
        .footer {
            background-color: #6c757d;
            color: white;
            padding: 15px;
            text-align: center;
            border-radius: 0 0 5px 5px;
            font-size: 12px;
        }
        .label {
            font-weight: bold;
            color: #495057;
        }
        .value {
            color: #212529;
            word-break: break-all;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚨 Alert Bezpieczeństwa</h1>
        <p>{{ server_name }}</p>
    </div>
    
    <div class="content">
        <div class="alert-box">
            <h2>⚠️ Wykryto podejrzaną aktywność</h2>
            <p><strong>Typ zdarzenia:</strong> {{ event_type }}</p>
            <p><strong>Data i czas:</strong> {{ timestamp }}</p>
        </div>
        
        <div class="details">
            <h3>📋 Szczegóły zdarzenia:</h3>
            <p><span class="label">Opis:</span> <span class="value">{{ details }}</span></p>
            <p><span class="label">Adres IP:</span> <span class="value">{{ client_ip }}</span></p>
            <p><span class="label">User Agent:</span> <span class="value">{{ user_agent }}</span></p>
        </div>
        
        <div class="alert-box">
            <h3>🔍 Co należy sprawdzić:</h3>
            <ul>
                <li>Czy to jest prawdziwy użytkownik próbujący uzyskać dostęp?</li>
                <li>Czy IP jest znane i zaufane?</li>
                <li>Czy występują wzorce ataków (wiele prób z różnych IP)?</li>
                <li>Czy token został skompromitowany?</li>
            </ul>
        </div>
        
        <div class="details">
            <h3>🛡️ Zalecane działania:</h3>
            <ul>
                <li>Sprawdź logi serwera pod kątem podobnych zdarzeń</li>
                <li>Rozważ blokadę IP jeśli aktywność jest podejrzana</li>
                <li>Zweryfikuj czy użytkownik rzeczywiście istnieje</li>
                <li>Sprawdź czy nie ma problemów z generowaniem tokenów</li>
            </ul>
        </div>
    </div>
    
    <div class="footer">
        <p>Ten alert został wygenerowany automatycznie przez system bezpieczeństwa.</p>
        <p>Jeśli uważasz, że to fałszywy alarm, możesz zignorować ten email.</p>
        <p>&copy; {{ server_name }} - System Bezpieczeństwa</p>
    </div>
</body>
</html>''',
        'text_content': '''🚨 ALERT BEZPIECZEŃSTWA - {{ server_name }}

⚠️ WYKRYTO PODEJRZANĄ AKTYWNOŚĆ

Typ zdarzenia: {{ event_type }}
Data i czas: {{ timestamp }}

📋 SZCZEGÓŁY ZDARZENIA:
Opis: {{ details }}
Adres IP: {{ client_ip }}
User Agent: {{ user_agent }}

🔍 CO NALEŻY SPRAWDZIĆ:
- Czy to jest prawdziwy użytkownik próbujący uzyskać dostęp?
- Czy IP jest znane i zaufane?
- Czy występują wzorce ataków (wiele prób z różnych IP)?
- Czy token został skompromitowany?

🛡️ ZALECANE DZIAŁANIA:
- Sprawdź logi serwera pod kątem podobnych zdarzeń
- Rozważ blokadę IP jeśli aktywność jest podejrzana
- Zweryfikuj czy użytkownik rzeczywiście istnieje
- Sprawdź czy nie ma problemów z generowaniem tokenów

---
Ten alert został wygenerowany automatycznie przez system bezpieczeństwa.
Jeśli uważasz, że to fałszywy alarm, możesz zignorować ten email.

© {{ server_name }} - System Bezpieczeństwa''',
        'variables': '''{"event_type": "Typ zdarzenia bezpieczeństwa", "details": "Szczegółowy opis zdarzenia", "client_ip": "Adres IP klienta", "user_agent": "User Agent przeglądarki", "timestamp": "Data i czas zdarzenia", "server_name": "Nazwa serwera"}'''
    })
    
    print("✅ Security alert template added successfully")


def downgrade():
    """Remove security_alert template from default_email_templates"""
    # Get database connection
    connection = op.get_bind()
    
    print("🔄 Removing security_alert template from default_email_templates...")
    
    # Remove security alert template
    connection.execute(sa.text("""
        DELETE FROM default_email_templates 
        WHERE name = 'security_alert'
    """))
    
    print("✅ Security alert template removed successfully")
