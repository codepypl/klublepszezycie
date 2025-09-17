"""
Tests for user roles system
"""
import pytest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User

@pytest.fixture
def app():
    """Create test app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

def test_user_role_methods(app):
    """Test user role checking methods"""
    with app.app_context():
        # Test admin user
        admin_user = User(
            email='admin@test.com',
            password_hash='test_hash',
            role='admin'
        )
        db.session.add(admin_user)
        db.session.commit()
        
        assert admin_user.is_admin_role() == True
        assert admin_user.is_ankieter_role() == False
        assert admin_user.is_user_role() == False
        assert admin_user.has_role('admin') == True
        assert admin_user.has_role('ankieter') == False
        
        # Test ankieter user
        ankieter_user = User(
            email='ankieter@test.com',
            password_hash='test_hash',
            role='ankieter'
        )
        db.session.add(ankieter_user)
        db.session.commit()
        
        assert ankieter_user.is_admin_role() == False
        assert ankieter_user.is_ankieter_role() == True
        assert ankieter_user.is_user_role() == False
        assert ankieter_user.has_role('ankieter') == True
        assert ankieter_user.has_role('admin') == False
        
        # Test regular user
        regular_user = User(
            email='user@test.com',
            password_hash='test_hash',
            role='user'
        )
        db.session.add(regular_user)
        db.session.commit()
        
        assert regular_user.is_admin_role() == False
        assert regular_user.is_ankieter_role() == False
        assert regular_user.is_user_role() == True
        assert regular_user.has_role('user') == True
        assert regular_user.has_role('admin') == False

def test_backward_compatibility(app):
    """Test backward compatibility with is_admin field"""
    with app.app_context():
        # Test user with is_admin=True but role='user'
        legacy_admin = User(
            email='legacy@test.com',
            password_hash='test_hash',
            is_admin=True,
            role='user'
        )
        db.session.add(legacy_admin)
        db.session.commit()
        
        # Should still be considered admin due to is_admin field
        assert legacy_admin.is_admin_role() == True
        assert legacy_admin.has_role('admin') == True

def test_ankieter_dashboard_access(client, app):
    """Test ankieter dashboard access"""
    with app.app_context():
        # Create ankieter user
        ankieter = User(
            email='ankieter@test.com',
            password_hash='test_hash',
            role='ankieter',
            is_active=True
        )
        db.session.add(ankieter)
        db.session.commit()
        
        # Test access to ankieter dashboard
        with client.session_transaction() as sess:
            sess['_user_id'] = str(ankieter.id)
            sess['_fresh'] = True
        
        response = client.get('/ankieter/')
        assert response.status_code == 200
        assert b'Dashboard Ankietera' in response.data

def test_admin_can_access_ankieter_dashboard(client, app):
    """Test that admin can access ankieter dashboard"""
    with app.app_context():
        # Create admin user
        admin = User(
            email='admin@test.com',
            password_hash='test_hash',
            role='admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        
        # Test access to ankieter dashboard
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
            sess['_fresh'] = True
        
        response = client.get('/ankieter/')
        assert response.status_code == 200
        assert b'Dashboard Ankietera' in response.data

def test_regular_user_cannot_access_ankieter_dashboard(client, app):
    """Test that regular user cannot access ankieter dashboard"""
    with app.app_context():
        # Create regular user
        user = User(
            email='user@test.com',
            password_hash='test_hash',
            role='user',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        
        # Test access to ankieter dashboard
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
        
        response = client.get('/ankieter/')
        assert response.status_code == 302  # Redirect to login
