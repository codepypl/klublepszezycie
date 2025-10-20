"""
Admin routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.blueprints.admin_controller import AdminController

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin dashboard
@admin_bp.route('/')
@login_required
def dashboard():
    """Admin dashboard"""
    data = AdminController.get_dashboard_data()
    
    if not data['success']:
        flash(f'Błąd podczas ładowania dashboardu: {data["error"]}', 'error')
    
    return render_template('admin/dashboard.html',
        stats=data['stats'],
        recent_events=data['recent_events'],
        recent_registrations=data['recent_registrations']
    )

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
    from app.config.config import get_config
    config = get_config()
    return render_template('admin/email_campaigns.html', config=config)

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

@admin_bp.route('/email-logs')
@login_required
def email_logs():
    """Logi emaili"""
    from app.services.log_service import LogService
    
    # Get initial stats
    stats = LogService.get_logs_stats()
    
    return render_template('admin/email_logs.html', stats=stats)


@admin_bp.route('/email-monitor')
@login_required
def email_monitor():
    """Monitor systemu emaili"""
    return render_template('admin/email_monitor.html')

# API endpoints for email monitoring
@admin_bp.route('/api/email/queue-stats')
@login_required
def api_email_queue_stats():
    """API: Statystyki kolejki emaili"""
    try:
        # Test database connection first
        from app import db
        from app.models import EmailQueue
        
        # Simple test query
        test_count = EmailQueue.query.count()
        print(f"DEBUG: Database connection test - EmailQueue count: {test_count}")
        
        # Test if we can access the database session
        from sqlalchemy import text
        result = db.session.execute(text('SELECT 1')).scalar()
        print(f"DEBUG: Database session test passed, result: {result}")
        
        # Test direct query
        direct_stats = {
            'total': EmailQueue.query.count(),
            'pending': EmailQueue.query.filter_by(status='pending').count(),
            'failed': EmailQueue.query.filter_by(status='failed').count(),
            'processing': EmailQueue.query.filter_by(status='processing').count(),
            'sent': EmailQueue.query.filter_by(status='sent').count()
        }
        print(f"DEBUG: Direct query stats: {direct_stats}")
        
        # Try EmailManager first
        try:
            from app.services.email_v2 import EmailManager
            email_manager = EmailManager()
            stats = email_manager.get_stats()
            print(f"DEBUG: EmailManager stats: {stats}")  # Debug log
            return jsonify({'success': True, 'stats': stats})
        except Exception as em_error:
            print(f"DEBUG: EmailManager failed, using direct query: {em_error}")
            # Fallback to direct query
            return jsonify({'success': True, 'stats': direct_stats})
    except Exception as e:
        print(f"DEBUG: Error in api_email_queue_stats: {e}")  # Debug log
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/email/process-queue', methods=['POST'])
@login_required
def api_process_email_queue():
    """API: Przetwórz kolejkę emaili"""
    try:
        from app.services.email_v2 import EmailManager
        email_manager = EmailManager()
        
        # Get limit from JSON or form data
        limit = 50  # default
        if request.is_json and request.json:
            limit = request.json.get('limit', 50)
        elif request.form:
            limit = int(request.form.get('limit', 50))
        elif request.args:
            limit = int(request.args.get('limit', 50))
        stats = email_manager.process_queue(limit=limit)
        
        return jsonify({
            'success': True,
            'stats': stats,
            'message': f'Przetworzono {stats.get("processed", 0)} emaili'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/email/retry-failed', methods=['POST'])
@login_required
def api_retry_failed_emails():
    """API: Ponów nieudane emaile"""
    try:
        from app.services.email_v2.queue.processor import EmailQueueProcessor
        processor = EmailQueueProcessor()
        
        # Get limit from JSON or form data
        limit = 10  # default
        if request.is_json and request.json:
            limit = request.json.get('limit', 10)
        elif request.form:
            limit = int(request.form.get('limit', 10))
        elif request.args:
            limit = int(request.args.get('limit', 10))
        stats = processor.retry_failed_emails(limit=limit)
        
        return jsonify({
            'success': True,
            'stats': stats,
            'message': f'Ponowiono {stats.get("retried", 0)} emaili'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/email/cleanup', methods=['POST'])
@login_required
def api_cleanup_emails():
    """API: Wyczyść stare emaile"""
    try:
        from app.services.email_v2.queue.processor import EmailQueueProcessor
        processor = EmailQueueProcessor()
        
        # Get days from JSON or form data
        days = 30  # default
        if request.is_json and request.json:
            days = request.json.get('days', 30)
        elif request.form:
            days = int(request.form.get('days', 30))
        elif request.args:
            days = int(request.args.get('days', 30))
        stats = processor.cleanup_old_emails(days=days)
        
        return jsonify({
            'success': True,
            'stats': stats,
            'message': f'Usunięto {stats.get("total_deleted", 0)} starych emaili'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Content Management Routes
@admin_bp.route('/menu')
@login_required
def menu():
    """Menu management page"""
    from app.models import MenuItem
    menu_items = MenuItem.query.order_by(MenuItem.order.asc()).all()
    return render_template('admin/menu.html', menu_items=menu_items)

@admin_bp.route('/sections')
@login_required
def sections():
    """Sections management page"""
    from app.models import Section
    sections = Section.query.order_by(Section.order.asc()).all()
    return render_template('admin/sections.html', sections=sections)


@admin_bp.route('/benefits')
@login_required
def benefits():
    """Benefits management page"""
    from app.models import BenefitItem
    benefits = BenefitItem.query.order_by(BenefitItem.order.asc()).all()
    return render_template('admin/benefits.html', benefits=benefits)

# Benefits API
@admin_bp.route('/testimonials')
@login_required
def testimonials():
    """Testimonials management page"""
    from app.models import Testimonial
    testimonials = Testimonial.query.order_by(Testimonial.order.asc()).all()
    return render_template('admin/testimonials.html', testimonials=testimonials)

@admin_bp.route('/faq')
@login_required
def faq():
    """FAQ management page"""
    from app.models import FAQ
    faqs = FAQ.query.order_by(FAQ.order.asc()).all()
    return render_template('admin/faq.html', faqs=faqs)


# SEO and Social Media routes are now handled by separate blueprints
# @admin_bp.route('/seo') - handled by seo_bp
# @admin_bp.route('/social') - handled by social_bp

# User Groups API

# Email system removed - will be redesigned from scratch

# Email campaigns removed - will be redesigned from scratch

# CRM Settings page
@admin_bp.route('/crm/settings')
@login_required
def crm_settings():
    """CRM settings page"""
    data = AdminController.get_crm_settings_data()
    
    if not data['success']:
        flash(f'Błąd podczas ładowania ustawień CRM: {data["error"]}', 'error')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/crm_settings.html')

# Clear all CRM data
@admin_bp.route('/crm/clear-all', methods=['POST'])
@login_required
def crm_clear_all():
    """Clear all CRM data"""
    result = AdminController.clear_crm_data()
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('admin.crm_settings'))

# CRM Analysis page

@admin_bp.route('/crm/analysis')
@login_required
def crm_analysis():
    """CRM analysis page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    data = AdminController.get_crm_analysis_data(page=page, search=search)
    
    if not data['success']:
        flash(f'Błąd podczas ładowania analizy CRM: {data["error"]}', 'error')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/crm_analysis.html', 
                         contacts=data['contacts'], 
                         contact_analyses=data['contact_analyses'],
                         search=data['search'])

# CRM Campaigns page
@admin_bp.route('/crm/campaigns')
@login_required
def crm_campaigns():
    """CRM campaigns management page"""
    return render_template('admin/crm/campaigns.html')

# CRM Blacklist page
@admin_bp.route('/crm/blacklist')
@login_required
def crm_blacklist():
    """CRM blacklist management page"""
    return render_template('admin/crm/blacklist.html')

