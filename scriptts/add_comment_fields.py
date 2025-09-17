#!/usr/bin/env python3
"""
Migration script to add new fields to blog_comments table
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db

def migrate_comment_fields():
    """Add new fields to blog_comments table"""
    app = create_app()
    
    with app.app_context():
        try:
            from sqlalchemy import text
            
            # Add new columns to blog_comments table
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE blog_comments 
                    ADD COLUMN IF NOT EXISTS parent_id INTEGER REFERENCES blog_comments(id),
                    ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45),
                    ADD COLUMN IF NOT EXISTS user_agent TEXT,
                    ADD COLUMN IF NOT EXISTS browser VARCHAR(100),
                    ADD COLUMN IF NOT EXISTS operating_system VARCHAR(100),
                    ADD COLUMN IF NOT EXISTS location_country VARCHAR(100),
                    ADD COLUMN IF NOT EXISTS location_city VARCHAR(100)
                """))
                conn.commit()
            
            # Remove author_website column if it exists
            try:
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE blog_comments DROP COLUMN author_website"))
                    conn.commit()
                print("✅ Removed author_website column")
            except Exception as e:
                print(f"ℹ️  author_website column not found or already removed: {e}")
            
            print("✅ Successfully added new comment fields")
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            return False
    
    return True

if __name__ == "__main__":
    if migrate_comment_fields():
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
        sys.exit(1)
