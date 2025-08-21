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
from models import db, User, MenuItem, Section, BenefitItem, Testimonial, SocialLink, Registration, FAQ, SEOSettings, PresentationSchedule
from config import config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config['development'])

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

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

# Routes
@app.route('/')
def index():
    # Get data from database
    menu_items = MenuItem.query.filter_by(is_active=True).order_by(MenuItem.order).all()
    hero_section = Section.query.filter_by(name='hero', is_active=True).first()
    benefits_section = Section.query.filter_by(name='benefits', is_active=True).first()
    benefits_items = BenefitItem.query.filter_by(is_active=True).order_by(BenefitItem.order).all()
    about_section = Section.query.filter_by(name='about', is_active=True).first()
    testimonials = Testimonial.query.filter_by(is_active=True).order_by(Testimonial.created_at.desc()).limit(3).all()
    social_links = SocialLink.query.filter_by(is_active=True).order_by(SocialLink.order).all()
    faqs = FAQ.query.filter_by(is_active=True).order_by(FAQ.order).all()
    
    # Get next presentation date from database or calculate default
    schedule = PresentationSchedule.query.filter_by(is_active=True).first()
    if schedule and schedule.next_presentation_date:
        next_presentation = schedule.next_presentation_date
    else:
        # Fallback to automatic calculation
        today = datetime.now()
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0 and today.hour >= 10:
            days_until_saturday = 7
        next_saturday = today + timedelta(days=days_until_saturday)
        next_presentation = next_saturday.replace(hour=10, minute=0, second=0, microsecond=0)
    
    return render_template('index.html',
                         next_presentation=next_presentation,
                         schedule=schedule,
                         testimonials=testimonials,
                         menu_items=menu_items,
                         hero_section=hero_section,
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
    
    # Save registration to database
    registration = Registration(
        name=name,
        email=email,
        phone=phone,
        status='pending'
    )
    db.session.add(registration)
    db.session.commit()
    
    flash(f'Dziękujemy {name}! Twoje miejsce zostało zarezerwowane. Wysyłamy potwierdzenie na adres {email}.', 'success')
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

@app.route('/admin/presentation-schedule')
@login_required
def admin_presentation_schedule():
    if not current_user.is_admin:
        return redirect(url_for('admin_login'))
    
    schedule = PresentationSchedule.query.first()
    return render_template('admin/presentation_schedule.html', schedule=schedule)

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
            # Konwertujemy checkbox na boolean
            data['is_active'] = 'is_active' in request.form
        
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
        # Obsługujemy zarówno JSON jak i FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            # Konwertujemy checkbox na boolean
            data['is_active'] = 'is_active' in request.form
        
        item = MenuItem.query.get(data['id'])
        if item:
            item.title = data['title']
            item.url = data['url']
            item.order = data['order']
            item.is_active = data.get('is_active', True)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Item not found'}), 404
    
    elif request.method == 'DELETE':
        item_id = request.args.get('id', type=int)
        item = MenuItem.query.get(item_id)
        if item:
            db.session.delete(item)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Item not found'}), 404

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
            'order': section.order,
            'is_active': section.is_active
        } for section in sections])
    
    elif request.method == 'POST':
        # Obsługujemy zarówno JSON jak i FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            # Konwertujemy checkbox na boolean
            data['is_active'] = 'is_active' in request.form
        
        new_section = Section(
            name=data['name'],
            title=data.get('title'),
            subtitle=data.get('subtitle'),
            content=data.get('content'),
            background_image=data.get('background_image'),
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
            # Konwertujemy checkbox na boolean
            data['is_active'] = 'is_active' in request.form
        
        section = Section.query.get(data['id'])
        if section:
            section.name = data.get('name')
            section.title = data.get('title')
            section.subtitle = data.get('subtitle')
            section.content = data.get('content')
            section.background_image = data.get('background_image')
            section.order = data.get('order', 0)
            section.is_active = data.get('is_active', True)
            db.session.commit()
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
        # Obsługujemy zarówno JSON jak i FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            # Konwertujemy checkbox na boolean
            data['is_active'] = 'is_active' in request.form
        
        new_benefit = BenefitItem(
            title=data['title'],
            description=data['description'],
            icon=data.get('icon', ''),
            image=data.get('image', ''),
            order=data.get('order', 0),
            is_active=data.get('is_active', True)
        )
        db.session.add(new_benefit)
        db.session.commit()
        return jsonify({'success': True, 'id': new_benefit.id})
    
    elif request.method == 'PUT':
        # Obsługujemy zarówno JSON jak i FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            # Konwertujemy checkbox na boolean
            data['is_active'] = 'is_active' in request.form
        
        benefit = BenefitItem.query.get(data['id'])
        if benefit:
            benefit.title = data['title']
            benefit.description = data['description']
            benefit.icon = data.get('icon', '')
            benefit.image = data.get('image', '')
            benefit.order = data.get('order', 0)
            benefit.is_active = data.get('is_active', True)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Benefit not found'}), 404
    
    elif request.method == 'DELETE':
        benefit_id = request.args.get('id', type=int)
        benefit = BenefitItem.query.get(benefit_id)
        if benefit:
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
            # Konwertujemy checkbox na boolean
            data['is_active'] = 'is_active' in request.form
        
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
            # Konwertujemy checkbox na boolean
            data['is_active'] = 'is_active' in request.form
        
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
            # Konwertujemy checkbox na boolean
            data['is_active'] = 'is_active' in request.form
        
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
            # Konwertujemy checkbox na boolean
            data['is_active'] = 'is_active' in request.form
        
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
            # Konwertujemy checkbox na boolean
            data['is_active'] = 'is_active' in request.form
        
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

@app.route('/admin/api/presentation-schedule', methods=['GET', 'POST', 'PUT'])
@login_required
def api_presentation_schedule():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        schedule = PresentationSchedule.query.first()
        if schedule:
            return jsonify({
                'id': schedule.id,
                'title': schedule.title,
                'next_presentation_date': schedule.next_presentation_date.isoformat() if schedule.next_presentation_date else None,
                'custom_text': schedule.custom_text,
                'is_active': schedule.is_active
            })
        return jsonify({'error': 'No schedule found'}), 404
    
    elif request.method == 'POST':
        # Obsługujemy zarówno JSON jak i FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            # Konwertujemy checkbox na boolean
            data['is_active'] = 'is_active' in request.form
        
        # Konwertujemy string daty na datetime
        from datetime import datetime
        presentation_date = datetime.fromisoformat(data['next_presentation_date'].replace('Z', '+00:00'))
        
        new_schedule = PresentationSchedule(
            title=data.get('title', 'Następna sesja'),
            next_presentation_date=presentation_date,
            custom_text=data.get('custom_text', ''),
            is_active=data.get('is_active', True)
        )
        db.session.add(new_schedule)
        db.session.commit()
        return jsonify({'success': True, 'id': new_schedule.id})
    
    elif request.method == 'PUT':
        # Obsługujemy zarówno JSON jak i FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            # Konwertujemy checkbox na boolean
            data['is_active'] = 'is_active' in request.form
        
        schedule = PresentationSchedule.query.get(data['id'])
        if schedule:
            schedule.title = data.get('title', 'Następna sesja')
            # Konwertujemy string daty na datetime
            from datetime import datetime
            presentation_date = datetime.fromisoformat(data['next_presentation_date'].replace('Z', '+00:00'))
            schedule.next_presentation_date = presentation_date
            schedule.custom_text = data.get('custom_text', '')
            schedule.is_active = data.get('is_active', True)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Schedule not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
