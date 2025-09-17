#!/usr/bin/env python3
"""
Migration script to remove settings tables from database
This script removes tables that were replaced with configuration files
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DevelopmentConfig

def get_db_connection():
    """Get database connection"""
    try:
        # Parse database URL
        db_url = DevelopmentConfig.SQLALCHEMY_DATABASE_URI
        if db_url.startswith('postgresql://'):
            # Extract connection details
            db_url = db_url.replace('postgresql://', '')
            if '@' in db_url:
                user_pass, host_db = db_url.split('@', 1)
                if ':' in user_pass:
                    user, password = user_pass.split(':', 1)
                else:
                    user = user_pass
                    password = ''
                
                if ':' in host_db:
                    host, port_db = host_db.split(':', 1)
                    if '/' in port_db:
                        port, database = port_db.split('/', 1)
                    else:
                        port = port_db
                        database = 'postgres'
                else:
                    host = host_db
                    port = '5432'
                    database = 'postgres'
            else:
                # Fallback for simple format
                user = 'postgres'
                password = ''
                host = 'localhost'
                port = '5432'
                database = 'betterlife'
        else:
            raise ValueError("Unsupported database URL format")
        
        # Connect to database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return None

def remove_table(conn, table_name):
    """Remove table if it exists"""
    try:
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, (table_name,))
        
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print(f"🗑️  Removing table: {table_name}")
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
            print(f"✅ Table {table_name} removed successfully")
        else:
            print(f"ℹ️  Table {table_name} does not exist, skipping")
        
        cursor.close()
        return True
    except Exception as e:
        print(f"❌ Error removing table {table_name}: {e}")
        return False

def main():
    """Main migration function"""
    print("🚀 Starting migration to remove settings tables...")
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    try:
        # List of tables to remove
        tables_to_remove = [
            'seo_settings',
            'footer_settings', 
            'legal_documents',
            'blog_post_images',
            'presentation_schedule',
            'registrations',
            'crm_import_logs',
            'crm_call_queue'
        ]
        
        print(f"📋 Tables to remove: {', '.join(tables_to_remove)}")
        
        # Remove each table
        success_count = 0
        for table_name in tables_to_remove:
            if remove_table(conn, table_name):
                success_count += 1
        
        print(f"\n📊 Migration completed:")
        print(f"   ✅ Successfully removed: {success_count}/{len(tables_to_remove)} tables")
        print(f"   ❌ Failed: {len(tables_to_remove) - success_count}/{len(tables_to_remove)} tables")
        
        if success_count == len(tables_to_remove):
            print("\n🎉 All settings tables removed successfully!")
            print("\n📝 Next steps:")
            print("   1. Update your application configuration files")
            print("   2. Test the application to ensure everything works")
            print("   3. Consider creating backup of current database")
            return True
        else:
            print("\n⚠️  Some tables could not be removed. Check the errors above.")
            return False
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

