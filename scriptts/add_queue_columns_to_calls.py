#!/usr/bin/env python3
"""
Migration script to add queue management columns to crm_calls table
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

def add_queue_columns():
    """Add queue management columns to crm_calls table"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Adding queue management columns to crm_calls table...")
            
            # Add queue_status column
            db.session.execute(text("""
                ALTER TABLE crm_calls 
                ADD COLUMN queue_status VARCHAR(20) DEFAULT 'pending'
            """))
            print("✅ Added queue_status column")
            
            # Add queue_type column
            db.session.execute(text("""
                ALTER TABLE crm_calls 
                ADD COLUMN queue_type VARCHAR(20) DEFAULT 'new'
            """))
            print("✅ Added queue_type column")
            
            # Add scheduled_date column
            db.session.execute(text("""
                ALTER TABLE crm_calls 
                ADD COLUMN scheduled_date TIMESTAMP
            """))
            print("✅ Added scheduled_date column")
            
            # Update existing records to have proper queue_status
            db.session.execute(text("""
                UPDATE crm_calls 
                SET queue_status = 'completed' 
                WHERE queue_status IS NULL
            """))
            print("✅ Updated existing records with queue_status")
            
            db.session.commit()
            print("🎉 Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting migration: Add queue columns to crm_calls")
    print("=" * 60)
    
    success = add_queue_columns()
    
    if success:
        print("=" * 60)
        print("✅ Migration completed successfully!")
        print("The crm_calls table now has queue management columns.")
    else:
        print("=" * 60)
        print("❌ Migration failed!")
        sys.exit(1)
