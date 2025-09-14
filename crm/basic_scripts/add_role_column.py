#!/usr/bin/env python3
"""
Script to add role column to users table
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_role_column():
    """Add role column to users table"""
    try:
        # Get database URL from environment
        database_url = os.getenv('DATABASE_URL', 'postgresql://shadi@localhost:5432/betterlife')
        
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check if role column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'role'
            """))
            
            if result.fetchone():
                print("✅ Column 'role' already exists in users table")
                return
            
            # Add role column
            print("🔄 Adding 'role' column to users table...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN role VARCHAR(20) DEFAULT 'user'
            """))
            
            # Update existing admin users
            print("🔄 Updating existing admin users...")
            conn.execute(text("""
                UPDATE users 
                SET role = 'admin' 
                WHERE is_admin = true
            """))
            
            # Commit changes
            conn.commit()
            
            print("✅ Successfully added 'role' column to users table")
            print("✅ Updated existing admin users to have 'admin' role")
            
    except Exception as e:
        print(f"❌ Error adding role column: {e}")
        sys.exit(1)

if __name__ == '__main__':
    add_role_column()
