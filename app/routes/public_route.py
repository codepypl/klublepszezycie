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
from app.models import db, EventSchedule, User, UserGroup
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
    """User registration - JSON API with new user management logic"""
    try:
        # Only accept JSON data
        if not request.is_json:
            return jsonify({'success': False, 'message': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        
        # Validate input
        if not data.get('first_name') or not data.get('email'):
            return jsonify({'success': False, 'message': 'Imię i email są wymagane'}), 400
        
        if not validate_email(data['email']):
            return jsonify({'success': False, 'message': 'Nieprawidłowy format email'}), 400
        
        if data.get('phone') and not validate_phone(data['phone']):
            return jsonify({'success': False, 'message': 'Nieprawidłowy format telefonu'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        
        if existing_user:
            # User exists - check their status
            if existing_user.club_member:
                # User is already club member
                return jsonify({'success': True, 'message': 'Witamy z powrotem! Jesteś już członkiem klubu'})
            else:
                # User exists but is not club member - convert to club member
                existing_user.club_member = True
                existing_user.account_type = 'club_member'
                db.session.commit()
                print(f"✅ Converted existing user to club member: {existing_user.email}")
        else:
            # Create new club member user
            from werkzeug.security import generate_password_hash
            import uuid
            
            # Generate temporary password
            temp_password = str(uuid.uuid4())[:8]
            
            user = User(
                first_name=data['first_name'],
                email=data['email'],
                phone=data.get('phone', ''),
                password_hash=generate_password_hash(temp_password),
                is_active=True,
                is_temporary_password=True,
                club_member=True,
                account_type='club_member',
                role='user'
            )
            
            try:
                db.session.add(user)
                db.session.commit()
                print(f"✅ Created new club member: {user.email}")
            except Exception as e:
                db.session.rollback()
                # Check if it's a duplicate key error
                if 'duplicate key' in str(e) or 'UNIQUE constraint' in str(e):
                    # User was created by another process, try to get it
                    existing_user = User.query.filter_by(email=data['email']).first()
                    if existing_user:
                        if not existing_user.club_member:
                            existing_user.club_member = True
                            existing_user.account_type = 'club_member'
                            db.session.commit()
                        return jsonify({'success': True, 'message': 'Witamy z powrotem! Zostałeś dodany do klubu'})
                # Re-raise the exception if it's not a duplicate key error
                raise e
        
        # Add user to system groups
        from app.services.group_manager import GroupManager
        group_manager = GroupManager()
        
        # Get the user (either existing or newly created)
        if existing_user:
            user = existing_user
        
        # Add to all users group
        success, message = group_manager.add_user_to_all_users(user.id)
        if success:
            print(f"✅ Dodano użytkownika {user.email} do grupy wszystkich użytkowników")
        else:
            print(f"❌ Błąd dodawania do grupy wszystkich użytkowników: {message}")
        
        # Add to club members group
        success, message = group_manager.add_user_to_club_members(user.id)
        if success:
            print(f"✅ Dodano użytkownika {user.email} do grupy członków klubu")
        else:
            print(f"❌ Błąd dodawania do grupy członków klubu: {message}")
        
        # Synchronize all groups to ensure consistency
        try:
            # Sync club members group
            success, message = group_manager.sync_club_members_group()
            if success:
                print(f"✅ Zsynchronizowano grupę członków klubu po utworzeniu użytkownika")
            else:
                print(f"❌ Błąd synchronizacji grupy członków klubu: {message}")
            
            # Sync event groups
            success, message = group_manager.sync_event_groups()
            if success:
                print(f"✅ Zsynchronizowano grupy wydarzeń po utworzeniu użytkownika")
            else:
                print(f"❌ Błąd synchronizacji grup wydarzeń: {message}")
        except Exception as sync_error:
            print(f"❌ Błąd synchronizacji grup po utworzeniu użytkownika: {str(sync_error)}")
        
        # Send welcome email with temporary password (only for new users)
        if not existing_user:
            try:
                email_service = EmailService()
                
                # Generate unsubscribe and delete account URLs
                unsubscribe_token = generate_unsubscribe_token(user.email, 'unsubscribe')
                delete_token = generate_unsubscribe_token(user.email, 'delete_account')
                
                context = {
                    'user_name': user.first_name,
                    'user_email': user.email,
                    'temporary_password': temp_password,
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
        
        # Get registration count - count users registered for this event
        registration_count = User.query.filter_by(
            event_id=event_id,
            account_type='event_registration'
        ).count()
        
        # Check if user is already registered (if email provided)
        user_email = request.args.get('email')
        is_registered = False
        if user_email:
            existing_user = User.query.filter_by(
                event_id=event_id,
                email=user_email,
                account_type='event_registration'
            ).first()
            is_registered = existing_user is not None
        
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
        existing_user = User.query.filter_by(
            event_id=event_id,
            email=email,
            account_type='event_registration'
        ).first()
        
        if existing_user:
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
    """Register for event with new user management logic"""
    try:
        data = request.get_json()
        print(f"🔍 Event registration data: {data}")
        
        # Check if data is valid JSON
        if not data:
            print("❌ No data received")
            return jsonify({'success': False, 'message': 'Nieprawidłowe dane JSON'}), 400
        
        # Validate input
        print(f"🔍 Validating data: first_name='{data.get('first_name')}', email='{data.get('email')}', phone='{data.get('phone')}'")
        
        if not data.get('first_name') or not data.get('email'):
            print(f"❌ Missing required fields: first_name={data.get('first_name')}, email={data.get('email')}")
            return jsonify({'success': False, 'message': 'Imię i email są wymagane'}), 400
        
        email_valid = validate_email(data['email'])
        print(f"🔍 Email validation result: {email_valid}")
        if not email_valid:
            print(f"❌ Invalid email format: {data['email']}")
            return jsonify({'success': False, 'message': 'Nieprawidłowy format email'}), 400
        
        if data.get('phone'):
            phone_valid = validate_phone(data['phone'])
            print(f"🔍 Phone validation result: {phone_valid} for phone: '{data['phone']}'")
            if not phone_valid:
                print(f"❌ Invalid phone format: {data['phone']}")
                return jsonify({'success': False, 'message': 'Nieprawidłowy format telefonu'}), 400
        else:
            print("🔍 No phone provided, skipping phone validation")
        
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
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        
        if existing_user:
            # User exists - check their status
            if existing_user.club_member:
                # User is club member - they don't need to register
                return jsonify({
                    'success': False, 
                    'message': 'Ten adres e-mail jest używany przez jednego z członków klubu, nie musisz rejestrować się na wydarzenie, ponieważ wszyscy członkowie klubu są automatycznie zapisani na każde wydarzenie.'
                }), 400
            else:
                # User exists but is not club member - allow registration
                print(f"🔍 Existing user found: {existing_user.email}, club_member: {existing_user.club_member}")
        else:
            # User doesn't exist - will be created during registration
            pass
        
        # Check max participants - count users registered for this event
        if event.max_participants:
            current_registrations = User.query.filter_by(
                event_id=event_id,
                account_type='event_registration'
            ).count()
            if current_registrations >= event.max_participants:
                return jsonify({'success': False, 'message': 'Brak wolnych miejsc na to wydarzenie'}), 400
        
        # Use database transaction with proper locking to prevent race conditions
        try:
            # Check if user is already registered for this event (with row-level locking)
            existing_event_user = User.query.filter_by(
                event_id=event_id,
                email=data['email'],
                account_type='event_registration'
            ).with_for_update().first()
            
            if existing_event_user:
                print(f"❌ User already registered for this event: {data['email']}")
                return jsonify({'success': False, 'message': 'Jesteś już zarejestrowany na to wydarzenie'}), 400
            
            # Double-check max participants after locking
            if event.max_participants:
                current_registrations = User.query.filter_by(
                    event_id=event_id,
                    account_type='event_registration'
                ).count()
                if current_registrations >= event.max_participants:
                    print(f"❌ Event full: {current_registrations}/{event.max_participants}")
                    return jsonify({'success': False, 'message': 'Brak wolnych miejsc na to wydarzenie'}), 400
            
            # Create user account for event registration
            if not existing_user:
                from app.blueprints.users_controller import UsersController
                user_result = UsersController.create_event_registration_user(
                    first_name=data['first_name'],
                    email=data['email'],
                    phone=data.get('phone', ''),
                    event_id=event_id,
                    group_id=None  # Will be set after group creation
                )
                
                if not user_result['success']:
                    print(f"❌ Failed to create user: {user_result['error']}")
                    db.session.rollback()
                    return jsonify({'success': False, 'message': 'Błąd podczas tworzenia konta użytkownika. Spróbuj ponownie.'}), 500
                else:
                    print(f"✅ User created for event registration: {data['email']}")
                    created_user = user_result['user']
            else:
                # Update existing user to register for this event
                existing_user.account_type = 'event_registration'
                existing_user.event_id = event_id
                existing_user.group_id = None  # Will be set after group creation
                created_user = existing_user
            
            # Get or create event group
            from app.services.group_manager import GroupManager
            group_manager = GroupManager()
            
            # Get event group
            event_group = UserGroup.query.filter_by(group_type='event_based', event_id=event_id).first()
            if not event_group:
                # Create event group if it doesn't exist
                event_group = UserGroup(
                    name=f"Wydarzenie: {event.title}",
                    description=f"Grupa uczestników wydarzenia: {event.title}",
                    group_type='event_based',
                    event_id=event_id
                )
                db.session.add(event_group)
                db.session.commit()
            
            # Update user's group_id
            created_user.group_id = event_group.id
            db.session.commit()
            
            # Synchronize event group
            print(f"🔍 Starting event group synchronization for event {event_id}")
            success, message = group_manager.async_sync_event_group(event_id)
            if success:
                print(f"✅ Event group synchronized: {event.title}")
            else:
                print(f"❌ Event group synchronization error: {message}")
            
            # Send confirmation email
            email_service = EmailService()
            
            # Generate unsubscribe and delete account URLs
            unsubscribe_token = generate_unsubscribe_token(created_user.email, 'unsubscribe')
            delete_token = generate_unsubscribe_token(created_user.email, 'delete_account')
            
            context = {
                'user_name': created_user.first_name,
                'event_title': event.title,
                'event_date': event.event_date.strftime('%d.%m.%Y') if event.event_date else '',
                'event_time': event.event_date.strftime('%H:%M') if event.event_date else '',
                'event_location': event.location or 'Online',
                'event_description': event.description or '',
                'unsubscribe_url': request.url_root + f'api/unsubscribe/{created_user.email}/{unsubscribe_token}',
                'delete_account_url': request.url_root + f'api/delete-account/{created_user.email}/{delete_token}'
            }
            
            success, message = email_service.send_template_email(
                to_email=created_user.email,
                template_name='event_registration_confirmation',
                context=context
            )
            
            if success:
                print(f"✅ Confirmation email sent to {created_user.email}")
            else:
                print(f"❌ Failed to send confirmation email: {message}")
            
            # Call register_for_event to complete the registration process
            # This will add user to group and send confirmation email
            return register_for_event(created_user, event_id)
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Database error during registration: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': 'Błąd podczas rejestracji. Spróbuj ponownie.'}), 500
        
    except Exception as e:
        print(f"❌ Unexpected error in register_event: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Wystąpił nieoczekiwany błąd. Spróbuj ponownie.'}), 500

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

@public_bp.route('/api/unsubscribe/<email>/<token>')
def unsubscribe_api(email, token):
    """API endpoint for unsubscribe from newsletter"""
    try:
        result = PublicController.unsubscribe_from_newsletter(email, token)
        
        if result['success']:
            return render_template('email/unsubscribe_success.html', 
                                 message=result['message'])
        else:
            return render_template('email/unsubscribe_error.html', 
                                 error=result['error'])
    except Exception as e:
        return render_template('email/unsubscribe_error.html', 
                             error=f'Wystąpił błąd: {str(e)}')

@public_bp.route('/api/delete-account/<email>/<token>')
def delete_account_api(email, token):
    """API endpoint for delete account"""
    try:
        result = PublicController.delete_user_account(email, token)
        
        if result['success']:
            return render_template('email/delete_account_success.html', 
                                 message=result['message'])
        else:
            return render_template('email/delete_account_error.html', 
                                 error=result['error'])
    except Exception as e:
        return render_template('email/delete_account_error.html', 
                             error=f'Wystąpił błąd: {str(e)}')

def register_for_event(user, event_id):
    """Register existing user for a specific event"""
    try:
        from app.models import EventSchedule, UserHistory, UserLogs, Stats
        
        # Check if event exists and is active
        event = EventSchedule.query.filter_by(
            id=event_id, 
            is_active=True, 
            is_published=True
        ).first()
        
        if not event:
            return jsonify({'success': False, 'message': 'Wydarzenie nie zostało znalezione lub nie jest dostępne'}), 404
        
        # Check if user is already registered for this event (but only if they weren't just created)
        # If user already has event_id and account_type set, they were just registered in register_event
        if user.event_id == event_id and user.account_type == 'event_registration':
            print(f"✅ User {user.email} was just registered for event {event_id}, proceeding with group assignment and email")
        else:
            # Check if user is already registered for this event from previous registration
            existing_registration = User.query.filter_by(
                id=user.id, 
                event_id=event_id,
                account_type='event_registration'
            ).first()
            
            if existing_registration:
                return jsonify({'success': False, 'message': 'Jesteś już zarejestrowany na to wydarzenie'}), 400
        
        # Update user to register for event
        user.account_type = 'event_registration'
        user.event_id = event_id
        
        # Log the registration in UserHistory (event participation history)
        UserHistory.log_event_registration(
            user_id=user.id,
            event_id=event_id,
            was_club_member=user.club_member or False
        )
        
        # Log the action in UserLogs (user activity logs)
        try:
            from flask import request
            ip_address = request.remote_addr if request else None
            user_agent = request.headers.get('User-Agent') if request else None
        except:
            ip_address = None
            user_agent = None
            
        UserLogs.log_event_registration(
            user_id=user.id,
            event_id=event_id,
            event_title=event.title,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Update stats
        Stats.increment('event_registrations', related_id=event_id, related_type='event')
        Stats.increment('total_registrations')
        
        # Add user to event group and synchronize all groups
        from app.services.group_manager import GroupManager
        group_manager = GroupManager()
        
        # Add user to specific event group
        success, message = group_manager.add_user_to_event_group(user.id, event_id)
        if success:
            print(f"✅ Dodano użytkownika {user.email} do grupy wydarzenia: {event.title}")
        else:
            print(f"❌ Błąd dodawania do grupy wydarzenia: {message}")
        
        # Synchronize all groups to ensure consistency
        try:
            # Sync club members group (in case user became club member)
            success, message = group_manager.sync_club_members_group()
            if success:
                print(f"✅ Zsynchronizowano grupę członków klubu po rejestracji na wydarzenie")
            else:
                print(f"❌ Błąd synchronizacji grupy członków klubu: {message}")
            
            # Sync event groups
            success, message = group_manager.sync_event_groups()
            if success:
                print(f"✅ Zsynchronizowano grupy wydarzeń po rejestracji")
            else:
                print(f"❌ Błąd synchronizacji grup wydarzeń: {message}")
        except Exception as sync_error:
            print(f"❌ Błąd synchronizacji grup po rejestracji: {str(sync_error)}")
        
        db.session.commit()
        
        # Send confirmation email to user
        try:
            email_service = EmailService()
            
            # Generate unsubscribe token
            unsubscribe_token = generate_unsubscribe_token(user.email, 'unsubscribe')
            
            # Get base URL safely
            try:
                from flask import request
                base_url = request.url_root if request else 'http://localhost:5000/'
            except:
                base_url = 'http://localhost:5000/'
            
            context = {
                'user_name': user.first_name,
                'event_title': event.title,
                'event_date': event.event_date.strftime('%d.%m.%Y') if event.event_date else 'Nie podano',
                'event_time': event.event_date.strftime('%H:%M') if event.event_date else 'Nie podano',
                'event_location': event.location or 'Nie podano',
                'event_description': event.description or '',
                'unsubscribe_url': base_url + f'api/unsubscribe/{user.email}/{unsubscribe_token}'
            }
            
            success, message = email_service.send_template_email(
                to_email=user.email,
                template_name='event_registration',
                context=context
            )
            
            if success:
                print(f"✅ Wysłano email potwierdzenia rejestracji na wydarzenie: {user.email}")
            else:
                print(f"❌ Błąd wysyłania email potwierdzenia: {message}")
                
        except Exception as e:
            print(f"❌ Błąd wysyłania email potwierdzenia: {str(e)}")
        
        # Send admin notification about event registration
        try:
            import os
            admin_email = os.getenv('ADMIN_EMAIL', 'admin@lepszezycie.pl')
            admin_context = {
                'user_name': user.first_name,
                'user_email': user.email,
                'event_title': event.title,
                'event_date': event.event_date.strftime('%d.%m.%Y %H:%M') if event.event_date else 'Nie podano',
                'registration_date': get_local_now().strftime('%d.%m.%Y %H:%M'),
                'registration_source': f'Rejestracja na wydarzenie - {event.title}'
            }
            
            email_service = EmailService()
            email_service.send_template_email(
                to_email=admin_email,
                template_name='admin_notification',
                context=admin_context,
                to_name='Administrator'
            )
        except Exception as e:
            print(f"❌ Błąd wysyłania powiadomienia administratora: {e}")
        
        return jsonify({'success': True, 'message': f'Zostałeś zarejestrowany na wydarzenie: {event.title}. Sprawdź email z potwierdzeniem.'})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Event registration error: {str(e)}")
        return jsonify({'success': False, 'message': f'Błąd rejestracji na wydarzenie: {str(e)}'}), 500
