"""
Tests for ankieter functionality
"""
import pytest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app import create_app, db
from crm.models import Contact, Call, CallQueue
from models import User

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

@pytest.fixture
def ankieter_user(app):
    """Create ankieter user"""
    with app.app_context():
        ankieter = User(
            email='ankieter@test.com',
            password_hash='test_hash',
            role='ankieter',
            is_active=True
        )
        db.session.add(ankieter)
        db.session.commit()
        return ankieter

@pytest.fixture
def admin_user(app):
    """Create admin user"""
    with app.app_context():
        admin = User(
            email='admin@test.com',
            password_hash='test_hash',
            role='admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        return admin

@pytest.fixture
def sample_contacts(app):
    """Create sample contacts"""
    with app.app_context():
        contacts = []
        for i in range(3):
            contact = Contact(
                name=f'Contact {i+1}',
                phone=f'+48 123 456 78{i}',
                email=f'contact{i+1}@example.com',
                company=f'Company {i+1}'
            )
            db.session.add(contact)
            contacts.append(contact)
        
        db.session.commit()
        return contacts

def test_ankieter_dashboard_access(client, app, ankieter_user):
    """Test ankieter can access dashboard"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(ankieter_user.id)
        sess['_fresh'] = True
    
    response = client.get('/ankieter/')
    assert response.status_code == 200
    assert b'Dashboard Ankietera' in response.data

def test_admin_can_access_ankieter_dashboard(client, app, admin_user):
    """Test admin can access ankieter dashboard"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_user.id)
        sess['_fresh'] = True
    
    response = client.get('/ankieter/')
    assert response.status_code == 200
    assert b'Dashboard Ankietera' in response.data

def test_regular_user_cannot_access_ankieter_dashboard(client, app):
    """Test regular user cannot access ankieter dashboard"""
    with app.app_context():
        user = User(
            email='user@test.com',
            password_hash='test_hash',
            role='user',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
        
        response = client.get('/ankieter/')
        assert response.status_code == 302  # Redirect to login

def test_ankieter_calls_page(client, app, ankieter_user):
    """Test ankieter can access calls page"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(ankieter_user.id)
        sess['_fresh'] = True
    
    response = client.get('/ankieter/calls')
    assert response.status_code == 200
    assert b'Zarządzanie połączeniami' in response.data

def test_ankieter_contacts_page(client, app, ankieter_user):
    """Test ankieter can access contacts page"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(ankieter_user.id)
        sess['_fresh'] = True
    
    response = client.get('/ankieter/contacts')
    assert response.status_code == 200
    assert b'Zarządzanie kontaktami' in response.data

def test_call_queue_priority_system(app, ankieter_user, sample_contacts):
    """Test call queue priority system"""
    with app.app_context():
        # Create call queue entries with different priorities
        high_priority = CallQueue(
            contact_id=sample_contacts[0].id,
            priority='high',
            status='pending'
        )
        
        medium_priority = CallQueue(
            contact_id=sample_contacts[1].id,
            priority='medium',
            status='pending'
        )
        
        low_priority = CallQueue(
            contact_id=sample_contacts[2].id,
            priority='low',
            status='pending'
        )
        
        db.session.add_all([high_priority, medium_priority, low_priority])
        db.session.commit()
        
        # Test priority ordering
        queue_entries = CallQueue.query.order_by(
            db.case(
                (CallQueue.priority == 'high', 1),
                (CallQueue.priority == 'medium', 2),
                (CallQueue.priority == 'low', 3)
            )
        ).all()
        
        assert queue_entries[0].priority == 'high'
        assert queue_entries[1].priority == 'medium'
        assert queue_entries[2].priority == 'low'

def test_call_creation_with_ankieter(app, ankieter_user, sample_contacts):
    """Test call creation by ankieter"""
    with app.app_context():
        call = Call(
            contact_id=sample_contacts[0].id,
            ankieter_id=ankieter_user.id,
            call_date='2024-01-01 10:00:00',
            status='interested',
            priority='high',
            notes='Very interested customer',
            duration_minutes=20
        )
        
        db.session.add(call)
        db.session.commit()
        
        assert call.id is not None
        assert call.ankieter_id == ankieter_user.id
        assert call.contact_id == sample_contacts[0].id
        assert call.status == 'interested'
        assert call.duration_minutes == 20
