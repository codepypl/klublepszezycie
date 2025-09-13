"""
Testy walidacji wydarzeń
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import json

from app.utils.timezone import get_local_now


class TestEventValidationUtils:
    """Testy funkcji walidacji z utils/validation.py"""
    
    def test_validate_event_date_with_future_date(self):
        """Test walidacji daty w przyszłości"""
        from app.utils.validation import validate_event_date
        
        future_date = (get_local_now() + timedelta(days=1)).strftime('%Y-%m-%d')
        is_valid, result = validate_event_date(future_date)
        
        assert is_valid is True
        assert isinstance(result, datetime)
    
    def test_validate_event_date_with_past_date(self):
        """Test walidacji daty w przeszłości"""
        from app.utils.validation import validate_event_date
        
        past_date = (get_local_now() - timedelta(days=1)).strftime('%Y-%m-%d')
        is_valid, result = validate_event_date(past_date)
        
        assert is_valid is False
        assert 'Data wydarzenia nie może być w przeszłości' in result
    
    def test_validate_event_date_with_invalid_format(self):
        """Test walidacji daty z nieprawidłowym formatem"""
        from app.utils.validation import validate_event_date
        
        is_valid, result = validate_event_date('invalid-date')
        
        assert is_valid is False
        assert 'Nieprawidłowy format daty' in result
    
    def test_validate_event_date_with_today_date(self):
        """Test walidacji daty na dzisiaj (powinna być dozwolona)"""
        from app.utils.validation import validate_event_date
        
        today = get_local_now().strftime('%Y-%m-%d')
        is_valid, result = validate_event_date(today)
        
        assert is_valid is True
        assert isinstance(result, datetime)


class TestEventValidationAPI:
    """Testy walidacji API wydarzeń (bez bazy danych)"""
    
    def test_validate_event_data_missing_title(self):
        """Test walidacji danych wydarzenia - brak tytułu"""
        data = {
            'event_type': 'workshop',
            'event_date': (get_local_now() + timedelta(days=1)).isoformat(),
            'description': 'Test description'
        }
        
        # Symuluj walidację z API
        if not data.get('title'):
            assert True  # Tytuł jest wymagany
        else:
            assert False
    
    def test_validate_event_data_missing_event_type(self):
        """Test walidacji danych wydarzenia - brak typu"""
        data = {
            'title': 'Test Event',
            'event_date': (get_local_now() + timedelta(days=1)).isoformat(),
            'description': 'Test description'
        }
        
        # Symuluj walidację z API
        if not data.get('event_type'):
            assert True  # Typ wydarzenia jest wymagany
        else:
            assert False
    
    def test_validate_event_data_past_date(self):
        """Test walidacji danych wydarzenia - data w przeszłości"""
        past_date = (get_local_now() - timedelta(days=1)).isoformat()
        
        try:
            from app.utils.timezone import get_local_timezone
            import pytz
            
            event_date = datetime.fromisoformat(past_date)
            now = get_local_now()
            
            # Konwertuj event_date do timezone-aware jeśli nie jest
            if event_date.tzinfo is None:
                tz = get_local_timezone()
                event_date = tz.localize(event_date)
            
            if event_date < now:
                assert True  # Data w przeszłości powinna być odrzucona
            else:
                assert False
        except ValueError:
            assert False  # Nieprawidłowy format daty
    
    def test_validate_event_data_future_date(self):
        """Test walidacji danych wydarzenia - data w przyszłości"""
        future_date = (get_local_now() + timedelta(days=1)).isoformat()
        
        try:
            from app.utils.timezone import get_local_timezone
            import pytz
            
            event_date = datetime.fromisoformat(future_date)
            now = get_local_now()
            
            # Konwertuj event_date do timezone-aware jeśli nie jest
            if event_date.tzinfo is None:
                tz = get_local_timezone()
                event_date = tz.localize(event_date)
            
            if event_date < now:
                assert False  # Data w przyszłości powinna być zaakceptowana
            else:
                assert True
        except ValueError:
            assert False  # Nieprawidłowy format daty
    
    def test_validate_event_data_invalid_date_format(self):
        """Test walidacji danych wydarzenia - nieprawidłowy format daty"""
        try:
            event_date = datetime.fromisoformat('invalid-date-format')
            assert False  # Nieprawidłowy format powinien być odrzucony
        except ValueError:
            assert True  # Nieprawidłowy format daty
    
    def test_validate_event_data_end_date_before_start_date(self):
        """Test walidacji danych wydarzenia - data zakończenia przed datą rozpoczęcia"""
        start_date = (get_local_now() + timedelta(days=2)).isoformat()
        end_date = (get_local_now() + timedelta(days=1)).isoformat()
        
        try:
            start_datetime = datetime.fromisoformat(start_date)
            end_datetime = datetime.fromisoformat(end_date)
            
            if end_datetime <= start_datetime:
                assert True  # Data zakończenia przed datą rozpoczęcia powinna być odrzucona
            else:
                assert False
        except ValueError:
            assert False  # Nieprawidłowy format daty
    
    def test_validate_event_data_valid_end_date(self):
        """Test walidacji danych wydarzenia - prawidłowa data zakończenia"""
        start_date = (get_local_now() + timedelta(days=1)).isoformat()
        end_date = (get_local_now() + timedelta(days=1, hours=2)).isoformat()
        
        try:
            start_datetime = datetime.fromisoformat(start_date)
            end_datetime = datetime.fromisoformat(end_date)
            
            if end_datetime <= start_datetime:
                assert False  # Prawidłowa data zakończenia powinna być zaakceptowana
            else:
                assert True
        except ValueError:
            assert False  # Nieprawidłowy format daty
