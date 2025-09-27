"""
Celery Monitor Service - monitoring zadań Celery
"""
import logging
from datetime import datetime, timedelta
from celery_app import celery
from app.services.celery_cleanup import CeleryCleanupService

logger = logging.getLogger(__name__)

class CeleryMonitorService:
    """Serwis do monitorowania zadań Celery"""
    
    def __init__(self):
        self.cleanup_service = CeleryCleanupService()
    
    def get_celery_status(self):
        """
        Pobiera status Celery
        
        Returns:
            dict: Status Celery
        """
        try:
            # Sprawdź połączenie z Celery z timeout
            inspect = celery.control.inspect(timeout=5)
            
            # Pobierz informacje o workerach
            stats = inspect.stats()
            active = inspect.active()
            scheduled = inspect.scheduled()
            reserved = inspect.reserved()
            
            # Policz zadania
            total_scheduled = 0
            total_active = 0
            total_reserved = 0
            
            if scheduled:
                for worker, tasks in scheduled.items():
                    total_scheduled += len(tasks)
            
            if active:
                for worker, tasks in active.items():
                    total_active += len(tasks)
            
            if reserved:
                for worker, tasks in reserved.items():
                    total_reserved += len(tasks)
            
            # Sprawdź czy Celery działa
            is_healthy = stats is not None and len(stats) > 0
            
            return {
                'success': True,
                'is_healthy': is_healthy,
                'workers_count': len(stats) if stats else 0,
                'total_scheduled': total_scheduled,
                'total_active': total_active,
                'total_reserved': total_reserved,
                'workers': list(stats.keys()) if stats else [],
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Błąd pobierania statusu Celery: {e}")
            return {
                'success': False,
                'is_healthy': False,
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    def get_tasks(self, task_type='all', event_id=None, limit=50):
        """
        Pobiera listę zadań Celery
        
        Args:
            task_type (str): Typ zadań (all, scheduled, active, completed)
            event_id (int, optional): ID wydarzenia do filtrowania
            limit (int): Limit wyników
            
        Returns:
            dict: Lista zadań
        """
        try:
            tasks = []
            
            if task_type in ['all', 'scheduled']:
                # Pobierz zaplanowane zadania
                scheduled_tasks = self.cleanup_service.get_scheduled_event_tasks()
                for task in scheduled_tasks:
                    if event_id is None or (task['args'] and len(task['args']) > 0 and task['args'][0] == event_id):
                        tasks.append({
                            'id': task['task_id'],
                            'name': task['task_name'],
                            'args': task['args'],
                            'eta': task['eta'],
                            'worker': task['worker'],
                            'status': 'scheduled',
                            'type': 'scheduled'
                        })
            
            if task_type in ['all', 'active']:
                # Pobierz aktywne zadania z timeout
                inspect = celery.control.inspect(timeout=5)
                active_tasks = inspect.active()
                
                if active_tasks:
                    for worker, worker_tasks in active_tasks.items():
                        for task in worker_tasks:
                            if event_id is None or (task.get('args') and len(task.get('args', [])) > 0 and task.get('args')[0] == event_id):
                                tasks.append({
                                    'id': task.get('id'),
                                    'name': task.get('name'),
                                    'args': task.get('args', []),
                                    'eta': None,
                                    'worker': worker,
                                    'status': 'active',
                                    'type': 'active',
                                    'time_start': task.get('time_start')
                                })
            
            # Sortuj po ETA (zaplanowane pierwsze)
            tasks.sort(key=lambda x: x['eta'] or datetime.max.isoformat())
            
            # Ogranicz wyniki
            if limit > 0:
                tasks = tasks[:limit]
            
            return {
                'success': True,
                'tasks': tasks,
                'total_count': len(tasks),
                'task_type': task_type,
                'event_id': event_id,
                'limit': limit
            }
            
        except Exception as e:
            logger.error(f"❌ Błąd pobierania zadań Celery: {e}")
            return {
                'success': False,
                'error': str(e),
                'tasks': []
            }
    
    def cancel_task(self, task_id):
        """
        Anuluje zadanie Celery
        
        Args:
            task_id (str): ID zadania
            
        Returns:
            dict: Wynik anulowania
        """
        try:
            # Anuluj zadanie
            celery.control.revoke(task_id, terminate=True)
            
            logger.info(f"🚫 Anulowano zadanie Celery: {task_id}")
            
            return {
                'success': True,
                'message': f'Zadanie {task_id} zostało anulowane',
                'task_id': task_id
            }
            
        except Exception as e:
            logger.error(f"❌ Błąd anulowania zadania {task_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'task_id': task_id
            }
    
    def get_task_details(self, task_id):
        """
        Pobiera szczegóły zadania
        
        Args:
            task_id (str): ID zadania
            
        Returns:
            dict: Szczegóły zadania
        """
        try:
            # Sprawdź w zaplanowanych zadaniach
            scheduled_tasks = self.cleanup_service.get_scheduled_event_tasks()
            for task in scheduled_tasks:
                if task['task_id'] == task_id:
                    return {
                        'success': True,
                        'task': task,
                        'status': 'scheduled'
                    }
            
            # Sprawdź w aktywnych zadaniach z timeout
            inspect = celery.control.inspect(timeout=5)
            active_tasks = inspect.active()
            
            if active_tasks:
                for worker, worker_tasks in active_tasks.items():
                    for task in worker_tasks:
                        if task.get('id') == task_id:
                            return {
                                'success': True,
                                'task': {
                                    'task_id': task.get('id'),
                                    'task_name': task.get('name'),
                                    'args': task.get('args', []),
                                    'worker': worker,
                                    'time_start': task.get('time_start')
                                },
                                'status': 'active'
                            }
            
            return {
                'success': False,
                'error': 'Zadanie nie znalezione',
                'task_id': task_id
            }
            
        except Exception as e:
            logger.error(f"❌ Błąd pobierania szczegółów zadania {task_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'task_id': task_id
            }
    
    def get_event_tasks_summary(self, event_id):
        """
        Pobiera podsumowanie zadań dla wydarzenia
        
        Args:
            event_id (int): ID wydarzenia
            
        Returns:
            dict: Podsumowanie zadań
        """
        try:
            # Pobierz zadania dla wydarzenia
            event_tasks = self.cleanup_service.get_scheduled_event_tasks(event_id)
            
            # Grupuj zadania według typu
            tasks_by_type = {}
            for task in event_tasks:
                task_type = task['task_name'].split('.')[-1]  # Ostatnia część nazwy
                if task_type not in tasks_by_type:
                    tasks_by_type[task_type] = []
                tasks_by_type[task_type].append(task)
            
            return {
                'success': True,
                'event_id': event_id,
                'total_tasks': len(event_tasks),
                'tasks_by_type': tasks_by_type,
                'tasks': event_tasks
            }
            
        except Exception as e:
            logger.error(f"❌ Błąd pobierania podsumowania zadań dla wydarzenia {event_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'event_id': event_id
            }
