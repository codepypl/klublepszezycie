#!/usr/bin/env python3
"""
Database export script for Better Life Club
Exports PostgreSQL database to SQL file
"""

import os
import sys
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def export_database():
    """Export PostgreSQL database to SQL file"""
    
    # Database connection details from environment
    db_url = os.getenv('DEV_DATABASE_URLs', '')
    
    # Parse database URL
    if db_url.startswith('postgresql://'):
        # Remove postgresql:// prefix
        connection_string = db_url[12:]
        
        # Split into user, host, port, and database
        if '@' in connection_string:
            user_part, rest = connection_string.split('@', 1)
            username = user_part
            
            if ':' in rest:
                host_port, database = rest.split('/', 1)
                if ':' in host_port:
                    host, port = host_port.split(':', 1)
                else:
                    host = host_port
                    port = '5432'
            else:
                host = rest.split('/')[0]
                port = '5432'
                database = rest.split('/')[1]
        else:
            # No username specified
            username = None
            if ':' in connection_string:
                host_port, database = connection_string.split('/', 1)
                if ':' in host_port:
                    host, port = host_port.split(':', 1)
                else:
                    host = host_port
                    port = '5432'
            else:
                host = connection_string.split('/')[0]
                port = '5432'
                database = connection_string.split('/')[1]
    else:
        print("❌ Invalid database URL format")
        return
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"betterlife_backup_{timestamp}.sql"
    
    print(f"🗄️  Exporting database '{database}' from {host}:{port}")
    print(f"👤 User: {username or 'default'}")
    print(f"📁 Output file: {filename}")
    print()
    
    # Build pg_dump command
    cmd = ['pg_dump']
    
    if username:
        cmd.extend(['-U', username])
    
    cmd.extend([
        '-h', host,
        '-p', port,
        '-d', database,
        '--verbose',
        '--no-password',
        '-f', filename
    ])
    
    print(f"🔧 Running command: {' '.join(cmd)}")
    print()
    
    try:
        # Set PGPASSWORD if available
        env = os.environ.copy()
        if 'DATABASE_PASSWORD' in env:
            env['PGPASSWORD'] = env['DATABASE_PASSWORD']
        
        # Run pg_dump
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database exported successfully!")
            print(f"📁 File saved as: {filename}")
            
            # Get file size
            if os.path.exists(filename):
                size = os.path.getsize(filename)
                size_mb = size / (1024 * 1024)
                print(f"📊 File size: {size_mb:.2f} MB")
        else:
            print("❌ Export failed!")
            print(f"Error: {result.stderr}")
            
            # Check if it's a password issue
            if "password authentication failed" in result.stderr.lower():
                print("\n💡 Tip: Set DATABASE_PASSWORD in your .env file")
                print("   or use PGPASSWORD environment variable")
            
    except FileNotFoundError:
        print("❌ pg_dump command not found!")
        print("💡 Make sure PostgreSQL client tools are installed")
        print("   On macOS: brew install postgresql")
        print("   On Ubuntu: sudo apt-get install postgresql-client")
        print("   On Windows: Download from https://www.postgresql.org/download/windows/")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def export_schema_only():
    """Export only database schema (without data)"""
    
    # Database connection details from environment
    db_url = os.getenv('DATABASE_URL', 'postgresql://shadi@localhost:5432/betterlife')
    
    # Parse database URL (same logic as above)
    if db_url.startswith('postgresql://'):
        connection_string = db_url[12:]
        
        if '@' in connection_string:
            user_part, rest = connection_string.split('@', 1)
            username = user_part
            
            if ':' in rest:
                host_port, database = rest.split('/', 1)
                if ':' in host_port:
                    host, port = host_port.split(':', 1)
                else:
                    host = host_port
                    port = '5432'
            else:
                host = rest.split('/')[0]
                port = '5432'
                database = rest.split('/')[1]
        else:
            username = None
            if ':' in connection_string:
                host_port, database = connection_string.split('/', 1)
                if ':' in host_port:
                    host, port = host_port.split(':', 1)
                else:
                    host = host_port
                    port = '5432'
            else:
                host = connection_string.split('/')[0]
                port = '5432'
                database = connection_string.split('/')[1]
    else:
        print("❌ Invalid database URL format")
        return
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"betterlife_schema_{timestamp}.sql"
    
    print(f"🗄️  Exporting schema from database '{database}' on {host}:{port}")
    print(f"👤 User: {username or 'default'}")
    print(f"📁 Output file: {filename}")
    print()
    
    # Build pg_dump command for schema only
    cmd = ['pg_dump']
    
    if username:
        cmd.extend(['-U', username])
    
    cmd.extend([
        '-h', host,
        '-p', port,
        '-d', database,
        '--schema-only',
        '--verbose',
        '--no-password',
        '-f', filename
    ])
    
    print(f"🔧 Running command: {' '.join(cmd)}")
    print()
    
    try:
        # Set PGPASSWORD if available
        env = os.environ.copy()
        if 'DATABASE_PASSWORD' in env:
            env['PGPASSWORD'] = env['DATABASE_PASSWORD']
        
        # Run pg_dump
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Schema exported successfully!")
            print(f"📁 File saved as: {filename}")
            
            # Get file size
            if os.path.exists(filename):
                size = os.path.getsize(filename)
                size_kb = size / 1024
                print(f"📊 File size: {size_kb:.2f} KB")
        else:
            print("❌ Schema export failed!")
            print(f"Error: {result.stderr}")
            
    except FileNotFoundError:
        print("❌ pg_dump command not found!")
        print("💡 Make sure PostgreSQL client tools are installed")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == '__main__':
    print("🚀 Better Life Club - Database Export Tool")
    print("=" * 50)
    print()
    
    print("Choose export type:")
    print("1. Full database export (with data)")
    print("2. Schema only export (structure only)")
    print("3. Both")
    print()
    
    try:
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == '1':
            export_database()
        elif choice == '2':
            export_schema_only()
        elif choice == '3':
            print("\n📦 Exporting both full database and schema...")
            print("=" * 50)
            export_database()
            print("\n" + "=" * 50)
            export_schema_only()
        else:
            print("❌ Invalid choice. Please run the script again.")
            
    except KeyboardInterrupt:
        print("\n\n👋 Export cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
