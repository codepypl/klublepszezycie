import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # PostgreSQL Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Timezone Configuration
    TIMEZONE = os.getenv('TIMEZONE')
    USE_LOCAL_TIME = os.getenv('USE_LOCAL_TIME', 'true').lower() == 'true'
    
    # File Upload Settings
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 0)) if os.getenv('MAX_CONTENT_LENGTH') else None
    
    # Email Configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 0)) if os.getenv('MAIL_PORT') else None
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'false').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    MAIL_DEFAULT_SENDER_NAME = os.getenv('MAIL_DEFAULT_SENDER_NAME')
    
    # Email Settings
    EMAIL_BATCH_SIZE = int(os.getenv('EMAIL_BATCH_SIZE', 0)) if os.getenv('EMAIL_BATCH_SIZE') else None
    EMAIL_DELAY = int(os.getenv('EMAIL_DELAY', 0)) if os.getenv('EMAIL_DELAY') else None
    
    # Admin Settings
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
    
    # Celery Configuration
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')
    
    # Email Queue Settings
    EMAIL_QUEUE_BATCH_SIZE = int(os.getenv('EMAIL_QUEUE_BATCH_SIZE', 0)) if os.getenv('EMAIL_QUEUE_BATCH_SIZE') else None
    EMAIL_QUEUE_DELAY = int(os.getenv('EMAIL_QUEUE_DELAY', 0)) if os.getenv('EMAIL_QUEUE_DELAY') else None
    
    # Group Synchronization Settings
    AUTO_GROUP_SYNC = os.getenv('AUTO_GROUP_SYNC', 'false').lower() == 'true'
    
    # Mailgun Configuration
    MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN')
    MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
    
    # Base URL
    BASE_URL = os.getenv('BASE_URL')


class DevelopmentConfig(Config):
    DEBUG = True
    
    # Database connection parameters for scripts
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}