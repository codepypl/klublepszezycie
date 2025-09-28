from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.services.log_service import LogService
from app.models.email_model import EmailTemplate, EmailCampaign
from app.models.events_model import EventSchedule
from datetime import datetime

log_route = Blueprint('log_route', __name__)

@log_route.route('/admin/logs')
@login_required
def logs():
    """Strona z logami emaili"""
    try:
        # Get initial stats
        stats = LogService.get_logs_stats()
        
        # Get available templates for filter
        templates = EmailTemplate.query.filter_by(is_active=True).all()
        
        # Get available campaigns for filter
        campaigns = EmailCampaign.query.all()
        
        # Get recent events for filter
        recent_events = EventSchedule.query.order_by(EventSchedule.event_date.desc()).limit(20).all()
        
        return render_template('admin/logs.html', 
                             stats=stats,
                             templates=templates,
                             campaigns=campaigns,
                             recent_events=recent_events)
        
    except Exception as e:
        flash(f'Błąd ładowania logów: {str(e)}', 'error')
        return render_template('admin/logs.html', 
                             stats={},
                             templates=[],
                             campaigns=[],
                             recent_events=[])

@log_route.route('/admin/logs/<int:log_id>')
@login_required
def log_details(log_id):
    """Szczegóły logu emaila"""
    try:
        log_details = LogService.get_log_details(log_id)
        
        if not log_details:
            flash('Log nie został znaleziony', 'error')
            return redirect(url_for('log_route.logs'))
        
        return render_template('admin/log_details.html', log=log_details)
        
    except Exception as e:
        flash(f'Błąd ładowania szczegółów logu: {str(e)}', 'error')
        return redirect(url_for('log_route.logs'))

@log_route.route('/admin/logs/cleanup', methods=['POST'])
@login_required
def cleanup_logs():
    """Czyści stare logi"""
    try:
        success, message, stats = LogService.cleanup_old_logs(hours=48)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        return jsonify({
            'success': success,
            'message': message,
            'stats': stats
        })
        
    except Exception as e:
        flash(f'Błąd czyszczenia logów: {str(e)}', 'error')
        return jsonify({
            'success': False,
            'message': f'Błąd czyszczenia logów: {str(e)}'
        }), 500

@log_route.route('/admin/logs/export')
@login_required
def export_logs():
    """Eksportuje logi do CSV"""
    try:
        import csv
        import io
        from flask import Response
        
        # Get all logs (without pagination for export)
        logs, _ = LogService.get_logs(per_page=10000)
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Email', 'Temat', 'Status', 'Data wysłania', 
            'ID Szablonu', 'Nazwa Szablonu', 'ID Kampanii', 
            'Nazwa Kampanii', 'ID Wydarzenia', 'Nazwa Wydarzenia', 
            'Komunikat błędu'
        ])
        
        # Write data
        for log in logs:
            writer.writerow([
                log['id'],
                log['email'],
                log['subject'],
                log['status'],
                log['sent_at'] or '',
                log['template_id'] or '',
                log['template_name'] or '',
                log['campaign_id'] or '',
                log['campaign_name'] or '',
                log['event_id'] or '',
                log['event_info']['title'] if log['event_info'] else '',
                log['error_message'] or ''
            ])
        
        # Prepare response
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=email_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
        
    except Exception as e:
        flash(f'Błąd eksportu logów: {str(e)}', 'error')
        return redirect(url_for('log_route.logs'))

@log_route.route('/admin/logs/stats/refresh')
@login_required
def refresh_stats():
    """Odświeża statystyki logów"""
    try:
        stats = LogService.get_logs_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
