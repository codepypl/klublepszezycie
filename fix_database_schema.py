#!/usr/bin/env python3
"""
Fix database schema - add missing columns
"""
from app import create_app
from app.models import db
from sqlalchemy import text

def fix_database_schema():
    """Add missing columns to database tables"""
    app = create_app()
    
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Add missing columns to event_schedule table
                conn.execute(text("""
                    ALTER TABLE event_schedule
                    ADD COLUMN IF NOT EXISTS end_date TIMESTAMP,
                    ADD COLUMN IF NOT EXISTS duration_minutes INTEGER DEFAULT 60,
                    ADD COLUMN IF NOT EXISTS max_participants INTEGER,
                    ADD COLUMN IF NOT EXISTS location VARCHAR(200),
                    ADD COLUMN IF NOT EXISTS is_online BOOLEAN DEFAULT false,
                    ADD COLUMN IF NOT EXISTS meeting_link VARCHAR(500),
                    ADD COLUMN IF NOT EXISTS is_published BOOLEAN DEFAULT true,
                    ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT false,
                    ADD COLUMN IF NOT EXISTS seo_title VARCHAR(200),
                    ADD COLUMN IF NOT EXISTS seo_description TEXT,
                    ADD COLUMN IF NOT EXISTS seo_keywords VARCHAR(500)
                """))
                
                # Add missing columns to testimonials table
                conn.execute(text("""
                    ALTER TABLE testimonials
                    ADD COLUMN IF NOT EXISTS author_title VARCHAR(100),
                    ADD COLUMN IF NOT EXISTS rating INTEGER DEFAULT 5,
                    ADD COLUMN IF NOT EXISTS "order" INTEGER DEFAULT 0
                """))
                
                # Add missing columns to seo_settings table
                conn.execute(text("""
                    ALTER TABLE seo_settings
                    ADD COLUMN IF NOT EXISTS title VARCHAR(200),
                    ADD COLUMN IF NOT EXISTS description TEXT,
                    ADD COLUMN IF NOT EXISTS keywords VARCHAR(500),
                    ADD COLUMN IF NOT EXISTS og_title VARCHAR(200),
                    ADD COLUMN IF NOT EXISTS og_description TEXT,
                    ADD COLUMN IF NOT EXISTS og_image VARCHAR(200),
                    ADD COLUMN IF NOT EXISTS twitter_title VARCHAR(200),
                    ADD COLUMN IF NOT EXISTS twitter_description TEXT,
                    ADD COLUMN IF NOT EXISTS twitter_image VARCHAR(200),
                    ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true
                """))
                
                conn.commit()
                print("✅ Successfully added missing columns to database")
                
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            return False
    
    return True

if __name__ == "__main__":
    if fix_database_schema():
        print("🎉 Database migration completed successfully!")
    else:
        print("💥 Database migration failed!")
