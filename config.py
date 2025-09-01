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
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    
    # Email Configuration (Zoho Mail)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.zoho.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'no.reply@lepszezycie.pl')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '3A_8!24A_6qRdnUV4m_Ujzed.fV')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'no.reply@lepszezycie.pl')
    MAIL_DEFAULT_SENDER_NAME = os.getenv('MAIL_DEFAULT_SENDER_NAME', 'Lepsze Życie Club')
    
    # Email Settings
    EMAIL_BATCH_SIZE = int(os.getenv('EMAIL_BATCH_SIZE', 50))  # Max emails per batch
    EMAIL_DELAY = int(os.getenv('EMAIL_DELAY', 1))  # Delay between emails in seconds



class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL', 
        'postgresql://shadi:Das5ahec@localhost:5432/klub')
    
    # Database connection parameters for scripts
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'klub')
    DB_USER = os.getenv('DB_USER', 'shadi')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'Das5ahec')

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
