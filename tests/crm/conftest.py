"""
Configuration for CRM tests
"""
import pytest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

@pytest.fixture(scope="session")
def app():
    """Create test app for session"""
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app

@pytest.fixture(scope="function")
def db_session(app):
    """Create database session for each test"""
    with app.app_context():
        from app import db
        db.create_all()
        yield db
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()
