"""
Migration: Add order column to pages table
Date: 2025-08-29
Description: Adds order column for sorting pages
"""

from sqlalchemy import create_engine, text
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def upgrade():
    """Add order column to pages table"""
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    with engine.connect() as conn:
        # Add order column with default value 0
        conn.execute(text("ALTER TABLE pages ADD COLUMN IF NOT EXISTS \"order\" INTEGER DEFAULT 0"))
        
        # Update existing records to have order = 0
        conn.execute(text("UPDATE pages SET \"order\" = 0 WHERE \"order\" IS NULL"))
        
        # Make order column NOT NULL
        conn.execute(text("ALTER TABLE pages ALTER COLUMN \"order\" SET NOT NULL"))
        
        conn.commit()
    
    print("✅ Added order column to pages table")

def downgrade():
    """Remove order column from pages table"""
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE pages DROP COLUMN IF EXISTS \"order\""))
        conn.commit()
    
    print("❌ Removed order column from pages table")

if __name__ == "__main__":
    print("Running migration: Add order column to pages table")
    upgrade()
    print("Migration completed!")
