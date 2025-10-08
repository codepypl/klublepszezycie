"""
Email data validators
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from flask import request
import json
import re


class EmailValidator:
    """Walidator danych emaili"""
    
    @staticmethod
    def validate_template_data(data: Dict) -> Tuple[bool, str]:
        """Waliduje dane szablonu emaila"""
        if not data.get('name') or not data['name'].strip():
            return False, 'Nazwa szablonu jest wymagana'
        
        if not data.get('subject') or not data['subject'].strip():
            return False, 'Temat szablonu jest wymagany'
        
        if not data.get('html_content') or not data['html_content'].strip():
            return False, 'Treść HTML jest wymagana'
        
        # Walidacja nazwy szablonu (tylko litery, cyfry, podkreślenia, myślniki)
        if not re.match(r'^[a-zA-Z0-9_-]+$', data['name']):
            return False, 'Nazwa szablonu może zawierać tylko litery, cyfry, podkreślenia i myślniki'
        
        return True, 'OK'
    
    @staticmethod
    def validate_campaign_data(data: Dict) -> Tuple[bool, str]:
        """Waliduje dane kampanii emailowej"""
        if not data.get('name') or not data['name'].strip():
            return False, 'Nazwa kampanii jest wymagana'
        
        if not data.get('subject') or not data['subject'].strip():
            return False, 'Temat kampanii jest wymagany'
        
        if not data.get('recipient_groups') or not isinstance(data['recipient_groups'], list) or len(data['recipient_groups']) == 0:
            return False, 'Musisz wybrać co najmniej jedną grupę odbiorców'
        
        if not data.get('template_id') or data['template_id'] == '' or data['template_id'] == 'null':
            return False, 'Musisz wybrać szablon emaila'
        
        return True, 'OK'
    
    @staticmethod
    def validate_scheduled_time(scheduled_at: str) -> Tuple[bool, str, Optional[datetime]]:
        """Waliduje i parsuje czas wysyłki"""
        if not scheduled_at:
            return True, 'OK', None
        
        try:
            from app.utils.timezone_utils import get_local_timezone, get_local_now
            
            # Parse date from frontend
            if 'T' in scheduled_at and '+' not in scheduled_at and 'Z' not in scheduled_at:
                # Format: "2025-09-28T15:30" (bez timezone) - interpretuj jako czas lokalny
                naive_time = datetime.fromisoformat(scheduled_at)
                local_tz = get_local_timezone()
                scheduled_datetime = local_tz.localize(naive_time)
            else:
                # Format z timezone: "2025-09-28T15:30Z" lub "2025-09-28T15:30+02:00"
                scheduled_datetime = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
            
            # Sprawdź czy data jest w przyszłości
            now = get_local_now()
            if now.tzinfo is None:
                now = now.replace(tzinfo=get_local_timezone())
            if scheduled_datetime.tzinfo is None:
                scheduled_datetime = scheduled_datetime.replace(tzinfo=get_local_timezone())
            
            if scheduled_datetime <= now:
                return False, 'Data wysyłki musi być w przyszłości', None
            
            return True, 'OK', scheduled_datetime
            
        except ValueError as e:
            return False, f'Nieprawidłowy format daty: {str(e)}', None
        except Exception as e:
            return False, f'Błąd parsowania daty: {str(e)}', None
    
    @staticmethod
    def validate_recipient_groups(groups: List[int]) -> Tuple[bool, str]:
        """Waliduje grupy odbiorców"""
        if not groups:
            return False, 'Musisz wybrać co najmniej jedną grupę odbiorców'
        
        if not isinstance(groups, list):
            return False, 'Grupy odbiorców muszą być listą'
        
        if len(groups) == 0:
            return False, 'Musisz wybrać co najmniej jedną grupę odbiorców'
        
        # Sprawdź czy wszystkie ID są liczbami
        for group_id in groups:
            if not isinstance(group_id, int) or group_id <= 0:
                return False, 'Nieprawidłowe ID grupy odbiorców'
        
        return True, 'OK'
    
    @staticmethod
    def validate_content_variables(variables: Dict) -> Tuple[bool, str]:
        """Waliduje zmienne treści"""
        if not variables:
            return True, 'OK'
        
        if not isinstance(variables, dict):
            return False, 'Zmienne treści muszą być słownikiem'
        
        # Sprawdź czy wszystkie wartości są stringami
        for key, value in variables.items():
            if not isinstance(key, str) or not isinstance(value, str):
                return False, 'Wszystkie klucze i wartości zmiennych muszą być tekstem'
        
        return True, 'OK'


class CampaignStatusValidator:
    """Walidator statusów kampanii"""
    
    VALID_STATUSES = ['draft', 'ready', 'scheduled', 'sending', 'sent', 'completed', 'cancelled']
    TRANSITION_RULES = {
        'draft': ['ready', 'cancelled'],
        'ready': ['sending', 'scheduled', 'cancelled'],
        'scheduled': ['sending', 'ready', 'cancelled'],
        'sending': ['sent', 'completed', 'cancelled'],
        'sent': ['completed'],
        'completed': [],  # Status końcowy
        'cancelled': []   # Status końcowy
    }
    
    @classmethod
    def is_valid_status(cls, status: str) -> bool:
        """Sprawdza czy status jest prawidłowy"""
        return status in cls.VALID_STATUSES
    
    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        """Sprawdza czy przejście między statusami jest dozwolone"""
        if not cls.is_valid_status(from_status) or not cls.is_valid_status(to_status):
            return False
        
        return to_status in cls.TRANSITION_RULES.get(from_status, [])
    
    @classmethod
    def get_allowed_transitions(cls, current_status: str) -> List[str]:
        """Zwraca listę dozwolonych przejść z obecnego statusu"""
        return cls.TRANSITION_RULES.get(current_status, [])
