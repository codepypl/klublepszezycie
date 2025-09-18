"""
Public business logic controller
"""
from flask import request, jsonify, flash, redirect, url_for
from app.models import db, EventSchedule, EventRegistration, User, Section, MenuItem, FAQ, BenefitItem, Testimonial, SocialLink, FooterSettings
from app.services.email_service import EmailService
from app.api.email_api import add_user_to_event_group
import os
import hmac
import hashlib
from datetime import datetime
from app.utils.validation_utils import validate_email, validate_phone, validate_event_date
from app.utils.timezone_utils import get_local_now, convert_to_local
from app.utils.blog_utils import generate_blog_link
import json
import logging
import hashlib
import hmac

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
            if has_request_context and request.endpoint.startswith('blog.'):
                # For blog pages, show items marked for blog OR items not marked for any specific page
                menu_items_db = MenuItem.query.filter(
                    MenuItem.is_active == True,
                    (MenuItem.blog == True) | (MenuItem.blog == False)
                ).order_by(MenuItem.order.asc()).all()
            else:
                # For other pages, show items NOT marked for blog
                menu_items_db = MenuItem.query.filter(
                    MenuItem.is_active == True,
                    MenuItem.blog == False
                ).order_by(MenuItem.order.asc()).all()
            
            menu_items = []
            for item in menu_items_db:
                # Use blog_url if available and we're on blog pages, otherwise use regular url
                if has_request_context and request.endpoint.startswith('blog.') and item.blog_url:
                    url = item.blog_url
                else:
                    url = item.url
                menu_items.append({
                    'title': item.title, 
                    'url': url, 
                    'is_active': item.is_active
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
                    'subtitle': section.subtitle
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
            current_registrations = EventRegistration.query.filter_by(event_id=event_id).count()
            if event.max_participants and current_registrations >= event.max_participants:
                return {
                    'success': False,
                    'error': 'Wydarzenie jest pełne'
                }
            
            # Check if user already registered
            existing_registration = EventRegistration.query.filter_by(
                event_id=event_id, email=email
            ).first()
            
            if existing_registration:
                return {
                    'success': False,
                    'error': 'Jesteś już zarejestrowany na to wydarzenie'
                }
            
            # Create registration
            registration = EventRegistration(
                event_id=event_id,
                first_name=name,
                email=email,
                phone=phone,
                notes=notes,
                status='confirmed'
            )
            
            db.session.add(registration)
            db.session.commit()
            
            # Add user to event group if exists
            try:
                add_user_to_event_group(email, event.title)
            except Exception as e:
                logging.warning(f"Failed to add user to event group: {str(e)}")
            
            return {
                'success': True,
                'registration': registration,
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
                    'error': 'Nieprawidłowy lub wygasły token'
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
                    'error': 'Użytkownik nie został znaleziony'
                }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def delete_user_account(email, token):
        """Delete user account"""
        try:
            if not verify_unsubscribe_token(email, 'delete_account', token):
                return {
                    'success': False,
                    'error': 'Nieprawidłowy lub wygasły token'
                }
            
            # Find user by email
            user = User.query.filter_by(email=email).first()
            if user:
                # Don't allow deleting admin users
                if user.is_admin_role():
                    return {
                        'success': False,
                        'error': 'Nie można usunąć konta administratora'
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
                
                # Asynchronicznie synchronizuj wszystkie grupy wydarzeń po usunięciu użytkownika
                success, message = group_manager.sync_event_groups()
                if success:
                    print(f"✅ Zsynchronizowano wszystkie grupy wydarzeń po usunięciu użytkownika {user.email}")
                else:
                    print(f"❌ Błąd synchronizacji grup wydarzeń: {message}")
                
                # Delete user
                db.session.delete(user)
                db.session.commit()
                
                print(f"✅ Użytkownik {user.email} został usunięty z systemu")
                
                return {
                    'success': True,
                    'message': 'Konto zostało usunięte pomyślnie'
                }
            else:
                return {
                    'success': False,
                    'error': 'Użytkownik nie został znaleziony'
                }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
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
            email_service.send_email(
                to_email='kontakt@klublepszezycie.pl',
                to_name='Klub Lepsze Życie',
                subject=f'Wiadomość kontaktowa: {subject}',
                template='contact_message',
                sender_name=name,
                sender_email=email,
                message=message
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
    """Generate unsubscribe token for email"""
    try:
        secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')
        message = f"{email}:{action}"
        token = hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return token
    except Exception:
        return None

def verify_unsubscribe_token(email, action, token):
    """Verify unsubscribe token"""
    try:
        secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')
        expected_token = generate_unsubscribe_token(email, action)
        return hmac.compare_digest(token, expected_token)
    except Exception:
        return False
