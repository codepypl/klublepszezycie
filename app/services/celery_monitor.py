"""
Celery Monitor Service - monitoring zadań Celery - NOWY SYSTEM v2
"""
import logging
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from celery import current_app as celery
from app import create_app

logger = logging.getLogger(__name__)

class CeleryMonitorService:
    """Serwis do monitorowania zadań Celery - NOWY SYSTEM v2"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.app = create_app()
    
    def get_celery_status(self) -> Dict[str, Any]:
        """
        Pobiera status Celery - NOWY SYSTEM v2
        
        Returns:
            dict: Status Celery
        """
        try:
            with self.app.app_context():
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
                
                # Sprawdź Redis
                redis_healthy = self._check_redis_connection()
                
                # Sprawdź beat schedule
                beat_healthy = self._check_beat_schedule()
                
                return {
                    'success': True,
                    'is_healthy': is_healthy,
                    'redis_healthy': redis_healthy,
                    'beat_healthy': beat_healthy,
                    'workers_count': len(stats) if stats else 0,
                    'total_scheduled': total_scheduled,
                    'total_active': total_active,
                    'total_reserved': total_reserved,
                    'total_tasks': total_scheduled + total_active + total_reserved,
                    'workers': list(stats.keys()) if stats else [],
                    'last_check': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Błąd pobierania statusu Celery: {e}")
            return {
                'success': False,
                'is_healthy': False,
                'redis_healthy': False,
                'beat_healthy': False,
                'workers_count': 0,
                'total_scheduled': 0,
                'total_active': 0,
                'total_reserved': 0,
                'total_tasks': 0,
                'workers': [],
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    def _check_redis_connection(self) -> bool:
        """Sprawdza połączenie z Redis"""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"❌ Błąd połączenia z Redis: {e}")
            return False
    
    def _check_beat_schedule(self) -> bool:
        """Sprawdza czy beat schedule jest aktywny"""
        try:
            # Sprawdź czy beat schedule istnieje w Redis
            beat_keys = self.redis_client.keys('celery-beat-schedule*')
            return len(beat_keys) > 0
        except Exception as e:
            logger.error(f"❌ Błąd sprawdzania beat schedule: {e}")
            return False
    
    def get_tasks(self, task_type: str = 'all', event_id: Optional[int] = None, limit: int = 50) -> Dict[str, Any]:
        """
        Pobiera zadania Celery - NOWY SYSTEM v2
        
        Args:
            task_type: Typ zadań (all, scheduled, active, completed)
            event_id: ID wydarzenia (opcjonalne)
            limit: Limit wyników
            
        Returns:
            dict: Lista zadań
        """
        try:
            with self.app.app_context():
                tasks = []
                
                # Pobierz zaplanowane zadania
                if task_type in ['all', 'scheduled']:
                    inspect = celery.control.inspect(timeout=5)
                    scheduled_tasks = inspect.scheduled()
                    
                    if scheduled_tasks:
                        for worker, worker_tasks in scheduled_tasks.items():
                            for task in worker_tasks:
                                if event_id is None or (task.get('args') and len(task.get('args', [])) > 0 and task.get('args')[0] == event_id):
                                    tasks.append({
                                        'id': task.get('id'),
                                        'name': task.get('name'),
                                        'args': task.get('args', []),
                                        'eta': task.get('eta'),
                                        'worker': worker,
                                        'status': 'scheduled',
                                        'type': 'scheduled',
                                        'time_start': None
                                    })
                
                # Pobierz aktywne zadania
                if task_type in ['all', 'active']:
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
                
                # Pobierz zarezerwowane zadania
                if task_type in ['all', 'reserved']:
                    inspect = celery.control.inspect(timeout=5)
                    reserved_tasks = inspect.reserved()
                    
                    if reserved_tasks:
                        for worker, worker_tasks in reserved_tasks.items():
                            for task in worker_tasks:
                                if event_id is None or (task.get('args') and len(task.get('args', [])) > 0 and task.get('args')[0] == event_id):
                                    tasks.append({
                                        'id': task.get('id'),
                                        'name': task.get('name'),
                                        'args': task.get('args', []),
                                        'eta': None,
                                        'worker': worker,
                                        'status': 'reserved',
                                        'type': 'reserved',
                                        'time_start': None
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
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        Anuluje zadanie Celery - NOWY SYSTEM v2
        
        Args:
            task_id: ID zadania
            
        Returns:
            dict: Wynik anulowania
        """
        try:
            with self.app.app_context():
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
    
    def get_task_details(self, task_id: str) -> Dict[str, Any]:
        """
        Pobiera szczegóły zadania - NOWY SYSTEM v2
        
        Args:
            task_id: ID zadania
            
        Returns:
            dict: Szczegóły zadania
        """
        try:
            with self.app.app_context():
                # Sprawdź w aktywnych zadaniach
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
                
                # Sprawdź w zaplanowanych zadaniach
                scheduled_tasks = inspect.scheduled()
                
                if scheduled_tasks:
                    for worker, worker_tasks in scheduled_tasks.items():
                        for task in worker_tasks:
                            if task.get('id') == task_id:
                                return {
                                    'success': True,
                                    'task': {
                                        'task_id': task.get('id'),
                                        'task_name': task.get('name'),
                                        'args': task.get('args', []),
                                        'worker': worker,
                                        'eta': task.get('eta'),
                                        'time_start': None
                                    },
                                    'status': 'scheduled'
                                }
                
                # Sprawdź w zarezerwowanych zadaniach
                reserved_tasks = inspect.reserved()
                
                if reserved_tasks:
                    for worker, worker_tasks in reserved_tasks.items():
                        for task in worker_tasks:
                            if task.get('id') == task_id:
                                return {
                                    'success': True,
                                    'task': {
                                        'task_id': task.get('id'),
                                        'task_name': task.get('name'),
                                        'args': task.get('args', []),
                                        'worker': worker,
                                        'time_start': None
                                    },
                                    'status': 'reserved'
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
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Pobiera statystyki kolejki - NOWY SYSTEM v2
        
        Returns:
            dict: Statystyki kolejki
        """
        try:
            with self.app.app_context():
                from app.models import EmailQueue, EmailLog
                
                # Statystyki kolejki
                pending_count = EmailQueue.query.filter_by(status='pending').count()
                sent_count = EmailQueue.query.filter_by(status='sent').count()
                failed_count = EmailQueue.query.filter_by(status='failed').count()
                processing_count = EmailQueue.query.filter_by(status='processing').count()
                
                # Statystyki logów
                total_logs = EmailLog.query.count()
                sent_logs = EmailLog.query.filter_by(status='sent').count()
                sent_test_logs = EmailLog.query.filter_by(status='sent_test').count()
                failed_logs = EmailLog.query.filter_by(status='failed').count()
                
                return {
                    'success': True,
                    'queue': {
                        'pending': pending_count,
                        'sent': sent_count,
                        'failed': failed_count,
                        'processing': processing_count,
                        'total': pending_count + sent_count + failed_count + processing_count
                    },
                    'logs': {
                        'total': total_logs,
                        'sent': sent_logs,
                        'sent_test': sent_test_logs,
                        'failed': failed_logs
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ Błąd pobierania statystyk kolejki: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_beat_schedule(self) -> Dict[str, Any]:
        """
        Pobiera harmonogram beat - NOWY SYSTEM v2
        
        Returns:
            dict: Harmonogram beat
        """
        try:
            with self.app.app_context():
                # Pobierz beat schedule z konfiguracji
                beat_schedule = celery.conf.beat_schedule
                
                schedule_info = []
                for name, config in beat_schedule.items():
                    # Konwertuj schedule na string dla JSON serialization
                    schedule_value = config['schedule']
                    if hasattr(schedule_value, '__str__'):
                        schedule_str = str(schedule_value)
                    else:
                        schedule_str = schedule_value
                    
                    schedule_info.append({
                        'name': name,
                        'task': config['task'],
                        'schedule': schedule_str,
                        'options': config.get('options', {})
                    })
                
                return {
                    'success': True,
                    'schedule': schedule_info,
                    'total_tasks': len(schedule_info)
                }
                
        except Exception as e:
            logger.error(f"❌ Błąd pobierania harmonogramu beat: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def restart_worker(self) -> Dict[str, Any]:
        """
        Restartuje worker Celery - NOWY SYSTEM v2
        
        Returns:
            dict: Wynik restartu
        """
        try:
            with self.app.app_context():
                # Wyślij sygnał restart do wszystkich workerów
                celery.control.broadcast('shutdown')
                
                logger.info("🔄 Wysłano sygnał restart do workerów Celery")
                
                return {
                    'success': True,
                    'message': 'Sygnał restart został wysłany do workerów'
                }
                
        except Exception as e:
            logger.error(f"❌ Błąd restartu workerów: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_worker_logs(self, worker_name: str = None, lines: int = 100) -> Dict[str, Any]:
        """
        Pobiera logi workerów - NOWY SYSTEM v2
        
        Args:
            worker_name: Nazwa workera (opcjonalne)
            lines: Liczba linii do pobrania
            
        Returns:
            dict: Logi workerów
        """
        try:
            with self.app.app_context():
                # Pobierz logi z Redis
                log_keys = self.redis_client.keys('celery*')
                
                logs = []
                for key in log_keys:
                    if 'log' in key.lower():
                        log_data = self.redis_client.lrange(key, -lines, -1)
                        logs.extend(log_data)
                
                return {
                    'success': True,
                    'logs': logs,
                    'total_lines': len(logs)
                }
                
        except Exception as e:
            logger.error(f"❌ Błąd pobierania logów workerów: {e}")
            return {
                'success': False,
                'error': str(e)
            }