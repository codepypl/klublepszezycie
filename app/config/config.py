"""
Enhanced Configuration Management
Zarządzanie konfiguracją aplikacji z walidacją i domyślnymi wartościami
"""
import os
import logging
from typing import Optional, Union
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logger for configuration
logger = logging.getLogger(__name__)

class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails"""
    pass

class Config:
    """Base configuration class with validation and defaults"""
    
    def __init__(self):
        """Initialize configuration with validation"""
        self._validate_required_settings()
        self._log_configuration()
    
    def _validate_required_settings(self):
        """Validate that all required settings are present"""
        required_settings = [
            'SECRET_KEY',
            'DATABASE_URL',
            'MAIL_SERVER',
            'MAIL_USERNAME',
            'MAIL_PASSWORD',
            'ADMIN_EMAIL',
            'BASE_URL'
        ]
        
        missing_settings = []
        for setting in required_settings:
            if not os.getenv(setting):
                missing_settings.append(setting)
        
        if missing_settings:
            raise ConfigValidationError(
                f"Missing required environment variables: {', '.join(missing_settings)}. "
                f"Please check your .env file or environment variables."
            )
    
    def _log_configuration(self):
        """Log configuration status (without sensitive data)"""
        logger.info("🔧 Configuration loaded successfully")
        logger.info(f"📊 Database: {Config._mask_url(os.getenv('DATABASE_URL'))}")
        logger.info(f"📧 Mail Server: {os.getenv('MAIL_SERVER')}")
        logger.info(f"🌐 Base URL: {os.getenv('BASE_URL')}")
        logger.info(f"👤 Admin Email: {os.getenv('ADMIN_EMAIL')}")
    
    @staticmethod
    def _mask_url(url: str) -> str:
        """Mask sensitive parts of URL for logging"""
        if not url:
            return "Not set"
        if '@' in url:
            return url.split('@')[0].split('://')[0] + '://***@' + url.split('@')[1]
        return url
    
    def _get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean value from environment variable"""
        value = os.getenv(key, '').lower()
        return value in ('true', '1', 'yes', 'on')
    
    def _get_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        """Get integer value from environment variable"""
        value = os.getenv(key)
        if not value:
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Invalid integer value for {key}: {value}, using default: {default}")
            return default
    
    def _get_str(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get string value from environment variable"""
        return os.getenv(key, default)
    
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # PostgreSQL Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Timezone Configuration
    TIMEZONE = os.getenv('TIMEZONE', 'Europe/Warsaw')
    USE_LOCAL_TIME = os.getenv('USE_LOCAL_TIME', 'true').lower() == 'true'
    
    # File Upload Settings
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB default
    
    # Email Configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    MAIL_DEFAULT_SENDER_NAME = os.getenv('MAIL_DEFAULT_SENDER_NAME', 'Lepsze Życie Club')
    
    # Email Settings
    EMAIL_BATCH_SIZE = int(os.getenv('EMAIL_BATCH_SIZE', 50))
    EMAIL_DELAY = int(os.getenv('EMAIL_DELAY', 1))
    
    # Admin Settings
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # Celery Configuration
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # Email Queue Settings
    EMAIL_QUEUE_BATCH_SIZE = int(os.getenv('EMAIL_QUEUE_BATCH_SIZE', 100))
    EMAIL_QUEUE_DELAY = int(os.getenv('EMAIL_QUEUE_DELAY', 2))
    
    # Group Synchronization Settings
    AUTO_GROUP_SYNC = os.getenv('AUTO_GROUP_SYNC', 'false').lower() == 'true'
    
    # Mailgun Configuration
    MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN')
    MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
    
    # Base URL
    BASE_URL = os.getenv('BASE_URL')
    
    # Additional settings with defaults
    DEBUG = False
    TESTING = False
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'app/logs/app.log')
    
    # Security Settings
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    
    # Pagination Settings
    PAGINATE_BY = int(os.getenv('PAGINATE_BY', 10))  # Default items per page for admin tables
    
    @classmethod
    def validate_config(cls):
        """Validate configuration and return status"""
        try:
            cls()
            return True, "Configuration is valid"
        except ConfigValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Configuration error: {str(e)}"


class DevelopmentConfig(Config):
    """Development configuration with additional settings"""
    DEBUG = True
    TESTING = False
    
    # Database connection parameters for scripts
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'betterlife')
    DB_USER = os.getenv('DB_USER', 'shadi')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    
    # Development-specific settings
    SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'false').lower() == 'true'
    WTF_CSRF_ENABLED = True
    
    def __init__(self):
        super().__init__()
        logger.info("🔧 Development configuration loaded")


class ProductionConfig(Config):
    """Production configuration with security enhancements"""
    DEBUG = False
    TESTING = False
    
    # Production security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Production logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARNING')
    
    def __init__(self):
        super().__init__()
        logger.info("🔧 Production configuration loaded")


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'sqlite:///:memory:')
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    def __init__(self):
        super().__init__()
        logger.info("🔧 Testing configuration loaded")


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env: str = None) -> Config:
    """Get configuration for specified environment"""
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    
    if env not in config:
        logger.warning(f"Unknown environment: {env}, using default")
        env = 'default'
    
    return config[env]


def validate_all_configs():
    """Validate all configuration environments"""
    results = {}
    for env_name, config_class in config.items():
        if env_name == 'default':
            continue
        try:
            config_class()
            results[env_name] = True
        except Exception as e:
            results[env_name] = str(e)
    
    return results


if __name__ == "__main__":
    """Test configuration when run directly"""
    print("🧪 Testing configuration...")
    
    # Test all configurations
    results = validate_all_configs()
    
    for env, status in results.items():
        if status is True:
            print(f"✅ {env}: Valid")
        else:
            print(f"❌ {env}: {status}")
    
    # Test current environment
    current_env = os.getenv('FLASK_ENV', 'development')
    print(f"\n🔧 Current environment: {current_env}")
    
    try:
        current_config = get_config(current_env)
        print(f"✅ Current configuration is valid")
    except Exception as e:
        print(f"❌ Current configuration error: {e}")