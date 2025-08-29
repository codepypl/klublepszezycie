#!/usr/bin/env python3
"""
Database initialization script for Better Life Club
Creates tables and populates with sample data
"""

import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
import secrets

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import (
    User, MenuItem, Section, BenefitItem, Testimonial, SocialLink, 
    FAQ, PresentationSchedule, Registration, Page, EmailTemplate, 
    EmailSubscription, EmailLog, SEOSettings, EventSchedule
)
from werkzeug.security import generate_password_hash

def init_database():
    """Initialize database with sample data"""
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        print("Creating admin user...")
        # Create admin user
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@lepszezycie.pl',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin_user)
            print("✓ Admin user created")
        else:
            print("✓ Admin user already exists")
        
        print("Creating menu items...")
        # Create menu items
        menu_items_data = [
            {'title': 'Start', 'url': '#hero', 'order': 1, 'is_active': True},
            {'title': 'Korzyści', 'url': '#benefits', 'order': 2, 'is_active': True},
            {'title': 'O Klubie', 'url': '#about', 'order': 3, 'is_active': True},
            {'title': 'Opinie', 'url': '#testimonials', 'order': 4, 'is_active': True},
            {'title': 'Zapisz się', 'url': '#register', 'order': 5, 'is_active': True}
        ]
        
        for item_data in menu_items_data:
            existing_item = MenuItem.query.filter_by(title=item_data['title']).first()
            if not existing_item:
                menu_item = MenuItem(**item_data)
                db.session.add(menu_item)
                print(f"✓ Menu item '{item_data['title']}' created")
            else:
                print(f"✓ Menu item '{item_data['title']}' already exists")
        
        print("Creating sections...")
        # Create sections
        sections_data = [
            {
                'name': 'hero',
                'title': '💡 Chcesz lepsze życie po 50-tce? Dołącz do klubu, który zmienia życie w 4 kluczowych obszarach!',
                'subtitle': 'Odkryj, jak Klub "Lepsze Życie" pomaga osobom 50+ poprawić finanse, zdrowie, budować społeczność i opanować narzędzia AI — aby żyć mądrzej i pełniej.',
                'background_image': 'static/images/hero/hero-bg.jpg',
                'order': 1,
                'is_active': True
            },
            {
                'name': 'benefits',
                'title': '🧭 Czego nauczysz się na prezentacji',
                'subtitle': 'Praktyczna wiedza dostosowana do potrzeb osób 50+, która zmieni Twoje życie',
                'order': 2,
                'is_active': True
            },
            {
                'name': 'about',
                'title': '🌱 Klub zbudowany specjalnie dla osób 50+',
                'content': '"Lepsze Życie" to więcej niż tylko klub. To społeczność osób 50+, które rozumieją, że życie po pięćdziesiątce może być najlepszym okresem w życiu.',
                'background_image': 'static/images/about/community-senior.jpg',
                'enable_pillars': True,
                'enable_floating_cards': True,
                'pillars_count': 4,
                'floating_cards_count': 3,
                'pillars_data': json.dumps([
                    {
                        'icon': 'fas fa-coins',
                        'title': 'Finanse',
                        'color': 'text-primary',
                        'description': 'Mądre zarządzanie finansami po 50-tce',
                        'link': '/finanse'
                    },
                    {
                        'icon': 'fas fa-heart',
                        'title': 'Zdrowie',
                        'color': 'text-success',
                        'description': 'Witalność i energia w każdym wieku',
                        'link': '/zdrowie'
                    },
                    {
                        'icon': 'fas fa-users',
                        'title': 'Społeczność',
                        'color': 'text-info',
                        'description': 'Budowanie prawdziwych przyjaźni',
                        'link': '/spolecznosc'
                    },
                    {
                        'icon': 'fas fa-robot',
                        'title': 'AI & Technologia',
                        'color': 'text-warning',
                        'description': 'Nowoczesne narzędzia dla lepszego życia',
                        'link': '/ai-technologia'
                    }
                ]),
                'floating_cards_data': json.dumps([
                    {
                        'icon': 'fas fa-lightbulb',
                        'title': 'Inspiracja',
                        'color': 'text-primary',
                        'delay': 0,
                        'link': '/inspiracja'
                    },
                    {
                        'icon': 'fas fa-star',
                        'title': 'Wiedza',
                        'color': 'text-warning',
                        'delay': 200,
                        'link': '/wiedza'
                    },
                    {
                        'icon': 'fas fa-rocket',
                        'title': 'Rozwój',
                        'color': 'text-success',
                        'delay': 400,
                        'link': '/rozwoj'
                    }
                ]),
                'order': 3,
                'is_active': True
            },
            {
                'name': 'testimonials',
                'title': '💬 Co mówią nasi członkowie 50+',
                'subtitle': 'Prawdziwe historie osób, które zmieniły swoje życie dzięki klubowi',
                'order': 4,
                'is_active': True
            },
            {
                'name': 'cta',
                'title': '🚀 Gotowy na lepsze życie po 50-tce?',
                'subtitle': 'Zarezerwuj miejsce w darmowej prezentacji "Lepsze Życie" — i dowiedz się, jak ten klub może pomóc Ci żyć z większym celem, społecznością i nowoczesnymi umiejętnościami.',
                'order': 5,
                'is_active': True
            },
            {
                'name': 'faq',
                'title': '❓ Często zadawane pytania',
                'subtitle': 'Odpowiedzi na najczęściej zadawane pytania o klub "Lepsze Życie"',
                'order': 6,
                'is_active': True
            }
        ]
        
        for section_data in sections_data:
            existing_section = Section.query.filter_by(name=section_data['name']).first()
            if not existing_section:
                section = Section(**section_data)
                db.session.add(section)
                print(f"✓ Section '{section_data['name']}' created")
            else:
                print(f"✓ Section '{section_data['name']}' already exists")
        
        # Commit sections first to get their IDs
        db.session.commit()
        
        print("Creating benefit items...")
        # Create benefit items
        benefits_data = [
            {
                'title': 'Finanse & Gift of Legacy',
                'description': 'Poznaj koncepcję "Gift of Legacy" - jak mądrze zarządzać finansami, planować spadek i przekazać wartościowe dziedzictwo rodzinie',
                'icon': 'fas fa-gift',
                'image': 'static/images/benefits/legacy.jpg',
                'order': 1,
                'is_active': True
            },
            {
                'title': 'Narzędzia AI dla 50+',
                'description': 'Naucz się korzystać z Chat GPT i innych narzędzi AI w codziennym życiu. Poznaj plusy i minusy, bezpieczne praktyki',
                'icon': 'fas fa-robot',
                'image': 'static/images/benefits/ai-senior.jpg',
                'order': 2,
                'is_active': True
            },
            {
                'title': 'Społeczność & Przeciwdziałanie Samotności',
                'description': 'Dołącz do społeczności osób 50+, która wspólnie organizuje eventy, spotkania i spędza czas, budując prawdziwe przyjaźnie',
                'icon': 'fas fa-hands-helping',
                'image': 'static/images/benefits/community-senior.jpg',
                'order': 3,
                'is_active': True
            },
            {
                'title': 'Zdrowie & Witalność',
                'description': 'Proste sposoby na poprawę zdrowia i energii po 50-tce, dostosowane do Twoich możliwości i stylu życia',
                'icon': 'fas fa-heart',
                'image': 'static/images/benefits/health-senior.jpg',
                'order': 4,
                'is_active': True
            }
        ]
        
        for benefit_data in benefits_data:
            existing_benefit = BenefitItem.query.filter_by(title=benefit_data['title']).first()
            if not existing_benefit:
                benefit = BenefitItem(**benefit_data)
                db.session.add(benefit)
                print(f"✓ Benefit '{benefit_data['title']}' created")
            else:
                print(f"✓ Benefit '{benefit_data['title']}' already exists")
        
        print("Creating testimonials...")
        # Create testimonials
        testimonials_data = [
            {
                'author_name': 'Jan K., 58 lat',
                'content': 'Dzięki klubowi nauczyłem się zarządzać finansami i planować przyszłość. Teraz czuję się bezpieczniej finansowo.',
                'member_since': '2023',
                'rating': 5,
                'is_active': True
            },
            {
                'author_name': 'Maria W., 62 lata',
                'content': 'Narzędzia AI, których nauczyłam się w klubie, oszczędzają mi czas w codziennych sprawach. Chat GPT pomaga mi w planowaniu.',
                'member_since': '2024',
                'rating': 5,
                'is_active': True
            },
            {
                'author_name': 'Piotr M., 55 lat',
                'content': 'Klub pomógł mi zbudować nowe przyjaźnie i znaleźć pasję w wieku, gdy myślałem, że to już niemożliwe.',
                'member_since': '2023',
                'rating': 5,
                'is_active': True
            }
        ]
        
        for testimonial_data in testimonials_data:
            existing_testimonial = Testimonial.query.filter_by(author_name=testimonial_data['author_name']).first()
            if not existing_testimonial:
                testimonial = Testimonial(**testimonial_data)
                db.session.add(testimonial)
                print(f"✓ Testimonial from '{testimonial_data['author_name']}' created")
            else:
                print(f"✓ Testimonial from '{testimonial_data['author_name']}' already exists")
        
        print("Creating social links...")
        # Create social links
        social_links_data = [
            {'platform': 'Facebook', 'url': '#', 'icon': 'fab fa-facebook', 'order': 1, 'is_active': True},
            {'platform': 'Instagram', 'url': '#', 'icon': 'fab fa-instagram', 'order': 2, 'is_active': True},
            {'platform': 'LinkedIn', 'url': '#', 'icon': 'fab fa-linkedin', 'order': 3, 'is_active': True},
            {'platform': 'YouTube', 'url': '#', 'icon': 'fab fa-youtube', 'order': 4, 'is_active': True}
        ]
        
        for link_data in social_links_data:
            existing_link = SocialLink.query.filter_by(platform=link_data['platform']).first()
            if not existing_link:
                social_link = SocialLink(**link_data)
                db.session.add(social_link)
                print(f"✓ Social link '{link_data['platform']}' created")
            else:
                print(f"✓ Social link '{link_data['platform']}' already exists")
        
        print("Creating FAQ items...")
        # Create FAQ items
        faq_data = [
            {
                'question': 'Czy ta prezentacja jest darmowa?',
                'answer': 'Tak, 100% darmowo. Nie ma żadnych kosztów i żadnych zobowiązań do dołączenia.',
                'order': 1,
                'is_active': True
            },
            {
                'question': 'Czy potrzebuję doświadczenia z AI lub rozwojem osobistym?',
                'answer': 'Nie! Witamy ludzi ze wszystkich środowisk. Prezentacja jest dostosowana do początkujących.',
                'order': 2,
                'is_active': True
            },
            {
                'question': 'Co jeśli nie mogę uczestniczyć na żywo?',
                'answer': 'Zarejestruj się i tak, a wyślemy Ci nagranie (jeśli będzie dostępne).',
                'order': 3,
                'is_active': True
            },
            {
                'question': 'Jak długo trwa prezentacja?',
                'answer': 'Prezentacja trwa około 60-90 minut, w tym czas na pytania i odpowiedzi.',
                'order': 4,
                'is_active': True
            },
            {
                'question': 'Czy otrzymam materiały po prezentacji?',
                'answer': 'Tak, wszyscy uczestnicy otrzymają podsumowanie i dodatkowe materiały drogą elektroniczną.',
                'order': 5,
                'is_active': True
            }
        ]
        
        for faq_item in faq_data:
            existing_faq = FAQ.query.filter_by(question=faq_item['question']).first()
            if not existing_faq:
                faq = FAQ(**faq_item)
                db.session.add(faq)
                print(f"✓ FAQ '{faq_item['question'][:30]}...' created")
            else:
                print(f"✓ FAQ '{faq_item['question'][:30]}...' already exists")
        
        print("Creating email templates...")
        # Create email templates
        email_templates_data = [
            {
                'name': 'welcome',
                'subject': 'Witamy w Klubie Lepsze Życie!',
                'html_content': '''
                <h2>Witamy w Klubie Lepsze Życie!</h2>
                <p>Cześć {{name}},</p>
                <p>Dziękujemy za dołączenie do naszego klubu! Jesteśmy podekscytowani, że będziesz częścią społeczności osób 50+, które dążą do lepszego życia.</p>
                <p>Wkrótce otrzymasz więcej informacji o naszych wydarzeniach i możliwościach rozwoju.</p>
                <p>Pozdrawiamy,<br>Zespół Klubu Lepsze Życie</p>
                ''',
                'text_content': 'Witamy w Klubie Lepsze Życie! Dziękujemy za dołączenie.',
                'template_type': 'welcome',
                'variables': json.dumps(['name', 'email']),
                'is_active': True
            },
            {
                'name': 'reminder',
                'subject': 'Przypomnienie o wydarzeniu - {{event_title}}',
                'html_content': '''
                <h2>Przypomnienie o wydarzeniu</h2>
                <p>Cześć {{name}},</p>
                <p>Przypominamy o jutrzejszym wydarzeniu: <strong>{{event_title}}</strong></p>
                <p><strong>Data:</strong> {{event_date}}<br>
                <strong>Godzina:</strong> {{event_time}}<br>
                <strong>Miejsce:</strong> {{event_location}}</p>
                <p>Do zobaczenia!</p>
                <p>Pozdrawiamy,<br>Zespół Klubu Lepsze Życie</p>
                ''',
                'text_content': 'Przypomnienie o jutrzejszym wydarzeniu: {{event_title}}',
                'template_type': 'reminder',
                'variables': json.dumps(['name', 'event_title', 'event_date', 'event_time', 'event_location']),
                'is_active': True
            }
        ]
        
        for template_data in email_templates_data:
            existing_template = EmailTemplate.query.filter_by(name=template_data['name']).first()
            if not existing_template:
                template = EmailTemplate(**template_data)
                db.session.add(template)
                print(f"✓ Email template '{template_data['name']}' created")
            else:
                print(f"✓ Email template '{template_data['name']}' already exists")
        
        print("Creating SEO settings...")
        # Create SEO settings
        seo_settings_data = [
            {
                'page_type': 'home',
                'page_title': 'Klub Lepsze Życie - Lepsze życie po 50-tce',
                'meta_description': 'Dołącz do klubu osób 50+ i odkryj, jak poprawić finanse, zdrowie, budować społeczność i opanować narzędzia AI.',
                'meta_keywords': 'klub 50+, rozwój osobisty, finanse, zdrowie, społeczność, AI, lepsze życie',
                'og_title': 'Klub Lepsze Życie - Lepsze życie po 50-tce',
                'og_description': 'Dołącz do klubu osób 50+ i odkryj, jak poprawić finanse, zdrowie, budować społeczność i opanować narzędzia AI.',
                'og_image': 'static/images/hero/hero-bg.jpg',
                'og_type': 'website',
                'twitter_card': 'summary_large_image',
                'twitter_title': 'Klub Lepsze Życie - Lepsze życie po 50-tce',
                'twitter_description': 'Dołącz do klubu osób 50+ i odkryj, jak poprawić finanse, zdrowie, budować społeczność i opanować narzędzia AI.',
                'twitter_image': 'static/images/hero/hero-bg.jpg',
                'canonical_url': 'https://lepszezycie.pl',
                'is_active': True
            }
        ]
        
        for seo_data in seo_settings_data:
            existing_seo = SEOSettings.query.filter_by(page_type=seo_data['page_type']).first()
            if not existing_seo:
                seo = SEOSettings(**seo_data)
                db.session.add(seo)
                print(f"✓ SEO settings for '{seo_data['page_type']}' created")
            else:
                print(f"✓ SEO settings for '{seo_data['page_type']}' already exists")
        
        print("Creating sample pages...")
        # Create sample pages
        pages_data = [
            {
                'title': 'O nas',
                'slug': 'o-nas',
                'content': '<h1>O Klubie Lepsze Życie</h1><p>Jesteśmy społecznością osób 50+, które wierzą, że życie po pięćdziesiątce może być najlepszym okresem w życiu.</p>',
                'meta_description': 'Poznaj historię i misję Klubu Lepsze Życie - społeczności osób 50+ dążących do lepszego życia.',
                'meta_keywords': 'o nas, historia, misja, klub lepsze życie',
                'is_active': True,
                'is_published': True,
                'published_at': datetime.now()
            }
        ]
        
        for page_data in pages_data:
            existing_page = Page.query.filter_by(slug=page_data['slug']).first()
            if not existing_page:
                page = Page(**page_data)
                db.session.add(page)
                print(f"✓ Page '{page_data['title']}' created")
            else:
                print(f"✓ Page '{page_data['title']}' already exists")
        
        print("Creating sample event schedule...")
        # Create sample event schedule
        existing_event = EventSchedule.query.first()
        if not existing_event:
            # Calculate next Saturday at 10:00
            today = datetime.now()
            days_until_saturday = (5 - today.weekday()) % 7
            if days_until_saturday == 0 and today.hour >= 10:
                days_until_saturday = 7
            next_saturday = today + timedelta(days=days_until_saturday)
            next_event = next_saturday.replace(hour=10, minute=0, second=0, microsecond=0)
            
            sample_event = EventSchedule(
                title='Prezentacja "Lepsze Życie"',
                event_type='Prezentacja',
                event_date=next_event,
                end_date=next_event + timedelta(hours=1, minutes=30),
                description='Darmowa prezentacja o tym, jak klub może pomóc Ci żyć lepiej po 50-tce.',
                meeting_link='https://meet.google.com/xxx-yyyy-zzz',
                location='Online',
                is_active=True,
                is_published=True
            )
            db.session.add(sample_event)
            print(f"✓ Sample event created for {next_event.strftime('%d.%m.%Y o %H:%M')}")
        else:
            print("✓ Sample event already exists")
        
        # Commit all changes
        db.session.commit()
        print("✓ All data created successfully!")
        
        print("Creating presentation schedule...")
        # Create default presentation schedule
        existing_schedule = PresentationSchedule.query.first()
        if not existing_schedule:
            # Calculate next Saturday at 10:00
            today = datetime.now()
            days_until_saturday = (5 - today.weekday()) % 7
            if days_until_saturday == 0 and today.hour >= 10:
                days_until_saturday = 7
            next_saturday = today + timedelta(days=days_until_saturday)
            next_presentation = next_saturday.replace(hour=10, minute=0, second=0, microsecond=0)
            
            default_schedule = PresentationSchedule(
                title='Następna sesja',
                next_presentation_date=next_presentation,
                custom_text='',
                is_active=True
            )
            db.session.add(default_schedule)
            print(f"✓ Default presentation schedule created for {next_presentation.strftime('%d.%m.%Y o %H:%M')}")
        else:
            print("✓ Presentation schedule already exists")
        
        # Final commit
        db.session.commit()
        print("✓ Database initialization completed!")
        print("\n📋 Login credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        print("\n🌐 Access admin panel at: http://localhost:5000/admin")

if __name__ == '__main__':
    init_database()

