"""
Celery Cleanup Service - anulowanie zadań Celery związanych z wydarzeniami
"""
import logging
from celery_app import celery

logger = logging.getLogger(__name__)

class CeleryCleanupService:
    """Serwis do czyszczenia zadań Celery"""
    
    @staticmethod
    def cancel_event_tasks(event_id):
        """
        Anuluje wszystkie zaplanowane zadania Celery związane z wydarzeniem
        
        Args:
            event_id (int): ID wydarzenia
            
        Returns:
            int: Liczba anulowanych zadań
        """
        try:
            cancelled_count = 0
            
            # Pobierz wszystkie zaplanowane zadania
            scheduled_tasks = celery.control.inspect().scheduled()
            
            if not scheduled_tasks:
                logger.info(f"Brak zaplanowanych zadań do anulowania dla wydarzenia {event_id}")
                return 0
            
            # Przejdź przez wszystkich workerów
            for worker, tasks in scheduled_tasks.items():
                for task in tasks:
                    task_name = task.get('request', {}).get('name', '')
                    task_args = task.get('request', {}).get('args', [])
                    task_id = task.get('request', {}).get('id')
                    
                    # Sprawdź czy zadanie dotyczy tego wydarzenia
                    if CeleryCleanupService._is_event_related_task(task_name, task_args, event_id):
                        try:
                            # Anuluj zadanie
                            celery.control.revoke(task_id, terminate=True)
                            cancelled_count += 1
                            logger.info(f"🚫 Anulowano zadanie {task_name} (ID: {task_id}) dla wydarzenia {event_id}")
                        except Exception as e:
                            logger.error(f"❌ Błąd anulowania zadania {task_id}: {e}")
            
            logger.info(f"✅ Anulowano {cancelled_count} zadań dla wydarzenia {event_id}")
            return cancelled_count
            
        except Exception as e:
            logger.error(f"❌ Błąd anulowania zadań dla wydarzenia {event_id}: {e}")
            return 0
    
    @staticmethod
    def _is_event_related_task(task_name, task_args, event_id):
        """
        Sprawdza czy zadanie jest związane z wydarzeniem
        
        Args:
            task_name (str): Nazwa zadania
            task_args (list): Argumenty zadania
            event_id (int): ID wydarzenia
            
        Returns:
            bool: True jeśli zadanie jest związane z wydarzeniem
        """
        # Lista zadań związanych z wydarzeniami
        event_related_tasks = [
            'app.tasks.email_tasks.send_event_reminder_task',
            'app.tasks.email_tasks.schedule_event_reminders_task',
            'app.tasks.event_tasks.process_event_reminders_task'
        ]
        
        # Sprawdź czy nazwa zadania jest w liście zadań związanych z wydarzeniami
        if task_name not in event_related_tasks:
            return False
        
        # Sprawdź argumenty zadania
        if not task_args:
            return False
        
        # Dla send_event_reminder_task: args=[event_id, reminder_type, group_type]
        if task_name == 'app.tasks.email_tasks.send_event_reminder_task':
            if len(task_args) >= 1 and task_args[0] == event_id:
                return True
        
        # Dla schedule_event_reminders_task: args=[event_id, group_type]
        elif task_name == 'app.tasks.email_tasks.schedule_event_reminders_task':
            if len(task_args) >= 1 and task_args[0] == event_id:
                return True
        
        # Dla process_event_reminders_task: sprawdź czy przetwarza to wydarzenie
        elif task_name == 'app.tasks.event_tasks.process_event_reminders_task':
            # To zadanie przetwarza wszystkie wydarzenia, więc nie anulujemy go
            # Można by dodać logikę sprawdzającą czy wydarzenie jest w kolejce
            return False
        
        return False
    
    @staticmethod
    def cancel_all_event_tasks():
        """
        Anuluje wszystkie zadania związane z wydarzeniami
        
        Returns:
            int: Liczba anulowanych zadań
        """
        try:
            cancelled_count = 0
            
            # Pobierz wszystkie zaplanowane zadania
            scheduled_tasks = celery.control.inspect().scheduled()
            
            if not scheduled_tasks:
                logger.info("Brak zaplanowanych zadań do anulowania")
                return 0
            
            # Przejdź przez wszystkich workerów
            for worker, tasks in scheduled_tasks.items():
                for task in tasks:
                    task_name = task.get('request', {}).get('name', '')
                    task_id = task.get('request', {}).get('id')
                    
                    # Sprawdź czy zadanie dotyczy wydarzeń
                    if CeleryCleanupService._is_event_task(task_name):
                        try:
                            # Anuluj zadanie
                            celery.control.revoke(task_id, terminate=True)
                            cancelled_count += 1
                            logger.info(f"🚫 Anulowano zadanie {task_name} (ID: {task_id})")
                        except Exception as e:
                            logger.error(f"❌ Błąd anulowania zadania {task_id}: {e}")
            
            logger.info(f"✅ Anulowano {cancelled_count} zadań związanych z wydarzeniami")
            return cancelled_count
            
        except Exception as e:
            logger.error(f"❌ Błąd anulowania zadań: {e}")
            return 0
    
    @staticmethod
    def _is_event_task(task_name):
        """
        Sprawdza czy zadanie jest związane z wydarzeniami
        
        Args:
            task_name (str): Nazwa zadania
            
        Returns:
            bool: True jeśli zadanie jest związane z wydarzeniami
        """
        event_related_tasks = [
            'app.tasks.email_tasks.send_event_reminder_task',
            'app.tasks.email_tasks.schedule_event_reminders_task',
            'app.tasks.event_tasks.process_event_reminders_task',
            'app.tasks.event_tasks.archive_ended_events_task',
            'app.tasks.event_tasks.cleanup_old_reminders_task'
        ]
        
        return task_name in event_related_tasks
    
    @staticmethod
    def get_scheduled_event_tasks(event_id=None):
        """
        Pobiera listę zaplanowanych zadań związanych z wydarzeniami
        
        Args:
            event_id (int, optional): ID wydarzenia. Jeśli None, zwraca wszystkie zadania wydarzeń
            
        Returns:
            list: Lista zadań
        """
        try:
            scheduled_tasks = celery.control.inspect().scheduled()
            
            if not scheduled_tasks:
                return []
            
            event_tasks = []
            
            # Przejdź przez wszystkich workerów
            for worker, tasks in scheduled_tasks.items():
                for task in tasks:
                    task_name = task.get('request', {}).get('name', '')
                    task_args = task.get('request', {}).get('args', [])
                    task_id = task.get('request', {}).get('id')
                    eta = task.get('eta')
                    
                    # Sprawdź czy zadanie dotyczy wydarzeń
                    if event_id is None:
                        # Zwróć wszystkie zadania wydarzeń
                        if CeleryCleanupService._is_event_task(task_name):
                            event_tasks.append({
                                'task_id': task_id,
                                'task_name': task_name,
                                'args': task_args,
                                'eta': eta,
                                'worker': worker
                            })
                    else:
                        # Zwróć tylko zadania dla konkretnego wydarzenia
                        if CeleryCleanupService._is_event_related_task(task_name, task_args, event_id):
                            event_tasks.append({
                                'task_id': task_id,
                                'task_name': task_name,
                                'args': task_args,
                                'eta': eta,
                                'worker': worker
                            })
            
            return event_tasks
            
        except Exception as e:
            logger.error(f"❌ Błąd pobierania zadań: {e}")
            return []
