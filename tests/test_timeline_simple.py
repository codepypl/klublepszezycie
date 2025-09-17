"""
Simple tests for timeline functionality using existing database
"""
import pytest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import EventSchedule


class TestTimelineSimple:
    """Simple test cases for timeline functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_app(self):
        """Setup test application using existing database"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        with self.app.app_context():
            yield self.app
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return self.app.test_client()
    
    def test_timeline_exists_when_multiple_events(self, client):
        """Test that timeline section exists when there are multiple events"""
        response = client.get('/')
        assert response.status_code == 200
        
        # Check if timeline section exists
        content = response.data.decode('utf-8')
        
        # Count active published events
        with self.app.app_context():
            events_count = EventSchedule.query.filter_by(
                is_active=True, 
                is_published=True
            ).count()
        
        if events_count > 1:
            # Timeline should exist
            assert 'events-timeline' in content
            assert 'Nadchodzące Wydarzenia' in content
        else:
            # Timeline should not exist
            assert 'events-timeline' not in content
    
    def test_timeline_structure(self, client):
        """Test that timeline has correct HTML structure"""
        response = client.get('/')
        assert response.status_code == 200
        
        content = response.data.decode('utf-8')
        
        # Check if timeline exists
        if 'events-timeline' in content:
            # Check for timeline components
            assert 'timeline' in content
            assert 'timeline-item' in content
            assert 'timeline-marker' in content
            assert 'timeline-content' in content
            assert 'event-registration-form' in content
    
    def test_timeline_events_have_forms(self, client):
        """Test that timeline events have registration forms"""
        response = client.get('/')
        assert response.status_code == 200
        
        content = response.data.decode('utf-8')
        
        if 'events-timeline' in content:
            # Check for form elements
            assert 'Zapisz się' in content
            assert 'Twoje imię' in content
            assert 'Twój email' in content
    
    def test_timeline_position_between_about_cta(self, client):
        """Test that timeline is positioned between about and CTA sections"""
        response = client.get('/')
        assert response.status_code == 200
        
        content = response.data.decode('utf-8')
        
        if 'events-timeline' in content:
            # Find positions
            about_pos = content.find('id="about"')
            timeline_pos = content.find('id="events-timeline"')
            cta_pos = content.find('id="cta"')
            
            # Timeline should be between about and CTA
            if about_pos != -1 and cta_pos != -1:
                assert about_pos < timeline_pos < cta_pos
    
    def test_timeline_css_styles_exist(self, client):
        """Test that timeline CSS styles are loaded"""
        response = client.get('/')
        assert response.status_code == 200
        
        content = response.data.decode('utf-8')
        
        # Check for CSS file inclusion
        assert 'style.css' in content
        
        # Check for Bootstrap and other dependencies
        assert 'bootstrap' in content
        assert 'font-awesome' in content or 'fontawesome' in content


if __name__ == '__main__':
    pytest.main([__file__])

