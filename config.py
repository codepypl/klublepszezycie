import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # PostgreSQL Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 
        'postgresql://shadi@localhost:5432/betterlife')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Timezone Configuration
    TIMEZONE = os.getenv('TIMEZONE', 'Europe/Warsaw')  # Domyślnie polski czas
    USE_LOCAL_TIME = os.getenv('USE_LOCAL_TIME', 'true').lower() == 'true'
    
    # File Upload Settings
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    
    
    # Email Configuration (Zoho Mail)
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    MAIL_DEFAULT_SENDER_NAME = os.getenv('MAIL_DEFAULT_SENDER_NAME')
    
    # Email Settings
    EMAIL_BATCH_SIZE = int(os.getenv('EMAIL_BATCH_SIZE', 50))  # Max emails per batch
    EMAIL_DELAY = int(os.getenv('EMAIL_DELAY', 1))  # Delay between emails in seconds
    
    # Admin Settings
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@lepszezycie.pl')
    
    # Celery Configuration
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # Email Queue Settings
    EMAIL_QUEUE_BATCH_SIZE = int(os.getenv('EMAIL_QUEUE_BATCH_SIZE', 50))
    EMAIL_QUEUE_DELAY = int(os.getenv('EMAIL_QUEUE_DELAY', 1))  # seconds between emails



class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL', 
        'postgresql://shadi@localhost:5432/betterlife')
    
    # Database connection parameters for scripts
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
