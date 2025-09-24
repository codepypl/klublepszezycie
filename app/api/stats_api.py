"""
Stats API endpoints
"""
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from app.models import Stats
from app.utils.auth_utils import admin_required_api
import logging

stats_api_bp = Blueprint('stats_api', __name__)

@stats_api_bp.route('/stats/update-all', methods=['POST'])
@login_required
@admin_required_api
def update_all_stats():
    """Update all statistics from database"""
    try:
        results = Stats.update_all_stats()
        
        return jsonify({
            'success': True,
            'message': 'Wszystkie statystyki zostały zaktualizowane',
            'stats': results
        })
    except Exception as e:
        logging.error(f"Error updating all stats: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@stats_api_bp.route('/stats/dashboard', methods=['GET'])
@login_required
@admin_required_api
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        stats = {
            'users': {
                'total': Stats.get_total_users(),
                'active': Stats.get_active_users(),
                'admin': Stats.get_admin_users(),
                'new_30_days': Stats.get_new_users_30_days()
            },
            'events': {
                'total': Stats.get_total_events(),
                'registrations': Stats.get_total_registrations()
            },
            'blog': {
                'posts': Stats.get_total_blog_posts(),
                'categories': Stats.get_total_blog_categories(),
                'comments': Stats.get_total_blog_comments()
            },
            'crm': {
                'contacts': Stats.get_total_contacts(),
                'calls': Stats.get_total_calls(),
                'imports': Stats.get_total_imports(),
                'blacklist': Stats.get_total_blacklist(),
                'daily_calls': Stats.get_daily_calls(),
                'daily_leads': Stats.get_daily_leads()
            },
            'email': {
                'total': Stats.get_total_emails(),
                'pending': Stats.get_pending_emails(),
                'sent': Stats.get_sent_emails(),
                'failed': Stats.get_failed_emails(),
                'logs': Stats.get_total_email_logs(),
                'bounced': Stats.get_bounced_emails()
            },
            'other': {
                'testimonials': Stats.get_total_testimonials()
            }
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logging.error(f"Error getting dashboard stats: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@stats_api_bp.route('/stats/users', methods=['GET'])
@login_required
@admin_required_api
def get_user_stats():
    """Get user statistics"""
    try:
        # Update stats before getting them
        Stats.update_user_stats()
        
        stats = {
            'total': Stats.get_total_users(),
            'active': Stats.get_active_users(),
            'admin': Stats.get_admin_users(),
            'total_registrations': Stats.get_total_registrations()
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logging.error(f"Error getting user stats: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@stats_api_bp.route('/stats/crm', methods=['GET'])
@login_required
@admin_required_api
def get_crm_stats():
    """Get CRM statistics"""
    try:
        stats = {
            'contacts': Stats.get_total_contacts(),
            'calls': Stats.get_total_calls(),
            'imports': Stats.get_total_imports(),
            'blacklist': Stats.get_total_blacklist(),
            'daily_calls': Stats.get_daily_calls(),
            'daily_leads': Stats.get_daily_leads()
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logging.error(f"Error getting CRM stats: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@stats_api_bp.route('/stats/email', methods=['GET'])
@login_required
@admin_required_api
def get_email_stats():
    """Get email statistics"""
    try:
        stats = {
            'total': Stats.get_total_emails(),
            'pending': Stats.get_pending_emails(),
            'sent': Stats.get_sent_emails(),
            'failed': Stats.get_failed_emails(),
            'logs': Stats.get_total_email_logs(),
            'bounced': Stats.get_bounced_emails()
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logging.error(f"Error getting email stats: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
