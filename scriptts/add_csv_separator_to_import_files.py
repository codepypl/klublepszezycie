#!/usr/bin/env python3
"""
Migration script to add csv_separator column to crm_import_files table
"""
import os
import sys
from sqlalchemy import create_engine, text

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db

def migrate_csv_separator():
    """Add csv_separator column to crm_import_files table"""
    app = create_app()
    
    with app.app_context():
        try:
            with db.engine.connect() as connection:
                # Add csv_separator column
                connection.execute(text("""
                    ALTER TABLE crm_import_files 
                    ADD COLUMN csv_separator VARCHAR(5) DEFAULT ',';
                """))
                connection.commit()
                print("✅ Added csv_separator column to crm_import_files table")
                
                # Update existing records with default separator
                connection.execute(text("""
                    UPDATE crm_import_files 
                    SET csv_separator = ',' 
                    WHERE csv_separator IS NULL;
                """))
                connection.commit()
                print("✅ Updated existing records with default separator")
            
            print("🎉 Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False
    
    return True

if __name__ == "__main__":
    migrate_csv_separator()
