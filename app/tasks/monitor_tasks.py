"""
Monitor Tasks - zadania do monitorowania zmian w czasie rzeczywistym
"""
from datetime import datetime
from celery import current_app as celery
from app.services.event_monitor import EventMonitorService
import logging

logger = logging.getLogger(__name__)

@celery.task(bind=True, name='monitor_event_changes')
def monitor_event_changes_task(self):
    """
    Zadanie do monitorowania zmian wydarzeń i aktualizacji kolejki emaili
    """
    try:
        logger.info("🔄 Rozpoczynam monitorowanie zmian wydarzeń...")
        
        monitor = EventMonitorService()
        result = monitor.monitor_event_changes()
        
        if result['success']:
            logger.info(f"✅ Monitorowanie zakończone: {result['updated_count']} zaktualizowanych, {result['error_count']} błędów")
        else:
            logger.error(f"❌ Błąd monitorowania: {result.get('error', 'Nieznany błąd')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Błąd zadania monitorowania wydarzeń: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@celery.task(bind=True, name='monitor_member_changes')
def monitor_member_changes_task(self):
    """
    Zadanie do monitorowania zmian w członkach klubu i uczestnikach
    """
    try:
        logger.info("🔄 Rozpoczynam monitorowanie zmian członków...")
        
        monitor = EventMonitorService()
        result = monitor.monitor_member_changes()
        
        if result['success']:
            logger.info(f"✅ Monitorowanie członków zakończone: {len(result.get('updated_events', []))} zaktualizowanych wydarzeń")
        else:
            logger.error(f"❌ Błąd monitorowania członków: {result.get('error', 'Nieznany błąd')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Błąd zadania monitorowania członków: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@celery.task(bind=True, name='full_system_monitor')
def full_system_monitor_task(self):
    """
    Kompleksowe monitorowanie całego systemu
    """
    try:
        logger.info("🔄 Rozpoczynam pełne monitorowanie systemu...")
        
        monitor = EventMonitorService()
        
        # Monitoruj zmiany wydarzeń
        event_result = monitor.monitor_event_changes()
        
        # Monitoruj zmiany członków
        member_result = monitor.monitor_member_changes()
        
        # Połącz wyniki
        result = {
            'success': event_result['success'] and member_result['success'],
            'event_monitoring': event_result,
            'member_monitoring': member_result,
            'timestamp': datetime.now().isoformat()
        }
        
        if result['success']:
            logger.info("✅ Pełne monitorowanie zakończone pomyślnie")
        else:
            logger.error("❌ Błędy podczas pełnego monitorowania")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Błąd pełnego monitorowania: {e}")
        return {
            'success': False,
            'error': str(e)
        }
