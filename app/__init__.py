"""
Flask application factory
"""
import os
import logging
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from app.models import db
# Usunięto TaskManager - niepotrzebny

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """Factory function for creating Flask app"""
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Konfiguracja
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    if config_name == 'production':
        app.config.from_object('app.config.config.ProductionConfig')
    elif config_name == 'testing':
        app.config.from_object('app.config.config.TestingConfig')
    else:
        app.config.from_object('app.config.config.DevelopmentConfig')
    
    # Inicjalizacja rozszerzeń
    db.init_app(app)
    migrate = Migrate(app, db, directory='app/migrations')
    
    # CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["https://klublepszezycie.pl", "http://localhost:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
        }
    })
    
    # Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Musisz się zalogować, aby uzyskać dostęp do tej strony.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Rejestracja blueprintów z routes
    from app.routes import (
        admin_route, ankieter_routes, auth_route, blog_route, crm_routes, events_route,
        footer_route, log_route, public_route, seo_route, social_route,
        user_groups_route, users_route, unsubscribe_routes
    )
    
    app.register_blueprint(public_route.public_bp)
    app.register_blueprint(auth_route.auth_bp)
    app.register_blueprint(admin_route.admin_bp)
    app.register_blueprint(ankieter_routes.ankieter_bp)
    app.register_blueprint(blog_route.blog_bp)
    app.register_blueprint(crm_routes.crm_bp)
    app.register_blueprint(events_route.events_bp)
    app.register_blueprint(footer_route.footer_bp)
    app.register_blueprint(log_route.log_route)
    app.register_blueprint(seo_route.seo_bp)
    app.register_blueprint(social_route.social_bp)
    app.register_blueprint(user_groups_route.user_groups_bp)
    app.register_blueprint(users_route.users_bp)
    app.register_blueprint(unsubscribe_routes.unsubscribe_bp)
    
    # Rejestracja API blueprintów - uproszczona wersja
    try:
        from app.api import benefits_api, faq_api, log_api, menu_api, sections_api, seo_api, social_api, stats_api, testimonials_api, user_groups_api, users_api
        from app.api.email import async_email_api, queue_api, monitoring_api, campaigns_api, templates_api
        from app.api.events import events_api
        
        app.register_blueprint(benefits_api.benefits_api_bp, url_prefix='/api')
        app.register_blueprint(faq_api.faq_api_bp, url_prefix='/api')
        app.register_blueprint(log_api.log_bp, url_prefix='/api')
        app.register_blueprint(menu_api.menu_api_bp, url_prefix='/api')
        app.register_blueprint(sections_api.sections_api_bp, url_prefix='/api')
        app.register_blueprint(seo_api.seo_api_bp, url_prefix='/api')
        app.register_blueprint(social_api.social_api_bp, url_prefix='/api')
        app.register_blueprint(stats_api.stats_api_bp, url_prefix='/api')
        app.register_blueprint(testimonials_api.testimonials_api_bp, url_prefix='/api')
        app.register_blueprint(user_groups_api.user_groups_bp, url_prefix='/api')
        app.register_blueprint(users_api.users_api_bp, url_prefix='/api')
        app.register_blueprint(async_email_api.async_email_bp, url_prefix='/api')
        app.register_blueprint(queue_api.email_queue_bp, url_prefix='/api')
        app.register_blueprint(monitoring_api.email_monitoring_bp, url_prefix='/api')
        app.register_blueprint(campaigns_api.email_campaigns_bp, url_prefix='/api')
        app.register_blueprint(templates_api.email_templates_bp, url_prefix='/api')
        app.register_blueprint(events_api.events_api_bp, url_prefix='/api')
        
        # Rejestracja blog API
        from app.api.blog import posts_api, tags_api, categories_api, media_api, comments_api
        app.register_blueprint(posts_api.posts_api_bp, url_prefix='/api')
        app.register_blueprint(tags_api.tags_api_bp, url_prefix='/api')
        app.register_blueprint(categories_api.categories_api_bp, url_prefix='/api')
        app.register_blueprint(media_api.media_api_bp, url_prefix='/api')
        app.register_blueprint(comments_api.comments_api_bp, url_prefix='/api')
        
        logger.info("✅ Blog API blueprints zarejestrowane")
        
        logger.info("✅ API blueprints zarejestrowane")
    except Exception as e:
        logger.warning(f"⚠️ Nie udało się zarejestrować wszystkich API blueprintów: {e}")
    
    
    # TaskManager usunięty - niepotrzebny w systemie z cronem
    
    # Event listeners dla automatycznej synchronizacji grup
    try:
        from app.services.group_manager import GroupManager
        group_manager = GroupManager()
        # group_manager.setup_event_listeners()  # Metoda nie istnieje
        logger.info("✅ Event listeners dla automatycznej synchronizacji grup zostały skonfigurowane")
        logger.info("🚀 Automatyczna synchronizacja grup została włączona")
    except Exception as e:
        logger.warning(f"⚠️ Nie udało się skonfigurować event listeners: {e}")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        from flask import render_template
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        return render_template('500.html'), 500
    
    # Context processors
    @app.context_processor
    def inject_user():
        from flask_login import current_user
        return dict(current_user=current_user)
    
    @app.context_processor
    def inject_config():
        return dict(config=app.config)
    
    # Shutdown handler
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()
    
    # Graceful shutdown - TaskManager usunięty
    
    # Dodaj filtry Jinja2
    @app.template_filter('from_json')
    def from_json_filter(value):
        """Filtr do parsowania JSON w szablonach"""
        import json
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return {}
        return value or {}
    
    # Dodaj funkcje globalne do kontekstu Jinja2
    @app.template_global()
    def get_seo_settings(page_type, fallback_to_default=True):
        """Funkcja globalna do pobierania ustawień SEO"""
        from app.utils.seo_utils import SEOManager
        return SEOManager.get_seo_settings(page_type, fallback_to_default)
    
    @app.template_global()
    def get_blog_category_seo(category):
        """Funkcja globalna do pobierania SEO dla kategorii bloga"""
        from app.utils.seo_utils import SEOManager
        return SEOManager.generate_blog_category_seo(category)
    
    @app.template_global()
    def get_blog_tag_seo(tag):
        """Funkcja globalna do pobierania SEO dla tagów bloga"""
        from app.utils.seo_utils import SEOManager
        return SEOManager.get_blog_tag_seo(tag)
    
    @app.template_global()
    def generate_blog_link(link_data):
        """Funkcja globalna do generowania linków bloga"""
        from app.utils.blog_utils import generate_blog_link
        return generate_blog_link(link_data)
    
    @app.template_global()
    def get_post_url_with_category(post):
        """Funkcja globalna do generowania URL postów z kategorią"""
        from app.blueprints.blog_controller import BlogController
        return BlogController.get_post_url_with_category(post)
    
    @app.template_global()
    def get_category_url_with_hierarchy(category):
        """Funkcja globalna do generowania URL kategorii z hierarchią"""
        from app.blueprints.blog_controller import BlogController
        return BlogController.get_category_url_with_hierarchy(category)
    
    logger.info("✅ Flask application initialized successfully!")
    return app