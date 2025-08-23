"""
Calendar Integration Service
Handles integration with Google Calendar, Outlook, and Apple Calendar
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import pytz
from config import config


class CalendarService:
    def __init__(self):
        self.google_config = {
            'client_id': config.get('GOOGLE_CALENDAR_CLIENT_ID', ''),
            'client_secret': config.get('GOOGLE_CALENDAR_CLIENT_SECRET', ''),
            'api_key': config.get('GOOGLE_CALENDAR_API_KEY', ''),
            'calendar_id': config.get('GOOGLE_CALENDAR_CALENDAR_ID', 'primary')
        }
        
        self.outlook_config = {
            'client_id': config.get('OUTLOOK_CLIENT_ID', ''),
            'client_secret': config.get('OUTLOOK_CLIENT_SECRET', ''),
            'tenant_id': config.get('OUTLOOK_TENANT_ID', '')
        }
        
        self.ical_config = {
            'timezone': config.get('ICAL_TIMEZONE', 'Europe/Warsaw'),
            'organizer': config.get('ICAL_ORGANIZER', 'noreply@lepszezycie.pl'),
            'organizer_name': config.get('ICAL_ORGANIZER_NAME', 'Klub Lepsze Życie')
        }
    
    def create_google_calendar_event(self, event_data: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Tworzy wydarzenie w Google Calendar
        
        Args:
            event_data: Dane wydarzenia
            
        Returns:
            (success, event_id, error_message)
        """
        if not all([self.google_config['client_id'], self.google_config['client_secret'], self.google_config['api_key']]):
            return False, None, "Brak konfiguracji Google Calendar"
        
        try:
            # Format daty dla Google Calendar API
            start_time = event_data['event_date'].isoformat() + 'Z'
            end_time = (event_data.get('end_date') or event_data['event_date'] + timedelta(hours=1)).isoformat() + 'Z'
            
            event_body = {
                'summary': event_data['title'],
                'description': event_data.get('description', ''),
                'start': {
                    'dateTime': start_time,
                    'timeZone': self.ical_config['timezone']
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': self.ical_config['timezone']
                },
                'location': event_data.get('location', 'Online'),
                'organizer': {
                    'email': self.ical_config['organizer'],
                    'displayName': self.ical_config['organizer_name']
                }
            }
            
            if event_data.get('meeting_link'):
                event_body['conferenceData'] = {
                    'createRequest': {
                        'requestId': f"meet_{event_data['id']}_{int(datetime.now().timestamp())}",
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        }
                    }
                }
            
            # W rzeczywistej implementacji użyj Google Calendar API
            # Na razie zwracamy symulację
            event_id = f"google_event_{event_data['id']}_{int(datetime.now().timestamp())}"
            return True, event_id, None
            
        except Exception as e:
            return False, None, f"Błąd Google Calendar: {str(e)}"
    
    def create_outlook_event(self, event_data: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Tworzy wydarzenie w Outlook/Office 365
        
        Args:
            event_data: Dane wydarzenia
            
        Returns:
            (success, event_id, error_message)
        """
        if not all([self.outlook_config['client_id'], self.outlook_config['client_secret'], self.outlook_config['tenant_id']]):
            return False, None, "Brak konfiguracji Outlook"
        
        try:
            # Format daty dla Microsoft Graph API
            start_time = event_data['event_date'].isoformat() + 'Z'
            end_time = (event_data.get('end_date') or event_data['event_date'] + timedelta(hours=1)).isoformat() + 'Z'
            
            event_body = {
                'subject': event_data['title'],
                'body': {
                    'contentType': 'HTML',
                    'content': event_data.get('description', '')
                },
                'start': {
                    'dateTime': start_time,
                    'timeZone': self.ical_config['timezone']
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': self.ical_config['timezone']
                },
                'location': {
                    'displayName': event_data.get('location', 'Online')
                },
                'isOnlineMeeting': bool(event_data.get('meeting_link')),
                'onlineMeeting': {
                    'joinUrl': event_data.get('meeting_link', '')
                } if event_data.get('meeting_link') else None
            }
            
            # W rzeczywistej implementacji użyj Microsoft Graph API
            # Na razie zwracamy symulację
            event_id = f"outlook_event_{event_data['id']}_{int(datetime.now().timestamp())}"
            return True, event_id, None
            
        except Exception as e:
            return False, None, f"Błąd Outlook: {str(e)}"
    
    def generate_ical_file(self, event_data: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Generuje plik iCal dla Apple Calendar i innych aplikacji
        
        Args:
            event_data: Dane wydarzenia
            
        Returns:
            (success, ical_content, error_message)
        """
        try:
            # Generuj unikalny UID
            ical_uid = f"event_{event_data['id']}_{int(datetime.now().timestamp())}@lepszezycie.pl"
            
            # Ustaw datę zakończenia
            end_time = event_data.get('end_date') or (event_data['event_date'] + timedelta(hours=1))
            
            # Formatuj daty dla iCal
            start_str = event_data['event_date'].strftime('%Y%m%dT%H%M%SZ')
            end_str = end_time.strftime('%Y%m%dT%H%M%SZ')
            now_str = datetime.now().strftime('%Y%m%dT%H%M%SZ')
            
            # Generuj zawartość iCal
            ical_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Klub Lepsze Życie//Wydarzenie//PL
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:{ical_uid}
DTSTAMP:{now_str}
DTSTART:{start_str}
DTEND:{end_str}
SUMMARY:{event_data['title']}
DESCRIPTION:{event_data.get('description', 'Wydarzenie klubu Lepsze Życie').replace(chr(10), '\\n')}
LOCATION:{event_data.get('location', 'Online')}
URL:{event_data.get('meeting_link', '')}
STATUS:CONFIRMED
SEQUENCE:0
ORGANIZER;CN={self.ical_config['organizer_name']}:mailto:{self.ical_config['organizer']}
END:VEVENT
END:VCALENDAR"""
            
            return True, ical_content, None
            
        except Exception as e:
            return False, None, f"Błąd generowania iCal: {str(e)}"
    
    def create_calendar_links(self, event_data: Dict) -> Dict[str, str]:
        """
        Generuje linki do dodania wydarzenia do różnych kalendarzy
        
        Args:
            event_data: Dane wydarzenia
            
        Returns:
            Słownik z linkami do kalendarzy
        """
        try:
            # Format daty dla linków
            start_time = event_data['event_date'].strftime('%Y%m%dT%H%M%SZ')
            end_time = (event_data.get('end_date') or event_data['event_date'] + timedelta(hours=1)).strftime('%Y%m%dT%H%M%SZ')
            
            # Google Calendar
            google_link = (
                "https://calendar.google.com/calendar/render?"
                f"action=TEMPLATE&text={event_data['title'].replace(' ', '+')}&"
                f"dates={start_time}/{end_time}&"
                f"details={event_data.get('description', '').replace(' ', '+')}&"
                f"location={event_data.get('location', 'Online').replace(' ', '+')}"
            )
            
            # Outlook/Office 365
            outlook_link = (
                "https://outlook.office.com/calendar/0/deeplink/compose?"
                f"subject={event_data['title'].replace(' ', '%20')}&"
                f"startdt={start_time}&"
                f"enddt={end_time}&"
                f"body={event_data.get('description', '').replace(' ', '%20')}&"
                f"location={event_data.get('location', 'Online').replace(' ', '%20')}"
            )
            
            # Yahoo Calendar
            yahoo_link = (
                "https://calendar.yahoo.com/?v=60&view=d&type=20&"
                f"title={event_data['title'].replace(' ', '%20')}&"
                f"st={start_time}&"
                f"et={end_time}&"
                f"desc={event_data.get('description', '').replace(' ', '%20')}&"
                f"in_loc={event_data.get('location', 'Online').replace(' ', '%20')}"
            )
            
            return {
                'google': google_link,
                'outlook': outlook_link,
                'yahoo': yahoo_link
            }
            
        except Exception as e:
            return {}
    
    def sync_event_to_calendars(self, event_data: Dict) -> Dict[str, Tuple[bool, Optional[str], Optional[str]]]:
        """
        Synchronizuje wydarzenie ze wszystkimi skonfigurowanymi kalendarzami
        
        Args:
            event_data: Dane wydarzenia
            
        Returns:
            Słownik z wynikami synchronizacji dla każdego kalendarza
        """
        results = {}
        
        # Google Calendar
        if self.google_config['client_id']:
            results['google'] = self.create_google_calendar_event(event_data)
        
        # Outlook
        if self.outlook_config['client_id']:
            results['outlook'] = self.create_outlook_event(event_data)
        
        # iCal (zawsze dostępny)
        results['ical'] = self.generate_ical_file(event_data)
        
        return results


# Instancja globalna
calendar_service = CalendarService()
