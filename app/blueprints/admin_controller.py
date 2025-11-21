"""
Admin business logic controller
"""
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, EventSchedule, User, UserGroup, Section, Stats, UserLogs
from app.utils.timezone_utils import get_local_now
from app.utils.auth_utils import admin_required
import json

class AdminController:
    """Admin business logic controller"""
    
    @staticmethod
    def get_dashboard_data():
        """Get dashboard statistics and data"""
        try:
            # Get statistics from central stats table
            total_events = Stats.get_total_events()
            total_registrations = Stats.get_total_registrations()
            total_users = Stats.get_total_users()
            total_testimonials = Stats.get_total_testimonials()
            new_users = Stats.get_new_users_30_days()
            
            # Get recent events
            recent_events = EventSchedule.query.order_by(EventSchedule.created_at.desc()).limit(5).all()
            
            # Get recent registrations - get recent event registration users
            recent_registrations = User.query.filter_by(
                account_type='event_registration'
            ).order_by(User.created_at.desc()).limit(5).all()
            
            # Create stats object
            stats = {
                'total_users': total_users,
                'new_users': new_users,
                'total_testimonials': total_testimonials,
                'total_registrations': total_registrations
            }
            
            return {
                'success': True,
                'stats': stats,
                'recent_events': recent_events,
                'recent_registrations': recent_registrations
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stats': {
                    'total_users': 0,
                    'new_users': 0,
                    'total_testimonials': 0,
                    'total_registrations': 0
                },
                'recent_events': [],
                'recent_registrations': []
            }
    
    # CRM functions removed - CRM module not used
