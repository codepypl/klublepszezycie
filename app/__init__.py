"""
Główna aplikacja Flask - refaktoryzowana wersja
"""
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

# Import db from models to avoid conflicts
from models import db

# Initialize extensions
login_manager = LoginManager()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://shadi@localhost:5432/betterlife')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Setup logging for Flask app
    import logging
    logger = logging.getLogger(__name__)
    logger.info("🔧 Initializing Flask application...")
    
    # Initialize extensions with app
    logger.info("🔗 Initializing database connection...")
    db.init_app(app)
    
    logger.info("🔐 Setting up authentication...")
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Musisz się zalogować, aby uzyskać dostęp do tej strony.'
    login_manager.login_message_category = 'info'
    
    # Import models in app context
    logger.info("📊 Loading database models...")
    with app.app_context():
        from models import User, EventSchedule, EventRegistration, UserGroup, EventRecipientGroup, BlogCategory, BlogPost, BlogTag, BlogComment, SEOSettings, SocialLink, FooterSettings, LegalDocument, EmailTemplate, UserGroupMember, EmailCampaign, EmailQueue, EmailLog, PasswordResetToken
    
    # Register blueprints
    logger.info("🛣️ Registering routes...")
    from app.blueprints import public_bp, admin_bp, api_bp, auth_bp, blog_bp, seo_bp, social_bp, events_bp, users_bp, footer_bp, email_api_bp, ankieter_bp
    from crm.crm_api import crm_api_bp
    
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(email_api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(seo_bp, url_prefix='/admin')
    app.register_blueprint(social_bp, url_prefix='/admin')
    app.register_blueprint(events_bp, url_prefix='/admin')
    app.register_blueprint(users_bp, url_prefix='/admin')
    app.register_blueprint(footer_bp, url_prefix='/admin')
    app.register_blueprint(ankieter_bp, url_prefix='/crm')
    app.register_blueprint(crm_api_bp)
    
    # Import user loader
    logger.info("👤 Setting up user authentication...")
    from app.utils.auth import load_user
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
    
    # Add SEO context processor
    logger.info("🔍 Adding SEO context processor...")
    @app.context_processor
    def inject_seo():
        """Inject SEO utilities into all templates"""
        def get_seo_settings(page_type, fallback=True):
            from app.utils.seo import SEOManager
            return SEOManager.get_seo_settings(page_type, fallback)
        
        def get_blog_post_seo(post):
            from app.utils.seo import SEOManager
            return SEOManager.generate_blog_post_seo(post)
        
        def get_blog_category_seo(category):
            from app.utils.seo import SEOManager
            return SEOManager.generate_blog_category_seo(category)
        
        def get_blog_tag_seo(tag):
            from app.utils.seo import SEOManager
            return SEOManager.generate_blog_tag_seo(tag)
        
        def get_event_seo(event):
            from app.utils.seo import SEOManager
            return SEOManager.generate_event_seo(event)
        
        def get_section_seo(section):
            from app.utils.seo import SEOManager
            return SEOManager.generate_section_seo(section)
        
        return {
            'get_seo_settings': get_seo_settings,
            'get_blog_post_seo': get_blog_post_seo,
            'get_blog_category_seo': get_blog_category_seo,
            'get_blog_tag_seo': get_blog_tag_seo,
            'get_event_seo': get_event_seo,
            'get_section_seo': get_section_seo
        }
    
    # Create database tables
    logger.info("🗄️ Creating database tables...")
    with app.app_context():
        db.create_all()
        logger.info("✅ Database tables created successfully!")
    
    logger.info("✅ Flask application initialized successfully!")
    return app
