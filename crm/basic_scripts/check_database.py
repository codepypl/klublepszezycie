#!/usr/bin/env python3
"""
Check database state
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_database():
    """Check database state"""
    try:
        # Add project root to path
        project_root = os.path.join(os.path.dirname(__file__), '..', '..')
        sys.path.insert(0, project_root)
        
        from app import create_app, db
        from app.models import User
        
        # Create app
        app = create_app()
        
        with app.app_context():
            print("🔍 Checking database state...")
            
            # Check users table structure
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            
            print("\n📊 Users table columns:")
            columns = inspector.get_columns('users')
            for col in columns:
                print(f"   - {col['name']}: {col['type']}")
            
            # Check if role column exists
            has_role = any(col['name'] == 'role' for col in columns)
            print(f"\n✅ Role column exists: {has_role}")
            
            # Check CRM tables
            existing_tables = inspector.get_table_names()
            crm_tables = ['crm_contacts', 'crm_calls', 'crm_blacklist', 'crm_import_files', 'crm_import_records']
            
            print(f"\n📊 CRM tables:")
            for table in crm_tables:
                exists = table in existing_tables
                print(f"   - {table}: {'✅' if exists else '❌'}")
            
            # Check users by role
            if has_role:
                print(f"\n👥 Users by role:")
                result = db.session.execute(text("SELECT role, COUNT(*) FROM users GROUP BY role"))
                for role, count in result:
                    print(f"   - {role}: {count} users")
            
            # Check total users
            total_users = User.query.count()
            print(f"\n📈 Total users: {total_users}")
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_database()
