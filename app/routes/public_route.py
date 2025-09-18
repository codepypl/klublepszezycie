"""
Public routes
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_from_directory
from app.blueprints.public_controller import PublicController, generate_unsubscribe_token
from app.api.email_api import add_user_to_event_group
from app.services.email_service import EmailService
from app.utils.timezone_utils import get_local_now, convert_to_local
from app.utils.blog_utils import generate_blog_link
from app.utils.validation_utils import validate_email, validate_phone
from app.models import db, EventSchedule, User, EventRegistration
import logging
from datetime import datetime

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def index():
    """Home page - fully dynamic based on database"""
    try:
        # Get upcoming and current events
        now = get_local_now()
        now_naive = now.replace(tzinfo=None)
        
        # Get events that are upcoming or currently happening
        upcoming_events = EventSchedule.query.filter(
            EventSchedule.is_active == True,
            EventSchedule.is_published == True,
            EventSchedule.is_archived == False  # Exclude archived events
        ).filter(
            # Include events that haven't ended yet (either no end_date or end_date is in future)
            (EventSchedule.end_date.is_(None)) | (EventSchedule.end_date >= now_naive)
        ).order_by(EventSchedule.event_date.asc()).limit(6).all()
        
        # Convert event dates to local timezone for display
        for event in upcoming_events:
            if event.event_date:
                event.event_date_local = convert_to_local(event.event_date)
        
        # Get next event for registration form
        next_event = upcoming_events[0] if upcoming_events else None
        
        # Determine event status
        event_status = 'upcoming'
        if next_event:
            event_start = next_event.event_date
            event_end = next_event.end_date
            
            if event_start and event_end:
                # Event has both start and end time
                if now_naive >= event_start and now_naive <= event_end:
                    event_status = 'current'  # Event is currently happening
                elif now_naive < event_start:
                    event_status = 'upcoming'  # Event is in the future
                else:
                    event_status = 'past'  # Event has ended
            elif event_start:
                # Event has only start time (legacy support)
                if now_naive >= event_start:
                    event_status = 'current'
                else:
                    event_status = 'upcoming'
        
        # Get all database data dynamically
        db_data = PublicController.get_database_data()
        
        return render_template('index.html', 
                             events=upcoming_events, 
                             next_event=next_event, 
                             event_status=event_status,
                             generate_blog_link=generate_blog_link,
                             **db_data)
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error loading homepage: {str(e)}")
        flash(f'Błąd podczas ładowania strony: {str(e)}', 'error')
        
        # Get minimal data from database even in error case
        try:
            db_data = PublicController.get_database_data()
        except:
            db_data = {
                'menu_items': [],
                'sections': [],
                'hero_section': None,
                'benefits_section': None,
                'benefits_items': [],
                'about_section': None,
                'testimonials_section': None,
                'testimonials': [],
                'cta_section': {
                    'title': 'Dołącz do Klubu Lepszego Życia',
                    'subtitle': 'Zarejestruj się na darmową prezentację i odkryj jak zmienić swoje życie na lepsze'
                },
                'faq_section': {
                    'title': 'Często zadawane pytania'
                },
                'social_links': [],
                'faqs': []
            }
        
        return render_template('index.html', 
                             events=[], 
                             next_event=None, 
                             event_status='upcoming',
                             generate_blog_link=generate_blog_link,
                             **db_data)

@public_bp.route('/register', methods=['POST'])
def register():
    """User registration - JSON API"""
    try:
        # Only accept JSON data
        if not request.is_json:
            return jsonify({'success': False, 'message': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        
        # Validate input
        if not data.get('name') or not data.get('email'):
            return jsonify({'success': False, 'message': 'Imię i email są wymagane'}), 400
        
        if not validate_email(data['email']):
            return jsonify({'success': False, 'message': 'Nieprawidłowy format email'}), 400
        
        if data.get('phone') and not validate_phone(data['phone']):
            return jsonify({'success': False, 'message': 'Nieprawidłowy format telefonu'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            # If user exists and event_id is provided, just register for the event
            if data.get('event_id'):
                return register_for_event(existing_user, data['event_id'])
            return jsonify({'success': False, 'message': 'Użytkownik z tym emailem już istnieje'}), 400
        
        # Create new user
        from werkzeug.security import generate_password_hash
        import uuid
        
        # Generate temporary password
        temp_password = str(uuid.uuid4())[:8]
        
        user = User(
            first_name=data['name'],
            email=data['email'],
            phone=data.get('phone', ''),
            password_hash=generate_password_hash(temp_password),  # Use same password
            is_active=True,
            is_temporary_password=True,
            club_member=True  # CTA form always joins the club
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Add user to system groups
        from app.services.group_manager import GroupManager
        group_manager = GroupManager()
        
        # Add to all users group
        success, message = group_manager.add_user_to_all_users(user.id)
        if success:
            print(f"✅ Dodano użytkownika {user.email} do grupy wszystkich użytkowników")
        else:
            print(f"❌ Błąd dodawania do grupy wszystkich użytkowników: {message}")
        
        # Add to club members group if they want club news
        if user.club_member:
            success, message = group_manager.add_user_to_club_members(user.id)
            if success:
                print(f"✅ Dodano użytkownika {user.email} do grupy członków klubu")
            else:
                print(f"❌ Błąd dodawania do grupy członków klubu: {message}")
        
        # Send welcome email with temporary password (optional - don't fail registration if email fails)
        try:
            email_service = EmailService()
            
            # Generate unsubscribe and delete account URLs
            unsubscribe_token = generate_unsubscribe_token(user.email, 'unsubscribe')
            delete_token = generate_unsubscribe_token(user.email, 'delete_account')
            
            context = {
                'user_name': user.first_name,
                'user_email': user.email,
                'temporary_password': temp_password,  # Use same password
                'login_url': request.url_root + 'login',
                'unsubscribe_url': request.url_root + f'api/unsubscribe/{user.email}/{unsubscribe_token}',
                'delete_account_url': request.url_root + f'api/delete-account/{user.email}/{delete_token}'
            }
            
            success, message = email_service.send_template_email(
                to_email=user.email,
                template_name='welcome',  # Use existing welcome template
                context=context
            )
            
            if not success:
                print(f"Failed to send welcome email: {message}")
        except Exception as e:
            print(f"Email service error (registration continues): {e}")
        
        # Note: on_user_joined_club is not called here because this is a new user registration
        # The welcome email with temporary password is already sent above
        
        # Send admin notification
        try:
            import os
            admin_email = os.getenv('ADMIN_EMAIL', 'admin@lepszezycie.pl')
            admin_context = {
                'user_name': user.first_name,
                'user_email': user.email,
                'user_phone': user.phone or 'Nie podano',
                'registration_date': datetime.now().strftime('%d.%m.%Y %H:%M'),
                'registration_source': 'Formularz CTA (sekcja Dołącz do klubu)'
            }
            
            email_service = EmailService()
            success, message = email_service.send_template_email(
                to_email=admin_email,
                template_name='admin_notification',
                context=admin_context,
                to_name='Administrator'
            )
            
            if success:
                print(f"✅ Wysłano powiadomienie administratora o nowym członku: {user.email}")
            else:
                print(f"❌ Błąd wysyłania powiadomienia administratora: {message}")
                
        except Exception as e:
            print(f"Error sending admin notification: {str(e)}")
        
        # If event_id is provided, register for the event
        if data.get('event_id'):
            return register_for_event(user, data['event_id'])
        
        return jsonify({
            'success': True, 
            'message': 'Rejestracja zakończona pomyślnie. Sprawdź email z instrukcjami.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Błąd rejestracji: {str(e)}'}), 500

@public_bp.route('/api/event-status', methods=['GET'])
def api_event_status():
    """Get event status and registration info"""
    try:
        event_id = request.args.get('event_id', type=int)
        if not event_id:
            return jsonify({'error': 'Event ID required'}), 400
        
        event = EventSchedule.query.get(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        # Check if event is still open for registration
        now = get_local_now()
        now_naive = now.replace(tzinfo=None)
        
        # Registration is open only if event hasn't started yet
        is_registration_open = event.event_date and event.event_date > now_naive
        
        # Get registration count
        registration_count = EventRegistration.query.filter_by(event_id=event_id).count()
        
        # Check if user is already registered (if email provided)
        user_email = request.args.get('email')
        is_registered = False
        if user_email:
            existing_registration = EventRegistration.query.filter_by(
                event_id=event_id, 
                email=user_email
            ).first()
            is_registered = existing_registration is not None
        
        return jsonify({
            'event_id': event_id,
            'title': event.title,
            'event_date': event.event_date.isoformat() if event.event_date else None,
            'is_registration_open': is_registration_open,
            'registration_count': registration_count,
            'max_participants': event.max_participants,
            'is_registered': is_registered,
            'location': event.location,
            'description': event.description
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@public_bp.route('/check-registration/<int:event_id>', methods=['POST'])
def check_registration(event_id):
    """Sprawdź czy użytkownik jest już zarejestrowany na wydarzenie"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'message': 'Email jest wymagany'}), 400
        
        # Check if user is already registered
        existing_registration = EventRegistration.query.filter_by(
            event_id=event_id,
            email=email
        ).first()
        
        if existing_registration:
            return jsonify({
                'success': False, 
                'message': 'Jesteś już zarejestrowany na to wydarzenie',
                'is_registered': True
            }), 200
        else:
            return jsonify({
                'success': True,
                'message': 'Można się zarejestrować',
                'is_registered': False
            }), 200
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Błąd sprawdzania rejestracji: {str(e)}'}), 500

@public_bp.route('/register-event/<int:event_id>', methods=['POST'])
def register_event(event_id):
    """Register for event"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('name') or not data.get('email'):
            return jsonify({'success': False, 'message': 'Imię i email są wymagane'}), 400
        
        if not validate_email(data['email']):
            return jsonify({'success': False, 'message': 'Nieprawidłowy format email'}), 400
        
        if data.get('phone') and not validate_phone(data['phone']):
            return jsonify({'success': False, 'message': 'Nieprawidłowy format telefonu'}), 400
        
        # Get event
        event = EventSchedule.query.get(event_id)
        if not event:
            return jsonify({'error': 'Event not found'}), 404
        
        # Check if registration is still open
        now = get_local_now()
        now_naive = now.replace(tzinfo=None)
        
        # Check if event has started
        if event.event_date and event.event_date <= now_naive:
            return jsonify({'success': False, 'message': 'Rejestracja na to wydarzenie jest już zamknięta - wydarzenie się rozpoczęło'}), 400
        
        # Check if event has ended (if end_date is set)
        if event.end_date and event.end_date <= now_naive:
            return jsonify({'success': False, 'message': 'Rejestracja na to wydarzenie jest już zamknięta - wydarzenie się zakończyło'}), 400
        
        # Check if user is already registered
        existing_registration = EventRegistration.query.filter_by(
            event_id=event_id,
            email=data['email']
        ).first()
        
        if existing_registration:
            return jsonify({'success': False, 'message': 'Jesteś już zarejestrowany na to wydarzenie'}), 400
        
        # Check max participants
        if event.max_participants:
            current_registrations = EventRegistration.query.filter_by(event_id=event_id).count()
            if current_registrations >= event.max_participants:
                return jsonify({'success': False, 'message': 'Brak wolnych miejsc na to wydarzenie'}), 400
        
        # Create registration
        registration = EventRegistration(
            event_id=event_id,
            name=data['name'],
            email=data['email'],
            phone=data.get('phone', ''),
            wants_club_news=data.get('wants_club_news', False),
            status='confirmed'  # Automatically confirm registration
        )
        
        db.session.add(registration)
        db.session.commit()
        
        # Add email to event group (regardless of whether user has account)
        from app.services.group_manager import GroupManager
        group_manager = GroupManager()
        
        success, message = group_manager.add_email_to_event_group(
            email=registration.email,
            name=registration.name,
            event_id=event_id
        )
        if success:
            print(f"✅ Dodano {registration.email} do grupy wydarzenia: {event.title}")
        else:
            print(f"❌ Błąd dodawania do grupy wydarzenia: {message}")
        
        # Add user to event group if they have a user account
        user = User.query.filter_by(email=registration.email).first()
        if user:
            success, message = add_user_to_event_group(user.id, event_id)
            if success:
                print(f"✅ Dodano użytkownika {user.email} do grupy wydarzenia: {event.title}")
            else:
                print(f"❌ Błąd dodawania użytkownika do grupy wydarzenia: {message}")
        
        # Create user account if wants_club_news is True
        user_created = False
        if registration.wants_club_news:
            try:
                # Check if user already exists
                existing_user = User.query.filter_by(email=registration.email).first()
                if not existing_user:
                    # Generate temporary password
                    import uuid
                    temp_password = str(uuid.uuid4())[:8]
                    
                    # Create new user
                    from werkzeug.security import generate_password_hash
                    new_user = User(
                        email=registration.email,
                        name=registration.name,
                        password_hash=generate_password_hash(temp_password),
                        is_active=True,
                        is_temporary_password=True,
                        club_member=True
                    )
                    
                    db.session.add(new_user)
                    db.session.commit()
                    user_created = True
                    
                    # Add new user to system groups
                    from app.services.group_manager import GroupManager
                    group_manager = GroupManager()
                    
                    # Add to all users group
                    success, message = group_manager.add_user_to_all_users(new_user.id)
                    if success:
                        print(f"✅ Dodano nowego użytkownika {new_user.email} do grupy wszystkich użytkowników")
                    else:
                        print(f"❌ Błąd dodawania do grupy wszystkich użytkowników: {message}")
                    
                    # Add to club members group
                    success, message = group_manager.add_user_to_club_members(new_user.id)
                    if success:
                        print(f"✅ Dodano nowego użytkownika {new_user.email} do grupy członków klubu")
                    else:
                        print(f"❌ Błąd dodawania do grupy członków klubu: {message}")
                    
                    # Add new user to event group
                    success, message = add_user_to_event_group(new_user.id, event_id)
                    if success:
                        print(f"✅ Dodano nowego użytkownika {new_user.email} do grupy wydarzenia: {event.title}")
                    else:
                        print(f"❌ Błąd dodawania nowego użytkownika do grupy wydarzenia: {message}")
                    
                    # Send welcome email with temporary password
                    # Generate unsubscribe and delete account URLs
                    unsubscribe_token = generate_unsubscribe_token(registration.email, 'unsubscribe')
                    delete_token = generate_unsubscribe_token(registration.email, 'delete_account')
                    
                    welcome_context = {
                        'user_name': registration.name,
                        'user_email': registration.email,
                        'temporary_password': temp_password,
                        'login_url': request.url_root + 'login',
                        'unsubscribe_url': request.url_root + f'api/unsubscribe/{registration.email}/{unsubscribe_token}',
                        'delete_account_url': request.url_root + f'api/delete-account/{registration.email}/{delete_token}'
                    }
                    
                    welcome_success, welcome_message = email_service.send_template_email(
                        to_email=registration.email,
                        template_name='welcome',
                        context=welcome_context
                    )
                    
                    if not welcome_success:
                        print(f"Failed to send welcome email: {welcome_message}")
                    
                    # Note: on_user_registration is not called here because the welcome email 
                    # with temporary password is already sent above
                    
                    # Send admin notification for new club member
                    try:
                        from config import config
                        admin_email = config['development'].ADMIN_EMAIL
                        admin_context = {
                            'user_name': new_user.first_name,
                            'user_email': new_user.email,
                            'user_phone': new_user.phone or 'Nie podano',
                            'registration_date': datetime.now().strftime('%d.%m.%Y %H:%M'),
                            'registration_source': f'Rejestracja na wydarzenie: {event.title}'
                        }
                        
                        email_service = EmailService()
                        success, message = email_service.send_template_email(
                            to_email=admin_email,
                            template_name='admin_notification',
                            context=admin_context,
                            to_name='Administrator'
                        )
                        
                        if success:
                            print(f"✅ Wysłano powiadomienie administratora o nowym członku: {new_user.email}")
                        else:
                            print(f"❌ Błąd wysyłania powiadomienia administratora: {message}")
                            
                    except Exception as e:
                        print(f"Error sending admin notification: {str(e)}")
                        
            except Exception as e:
                print(f"Error creating user account: {str(e)}")
                # Don't fail the registration if user creation fails
        
        # Send confirmation email
        email_service = EmailService()
        
        # Generate unsubscribe and delete account URLs
        unsubscribe_token = generate_unsubscribe_token(registration.email, 'unsubscribe')
        delete_token = generate_unsubscribe_token(registration.email, 'delete_account')
        
        context = {
            'user_name': registration.name,
            'user_email': registration.email,
            'event_title': event.title,  # Fixed: was event_name, should be event_title
            'event_date': event.event_date.strftime('%d.%m.%Y') if event.event_date else '',
            'event_time': event.event_date.strftime('%H:%M') if event.event_date else '',
            'event_location': event.location or 'Online',
            'event_description': event.description or '',
            'unsubscribe_url': request.url_root + f'api/unsubscribe/{registration.email}/{unsubscribe_token}',
            'delete_account_url': request.url_root + f'api/delete-account/{registration.email}/{delete_token}'
        }
        
        success, message = email_service.send_template_email(
            to_email=registration.email,
            template_name='event_registration',
            context=context
        )
        
        if not success:
            print(f"Failed to send confirmation email: {message}")
        
        # Call email automation for event registration
        try:
            from app.services.email_automation import EmailAutomation
            automation = EmailAutomation()
            automation.on_event_registration(registration.id)
        except Exception as e:
            print(f"Error calling event registration automation: {str(e)}")
        
        # Prepare success message
        success_message = 'Rejestracja zakończona pomyślnie. Sprawdź email z potwierdzeniem.'
        if user_created:
            success_message += ' Konto użytkownika zostało utworzone - sprawdź email z danymi logowania.'
        
        return jsonify({
            'success': True,
            'message': success_message
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Błąd rejestracji: {str(e)}'}), 500

@public_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    import os
    from flask import current_app
    
    # Get the absolute path to the static directory
    static_dir = os.path.join(current_app.root_path, '..', 'static')
    
    try:
        # First try uploads directory
        uploads_dir = os.path.join(static_dir, 'uploads')
        return send_from_directory(uploads_dir, filename)
    except FileNotFoundError:
        try:
            # Then try benefits directory with .jpg extension
            benefits_dir = os.path.join(static_dir, 'images', 'benefits')
            return send_from_directory(benefits_dir, filename + '.jpg')
        except FileNotFoundError:
            try:
                # Try benefits directory without extension (in case filename already has .jpg)
                benefits_dir = os.path.join(static_dir, 'images', 'benefits')
                return send_from_directory(benefits_dir, filename)
            except FileNotFoundError:
                # Return a default image if file not found
                hero_dir = os.path.join(static_dir, 'images', 'hero')
                return send_from_directory(hero_dir, 'hero-bg.jpg')

# Legal documents routes
@public_bp.route('/privacy-policy')
def privacy_policy():
    """Public privacy policy page"""
    from app.models import SocialLink
    
    document = LegalDocument.query.filter_by(document_type='privacy_policy', is_active=True).first()
    if not document:
        flash('Polityka prywatności nie jest dostępna', 'error')
        return redirect(url_for('public.index'))
    
    # Get footer data
    footer_settings = FooterSettings.query.first()
    active_social_links = SocialLink.query.filter_by(is_active=True).order_by(SocialLink.order.asc()).all()
    
    return render_template('public/privacy_policy.html', 
                         document=document,
                         footer_settings=footer_settings,
                         active_social_links=active_social_links)

@public_bp.route('/terms')
def terms():
    """Public terms page"""
    from app.models import SocialLink
    
    document = LegalDocument.query.filter_by(document_type='terms', is_active=True).first()
    if not document:
        flash('Regulamin nie jest dostępny', 'error')
        return redirect(url_for('public.index'))
    
    # Get footer data
    footer_settings = FooterSettings.query.first()
    active_social_links = SocialLink.query.filter_by(is_active=True).order_by(SocialLink.order.asc()).all()
    
    return render_template('public/terms.html', 
                         document=document,
                         footer_settings=footer_settings,
                         active_social_links=active_social_links)

def register_for_event(user, event_id):
    """Register existing user for a specific event"""
    try:
        from app.models import EventRegistration, EventSchedule
        
        # Check if event exists and is active
        event = EventSchedule.query.filter_by(
            id=event_id, 
            is_active=True, 
            is_published=True
        ).first()
        
        if not event:
            return jsonify({'success': False, 'message': 'Wydarzenie nie zostało znalezione lub nie jest dostępne'}), 404
        
        # Check if user is already registered for this event
        existing_registration = EventRegistration.query.filter_by(
            user_id=user.id, 
            event_id=event_id
        ).first()
        
        if existing_registration:
            return jsonify({'success': False, 'message': 'Jesteś już zarejestrowany na to wydarzenie'}), 400
        
        # Create event registration
        registration = EventRegistration(
            user_id=user.id,
            event_id=event_id,
            registration_date=get_local_now(),
            status='confirmed'
        )
        
        db.session.add(registration)
        db.session.commit()
        
        # Send admin notification about event registration
        try:
            from config import config
            admin_email = config['development'].ADMIN_EMAIL
            admin_context = {
                'user_name': user.first_name,
                'user_email': user.email,
                'event_title': event.title,
                'event_date': event.event_date.strftime('%d.%m.%Y %H:%M') if event.event_date else 'Nie podano',
                'registration_date': get_local_now().strftime('%d.%m.%Y %H:%M'),
                'registration_source': f'Timeline - {event.title}'
            }
            
            email_service = EmailService()
            email_service.send_template_email(
                to_email=admin_email,
                template_name='admin_notification',
                context=admin_context,
                to_name='Administrator'
            )
        except Exception as e:
            print(f"Error sending admin notification: {e}")
        
        return jsonify({'success': True, 'message': f'Zostałeś zarejestrowany na wydarzenie: {event.title}'})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Event registration error: {str(e)}")
        return jsonify({'success': False, 'message': f'Błąd rejestracji na wydarzenie: {str(e)}'}), 500
