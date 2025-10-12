"""
Twilio VoIP Service for CRM Agent Calls
Provides cloud-based VoIP calling functionality
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from flask import request, jsonify

logger = logging.getLogger(__name__)

class TwilioVoIPService:
    """Service for handling VoIP calls through Twilio"""
    
    def __init__(self):
        # Twilio credentials from environment
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')  # Twilio number
        
        if not all([self.account_sid, self.auth_token, self.phone_number]):
            logger.warning("⚠️ Twilio credentials not configured")
            self.client = None
        else:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("✅ Twilio VoIP service initialized")
    
    def is_configured(self) -> bool:
        """Check if Twilio is properly configured"""
        return self.client is not None
    
    def make_call(self, to_number: str, agent_id: int, contact_id: int) -> Dict[str, Any]:
        """
        Make an outbound call through Twilio
        
        Args:
            to_number: Phone number to call (with country code, e.g., +48123456789)
            agent_id: ID of the agent making the call
            contact_id: ID of the contact being called
            
        Returns:
            Dict with call status and details
        """
        try:
            if not self.is_configured():
                return {
                    'success': False,
                    'error': 'Twilio nie jest skonfigurowane'
                }
            
            # Validate phone number
            if not to_number.startswith('+'):
                to_number = '+48' + to_number  # Default to Poland if no country code
            
            logger.info(f"📞 Making Twilio call to {to_number} for agent {agent_id}")
            
            # Create call through Twilio
            call = self.client.calls.create(
                to=to_number,
                from_=self.phone_number,
                url=f"{self._get_webhook_url()}/api/voip/twilio/voice",
                method='POST',
                status_callback=f"{self._get_webhook_url()}/api/voip/twilio/status",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                status_callback_method='POST'
            )
            
            logger.info(f"✅ Twilio call initiated with SID: {call.sid}")
            
            return {
                'success': True,
                'call_sid': call.sid,
                'status': call.status,
                'to_number': to_number,
                'from_number': self.phone_number,
                'agent_id': agent_id,
                'contact_id': contact_id,
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Twilio call error: {e}")
            
            # Check for specific Twilio errors
            if "21215" in error_msg or "geo-permissions" in error_msg:
                error_msg = "Błąd uprawnień geograficznych. Sprawdź ustawienia w konsoli Twilio: https://www.twilio.com/console/voice/calls/geo-permissions"
            elif "21205" in error_msg:
                error_msg = "Błąd URL webhook. Sprawdź APP_BASE_URL w .env"
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def get_call_status(self, call_sid: str) -> Dict[str, Any]:
        """Get current status of a call"""
        try:
            if not self.is_configured():
                return {'success': False, 'error': 'Twilio nie jest skonfigurowane'}
            
            call = self.client.calls(call_sid).fetch()
            
            return {
                'success': True,
                'call_sid': call.sid,
                'status': call.status,
                'direction': call.direction,
                'duration': call.duration,
                'start_time': call.start_time.isoformat() if call.start_time else None,
                'end_time': call.end_time.isoformat() if call.end_time else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting call status: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_calls_by_date_range(self, start_date: datetime, end_date: datetime, phone_number: str = None) -> Dict[str, Any]:
        """Get calls from Twilio for a specific date range"""
        try:
            if not self.is_configured():
                return {'success': False, 'error': 'Twilio nie jest skonfigurowane'}
            
            # Convert datetime to Twilio format
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            # Build filter parameters
            filters = {
                'start_time_after': start_date_str,
                'start_time_before': end_date_str
            }
            
            if phone_number:
                filters['to'] = phone_number
            
            # Fetch calls from Twilio
            calls = self.client.calls.list(**filters)
            
            call_data = []
            for call in calls:
                call_info = {
                    'sid': call.sid,
                    'status': call.status,
                    'direction': call.direction,
                    'from': call.from_,
                    'to': call.to,
                    'duration': call.duration,
                    'start_time': call.start_time.isoformat() if call.start_time else None,
                    'end_time': call.end_time.isoformat() if call.end_time else None,
                    'price': call.price,
                    'price_unit': call.price_unit
                }
                call_data.append(call_info)
            
            return {
                'success': True,
                'calls': call_data,
                'total_count': len(call_data)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting calls from Twilio: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_daily_call_stats(self, date) -> Dict[str, Any]:
        """Get daily call statistics from Twilio"""
        try:
            if not self.is_configured():
                return {'success': False, 'error': 'Twilio nie jest skonfigurowane'}
            
            # Convert date to datetime if needed
            if hasattr(date, 'date'):  # If it's already a datetime
                date_obj = date
            else:  # If it's a date object
                date_obj = datetime.combine(date, datetime.min.time())
            
            # Get start and end of day
            start_date = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = date_obj.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            result = self.get_calls_by_date_range(start_date, end_date)
            
            if not result['success']:
                return result
            
            calls = result['calls']
            
            # Calculate statistics
            total_calls = len(calls)
            completed_calls = len([c for c in calls if c['status'] == 'completed'])
            failed_calls = len([c for c in calls if c['status'] == 'failed'])
            busy_calls = len([c for c in calls if c['status'] == 'busy'])
            no_answer_calls = len([c for c in calls if c['status'] == 'no-answer'])
            
            # Calculate total duration
            total_duration = sum(c['duration'] for c in calls if c['duration'] is not None)
            
            # Calculate average duration
            avg_duration = total_duration / completed_calls if completed_calls > 0 else 0
            
            # Find longest call
            longest_call = max(calls, key=lambda x: x['duration'] or 0) if calls else None
            longest_duration = longest_call['duration'] if longest_call else 0
            
            return {
                'success': True,
                'date': date.strftime('%Y-%m-%d'),
                'total_calls': total_calls,
                'completed_calls': completed_calls,
                'failed_calls': failed_calls,
                'busy_calls': busy_calls,
                'no_answer_calls': no_answer_calls,
                'total_duration_seconds': total_duration,
                'average_duration_seconds': avg_duration,
                'longest_call_seconds': longest_duration,
                'calls': calls  # Raw call data for detailed analysis
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting daily call stats from Twilio: {e}")
            return {'success': False, 'error': str(e)}
    
    def end_call(self, call_sid: str) -> Dict[str, Any]:
        """End an active call"""
        try:
            if not self.is_configured():
                return {'success': False, 'error': 'Twilio nie jest skonfigurowane'}
            
            call = self.client.calls(call_sid).update(status='completed')
            
            return {
                'success': True,
                'call_sid': call.sid,
                'status': call.status
            }
            
        except Exception as e:
            logger.error(f"❌ Error ending call: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_call_details(self, call_sid: str) -> Dict[str, Any]:
        """
        Pobiera szczegóły połączenia z Twilio API
        
        Args:
            call_sid: Twilio Call SID
            
        Returns:
            Dict z szczegółami połączenia (status, duration, timestamps, etc.)
        """
        try:
            if not self.is_configured():
                return {}
            
            call = self.client.calls(call_sid).fetch()
            
            return {
                'sid': call.sid,
                'status': call.status,
                'duration': int(call.duration or 0),
                'start_time': call.start_time.isoformat() if call.start_time else None,
                'end_time': call.end_time.isoformat() if call.end_time else None,
                'from_number': call.from_,
                'to_number': call.to,
                'price': float(call.price) if call.price else 0.0,
                'price_unit': call.price_unit,
                'direction': call.direction
            }
        except Exception as e:
            logger.error(f"❌ Error fetching call details for {call_sid}: {e}")
            return {}
    
    def get_call_recording(self, call_sid: str) -> Dict[str, Any]:
        """Get recording URL for a call (if available)"""
        try:
            if not self.is_configured():
                return {'success': False, 'error': 'Twilio nie jest skonfigurowane'}
            
            recordings = self.client.recordings.list(call_sid=call_sid)
            
            if recordings:
                recording = recordings[0]
                return {
                    'success': True,
                    'recording_url': f"https://api.twilio.com{recording.uri}",
                    'duration': recording.duration,
                    'format': recording.channels
                }
            else:
                return {'success': False, 'error': 'Brak nagrania'}
                
        except Exception as e:
            logger.error(f"❌ Error getting recording: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_webhook_url(self) -> str:
        """Get the webhook URL for Twilio callbacks"""
        base_url = os.getenv('APP_BASE_URL', 'http://localhost:5000')
        webhook_url = base_url.rstrip('/')
        logger.info(f"🔗 Twilio webhook URL: {webhook_url}")
        return webhook_url
    
    def generate_twiml_for_agent(self, agent_name: str = "Agent") -> str:
        """
        Generate TwiML for agent side of the call
        This is what the agent hears when they pick up
        """
        response = VoiceResponse()
        
        # Say hello to agent
        response.say(f"Dzień dobry {agent_name}, zostałeś połączony z klientem.", language='pl')
        
        # Play some background music or hold music
        response.play('https://demo.twilio.com/docs/classic.mp3')
        
        return str(response)
    
    def generate_twiml_for_customer(self) -> str:
        """
        Generate TwiML for customer side of the call
        This is what the customer hears
        """
        response = VoiceResponse()
        
        # Say hello to customer
        response.say("Dzień dobry, dzwonię z Klubu Lepsze Życie. Proszę czekać na połączenie z naszym doradcą.", language='pl')
        
        # Play hold music
        response.play('https://demo.twilio.com/docs/classic.mp3')
        
        return str(response)

# Global instance
twilio_service = TwilioVoIPService()
