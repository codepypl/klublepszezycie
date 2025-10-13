"""
Testy dla DashboardStatsService
"""
import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock

from app import create_app
from app.models import db, User
from app.models.crm_model import Call, Contact, Campaign
from app.models.stats_model import Stats
from app.services.dashboard_stats_service import DashboardStatsService


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def service():
    """Create DashboardStatsService instance"""
    return DashboardStatsService()


@pytest.fixture
def ankieter(app):
    """Create test ankieter user"""
    with app.app_context():
        user = User(
            first_name='Jan',
            email='ankieter@test.pl',
            password_hash='test',
            account_type='ankieter',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def campaign(app):
    """Create test campaign"""
    with app.app_context():
        campaign = Campaign(
            name='Test Campaign',
            is_active=True
        )
        db.session.add(campaign)
        db.session.commit()
        return campaign.id


class TestDashboardStatsService:
    """Test suite for DashboardStatsService"""
    
    def test_get_empty_stats(self, app, service, ankieter):
        """Test getting stats when no data exists"""
        with app.app_context():
            today = date.today()
            stats = service.get_stats_for_ankieter(ankieter, today)
            
            assert stats is not None
            assert stats['leads_today'] == 0
            assert stats['calls_total_today'] == 0
            assert stats['calls_connected_today'] == 0
            assert stats['calls_missed_today'] == 0
            assert stats['total_call_time_today'] == 0
            assert stats['average_call_time_today'] == 0
            assert stats['total_contacts'] == 0
            assert stats['total_rescheduled'] == 0
            assert stats['active_campaigns'] == 0
    
    def test_database_stats_leads(self, app, service, ankieter, campaign):
        """Test counting leads from database"""
        with app.app_context():
            # Create contact
            contact = Contact(
                name='Test Contact',
                phone='+48123456789',
                campaign_id=campaign,
                assigned_ankieter_id=ankieter
            )
            db.session.add(contact)
            db.session.commit()
            
            # Create lead call
            call = Call(
                contact_id=contact.id,
                ankieter_id=ankieter,
                campaign_id=campaign,
                call_date=datetime.now(),
                status='lead',
                duration=120
            )
            db.session.add(call)
            db.session.commit()
            
            # Get stats
            today = date.today()
            stats = service._get_database_stats(ankieter, today)
            
            assert stats['leads_today'] == 1
    
    def test_database_stats_contacts(self, app, service, ankieter, campaign):
        """Test counting total contacts"""
        with app.app_context():
            # Create 3 contacts
            for i in range(3):
                contact = Contact(
                    name=f'Contact {i}',
                    phone=f'+4812345678{i}',
                    campaign_id=campaign,
                    assigned_ankieter_id=ankieter,
                    is_active=True
                )
                db.session.add(contact)
            db.session.commit()
            
            # Get stats
            today = date.today()
            stats = service._get_database_stats(ankieter, today)
            
            assert stats['total_contacts'] == 3
    
    def test_database_stats_rescheduled(self, app, service, ankieter, campaign):
        """Test counting rescheduled contacts"""
        with app.app_context():
            # Create rescheduled contacts
            for i in range(2):
                contact = Contact(
                    name=f'Rescheduled {i}',
                    phone=f'+4891234567{i}',
                    campaign_id=campaign,
                    assigned_ankieter_id=ankieter,
                    business_reason='przełożenie'
                )
                db.session.add(contact)
            
            # Create normal contact
            contact = Contact(
                name='Normal Contact',
                phone='+48999888777',
                campaign_id=campaign,
                assigned_ankieter_id=ankieter
            )
            db.session.add(contact)
            db.session.commit()
            
            # Get stats
            today = date.today()
            stats = service._get_database_stats(ankieter, today)
            
            assert stats['total_rescheduled'] == 2
    
    def test_update_stats_after_call_lead(self, app, service, ankieter, campaign):
        """Test updating Stats after lead call"""
        with app.app_context():
            # Create contact and call
            contact = Contact(
                name='Test Lead',
                phone='+48111222333',
                campaign_id=campaign,
                assigned_ankieter_id=ankieter
            )
            db.session.add(contact)
            db.session.commit()
            
            call = Call(
                contact_id=contact.id,
                ankieter_id=ankieter,
                campaign_id=campaign,
                call_date=datetime.now(),
                status='lead',
                duration=180
            )
            db.session.add(call)
            db.session.commit()
            
            # Update stats
            result = service.update_stats_after_call(call.id)
            
            assert result is True
            
            # Check if stats were saved
            today = date.today()
            leads_stat = Stats.get_value(
                stat_type='ankieter_leads_daily',
                related_id=ankieter,
                related_type='ankieter',
                date_period=today
            )
            
            assert leads_stat == 1
    
    def test_twilio_stats_with_mock(self, app, service, ankieter, campaign):
        """Test getting Twilio stats with mocked Twilio API"""
        with app.app_context():
            # Create contact
            contact = Contact(
                name='Twilio Test',
                phone='+48555666777',
                campaign_id=campaign,
                assigned_ankieter_id=ankieter
            )
            db.session.add(contact)
            db.session.commit()
            
            # Create call with Twilio SID
            call = Call(
                contact_id=contact.id,
                ankieter_id=ankieter,
                campaign_id=campaign,
                call_date=datetime.now(),
                status='completed',
                twilio_sid='CA123456789',
                duration=240
            )
            db.session.add(call)
            db.session.commit()
            
            # Mock Twilio API response
            mock_twilio_response = {
                'sid': 'CA123456789',
                'status': 'completed',
                'duration': 240,
                'start_time': datetime.now().isoformat(),
                'end_time': datetime.now().isoformat(),
                'from_number': '+48000000000',
                'to_number': '+48555666777',
                'price': -0.05,
                'price_unit': 'USD',
                'direction': 'outbound-api'
            }
            
            # Patch Twilio service
            with patch.object(service.twilio_service, 'get_call_details', return_value=mock_twilio_response):
                today = date.today()
                stats = service._get_twilio_stats(ankieter, today)
                
                assert stats['calls_total_today'] == 1
                assert stats['calls_connected_today'] == 1
                assert stats['calls_missed_today'] == 0
                assert stats['total_call_time_today'] == 240
                assert stats['average_call_time_today'] == 240.0
    
    def test_active_campaigns_count(self, app, service, ankieter):
        """Test counting active campaigns"""
        with app.app_context():
            # Create 2 active campaigns
            for i in range(2):
                campaign = Campaign(
                    name=f'Active Campaign {i}',
                    is_active=True
                )
                db.session.add(campaign)
            
            # Create 1 inactive campaign
            campaign = Campaign(
                name='Inactive Campaign',
                is_active=False
            )
            db.session.add(campaign)
            db.session.commit()
            
            # Get stats
            today = date.today()
            stats = service._get_database_stats(ankieter, today)
            
            assert stats['active_campaigns'] == 2
    
    def test_stats_saved_to_stats_table(self, app, service, ankieter, campaign):
        """Test if stats are saved to Stats table"""
        with app.app_context():
            # Create lead call
            contact = Contact(
                name='Stats Test',
                phone='+48444555666',
                campaign_id=campaign,
                assigned_ankieter_id=ankieter
            )
            db.session.add(contact)
            db.session.commit()
            
            call = Call(
                contact_id=contact.id,
                ankieter_id=ankieter,
                campaign_id=campaign,
                call_date=datetime.now(),
                status='lead'
            )
            db.session.add(call)
            db.session.commit()
            
            # Get stats (this should save to Stats table)
            today = date.today()
            stats = service._get_database_stats(ankieter, today)
            
            # Verify stats were saved
            stat_entry = Stats.query.filter_by(
                stat_type='ankieter_leads_daily',
                related_id=ankieter,
                related_type='ankieter',
                date_period=today
            ).first()
            
            assert stat_entry is not None
            assert stat_entry.stat_value == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])





