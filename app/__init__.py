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
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://shadi@localhost:5432/betterlife')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'static/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
    
    # Setup logging for Flask app
    import logging
    logger = logging.getLogger(__name__)
    logger.info("🔧 Initializing Flask application...")
    
    # Initialize extensions with app
    logger.info("🔗 Initializing database connection...")
    db.init_app(app)
    
    logger.info("🔄 Setting up database migrations...")
    migrate.init_app(app, db)
    
    logger.info("🔐 Setting up authentication...")
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Musisz się zalogować, aby uzyskać dostęp do tej strony.'
    login_manager.login_message_category = 'info'
    
    # Import models in app context
    logger.info("📊 Loading database models...")
    with app.app_context():
        from app.models import User, EventSchedule, EventRegistration, UserGroup, BlogCategory, BlogPost, BlogTag, BlogComment, SocialLink, EmailTemplate, UserGroupMember, EmailCampaign, EmailQueue, EmailLog, PasswordResetToken, SEOSettings, FooterSettings, LegalDocument
    
    # Register blueprints
    logger.info("🛣️ Registering routes...")
    from app.routes import public_bp, admin_bp, auth_bp, blog_bp, seo_bp, social_bp, events_bp, users_bp, footer_bp, crm_bp, ankieter_bp
    from app.api import email_bp, users_api_bp, testimonials_api_bp, sections_api_bp, menu_api_bp, faq_api_bp, benefits_api_bp, events_api_bp, blog_api_bp, seo_api_bp, social_api_bp, crm_api_bp, agent_api_bp
    
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    # Main API blueprint removed - individual API modules are registered separately
    app.register_blueprint(email_bp, url_prefix='/api')
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
    app.register_blueprint(seo_bp, url_prefix='/admin')
    app.register_blueprint(social_bp, url_prefix='/admin')
    app.register_blueprint(events_bp, url_prefix='/admin')
    app.register_blueprint(users_bp, url_prefix='/admin')
    app.register_blueprint(footer_bp, url_prefix='/admin')
    app.register_blueprint(crm_bp, url_prefix='/admin/crm')
    app.register_blueprint(ankieter_bp, url_prefix='/ankieter')
    app.register_blueprint(crm_api_bp, url_prefix='/api/crm')
    app.register_blueprint(agent_api_bp, url_prefix='/api/crm/agent')
    
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
