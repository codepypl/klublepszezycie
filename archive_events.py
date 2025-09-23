#!/usr/bin/env python3
"""
Script to archive ended events and clean up their groups
"""
import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.email_automation import EmailAutomation
from app.services.group_manager import GroupManager

def main():
    """Main function to archive events and clean up groups"""
    app = create_app()
    
    with app.app_context():
        print("🚀 Rozpoczynam archiwizację wydarzeń...")
        print(f"📅 Czas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 50)
        
        # Initialize services
        email_automation = EmailAutomation()
        group_manager = GroupManager()
        
        # Archive ended events (sets is_archived=True, is_active=False, is_published=False)
        print("📦 Archiwizowanie zakończonych wydarzeń...")
        print("   - Ustawienie is_archived=True")
        print("   - Ustawienie is_active=False") 
        print("   - Ustawienie is_published=False")
        print("   - Czyszczenie grup wydarzenia")
        success, message = email_automation.archive_ended_events()
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ Błąd archiwizacji: {message}")
        
        print("-" * 30)
        
        # Clean up orphaned groups
        print("🧹 Czyszczenie nieużywanych grup...")
        success, message = group_manager.cleanup_orphaned_groups()
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ Błąd czyszczenia grup: {message}")
        
        print("-" * 30)
        
        # Update all groups
        print("🔄 Aktualizacja wszystkich grup...")
        success, message = email_automation.update_all_groups()
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ Błąd aktualizacji grup: {message}")
        
        print("-" * 50)
        print("✅ Archiwizacja zakończona!")

if __name__ == "__main__":
    main()
