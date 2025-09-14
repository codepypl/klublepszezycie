#!/usr/bin/env python3
"""
Script to create CRM tables
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_crm_tables():
    """Create CRM tables"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
        
        from app import create_app, db
        from crm.models import Contact, Call, CallQueue, ImportLog, BlacklistEntry
        
        # Create app
        app = create_app()
        
        with app.app_context():
            # Check if tables already exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            crm_tables = ['crm_contacts', 'crm_calls', 'crm_call_queue', 'crm_import_logs', 'crm_blacklist']
            
            if all(table in existing_tables for table in crm_tables):
                print("✅ CRM tables already exist!")
                return
            
            # Create tables
            print("🔄 Creating CRM tables...")
            db.create_all()
            
            print("✅ CRM tables created successfully!")
            print("   - crm_contacts")
            print("   - crm_calls") 
            print("   - crm_call_queue")
            print("   - crm_import_logs")
            
    except Exception as e:
        print(f"❌ Error creating CRM tables: {e}")
        sys.exit(1)

if __name__ == '__main__':
    create_crm_tables()
