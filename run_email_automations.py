#!/usr/bin/env python3
"""
Script to run email automations
Can be run manually or scheduled with cron
"""

import sys
import os
import logging
from datetime import datetime

# Dodaj ścieżkę do katalogu głównego
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from services.email_automation_service import email_automation_service
from services.email_campaign_service import email_campaign_service
from config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_automations.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_app():
    """Create Flask app for running automations"""
    app = Flask(__name__)
    app.config.from_object(config['development'])
    
    return app

def run_event_email_schedules():
    """Run scheduled event emails"""
    try:
        logger.info("🔄 Uruchamianie zaplanowanych emaili dla wydarzeń...")
        
        results = email_automation_service.process_scheduled_emails()
        
        logger.info(f"✅ Przetworzono {results['processed']} zaplanowanych emaili")
        logger.info(f"   • Sukces: {results['success']}")
        logger.info(f"   • Błędy: {results['failed']}")
        
        if results['errors']:
            logger.warning("⚠️ Wystąpiły błędy:")
            for error in results['errors']:
                logger.warning(f"   - {error}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Błąd podczas przetwarzania zaplanowanych emaili: {e}")
        return None

def run_scheduled_campaigns():
    """Run scheduled email campaigns"""
    try:
        logger.info("🔄 Uruchamianie zaplanowanych kampanii emailowych...")
        
        results = email_campaign_service.process_scheduled_campaigns()
        
        logger.info(f"✅ Przetworzono {results['processed']} zaplanowanych kampanii")
        logger.info(f"   • Sukces: {results['success']}")
        logger.info(f"   • Błędy: {results['failed']}")
        
        if results['errors']:
            logger.warning("⚠️ Wystąpiły błędy:")
            for error in results['errors']:
                logger.warning(f"   - {error}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Błąd podczas przetwarzania zaplanowanych kampanii: {e}")
        return None

def get_automation_statistics():
    """Get automation statistics"""
    try:
        stats = email_automation_service.get_automation_statistics()
        
        logger.info("📊 Statystyki automatyzacji:")
        logger.info(f"   • Aktywne automatyzacje: {stats.get('total_automations', 0)}")
        logger.info(f"   • Oczekujące harmonogramy: {stats.get('pending_schedules', 0)}")
        logger.info(f"   • Ostatnie wykonania: {stats.get('recent_executions', 0)}")
        logger.info(f"   • Wskaźnik sukcesu: {stats.get('success_rate', 0)}%")
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Błąd podczas pobierania statystyk: {e}")
        return None

def main():
    """Main function to run all automations"""
    logger.info("🚀 Uruchamianie systemu automatyzacji emailowych...")
    logger.info(f"⏰ Czas uruchomienia: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Pobierz statystyki
            logger.info("\n📊 Pobieranie statystyk...")
            stats = get_automation_statistics()
            
            # Uruchom zaplanowane emaile dla wydarzeń
            logger.info("\n📅 Przetwarzanie emaili dla wydarzeń...")
            event_results = run_event_email_schedules()
            
            # Uruchom zaplanowane kampanie
            logger.info("\n📧 Przetwarzanie kampanii emailowych...")
            campaign_results = run_scheduled_campaigns()
            
            # Podsumowanie
            logger.info("\n📋 Podsumowanie wykonania:")
            
            if event_results:
                logger.info(f"   • Wydarzenia: {event_results['processed']} przetworzone")
                logger.info(f"     - Sukces: {event_results['success']}")
                logger.info(f"     - Błędy: {event_results['failed']}")
            
            if campaign_results:
                logger.info(f"   • Kampanie: {campaign_results['processed']} przetworzone")
                logger.info(f"     - Sukces: {campaign_results['success']}")
                logger.info(f"     - Błędy: {campaign_results['failed']}")
            
            logger.info("\n✅ Wykonanie automatyzacji zakończone")
            return True
            
        except Exception as e:
            logger.error(f"\n❌ Błąd podczas wykonywania automatyzacji: {e}")
            return False

def run_specific_automation(automation_type):
    """Run specific automation type"""
    logger.info(f"🎯 Uruchamianie automatyzacji: {automation_type}")
    
    app = create_app()
    
    with app.app_context():
        try:
            if automation_type == 'events':
                results = run_event_email_schedules()
            elif automation_type == 'campaigns':
                results = run_scheduled_campaigns()
            elif automation_type == 'stats':
                results = get_automation_statistics()
            else:
                logger.error(f"❌ Nieznany typ automatyzacji: {automation_type}")
                return False
            
            if results:
                logger.info(f"✅ Automatyzacja {automation_type} wykonana pomyślnie")
                return True
            else:
                logger.error(f"❌ Automatyzacja {automation_type} nie powiodła się")
                return False
                
        except Exception as e:
            logger.error(f"❌ Błąd podczas wykonywania automatyzacji {automation_type}: {e}")
            return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Uruchom konkretną automatyzację
        automation_type = sys.argv[1]
        success = run_specific_automation(automation_type)
    else:
        # Uruchom wszystkie automatyzacje
        success = main()
    
    sys.exit(0 if success else 1)

