"""
Template versioning service for managing email template versions
"""
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from app.models import db
from app.models.email_model import EmailTemplate, DefaultEmailTemplate
# Using the extended EmailTemplate model from email_model.py
from app.services.email_service import EmailService

class TemplateVersioningService:
    """Service for managing template versioning"""
    
    def __init__(self):
        self.email_service = EmailService()
    
    def start_editing_default_template(self, template_name: str) -> Tuple[bool, str, Optional[EmailTemplate]]:
        """
        Start editing a default template by creating an edited copy
        
        Args:
            template_name: Name of the default template to edit
            
        Returns:
            Tuple of (success, message, new_template)
        """
        try:
            # Check if default template exists
            default_template = DefaultEmailTemplate.query.filter_by(name=template_name).first()
            if not default_template:
                return False, f"Default template '{template_name}' not found", None
            
            # Create edited copy
            new_template, message = EmailTemplate.create_from_default(template_name)
            if not new_template:
                return False, message, None
            
            return True, f"Started editing '{template_name}'. Created version {new_template.version}", new_template
            
        except Exception as e:
            return False, f"Error starting edit: {str(e)}", None
    
    def save_template_version(self, template_id: int, changes: Dict, make_default: bool = False) -> Tuple[bool, str]:
        """
        Save a new version of a template
        
        Args:
            template_id: ID of the template to save
            changes: Dictionary of changes to apply
            make_default: Whether to make this version the default template
            
        Returns:
            Tuple of (success, message)
        """
        try:
            template = EmailTemplate.query.get(template_id)
            if not template:
                return False, "Template not found"
            
            # Create new version with changes
            new_version = template.create_version(changes)
            
            if make_default:
                if not template.original_template_name:
                    return False, "Cannot make default - template has no original template name"
                
                # Show modal confirmation would be handled in frontend
                # For now, we'll just return success with a message
                return True, f"Version {new_version.version} saved. Ready to make default (requires confirmation)."
            
            return True, f"Version {new_version.version} saved successfully"
            
        except Exception as e:
            return False, f"Error saving version: {str(e)}"
    
    def make_template_default(self, template_id: int) -> Tuple[bool, str]:
        """
        Make a template version the default template (with confirmation)
        
        Args:
            template_id: ID of the template to make default
            
        Returns:
            Tuple of (success, message)
        """
        try:
            template = EmailTemplate.query.get(template_id)
            if not template:
                return False, "Template not found"
            
            success, message = template.make_default()
            return success, message
            
        except Exception as e:
            return False, f"Error making default: {str(e)}"
    
    def restore_default_template(self, template_name: str) -> Tuple[bool, str]:
        """
        Restore a template to its default version
        
        Args:
            template_name: Name of the template to restore
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Deactivate all edited versions
            edited_templates = EmailTemplate.query.filter_by(
                original_template_name=template_name,
                is_edited_copy=True
            ).all()
            
            for template in edited_templates:
                template.is_active = False
            
            db.session.commit()
            
            return True, f"Template '{template_name}' restored to default version"
            
        except Exception as e:
            return False, f"Error restoring default: {str(e)}"
    
    def get_template_versions(self, template_name: str) -> List[EmailTemplate]:
        """
        Get all versions of a template
        
        Args:
            template_name: Name of the template
            
        Returns:
            List of template versions
        """
        return EmailTemplate.query.filter_by(name=template_name)\
            .order_by(EmailTemplate.version.desc()).all()
    
    def restore_to_version(self, template_name: str, version: int) -> Tuple[bool, str]:
        """
        Restore template to a specific version
        
        Args:
            template_name: Name of the template
            version: Version number to restore to
            
        Returns:
            Tuple of (success, message)
        """
        try:
            template = EmailTemplate.query.filter_by(
                name=template_name,
                version=version
            ).first()
            
            if not template:
                return False, f"Version {version} not found for template '{template_name}'"
            
            # Get the latest version to restore
            latest_template = EmailTemplate.query.filter_by(name=template_name)\
                .order_by(EmailTemplate.version.desc()).first()
            
            if not latest_template:
                return False, f"No active template found for '{template_name}'"
            
            success, message = latest_template.restore_to_version(version)
            return success, message
            
        except Exception as e:
            return False, f"Error restoring version: {str(e)}"
    
    def delete_template(self, template_id: int) -> Tuple[bool, str]:
        """
        Delete a template and all its versions
        
        Args:
            template_id: ID of the template to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            template = EmailTemplate.query.get(template_id)
            if not template:
                return False, "Template not found"
            
            # Check if it's a default template
            if template.is_default or template.edited_from_default:
                return False, "Cannot delete default template directly. Use restore to default instead."
            
            # Delete all versions of this template
            versions = EmailTemplate.query.filter_by(name=template.name).all()
            for version in versions:
                db.session.delete(version)
            
            db.session.commit()
            
            return True, f"Template '{template.name}' and all its versions deleted"
            
        except Exception as e:
            return False, f"Error deleting template: {str(e)}"
    
    def send_test_email(self, template_name: str, test_email: str, context: Dict = None) -> Tuple[bool, str]:
        """
        Send a test email using a template
        
        Args:
            template_name: Name of the template to use
            test_email: Email address to send test to
            context: Template context variables
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get the active template (default or edited version)
            template = EmailTemplate.get_default_or_active(template_name)
            if not template:
                return False, f"Template '{template_name}' not found"
            
            # Prepare test context
            if context is None:
                context = {
                    'user_name': 'Test User',
                    'user_email': test_email,
                    'event_title': 'Test Event',
                    'event_date': '2024-12-31',
                    'event_time': '18:00',
                    'event_location': 'Online - Zoom',
                    'event_url': 'https://zoom.us/j/123456789',
                    'temporary_password': 'TempPass123!',
                    'login_url': 'https://klublepszezycie.pl/login',
                    'server_name': 'Test Server',
                    'request_id': 'REQ-12345',
                    'session_id': 'SESS-67890',
                    'severity': 'Medium',
                    'registration_date': '2024-12-27',
                    'admin_panel_url': 'https://klublepszezycie.pl/admin',
                    'message_subject': 'Test Message Subject',
                    'message_content': 'To jest testowa wiadomość od administratora.',
                    'contact_url': 'https://klublepszezycie.pl/contact',
                    'post_title': 'Test Post Title',
                    'comment_author': 'Test Commenter',
                    'comment_email': 'commenter@example.com',
                    'comment_date': '2024-12-27',
                    'comment_content': 'To jest testowy komentarz.',
                    'moderation_url': 'https://klublepszezycie.pl/admin/comments',
                    'new_password': 'NewAdminPass123!'
                }
            
            # Send test email
            success, message = self.email_service.send_template_email(
                to_email=test_email,
                template_name=template_name,
                context=context,
                to_name='Test User',
                use_queue=False
            )
            
            return success, message
            
        except Exception as e:
            return False, f"Error sending test email: {str(e)}"
    
    def get_template_info(self, template_name: str) -> Dict:
        """
        Get comprehensive information about a template
        
        Args:
            template_name: Name of the template
            
        Returns:
            Dictionary with template information
        """
        try:
            # Get default template info
            default_template = DefaultEmailTemplate.query.filter_by(name=template_name).first()
            
            # Get active edited version
            active_template = EmailTemplate.get_active_template(template_name)
            
            # Get all versions
            versions = self.get_template_versions(template_name)
            
            return {
                'name': template_name,
                'has_default': default_template is not None,
                'has_active_edited': active_template is not None,
                'active_version': active_template.version if active_template else 1,
                'total_versions': len(versions),
                'versions': [
                    {
                        'id': v.id,
                        'version': v.version,
                        'created_at': v.created_at.isoformat(),
                        'is_default': v.is_default,
                        'is_active': v.is_active,
                        'is_edited_copy': v.is_edited_copy,
                        'description': v.description
                    } for v in versions
                ],
                'default_template': {
                    'subject': default_template.subject if default_template else None,
                    'updated_at': default_template.updated_at.isoformat() if default_template else None
                } if default_template else None
            }
            
        except Exception as e:
            return {'error': f"Error getting template info: {str(e)}"}
