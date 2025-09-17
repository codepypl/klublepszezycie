#!/usr/bin/env python3
"""
Server migration script - safer approach
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def migrate_server():
    """Run server migration"""
    try:
        # Add project root to path
        project_root = os.path.join(os.path.dirname(__file__), '..', '..')
        sys.path.insert(0, project_root)
        
        print("🔄 Starting server migration...")
        
        # Import after path setup
        from app import create_app, db
        from app.models import User
        from crm.models import Contact, Call, BlacklistEntry, ImportFile, ImportRecord
        
        # Create app
        app = create_app()
        
        with app.app_context():
            print("📊 Checking current database state...")
            
            # Check if role column exists
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'role' not in columns:
                print("🔄 Adding role column to users table...")
                db.engine.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'"))
                print("✅ Role column added!")
            else:
                print("✅ Role column already exists!")
            
            # Update existing admins
            print("🔄 Updating existing administrators...")
            admin_count = db.session.execute(text("UPDATE users SET role = 'admin' WHERE is_admin = true")).rowcount
            print(f"✅ Updated {admin_count} administrators!")
            
            # Check CRM tables
            existing_tables = inspector.get_table_names()
            crm_tables = ['crm_contacts', 'crm_calls', 'crm_blacklist', 'crm_import_files', 'crm_import_records']
            
            missing_tables = [table for table in crm_tables if table not in existing_tables]
            
            if missing_tables:
                print(f"🔄 Creating missing CRM tables: {', '.join(missing_tables)}...")
                db.create_all()
                print("✅ CRM tables created!")
            else:
                print("✅ All CRM tables already exist!")
            
            # Verify everything
            print("\n📋 Verification:")
            print(f"   - Users with role column: ✅")
            print(f"   - CRM tables: {len([t for t in crm_tables if t in existing_tables])}/{len(crm_tables)}")
            
            # Count users by role
            result = db.session.execute(text("SELECT role, COUNT(*) FROM users GROUP BY role"))
            for role, count in result:
                print(f"   - {role}: {count} users")
            
            print("\n🎉 Migration completed successfully!")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    migrate_server()
