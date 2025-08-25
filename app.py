from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import uuid
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# File upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'mov'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    """Sprawdza czy plik ma dozwolone rozszerzenie"""
    if not filename or '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS

def validate_file_type(file):
    """Waliduje typ pliku na podstawie MIME type"""
    allowed_mime_types = {
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
        'video/mp4', 'video/webm', 'video/mov'
    }
    
    # Sprawdź MIME type
    if file.content_type not in allowed_mime_types:
        return False, f"Niedozwolony typ pliku: {file.content_type}"
    
    # Sprawdź rozszerzenie
    if not allowed_file(file.filename):
        return False, f"Niedozwolone rozszerzenie pliku: {file.filename}"
    
    # Sprawdź rozmiar (max 50MB)
    max_size = 50 * 1024 * 1024  # 50MB
    if file.content_length and file.content_length > max_size:
        return False, "Plik jest za duży. Maksymalny rozmiar: 50MB"
    
    return True, None

def validate_event_date(event_date_str):
    """Waliduje datę wydarzenia - nie może być w przeszłości"""
    try:
        event_date = datetime.fromisoformat(event_date_str.replace('Z', '+00:00'))
        # Porównuj z początkiem dzisiejszego dnia, nie z aktualnym momentem
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if event_date < today:
            return False, "Data wydarzenia nie może być w przeszłości"
        return True, None
    except ValueError:
        return False, "Nieprawidłowy format daty"

# Import models and config
from models import db, User, MenuItem, Section, BenefitItem, Testimonial, SocialLink, Registration, FAQ, SEOSettings, EventSchedule, Page, EmailTemplate, EmailSubscription, EmailLog, EmailSchedule, CustomEmailCampaign, EmailRecipientGroup, EventRegistration, EventNotification, EventRecipientGroup
from config import config
from email_service import email_service


# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config['development'])

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

# Custom Jinja2 filters
@app.template_filter('from_json')
def from_json_filter(value):
    """Convert JSON string to Python object"""
    if value is None:
        return []
    try:
        import json
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
with app.app_context():
    db.create_all()
    # Create admin user if not exists
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email=app.config['ADMIN_EMAIL'],  # ← Użyj konfiguracji!
            password_hash=generate_password_hash(app.config['ADMIN_PASSWORD']),
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()
    else:
        # Aktualizuj email admina z konfiguracji
        if admin_user.email != app.config['ADMIN_EMAIL']:
            admin_user.email = app.config['ADMIN_EMAIL']
            db.session.commit()
    
    # Create default email templates if they don't exist
    welcome_template = EmailTemplate.query.filter_by(template_type='welcome').first()
    if not welcome_template:
        welcome_template = EmailTemplate(
            name='Email Powitalny',
            subject='Witamy w Klubie Lepsze Życie! 🎉',
            html_content='''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Witamy w Klubie Lepsze Życie</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #28a745; margin-bottom: 10px;">🎉 Witamy w Klubie Lepsze Życie!</h1>
        <p style="font-size: 18px; color: #666;">Cieszę się, że dołączyłeś do nas!</p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #007bff; margin-top: 0;">Cześć {{name}}!</h2>
        <p>Dziękujemy za zarejestrowanie się na naszą darmową prezentację. Twoje miejsce zostało zarezerwowane!</p>
        
        <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #155724; margin-top: 0;">📅 Co dalej?</h3>
            <ul style="text-align: left; margin: 0; padding-left: 20px;">
                <li>Otrzymasz przypomnienie o wydarzeniu na 24h przed</li>
                <li>Będziesz informowany o nowych wydarzeniach i webinarach</li>
                <li>Dostaniesz dostęp do ekskluzywnych materiałów</li>
            </ul>
        </div>
    </div>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
        <h3 style="color: #856404; margin-top: 0;">🔒 Twoje dane są bezpieczne</h3>
        <p style="margin-bottom: 10px;">Możesz w każdej chwili:</p>
        <p style="margin: 5px 0;"><a href="{{unsubscribe_url}}" style="color: #856404;">📧 Zrezygnować z subskrypcji</a></p>
        <p style="margin: 5px 0;"><a href="{{delete_account_url}}" style="color: #856404;">🗑️ Usunąć swoje konto</a></p>
    </div>
    
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 14px;">
            Z poważaniem,<br>
            <strong>Zespół Klubu Lepsze Życie</strong>
        </p>
        <p style="color: #999; font-size: 12px; margin-top: 20px;">
            Ten email został wysłany na adres {{email}}
        </p>
    </div>
</body>
</html>
            ''',
            text_content='''
Witamy w Klubie Lepsze Życie! 🎉

Cześć {{name}}!

Dziękujemy za zarejestrowanie się na naszą darmową prezentację. Twoje miejsce zostało zarezerwowane!

Co dalej?
- Otrzymasz przypomnienie o wydarzeniu na 24h przed
- Będziesz informowany o nowych wydarzeniach i webinarach
- Dostaniesz dostęp do ekskluzywnych materiałów

Twoje dane są bezpieczne - możesz w każdej chwili:
- Zrezygnować z subskrypcji: {{unsubscribe_url}}
- Usunąć swoje konto: {{delete_account_url}}

Z poważaniem,
Zespół Klubu Lepsze Życie

Ten email został wysłany na adres {{email}}
            ''',
            template_type='welcome',
            variables='name,email,unsubscribe_url,delete_account_url',
            is_active=True
        )
        db.session.add(welcome_template)
        
        reminder_template = EmailTemplate.query.filter_by(template_type='reminder').first()
        if not reminder_template:
            reminder_template = EmailTemplate(
                name='Przypomnienie o Wydarzeniu',
                subject='🔔 Przypomnienie: {{event_type}} - {{event_date}}',
                html_content='''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Przypomnienie o Wydarzeniu</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #dc3545; margin-bottom: 10px;">🔔 Przypomnienie o Wydarzeniu</h1>
        <p style="font-size: 18px; color: #666;">Nie przegap tego wydarzenia!</p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #007bff; margin-top: 0;">Cześć {{name}}!</h2>
        <p>Przypominamy o nadchodzącym wydarzeniu:</p>
        
        <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #155724; margin-top: 0;">📅 {{event_type}}</h3>
            <p style="margin: 0;"><strong>Data:</strong> {{event_date}}</p>
            {% if event_details %}
            <p style="margin: 10px 0 0 0;"><strong>Szczegóły:</strong> {{event_details}}</p>
            {% endif %}
        </div>
    </div>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
        <h3 style="color: #856404; margin-top: 0;">🔒 Twoje dane są bezpieczne</h3>
        <p style="margin-bottom: 10px;">Możesz w każdej chwili:</p>
        <p style="margin: 5px 0;"><a href="{{unsubscribe_url}}" style="color: #856404;">📧 Zrezygnować z subskrypcji</a></p>
        <p style="margin: 5px 0;"><a href="{{delete_account_url}}" style="color: #856404;">🗑️ Usunąć swoje konto</a></p>
    </div>
    
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 14px;">
            Z poważaniem,<br>
            <strong>Zespół Klubu Lepsze Życie</strong>
        </p>
        <p style="color: #999; font-size: 12px; margin-top: 20px;">
            Ten email został wysłany na adres {{email}}
        </p>
    </div>
</body>
</html>
                ''',
                text_content='''
Przypomnienie o Wydarzeniu

Cześć {{name}}!

Przypominamy o nadchodzącym wydarzeniu:

📅 {{event_type}}
Data: {{event_date}}
{% if event_details %}
Szczegóły: {{event_details}}
{% endif %}

Twoje dane są bezpieczne - możesz w każdej chwili:
- Zrezygnować z subskrypcji: {{unsubscribe_url}}
- Usunąć swoje konto: {{delete_account_url}}

Z poważaniem,
Zespół Klubu Lepsze Życie

Ten email został wysłany na adres {{email}}
                ''',
                template_type='reminder',
                variables='name,email,event_type,event_date,event_details,unsubscribe_url,delete_account_url',
                is_active=True
            )
            db.session.add(reminder_template)
        
        # Add admin notification template
        admin_notification_template = EmailTemplate.query.filter_by(template_type='admin_notification').first()
        if not admin_notification_template:
            admin_notification_template = EmailTemplate(
                name='Powiadomienie dla Administratora',
                subject='🔔 Nowa rejestracja w Klubie Lepsze Życie',
                html_content='''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nowa Rejestracja</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #28a745; margin-bottom: 10px;">🔔 Nowa Rejestracja w Klubie</h1>
        <p style="font-size: 18px; color: #666;">Pojawił się nowy członek!</p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #007bff; margin-top: 0;">Cześć {{admin_name}}!</h2>
        <p>W systemie pojawiła się nowa rejestracja:</p>
        
        <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #155724; margin-top: 0;">👤 Nowy Członek</h3>
            <p style="margin: 5px 0;"><strong>Imię:</strong> {{new_member_name}}</p>
            <p style="margin: 5px 0;"><strong>Email:</strong> {{new_member_email}}</p>
            <p style="margin: 5px 0;"><strong>Data rejestracji:</strong> {{registration_date}}</p>
        </div>
    </div>
    
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 14px;">
            Z poważaniem,<br>
            <strong>System Klubu Lepsze Życie</strong>
        </p>
    </div>
</body>
</html>
                ''',
                text_content='''
Nowa Rejestracja w Klubie

Cześć {{admin_name}}!

W systemie pojawiła się nowa rejestracja:

👤 Nowy Członek
Imię: {{new_member_name}}
Email: {{new_member_email}}
Data rejestracji: {{registration_date}}

Z poważaniem,
System Klubu Lepsze Życie
                ''',
                template_type='admin_notification',
                variables='admin_name,new_member_name,new_member_email,registration_date',
                is_active=True
            )
            db.session.add(admin_notification_template)
        
        # Usuwamy szablon approval - nie jest potrzebny
        
        # Create default newsletter template
        newsletter_template = EmailTemplate.query.filter_by(template_type='newsletter').first()
        if not newsletter_template:
            newsletter_template = EmailTemplate(
                name='Newsletter Klubu',
                subject='📰 Newsletter Klubu Lepsze Życie - {{newsletter_title}}',
                html_content='''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Newsletter Klubu Lepsze Życie</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #28a745; margin-bottom: 10px;">📰 Newsletter Klubu Lepsze Życie</h1>
        <p style="font-size: 18px; color: #666;">Najnowsze informacje i aktualności</p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #007bff; margin-top: 0;">Cześć {{name}}!</h2>
        <p>Oto najnowsze informacje z naszego klubu:</p>
        
        <div style="background-color: #e7f3ff; border: 1px solid #b3d9ff; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #0056b3; margin-top: 0;">📋 {{newsletter_title}}</h3>
                            {{newsletter_content}}
        </div>
    </div>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
        <h3 style="color: #856404; margin-top: 0;">🔒 Twoje dane są bezpieczne</h3>
        <p style="margin-bottom: 10px;">Możesz w każdej chwili:</p>
        <p style="margin: 5px 0;"><a href="{{unsubscribe_url}}" style="color: #856404;">📧 Zrezygnować z subskrypcji</a></p>
        <p style="margin: 5px 0;"><a href="{{delete_account_url}}" style="color: #856404;">🗑️ Usunąć swoje konto</a></p>
    </div>
    
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 14px;">
            Z poważaniem,<br>
            <strong>Zespół Klubu Lepsze Życie</strong>
        </p>
        <p style="color: #999; font-size: 12px; margin-top: 20px;">
            Ten email został wysłany na adres {{email}}
        </p>
    </div>
</body>
</html>
                ''',
                text_content='''
Newsletter Klubu Lepsze Życie 📰

Cześć {{name}}!

Oto najnowsze informacje z naszego klubu:

{{newsletter_title}}

{{newsletter_content}}

Twoje dane są bezpieczne - możesz w każdej chwili:
- Zrezygnować z subskrypcji: {{unsubscribe_url}}
- Usunąć swoje konto: {{delete_account_url}}

Z poważaniem,
Zespół Klubu Lepsze Życie

Ten email został wysłany na adres {{email}}
                ''',
                template_type='newsletter',
                variables='name,email,newsletter_title,newsletter_content,unsubscribe_url,delete_account_url',
                is_active=True
            )
            db.session.add(newsletter_template)
        

        
        # Create default custom template
        custom_template = EmailTemplate.query.filter_by(template_type='custom').first()
        if not custom_template:
            custom_template = EmailTemplate(
                name='Email Własny',
                subject='📧 {{custom_subject}}',
                html_content='''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Własny</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #6f42c1; margin-bottom: 10px;">📧 Email Własny</h1>
        <p style="font-size: 18px; color: #666;">Wiadomość od Klubu Lepsze Życie</p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #007bff; margin-top: 0;">Cześć {{name}}!</h2>
        
        <div style="background-color: #e7f3ff; border: 1px solid #b3d9ff; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #0056b3; margin-top: 0;">{{custom_subject}}</h3>
            <div style="background-color: white; padding: 15px; border-radius: 3px; margin-top: 10px;">
                {{custom_content}}
            </div>
        </div>
    </div>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
        <h3 style="color: #856404; margin-top: 0;">🔒 Twoje dane są bezpieczne</h3>
        <p style="margin-bottom: 10px;">Możesz w każdej chwili:</p>
        <p style="margin: 5px 0;"><a href="{{unsubscribe_url}}" style="color: #856404;">📧 Zrezygnować z subskrypcji</a></p>
        <p style="margin: 5px 0;"><a href="{{delete_account_url}}" style="color: #856404;">🗑️ Usunąć swoje konto</a></p>
    </div>
    
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 14px;">
            Z poważaniem,<br>
            <strong>Zespół Klubu Lepsze Życie</strong>
        </p>
        <p style="color: #999; font-size: 12px; margin-top: 20px;">
            Ten email został wysłany na adres {{email}}
        </p>
    </div>
</body>
</html>
                ''',
                text_content='''
Email Własny 📧

Cześć {{name}}!

{{custom_subject}}

{{custom_content}}

Twoje dane są bezpieczne - możesz w każdej chwili:
- Zrezygnować z subskrypcji: {{unsubscribe_url}}
- Usunąć swoje konto: {{delete_account_url}}

Z poważaniem,
Zespół Klubu Lepsze Życie

Ten email został wysłany na adres {{email}}
                ''',
                template_type='custom',
                variables='name,email,custom_subject,custom_content,unsubscribe_url,delete_account_url',
                is_active=True
            )
            db.session.add(custom_template)
        
        db.session.commit()

# Routes
@app.route('/')
def index():
    # Get data from database
    menu_items = MenuItem.query.filter_by(is_active=True).order_by(MenuItem.order).all()
    hero_section = Section.query.filter_by(name='hero', is_active=True).first()
    benefits_section = Section.query.filter_by(name='benefits', is_active=True).first()
    benefits_items = BenefitItem.query.filter_by(is_active=True).order_by(BenefitItem.order).all() if benefits_section else []
    about_section = Section.query.filter_by(name='about', is_active=True).first()
    testimonials_section = Section.query.filter_by(name='testimonials', is_active=True).first()
    testimonials = Testimonial.query.filter_by(is_active=True).order_by(Testimonial.created_at.desc()).limit(3).all() if testimonials_section else []
    cta_section = Section.query.filter_by(name='cta', is_active=True).first()
    faq_section = Section.query.filter_by(name='faq', is_active=True).first()
    social_links = SocialLink.query.filter_by(is_active=True).order_by(SocialLink.order).all()
    faqs = FAQ.query.filter_by(is_active=True).order_by(FAQ.order).all() if faq_section else []
    
    # Get next published and active event from database
    next_event = EventSchedule.query.filter_by(
        is_active=True, 
        is_published=True
    ).filter(
        EventSchedule.event_date > datetime.now()
    ).order_by(EventSchedule.event_date).first()
    
    # Get all events for current month (excluding the one in hero)
    current_month_events = []
    if next_event:
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)
        
        current_month_events = EventSchedule.query.filter_by(
            is_active=True, 
            is_published=True
        ).filter(
            EventSchedule.event_date >= current_month,
            EventSchedule.event_date < next_month,
            EventSchedule.id != next_event.id  # Exclude hero event
        ).order_by(EventSchedule.event_date).all()
    
    return render_template('index.html',
                         next_event=next_event,
                         current_month_events=current_month_events,
                         testimonials=testimonials,
                         testimonials_section=testimonials_section,
                         cta_section=cta_section,
                         faq_section=faq_section,
                         menu_items=menu_items,
                         hero_section=hero_section,
                         benefits_section=benefits_section,
                         benefits_items=benefits_items,
                         about_section=about_section,
                         social_links=social_links,
                         faqs=faqs)

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone', '')
    
    if not name or not email:
        flash('Proszę wypełnić wszystkie wymagane pola.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Save registration to database
        registration = Registration(
            name=name,
            email=email,
            phone=phone,
            status='pending'  # Wymaga zatwierdzenia przez administratora
        )
        db.session.add(registration)
        
        # Add user to email subscription for automatic reminders
        email_service.add_subscriber(email, name, subscription_type='all')
        
        # Email powitalny będzie wysłany dopiero po zatwierdzeniu przez administratora
        
        # Send notification to admin about new registration
        admin_users = User.query.filter_by(is_admin=True).all()
        for admin in admin_users:
            email_service.send_template_email(
                to_email=admin.email,
                template_name='admin_notification',
                variables={
                    'admin_name': admin.username,
                    'new_member_name': name,
                    'new_member_email': email,
                    'registration_date': datetime.now().strftime('%d.%m.%Y %H:%M')
                }
            )
        
        db.session.commit()
    
        return jsonify({
            'success': True,
            'message': f'Dziękujemy {name}! Twoje miejsce zostało zarezerwowane.'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error during registration: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Wystąpił błąd podczas rejestracji. Spróbuj ponownie.'
        }), 500


@app.route('/register-event/<int:event_id>', methods=['POST'])
def register_event(event_id):
    """Zapisy na konkretne wydarzenia"""
    event = EventSchedule.query.get_or_404(event_id)
    
    if not event.is_active or not event.is_published:
        return jsonify({'success': False, 'error': 'Wydarzenie nie jest dostępne'}), 400
    
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone', '')
    wants_club_news = request.form.get('wants_club_news') == 'true'
    
    if not name or not email:
        return jsonify({'success': False, 'error': 'Proszę wypełnić wszystkie wymagane pola.'}), 400
    
    try:
        # Sprawdź czy użytkownik już się zapisał na to wydarzenie
        existing_registration = EventRegistration.query.filter_by(
            event_id=event_id, 
            email=email
        ).first()
        
        if existing_registration:
            return jsonify({'success': False, 'error': 'Jesteś już zapisany na to wydarzenie.'}), 400
        
        # Zapisz na wydarzenie
        registration = EventRegistration(
            event_id=event_id,
            name=name,
            email=email,
            phone=phone,
            wants_club_news=wants_club_news,
            status='confirmed'
        )
        db.session.add(registration)
        
        # Jeśli użytkownik chce dołączyć do klubu
        if wants_club_news:
            email_service.add_subscriber(email, name, subscription_type='all')
        
        # Utwórz grupę odbiorców dla tego wydarzenia (jeśli nie istnieje)
        recipient_group = EventRecipientGroup.query.filter_by(
            event_id=event_id,
            group_type='event_registrations'
        ).first()
        
        if not recipient_group:
            recipient_group = EventRecipientGroup(
                event_id=event_id,
                name=f'Zapisy na {event.title}',
                description=f'Użytkownicy zapisani na wydarzenie: {event.title}',
                group_type='event_registrations',
                criteria_config=json.dumps({'event_id': event_id})
            )
            db.session.add(recipient_group)
        
        # Utwórz harmonogram powiadomień (jeśli nie istnieje)
        notification_types = [
            ('24h_before', timedelta(hours=24)),
            ('1h_before', timedelta(hours=1)),
            ('5min_before', timedelta(minutes=5))
        ]
        
        for notif_type, time_offset in notification_types:
            notification_time = event.event_date - time_offset
            
            # Sprawdź czy powiadomienie już istnieje
            existing_notification = EventNotification.query.filter_by(
                event_id=event_id,
                notification_type=notif_type
            ).first()
            
            if not existing_notification and notification_time > datetime.now():
                notification = EventNotification(
                    event_id=event_id,
                    notification_type=notif_type,
                    scheduled_at=notification_time,
                    subject=f'Przypomnienie: {event.title}',
                    template_name=f'event_reminder_{notif_type}'
                )
                db.session.add(notification)
        
        db.session.commit()
        
        # Wyślij email potwierdzający
        email_service.send_template_email(
            to_email=email,
            template_name='event_registration_confirmation',
            variables={
                'name': name,
                'event_title': event.title,
                'event_date': event.event_date.strftime('%d.%m.%Y o %H:%M'),
                'event_type': event.event_type,
                'meeting_link': event.meeting_link,
                'location': event.location
            }
        )
        
        return jsonify({
            'success': True,
            'message': f'Dziękujemy {name}! Zostałeś zapisany na wydarzenie "{event.title}".'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error during event registration: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Wystąpił błąd podczas zapisu. Spróbuj ponownie.'
        }), 500

# Admin routes for email management
@app.route('/admin/email-schedules')
@login_required
def admin_email_schedules():
    """Admin panel for email schedules"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    schedules = EmailSchedule.query.order_by(EmailSchedule.created_at.desc()).all()
    return render_template('admin/email_schedules.html', schedules=schedules)

# API endpoints for email schedules
@app.route('/admin/api/email-schedules', methods=['GET'])
@login_required
def api_get_email_schedules():
    """Get all email schedules"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        schedules = EmailSchedule.query.order_by(EmailSchedule.created_at.desc()).all()
        schedules_data = []
        
        for schedule in schedules:
            schedule_dict = {
                'id': schedule.id,
                'name': schedule.name,
                'template_type': schedule.template_type,
                'schedule_type': schedule.schedule_type,
                'is_active': schedule.is_active,
                'last_run': schedule.last_run.isoformat() if schedule.last_run else None,
                'next_run': schedule.next_run.isoformat() if schedule.next_run else None,
                'created_at': schedule.created_at.isoformat(),
                'updated_at': schedule.updated_at.isoformat()
            }
            
            # Add specific fields based on schedule type
            if schedule.schedule_type == 'interval':
                schedule_dict['interval_value'] = schedule.interval_value
                schedule_dict['interval_unit'] = schedule.interval_unit
            elif schedule.schedule_type == 'cron':
                schedule_dict['cron_expression'] = schedule.cron_expression
            elif schedule.schedule_type == 'event_based':
                schedule_dict['trigger_event'] = schedule.trigger_event
            
            schedules_data.append(schedule_dict)
        
        return jsonify({'success': True, 'schedules': schedules_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/email-schedules', methods=['POST'])
@login_required
def api_create_email_schedule():
    """Create new email schedule"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        name = request.form.get('name')
        template_type = request.form.get('template_type')
        schedule_type = request.form.get('schedule_type')
        is_active = request.form.get('is_active') == '1'
        
        if not all([name, template_type, schedule_type]):
            return jsonify({'success': False, 'error': 'Wszystkie pola są wymagane'}), 400
        
        # Create schedule object
        schedule = EmailSchedule(
            name=name,
            template_type=template_type,
            schedule_type=schedule_type,
            is_active=is_active
        )
        
        # Set specific fields based on schedule type
        if schedule_type == 'interval':
            interval_value = request.form.get('interval_value', type=int)
            interval_unit = request.form.get('interval_unit')
            if not interval_value or not interval_unit:
                return jsonify({'success': False, 'error': 'Wartość i jednostka interwału są wymagane'}), 400
            
            schedule.interval_value = interval_value
            schedule.interval_unit = interval_unit
            
            # Calculate next run for interval schedules
            schedule.next_run = calculate_next_run_interval(interval_value, interval_unit)
            
        elif schedule_type == 'cron':
            cron_expression = request.form.get('cron_expression')
            if not cron_expression:
                return jsonify({'success': False, 'error': 'Wyrażenie Cron jest wymagane'}), 400
            
            schedule.cron_expression = cron_expression
            
            # Calculate next run for cron schedules
            schedule.next_run = calculate_next_run_cron(cron_expression)
            
        elif schedule_type == 'event_based':
            trigger_event = request.form.get('trigger_event')
            if not trigger_event:
                return jsonify({'success': False, 'error': 'Zdarzenie wyzwalające jest wymagane'}), 400
            
            schedule.trigger_event = trigger_event
            # Event-based schedules don't have next_run until triggered
        
        db.session.add(schedule)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Harmonogram "{name}" został utworzony pomyślnie'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/email-schedules/<int:schedule_id>', methods=['GET'])
@login_required
def api_get_email_schedule(schedule_id):
    """Get specific email schedule"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        schedule = EmailSchedule.query.get_or_404(schedule_id)
        
        schedule_data = {
            'id': schedule.id,
            'name': schedule.name,
            'template_type': schedule.template_type,
            'schedule_type': schedule.schedule_type,
            'is_active': schedule.is_active,
            'last_run': schedule.last_run.isoformat() if schedule.last_run else None,
            'next_run': schedule.next_run.isoformat() if schedule.next_run else None,
            'created_at': schedule.created_at.isoformat(),
            'updated_at': schedule.updated_at.isoformat()
        }
        
        # Add specific fields based on schedule type
        if schedule.schedule_type == 'interval':
            schedule_data['interval_value'] = schedule.interval_value
            schedule_data['interval_unit'] = schedule.interval_unit
        elif schedule.schedule_type == 'cron':
            schedule_data['cron_expression'] = schedule.cron_expression
        elif schedule.schedule_type == 'event_based':
            schedule_data['trigger_event'] = schedule.trigger_event
        
        return jsonify({'success': True, 'schedule': schedule_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/email-schedules/<int:schedule_id>', methods=['PUT'])
@login_required
def api_update_email_schedule(schedule_id):
    """Update email schedule"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        schedule = EmailSchedule.query.get_or_404(schedule_id)
        
        name = request.form.get('name')
        template_type = request.form.get('template_type')
        schedule_type = request.form.get('schedule_type')
        is_active = request.form.get('is_active') == '1'
        
        if not all([name, template_type, schedule_type]):
            return jsonify({'success': False, 'error': 'Wszystkie pola są wymagane'}), 400
        
        # Update basic fields
        schedule.name = name
        schedule.template_type = template_type
        schedule.is_active = is_active
        
        # Handle schedule type change
        if schedule.schedule_type != schedule_type:
            schedule.schedule_type = schedule_type
            
            # Clear old specific fields
            schedule.interval_value = None
            schedule.interval_unit = None
            schedule.cron_expression = None
            schedule.trigger_event = None
        
        # Set specific fields based on schedule type
        if schedule_type == 'interval':
            interval_value = request.form.get('interval_value', type=int)
            interval_unit = request.form.get('interval_unit')
            if not interval_value or not interval_unit:
                return jsonify({'success': False, 'error': 'Wartość i jednostka interwału są wymagane'}), 400
            
            schedule.interval_value = interval_value
            schedule.interval_unit = interval_unit
            
            # Recalculate next run
            schedule.next_run = calculate_next_run_interval(interval_value, interval_unit)
            
        elif schedule_type == 'cron':
            cron_expression = request.form.get('cron_expression')
            if not cron_expression:
                return jsonify({'success': False, 'error': 'Wyrażenie Cron jest wymagane'}), 400
            
            schedule.cron_expression = cron_expression
            
            # Recalculate next run
            schedule.next_run = calculate_next_run_cron(cron_expression)
            
        elif schedule_type == 'event_based':
            trigger_event = request.form.get('trigger_event')
            if not trigger_event:
                return jsonify({'success': False, 'error': 'Zdarzenie wyzwalające jest wymagane'}), 400
            
            schedule.trigger_event = trigger_event
            # Event-based schedules don't have next_run until triggered
        
        schedule.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Harmonogram "{name}" został zaktualizowany pomyślnie'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/email-schedules/<int:schedule_id>', methods=['DELETE'])
@login_required
def api_delete_email_schedule(schedule_id):
    """Delete email schedule"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        schedule = EmailSchedule.query.get_or_404(schedule_id)
        name = schedule.name
        
        db.session.delete(schedule)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Harmonogram "{name}" został usunięty pomyślnie'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/email-schedules/<int:schedule_id>/toggle', methods=['POST'])
@login_required
def api_toggle_email_schedule(schedule_id):
    """Toggle email schedule status"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        schedule = EmailSchedule.query.get_or_404(schedule_id)
        schedule.is_active = not schedule.is_active
        
        if schedule.is_active and schedule.schedule_type in ['interval', 'cron']:
            # Recalculate next run for active schedules
            if schedule.schedule_type == 'interval':
                schedule.next_run = calculate_next_run_interval(schedule.interval_value, schedule.interval_unit)
            elif schedule.schedule_type == 'cron':
                schedule.next_run = calculate_next_run_cron(schedule.cron_expression)
        
        schedule.updated_at = datetime.utcnow()
        db.session.commit()
        
        status_text = 'aktywowany' if schedule.is_active else 'deaktywowany'
        return jsonify({
            'success': True, 
            'message': f'Harmonogram "{schedule.name}" został {status_text}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/email-schedules/<int:schedule_id>/run', methods=['POST'])
@login_required
def api_run_email_schedule(schedule_id):
    """Run email schedule manually"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        schedule = EmailSchedule.query.get_or_404(schedule_id)
        
        if not schedule.is_active:
            return jsonify({'success': False, 'error': 'Harmonogram jest nieaktywny'}), 400
        
        # Execute the schedule
        result = execute_email_schedule(schedule)
        
        # Update last_run and next_run
        schedule.last_run = datetime.utcnow()
        if schedule.schedule_type in ['interval', 'cron']:
            if schedule.schedule_type == 'interval':
                schedule.next_run = calculate_next_run_interval(schedule.interval_value, schedule.interval_unit)
            elif schedule.schedule_type == 'cron':
                schedule.next_run = calculate_next_run_cron(schedule.cron_expression)
        
        schedule.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Harmonogram "{schedule.name}" został uruchomiony pomyślnie. {result}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/email-schedules/run-all', methods=['POST'])
@login_required
def api_run_all_email_schedules():
    """Run all active email schedules"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        active_schedules = EmailSchedule.query.filter_by(is_active=True).all()
        
        if not active_schedules:
            return jsonify({'success': False, 'error': 'Brak aktywnych harmonogramów'}), 400
        
        results = []
        for schedule in active_schedules:
            try:
                result = execute_email_schedule(schedule)
                results.append(f"{schedule.name}: {result}")
                
                # Update last_run and next_run
                schedule.last_run = datetime.utcnow()
                if schedule.schedule_type in ['interval', 'cron']:
                    if schedule.schedule_type == 'interval':
                        schedule.next_run = calculate_next_run_interval(schedule.interval_value, schedule.interval_unit)
                    elif schedule.schedule_type == 'cron':
                        schedule.next_run = calculate_next_run_cron(schedule.cron_expression)
                
                schedule.updated_at = datetime.utcnow()
                
            except Exception as e:
                results.append(f"{schedule.name}: Błąd - {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Uruchomiono {len(active_schedules)} harmonogramów. Wyniki: {" | ".join(results)}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/email-campaigns')
@login_required
def admin_email_campaigns():
    """Admin panel for email campaigns"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    campaigns = CustomEmailCampaign.query.order_by(CustomEmailCampaign.created_at.desc()).all()
    return render_template('admin/email_campaigns.html', campaigns=campaigns)

# API endpoints for email campaigns
@app.route('/admin/api/email-campaigns', methods=['GET'])
@login_required
def api_get_email_campaigns():
    """Get all email campaigns"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        campaigns = CustomEmailCampaign.query.order_by(CustomEmailCampaign.created_at.desc()).all()
        campaigns_data = []
        
        for campaign in campaigns:
            campaign_dict = {
                'id': campaign.id,
                'name': campaign.name,
                'subject': campaign.subject,
                'recipient_type': campaign.recipient_type,
                'send_type': campaign.send_type,
                'status': campaign.status,
                'sent_count': campaign.sent_count,
                'total_count': campaign.total_count,
                'created_at': campaign.created_at.isoformat(),
                'updated_at': campaign.updated_at.isoformat()
            }
            
            # Add specific fields based on recipient type
            if campaign.recipient_type == 'specific':
                campaign_dict['recipient_emails'] = campaign.recipient_emails
            elif campaign.recipient_type == 'filtered':
                campaign_dict['recipient_filters'] = campaign.recipient_filters
            
            # Add scheduling info
            if campaign.send_type == 'scheduled':
                campaign_dict['scheduled_at'] = campaign.scheduled_at.isoformat() if campaign.scheduled_at else None
            
            campaigns_data.append(campaign_dict)
        
        return jsonify({'success': True, 'campaigns': campaigns_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/email-campaigns', methods=['POST'])
@login_required
def api_create_email_campaign():
    """Create new email campaign"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        name = request.form.get('name')
        subject = request.form.get('subject')
        html_content = request.form.get('html_content')
        text_content = request.form.get('text_content')
        recipient_type = request.form.get('recipient_type')
        send_type = request.form.get('send_type')
        
        if not all([name, subject, html_content, recipient_type, send_type]):
            return jsonify({'success': False, 'error': 'Wszystkie wymagane pola muszą być wypełnione'}), 400
        
        # Create campaign object
        campaign = CustomEmailCampaign(
            name=name,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            recipient_type=recipient_type,
            send_type=send_type,
            status='draft'
        )
        
        # Set recipient data based on type
        if recipient_type == 'specific':
            recipient_emails = request.form.get('recipient_emails')
            if not recipient_emails:
                return jsonify({'success': False, 'error': 'Adresy e-mail są wymagane dla konkretnych odbiorców'}), 400
            
            # Parse emails and store as JSON
            emails_list = [email.strip() for email in recipient_emails.split('\n') if email.strip()]
            campaign.recipient_emails = json.dumps(emails_list)
            campaign.total_count = len(emails_list)
            
        elif recipient_type == 'filtered':
            recipient_filters = request.form.get('recipient_filters')
            if recipient_filters:
                campaign.recipient_filters = recipient_filters
                # Calculate total count based on filters
                campaign.total_count = calculate_filtered_recipients_count(recipient_filters)
            else:
                campaign.total_count = 0
                
        elif recipient_type == 'all':
            # Count all approved subscribers
            campaign.total_count = email_service.get_approved_subscribers_count()
        
        # Set scheduling if needed
        if send_type == 'scheduled':
            scheduled_at = request.form.get('scheduled_at')
            if scheduled_at:
                campaign.scheduled_at = datetime.fromisoformat(scheduled_at.replace('T', ' '))
                campaign.status = 'scheduled'
        
        db.session.add(campaign)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Kampania "{name}" została utworzona pomyślnie'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/email-campaigns/<int:campaign_id>', methods=['GET'])
@login_required
def api_get_email_campaign(campaign_id):
    """Get specific email campaign"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        campaign = CustomEmailCampaign.query.get_or_404(campaign_id)
        
        campaign_data = {
            'id': campaign.id,
            'name': campaign.name,
            'subject': campaign.subject,
            'html_content': campaign.html_content,
            'text_content': campaign.text_content,
            'recipient_type': campaign.recipient_type,
            'send_type': campaign.send_type,
            'status': campaign.status,
            'sent_count': campaign.sent_count,
            'total_count': campaign.total_count,
            'created_at': campaign.created_at.isoformat(),
            'updated_at': campaign.updated_at.isoformat()
        }
        
        # Add specific fields based on recipient type
        if campaign.recipient_type == 'specific':
            campaign_data['recipient_emails'] = campaign.recipient_emails
        elif campaign.recipient_type == 'filtered':
            campaign_data['recipient_filters'] = campaign.recipient_filters
        
        # Add scheduling info
        if campaign.send_type == 'scheduled':
            campaign_data['scheduled_at'] = campaign.scheduled_at.isoformat() if campaign.scheduled_at else None
        
        return jsonify({'success': True, 'campaign': campaign_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/email-campaigns/<int:campaign_id>', methods=['PUT'])
@login_required
def api_update_email_campaign(campaign_id):
    """Update email campaign"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        campaign = CustomEmailCampaign.query.get_or_404(campaign_id)
        
        name = request.form.get('name')
        subject = request.form.get('subject')
        html_content = request.form.get('html_content')
        text_content = request.form.get('text_content')
        recipient_type = request.form.get('recipient_type')
        send_type = request.form.get('send_type')
        
        if not all([name, subject, html_content, recipient_type, send_type]):
            return jsonify({'success': False, 'error': 'Wszystkie wymagane pola muszą być wypełnione'}), 400
        
        # Update basic fields
        campaign.name = name
        campaign.subject = subject
        campaign.html_content = html_content
        campaign.text_content = text_content
        campaign.recipient_type = recipient_type
        campaign.send_type = send_type
        
        # Update recipient data based on type
        if recipient_type == 'specific':
            recipient_emails = request.form.get('recipient_emails')
            if not recipient_emails:
                return jsonify({'success': False, 'error': 'Adresy e-mail są wymagane dla konkretnych odbiorców'}), 400
            
            # Parse emails and store as JSON
            emails_list = [email.strip() for email in recipient_emails.split('\n') if email.strip()]
            campaign.recipient_emails = json.dumps(emails_list)
            campaign.total_count = len(emails_list)
            
        elif recipient_type == 'filtered':
            recipient_filters = request.form.get('recipient_filters')
            if recipient_filters:
                campaign.recipient_filters = recipient_filters
                # Calculate total count based on filters
                campaign.total_count = calculate_filtered_recipients_count(recipient_filters)
            else:
                campaign.total_count = 0
                
        elif recipient_type == 'all':
            # Count all approved subscribers
            campaign.total_count = email_service.get_approved_subscribers_count()
        
        # Update scheduling if needed
        if send_type == 'scheduled':
            scheduled_at = request.form.get('scheduled_at')
            if scheduled_at:
                campaign.scheduled_at = datetime.fromisoformat(scheduled_at.replace('T', ' '))
                campaign.status = 'scheduled'
            else:
                campaign.status = 'draft'
        else:
            campaign.status = 'draft'
            campaign.scheduled_at = None
        
        campaign.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Kampania "{name}" została zaktualizowana pomyślnie'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/email-campaigns/<int:campaign_id>', methods=['DELETE'])
@login_required
def api_delete_email_campaign(campaign_id):
    """Delete email campaign"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        campaign = CustomEmailCampaign.query.get_or_404(campaign_id)
        name = campaign.name
        
        db.session.delete(campaign)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Kampania "{name}" została usunięta pomyślnie'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/email-campaigns/<int:campaign_id>/send', methods=['POST'])
@login_required
def api_send_email_campaign(campaign_id):
    """Send email campaign"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        campaign = CustomEmailCampaign.query.get_or_404(campaign_id)
        
        if campaign.status == 'completed':
            return jsonify({'success': False, 'error': 'Kampania została już wysłana'}), 400
        
        # Get recipients based on type
        recipients = get_campaign_recipients(campaign)
        if not recipients:
            return jsonify({'success': False, 'error': 'Brak odbiorców dla tej kampanii'}), 400
        
        # Send emails
        sent_count = 0
        for recipient in recipients:
            try:
                # Prepare variables for template
                variables = {
                    'name': recipient.get('name', 'Użytkowniku'),
                    'email': recipient['email'],
                    'unsubscribe_url': url_for('unsubscribe_email', token=recipient.get('unsubscribe_token', ''), _external=True),
                    'delete_account_url': url_for('delete_account', token=recipient.get('delete_token', ''), _external=True)
                }
                
                # Send email using custom content
                result = email_service.send_custom_email(
                    to_email=recipient['email'],
                    subject=campaign.subject,
                    html_content=campaign.html_content,
                    text_content=campaign.text_content,
                    variables=variables
                )
                
                if result:
                    sent_count += 1
                    
            except Exception as e:
                print(f"Error sending campaign email to {recipient['email']}: {str(e)}")
        
        # Update campaign status
        campaign.status = 'completed'
        campaign.sent_count = sent_count
        campaign.sent_at = datetime.utcnow()
        campaign.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Kampania "{campaign.name}" została wysłana pomyślnie do {sent_count}/{len(recipients)} odbiorców'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/recipient-groups')
@login_required
def admin_recipient_groups():
    """Admin panel for recipient groups"""
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    groups = EmailRecipientGroup.query.order_by(EmailRecipientGroup.created_at.desc()).all()
    return render_template('admin/recipient_groups.html', groups=groups)

# API endpoints for recipient groups
@app.route('/admin/api/recipient-groups', methods=['GET', 'POST'])
@login_required
def api_recipient_groups():
    """Get all recipient groups or create new one"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        try:
            groups = EmailRecipientGroup.query.order_by(EmailRecipientGroup.created_at.desc()).all()
            groups_data = []
            
            for group in groups:
                group_dict = {
                    'id': group.id,
                    'name': group.name,
                    'description': group.description,
                    'criteria_type': group.criteria_type,
                    'member_count': group.member_count,
                    'is_active': group.is_active,
                    'created_at': group.created_at.isoformat(),
                    'updated_at': group.updated_at.isoformat()
                }
                
                # Add criteria configuration if exists
                if group.criteria_config:
                    group_dict['criteria_config'] = group.criteria_config
                
                groups_data.append(group_dict)
            
            return jsonify({'success': True, 'groups': groups_data})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.form.to_dict()
            
            # Convert checkbox to boolean
            data['is_active'] = 'is_active' in request.form
            
            new_group = EmailRecipientGroup(
                name=data['name'],
                description=data.get('description', ''),
                criteria_type=data['criteria_type'],
                criteria_config=data.get('criteria_config', ''),
                is_active=data['is_active']
            )
            
            db.session.add(new_group)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': f'Grupa "{new_group.name}" została utworzona pomyślnie',
                'id': new_group.id
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/recipient-groups/<int:group_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_recipient_group_by_id(group_id):
    """Get, update or delete recipient group by ID"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    group = EmailRecipientGroup.query.get_or_404(group_id)
    
    if request.method == 'GET':
        try:
            group_dict = {
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'criteria_type': group.criteria_type,
                'member_count': group.member_count,
                'is_active': group.is_active,
                'created_at': group.created_at.isoformat(),
                'updated_at': group.updated_at.isoformat()
            }
            
            if group.criteria_config:
                group_dict['criteria_config'] = group.criteria_config
            
            return jsonify({'success': True, 'group': group_dict})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'PUT':
        try:
            data = request.form.to_dict()
            
            # Convert checkbox to boolean
            data['is_active'] = 'is_active' in request.form
            
            group.name = data['name']
            group.description = data.get('description', '')
            group.criteria_type = data['criteria_type']
            group.criteria_config = data.get('criteria_config', '')
            group.is_active = data['is_active']
            group.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': f'Grupa "{group.name}" została zaktualizowana pomyślnie'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            name = group.name
            
            db.session.delete(group)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': f'Grupa "{name}" została usunięta pomyślnie'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/api/check-schedules', methods=['POST'])
@login_required
def api_check_schedules():
    """Manually check and run due schedules"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        check_and_run_schedules()
        return jsonify({
            'success': True, 
            'message': 'Sprawdzanie harmonogramów zostało uruchomione'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password) and user.is_admin:
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Nieprawidłowa nazwa użytkownika lub hasło.', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    stats = {
        'total_registrations': Registration.query.count(),
        'pending_registrations': Registration.query.filter_by(status='pending').count(),
        'total_testimonials': Testimonial.query.count(),
        'active_menu_items': MenuItem.query.filter_by(is_active=True).count()
    }
    
    recent_registrations = Registration.query.order_by(Registration.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', stats=stats, recent_registrations=recent_registrations)

@app.route('/admin/menu')
@login_required
def admin_menu():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    menu_items = MenuItem.query.order_by(MenuItem.order).all()
    return render_template('admin/menu.html', menu_items=menu_items)

@app.route('/admin/sections')
@login_required
def admin_sections():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    sections = Section.query.order_by(Section.order).all()
    return render_template('admin/sections.html', sections=sections)

@app.route('/admin/benefits')
@login_required
def admin_benefits():
    if not current_user.is_admin:
        return redirect(url_for('admin_login'))
    
    benefits = BenefitItem.query.order_by(BenefitItem.order).all()
    return render_template('admin/benefits.html', benefits=benefits)

@app.route('/admin/testimonials')
@login_required
def admin_testimonials():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
    return render_template('admin/testimonials.html', testimonials=testimonials)

@app.route('/admin/registrations')
@login_required
def admin_registrations():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    registrations = Registration.query.order_by(Registration.created_at.desc()).all()
    return render_template('admin/registrations.html', registrations=registrations)

@app.route('/admin/social')
@login_required
def admin_social():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    social_links = SocialLink.query.order_by(SocialLink.order).all()
    return render_template('admin/social.html', social_links=social_links)

@app.route('/admin/faq')
@login_required
def admin_faq():
    if not current_user.is_admin:
        return redirect(url_for('admin_login'))
    
    faqs = FAQ.query.order_by(FAQ.order).all()
    return render_template('admin/faq.html', faqs=faqs)

@app.route('/admin/seo')
@login_required
def admin_seo():
    if not current_user.is_admin:
        return redirect(url_for('admin_login'))
    seo_settings = SEOSettings.query.all()
    return render_template('admin/seo.html', seo_settings=seo_settings)

@app.route('/admin/event-schedule')
@login_required
def admin_event_schedule():
    if not current_user.is_admin:
        return redirect(url_for('admin_login'))
    
    events = EventSchedule.query.order_by(EventSchedule.event_date.desc()).all()
    return render_template('admin/event_schedule.html', events=events)

@app.route('/admin/pages')
@login_required
def admin_pages():
    if not current_user.is_admin:
        return redirect(url_for('admin_login'))
    return render_template('admin/pages.html')

@app.route('/admin/email-templates')
@login_required
def email_templates():
    if not current_user.is_admin:
        return redirect(url_for('admin_login'))
    return render_template('admin/email_templates.html')

# API routes for content management
@app.route('/admin/api/menu', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_menu():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        menu_items = MenuItem.query.order_by(MenuItem.order).all()
        return jsonify([{
            'id': item.id,
            'title': item.title,
            'url': item.url,
            'order': item.order,
            'is_active': item.is_active
        } for item in menu_items])
    
    elif request.method == 'POST':
        # Obsługujemy zarówno JSON jak i FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            # Konwertujemy checkbox na boolean - sprawdzamy wartość pola
            if 'is_active' in data:
                data['is_active'] = data['is_active'] in [True, 'true', 'True', '1', 1]
            else:
                data['is_active'] = False
        
        new_item = MenuItem(
            title=data['title'],
            url=data['url'],
            order=data['order'],
            is_active=data.get('is_active', True)
        )
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'success': True, 'item': {
            'id': new_item.id,
            'title': new_item.title,
            'url': new_item.url,
            'order': new_item.order,
            'is_active': new_item.is_active
        }})
    
    elif request.method == 'PUT':
        data = request.get_json() if request.is_json else request.form.to_dict()
        item_id = data.get('id')
        item = MenuItem.query.get(item_id)
        
        if not item:
            return jsonify({'success': False, 'error': 'Menu item not found'}), 404
        
        item.title = data.get('title', item.title)
        item.url = data.get('url', item.url)
        item.order = data.get('order', item.order)
        item.is_active = data.get('is_active', item.is_active)
        
        db.session.commit()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        try:
            item_id = request.args.get('id', type=int)
            
            if not item_id:
                return jsonify({'success': False, 'message': 'Brak ID elementu menu'}), 400
            
            item = MenuItem.query.get(item_id)
            if not item:
                return jsonify({'success': False, 'message': 'Element menu nie został znaleziony'}), 404
            
            db.session.delete(item)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Element menu został usunięty pomyślnie'})
            
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting menu item: {str(e)}")
            return jsonify({'success': False, 'message': f'Wystąpił błąd podczas usuwania elementu menu: {str(e)}'}), 500

@app.route('/admin/api/sections', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_sections():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        sections = Section.query.order_by(Section.order).all()
        return jsonify([{
            'id': section.id,
            'name': section.name,
            'title': section.title,
            'subtitle': section.subtitle,
            'content': section.content,
            'background_image': section.background_image,
            'pillars_data': section.pillars_data,
            'final_text': section.final_text,
            'floating_cards_data': section.floating_cards_data,
            'enable_pillars': section.enable_pillars,
            'enable_floating_cards': section.enable_floating_cards,
            'pillars_count': section.pillars_count,
            'floating_cards_count': section.floating_cards_count,
            'order': section.order,
            'is_active': section.is_active
        } for section in sections])
    
    elif request.method == 'POST':
        # Obsługujemy zarówno JSON jak i FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            # Konwertujemy checkbox na boolean - sprawdzamy wartość pola
            if 'is_active' in data:
                data['is_active'] = data['is_active'] in [True, 'true', 'True', '1', 1]
            else:
                data['is_active'] = False
            # Konwertujemy boolean na prawdziwe boolean
            if 'enable_pillars' in data:
                data['enable_pillars'] = data['enable_pillars'] in [True, 'true', 'True', '1', 1]
            else:
                data['enable_pillars'] = False
            if 'enable_floating_cards' in data:
                data['enable_floating_cards'] = data['enable_floating_cards'] in [True, 'true', 'True', '1', 1]
            else:
                data['enable_floating_cards'] = False
        
        new_section = Section(
            name=data['name'],
            title=data.get('title'),
            subtitle=data.get('subtitle'),
            content=data.get('content'),
            background_image=data.get('background_image'),
            pillars_data=data.get('pillars_data'),
            final_text=data.get('final_text'),
            floating_cards_data=data.get('floating_cards_data'),
            enable_pillars=data.get('enable_pillars', False),
            enable_floating_cards=data.get('enable_floating_cards', False),
            pillars_count=data.get('pillars_count', 4),
            floating_cards_count=data.get('floating_cards_count', 3),
            order=data.get('order', 0),
            is_active=data.get('is_active', True)
        )
        db.session.add(new_section)
        db.session.commit()
        return jsonify({'success': True, 'id': new_section.id})
    
    elif request.method == 'PUT':
        # Obsługujemy zarówno JSON jak i FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            print(f"Received form data: {data}")
            print(f"DEBUG: request.form keys: {list(request.form.keys())}")
            print(f"DEBUG: request.form values: {list(request.form.values())}")
            print(f"DEBUG: request.form.getlist('is_active'): {request.form.getlist('is_active')}")
            
            # Konwertujemy checkbox na boolean - sprawdzamy wartość pola
            # Jeśli wartość to 'true' (string) lub true (boolean), ustaw na True
            print(f"DEBUG: is_active raw value: {data.get('is_active')} (type: {type(data.get('is_active'))})")
            if 'is_active' in data:
                original_value = data['is_active']
                data['is_active'] = data['is_active'] in [True, 'true', 'True', '1', 1]
                print(f"DEBUG: is_active converted from '{original_value}' to {data['is_active']}")
            else:
                data['is_active'] = False
                print(f"DEBUG: is_active not found, set to False")
            
            print(f"DEBUG: Final data['is_active'] value: {data['is_active']}")
            print(f"DEBUG: Final data['is_active'] type: {type(data['is_active'])}")
            # Konwertujemy boolean na prawdziwe boolean
            if 'enable_pillars' in data:
                # Jeśli wartość to 'true' (string) lub true (boolean), ustaw na True
                data['enable_pillars'] = data['enable_pillars'] in [True, 'true', 'True', '1', 1]
            else:
                data['enable_pillars'] = False  # Jeśli pole nie jest wysłane, ustaw na False
                
            if 'enable_floating_cards' in data:
                # Jeśli wartość to 'true' (string) lub true (boolean), ustaw na True
                data['enable_floating_cards'] = data['enable_floating_cards'] in [True, 'true', 'True', '1', 1]
            else:
                data['enable_floating_cards'] = False  # Jeśli pole nie jest wysłane, ustaw na False
            
            # Usuwamy ukryte pola, które mogą powodować konflikty
            if 'enable_pillars_hidden' in data:
                del data['enable_pillars_hidden']
            if 'enable_floating_cards_hidden' in data:
                del data['enable_floating_cards_hidden']
        
        print(f"Processed data for update: {data}")
        
        section = Section.query.get(data['id'])
        if section:
            # Only update fields that are provided
            if 'name' in data:
                section.name = data['name']
            if 'title' in data:
                section.title = data['title']
            if 'subtitle' in data:
                section.subtitle = data['subtitle']
            if 'content' in data:
                section.content = data['content']
            if 'background_image' in data:
                section.background_image = data['background_image']
            if 'pillars_data' in data:
                section.pillars_data = data['pillars_data']
            if 'final_text' in data:
                section.final_text = data['final_text']
            if 'floating_cards_data' in data:
                section.floating_cards_data = data['floating_cards_data']
            if 'enable_pillars' in data:
                section.enable_pillars = data['enable_pillars']
                print(f"Updated enable_pillars to: {section.enable_pillars}")
            if 'enable_floating_cards' in data:
                section.enable_floating_cards = data['enable_floating_cards']
                print(f"Updated enable_floating_cards to: {section.enable_floating_cards}")
            if 'pillars_count' in data:
                section.pillars_count = data['pillars_count']
            if 'floating_cards_count' in data:
                section.floating_cards_count = data['floating_cards_count']
            if 'order' in data:
                section.order = data['order']
            if 'is_active' in data:
                section.is_active = data['is_active']
                print(f"Updated is_active to: {section.is_active}")
            
            db.session.commit()
            print(f"Section {section.id} updated successfully")
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Section not found'}), 404
    
    elif request.method == 'DELETE':
        try:
            section_id = request.args.get('id', type=int)
            if not section_id:
                return jsonify({'success': False, 'message': 'Brak ID sekcji'}), 400
            
            section = Section.query.get(section_id)
            if not section:
                return jsonify({'success': False, 'message': 'Sekcja nie została znaleziona'}), 404
            
            db.session.delete(section)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Sekcja została usunięta pomyślnie'})
            
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting section: {str(e)}")
            return jsonify({'success': False, 'message': f'Wystąpił błąd podczas usuwania sekcji: {str(e)}'}), 500

@app.route('/admin/api/sections/<int:section_id>', methods=['GET'])
@login_required
def api_section_by_id(section_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    section = Section.query.get(section_id)
    if section:
        return jsonify({
            'success': True,
            'section': {
                'id': section.id,
                'name': section.name,
                'title': section.title,
                'subtitle': section.subtitle,
                'content': section.content,
                'background_image': section.background_image,
                'pillars_data': section.pillars_data,
                'final_text': section.final_text,
                'floating_cards_data': section.floating_cards_data,
                'enable_pillars': section.enable_pillars,
                'enable_floating_cards': section.enable_floating_cards,
                'pillars_count': section.pillars_count,
                'floating_cards_count': section.floating_cards_count,
                'order': section.order,
                'is_active': section.is_active
            }
        })
    return jsonify({'success': False, 'error': 'Section not found'}), 404

@app.route('/admin/api/sections/bulk-update', methods=['POST'])
@login_required
def api_sections_bulk_update():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        sections_data = data.get('sections', [])
        
        for section_data in sections_data:
            section = Section.query.get(section_data['id'])
            if section:
                section.name = section_data.get('name', '')
                section.title = section_data.get('title', '')
                section.subtitle = section_data.get('subtitle', '')
                section.content = section_data.get('content', '')
                section.pillars_data = section_data.get('pillars_data')
                section.final_text = section_data.get('final_text')
                section.floating_cards_data = section_data.get('floating_cards_data')
                section.enable_pillars = section_data.get('enable_pillars', False)
                section.enable_floating_cards = section_data.get('enable_floating_cards', False)
                section.pillars_count = section_data.get('pillars_count', 4)
                section.floating_cards_count = section_data.get('floating_cards_count', 3)
                section.order = section_data.get('order', 0)
                section.is_active = section_data.get('is_active', True)
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/benefits', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_benefits():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        benefits = BenefitItem.query.order_by(BenefitItem.order).all()
        return jsonify([{
            'id': item.id,
            'title': item.title,
            'description': item.description,
            'icon': item.icon,
            'image': item.image,
            'order': item.order,
            'is_active': item.is_active
        } for item in benefits])
    
    elif request.method == 'POST':
        # Obsługujemy FormData z plikami
        data = request.form.to_dict()
        data['is_active'] = 'is_active' in request.form
        
        # Obsługa uploadu pliku
        image_path = ''
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                # Sprawdź rozszerzenie pliku
                allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    # Generuj unikalną nazwę pliku
                    filename = f"{uuid.uuid4().hex}.{file.filename.rsplit('.', 1)[1].lower()}"
                    filepath = os.path.join('static', 'images', 'benefits', filename)
                    
                    # Zapisz plik
                    try:
                        file.save(filepath)
                        image_path = filepath
                    except Exception as e:
                        return jsonify({'success': False, 'error': f'Błąd podczas zapisywania pliku: {str(e)}'}), 500
                else:
                    return jsonify({'success': False, 'error': 'Niedozwolony format pliku. Dozwolone: PNG, JPG, JPEG, GIF, WEBP'}), 400
        
        new_benefit = BenefitItem(
            title=data['title'],
            description=data.get('description', ''),
            icon=data.get('icon', ''),
            image=image_path,
            order=data.get('order', 0),
            is_active=data.get('is_active', True)
        )
        db.session.add(new_benefit)
        db.session.commit()
        return jsonify({'success': True, 'id': new_benefit.id})
    
    elif request.method == 'PUT':
        # Obsługujemy FormData z plikami
        data = request.form.to_dict()
        data['is_active'] = 'is_active' in request.form
        
        benefit = BenefitItem.query.get(data['id'])
        if benefit:
            # Obsługa uploadu nowego pliku
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    # Sprawdź rozszerzenie pliku
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                    if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                        # Generuj unikalną nazwę pliku
                        filename = f"{uuid.uuid4().hex}.{file.filename.rsplit('.', 1)[1].lower()}"
                        filepath = os.path.join('static', 'images', 'benefits', filename)
                        
                        # Usuń stary plik jeśli istnieje
                        if benefit.image and os.path.exists(benefit.image):
                            try:
                                os.remove(benefit.image)
                            except:
                                pass  # Ignoruj błędy usuwania
                        
                        # Zapisz nowy plik
                        try:
                            file.save(filepath)
                            benefit.image = filepath
                        except Exception as e:
                            return jsonify({'success': False, 'error': f'Błąd podczas zapisywania pliku: {str(e)}'}), 500
                    else:
                        return jsonify({'success': False, 'error': 'Niedozwolony format pliku. Dozwolone: PNG, JPG, JPEG, GIF, WEBP'}), 400
            
            benefit.title = data['title']
            benefit.description = data.get('description', '')
            benefit.icon = data.get('icon', '')
            benefit.order = data.get('order', 0)
            benefit.is_active = data.get('is_active', True)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Benefit not found'}), 404
    
    elif request.method == 'DELETE':
        try:
            benefit_id = request.args.get('id', type=int)
            if not benefit_id:
                return jsonify({'success': False, 'message': 'Brak ID korzyści'}), 400
            
            benefit = BenefitItem.query.get(benefit_id)
            if not benefit:
                return jsonify({'success': False, 'message': 'Korzyść nie została znaleziona'}), 404
            
            # Usuń plik obrazu jeśli istnieje
            if benefit.image and os.path.exists(benefit.image):
                try:
                    os.remove(benefit.image)
                except Exception as e:
                    print(f"Warning: Could not remove image file {benefit.image}: {str(e)}")
                    pass  # Ignoruj błędy usuwania pliku
            
            db.session.delete(benefit)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Korzyść została usunięta pomyślnie'})
            
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting benefit: {str(e)}")
            return jsonify({'success': False, 'message': f'Wystąpił błąd podczas usuwania korzyści: {str(e)}'}), 500

@app.route('/admin/api/social', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_social():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        social_links = SocialLink.query.order_by(SocialLink.order).all()
        return jsonify([{
            'id': link.id,
            'platform': link.platform,
            'url': link.url,
            'icon': link.icon,
            'order': link.order,
            'is_active': link.is_active
        } for link in social_links])
    
    elif request.method == 'POST':
        # Obsługujemy zarówno JSON jak i FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            # Konwertujemy checkbox na boolean - sprawdzamy wartość pola
            if 'is_active' in data:
                data['is_active'] = data['is_active'] in [True, 'true', 'True', '1', 1]
            else:
                data['is_active'] = False
        
        new_link = SocialLink(
            platform=data['platform'],
            url=data['url'],
            icon=data.get('icon', ''),
            order=data.get('order', 0),
            is_active=data.get('is_active', True)
        )
        db.session.add(new_link)
        db.session.commit()
        return jsonify({'success': True, 'id': new_link.id})
    
    elif request.method == 'PUT':
        # Obsługujemy zarówno JSON jak i FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            # Konwertujemy checkbox na boolean - sprawdzamy wartość pola
            if 'is_active' in data:
                data['is_active'] = data['is_active'] in [True, 'true', 'True', '1', 1]
            else:
                data['is_active'] = False
        
        link = SocialLink.query.get(data['id'])
        if link:
            link.platform = data['platform']
            link.url = data['url']
            link.icon = data.get('icon', '')
            link.order = data.get('order', 0)
            link.is_active = data.get('is_active', True)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Social link not found'}), 404
    
    elif request.method == 'DELETE':
        try:
            link_id = request.args.get('id', type=int)
            if not link_id:
                return jsonify({'success': False, 'message': 'Brak ID linku społecznościowego'}), 400
            
            link = SocialLink.query.get(link_id)
            if not link:
                return jsonify({'success': False, 'message': 'Link społecznościowy nie został znaleziony'}), 404
            
            db.session.delete(link)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Link społecznościowy został usunięty pomyślnie'})
            
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting social link: {str(e)}")
            return jsonify({'success': False, 'message': f'Wystąpił błąd podczas usuwania linku społecznościowego: {str(e)}'}), 500

@app.route('/admin/api/faq', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_faq():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        faqs = FAQ.query.order_by(FAQ.order).all()
        return jsonify([{
            'id': faq.id,
            'question': faq.question,
            'answer': faq.answer,
            'order': faq.order,
            'is_active': faq.is_active
        } for faq in faqs])
    
    elif request.method == 'POST':
        # Obsługujemy zarówno JSON jak i FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            # Konwertujemy checkbox na boolean - sprawdzamy wartość pola
            if 'is_active' in data:
                data['is_active'] = data['is_active'] in [True, 'true', 'True', '1', 1]
            else:
                data['is_active'] = False
        
        new_faq = FAQ(
            question=data['question'],
            answer=data['answer'],
            order=data.get('order', 0),
            is_active=data.get('is_active', True)
        )
        db.session.add(new_faq)
        db.session.commit()
        return jsonify({'success': True, 'id': new_faq.id})
    
    elif request.method == 'PUT':
        # Obsługujemy zarówno JSON jak i FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            # Konwertujemy checkbox na boolean
            data['is_active'] = 'is_active' in request.form
        
        faq = FAQ.query.get(data['id'])
        if faq:
            faq.question = data['question']
            faq.answer = data['answer']
            faq.order = data.get('order', 0)
            faq.is_active = data.get('is_active', True)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'FAQ not found'}), 404
    
    elif request.method == 'DELETE':
        faq_id = request.args.get('id', type=int)
        faq = FAQ.query.get(faq_id)
        if faq:
            db.session.delete(faq)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'FAQ not found'}), 404

@app.route('/admin/api/testimonials', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_testimonials():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
        return jsonify([{
            'id': testimonial.id,
            'author_name': testimonial.author_name,
            'content': testimonial.content,
            'member_since': testimonial.member_since,
            'rating': testimonial.rating,
            'is_active': testimonial.is_active,
            'created_at': testimonial.created_at.isoformat() if testimonial.created_at else None
        } for testimonial in testimonials])
    
    elif request.method == 'POST':
        # Obsługujemy zarówno JSON jak i FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            # Konwertujemy checkbox na boolean - sprawdzamy wartość pola
            if 'is_active' in data:
                data['is_active'] = data['is_active'] in [True, 'true', 'True', '1', 1]
            else:
                data['is_active'] = False
        
        new_testimonial = Testimonial(
            author_name=data['author_name'],
            content=data['content'],
            member_since=data.get('member_since', ''),
            rating=int(data.get('rating', 5)),
            is_active=data.get('is_active', True)
        )
        db.session.add(new_testimonial)
        db.session.commit()
        return jsonify({'success': True, 'id': new_testimonial.id})
    
    elif request.method == 'PUT':
        # Obsługujemy zarówno JSON jak i FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            # Konwertujemy checkbox na boolean - sprawdzamy wartość pola
            if 'is_active' in data:
                data['is_active'] = data['is_active'] in [True, 'true', 'True', '1', 1]
            else:
                data['is_active'] = False
        
        testimonial = Testimonial.query.get(data['id'])
        if testimonial:
            testimonial.author_name = data['author_name']
            testimonial.content = data['content']
            testimonial.member_since = data.get('member_since', '')
            testimonial.rating = int(data.get('rating', 5))
            testimonial.is_active = data.get('is_active', True)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Testimonial not found'}), 404
    
    elif request.method == 'DELETE':
        try:
            testimonial_id = request.args.get('id', type=int)
            if not testimonial_id:
                return jsonify({'success': False, 'message': 'Brak ID opinii'}), 400
            
            testimonial = Testimonial.query.get(testimonial_id)
            if not testimonial:
                return jsonify({'success': False, 'message': 'Opinia nie została znaleziona'}), 404
            
            db.session.delete(testimonial)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Opinia została usunięta pomyślnie'})
            
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting testimonial: {str(e)}")
            return jsonify({'success': False, 'message': f'Wystąpił błąd podczas usuwania opinii: {str(e)}'}), 500

@app.route('/admin/api/seo', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_seo():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        seo_settings = SEOSettings.query.all()
        return jsonify([{
            'id': seo.id,
            'page_type': seo.page_type,
            'page_title': seo.page_title,
            'meta_description': seo.meta_description,
            'meta_keywords': seo.meta_keywords,
            'og_title': seo.og_title,
            'og_description': seo.og_description,
            'og_image': seo.og_image,
            'og_type': seo.og_type,
            'twitter_card': seo.twitter_card,
            'twitter_title': seo.twitter_title,
            'twitter_description': seo.twitter_description,
            'twitter_image': seo.twitter_image,
            'canonical_url': seo.canonical_url,
            'structured_data': seo.structured_data,
            'is_active': seo.is_active
        } for seo in seo_settings])
    
    elif request.method == 'POST':
        # Obsługujemy zarówno JSON jak i FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            # Konwertujemy checkbox na boolean
            data['is_active'] = 'is_active' in request.form
        
        new_seo = SEOSettings(
            page_type=data['page_type'],
            page_title=data['page_title'],
            meta_description=data['meta_description'],
            meta_keywords=data.get('meta_keywords', ''),
            og_title=data.get('og_title', ''),
            og_description=data.get('og_description', ''),
            og_image=data.get('og_image', ''),
            og_type=data.get('og_type', 'website'),
            twitter_card=data.get('twitter_card', 'summary_large_image'),
            twitter_title=data.get('twitter_title', ''),
            twitter_description=data.get('twitter_description', ''),
            twitter_image=data.get('twitter_image', ''),
            canonical_url=data.get('canonical_url', ''),
            structured_data=data.get('structured_data', ''),
            is_active=data.get('is_active', True)
        )
        db.session.add(new_seo)
        db.session.commit()
        return jsonify({'success': True, 'id': new_seo.id})
    
    elif request.method == 'PUT':
        # Obsługujemy zarówno JSON jak i FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            # Konwertujemy checkbox na boolean
            data['is_active'] = 'is_active' in request.form
        
        seo = SEOSettings.query.get(data['id'])
        if seo:
            seo.page_type = data['page_type']
            seo.page_title = data['page_title']
            seo.meta_description = data['meta_description']
            seo.meta_keywords = data.get('meta_keywords', '')
            seo.og_title = data.get('og_title', '')
            seo.og_description = data.get('og_description', '')
            seo.og_image = data.get('og_image', '')
            seo.og_type = data.get('og_type', 'website')
            seo.twitter_card = data.get('twitter_card', 'summary_large_image')
            seo.twitter_title = data.get('twitter_title', '')
            seo.twitter_description = data.get('twitter_description', '')
            seo.twitter_image = data.get('twitter_image', '')
            seo.canonical_url = data.get('canonical_url', '')
            seo.structured_data = data.get('structured_data', '')
            seo.is_active = data.get('is_active', True)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'SEO settings not found'}), 404
    
    elif request.method == 'DELETE':
        seo_id = request.args.get('id', type=int)
        seo = SEOSettings.query.get(seo_id)
        if seo:
            db.session.delete(seo)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'SEO settings not found'}), 404

@app.route('/admin/api/upload', methods=['POST'])
@login_required
def upload_file():
    """Upload file for event background"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{int(datetime.now().timestamp())}{ext}"
        
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'url': f'/static/uploads/{filename}'
        })
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/admin/api/event-schedule', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_event_schedule():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        events = EventSchedule.query.order_by(EventSchedule.event_date.desc()).all()
        return jsonify([{
            'id': event.id,
            'title': event.title,
            'event_type': event.event_type,
            'event_date': event.event_date.isoformat() if event.event_date else None,
            'end_date': event.end_date.isoformat() if event.end_date else None,
            'description': event.description,
            'meeting_link': event.meeting_link,
            'location': event.location,
            'is_active': event.is_active,
            'is_published': event.is_published,
            'hero_background': event.hero_background,
            'hero_background_type': event.hero_background_type,

            'created_at': event.created_at.isoformat(),
            'updated_at': event.updated_at.isoformat()
        } for event in events])
    
    elif request.method == 'POST':
        data = request.form.to_dict()
        print(f"DEBUG EVENT POST: Received form data: {data}")
        print(f"DEBUG EVENT POST: request.form keys: {list(request.form.keys())}")
        print(f"DEBUG EVENT POST: is_active raw value: {data.get('is_active')} (type: {type(data.get('is_active'))})")
        print(f"DEBUG EVENT POST: is_published raw value: {data.get('is_published')} (type: {type(data.get('is_published'))})")
        
        # Konwertujemy checkbox na boolean - sprawdzamy wartość pola
        if 'is_active' in data:
            data['is_active'] = data['is_active'] in [True, 'true', 'True', '1', 1]
        else:
            data['is_active'] = False
            
        if 'is_published' in data:
            data['is_published'] = data['is_published'] in [True, 'true', 'True', '1', 1]
        else:
            data['is_published'] = False
        
        print(f"DEBUG EVENT POST: After conversion - is_active: {data['is_active']}, is_published: {data['is_published']}")
        
        # Walidacja daty wydarzenia
        is_date_valid, date_error = validate_event_date(data['event_date'])
        if not is_date_valid:
            return jsonify({'success': False, 'error': date_error}), 400
        
        # Parse datetime
        event_date = datetime.fromisoformat(data['event_date'].replace('Z', '+00:00'))
        
        # Handle file upload
        hero_background = ''
        if 'hero_background' in request.files and request.files['hero_background'].filename:
            file = request.files['hero_background']
            is_file_valid, file_error = validate_file_type(file)
            if not is_file_valid:
                return jsonify({'success': False, 'error': file_error}), 400
            
            filename = secure_filename(file.filename)
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{int(datetime.now().timestamp())}{ext}"
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            hero_background = f'/static/uploads/{filename}'
        
        new_event = EventSchedule(
            title=data['title'],
            event_type=data['event_type'],
            event_date=event_date,
            end_date=datetime.fromisoformat(data['end_date'].replace('Z', '+00:00')) if data.get('end_date') else None,
            description=data.get('description', ''),
            meeting_link=data.get('meeting_link', ''),
            location=data.get('location', ''),
            is_active=data['is_active'],
            is_published=data['is_published'],
            hero_background=hero_background,
            hero_background_type=data.get('hero_background_type', 'image'),
    
        )
        db.session.add(new_event)
        db.session.commit()
        return jsonify({'success': True, 'id': new_event.id})
    
    elif request.method == 'PUT':
        data = request.form.to_dict()
        print(f"DEBUG EVENT PUT: Received form data: {data}")
        print(f"DEBUG EVENT PUT: request.form keys: {list(request.form.keys())}")
        print(f"DEBUG EVENT PUT: is_active raw value: {data.get('is_active')} (type: {type(data.get('is_active'))})")
        print(f"DEBUG EVENT PUT: is_published raw value: {data.get('is_published')} (type: {type(data.get('is_published'))})")
        
        # Konwertujemy checkbox na boolean - sprawdzamy wartość pola
        if 'is_active' in data:
            data['is_active'] = data['is_active'] in [True, 'true', 'True', '1', 1]
        else:
            data['is_active'] = False
            
        if 'is_published' in data:
            data['is_published'] = data['is_published'] in [True, 'true', 'True', '1', 1]
        else:
            data['is_published'] = False
        
        print(f"DEBUG EVENT PUT: After conversion - is_active: {data['is_active']}, is_published: {data['is_published']}")
        
        event = EventSchedule.query.get(data['id'])
        if event:
            # Walidacja daty wydarzenia
            is_date_valid, date_error = validate_event_date(data['event_date'])
            if not is_date_valid:
                return jsonify({'success': False, 'error': date_error}), 400
            
            # Parse datetime
            event_date = datetime.fromisoformat(data['event_date'].replace('Z', '+00:00'))
            event.title = data['title']
            event.event_type = data['event_type']
            event.event_date = event_date
            event.end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00')) if data.get('end_date') else None
            event.description = data.get('description', '')
            event.meeting_link = data.get('meeting_link', '')
            event.location = data.get('location', '')
            event.is_active = data['is_active']
            event.is_published = data['is_published']
            
            # Handle file upload
            if 'hero_background' in request.files and request.files['hero_background'].filename:
                file = request.files['hero_background']
                is_file_valid, file_error = validate_file_type(file)
                if not is_file_valid:
                    return jsonify({'success': False, 'error': file_error}), 400
                
                filename = secure_filename(file.filename)
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{int(datetime.now().timestamp())}{ext}"
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                event.hero_background = f'/static/uploads/{filename}'
            elif data.get('hero_background'):
                event.hero_background = data.get('hero_background', '')
            
            event.hero_background_type = data.get('hero_background_type', 'image')
    
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Event not found'}), 404
    
    elif request.method == 'DELETE':
        event_id = request.args.get('id', type=int)
        event = EventSchedule.query.get(event_id)
        if event:
            db.session.delete(event)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Event not found'}), 404

@app.route('/admin/api/event-schedule/<int:event_id>', methods=['GET'])
@login_required
def api_event_by_id(event_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    event = EventSchedule.query.get(event_id)
    if event:
            return jsonify({
            'success': True,
            'event': {
                'id': event.id,
                'title': event.title,
                'event_type': event.event_type,
                'event_date': event.event_date.isoformat() if event.event_date else None,
                'end_date': event.end_date.isoformat() if event.end_date else None,
                'description': event.description,
                'meeting_link': event.meeting_link,
                'location': event.location,
                'is_active': event.is_active,
                'is_published': event.is_published,
                'hero_background': event.hero_background,
                'hero_background_type': event.hero_background_type,
                
                'created_at': event.created_at.isoformat(),
                'updated_at': event.updated_at.isoformat()
            }
        })
    return jsonify({'success': False, 'error': 'Event not found'}), 404

def send_event_reminders():
    """Send reminders about upcoming events to all subscribers"""
    try:
        # Get next published and active event
        now = datetime.now()
        next_event = EventSchedule.query.filter_by(
            is_active=True, 
            is_published=True
        ).filter(
            EventSchedule.event_date > now
        ).order_by(EventSchedule.event_date).first()
        
        if not next_event:
            return False
        
        # Check if event is within next 24 hours
        time_diff = next_event.event_date - now
        
        if time_diff.total_seconds() < 0 or time_diff.total_seconds() > 86400:  # 24 hours
            return False
        
        # Get all active subscribers
        subscribers = email_service.get_approved_subscribers()
        
        # Send reminders using email template
        for subscriber in subscribers:
            try:
                # Prepare variables for the reminder template
                variables = {
                    'name': subscriber.name or 'Użytkowniku',
                    'email': subscriber.email,
                    'event_type': next_event.title,
                    'event_date': next_event.event_date.strftime('%d.%m.%Y %H:%M'),
                    'event_details': next_event.description or f'Zapraszamy na {next_event.event_type.lower()}, który odbędzie się o godzinie {next_event.event_date.strftime("%H:%M")}.'
                }
                
                # Send email using the reminder template
                success = email_service.send_template_email(
                    to_email=subscriber.email,
                    template_name='reminder',
                    variables=variables
                )
                
                if not success:
                    print(f"Failed to send reminder to {subscriber.email}")
                    
            except Exception as e:
                print(f"Failed to send reminder to {subscriber.email}: {str(e)}")
        
        return True
    except Exception as e:
        print(f"Error sending event reminders: {str(e)}")
        return False

# Page routes
@app.route('/<slug>')
def page(slug):
    """Display individual page by slug"""
    page = Page.query.filter_by(slug=slug, is_active=True, is_published=True).first()
    if page:
        return render_template('page.html', page=page)
    else:
        # Return 404 if page not found
        return render_template('404.html'), 404

# Admin API for pages
@app.route('/admin/api/pages', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_pages():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        pages = Page.query.order_by(Page.created_at.desc()).all()
        return jsonify([{
            'id': page.id,
            'title': page.title,
            'slug': page.slug,
            'content': page.content,
            'meta_description': page.meta_description,
            'meta_keywords': page.meta_keywords,
            'is_active': page.is_active,
            'is_published': page.is_published,
            'published_at': page.published_at.isoformat() if page.published_at else None,
            'created_at': page.created_at.isoformat(),
            'updated_at': page.updated_at.isoformat()
        } for page in pages])
    
    elif request.method == 'POST':
        data = request.form.to_dict()
        
        # Handle checkboxes - sprawdzamy wartość pola
        if 'is_active' in data:
            data['is_active'] = data['is_active'] in [True, 'true', 'True', '1', 1]
        else:
            data['is_active'] = False
            
        if 'is_published' in data:
            data['is_published'] = data['is_published'] in [True, 'true', 'True', '1', 1]
        else:
            data['is_published'] = False
        
        # Set published_at if publishing
        published_at = None
        if data['is_published']:
            published_at = datetime.utcnow()
        
        new_page = Page(
            title=data['title'],
            slug=data['slug'],
            content=data.get('content', ''),
            meta_description=data.get('meta_description', ''),
            meta_keywords=data.get('meta_keywords', ''),
            is_active=data['is_active'],
            is_published=data['is_published'],
            published_at=published_at
        )
        db.session.add(new_page)
        db.session.commit()
        return jsonify({'success': True, 'id': new_page.id})
    
    elif request.method == 'PUT':
        data = request.form.to_dict()
        
        # Handle checkboxes - sprawdzamy wartość pola
        if 'is_active' in data:
            data['is_active'] = data['is_active'] in [True, 'true', 'True', '1', 1]
        else:
            data['is_active'] = False
            
        if 'is_published' in data:
            data['is_published'] = data['is_published'] in [True, 'true', 'True', '1', 1]
        else:
            data['is_published'] = False
        
        page = Page.query.get(data['id'])
        if page:
            page.title = data['title']
            page.slug = data['slug']
            page.content = data.get('content', '')
            page.meta_description = data.get('meta_description', '')
            page.meta_keywords = data.get('meta_keywords', '')
            page.is_active = data['is_active']
            page.is_published = data['is_published']
            
            # Update published_at if publishing
            if data['is_published'] and not page.published_at:
                page.published_at = datetime.utcnow()
            elif not data['is_published']:
                page.published_at = None
            
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Page not found'}), 404
    
    elif request.method == 'DELETE':
        page_id = request.args.get('id', type=int)
        page = Page.query.get(page_id)
        if page:
            db.session.delete(page)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Page not found'}), 404

@app.route('/admin/api/pages/<int:page_id>', methods=['GET'])
@login_required
def api_page_by_id(page_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    page = Page.query.get(page_id)
    if page:
        return jsonify({
            'success': True,
            'page': {
                'id': page.id,
                'title': page.title,
                'slug': page.slug,
                'content': page.content,
                'meta_description': page.meta_description,
                'meta_keywords': page.meta_keywords,
                'is_active': page.is_active,
                'is_published': page.is_published,
                'published_at': page.published_at.isoformat() if page.published_at else None,
                'created_at': page.created_at.isoformat(),
                'updated_at': page.updated_at.isoformat()
            }
        })
    return jsonify({'success': False, 'error': 'Page not found'}), 404

# Admin API for email templates
@app.route('/admin/api/email-templates', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_email_templates():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        templates = EmailTemplate.query.order_by(EmailTemplate.created_at.desc()).all()
        return jsonify([{
            'id': template.id,
            'name': template.name,
            'subject': template.subject,
            'html_content': template.html_content,
            'text_content': template.text_content,
            'template_type': template.template_type,
            'variables': template.variables,
            'is_active': template.is_active,
            'created_at': template.created_at.isoformat(),
            'updated_at': template.updated_at.isoformat()
        } for template in templates])
    
    elif request.method == 'POST':
        data = request.form.to_dict()
        # Konwertujemy checkbox na boolean - sprawdzamy wartość pola
        print(f"DEBUG: POST data received: {data}")
        if 'is_active' in data and data['is_active'] == '1':
            data['is_active'] = True
        else:
            data['is_active'] = False
        print(f"DEBUG: is_active converted to: {data['is_active']}")
        
        new_template = EmailTemplate(
            name=data['name'],
            subject=data['subject'],
            html_content=data.get('html_content', ''),
            text_content=data.get('text_content', ''),
            template_type=data['template_type'],
            variables=data.get('variables', ''),
            is_active=data['is_active']
        )
        db.session.add(new_template)
        db.session.commit()
        return jsonify({'success': True, 'id': new_template.id})
    
    elif request.method == 'PUT':
        data = request.form.to_dict()
        # Konwertujemy checkbox na boolean - sprawdzamy wartość pola
        print(f"DEBUG: PUT data received: {data}")
        if 'is_active' in data and data['is_active'] == '1':
            data['is_active'] = True
        else:
            data['is_active'] = False
        print(f"DEBUG: is_active converted to: {data['is_active']}")
        
        template = EmailTemplate.query.get(data['id'])
        if template:
            template.name = data['name']
            template.subject = data['subject']
            template.html_content = data.get('html_content', '')
            template.text_content = data.get('text_content', '')
            template.template_type = data['template_type']
            template.variables = data.get('variables', '')
            template.is_active = data['is_active']
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Template not found'}), 404
    
    elif request.method == 'DELETE':
        template_id = request.args.get('id', type=int)
        template = EmailTemplate.query.get(template_id)
        if template:
            db.session.delete(template)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Template not found'}), 404

@app.route('/admin/api/email-templates/<int:template_id>', methods=['GET'])
@login_required
def api_email_template_by_id(template_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    template = EmailTemplate.query.get(template_id)
    if template:
        return jsonify({
            'success': True,
            'template': {
                'id': template.id,
                'name': template.name,
                'subject': template.subject,
                'html_content': template.html_content,
                'text_content': template.text_content,
                'template_type': template.template_type,
                'variables': template.variables,
                'is_active': template.is_active,
                'created_at': template.created_at.isoformat(),
                'updated_at': template.updated_at.isoformat()
            }
        })
    return jsonify({'success': False, 'error': 'Template not found'}), 404

@app.route('/admin/api/email-templates/test', methods=['POST'])
@login_required
def api_test_email_template():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    template_id = request.form.get('template_id')
    test_email = request.form.get('test_email')
    
    if not template_id or not test_email:
        return jsonify({'success': False, 'error': 'Missing template_id or test_email'})
    
    try:
        # Get template
        template = EmailTemplate.query.get(template_id)
        if not template:
            return jsonify({'success': False, 'error': 'Template not found'})
        
        # Send test email using the template
        success = email_service.send_email(
            to_email=test_email,
            subject=f"[TEST] {template.subject}",
            html_content=template.html_content,
            text_content=template.text_content,
            template_id=template.id
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Test email sent successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to send test email'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Admin API for creating default email templates
@app.route('/admin/api/create-default-templates', methods=['POST'])
@login_required
def api_create_default_templates():
    """Create default email templates if they don't exist"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        created_templates = []
        
        # Create welcome template
        welcome_template = EmailTemplate.query.filter_by(template_type='welcome').first()
        if not welcome_template:
            welcome_template = EmailTemplate(
                name='Email Powitalny',
                subject='Witamy w Klubie Lepsze Życie! 🎉',
                html_content='''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Witamy w Klubie Lepsze Życie</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #28a745; margin-bottom: 10px;">🎉 Witamy w Klubie Lepsze Życie!</h1>
        <p style="font-size: 18px; color: #666;">Cieszę się, że dołączyłeś do nas!</p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #007bff; margin-top: 0;">Cześć {{name}}!</h2>
        <p>Dziękujemy za zarejestrowanie się na naszą darmową prezentację. Twoje miejsce zostało zarezerwowane!</p>
        
        <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #155724; margin-top: 0;">📅 Co dalej?</h3>
            <ul style="text-align: left; margin: 0; padding-left: 20px;">
                <li>Otrzymasz przypomnienie o wydarzeniu na 24h przed</li>
                <li>Będziesz informowany o nowych wydarzeniach i webinarach</li>
                <li>Dostaniesz dostęp do ekskluzywnych materiałów</li>
            </ul>
        </div>
    </div>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
        <h3 style="color: #856404; margin-top: 0;">🔒 Twoje dane są bezpieczne</h3>
        <p style="margin-bottom: 10px;">Możesz w każdej chwili:</p>
        <p style="margin: 5px 0;"><a href="{{unsubscribe_url}}" style="color: #856404;">📧 Zrezygnować z subskrypcji</a></p>
        <p style="margin: 5px 0;"><a href="{{delete_account_url}}" style="color: #856404;">🗑️ Usunąć swoje konto</a></p>
    </div>
    
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 14px;">
            Z poważaniem,<br>
            <strong>Zespół Klubu Lepsze Życie</strong>
        </p>
        <p style="color: #999; font-size: 12px; margin-top: 20px;">
            Ten email został wysłany na adres {{email}}
        </p>
    </div>
</body>
</html>
                ''',
                text_content='''
Witamy w Klubie Lepsze Życie! 🎉

Cześć {{name}}!

Dziękujemy za zarejestrowanie się na naszą darmową prezentację. Twoje miejsce zostało zarezerwowane!

Co dalej?
- Otrzymasz przypomnienie o wydarzeniu na 24h przed
- Będziesz informowany o nowych wydarzeniach i webinarach
- Dostaniesz dostęp do ekskluzywnych materiałów

Twoje dane są bezpieczne - możesz w każdej chwili:
- Zrezygnować z subskrypcji: {{unsubscribe_url}}
- Usunąć swoje konto: {{delete_account_url}}

Z poważaniem,
Zespół Klubu Lepsze Życie

Ten email został wysłany na adres {{email}}
                ''',
                template_type='welcome',
                variables='name,email,unsubscribe_url,delete_account_url',
                is_active=True
            )
            db.session.add(welcome_template)
            created_templates.append('welcome')
        
        # Create reminder template
        reminder_template = EmailTemplate.query.filter_by(template_type='reminder').first()
        if not reminder_template:
            reminder_template = EmailTemplate(
                name='Przypomnienie o Wydarzeniu',
                subject='🔔 Przypomnienie: {{event_type}} - {{event_date}}',
                html_content='''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Przypomnienie o Wydarzeniu</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #dc3545; margin-bottom: 10px;">🔔 Przypomnienie o Wydarzeniu</h1>
        <p style="font-size: 18px; color: #666;">Nie przegap tego wydarzenia!</p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #007bff; margin-top: 0;">Cześć {{name}}!</h2>
        <p>Przypominamy o nadchodzącym wydarzeniu:</p>
        
        <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #856404; margin-top: 0;">📅 {{event_type}}</h3>
            <p style="margin: 5px 0;"><strong>Data:</strong> {{event_date}}</p>
            <p style="margin: 5px 0;"><strong>Szczegóły:</strong></p>
            <div style="background-color: white; padding: 10px; border-radius: 3px; margin-top: 10px;">
                {{event_details}}
            </div>
        </div>
    </div>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
        <h3 style="color: #856404; margin-top: 0;">🔒 Twoje dane są bezpieczne</h3>
        <p style="margin-bottom: 10px;">Możesz w każdej chwili:</p>
        <p style="margin: 5px 0;"><a href="{{unsubscribe_url}}" style="color: #856404;">📧 Zrezygnować z subskrypcji</a></p>
        <p style="margin: 5px 0;"><a href="{{delete_account_url}}" style="color: #856404;">🗑️ Usunąć swoje konto</a></p>
    </div>
    
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 14px;">
            Z poważaniem,<br>
            <strong>Zespół Klubu Lepsze Życie</strong>
        </p>
        <p style="color: #999; font-size: 12px; margin-top: 20px;">
            Ten email został wysłany na adres {{email}}
        </p>
    </div>
</body>
</html>
                ''',
                text_content='''
Przypomnienie o Wydarzeniu 🔔

Cześć {{name}}!

Przypominamy o nadchodzącym wydarzeniu:

{{event_type}}
Data: {{event_date}}

Szczegóły:
{{event_details}}

Twoje dane są bezpieczne - możesz w każdej chwili:
- Zrezygnować z subskrypcji: {{unsubscribe_url}}
- Usunąć swoje konto: {{delete_account_url}}

Z poważaniem,
Zespół Klubu Lepsze Życie

Ten email został wysłany na adres {{email}}
                ''',
                template_type='reminder',
                variables='name,email,event_type,event_date,event_details,unsubscribe_url,delete_account_url',
                is_active=True
            )
            db.session.add(reminder_template)
            created_templates.append('reminder')
        
        # Create admin notification template
        admin_notification_template = EmailTemplate.query.filter_by(template_type='admin_notification').first()
        if not admin_notification_template:
            admin_notification_template = EmailTemplate(
                name='Powiadomienie dla Administratora',
                subject='🔔 Nowa rejestracja w Klubie Lepsze Życie',
                html_content='''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nowa Rejestracja</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #28a745; margin-bottom: 10px;">🔔 Nowa Rejestracja w Klubie</h1>
        <p style="font-size: 18px; color: #666;">Pojawił się nowy członek!</p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #007bff; margin-top: 0;">Cześć {{admin_name}}!</h2>
        <p>W systemie pojawiła się nowa rejestracja:</p>
        
        <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #155724; margin-top: 0;">👤 Nowy Członek</h3>
            <p style="margin: 5px 0;"><strong>Imię:</strong> {{new_member_name}}</p>
            <p style="margin: 5px 0;"><strong>Email:</strong> {{new_member_email}}</p>
            <p style="margin: 5px 0;"><strong>Data rejestracji:</strong> {{registration_date}}</p>
        </div>
    </div>
    
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 14px;">
            Z poważaniem,<br>
            <strong>System Klubu Lepsze Życie</strong>
        </p>
    </div>
</body>
</html>
                ''',
                text_content='''
Nowa Rejestracja w Klubie

Cześć {{admin_name}}!

W systemie pojawiła się nowa rejestracja:

👤 Nowy Członek
Imię: {{new_member_name}}
Email: {{new_member_email}}
Data rejestracji: {{registration_date}}

Z poważaniem,
System Klubu Lepsze Życie
                ''',
                template_type='admin_notification',
                variables='admin_name,new_member_name,new_member_email,registration_date',
                is_active=True
            )
            db.session.add(admin_notification_template)
            created_templates.append('admin_notification')
        
        # Create newsletter template
        newsletter_template = EmailTemplate.query.filter_by(template_type='newsletter').first()
        if not newsletter_template:
            newsletter_template = EmailTemplate(
                name='Newsletter Klubu',
                subject='📰 Newsletter Klubu Lepsze Życie - {{newsletter_title}}',
                html_content='''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Newsletter Klubu Lepsze Życie</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #28a745; margin-bottom: 10px;">📰 Newsletter Klubu Lepsze Życie</h1>
        <p style="font-size: 18px; color: #666;">Najnowsze informacje i aktualności</p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #007bff; margin-top: 0;">Cześć {{name}}!</h2>
        <p>Oto najnowsze informacje z naszego klubu:</p>
        
        <div style="background-color: #e7f3ff; border: 1px solid #b3d9ff; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #0056b3; margin-top: 0;">📋 {{newsletter_title}}</h3>
            {{newsletter_content}}
        </div>
    </div>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
        <h3 style="color: #856404; margin-top: 0;">🔒 Twoje dane są bezpieczne</h3>
        <p style="margin-bottom: 10px;">Możesz w każdej chwili:</p>
        <p style="margin: 5px 0;"><a href="{{unsubscribe_url}}" style="color: #856404;">📧 Zrezygnować z subskrypcji</a></p>
        <p style="margin: 5px 0;"><a href="{{delete_account_url}}" style="color: #856404;">🗑️ Usunąć swoje konto</a></p>
    </div>
    
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 14px;">
            Z poważaniem,<br>
            <strong>Zespół Klubu Lepsze Życie</strong>
        </p>
        <p style="color: #999; font-size: 12px; margin-top: 20px;">
            Ten email został wysłany na adres {{email}}
        </p>
    </div>
</body>
</html>
                ''',
                text_content='''
Newsletter Klubu Lepsze Życie 📰

Cześć {{name}}!

Oto najnowsze informacje z naszego klubu:

{{newsletter_title}}

{{newsletter_content}}

Twoje dane są bezpieczne - możesz w każdej chwili:
- Zrezygnować z subskrypcji: {{unsubscribe_url}}
- Usunąć swoje konto: {{delete_account_url}}

Z poważaniem,
Zespół Klubu Lepsze Życie

Ten email został wysłany na adres {{email}}
                ''',
                template_type='newsletter',
                variables='name,email,newsletter_title,newsletter_content,unsubscribe_url,delete_account_url',
                is_active=True
            )
            db.session.add(newsletter_template)
            created_templates.append('newsletter')
        
        # Create custom template
        custom_template = EmailTemplate.query.filter_by(template_type='custom').first()
        if not custom_template:
            custom_template = EmailTemplate(
                name='Email Własny',
                subject='📧 {{custom_subject}}',
                html_content='''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Własny</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #6f42c1; margin-bottom: 10px;">📧 Email Własny</h1>
        <p style="font-size: 18px; color: #666;">Wiadomość od Klubu Lepsze Życie</p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #007bff; margin-top: 0;">Cześć {{name}}!</h2>
        <p>Mamy dla Ciebie wiadomość:</p>
        
        <div style="background-color: #e7f3ff; border: 1px solid #b3d9ff; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #0056b3; margin-top: 0;">📋 {{custom_subject}}</h3>
            {{custom_content}}
        </div>
    </div>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
        <h3 style="color: #856404; margin-top: 0;">🔒 Twoje dane są bezpieczne</h3>
        <p style="margin-bottom: 10px;">Możesz w każdej chwili:</p>
        <p style="margin: 5px 0;"><a href="{{unsubscribe_url}}" style="color: #856404;">📧 Zrezygnować z subskrypcji</a></p>
        <p style="margin: 5px 0;"><a href="{{delete_account_url}}" style="color: #856404;">🗑️ Usunąć swoje konto</a></p>
    </div>
    
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 14px;">
            Z poważaniem,<br>
            <strong>Zespół Klubu Lepsze Życie</strong>
        </p>
        <p style="color: #999; font-size: 12px; margin-top: 20px;">
            Ten email został wysłany na adres {{email}}
        </p>
    </div>
</body>
</html>
                ''',
                text_content='''
Email Własny 📧

Cześć {{name}}!

Mamy dla Ciebie wiadomość:

{{custom_subject}}

{{custom_content}}

Twoje dane są bezpieczne - możesz w każdej chwili:
- Zrezygnować z subskrypcji: {{unsubscribe_url}}
- Usunąć swoje konto: {{delete_account_url}}

Z poważaniem,
Zespół Klubu Lepsze Życie

Ten email został wysłany na adres {{email}}
                ''',
                template_type='custom',
                variables='name,email,custom_subject,custom_content,unsubscribe_url,delete_account_url',
                is_active=True
            )
            db.session.add(custom_template)
            created_templates.append('custom')
        
        # Create event reminder templates
        event_reminder_templates = []
        reminder_types = [
            ('24h_before', '24h przed wydarzeniem'),
            ('1h_before', '1h przed wydarzeniem'),
            ('5min_before', '5min przed wydarzeniem')
        ]
        
        for notif_type, description in reminder_types:
            template_name = f'event_reminder_{notif_type}'
            existing_template = EmailTemplate.query.filter_by(name=template_name).first()
            
            if not existing_template:
                if notif_type == '24h_before':
                    subject = '🔔 Przypomnienie: {{event_title}} - jutro o {{event_time}}'
                    html_content = '''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Przypomnienie o Wydarzeniu</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #dc3545; margin-bottom: 10px;">🔔 Przypomnienie o Wydarzeniu</h1>
        <p style="font-size: 18px; color: #666;">Jutro o {{event_time}} - nie przegap tego!</p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #007bff; margin-top: 0;">Cześć {{name}}!</h2>
        <p>Przypominamy o jutrzejszym wydarzeniu:</p>
        
        <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #856404; margin-top: 0;">📅 {{event_title}}</h3>
            <p style="margin: 5px 0;"><strong>Data:</strong> {{event_date}}</p>
            <p style="margin: 5px 0;"><strong>Godzina:</strong> {{event_time}}</p>
            <p style="margin: 5px 0;"><strong>Typ:</strong> {{event_type}}</p>
            {% if event_location %}
            <p style="margin: 5px 0;"><strong>Lokalizacja:</strong> {{event_location}}</p>
            {% endif %}
            {% if event_meeting_link %}
            <p style="margin: 5px 0;"><strong>Link do spotkania:</strong> <a href="{{event_meeting_link}}" style="color: #856404;">{{event_meeting_link}}</a></p>
            {% endif %}
        </div>
        
        <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #155724; margin-top: 0;">📋 Opis wydarzenia</h3>
            <div style="background-color: white; padding: 15px; border-radius: 5px;">
                {{event_description}}
            </div>
        </div>
    </div>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
        <h3 style="color: #856404; margin-top: 0;">🔒 Twoje dane są bezpieczne</h3>
        <p style="margin-bottom: 10px;">Możesz w każdej chwili:</p>
        <p style="margin: 5px 0;"><a href="{{unsubscribe_url}}" style="color: #856404;">📧 Zrezygnować z subskrypcji</a></p>
        <p style="margin: 5px 0;"><a href="{{delete_account_url}}" style="color: #856404;">🗑️ Usunąć swoje konto</a></p>
    </div>
    
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 14px;">
            Z poważaniem,<br>
            <strong>Zespół Klubu Lepsze Życie</strong>
        </p>
        <p style="color: #999; font-size: 12px; margin-top: 20px;">
            Ten email został wysłany na adres {{email}}
        </p>
    </div>
</body>
</html>
                    '''
                    text_content = '''
Przypomnienie o Wydarzeniu 🔔

Cześć {{name}}!

Przypominamy o jutrzejszym wydarzeniu:

📅 {{event_title}}
Data: {{event_date}}
Godzina: {{event_time}}
Typ: {{event_type}}
{% if event_location %}Lokalizacja: {{event_location}}{% endif %}
{% if event_meeting_link %}Link do spotkania: {{event_meeting_link}}{% endif %}

📋 Opis wydarzenia:
{{event_description}}

Twoje dane są bezpieczne - możesz w każdej chwili:
- Zrezygnować z subskrypcji: {{unsubscribe_url}}
- Usunąć swoje konto: {{delete_account_url}}

Z poważaniem,
Zespół Klubu Lepsze Życie

Ten email został wysłany na adres {{email}}
                    '''
                elif notif_type == '1h_before':
                    subject = '⏰ Ostatnie przypomnienie: {{event_title}} - za godzinę!'
                    html_content = '''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ostatnie Przypomnienie o Wydarzeniu</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #fd7e14; margin-bottom: 10px;">⏰ Ostatnie Przypomnienie</h1>
        <p style="font-size: 18px; color: #666;">Wydarzenie za godzinę - przygotuj się!</p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #007bff; margin-top: 0;">Cześć {{name}}!</h2>
        <p>Wydarzenie rozpocznie się za godzinę:</p>
        
        <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #856404; margin-top: 0;">📅 {{event_title}}</h3>
            <p style="margin: 5px 0;"><strong>Data:</strong> {{event_date}}</p>
            <p style="margin: 5px 0;"><strong>Godzina:</strong> {{event_time}}</p>
            <p style="margin: 5px 0;"><strong>Typ:</strong> {{event_type}}</p>
            {% if event_location %}
            <p style="margin: 5px 0;"><strong>Lokalizacja:</strong> {{event_location}}</p>
            {% endif %}
            {% if event_meeting_link %}
            <p style="margin: 5px 0;"><strong>Link do spotkania:</strong> <a href="{{event_meeting_link}}" style="color: #856404;">{{event_meeting_link}}</a></p>
            {% endif %}
        </div>
        
        <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #155724; margin-top: 0;">📋 Opis wydarzenia</h3>
            <div style="background-color: white; padding: 15px; border-radius: 5px;">
                {{event_description}}
            </div>
        </div>
    </div>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
        <h3 style="color: #856404; margin-top: 0;">🔒 Twoje dane są bezpieczne</h3>
        <p style="margin-bottom: 10px;">Możesz w każdej chwili:</p>
        <p style="margin: 5px 0;"><a href="{{unsubscribe_url}}" style="color: #856404;">📧 Zrezygnować z subskrypcji</a></p>
        <p style="margin: 5px 0;"><a href="{{delete_account_url}}" style="color: #856404;">🗑️ Usunąć swoje konto</a></p>
    </div>
    
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 14px;">
            Z poważaniem,<br>
            <strong>Zespół Klubu Lepsze Życie</strong>
        </p>
        <p style="color: #999; font-size: 12px; margin-top: 20px;">
            Ten email został wysłany na adres {{email}}
        </p>
    </div>
</body>
</html>
                    '''
                    text_content = '''
Ostatnie Przypomnienie o Wydarzeniu ⏰

Cześć {{name}}!

Wydarzenie rozpocznie się za godzinę:

📅 {{event_title}}
Data: {{event_date}}
Godzina: {{event_time}}
Typ: {{event_type}}
{% if event_location %}Lokalizacja: {{event_location}}{% endif %}
{% if event_meeting_link %}Link do spotkania: {{event_meeting_link}}{% endif %}

📋 Opis wydarzenia:
{{event_description}}

Twoje dane są bezpieczne - możesz w każdej chwili:
- Zrezygnować z subskrypcji: {{unsubscribe_url}}
- Usunąć swoje konto: {{delete_account_url}}

Z poważaniem,
Zespół Klubu Lepsze Życie

Ten email został wysłany na adres {{email}}
                    '''
                else:  # 5min_before
                    subject = '🚀 Start za 5 minut: {{event_title}} - dołącz teraz!'
                    html_content = '''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Start Wydarzenia za 5 minut</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: 8px; margin-bottom: 30px;">
        <h1 style="color: #28a745; margin-bottom: 10px;">🚀 Start za 5 minut!</h1>
        <p style="font-size: 18px; color: #666;">Wydarzenie rozpocznie się za chwilę</p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #007bff; margin-top: 0;">Cześć {{name}}!</h2>
        <p>Wydarzenie rozpocznie się za 5 minut:</p>
        
        <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #155724; margin-top: 0;">📅 {{event_title}}</h3>
            <p style="margin: 5px 0;"><strong>Data:</strong> {{event_date}}</p>
            <p style="margin: 5px 0;"><strong>Godzina:</strong> {{event_time}}</p>
            <p style="margin: 5px 0;"><strong>Typ:</strong> {{event_type}}</p>
            {% if event_location %}
            <p style="margin: 5px 0;"><strong>Lokalizacja:</strong> {{event_location}}</p>
            {% endif %}
            {% if event_meeting_link %}
            <p style="margin: 5px 0;"><strong>Link do spotkania:</strong> <a href="{{event_meeting_link}}" style="color: #856404;">{{event_meeting_link}}</a></p>
            {% endif %}
        </div>
        
        <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #856404; margin-top: 0;">📋 Opis wydarzenia</h3>
            <div style="background-color: white; padding: 15px; border-radius: 5px;">
                {{event_description}}
            </div>
        </div>
        
        <div style="text-align: center; margin: 20px 0;">
            <a href="{{event_meeting_link}}" style="background-color: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">
                🚀 DOŁĄCZ DO SPOTKANIA
            </a>
        </div>
    </div>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
        <h3 style="color: #856404; margin-top: 0;">🔒 Twoje dane są bezpieczne</h3>
        <p style="margin-bottom: 10px;">Możesz w każdej chwili:</p>
        <p style="margin: 5px 0;"><a href="{{unsubscribe_url}}" style="color: #856404;">📧 Zrezygnować z subskrypcji</a></p>
        <p style="margin: 5px 0;"><a href="{{delete_account_url}}" style="color: #856404;">🗑️ Usunąć swoje konto</a></p>
    </div>
    
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 14px;">
            Z poważaniem,<br>
            <strong>Zespół Klubu Lepsze Życie</strong>
        </p>
        <p style="color: #999; font-size: 12px; margin-top: 20px;">
            Ten email został wysłany na adres {{email}}
        </p>
    </div>
</body>
</html>
                    '''
                    text_content = '''
Start za 5 minut! 🚀

Cześć {{name}}!

Wydarzenie rozpocznie się za 5 minut:

📅 {{event_title}}
Data: {{event_date}}
Godzina: {{event_time}}
Typ: {{event_type}}
{% if event_location %}Lokalizacja: {{event_location}}{% endif %}
{% if event_meeting_link %}Link do spotkania: {{event_meeting_link}}{% endif %}

📋 Opis wydarzenia:
{{event_description}}

🚀 DOŁĄCZ DO SPOTKANIA: {{event_meeting_link}}

Twoje dane są bezpieczne - możesz w każdej chwili:
- Zrezygnować z subskrypcji: {{unsubscribe_url}}
- Usunąć swoje konto: {{delete_account_url}}

Z poważaniem,
Zespół Klubu Lepsze Życie

Ten email został wysłany na adres {{email}}
                    '''
                
                template = EmailTemplate(
                    name=template_name,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content,
                    template_type='event_reminder',
                    variables='name,email,event_title,event_date,event_time,event_type,event_location,event_meeting_link,event_description,unsubscribe_url,delete_account_url',
                    is_active=True
                )
                db.session.add(template)
                event_reminder_templates.append(template_name)
        
        # Create event registration confirmation template
        event_registration_template = EmailTemplate.query.filter_by(name='event_registration_confirmation').first()
        if not event_registration_template:
            event_registration_template = EmailTemplate(
                name='event_registration_confirmation',
                subject='✅ Potwierdzenie zapisu: {{event_title}}',
                html_content='''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Potwierdzenie Zapisu na Wydarzenie</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #28a745; margin-bottom: 10px;">✅ Potwierdzenie Zapisu</h1>
        <p style="font-size: 18px; color: #666;">Twoje miejsce zostało zarezerwowane!</p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #007bff; margin-top: 0;">Cześć {{name}}!</h2>
        <p>Dziękujemy za zapisanie się na wydarzenie:</p>
        
        <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #155724; margin-top: 0;">📅 {{event_title}}</h3>
            <p style="margin: 5px 0;"><strong>Data:</strong> {{event_date}}</p>
            <p style="margin: 5px 0;"><strong>Typ:</strong> {{event_type}}</p>
            {% if event_location %}
            <p style="margin: 5px 0;"><strong>Lokalizacja:</strong> {{event_location}}</p>
            {% endif %}
            {% if event_meeting_link %}
            <p style="margin: 5px 0;"><strong>Link do spotkania:</strong> <a href="{{event_meeting_link}}" style="color: #155724;">{{event_meeting_link}}</a></p>
            {% endif %}
        </div>
        
        <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #856404; margin-top: 0;">📋 Opis wydarzenia</h3>
            <div style="background-color: white; padding: 15px; border-radius: 5px;">
                {{event_description}}
            </div>
        </div>
        
        <div style="background-color: #e7f3ff; border: 1px solid #b3d9ff; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #0056b3; margin-top: 0;">🔔 Co dalej?</h3>
            <ul style="text-align: left; margin: 0; padding-left: 20px;">
                <li>Otrzymasz przypomnienie 24h przed wydarzeniem</li>
                <li>Otrzymasz przypomnienie 1h przed wydarzeniem</li>
                <li>Otrzymasz link do spotkania 5min przed startem</li>
            </ul>
        </div>
    </div>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
        <h3 style="color: #856404; margin-top: 0;">🔒 Twoje dane są bezpieczne</h3>
        <p style="margin-bottom: 10px;">Możesz w każdej chwili:</p>
        <p style="margin: 5px 0;"><a href="{{unsubscribe_url}}" style="color: #856404;">📧 Zrezygnować z subskrypcji</a></p>
        <p style="margin: 5px 0;"><a href="{{delete_account_url}}" style="color: #856404;">🗑️ Usunąć swoje konto</a></p>
    </div>
    
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 14px;">
            Z poważaniem,<br>
            <strong>Zespół Klubu Lepsze Życie</strong>
        </p>
        <p style="color: #999; font-size: 12px; margin-top: 20px;">
            Ten email został wysłany na adres {{email}}
        </p>
    </div>
</body>
</html>
                ''',
                text_content='''
Potwierdzenie Zapisu na Wydarzenie ✅

Cześć {{name}}!

Dziękujemy za zapisanie się na wydarzenie:

📅 {{event_title}}
Data: {{event_date}}
Typ: {{event_type}}
{% if event_location %}Lokalizacja: {{event_location}}{% endif %}
{% if event_meeting_link %}Link do spotkania: {{event_meeting_link}}{% endif %}

📋 Opis wydarzenia:
{{event_description}}

🔔 Co dalej?
- Otrzymasz przypomnienie 24h przed wydarzeniem
- Otrzymasz przypomnienie 1h przed wydarzeniem
- Otrzymasz link do spotkania 5min przed startem

Twoje dane są bezpieczne - możesz w każdej chwili:
- Zrezygnować z subskrypcji: {{unsubscribe_url}}
- Usunąć swoje konto: {{delete_account_url}}

Z poważaniem,
Zespół Klubu Lepsze Życie

Ten email został wysłany na adres {{email}}
                ''',
                template_type='event_registration',
                variables='name,email,event_title,event_date,event_type,event_location,event_meeting_link,event_description,unsubscribe_url,delete_account_url',
                is_active=True
            )
            db.session.add(event_registration_template)
            created_templates.append('event_registration_confirmation')
        
        db.session.commit()
        
        if created_templates or event_reminder_templates:
            all_templates = created_templates + event_reminder_templates
            return jsonify({
                'success': True, 
                'message': f'Utworzono domyślne szablony: {", ".join(all_templates)}'
            })
        else:
            return jsonify({
                'success': True, 
                'message': 'Wszystkie domyślne szablony już istnieją'
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

# Admin API for creating event notification schedules
@app.route('/admin/api/create-event-schedules', methods=['POST'])
@login_required
def api_create_event_schedules():
    """Create default event notification schedules"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        created_schedules = []
        
        # Create schedule for 24h before event
        schedule_24h = EmailSchedule.query.filter_by(
            name='Przypomnienie 24h przed wydarzeniem',
            trigger_event='event_reminder'
        ).first()
        
        if not schedule_24h:
            schedule_24h = EmailSchedule(
                name='Przypomnienie 24h przed wydarzeniem',
                template_type='event_reminder',
                schedule_type='event_based',
                trigger_event='event_reminder',
                schedule_config=json.dumps({
                    'notification_type': '24h_before',
                    'description': 'Wysyła przypomnienie 24h przed wydarzeniem'
                }),
                is_active=True
            )
            db.session.add(schedule_24h)
            created_schedules.append('24h_before')
        
        # Create schedule for 1h before event
        schedule_1h = EmailSchedule.query.filter_by(
            name='Przypomnienie 1h przed wydarzeniem',
            trigger_event='event_reminder'
        ).first()
        
        if not schedule_1h:
            schedule_1h = EmailSchedule(
                name='Przypomnienie 1h przed wydarzeniem',
                template_type='event_reminder',
                schedule_type='event_based',
                trigger_event='event_reminder',
                schedule_config=json.dumps({
                    'notification_type': '1h_before',
                    'description': 'Wysyła przypomnienie 1h przed wydarzeniem'
                }),
                is_active=True
            )
            db.session.add(schedule_1h)
            created_schedules.append('1h_before')
        
        # Create schedule for 5min before event
        schedule_5min = EmailSchedule.query.filter_by(
            name='Link do spotkania 5min przed wydarzeniem',
            trigger_event='event_reminder'
        ).first()
        
        if not schedule_5min:
            schedule_5min = EmailSchedule(
                name='Link do spotkania 5min przed wydarzeniem',
                template_type='event_reminder',
                schedule_type='event_based',
                trigger_event='event_reminder',
                schedule_config=json.dumps({
                    'notification_type': '5min_before',
                    'description': 'Wysyła link do spotkania 5min przed wydarzeniem'
                }),
                is_active=True
            )
            db.session.add(schedule_5min)
            created_schedules.append('5min_before')
        
        db.session.commit()
        
        if created_schedules:
            return jsonify({
                'success': True,
                'message': f'Utworzono harmonogramy powiadomień: {", ".join(created_schedules)}'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Wszystkie harmonogramy powiadomień już istnieją'
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

# Admin API for email subscriptions
@login_required
def api_email_subscriptions():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        subscriptions = EmailSubscription.query.order_by(EmailSubscription.created_at.desc()).all()
        return jsonify([{
            'id': sub.id,
            'email': sub.email,
            'name': sub.name,
            'subscription_type': sub.subscription_type,
            'is_active': sub.is_active,
            'created_at': sub.created_at.isoformat(),
            'updated_at': sub.updated_at.isoformat()
        } for sub in subscriptions])
    
    elif request.method == 'DELETE':
        sub_id = request.args.get('id', type=int)
        subscription = EmailSubscription.query.get(sub_id)
        if subscription:
            db.session.delete(subscription)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Subscription not found'}), 404

@app.route('/admin/api/send-reminders', methods=['POST'])
@login_required
def api_send_reminders():
    """Manually send event reminders"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        success = send_event_reminders()
        if success:
            return jsonify({'success': True, 'message': 'Przypomnienia zostały wysłane'})
        else:
            return jsonify({'success': False, 'message': 'Brak nadchodzących wydarzeń lub błąd wysyłania'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/api/send-newsletter', methods=['POST'])
@login_required
def api_send_newsletter():
    """Send newsletter to all subscribers"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.form.to_dict()
        newsletter_title = data.get('newsletter_title', '')
        newsletter_content = data.get('newsletter_content', '')
        
        if not newsletter_title or not newsletter_content:
            return jsonify({'success': False, 'error': 'Brak tytułu lub treści newslettera'})
        
        # Get all active subscribers
        subscribers = email_service.get_approved_subscribers()
        
        if not subscribers:
            return jsonify({'success': False, 'error': 'Brak aktywnych subskrybentów'})
        
        # Send newsletter to all subscribers
        success_count = 0
        for subscriber in subscribers:
            variables = {
                'name': subscriber.name or 'Użytkowniku',
                'email': subscriber.email,
                'newsletter_title': newsletter_title,
                'newsletter_content': newsletter_content
            }
            
            success = email_service.send_template_email(
                to_email=subscriber.email,
                template_name='newsletter',
                variables=variables
            )
            
            if success:
                success_count += 1
        
        return jsonify({
            'success': True, 
            'message': f'Newsletter wysłany do {success_count}/{len(subscribers)} subskrybentów'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})



@app.route('/admin/api/send-custom-email', methods=['POST'])
@login_required
def api_send_custom_email():
    """Send custom email to all subscribers"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.form.to_dict()
        custom_subject = data.get('custom_subject', '')
        custom_content = data.get('custom_content', '')
        
        if not custom_subject or not custom_content:
            return jsonify({'success': False, 'error': 'Brak tematu lub treści emaila'})
        
        # Get all active subscribers
        subscribers = email_service.get_approved_subscribers()
        
        if not subscribers:
            return jsonify({'success': False, 'error': 'Brak aktywnych subskrybentów'})
        
        # Send custom email to all subscribers
        success_count = 0
        for subscriber in subscribers:
            variables = {
                'name': subscriber.name or 'Użytkowniku',
                'email': subscriber.email,
                'custom_subject': custom_subject,
                'custom_content': custom_content
            }
            
            success = email_service.send_template_email(
                to_email=subscriber.email,
                template_name='custom',
                variables=variables
            )
            
            if success:
                success_count += 1
        
        return jsonify({
            'success': True, 
            'message': f'Email własny wysłany do {success_count}/{len(subscribers)} subskrybentów'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Email routes
@app.route('/unsubscribe/<token>')
def unsubscribe_email(token):
    """Unsubscribe from email notifications"""
    success = email_service.unsubscribe_email(token)
    if success:
        return render_template('email/unsubscribe_success.html')
    else:
        return render_template('email/unsubscribe_error.html'), 404

@app.route('/delete-account/<token>')
def delete_account(token):
    """Delete account via email link"""
    success = email_service.delete_account(token)
    if success:
        return render_template('email/delete_account_success.html')
    else:
        return render_template('email/delete_account_error.html'), 404

# Initialize email service
with app.app_context():
    email_service.init_app(app)

    # Schedule automatic event reminder checking
    def check_and_send_reminders():
        """Check for upcoming events and send reminders automatically"""
        try:
            send_event_reminders()
        except Exception as e:
            print(f"Error in automatic reminder check: {str(e)}")
    
    # Note: In production, you would use a proper task scheduler like Celery or APScheduler
    # For now, this function can be called manually via admin panel or cron job
    print("Email service initialized. Use admin panel to manually send reminders or set up a cron job.")

# API endpoint for registrations management
@app.route('/admin/api/registrations', methods=['PUT'])
@app.route('/admin/api/registrations/<int:registration_id>', methods=['DELETE'])
@login_required
def api_update_registration_status(registration_id=None):
    """Update registration status (approve/reject) or delete registration"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'DELETE':
        # Delete registration
        try:
            if not registration_id:
                return jsonify({'success': False, 'error': 'Brak ID rejestracji'})
            
            registration = Registration.query.get(registration_id)
            if not registration:
                return jsonify({'success': False, 'error': 'Rejestracja nie została znaleziona'})
            
            # Also remove from email subscriptions if exists
            subscription = EmailSubscription.query.filter_by(email=registration.email).first()
            if subscription:
                db.session.delete(subscription)
            
            # Delete registration
            db.session.delete(registration)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Rejestracja została usunięta'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
    
    elif request.method == 'PUT':
        # Update registration status
        try:
            data = request.form.to_dict()
            registration_id = data.get('id')
            new_status = data.get('status')
            
            if not registration_id or not new_status:
                return jsonify({'success': False, 'error': 'Brak ID rejestracji lub statusu'})
            
            registration = Registration.query.get(registration_id)
            if not registration:
                return jsonify({'success': False, 'error': 'Rejestracja nie została znaleziona'})
            
            # Update status
            registration.status = new_status
            
            # If approved, send notification to admin about new approved member
            if new_status == 'approved':
                print(f"DEBUG: Sending welcome email to {registration.email} for {registration.name}")
                
                # Send welcome email to the newly approved user
                try:
                    welcome_result = email_service.send_welcome_email(registration.email, registration.name)
                    print(f"DEBUG: Welcome email result: {welcome_result}")
                except Exception as e:
                    print(f"DEBUG: Error sending welcome email: {str(e)}")
                
                # Send notification to admin about new approved member
                admin_users = User.query.filter_by(is_admin=True).all()
                for admin in admin_users:
                    try:
                        admin_result = email_service.send_template_email(
                            to_email=admin.email,
                            template_name='admin_notification',
                            variables={
                                'admin_name': admin.username,
                                'new_member_name': registration.name,
                                'new_member_email': registration.email,
                                'registration_date': registration.created_at.strftime('%d.%m.%Y %H:%M') if registration.created_at else 'Brak'
                            }
                        )
                        print(f"DEBUG: Admin notification result for {admin.email}: {admin_result}")
                    except Exception as e:
                        print(f"DEBUG: Error sending admin notification to {admin.email}: {str(e)}")
            
            db.session.commit()
            return jsonify({'success': True, 'message': f'Status rejestracji został zmieniony na {new_status}'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})

# API endpoint for email statistics
@app.route('/admin/api/email-stats', methods=['GET'])
@login_required
def api_email_stats():
    """Get email statistics for admin panel"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        total_subscribers = EmailSubscription.query.filter_by(is_active=True).count()
        total_emails_sent = EmailLog.query.filter_by(status='sent').count()
        
        return jsonify({
            'success': True,
            'totalSubscribers': total_subscribers,
            'totalEmailsSent': total_emails_sent
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Helper functions for email schedules
def calculate_next_run_interval(interval_value, interval_unit):
    """Calculate next run time for interval-based schedules"""
    now = datetime.utcnow()
    
    if interval_unit == 'minutes':
        return now + timedelta(minutes=interval_value)
    elif interval_unit == 'hours':
        return now + timedelta(hours=interval_value)
    elif interval_unit == 'days':
        return now + timedelta(days=interval_value)
    elif interval_unit == 'weeks':
        return now + timedelta(weeks=interval_value)
    elif interval_unit == 'months':
        # Approximate month as 30 days
        return now + timedelta(days=interval_value * 30)
    else:
        return now + timedelta(days=1)  # Default to 1 day

def calculate_next_run_cron(cron_expression):
    """Calculate next run time for cron-based schedules"""
    try:
        # Simple cron parser for common patterns
        # Format: minute hour day month day_of_week
        parts = cron_expression.split()
        if len(parts) != 5:
            return datetime.utcnow() + timedelta(days=1)
        
        minute, hour, day, month, day_of_week = parts
        
        now = datetime.utcnow()
        next_run = now.replace(second=0, microsecond=0)
        
        # Handle minute
        if minute != '*':
            next_run = next_run.replace(minute=int(minute))
            if next_run <= now:
                next_run = next_run + timedelta(hours=1)
        
        # Handle hour
        if hour != '*':
            next_run = next_run.replace(hour=int(hour))
            if next_run <= now:
                next_run = next_run + timedelta(days=1)
        
        # Handle day of week (0=Sunday, 1=Monday, etc.)
        if day_of_week != '*':
            target_day = int(day_of_week)
            current_day = next_run.weekday()
            days_ahead = (target_day - current_day) % 7
            if days_ahead == 0 and next_run <= now:
                days_ahead = 7
            next_run = next_run + timedelta(days=days_ahead)
        
        # Ensure next_run is in the future
        if next_run <= now:
            next_run = next_run + timedelta(days=1)
        
        return next_run
        
    except Exception:
        # Fallback to next day if cron parsing fails
        return datetime.utcnow() + timedelta(days=1)

def execute_email_schedule(schedule):
    """Execute an email schedule based on its type and template"""
    try:
        if schedule.template_type == 'newsletter':
            # Send newsletter to all approved subscribers
            subscribers = email_service.get_approved_subscribers()
            if not subscribers:
                return "Brak aktywnych subskrybentów"
            
            sent_count = 0
            for subscriber in subscribers:
                try:
                    result = email_service.send_template_email(
                        subscriber.email, 
                        'newsletter',
                        {
                            'name': subscriber.name or 'Użytkowniku',
                            'email': subscriber.email,
                            'unsubscribe_url': url_for('unsubscribe_email', token=subscriber.unsubscribe_token, _external=True),
                            'delete_account_url': url_for('delete_account', token=subscriber.delete_token, _external=True)
                        }
                    )
                    if result:
                        sent_count += 1
                except Exception as e:
                    print(f"Error sending newsletter to {subscriber.email}: {str(e)}")
            
            return f"Wysłano newsletter do {sent_count}/{len(subscribers)} subskrybentów"
            
        elif schedule.template_type == 'notification':
            # Send notification based on trigger event
            if schedule.schedule_type == 'event_based':
                if schedule.trigger_event == 'weekly_summary':
                    return send_weekly_summary_notification()
                elif schedule.trigger_event == 'monthly_summary':
                    return send_monthly_summary_notification()
                elif schedule.trigger_event == 'new_event':
                    return "Oczekuje na nowe wydarzenie"
                elif schedule.trigger_event == 'new_member':
                    return "Oczekuje na nowego członka"
                elif schedule.trigger_event == 'event_reminder':
                    return send_event_reminders()
                else:
                    return f"Nieznane zdarzenie: {schedule.trigger_event}"
            else:
                # For interval/cron schedules, send general notification
                subscribers = email_service.get_approved_subscribers()
                if not subscribers:
                    return "Brak aktywnych subskrybentów"
                
                sent_count = 0
                for subscriber in subscribers:
                    try:
                        result = email_service.send_template_email(
                            subscriber.email, 
                            'notification',
                            {
                                'name': subscriber.name or 'Użytkowniku',
                                'email': subscriber.email,
                                'unsubscribe_url': url_for('unsubscribe_email', token=subscriber.unsubscribe_token, _external=True),
                                'delete_account_url': url_for('delete_account', token=subscriber.delete_token, _external=True)
                            }
                        )
                        if result:
                            sent_count += 1
                    except Exception as e:
                        print(f"Error sending newsletter to {subscriber.email}: {str(e)}")
                
                return f"Wysłano powiadomienie do {sent_count}/{len(subscribers)} subskrybentów"
        
        elif schedule.template_type == 'reminder':
            # Send reminder emails based on schedule type
            if schedule.schedule_type == 'event_based':
                if schedule.trigger_event == 'event_reminder':
                    return send_event_reminders()
                elif schedule.trigger_event == 'weekly_summary':
                    return send_weekly_summary_reminder()
                elif schedule.trigger_event == 'monthly_summary':
                    return send_monthly_summary_reminder()
                else:
                    return f"Nieznane zdarzenie dla przypomnienia: {schedule.trigger_event}"
            else:
                # For interval/cron schedules, send general reminders
                subscribers = email_service.get_approved_subscribers()
                if not subscribers:
                    return "Brak aktywnych subskrybentów"
                
                sent_count = 0
                for subscriber in subscribers:
                    try:
                        result = email_service.send_template_email(
                            subscriber.email, 
                            'reminder',
                            {
                                'name': subscriber.name or 'Użytkowniku',
                                'email': subscriber.email,
                                'reminder_type': 'Ogólne przypomnienie',
                                'reminder_message': 'To jest automatyczne przypomnienie o aktywności w klubie',
                                'unsubscribe_url': url_for('unsubscribe_email', token=subscriber.unsubscribe_token, _external=True),
                                'delete_account_url': url_for('delete_account', token=subscriber.delete_token, _external=True)
                            }
                        )
                        if result:
                            sent_count += 1
                    except Exception as e:
                        print(f"Error sending reminder to {subscriber.email}: {str(e)}")
                
                return f"Wysłano przypomnienia do {sent_count}/{len(subscribers)} subskrybentów"
        
        else:
            return f"Nieznany typ szablonu: {schedule.template_type}"
            
    except Exception as e:
        return f"Błąd podczas wykonywania harmonogramu: {str(e)}"

def send_weekly_summary_notification():
    """Send weekly summary notification to all subscribers"""
    try:
        subscribers = email_service.get_approved_subscribers()
        if not subscribers:
            return "Brak aktywnych subskrybentów"
        
        # Get weekly statistics
        week_start = datetime.utcnow() - timedelta(days=7)
        new_members = Registration.query.filter(
            Registration.created_at >= week_start,
            Registration.status == 'approved'
        ).count()
        
        sent_count = 0
        for subscriber in subscribers:
            try:
                result = email_service.send_template_email(
                    subscriber.email, 
                    'notification',
                    {
                        'name': subscriber.name or 'Użytkowniku',
                        'email': subscriber.email,
                        'weekly_stats': f"W tym tygodniu dołączyło {new_members} nowych członków",
                        'unsubscribe_url': url_for('unsubscribe_email', token=subscriber.unsubscribe_token, _external=True),
                        'delete_account_url': url_for('delete_account', token=subscriber.delete_token, _external=True)
                    }
                )
                if result:
                    sent_count += 1
            except Exception as e:
                print(f"Error sending weekly summary to {subscriber.email}: {str(e)}")
        
        return f"Wysłano podsumowanie tygodnia do {sent_count}/{len(subscribers)} subskrybentów"
        
    except Exception as e:
        return f"Błąd podczas wysyłania podsumowania tygodnia: {str(e)}"

def send_monthly_summary_notification():
    """Send monthly summary notification to all subscribers"""
    try:
        subscribers = email_service.get_approved_subscribers()
        if not subscribers:
            return "Brak aktywnych subskrybentów"
        
        # Get monthly statistics
        month_start = datetime.utcnow() - timedelta(days=30)
        new_members = Registration.query.filter(
            Registration.created_at >= month_start,
            Registration.status == 'approved'
        ).count()
        
        total_members = Registration.query.filter_by(status='approved').count()
        
        sent_count = 0
        for subscriber in subscribers:
            try:
                result = email_service.send_template_email(
                    subscriber.email, 
                    'notification',
                    {
                        'name': subscriber.name or 'Użytkowniku',
                        'email': subscriber.email,
                        'monthly_stats': f"W tym miesiącu dołączyło {new_members} nowych członków. Łącznie w klubie: {total_members} osób.",
                        'unsubscribe_url': url_for('unsubscribe_email', token=subscriber.unsubscribe_token, _external=True),
                        'delete_account_url': url_for('delete_account', token=subscriber.delete_token, _external=True)
                    }
                )
                if result:
                    sent_count += 1
            except Exception as e:
                print(f"Error sending monthly summary to {subscriber.email}: {str(e)}")
        
        return f"Wysłano podsumowanie miesiąca do {sent_count}/{len(subscribers)} subskrybentów"
        
    except Exception as e:
        return f"Błąd podczas wysyłania podsumowania miesiąca: {str(e)}"

def send_weekly_summary_reminder():
    """Send weekly summary reminder to all subscribers"""
    try:
        subscribers = email_service.get_approved_subscribers()
        if not subscribers:
            return "Brak aktywnych subskrybentów"
        
        # Get weekly statistics for reminder
        week_start = datetime.utcnow() - timedelta(days=7)
        new_members = Registration.query.filter(
            Registration.created_at >= week_start,
            Registration.status == 'approved'
        ).count()
        
        upcoming_events = 0  # Placeholder - można dodać logikę dla wydarzeń
        
        sent_count = 0
        for subscriber in subscribers:
            try:
                result = email_service.send_template_email(
                    subscriber.email, 
                    'reminder',
                    {
                        'name': subscriber.name or 'Użytkowniku',
                        'email': subscriber.email,
                        'reminder_type': 'Podsumowanie tygodnia',
                        'reminder_message': f'W tym tygodniu dołączyło {new_members} nowych członków. Sprawdź co nowego w klubie!',
                        'weekly_stats': f"Nowi członkowie: {new_members}, Nadchodzące wydarzenia: {upcoming_events}",
                        'unsubscribe_url': url_for('unsubscribe_email', token=subscriber.unsubscribe_token, _external=True),
                        'delete_account_url': url_for('delete_account', token=subscriber.delete_token, _external=True)
                    }
                )
                if result:
                    sent_count += 1
            except Exception as e:
                print(f"Error sending weekly reminder to {subscriber.email}: {str(e)}")
        
        return f"Wysłano przypomnienia tygodniowe do {sent_count}/{len(subscribers)} subskrybentów"
        
    except Exception as e:
        return f"Błąd podczas wysyłania przypomnienia tygodniowego: {str(e)}"

def send_monthly_summary_reminder():
    """Send monthly summary reminder to all subscribers"""
    try:
        subscribers = email_service.get_approved_subscribers()
        if not subscribers:
            return "Brak aktywnych subskrybentów"
        
        # Get monthly statistics for reminder
        month_start = datetime.utcnow() - timedelta(days=30)
        new_members = Registration.query.filter(
            Registration.created_at >= month_start,
            Registration.status == 'approved'
        ).count()
        
        total_members = Registration.query.filter_by(status='approved').count()
        
        sent_count = 0
        for subscriber in subscribers:
            try:
                result = email_service.send_template_email(
                    subscriber.email, 
                    'reminder',
                    {
                        'name': subscriber.name or 'Użytkowniku',
                        'email': subscriber.email,
                        'reminder_type': 'Podsumowanie miesiąca',
                        'reminder_message': f'W tym miesiącu klub rośnie! Sprawdź co nowego i bądź aktywny.',
                        'monthly_stats': f"Nowi członkowie: {new_members}, Łącznie w klubie: {total_members} osób",
                        'unsubscribe_url': url_for('unsubscribe_email', token=subscriber.unsubscribe_token, _external=True),
                        'delete_account_url': url_for('delete_account', token=subscriber.delete_token, _external=True)
                    }
                )
                if result:
                    sent_count += 1
            except Exception as e:
                print(f"Error sending monthly reminder to {subscriber.email}: {str(e)}")
        
        return f"Wysłano przypomnienia miesięczne do {sent_count}/{len(subscribers)} subskrybentów"
        
    except Exception as e:
        return f"Błąd podczas wysyłania przypomnienia miesięcznego: {str(e)}"

def check_and_run_schedules():
    """Check and run due email schedules - to be called by cron job"""
    try:
        print(f"Checking schedules at {datetime.utcnow()}")
        
        # Find schedules that are due to run
        now = datetime.utcnow()
        due_schedules = EmailSchedule.query.filter(
            EmailSchedule.is_active == True,
            EmailSchedule.next_run <= now
        ).all()
        
        if not due_schedules:
            print("No schedules due to run")
            return
        
        print(f"Found {len(due_schedules)} schedules to run")
        
        for schedule in due_schedules:
            try:
                print(f"Executing schedule: {schedule.name} (ID: {schedule.id})")
                
                # Execute the schedule
                result = execute_email_schedule(schedule)
                print(f"Schedule {schedule.name} result: {result}")
                
                # Update last_run and next_run
                schedule.last_run = now
                if schedule.schedule_type in ['interval', 'cron']:
                    if schedule.schedule_type == 'interval':
                        schedule.next_run = calculate_next_run_interval(
                            schedule.interval_value, schedule.interval_unit
                        )
                    elif schedule.schedule_type == 'cron':
                        schedule.next_run = calculate_next_run_cron(
                            schedule.cron_expression
                        )
                
                schedule.updated_at = now
                
            except Exception as e:
                print(f"Error executing schedule {schedule.name}: {str(e)}")
        
        # Commit all changes
        db.session.commit()
        print(f"Successfully processed {len(due_schedules)} schedules")
        
    except Exception as e:
        print(f"Error in check_and_run_schedules: {str(e)}")
        db.session.rollback()

# Helper functions for email campaigns
def calculate_filtered_recipients_count(filters_json):
    """Calculate number of recipients based on filter criteria"""
    try:
        filters = json.loads(filters_json) if isinstance(filters_json, str) else filters_json
        
        query = Registration.query
        
        # Apply status filter
        if filters.get('status'):
            query = query.filter_by(status=filters['status'])
        
        # Apply date filters
        if filters.get('date_from'):
            date_from = datetime.fromisoformat(filters['date_from'])
            query = query.filter(Registration.created_at >= date_from)
        
        if filters.get('date_to'):
            date_to = datetime.fromisoformat(filters['date_to'])
            query = query.filter(Registration.created_at <= date_to)
        
        return query.count()
        
    except Exception as e:
        print(f"Error calculating filtered recipients count: {str(e)}")
        return 0

def get_campaign_recipients(campaign):
    """Get list of recipients for a campaign based on its type"""
    try:
        if campaign.recipient_type == 'specific':
            # Get specific email addresses
            if not campaign.recipient_emails:
                return []
            
            emails_list = json.loads(campaign.recipient_emails) if isinstance(campaign.recipient_emails, str) else campaign.recipient_emails
            
            recipients = []
            for email in emails_list:
                # Try to get subscriber info
                subscription = EmailSubscription.query.filter_by(email=email, is_active=True).first()
                if subscription:
                    recipients.append({
                        'email': email,
                        'name': subscription.name,
                        'unsubscribe_token': subscription.unsubscribe_token,
                        'delete_token': subscription.delete_token
                    })
                else:
                    # Add as anonymous recipient
                    recipients.append({
                        'email': email,
                        'name': None,
                        'unsubscribe_token': None,
                        'delete_token': None
                    })
            
            return recipients
            
        elif campaign.recipient_type == 'filtered':
            # Get recipients based on filters
            if not campaign.recipient_filters:
                return []
            
            filters = json.loads(campaign.recipient_filters) if isinstance(campaign.recipient_filters, str) else campaign.recipient_filters
            
            query = Registration.query
            
            # Apply status filter
            if filters.get('status'):
                query = query.filter_by(status=filters['status'])
            
            # Apply date filters
            if filters.get('date_from'):
                date_from = datetime.fromisoformat(filters['date_from'])
                query = query.filter(Registration.created_at >= date_from)
            
            if filters.get('date_to'):
                date_to = datetime.fromisoformat(filters['date_to'])
                query = query.filter(Registration.created_at <= date_to)
            
            registrations = query.all()
            
            recipients = []
            for registration in registrations:
                # Get subscription info
                subscription = EmailSubscription.query.filter_by(email=registration.email, is_active=True).first()
                if subscription:
                    recipients.append({
                        'email': registration.email,
                        'name': registration.name,
                        'unsubscribe_token': subscription.unsubscribe_token,
                        'delete_token': subscription.delete_token
                    })
            
            return recipients
            
        elif campaign.recipient_type == 'all':
            # Get all approved subscribers
            subscribers = email_service.get_approved_subscribers()
            recipients = []
            
            for subscriber in subscribers:
                recipients.append({
                    'email': subscriber.email,
                    'name': subscriber.name,
                    'unsubscribe_token': subscriber.unsubscribe_token,
                    'delete_token': subscriber.delete_token
                })
            
            return recipients
        
        else:
            return []
            
    except Exception as e:
        print(f"Error getting campaign recipients: {str(e)}")
        return []

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
