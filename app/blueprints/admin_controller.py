"""
Admin business logic controller
"""
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, EventSchedule, EventRegistration, User, UserGroup, Section
from app.utils.timezone_utils import get_local_now
from app.utils.auth_utils import admin_required
import json

class AdminController:
    """Admin business logic controller"""
    
    @staticmethod
    def get_dashboard_data():
        """Get dashboard statistics and data"""
        try:
            # Get statistics
            total_events = EventSchedule.query.count()
            total_registrations = EventRegistration.query.count()
            total_users = User.query.count()
            
            # Get testimonials count
            from app.models import Testimonial
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
    
    @staticmethod
    def get_crm_settings_data():
        """Get CRM settings data"""
        try:
            # Get CRM statistics
            from app.models.crm_model import Contact, Call, ImportFile, BlacklistEntry
            
            total_contacts = Contact.query.count()
            total_calls = Call.query.count()
            total_imports = ImportFile.query.count()
            total_blacklist = BlacklistEntry.query.count()
            
            # Get call statistics
            from app.models.crm_model import Call
            from datetime import datetime, timedelta
            
            today = datetime.now().date()
            daily_calls = Call.query.filter(Call.created_at >= today).count()
            daily_leads = Call.query.filter(
                Call.created_at >= today,
                Call.status == 'lead'
            ).count()
            
            stats = {
                'total_contacts': total_contacts,
                'total_calls': total_calls,
                'total_imports': total_imports,
                'total_blacklist': total_blacklist,
                'daily_calls': daily_calls,
                'daily_leads': daily_leads
            }
            
            return {
                'success': True,
                'stats': stats
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stats': {
                    'total_contacts': 0,
                    'total_calls': 0,
                    'total_imports': 0,
                    'total_blacklist': 0,
                    'daily_calls': 0,
                    'daily_leads': 0
                }
            }
    
    @staticmethod
    def clear_crm_data():
        """Clear all CRM data"""
        try:
            from app.models.crm_model import Contact, Call, ImportFile, ImportRecord, BlacklistEntry
            
            # Get counts before deletion
            contacts_count = Contact.query.count()
            calls_count = Call.query.count()
            imports_count = ImportFile.query.count()
            blacklist_count = BlacklistEntry.query.count()
            
            # Delete in correct order (respecting foreign keys)
            Call.query.delete()
            BlacklistEntry.query.delete()
            ImportRecord.query.delete()
            ImportFile.query.delete()
            Contact.query.delete()
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Usunięto wszystkie dane CRM: {contacts_count} kontaktów, {calls_count} połączeń, {imports_count} importów, {blacklist_count} wpisów z czarnej listy'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f'Błąd podczas usuwania danych CRM: {str(e)}'
            }
    
    @staticmethod
    def get_crm_export_data():
        """Get CRM export data"""
        try:
            from app.models.crm_model import Contact, Call, ImportFile, ImportRecord, BlacklistEntry
            
            total_contacts = Contact.query.count()
            total_calls = Call.query.count()
            total_imports = ImportFile.query.count()
            total_blacklist = BlacklistEntry.query.count()
            
            # Get recent imports
            recent_imports = ImportFile.query.order_by(ImportFile.created_at.desc()).limit(5).all()
            
            # Get call outcomes statistics
            from sqlalchemy import func
            call_outcomes = db.session.query(
                Call.status, 
                func.count(Call.id).label('count')
            ).group_by(Call.status).all()
            
            stats = {
                'total_contacts': total_contacts,
                'total_calls': total_calls,
                'total_imports': total_imports,
                'total_blacklist': total_blacklist,
                'call_outcomes': dict(call_outcomes)
            }
            
            return {
                'success': True,
                'stats': stats,
                'recent_imports': recent_imports
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stats': {
                    'total_contacts': 0,
                    'total_calls': 0,
                    'total_imports': 0,
                    'total_blacklist': 0,
                    'call_outcomes': {}
                },
                'recent_imports': []
            }
    
    @staticmethod
    def get_crm_analysis_data(page=1, per_page=20, search=''):
        """Get CRM analysis data"""
        try:
            from app.models.crm_model import Contact, Call
            from sqlalchemy import func, desc
            from datetime import datetime
            
            # Build query
            query = Contact.query
            
            if search:
                query = query.filter(
                    Contact.name.ilike(f'%{search}%') |
                    Contact.phone.ilike(f'%{search}%') |
                    Contact.email.ilike(f'%{search}%')
                )
            
            # Get contacts with pagination
            contacts = query.order_by(Contact.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            # For each contact, get call history and analysis
            contact_analyses = []
            for contact in contacts.items:
                calls = Call.query.filter_by(contact_id=contact.id).order_by(Call.call_date.desc()).all()
                
                # Determine why contact is shown to agent
                why_shown = "Nie wyświetlany"
                if contact.is_blacklisted:
                    why_shown = "Czarna lista"
                elif contact.call_attempts >= contact.max_call_attempts:
                    why_shown = "Osiągnięto limit prób"
                elif calls:
                    last_call = calls[0]
                    if last_call.status == 'callback' and last_call.next_call_date and last_call.next_call_date <= datetime.now():
                        why_shown = f"Oddzwonienie (zaplanowane na {last_call.next_call_date.strftime('%d.%m.%Y %H:%M')})"
                    elif last_call.status in ['no_answer', 'busy', 'wrong_number']:
                        why_shown = f"Potencjał (ostatni status: {last_call.status})"
                    elif last_call.status in ['lead', 'rejection']:
                        why_shown = f"Zamknięty (status: {last_call.status})"
                else:
                    why_shown = "Nowy kontakt"
                
                contact_analyses.append({
                    'contact': contact,
                    'calls': calls,
                    'why_shown': why_shown
                })
            
            return {
                'success': True,
                'contacts': contacts,
                'contact_analyses': contact_analyses,
                'search': search
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'contacts': None,
                'contact_analyses': [],
                'search': search
            }
