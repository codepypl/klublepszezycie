"""
Admin routes blueprint
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, EventSchedule, EventRegistration, User, UserGroup, EventRecipientGroup, Section
from app.utils.timezone import get_local_now
import json

admin_bp = Blueprint('admin', __name__)

# Admin dashboard
@admin_bp.route('/')
@login_required
def dashboard():
    """Admin dashboard"""
    try:
        # Get statistics
        total_events = EventSchedule.query.count()
        total_registrations = EventRegistration.query.count()
        total_users = User.query.count()
        
        # Get testimonials count
        from models import Testimonial
        total_testimonials = Testimonial.query.count()
        
        # Get new users from last 30 days
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        new_users = User.query.filter(User.created_at >= thirty_days_ago).count()
        
        # Get recent events
        recent_events = EventSchedule.query.order_by(EventSchedule.created_at.desc()).limit(5).all()
        
        # Get recent registrations
        recent_registrations = EventRegistration.query.order_by(
            EventRegistration.created_at.desc()
        ).limit(5).all()
        
        # Create stats object
        stats = {
            'total_users': total_users,
            'new_users': new_users,
            'total_testimonials': total_testimonials,
            'total_registrations': total_registrations
        }
        
        return render_template('admin/dashboard.html',
            stats=stats,
            recent_events=recent_events,
            recent_registrations=recent_registrations
        )
    except Exception as e:
        flash(f'Błąd podczas ładowania dashboardu: {str(e)}', 'error')
        # Create empty stats for error case
        stats = {
            'total_users': 0,
            'new_users': 0,
            'total_testimonials': 0,
            'total_registrations': 0
        }
        return render_template('admin/dashboard.html', stats=stats, recent_events=[], recent_registrations=[])

@admin_bp.route('/email-system')
@login_required
def email_system():
    """System mailingu - przekierowanie do szablonów"""
    return redirect(url_for('admin.email_templates'))

@admin_bp.route('/email-templates')
@login_required
def email_templates():
    """Szablony emaili"""
    return render_template('admin/email_templates.html')

@admin_bp.route('/email-campaigns')
@login_required
def email_campaigns():
    """Kampanie emaili"""
    return render_template('admin/email_campaigns.html')

@admin_bp.route('/email-groups')
@login_required
def email_groups():
    """Grupy użytkowników"""
    return render_template('admin/email_groups.html')

@admin_bp.route('/email-queue')
@login_required
def email_queue():
    """Kolejka emaili"""
    return render_template('admin/email_queue.html')

# Content Management Routes
@admin_bp.route('/menu')
@login_required
def menu():
    """Menu management page"""
    from models import MenuItem
    menu_items = MenuItem.query.order_by(MenuItem.order.asc()).all()
    return render_template('admin/menu.html', menu_items=menu_items)

@admin_bp.route('/sections')
@login_required
def sections():
    """Sections management page"""
    from models import Section
    sections = Section.query.order_by(Section.order.asc()).all()
    return render_template('admin/sections.html', sections=sections)


@admin_bp.route('/benefits')
@login_required
def benefits():
    """Benefits management page"""
    from models import BenefitItem
    benefits = BenefitItem.query.order_by(BenefitItem.order.asc()).all()
    return render_template('admin/benefits.html', benefits=benefits)

# Benefits API
@admin_bp.route('/testimonials')
@login_required
def testimonials():
    """Testimonials management page"""
    from models import Testimonial
    testimonials = Testimonial.query.order_by(Testimonial.order.asc()).all()
    return render_template('admin/testimonials.html', testimonials=testimonials)

@admin_bp.route('/faq')
@login_required
def faq():
    """FAQ management page"""
    from models import FAQ
    faqs = FAQ.query.order_by(FAQ.order.asc()).all()
    return render_template('admin/faq.html', faqs=faqs)


# SEO and Social Media routes are now handled by separate blueprints
# @admin_bp.route('/seo') - handled by seo_bp
# @admin_bp.route('/social') - handled by social_bp

# User Groups API

# Email system removed - will be redesigned from scratch

# Email campaigns removed - will be redesigned from scratch

