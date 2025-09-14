"""
Tests for timeline functionality
"""
import pytest
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models import EventSchedule, Section


class TestTimeline:
    """Test cases for timeline functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_app(self):
        """Setup test application"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        with self.app.app_context():
            db.create_all()
            yield self.app
            db.session.remove()
            db.drop_all()
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return self.app.test_client()
    
    def create_test_events(self):
        """Create test events for timeline testing"""
        now = datetime.now()
        
        # Create first event (will be shown in hero)
        event1 = EventSchedule(
            title="Najbliższe Wydarzenie",
            event_type="prezentacja",
            event_date=now + timedelta(days=1),
            description="To jest najbliższe wydarzenie",
            location="Online",
            is_active=True,
            is_published=True
        )
        
        # Create second event (will be shown in timeline)
        event2 = EventSchedule(
            title="Drugie Wydarzenie",
            event_type="webinar",
            event_date=now + timedelta(days=7),
            description="To jest drugie wydarzenie w timeline",
            location="Warszawa",
            is_active=True,
            is_published=True
        )
        
        # Create third event (will be shown in timeline)
        event3 = EventSchedule(
            title="Trzecie Wydarzenie",
            event_type="spotkanie",
            event_date=now + timedelta(days=14),
            description="To jest trzecie wydarzenie w timeline",
            location="Kraków",
            is_active=True,
            is_published=True
        )
        
        # Create unpublished event (should not appear)
        event4 = EventSchedule(
            title="Nieopublikowane Wydarzenie",
            event_type="inne",
            event_date=now + timedelta(days=21),
            description="To wydarzenie nie powinno się pokazać",
            location="Gdańsk",
            is_active=True,
            is_published=False  # Not published
        )
        
        db.session.add_all([event1, event2, event3, event4])
        db.session.commit()
        
        return [event1, event2, event3, event4]
    
    def test_timeline_shows_only_published_events(self, client):
        """Test that timeline shows only published events"""
        events = self.create_test_events()
        
        response = client.get('/')
        assert response.status_code == 200
        
        # Check that timeline section appears (should have 2 events in timeline)
        assert b'events-timeline' in response.data
        assert 'Nadchodzące Wydarzenia'.encode('utf-8') in response.data
        
        # Check that timeline shows only published events
        assert 'Drugie Wydarzenie'.encode('utf-8') in response.data
        assert 'Trzecie Wydarzenie'.encode('utf-8') in response.data
        assert 'Nieopublikowane Wydarzenie'.encode('utf-8') not in response.data
    
    def test_timeline_excludes_first_event(self, client):
        """Test that timeline excludes the first (closest) event"""
        events = self.create_test_events()
        
        response = client.get('/')
        assert response.status_code == 200
        
        # First event should not be in timeline (it's shown in hero)
        assert 'Najbliższe Wydarzenie'.encode('utf-8') not in response.data or response.data.count('Najbliższe Wydarzenie'.encode('utf-8')) == 1
    
    def test_timeline_not_shown_with_one_event(self, client):
        """Test that timeline is not shown when there's only one event"""
        now = datetime.now()
        
        # Create only one event
        event = EventSchedule(
            title="Jedno Wydarzenie",
            event_type="prezentacja",
            event_date=now + timedelta(days=1),
            description="To jest jedyne wydarzenie",
            location="Online",
            is_active=True,
            is_published=True
        )
        
        db.session.add(event)
        db.session.commit()
        
        response = client.get('/')
        assert response.status_code == 200
        
        # Timeline section should not appear
        assert b'events-timeline' not in response.data
    
    def test_timeline_shows_event_details(self, client):
        """Test that timeline shows correct event details"""
        events = self.create_test_events()
        
        response = client.get('/')
        assert response.status_code == 200
        
        # Check event details in timeline
        assert 'Drugie Wydarzenie'.encode('utf-8') in response.data
        assert b'webinar' in response.data
        assert 'To jest drugie wydarzenie w timeline'.encode('utf-8') in response.data
        assert 'Warszawa'.encode('utf-8') in response.data
    
    def test_timeline_event_registration_form(self, client):
        """Test that timeline events have registration forms"""
        events = self.create_test_events()
        
        response = client.get('/')
        assert response.status_code == 200
        
        # Check for registration form elements
        assert b'event-registration-form' in response.data
        assert 'Zapisz się'.encode('utf-8') in response.data
        assert 'Twoje imię'.encode('utf-8') in response.data
        assert 'Twój email'.encode('utf-8') in response.data
    
    def test_timeline_css_classes(self, client):
        """Test that timeline has correct CSS classes"""
        events = self.create_test_events()
        
        response = client.get('/')
        assert response.status_code == 200
        
        # Check for timeline CSS classes
        assert b'timeline' in response.data
        assert b'timeline-item' in response.data
        assert b'timeline-marker' in response.data
        assert b'timeline-content' in response.data
    
    def test_timeline_event_types(self, client):
        """Test that different event types are displayed correctly"""
        events = self.create_test_events()
        
        response = client.get('/')
        assert response.status_code == 200
        
        # Check that different event types are shown
        assert b'webinar' in response.data
        assert b'spotkanie' in response.data
    
    def test_timeline_event_dates_format(self, client):
        """Test that event dates are formatted correctly in timeline"""
        events = self.create_test_events()
        
        response = client.get('/')
        assert response.status_code == 200
        
        # Check for date formatting (should contain dots for Polish format)
        assert b'fas fa-calendar-alt' in response.data
        assert b'fas fa-clock' in response.data
    
    def test_timeline_meeting_links(self, client):
        """Test that meeting links are displayed when available"""
        now = datetime.now()
        
        # Create event with meeting link
        event = EventSchedule(
            title="Wydarzenie z linkiem",
            event_type="webinar",
            event_date=now + timedelta(days=7),
            description="Wydarzenie z linkiem do spotkania",
            location="Online",
            meeting_link="https://zoom.us/j/123456789",
            is_active=True,
            is_published=True
        )
        
        # Create another event without meeting link
        event2 = EventSchedule(
            title="Wydarzenie bez linku",
            event_type="prezentacja",
            event_date=now + timedelta(days=14),
            description="Wydarzenie bez linku",
            location="Warszawa",
            is_active=True,
            is_published=True
        )
        
        db.session.add_all([event, event2])
        db.session.commit()
        
        response = client.get('/')
        assert response.status_code == 200
        
        # Check that meeting link is shown when available
        assert 'Dołącz do spotkania'.encode('utf-8') in response.data
        assert b'https://zoom.us/j/123456789' in response.data
    
    def test_timeline_ordering(self, client):
        """Test that timeline events are ordered by date"""
        now = datetime.now()
        
        # Create events in random order
        event3 = EventSchedule(
            title="Trzecie Wydarzenie",
            event_type="spotkanie",
            event_date=now + timedelta(days=21),
            description="To jest trzecie wydarzenie",
            location="Kraków",
            is_active=True,
            is_published=True
        )
        
        event1 = EventSchedule(
            title="Pierwsze Wydarzenie",
            event_type="prezentacja",
            event_date=now + timedelta(days=7),
            description="To jest pierwsze wydarzenie",
            location="Warszawa",
            is_active=True,
            is_published=True
        )
        
        event2 = EventSchedule(
            title="Drugie Wydarzenie",
            event_type="webinar",
            event_date=now + timedelta(days=14),
            description="To jest drugie wydarzenie",
            location="Gdańsk",
            is_active=True,
            is_published=True
        )
        
        db.session.add_all([event3, event1, event2])
        db.session.commit()
        
        response = client.get('/')
        assert response.status_code == 200
        
        # Check that events appear in chronological order in timeline
        content = response.data.decode('utf-8')
        
        # Find positions of event titles in the timeline section
        timeline_start = content.find('events-timeline')
        timeline_end = content.find('cta', timeline_start)
        timeline_content = content[timeline_start:timeline_end]
        
        pos_first = timeline_content.find('Pierwsze Wydarzenie')
        pos_second = timeline_content.find('Drugie Wydarzenie')
        pos_third = timeline_content.find('Trzecie Wydarzenie')
        
        # First should come before second, second before third
        assert pos_first < pos_second < pos_third


if __name__ == '__main__':
    pytest.main([__file__])
