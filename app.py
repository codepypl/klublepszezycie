from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import models and config
from models import db, User, MenuItem, Section, BenefitItem, Testimonial, SocialLink, Registration, FAQ, SEOSettings, EventSchedule, Page, EmailTemplate, EmailSubscription, EmailLog
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
            email='admin@lepszezycie.pl',
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin_user)
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
        
        # Create default notification template
        notification_template = EmailTemplate.query.filter_by(template_type='notification').first()
        if not notification_template:
            notification_template = EmailTemplate(
                name='Powiadomienie Systemowe',
                subject='🔔 {{notification_title}}',
                html_content='''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Powiadomienie Systemowe</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #dc3545; margin-bottom: 10px;">🔔 Powiadomienie Systemowe</h1>
        <p style="font-size: 18px; color: #666;">Ważna informacja dla Ciebie</p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #007bff; margin-top: 0;">Cześć {{name}}!</h2>
        <p>Mamy dla Ciebie ważną wiadomość:</p>
        
        <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #856404; margin-top: 0;">📢 {{notification_title}}</h3>
            <p style="margin: 5px 0;"><strong>Data:</strong> {{notification_date}}</p>
            <p style="margin: 5px 0;"><strong>Wiadomość:</strong></p>
            <div style="background-color: white; padding: 10px; border-radius: 3px; margin-top: 10px;">
                {{notification_message}}
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
Powiadomienie Systemowe 🔔

Cześć {{name}}!

Mamy dla Ciebie ważną wiadomość:

{{notification_title}}
Data: {{notification_date}}

Wiadomość:
{{notification_message}}

Twoje dane są bezpieczne - możesz w każdej chwili:
- Zrezygnować z subskrypcji: {{unsubscribe_url}}
- Usunąć swoje konto: {{delete_account_url}}

Z poważaniem,
Zespół Klubu Lepsze Życie

Ten email został wysłany na adres {{email}}
                ''',
                template_type='notification',
                variables='name,email,notification_title,notification_date,notification_message,unsubscribe_url,delete_account_url',
                is_active=True
            )
            db.session.add(notification_template)
        
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
    
    return render_template('index.html',
                         next_event=next_event,
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
        
        flash(f'Dziękujemy {name}! Twoje miejsce zostało zarezerwowane. Administrator zostanie powiadomiony o Twojej rejestracji i skontaktuje się z Tobą.', 'success')
            
        return redirect(url_for('index'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error during registration: {str(e)}")
        flash('Wystąpił błąd podczas rejestracji. Spróbuj ponownie.', 'error')
        return redirect(url_for('index'))

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
        data = request.get_json() if request.is_json else request.form.to_dict()
        item_id = data.get('id')
        item = MenuItem.query.get(item_id)
        
        if not item:
            return jsonify({'success': False, 'error': 'Menu item not found'}), 404
        
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True})

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
        section_id = request.args.get('id', type=int)
        section = Section.query.get(section_id)
        if section:
            db.session.delete(section)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Section not found'}), 404

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
                    import uuid
                    import os
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
                        import uuid
                        import os
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
        benefit_id = request.args.get('id', type=int)
        benefit = BenefitItem.query.get(benefit_id)
        if benefit:
            # Usuń plik obrazu jeśli istnieje
            if benefit.image and os.path.exists(benefit.image):
                try:
                    os.remove(benefit.image)
                except:
                    pass  # Ignoruj błędy usuwania
            
            db.session.delete(benefit)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Benefit not found'}), 404

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
        link_id = request.args.get('id', type=int)
        link = SocialLink.query.get(link_id)
        if link:
            db.session.delete(link)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Social link not found'}), 404

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
        testimonial_id = request.args.get('id', type=int)
        testimonial = Testimonial.query.get(testimonial_id)
        if testimonial:
            db.session.delete(testimonial)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Testimonial not found'}), 404

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
        
        # Parse datetime
        event_date = datetime.fromisoformat(data['event_date'].replace('Z', '+00:00'))
        
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
                    template_name='Przypomnienie o Wydarzeniu',
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
        if 'is_active' in data:
            data['is_active'] = data['is_active'] in [True, 'true', 'True', '1', 1]
        else:
            data['is_active'] = False
        
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
        if 'is_active' in data:
            data['is_active'] = data['is_active'] in [True, 'true', 'True', '1', 1]
        else:
            data['is_active'] = False
        
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

# Admin API for email subscriptions
@app.route('/admin/api/email-subscriptions', methods=['GET', 'DELETE'])
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

@app.route('/admin/api/send-notification', methods=['POST'])
@login_required
def api_send_notification():
    """Send system notification to all subscribers"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        data = request.form.to_dict()
        notification_title = data.get('notification_title', '')
        notification_message = data.get('notification_message', '')
        
        if not notification_title or not notification_message:
            return jsonify({'success': False, 'error': 'Brak tytułu lub treści powiadomienia'})
        
        # Get all active subscribers
        subscribers = email_service.get_approved_subscribers()
        
        if not subscribers:
            return jsonify({'success': False, 'error': 'Brak aktywnych subskrybentów'})
        
        # Send notification to all subscribers
        success_count = 0
        for subscriber in subscribers:
            variables = {
                'name': subscriber.name or 'Użytkowniku',
                'email': subscriber.email,
                'notification_title': notification_title,
                'notification_message': notification_message,
                'notification_date': datetime.now().strftime('%d.%m.%Y %H:%M')
            }
            
            success = email_service.send_template_email(
                to_email=subscriber.email,
                template_name='notification',
                variables=variables
            )
            
            if success:
                success_count += 1
        
        return jsonify({
            'success': True, 
            'message': f'Powiadomienie wysłane do {success_count}/{len(subscribers)} subskrybentów'
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
                # Send welcome email to the newly approved user
                email_service.send_welcome_email(registration.email, registration.name)
                
                # Send notification to admin about new approved member
                admin_users = User.query.filter_by(is_admin=True).all()
                for admin in admin_users:
                    email_service.send_template_email(
                        to_email=admin.email,
                        template_name='admin_notification',
                        variables={
                            'admin_name': admin.username,
                            'new_member_name': registration.name,
                            'new_member_email': registration.email,
                            'registration_date': registration.created_at.strftime('%d.%m.%Y %H:%M') if registration.created_at else 'Brak'
                        }
                    )
            
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



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
