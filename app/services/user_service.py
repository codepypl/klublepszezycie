"""
User Service - operacje związane z użytkownikami i grupami
"""
import sys
import os
import argparse
import logging
from datetime import datetime

# Dodaj katalog główny projektu do ścieżki PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import create_app
from app.services.group_manager import GroupManager

def setup_logging():
    """Konfiguracja logowania"""
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'user_service.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def migrate_new_members():
    """Przenosi użytkowników z new_members do club_members po 7 dniach"""
    logger = setup_logging()
    logger.info("🔄 Rozpoczynam migrację użytkowników z new_members do club_members...")
    
    try:
        app = create_app()
        with app.app_context():
            group_manager = GroupManager()
            
            success, message = group_manager.migrate_new_members_to_club_members()
            
            if success:
                logger.info(f"✅ Migracja zakończona: {message}")
            else:
                logger.error(f"❌ Błąd migracji: {message}")
                
            return success, message
            
    except Exception as e:
        logger.error(f"❌ Nieoczekiwany błąd podczas migracji: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)

def main():
    """Główna funkcja skryptu"""
    parser = argparse.ArgumentParser(description='User Service - operacje na użytkownikach')
    parser.add_argument('--migrate-new-members', action='store_true', 
                       help='Przenieś użytkowników z new_members do club_members po 7 dniach')
    
    args = parser.parse_args()
    
    # Konfiguracja logowania
    logger = setup_logging()
    
    logger.info(f"🕐 Uruchomiono User Service: {datetime.now()}")
    logger.info(f"   Argumenty: {vars(args)}")
    
    try:
        if args.migrate_new_members:
            migrate_new_members()
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"❌ Nieoczekiwany błąd: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    logger.info("✅ User Service zakończony pomyślnie")

if __name__ == "__main__":
    main()

