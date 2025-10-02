"""
Cron-based email scheduling system
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from croniter import croniter
import pytz

from app import db
from app.models import EmailCampaign, EmailQueue
from app.utils.timezone_utils import get_local_now

class CronScheduler:
    """Advanced cron-based scheduler for email campaigns"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.default_timezone = pytz.timezone('Europe/Warsaw')
    
    def schedule_campaign_with_cron(self, campaign_id: int, cron_expression: str,
                                   timezone: str = 'Europe/Warsaw',
                                   start_date: datetime = None,
                                   end_date: datetime = None) -> Tuple[bool, str, List[datetime]]:
        """
        Schedule campaign using cron expression
        
        Args:
            campaign_id: Campaign ID
            cron_expression: Cron expression (e.g., "0 9 * * 1-5" for weekdays at 9 AM)
            timezone: Timezone name
            start_date: Start date for scheduling
            end_date: End date for scheduling
            
        Returns:
            Tuple[bool, str, List[datetime]]: (success, message, scheduled_dates)
        """
        try:
            # Validate campaign
            campaign = EmailCampaign.query.get(campaign_id)
            if not campaign:
                return False, "Kampania nie została znaleziona", []
            
            # Validate cron expression
            if not self.validate_cron_expression(cron_expression):
                return False, "Nieprawidłowe wyrażenie cron", []
            
            # Get timezone
            try:
                tz = pytz.timezone(timezone)
            except:
                tz = self.default_timezone
            
            # Calculate next scheduled dates
            scheduled_dates = self.calculate_next_runs(
                cron_expression, 
                start_date or get_local_now(),
                end_date,
                limit=10,
                timezone=tz
            )
            
            if not scheduled_dates:
                return False, "Nie znaleziono terminów wysyłki", []
            
            # Update campaign with cron schedule
            campaign.send_type = 'cron'
            campaign.scheduled_at = scheduled_dates[0]
            db.session.commit()
            
            self.logger.info(f"✅ Zaplanowano kampanię {campaign_id} z cron: {cron_expression}")
            return True, f"Zaplanowano {len(scheduled_dates)} wysyłek", scheduled_dates
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"❌ Błąd planowania kampanii z cron: {e}")
            return False, f"Błąd planowania: {str(e)}", []
    
    def validate_cron_expression(self, cron_expression: str) -> bool:
        """
        Validate cron expression syntax
        
        Args:
            cron_expression: Cron expression to validate
            
        Returns:
            bool: True if valid
        """
        try:
            croniter(cron_expression)
            return True
        except Exception as e:
            self.logger.error(f"❌ Nieprawidłowe wyrażenie cron: {e}")
            return False
    
    def calculate_next_runs(self, cron_expression: str, start_date: datetime,
                           end_date: datetime = None, limit: int = 10,
                           timezone: pytz.timezone = None) -> List[datetime]:
        """
        Calculate next run times based on cron expression
        
        Args:
            cron_expression: Cron expression
            start_date: Start date
            end_date: End date (optional)
            limit: Maximum number of runs to calculate
            timezone: Timezone
            
        Returns:
            List[datetime]: List of scheduled run times
        """
        try:
            tz = timezone or self.default_timezone
            
            # Make start_date timezone-aware
            if start_date.tzinfo is None:
                start_date = tz.localize(start_date)
            else:
                start_date = start_date.astimezone(tz)
            
            # Create croniter instance
            cron = croniter(cron_expression, start_date)
            
            scheduled_dates = []
            for _ in range(limit):
                next_run = cron.get_next(datetime)
                
                # Check if within end_date
                if end_date and next_run > end_date:
                    break
                
                scheduled_dates.append(next_run)
            
            return scheduled_dates
            
        except Exception as e:
            self.logger.error(f"❌ Błąd obliczania terminów: {e}")
            return []
    
    def get_next_run_time(self, cron_expression: str, base_time: datetime = None,
                         timezone: str = 'Europe/Warsaw') -> Optional[datetime]:
        """
        Get next run time for cron expression
        
        Args:
            cron_expression: Cron expression
            base_time: Base time (default: now)
            timezone: Timezone name
            
        Returns:
            Optional[datetime]: Next run time
        """
        try:
            tz = pytz.timezone(timezone)
            base = base_time or get_local_now()
            
            if base.tzinfo is None:
                base = tz.localize(base)
            else:
                base = base.astimezone(tz)
            
            cron = croniter(cron_expression, base)
            return cron.get_next(datetime)
            
        except Exception as e:
            self.logger.error(f"❌ Błąd pobierania następnego terminu: {e}")
            return None
    
    def get_cron_description(self, cron_expression: str, locale: str = 'pl') -> str:
        """
        Get human-readable description of cron expression
        
        Args:
            cron_expression: Cron expression
            locale: Locale for description
            
        Returns:
            str: Human-readable description
        """
        try:
            # Basic cron patterns
            patterns = {
                '* * * * *': 'Co minutę',
                '0 * * * *': 'Co godzinę',
                '0 0 * * *': 'Codziennie o północy',
                '0 9 * * *': 'Codziennie o 9:00',
                '0 12 * * *': 'Codziennie o 12:00',
                '0 18 * * *': 'Codziennie o 18:00',
                '0 9 * * 1-5': 'W dni robocze o 9:00',
                '0 9 * * 1': 'W poniedziałki o 9:00',
                '0 0 1 * *': 'Pierwszego dnia miesiąca o północy',
                '0 0 * * 0': 'W niedziele o północy',
            }
            
            if cron_expression in patterns:
                return patterns[cron_expression]
            
            # Parse cron expression
            parts = cron_expression.split()
            if len(parts) != 5:
                return cron_expression
            
            minute, hour, day, month, weekday = parts
            
            description = []
            
            # Minute
            if minute == '*':
                description.append('co minutę')
            elif minute == '0':
                pass  # On the hour
            else:
                description.append(f'o minucie {minute}')
            
            # Hour
            if hour == '*':
                if minute != '*':
                    description.append('co godzinę')
            else:
                description.append(f'o {hour}:00')
            
            # Day
            if day != '*':
                description.append(f'{day} dnia miesiąca')
            
            # Month
            if month != '*':
                months = {
                    '1': 'stycznia', '2': 'lutego', '3': 'marca',
                    '4': 'kwietnia', '5': 'maja', '6': 'czerwca',
                    '7': 'lipca', '8': 'sierpnia', '9': 'września',
                    '10': 'października', '11': 'listopada', '12': 'grudnia'
                }
                description.append(f'w {months.get(month, month)}')
            
            # Weekday
            if weekday != '*':
                weekdays = {
                    '0': 'w niedziele', '1': 'w poniedziałki', '2': 'we wtorki',
                    '3': 'w środy', '4': 'w czwartki', '5': 'w piątki',
                    '6': 'w soboty', '1-5': 'w dni robocze', '0,6': 'w weekendy'
                }
                description.append(weekdays.get(weekday, f'w dzień tygodnia {weekday}'))
            
            return ' '.join(description).capitalize() if description else cron_expression
            
        except Exception as e:
            self.logger.error(f"❌ Błąd generowania opisu cron: {e}")
            return cron_expression
    
    def get_common_cron_patterns(self) -> List[Dict[str, str]]:
        """
        Get common cron patterns with descriptions
        
        Returns:
            List[Dict[str, str]]: List of common patterns
        """
        return [
            {
                'expression': '0 9 * * 1-5',
                'description': 'W dni robocze o 9:00',
                'category': 'daily'
            },
            {
                'expression': '0 18 * * 1-5',
                'description': 'W dni robocze o 18:00',
                'category': 'daily'
            },
            {
                'expression': '0 9 * * *',
                'description': 'Codziennie o 9:00',
                'category': 'daily'
            },
            {
                'expression': '0 12 * * *',
                'description': 'Codziennie o 12:00',
                'category': 'daily'
            },
            {
                'expression': '0 9 * * 1',
                'description': 'W poniedziałki o 9:00',
                'category': 'weekly'
            },
            {
                'expression': '0 9 * * 5',
                'description': 'W piątki o 9:00',
                'category': 'weekly'
            },
            {
                'expression': '0 9 1 * *',
                'description': 'Pierwszego dnia miesiąca o 9:00',
                'category': 'monthly'
            },
            {
                'expression': '0 9 15 * *',
                'description': '15. dnia miesiąca o 9:00',
                'category': 'monthly'
            },
            {
                'expression': '0 9 1 1 *',
                'description': '1. stycznia o 9:00',
                'category': 'yearly'
            },
            {
                'expression': '0 */2 * * *',
                'description': 'Co 2 godziny',
                'category': 'hourly'
            }
        ]




