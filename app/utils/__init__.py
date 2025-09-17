# Utils module - centralized utilities for the application

# Import all utility modules for easy access
from .auth_utils import load_user, admin_required, ankieter_required, crm_required, role_required
from .blog_utils import generate_blog_link, get_blog_categories_for_select, get_blog_posts_for_select, validate_blog_link_data
from .crm_file_utils import create_import_directory_structure, generate_import_file_path, delete_import_file, get_relative_path_from_upload_folder
from .email_logging_utils import setup_email_logging, log_email_send, log_email_template_used, log_email_schedule_executed, log_email_system_status, log_smtp_connection
from .logging_utils import get_logger, log_info, log_error, log_warning
from .seo_utils import SEOManager
from .timezone_utils import get_local_datetime, get_local_timezone, get_local_now, convert_to_local, convert_to_utc
from .user_info_utils import get_user_info, get_client_ip, get_location_from_ip, is_private_ip
from .validation_utils import (
    allowed_file, validate_file_type, validate_event_date, validate_email, validate_phone,
    validate_blog_post, validate_blog_categories, validate_blog_tags, validate_featured_image,
    create_slug, generate_unique_slug
)

__all__ = [
    # Auth utilities
    'load_user', 'admin_required', 'ankieter_required', 'crm_required', 'role_required',
    
    # Blog utilities
    'generate_blog_link', 'get_blog_categories_for_select', 'get_blog_posts_for_select', 'validate_blog_link_data',
    
    # CRM file utilities
    'create_import_directory_structure', 'generate_import_file_path', 'delete_import_file', 'get_relative_path_from_upload_folder',
    
    # Email logging utilities
    'setup_email_logging', 'log_email_send', 'log_email_template_used', 'log_email_schedule_executed', 'log_email_system_status', 'log_smtp_connection',
    
    # Logging utilities
    'get_logger', 'log_info', 'log_error', 'log_warning',
    
    # SEO utilities
    'SEOManager',
    
    # Timezone utilities
    'get_local_datetime', 'get_local_timezone', 'get_local_now', 'convert_to_local', 'convert_to_utc',
    
    # User info utilities
    'get_user_info', 'get_client_ip', 'get_location_from_ip', 'is_private_ip',
    
    # Validation utilities
    'allowed_file', 'validate_file_type', 'validate_event_date', 'validate_email', 'validate_phone',
    'validate_blog_post', 'validate_blog_categories', 'validate_blog_tags', 'validate_featured_image',
    'create_slug', 'generate_unique_slug'
]