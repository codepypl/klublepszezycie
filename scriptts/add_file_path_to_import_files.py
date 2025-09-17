#!/usr/bin/env python3
"""
Migration script to add file_path column to crm_import_files table
"""
import os
import sys
from sqlalchemy import create_engine, text

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db

def migrate_import_files():
    """Add file_path column to crm_import_files table"""
    app = create_app()
    
    with app.app_context():
        try:
            with db.engine.connect() as connection:
                # Add file_path column
                connection.execute(text("""
                    ALTER TABLE crm_import_files 
                    ADD COLUMN file_path VARCHAR(500) DEFAULT '';
                """))
                connection.commit()
                print("✅ Added file_path column to crm_import_files table")
                
                # Update existing records with empty file_path (they will be cleaned up later)
                connection.execute(text("""
                    UPDATE crm_import_files 
                    SET file_path = '' 
                    WHERE file_path IS NULL;
                """))
                connection.commit()
                print("✅ Updated existing records with empty file_path")
                
                # Make file_path NOT NULL
                connection.execute(text("""
                    ALTER TABLE crm_import_files 
                    ALTER COLUMN file_path SET NOT NULL;
                """))
                connection.commit()
                print("✅ Made file_path column NOT NULL")
            
            print("🎉 Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False
    
    return True

if __name__ == "__main__":
    migrate_import_files()
