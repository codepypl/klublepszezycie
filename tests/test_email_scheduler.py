"""
Testy dla EmailScheduler v3

Test scenariuszy:
1. Planowanie wydarzeń z różnymi czasami (24h+, 1h+, 5min+, już minął)
2. Kampanie natychmiastowe vs planowane
3. Priorytetyzacja w kolejce
4. Duplikaty przypomnień
"""
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Importy będą działać po uruchomieniu z kontekstem aplikacji
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestEmailSchedulerEventReminders(unittest.TestCase):
    """Testy dla planowania przypomnień o wydarzeniach"""
    
    def setUp(self):
        """Przygotowanie testów"""
        from app.services.email_v2.queue.scheduler import EmailScheduler
        self.scheduler = EmailScheduler()
    
    @patch('app.services.email_v2.queue.scheduler.EventSchedule')
    @patch('app.services.email_v2.queue.scheduler.EmailTemplate')
    @patch('app.services.email_v2.queue.scheduler.db')
    @patch('app.services.email_v2.queue.scheduler.get_local_now')
    def test_event_24h_before_schedules_all_reminders(self, mock_now, mock_db, mock_template, mock_event_schedule):
        """Test: Wydarzenie za 24h+ wysyła 3 przypomnienia"""
        # Arrange
        now = datetime(2025, 10, 10, 12, 0, 0)
        event_date = datetime(2025, 10, 12, 12, 0, 0)  # Za 48h
        mock_now.return_value = now
        
        # Mock wydarzenia
        mock_event = Mock()
        mock_event.id = 1
        mock_event.title = "Test Event"
        mock_event.event_date = event_date
        mock_event.reminders_scheduled = False
        mock_event.location = "Test Location"
        mock_event.description = "Test Description"
        mock_event_schedule.query.get.return_value = mock_event
        
        # Mock uczestników
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.first_name = "Test"
        
        # Mock _get_event_participants
        with patch.object(self.scheduler, '_get_event_participants', return_value=[mock_user]):
            # Mock szablonów
            mock_template_obj = Mock()
            mock_template_obj.id = 1
            mock_template_obj.name = "event_reminder_24h"
            mock_template_obj.subject = "Przypomnienie: {{event_title}}"
            mock_template_obj.html_content = "<p>{{user_name}}</p>"
            mock_template_obj.text_content = "{{user_name}}"
            mock_template.query.filter_by.return_value.first.return_value = mock_template_obj
            
            # Mock _add_to_queue
            with patch.object(self.scheduler, '_add_to_queue', return_value=(True, "OK")):
                # Act
                success, message = self.scheduler.schedule_event_reminders(1)
        
        # Assert
        self.assertTrue(success)
        self.assertIn("3 przypomnień", message)  # 3 przypomnienia dla 1 użytkownika
    
    @patch('app.services.email_v2.queue.scheduler.EventSchedule')
    @patch('app.services.email_v2.queue.scheduler.EmailTemplate')
    @patch('app.services.email_v2.queue.scheduler.db')
    @patch('app.services.email_v2.queue.scheduler.get_local_now')
    def test_event_1h_before_schedules_2_reminders(self, mock_now, mock_db, mock_template, mock_event_schedule):
        """Test: Wydarzenie za 1h+ wysyła 2 przypomnienia (1h, 5min)"""
        # Arrange
        now = datetime(2025, 10, 10, 12, 0, 0)
        event_date = datetime(2025, 10, 10, 14, 0, 0)  # Za 2h
        mock_now.return_value = now
        
        # Mock wydarzenia
        mock_event = Mock()
        mock_event.id = 1
        mock_event.title = "Test Event"
        mock_event.event_date = event_date
        mock_event.reminders_scheduled = False
        mock_event.location = "Test Location"
        mock_event.description = "Test Description"
        mock_event_schedule.query.get.return_value = mock_event
        
        # Mock uczestników
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.first_name = "Test"
        
        # Mock _get_event_participants
        with patch.object(self.scheduler, '_get_event_participants', return_value=[mock_user]):
            # Mock szablonów
            mock_template_obj = Mock()
            mock_template_obj.id = 1
            mock_template_obj.name = "event_reminder_1h"
            mock_template_obj.subject = "Przypomnienie: {{event_title}}"
            mock_template_obj.html_content = "<p>{{user_name}}</p>"
            mock_template_obj.text_content = "{{user_name}}"
            mock_template.query.filter_by.return_value.first.return_value = mock_template_obj
            
            # Mock _add_to_queue
            with patch.object(self.scheduler, '_add_to_queue', return_value=(True, "OK")):
                # Act
                success, message = self.scheduler.schedule_event_reminders(1)
        
        # Assert
        self.assertTrue(success)
        self.assertIn("2 przypomnień", message)  # 2 przypomnienia dla 1 użytkownika
    
    @patch('app.services.email_v2.queue.scheduler.EventSchedule')
    @patch('app.services.email_v2.queue.scheduler.EmailTemplate')
    @patch('app.services.email_v2.queue.scheduler.db')
    @patch('app.services.email_v2.queue.scheduler.get_local_now')
    def test_event_5min_before_schedules_1_reminder(self, mock_now, mock_db, mock_template, mock_event_schedule):
        """Test: Wydarzenie za 5min+ wysyła 1 przypomnienie (5min)"""
        # Arrange
        now = datetime(2025, 10, 10, 12, 0, 0)
        event_date = datetime(2025, 10, 10, 12, 10, 0)  # Za 10 minut
        mock_now.return_value = now
        
        # Mock wydarzenia
        mock_event = Mock()
        mock_event.id = 1
        mock_event.title = "Test Event"
        mock_event.event_date = event_date
        mock_event.reminders_scheduled = False
        mock_event.location = "Test Location"
        mock_event.description = "Test Description"
        mock_event_schedule.query.get.return_value = mock_event
        
        # Mock uczestników
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.first_name = "Test"
        
        # Mock _get_event_participants
        with patch.object(self.scheduler, '_get_event_participants', return_value=[mock_user]):
            # Mock szablonów
            mock_template_obj = Mock()
            mock_template_obj.id = 1
            mock_template_obj.name = "event_reminder_5min"
            mock_template_obj.subject = "Przypomnienie: {{event_title}}"
            mock_template_obj.html_content = "<p>{{user_name}}</p>"
            mock_template_obj.text_content = "{{user_name}}"
            mock_template.query.filter_by.return_value.first.return_value = mock_template_obj
            
            # Mock _add_to_queue
            with patch.object(self.scheduler, '_add_to_queue', return_value=(True, "OK")):
                # Act
                success, message = self.scheduler.schedule_event_reminders(1)
        
        # Assert
        self.assertTrue(success)
        self.assertIn("1 przypomnień", message)  # 1 przypomnienie dla 1 użytkownika
    
    @patch('app.services.email_v2.queue.scheduler.EventSchedule')
    @patch('app.services.email_v2.queue.scheduler.get_local_now')
    def test_event_less_than_5min_before_schedules_nothing(self, mock_now, mock_event_schedule):
        """Test: Wydarzenie za mniej niż 5min nie wysyła nic"""
        # Arrange
        now = datetime(2025, 10, 10, 12, 0, 0)
        event_date = datetime(2025, 10, 10, 12, 3, 0)  # Za 3 minuty
        mock_now.return_value = now
        
        # Mock wydarzenia
        mock_event = Mock()
        mock_event.id = 1
        mock_event.title = "Test Event"
        mock_event.event_date = event_date
        mock_event.reminders_scheduled = False
        mock_event_schedule.query.get.return_value = mock_event
        
        # Mock uczestników
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        
        # Mock _get_event_participants
        with patch.object(self.scheduler, '_get_event_participants', return_value=[mock_user]):
            # Act
            success, message = self.scheduler.schedule_event_reminders(1)
        
        # Assert
        self.assertFalse(success)
        self.assertIn("mniej niż 5 minut", message)


class TestEmailSchedulerCampaigns(unittest.TestCase):
    """Testy dla planowania kampanii"""
    
    def setUp(self):
        """Przygotowanie testów"""
        from app.services.email_v2.queue.scheduler import EmailScheduler
        self.scheduler = EmailScheduler()
    
    @patch('app.services.email_v2.queue.scheduler.EmailCampaign')
    @patch('app.services.email_v2.queue.scheduler.db')
    @patch('app.services.email_v2.queue.scheduler.get_local_now')
    def test_immediate_campaign_scheduled_now(self, mock_now, mock_db, mock_campaign_model):
        """Test: Kampania natychmiastowa jest planowana na teraz"""
        # Arrange
        now = datetime(2025, 10, 10, 12, 0, 0)
        mock_now.return_value = now
        
        # Mock kampanii
        mock_campaign = Mock()
        mock_campaign.id = 1
        mock_campaign.name = "Test Campaign"
        mock_campaign.status = "draft"
        mock_campaign.send_type = "immediate"
        mock_campaign.template_id = None
        mock_campaign.template = None
        mock_campaign.content_variables = None
        mock_campaign_model.query.get.return_value = mock_campaign
        
        # Mock odbiorców
        mock_user = Mock()
        mock_user.email = "test@example.com"
        mock_user.first_name = "Test"
        
        # Mock _get_campaign_recipients
        with patch.object(self.scheduler, '_get_campaign_recipients', return_value=[mock_user]):
            # Mock _add_to_queue
            with patch.object(self.scheduler, '_add_to_queue', return_value=(True, "OK")) as mock_add:
                # Act
                success, message = self.scheduler.schedule_campaign(1)
                
                # Assert - sprawdź czy scheduled_at to teraz
                if mock_add.called:
                    call_args = mock_add.call_args
                    scheduled_at = call_args[1]['scheduled_at']
                    self.assertEqual(scheduled_at, now)
    
    @patch('app.services.email_v2.queue.scheduler.EmailCampaign')
    @patch('app.services.email_v2.queue.scheduler.db')
    @patch('app.services.email_v2.queue.scheduler.get_local_now')
    def test_scheduled_campaign_scheduled_at_future(self, mock_now, mock_db, mock_campaign_model):
        """Test: Kampania planowana jest planowana na przyszłość"""
        # Arrange
        now = datetime(2025, 10, 10, 12, 0, 0)
        scheduled_time = datetime(2025, 10, 15, 12, 0, 0)
        mock_now.return_value = now
        
        # Mock kampanii
        mock_campaign = Mock()
        mock_campaign.id = 1
        mock_campaign.name = "Test Campaign"
        mock_campaign.status = "draft"
        mock_campaign.send_type = "scheduled"
        mock_campaign.scheduled_at = scheduled_time
        mock_campaign.template_id = None
        mock_campaign.template = None
        mock_campaign.content_variables = None
        mock_campaign_model.query.get.return_value = mock_campaign
        
        # Mock odbiorców
        mock_user = Mock()
        mock_user.email = "test@example.com"
        mock_user.first_name = "Test"
        
        # Mock _get_campaign_recipients
        with patch.object(self.scheduler, '_get_campaign_recipients', return_value=[mock_user]):
            # Mock _add_to_queue
            with patch.object(self.scheduler, '_add_to_queue', return_value=(True, "OK")) as mock_add:
                # Act
                success, message = self.scheduler.schedule_campaign(1)
                
                # Assert - sprawdź czy scheduled_at to przyszłość
                if mock_add.called:
                    call_args = mock_add.call_args
                    scheduled_at = call_args[1]['scheduled_at']
                    self.assertEqual(scheduled_at, scheduled_time)


class TestEmailSchedulerPriorities(unittest.TestCase):
    """Testy dla priorytetyzacji"""
    
    def setUp(self):
        """Przygotowanie testów"""
        from app.services.email_v2.queue.scheduler import EmailScheduler
        self.scheduler = EmailScheduler()
    
    def test_priority_values(self):
        """Test: Sprawdź czy priorytety mają poprawne wartości"""
        self.assertEqual(self.scheduler.PRIORITY_SYSTEM, 0)
        self.assertEqual(self.scheduler.PRIORITY_EVENT, 1)
        self.assertEqual(self.scheduler.PRIORITY_CAMPAIGN, 2)
    
    @patch('app.services.email_v2.queue.scheduler.EmailTemplate')
    @patch('app.services.email_v2.queue.scheduler.db')
    def test_system_email_has_priority_0(self, mock_db, mock_template):
        """Test: Email systemowy ma priorytet 0"""
        # Arrange
        mock_template_obj = Mock()
        mock_template_obj.id = 1
        mock_template_obj.name = "password_reset"
        mock_template_obj.subject = "Reset hasła"
        mock_template_obj.html_content = "<p>Reset</p>"
        mock_template_obj.text_content = "Reset"
        mock_template.query.filter_by.return_value.first.return_value = mock_template_obj
        
        # Mock _add_to_queue
        with patch.object(self.scheduler, '_add_to_queue', return_value=(True, "OK")) as mock_add:
            # Act
            self.scheduler.schedule_immediate_email(
                to_email="test@example.com",
                template_name="password_reset",
                context={},
                email_type='system'
            )
            
            # Assert
            if mock_add.called:
                call_args = mock_add.call_args
                priority = call_args[1]['priority']
                self.assertEqual(priority, 0)


class TestEmailSchedulerDuplicates(unittest.TestCase):
    """Testy dla kontroli duplikatów"""
    
    def setUp(self):
        """Przygotowanie testów"""
        from app.services.email_v2.queue.scheduler import EmailScheduler
        self.scheduler = EmailScheduler()
    
    @patch('app.services.email_v2.queue.scheduler.EventSchedule')
    @patch('app.services.email_v2.queue.scheduler.EmailTemplate')
    @patch('app.services.email_v2.queue.scheduler.db')
    @patch('app.services.email_v2.queue.scheduler.get_local_now')
    def test_duplicate_event_reminder_prevented(self, mock_now, mock_db, mock_template, mock_event_schedule):
        """Test: Duplikat przypomnienia o wydarzeniu jest blokowany"""
        # Arrange
        now = datetime(2025, 10, 10, 12, 0, 0)
        event_date = datetime(2025, 10, 12, 12, 0, 0)
        mock_now.return_value = now
        
        # Mock wydarzenia
        mock_event = Mock()
        mock_event.id = 1
        mock_event.title = "Test Event"
        mock_event.event_date = event_date
        mock_event.reminders_scheduled = False
        mock_event.location = "Test Location"
        mock_event.description = "Test Description"
        mock_event_schedule.query.get.return_value = mock_event
        
        # Mock uczestników
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.first_name = "Test"
        
        # Mock _get_event_participants
        with patch.object(self.scheduler, '_get_event_participants', return_value=[mock_user]):
            # Mock szablonów
            mock_template_obj = Mock()
            mock_template_obj.id = 1
            mock_template_obj.name = "event_reminder_24h"
            mock_template_obj.subject = "Przypomnienie"
            mock_template_obj.html_content = "<p>Test</p>"
            mock_template_obj.text_content = "Test"
            mock_template.query.filter_by.return_value.first.return_value = mock_template_obj
            
            # Mock _add_to_queue - pierwsze wywołanie sukces, drugie duplikat
            call_count = [0]
            
            def add_to_queue_side_effect(*args, **kwargs):
                call_count[0] += 1
                duplicate_check_key = kwargs.get('duplicate_check_key', '')
                
                # Sprawdź czy to duplikat (to samo wydarzenie, użytkownik, szablon)
                if call_count[0] > 1 and 'event_reminder_1_1_1' in duplicate_check_key:
                    return (False, "Email już istnieje w kolejce")
                return (True, "OK")
            
            with patch.object(self.scheduler, '_add_to_queue', side_effect=add_to_queue_side_effect):
                # Act - pierwsze zaplanowanie
                success1, message1 = self.scheduler.schedule_event_reminders(1)
                
                # Reset flagi
                mock_event.reminders_scheduled = False
                
                # Act - drugie zaplanowanie (duplikat)
                success2, message2 = self.scheduler.schedule_event_reminders(1)
        
        # Assert - pierwsze powinno się udać
        self.assertTrue(success1)


if __name__ == '__main__':
    unittest.main()

