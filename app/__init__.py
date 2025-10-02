"""
Główna aplikacja Flask - refaktoryzowana wersja
"""
from flask import Flask, jsonify
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

# Import db from models to avoid conflicts
from app.models import db

# Initialize extensions
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Setup logging for Flask app first
    import logging
    logger = logging.getLogger(__name__)
    logger.info("🔧 Initializing Flask application...")
    
    # Load configuration from config.py with validation
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.config.config import get_config, ConfigValidationError
    
    config_name = os.getenv('FLASK_ENV', 'development')
    
    try:
        # Validate configuration before loading
        config_class = get_config(config_name)
        app.config.from_object(config_class)
        logger.info(f"✅ Configuration loaded successfully for environment: {config_name}")
    except ConfigValidationError as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Configuration loading failed: {e}")
        raise
    
    # Initialize extensions with app
    logger.info("🔗 Initializing database connection...")
    db.init_app(app)
    
    logger.info("🔄 Setting up database migrations...")
    migrate.init_app(app, db, directory='app/migrations')
    
    logger.info("🔐 Setting up authentication...")
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Musisz się zalogować, aby uzyskać dostęp do tej strony.'
    login_manager.login_message_category = 'info'
    
    # Import models in app context
    logger.info("📊 Loading database models...")
    with app.app_context():
        from app.models import User, EventSchedule, UserGroup, BlogCategory, BlogPost, BlogTag, BlogComment, SocialLink, EmailTemplate, UserGroupMember, EmailCampaign, EmailQueue, EmailLog, PasswordResetToken, SEOSettings, FooterSettings, LegalDocument, UserLogs, UserHistory, Stats
    
    # Register blueprints
    logger.info("🛣️ Registering routes...")
    from app.routes import public_bp, admin_bp, auth_bp, blog_bp, blog_admin_bp, seo_bp, social_bp, events_bp, users_bp, footer_bp, crm_bp, ankieter_bp
    from app.routes.unsubscribe_routes import unsubscribe_bp
    from app.routes.user_groups_route import user_groups_bp
    from app.api import email_bp, users_api_bp, testimonials_api_bp, sections_api_bp, menu_api_bp, faq_api_bp, benefits_api_bp, events_api_bp, blog_api_bp, seo_api_bp, social_api_bp, crm_api_bp, agent_api_bp, stats_api_bp
    from app.api.user_groups_api import user_groups_bp as user_groups_api_bp
    from app.api.email_v2_api import email_v2_bp
    from app.api.mailgun_webhook_api import mailgun_webhook_bp
    
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_groups_bp)
    # Main API blueprint removed - individual API modules are registered separately
    app.register_blueprint(email_bp, url_prefix='/api')
    app.register_blueprint(email_v2_bp, url_prefix='/api')  # Nowy system mailingu v2
    app.register_blueprint(user_groups_api_bp, url_prefix='/api')
    app.register_blueprint(users_api_bp, url_prefix='/api')
    app.register_blueprint(testimonials_api_bp, url_prefix='/api')
    app.register_blueprint(sections_api_bp, url_prefix='/api')
    app.register_blueprint(menu_api_bp, url_prefix='/api')
    app.register_blueprint(faq_api_bp, url_prefix='/api')
    app.register_blueprint(benefits_api_bp, url_prefix='/api')
    app.register_blueprint(events_api_bp, url_prefix='/api')
    app.register_blueprint(blog_api_bp, url_prefix='/api')
    app.register_blueprint(seo_api_bp, url_prefix='/api')
    app.register_blueprint(social_api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(blog_admin_bp)
    app.register_blueprint(seo_bp, url_prefix='/admin')
    app.register_blueprint(social_bp, url_prefix='/admin')
    app.register_blueprint(events_bp, url_prefix='/admin')
    app.register_blueprint(users_bp, url_prefix='/admin')
    app.register_blueprint(footer_bp, url_prefix='/admin')
    app.register_blueprint(crm_bp, url_prefix='/admin/crm')
    app.register_blueprint(ankieter_bp, url_prefix='/ankieter')
    app.register_blueprint(crm_api_bp, url_prefix='/api/crm')
    app.register_blueprint(agent_api_bp, url_prefix='/api/crm/agent')
    app.register_blueprint(stats_api_bp, url_prefix='/api')
    app.register_blueprint(mailgun_webhook_bp, url_prefix='/api')  # Webhook endpoints
    app.register_blueprint(unsubscribe_bp)
    
    # Log blueprints
    from app.api.log_api import log_bp
    from app.routes.log_route import log_route
    app.register_blueprint(log_bp, url_prefix='/api')
    app.register_blueprint(log_route)
    
    # Import user loader
    logger.info("👤 Setting up user authentication...")
    
    # Error handlers
    @app.errorhandler(413)
    def too_large(e):
        return jsonify({
            'success': False,
            'error': 'Artykuł jest za duży. Spróbuj zmniejszyć rozmiar obrazów lub treści.',
            'message': 'Content too large'
        }), 413
    from app.utils.auth_utils import load_user
    login_manager.user_loader(load_user)
    
    # Add custom Jinja2 filters
    logger.info("🔧 Adding custom Jinja2 filters...")
    @app.template_filter('from_json')
    def from_json_filter(value):
        """Convert JSON string to Python object"""
        if value is None or value == '':
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return None
    
    @app.template_filter('get_status_color')
    def get_status_color_filter(status):
        """Get Bootstrap color class for email status"""
        status_colors = {
            'sent': 'primary',
            'delivered': 'success',
            'opened': 'info',
            'clicked': 'warning',
            'bounced': 'danger',
            'failed': 'secondary',
            'sent_test': 'info'
        }
        return status_colors.get(status, 'secondary')
    
    @app.template_filter('get_status_label')
    def get_status_label_filter(status):
        """Get human-readable label for email status"""
        status_labels = {
            'sent': 'Wysłany',
            'delivered': 'Dostarczony',
            'opened': 'Otwarty',
            'clicked': 'Kliknięty',
            'bounced': 'Odrzucony',
            'failed': 'Błąd',
            'sent_test': 'Test Wysłany'
        }
        return status_labels.get(status, status.title())
    
    # Add SEO context processor
    logger.info("🔍 Adding SEO context processor...")
    @app.context_processor
    def inject_seo():
        """Inject SEO utilities into all templates"""
        def get_seo_settings(page_type, fallback=True):
            from app.utils.seo_utils import SEOManager
            return SEOManager.get_seo_settings(page_type, fallback)
        
        def get_blog_post_seo(post):
            from app.utils.seo_utils import SEOManager
            return SEOManager.generate_blog_post_seo(post)
        
        def get_blog_category_seo(category):
            from app.utils.seo_utils import SEOManager
            return SEOManager.generate_blog_category_seo(category)
        
        def get_blog_tag_seo(tag):
            from app.utils.seo_utils import SEOManager
            return SEOManager.generate_blog_tag_seo(tag)
        
        def get_event_seo(event):
            from app.utils.seo_utils import SEOManager
            return SEOManager.generate_event_seo(event)
        
        def get_section_seo(section):
            from app.utils.seo_utils import SEOManager
            return SEOManager.generate_section_seo(section)
        
        def get_post_url_with_category(post):
            from app.blueprints.blog_controller import BlogController
            return BlogController.get_post_url_with_category(post)
        
        def get_category_url_with_hierarchy(category):
            from app.blueprints.blog_controller import BlogController
            return BlogController.get_category_url_with_hierarchy(category)
        
        def get_blog_posts_for_select():
            from app.utils.blog_utils import get_blog_posts_for_select
            return get_blog_posts_for_select()
        
        def get_blog_categories_for_select():
            from app.utils.blog_utils import get_blog_categories_for_select
            return get_blog_categories_for_select()
        
        return {
            'get_seo_settings': get_seo_settings,
            'get_blog_post_seo': get_blog_post_seo,
            'get_blog_category_seo': get_blog_category_seo,
            'get_blog_tag_seo': get_blog_tag_seo,
            'get_event_seo': get_event_seo,
            'get_section_seo': get_section_seo,
            'get_post_url_with_category': get_post_url_with_category,
            'get_category_url_with_hierarchy': get_category_url_with_hierarchy,
            'get_blog_posts_for_select': get_blog_posts_for_select,
            'get_blog_categories_for_select': get_blog_categories_for_select
        }
    
    # Create database tables
    logger.info("🗄️ Creating database tables...")
    with app.app_context():
        db.create_all()
        logger.info("✅ Database tables created successfully!")
        
    # Configure group synchronization
    if app.config.get('AUTO_GROUP_SYNC', False):
        from app.services.group_sync_service import GroupSyncService
        GroupSyncService.enable_auto_sync()
        logger.info("🚀 Automatic group synchronization is enabled")
    else:
        logger.info("⏸️ Automatic group synchronization is disabled - using manual sync only")
    
    # Initialize Celery
    logger.info("🔄 Initializing Celery...")
    try:
        from celery_app import make_celery
        celery = make_celery(app)
        app.celery = celery
        logger.info("✅ Celery initialized successfully!")
    except Exception as e:
        logger.warning(f"⚠️ Celery initialization failed: {e}")
        logger.info("📧 Email processing will use cron job as backup")
    
    logger.info("✅ Flask application initialized successfully!")
    return app
