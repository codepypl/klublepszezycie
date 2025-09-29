"""
Admin routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.blueprints.admin_controller import AdminController

admin_bp = Blueprint('admin', __name__)

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


@admin_bp.route('/celery-monitor')
@login_required
def celery_monitor():
    """Monitor zadań Celery"""
    return render_template('admin/celery_monitor.html')

# API endpoints for Celery monitoring
@admin_bp.route('/api/celery/status')
@login_required
def api_celery_status():
    """API: Status Celery"""
    try:
        from app.services.celery_monitor import CeleryMonitorService
        monitor = CeleryMonitorService()
        status = monitor.get_celery_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/celery/tasks')
@login_required
def api_celery_tasks():
    """API: Lista zadań Celery"""
    try:
        from app.services.celery_monitor import CeleryMonitorService
        monitor = CeleryMonitorService()
        
        # Pobierz parametry filtrowania
        task_type = request.args.get('type', 'all')  # all, scheduled, active, completed
        event_id = request.args.get('event_id')
        limit = int(request.args.get('limit', 50))
        
        tasks = monitor.get_tasks(task_type=task_type, event_id=event_id, limit=limit)
        return jsonify(tasks)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/celery/tasks/<task_id>/cancel', methods=['POST'])
@login_required
def api_cancel_task(task_id):
    """API: Anuluj zadanie Celery"""
    try:
        from app.services.celery_monitor import CeleryMonitorService
        monitor = CeleryMonitorService()
        result = monitor.cancel_task(task_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/api/celery/events/<event_id>/cancel-all', methods=['POST'])
@login_required
def api_cancel_event_tasks(event_id):
    """API: Anuluj wszystkie zadania dla wydarzenia"""
    try:
        from app.services.celery_cleanup import CeleryCleanupService
        cleanup = CeleryCleanupService()
        cancelled_count = cleanup.cancel_event_tasks(int(event_id))
        return jsonify({
            'success': True, 
            'cancelled_count': cancelled_count,
            'message': f'Anulowano {cancelled_count} zadań dla wydarzenia {event_id}'
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
    
    return render_template('admin/crm_settings.html', stats=data['stats'])

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

# CRM Export page
@admin_bp.route('/crm/export')
@login_required
def crm_export():
    """CRM export page"""
    data = AdminController.get_crm_export_data()
    
    if not data['success']:
        flash(f'Błąd podczas ładowania strony eksportu CRM: {data["error"]}', 'error')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/crm_export.html', stats=data['stats'], recent_imports=data['recent_imports'])

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
