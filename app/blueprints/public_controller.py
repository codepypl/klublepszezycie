"""
Public business logic controller
"""
from flask import request, jsonify, flash, redirect, url_for
from app.models import db, EventSchedule, User, Section, MenuItem, FAQ, BenefitItem, Testimonial, SocialLink, FooterSettings, Stats, UserLogs, UserHistory
from app.services.email_service import EmailService
from app.api.email_api import add_user_to_event_group
import os
import hmac
import hashlib
import logging
from datetime import datetime
from app.utils.validation_utils import validate_email, validate_phone, validate_event_date
from app.utils.timezone_utils import get_local_now, convert_to_local
from app.utils.blog_utils import generate_blog_link
import json

class PublicController:
    """Public business logic controller"""
    
    @staticmethod
    def get_database_data():
        """Pobiera wszystkie dane z bazy danych w sposób dynamiczny"""
        try:
            # Check if we have request context
            has_request_context = False
            try:
                has_request_context = request.endpoint is not None
            except RuntimeError:
                has_request_context = False
            
            # Menu items - filter by blog column for blog pages
            # Check if we're on a blog page by looking at the endpoint
            is_blog_page = False
            if has_request_context and request.endpoint:
                is_blog_page = request.endpoint.startswith('blog.')
            
            if is_blog_page:
                # For blog pages, show ONLY items marked for blog (True) OR items for all pages (None)
                menu_items_db = MenuItem.query.filter(
                    MenuItem.is_active == True,
                    (MenuItem.blog == True) | (MenuItem.blog.is_(None))
                ).order_by(MenuItem.order.asc()).all()
            else:
                # For other pages, show items NOT marked for blog (False) OR items for all pages (None)
                menu_items_db = MenuItem.query.filter(
                    MenuItem.is_active == True,
                    (MenuItem.blog == False) | (MenuItem.blog.is_(None))
                ).order_by(MenuItem.order.asc()).all()
            
            menu_items = []
            for item in menu_items_db:
                # Use blog_url if available and we're on blog pages, otherwise use regular url
                if is_blog_page and item.blog_url:
                    url = item.blog_url
                else:
                    url = item.url
                # Check if this menu item should be marked as active
                is_current_page = False
                if has_request_context and request.endpoint:
                    # Check if current endpoint matches this menu item
                    if url and ('/' + request.endpoint.replace('.', '/') in url or 
                               request.endpoint == 'public.index' and url == '/' or
                               request.endpoint == 'blog.index' and 'blog' in url):
                        is_current_page = True
                
                menu_items.append({
                    'title': item.title, 
                    'url': url, 
                    'is_active': item.is_active,
                    'is_current_page': is_current_page
                })
            
            
            # All active sections (for dynamic display)
            sections_db = Section.query.filter_by(is_active=True).order_by(Section.order.asc()).all()
            sections = [
                {
                    'id': section.id, 
                    'name': section.name,
                    'title': section.title,
                    'content': section.content,
                    'order': section.order,
                    'is_active': section.is_active,
                    'enable_pillars': section.enable_pillars,
                    'pillars_data': section.pillars_data,
                    'enable_floating_cards': section.enable_floating_cards,
                    'floating_cards_data': section.floating_cards_data,
                    'final_text': section.final_text,
                    'background_image': section.background_image,
                    'subtitle': section.subtitle,
                    'css_class': section.css_class
                } for section in sections_db
            ]
            
            # FAQ items
            faq_items = FAQ.query.filter_by(is_active=True).order_by(FAQ.order.asc()).all()
            
            # Benefit items
            benefit_items = BenefitItem.query.filter_by(is_active=True).order_by(BenefitItem.order.asc()).all()
            
            # Testimonials
            testimonials = Testimonial.query.filter_by(is_active=True).order_by(Testimonial.order.asc()).all()
            
            # Social links
            social_links = SocialLink.query.filter_by(is_active=True).order_by(SocialLink.order.asc()).all()
            
            # Footer settings from database
            footer_settings = FooterSettings.query.first()
            if not footer_settings:
                footer_settings = FooterSettings()
                db.session.add(footer_settings)
                db.session.commit()
            
            return {
                'success': True,
                'menu_items': menu_items,
                'sections': sections,
                'faqs': faq_items,  # Changed from faq_items to faqs
                'benefits_items': benefit_items,  # Changed from benefit_items to benefits_items
                'testimonials': testimonials,
                'active_social_links': social_links,
                'footer_settings': footer_settings
            }
        except Exception as e:
            logging.error(f"Error getting database data: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'menu_items': [],
                'sections': [],
                'faqs': [],  # Changed from faq_items to faqs
                'benefits_items': [],  # Changed from benefit_items to benefits_items
                'testimonials': [],
                'active_social_links': [],
                'footer_settings': {}
            }
    
    @staticmethod
    def get_homepage_data():
        """Get homepage data"""
        try:
            # Get upcoming events
            now = get_local_now()
            upcoming_events = EventSchedule.query.filter(
                EventSchedule.event_date > now,
                EventSchedule.status == 'active'
            ).order_by(EventSchedule.event_date.asc()).limit(3).all()
            
            # Get recent blog posts
            from app.models import BlogPost
            recent_posts = BlogPost.query.filter_by(
                status='published'
            ).order_by(BlogPost.published_at.desc()).limit(3).all()
            
            return {
                'success': True,
                'upcoming_events': upcoming_events,
                'recent_posts': recent_posts
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'upcoming_events': [],
                'recent_posts': []
            }
    
    @staticmethod
    def register_for_event(event_id, name, email, phone, notes=None):
        """Register user for event"""
        try:
            # Validate input
            if not all([name, email, phone]):
                return {
                    'success': False,
                    'error': 'Wszystkie pola są wymagane'
                }
            
            if not validate_email(email):
                return {
                    'success': False,
                    'error': 'Nieprawidłowy format email'
                }
            
            if not validate_phone(phone):
                return {
                    'success': False,
                    'error': 'Nieprawidłowy format telefonu'
                }
            
            # Get event
            event = EventSchedule.query.get(event_id)
            if not event:
                return {
                    'success': False,
                    'error': 'Wydarzenie nie zostało znalezione'
                }
            
            if event.status != 'active':
                return {
                    'success': False,
                    'error': 'Wydarzenie nie jest aktywne'
                }
            
            # Check if event is full
            current_registrations = User.query.filter_by(
                event_id=event_id,
                account_type='event_registration'
            ).count()
            if event.max_participants and current_registrations >= event.max_participants:
                return {
                    'success': False,
                    'error': 'Wydarzenie jest pełne'
                }
            
            # Check if user already registered
            existing_user = User.query.filter_by(
                event_id=event_id,
                email=email,
                account_type='event_registration'
            ).first()
            
            if existing_user:
                return {
                    'success': False,
                    'error': 'Jesteś już zarejestrowany na to wydarzenie'
                }
            
            # Create or update user for event registration
            user = User.query.filter_by(email=email).first()
            if user:
                # Update existing user
                user.account_type = 'event_registration'
                user.event_id = event_id
            else:
                # Create new user - this would need password generation
                return {
                    'success': False,
                    'error': 'Ta funkcja wymaga utworzenia nowego użytkownika. Użyj nowego systemu rejestracji.'
                }
            
            db.session.commit()
            
            # Log the registration in UserHistory (event participation history)
            UserHistory.log_event_registration(
                user_id=user.id,
                event_id=event_id,
                was_club_member=user.club_member or False
            )
            
            # Log the action in UserLogs (user activity logs)
            UserLogs.log_event_registration(
                user_id=user.id,
                event_id=event_id,
                event_title=event.title
            )
            
            # Update stats
            Stats.increment('event_registrations', related_id=event_id, related_type='event')
            Stats.increment('total_registrations')
            
            # Add user to event group and synchronize all groups
            try:
                from app.services.group_manager import GroupManager
                group_manager = GroupManager()
                
                # Add user to specific event group
                success, message = group_manager.add_user_to_event_group(user.id, event_id)
                if success:
                    logging.info(f"✅ Dodano użytkownika {user.email} do grupy wydarzenia: {event.title}")
                else:
                    logging.warning(f"❌ Błąd dodawania do grupy wydarzenia: {message}")
                
                # Synchronize all groups to ensure consistency
                try:
                    # Sync club members group (in case user became club member)
                    success, message = group_manager.sync_club_members_group()
                    if success:
                        logging.info(f"✅ Zsynchronizowano grupę członków klubu po rejestracji na wydarzenie")
                    else:
                        logging.warning(f"❌ Błąd synchronizacji grupy członków klubu: {message}")
                    
                    # Sync event groups
                    success, message = group_manager.sync_event_groups()
                    if success:
                        logging.info(f"✅ Zsynchronizowano grupy wydarzeń po rejestracji")
                    else:
                        logging.warning(f"❌ Błąd synchronizacji grup wydarzeń: {message}")
                except Exception as sync_error:
                    logging.warning(f"❌ Błąd synchronizacji grup po rejestracji: {str(sync_error)}")
                    
            except Exception as e:
                logging.warning(f"Failed to add user to event group: {str(e)}")
            
            return {
                'success': True,
                'user': user,
                'message': 'Zostałeś zarejestrowany na wydarzenie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def subscribe_to_newsletter(email, name=None):
        """Subscribe to newsletter"""
        try:
            if not email:
                return {
                    'success': False,
                    'error': 'Email jest wymagany'
                }
            
            if not validate_email(email):
                return {
                    'success': False,
                    'error': 'Nieprawidłowy format email'
                }
            
            # Check if user already exists
            user = User.query.filter_by(email=email).first()
            if user:
                # User exists, add to club members group
                from app.models import UserGroup, UserGroupMember
                club_group = UserGroup.query.filter_by(group_type='club_members').first()
                if club_group:
                    existing_member = UserGroupMember.query.filter_by(
                        user_id=user.id, group_id=club_group.id
                    ).first()
                    if not existing_member:
                        member = UserGroupMember(user_id=user.id, group_id=club_group.id)
                        db.session.add(member)
                        db.session.commit()
                
                return {
                    'success': True,
                    'message': 'Zostałeś dodany do listy mailingowej'
                }
            else:
                # Create new user
                user = User(
                    first_name=name or email.split('@')[0],
                    email=email,
                    role='user',
                    is_active=True
                )
                db.session.add(user)
                db.session.flush()
                
                # Add to club members group
                from app.models import UserGroup, UserGroupMember
                club_group = UserGroup.query.filter_by(group_type='club_members').first()
                if club_group:
                    member = UserGroupMember(user_id=user.id, group_id=club_group.id)
                    db.session.add(member)
                
                db.session.commit()
                
                return {
                    'success': True,
                    'message': 'Zostałeś zarejestrowany i dodany do listy mailingowej'
                }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def unsubscribe_from_newsletter(email, token):
        """Unsubscribe from newsletter"""
        try:
            if not verify_unsubscribe_token(email, 'unsubscribe', token):
                return {
                    'success': False,
                    'error': 'Nieprawidłowy lub wygasły token',
                    'error_code': 'SE-ITK-01'
                }
            
            # Find user by email
            user = User.query.filter_by(email=email).first()
            if user:
                # Remove from club members group
                from app.models import UserGroup, UserGroupMember
                club_group = UserGroup.query.filter_by(group_type='club_members').first()
                if club_group:
                    member = UserGroupMember.query.filter_by(
                        user_id=user.id, group_id=club_group.id
                    ).first()
                    if member:
                        db.session.delete(member)
                        db.session.commit()
                        print(f"✅ Usunięto użytkownika {user.email} z grupy członków klubu")
                
                # Asynchronicznie synchronizuj wszystkie grupy wydarzeń
                from app.services.group_manager import GroupManager
                group_manager = GroupManager()
                
                # Synchronizuj wszystkie grupy wydarzeń
                success, message = group_manager.sync_event_groups()
                if success:
                    print(f"✅ Zsynchronizowano wszystkie grupy wydarzeń po wypisaniu użytkownika {user.email}")
                else:
                    print(f"❌ Błąd synchronizacji grup wydarzeń: {message}")
                
                return {
                    'success': True,
                    'message': 'Zostałeś wypisany z listy mailingowej i usunięty z wszystkich grup wydarzeń'
                }
            else:
                return {
                    'success': False,
                    'error': 'Nie udało się wypisać z listy mailingowej',
                    'error_code': 'SE-UNF-01'
                }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'error_code': 'SE-DBE-01'
            }
    
    @staticmethod
    def delete_user_account(email, token):
        """Delete user account"""
        try:
            if not verify_unsubscribe_token(email, 'delete_account', token):
                return {
                    'success': False,
                    'error': 'Nieprawidłowy lub wygasły token',
                    'error_code': 'SE-ITK-01'
                }
            
            # Find user by email
            user = User.query.filter_by(email=email).first()
            if user:
                # Don't allow deleting admin users
                if user.is_admin_role():
                    return {
                        'success': False,
                        'error': 'Nie można usunąć konta administratora',
                        'error_code': 'SE-ADP-01'
                    }
                
                # Remove user from all groups before deleting
                from app.services.group_manager import GroupManager
                group_manager = GroupManager()
                
                # Get all groups where user is a member
                from app.models import UserGroupMember
                user_memberships = UserGroupMember.query.filter_by(
                    user_id=user.id,
                    is_active=True
                ).all()
                
                print(f"🔍 Usuwanie użytkownika {user.email} (ID: {user.id}) z {len(user_memberships)} grup")
                
                # Remove from each group
                for membership in user_memberships:
                    group = membership.group
                    if group:
                        print(f"🔍 Usuwanie z grupy: {group.name}")
                        success, message = group_manager.remove_user_from_group(group.id, user.id)
                        if success:
                            print(f"✅ Usunięto z grupy: {group.name}")
                        else:
                            print(f"❌ Błąd usuwania z grupy {group.name}: {message}")
                
                # Delete user
                db.session.delete(user)
                db.session.commit()
                
                # Synchronizuj wszystkie grupy wydarzeń po usunięciu użytkownika
                success, message = group_manager.sync_event_groups()
                if success:
                    print(f"✅ Zsynchronizowano wszystkie grupy wydarzeń po usunięciu użytkownika {user.email}")
                else:
                    print(f"❌ Błąd synchronizacji grup wydarzeń: {message}")
                
                print(f"✅ Użytkownik {user.email} został usunięty z systemu")
                
                return {
                    'success': True,
                    'message': 'Konto zostało usunięte pomyślnie'
                }
            else:
                return {
                    'success': False,
                    'error': 'Nie udało się usunąć konta',
                    'error_code': 'SE-UNF-01'
                }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'error_code': 'SE-DBE-01'
            }
    
    @staticmethod
    def get_contact_form_data():
        """Get contact form data"""
        try:
            # Get contact information
            contact_info = {
                'email': 'kontakt@klublepszezycie.pl',
                'phone': '+48 123 456 789',
                'address': 'ul. Przykładowa 123, 00-000 Warszawa'
            }
            
            return {
                'success': True,
                'contact_info': contact_info
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'contact_info': {}
            }
    
    @staticmethod
    def send_contact_message(name, email, subject, message):
        """Send contact message"""
        try:
            if not all([name, email, subject, message]):
                return {
                    'success': False,
                    'error': 'Wszystkie pola są wymagane'
                }
            
            if not validate_email(email):
                return {
                    'success': False,
                    'error': 'Nieprawidłowy format email'
                }
            
            # Send email
            email_service = EmailService()
            email_service.send_template_email(
                to_email='kontakt@klublepszezycie.pl',
                template_name='contact_message',
                context={
                    'sender_name': name,
                    'sender_email': email,
                    'subject': subject,
                    'message': message
                },
                to_name='Klub Lepsze Życie'
            )
            
            return {
                'success': True,
                'message': 'Wiadomość została wysłana pomyślnie'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

def generate_unsubscribe_token(email, action):
    """Generate unsubscribe token for email with expiration"""
    try:
        secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')
        import time
        
        # Generate token with current timestamp (30 days from now)
        current_time = int(time.time())
        expiration_timestamp = current_time + (30 * 24 * 60 * 60)  # 30 days from now
        
        # Create message with email, action, and expiration timestamp
        message = f"{email}:{action}:{expiration_timestamp}"
        
        # Generate HMAC-SHA256 token
        token = hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        print(f"🔑 Generated token for {email}:{action} - expires in 30 days")
        print(f"   Token: {token}")
        print(f"   Generated at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))}")
        print(f"   Expires at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expiration_timestamp))}")
        return token
    except Exception as e:
        print(f"❌ Error generating token: {e}")
        return None

def verify_unsubscribe_token(email, action, token):
    """Verify unsubscribe token with proper expiration check"""
    try:
        secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')
        import time
        current_time = int(time.time())
        
        print(f"🔍 Verifying token for {email}:{action}")
        print(f"   Token: {token}")
        print(f"   Current time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))}")
        
        # Check if token was generated within last 30 days
        # We need to check all possible generation timestamps from 30 days ago to now
        for days_ago in range(30):  # Check last 30 days
            for hour in range(24):  # Check all hours in each day
                for minute in range(0, 60, 5):  # Check every 5 minutes
                    # Calculate when the token was generated (days_ago days, hour hours, minute minutes ago)
                    generation_time = current_time - (days_ago * 24 * 60 * 60) - (hour * 60 * 60) - (minute * 60)
                    # Calculate expiration timestamp (30 days from generation time)
                    expiration_timestamp = generation_time + (30 * 24 * 60 * 60)
                
                    message = f"{email}:{action}:{expiration_timestamp}"
                    expected_token = hmac.new(
                        secret_key.encode('utf-8'),
                        message.encode('utf-8'),
                        hashlib.sha256
                    ).hexdigest()
                    
                    if hmac.compare_digest(token, expected_token):
                        # Check if token is still valid (not expired)
                        if expiration_timestamp > current_time:
                            days_remaining = int((expiration_timestamp - current_time) / (24 * 60 * 60))
                            print(f"✅ Valid token for {email}:{action} - expires in {days_remaining} days")
                            print(f"   Generated {days_ago} days, {hour} hours, {minute} minutes ago at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(generation_time))}")
                            print(f"   Expires at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expiration_timestamp))}")
                            return True
                        else:
                            print(f"❌ Expired token for {email}:{action}")
                            print(f"   Generated {days_ago} days, {hour} hours, {minute} minutes ago at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(generation_time))}")
                            print(f"   Expired at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expiration_timestamp))}")
                            return False
            
        # Try old format without timestamp (backward compatibility)
        message = f"{email}:{action}"
        old_token = hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        if hmac.compare_digest(token, old_token):
            print(f"✅ Valid old format token for {email}:{action}")
            return True
            
        print(f"❌ Invalid token for {email}:{action}")
        return False
    except Exception as e:
        print(f"❌ Error verifying token: {e}")
        return False
