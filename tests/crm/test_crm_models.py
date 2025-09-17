"""
Tests for CRM models
"""
import pytest
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app import create_app, db
from crm.models import Contact, Call, ImportFile
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

def test_contact_creation(app):
    """Test contact model creation"""
    with app.app_context():
        contact = Contact(
            name='Jan Kowalski',
            phone='+48 123 456 789',
            email='jan@example.com',
            company='Test Company',
            source_file='test.csv'
        )
        
        db.session.add(contact)
        db.session.commit()
        
        assert contact.id is not None
        assert contact.name == 'Jan Kowalski'
        assert contact.phone == '+48 123 456 789'
        assert contact.email == 'jan@example.com'
        assert contact.company == 'Test Company'
        assert contact.source_file == 'test.csv'
        assert contact.is_active == True

def test_call_creation(app):
    """Test call model creation"""
    with app.app_context():
        # Create contact first
        contact = Contact(
            name='Jan Kowalski',
            phone='+48 123 456 789',
            email='jan@example.com'
        )
        db.session.add(contact)
        db.session.commit()
        
        # Create user (ankieter)
        ankieter = User(
            email='ankieter@test.com',
            password_hash='test_hash',
            role='ankieter'
        )
        db.session.add(ankieter)
        db.session.commit()
        
        # Create call
        call = Call(
            contact_id=contact.id,
            ankieter_id=ankieter.id,
            call_date='2024-01-01 10:00:00',
            status='interested',
            priority='high',
            notes='Very interested in our services',
            duration_minutes=15
        )
        
        db.session.add(call)
        db.session.commit()
        
        assert call.id is not None
        assert call.contact_id == contact.id
        assert call.ankieter_id == ankieter.id
        assert call.status == 'interested'
        assert call.priority == 'high'
        assert call.notes == 'Very interested in our services'
        assert call.duration_minutes == 15

def test_call_queue_creation(app):
    """Test call queue model creation"""
    with app.app_context():
        # Create contact first
        contact = Contact(
            name='Jan Kowalski',
            phone='+48 123 456 789',
            email='jan@example.com'
        )
        db.session.add(contact)
        db.session.commit()
        
        # Create call entry
        call_entry = Call(
            contact_id=contact.id,
            ankieter_id=1,  # Assuming user with ID 1 exists
            priority='high',
            scheduled_date=datetime(2024, 1, 1, 10, 0, 0),
            queue_status='pending',
            call_date=datetime.utcnow()
        )
        
        db.session.add(call_entry)
        db.session.commit()
        
        assert call_entry.id is not None
        assert call_entry.contact_id == contact.id
        assert call_entry.priority == 'high'
        assert call_entry.queue_status == 'pending'

def test_import_file_creation(app):
    """Test import file model creation"""
    with app.app_context():
        # Create user first
        user = User(
            email='admin@test.com',
            password_hash='test_hash',
            role='admin'
        )
        db.session.add(user)
        db.session.commit()
        
        # Create import file
        import_file = ImportFile(
            filename='contacts.csv',
            file_size=1024,
            file_type='csv',
            total_rows=55,
            processed_rows=50,
            import_status='completed',
            imported_by=user.id
        )
        
        db.session.add(import_file)
        db.session.commit()
        
        assert import_file.id is not None
        assert import_file.filename == 'contacts.csv'
        assert import_file.file_size == 1024
        assert import_file.total_rows == 55
        assert import_file.processed_rows == 50
        assert import_file.import_status == 'completed'
        assert import_file.imported_by == user.id

def test_contact_relationships(app):
    """Test contact relationships"""
    with app.app_context():
        # Create contact
        contact = Contact(
            name='Jan Kowalski',
            phone='+48 123 456 789',
            email='jan@example.com'
        )
        db.session.add(contact)
        db.session.commit()
        
        # Create user
        ankieter = User(
            email='ankieter@test.com',
            password_hash='test_hash',
            role='ankieter'
        )
        db.session.add(ankieter)
        db.session.commit()
        
        # Create call
        call = Call(
            contact_id=contact.id,
            ankieter_id=ankieter.id,
            call_date='2024-01-01 10:00:00',
            status='interested'
        )
        db.session.add(call)
        db.session.commit()
        
        # Test relationships
        assert len(contact.calls) == 1
        assert contact.calls[0].id == call.id
        assert call.contact.id == contact.id
        assert call.ankieter.id == ankieter.id
