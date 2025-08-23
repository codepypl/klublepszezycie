#!/usr/bin/env python3
"""
Database import script for Better Life Club
Imports PostgreSQL database from SQL file
"""

import os
import sys
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def import_database(sql_file, target_db=None):
    """Import PostgreSQL database from SQL file"""
    
    if not os.path.exists(sql_file):
        print(f"❌ File not found: {sql_file}")
        return False
    
    # Database connection details from environment
    db_url = os.getenv('DATABASE_URL', 'postgresql://shadi@localhost:5432/betterlife')
    
    # Parse database URL
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
                host_port, database = rest.split('/', 1)
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
        return False
    
    # Use target database if specified
    if target_db:
        database = target_db
    
    print(f"🗄️  Importing to database '{database}' on {host}:{port}")
    print(f"👤 User: {username or 'default'}")
    print(f"📁 Source file: {sql_file}")
    print()
    
    # Check if database exists, if not create it
    print("🔍 Checking if database exists...")
    check_cmd = ['psql']
    
    if username:
        check_cmd.extend(['-U', username])
    
    check_cmd.extend([
        '-h', host,
        '-p', port,
        '-lqt'  # List databases in quiet mode
    ])
    
    try:
        env = os.environ.copy()
        if 'DATABASE_PASSWORD' in env:
            env['PGPASSWORD'] = env['DATABASE_PASSWORD']
        
        result = subprocess.run(check_cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Check if our database exists in the list
            db_exists = any(database in line for line in result.stdout.split('\n'))
            
            if not db_exists:
                print(f"📝 Database '{database}' does not exist. Creating...")
                
                create_cmd = ['createdb']
                if username:
                    create_cmd.extend(['-U', username])
                
                create_cmd.extend([
                    '-h', host,
                    '-p', port,
                    database
                ])
                
                create_result = subprocess.run(create_cmd, env=env, capture_output=True, text=True)
                
                if create_result.returncode == 0:
                    print(f"✅ Database '{database}' created successfully!")
                else:
                    print(f"❌ Failed to create database: {create_result.stderr}")
                    return False
            else:
                print(f"✅ Database '{database}' already exists")
        else:
            print(f"⚠️  Could not check database existence: {result.stderr}")
            print("   Proceeding with import...")
    
    except FileNotFoundError:
        print("⚠️  psql/createdb commands not found!")
        print("   Proceeding with import...")
    
    # Build psql command for import
    import_cmd = ['psql']
    
    if username:
        import_cmd.extend(['-U', username])
    
    import_cmd.extend([
        '-h', host,
        '-p', port,
        '-d', database,
        '-f', sql_file,
        '--verbose'
    ])
    
    print(f"🔧 Running import command: {' '.join(import_cmd)}")
    print()
    
    try:
        # Set PGPASSWORD if available
        env = os.environ.copy()
        if 'DATABASE_PASSWORD' in env:
            env['PGPASSWORD'] = env['DATABASE_PASSWORD']
        
        # Run psql import
        result = subprocess.run(import_cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database imported successfully!")
            print(f"📁 Imported from: {sql_file}")
            print(f"🗄️  Target database: {database}")
            
            # Show some output for verification
            if result.stdout:
                print("\n📋 Import output:")
                print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
        else:
            print("❌ Import failed!")
            print(f"Error: {result.stderr}")
            
            # Check if it's a password issue
            if "password authentication failed" in result.stderr.lower():
                print("\n💡 Tip: Set DATABASE_PASSWORD in your .env file")
                print("   or use PGPASSWORD environment variable")
            
            return False
            
    except FileNotFoundError:
        print("❌ psql command not found!")
        print("💡 Make sure PostgreSQL client tools are installed")
        print("   On macOS: brew install postgresql")
        print("   On Ubuntu: sudo apt-get install postgresql-client")
        print("   On Windows: Download from https://www.postgresql.org/download/windows/")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def list_available_backups():
    """List available backup files in current directory"""
    backup_files = []
    
    for file in os.listdir('.'):
        if file.endswith('.sql') and ('backup' in file.lower() or 'schema' in file.lower()):
            backup_files.append(file)
    
    if not backup_files:
        print("❌ No backup files found in current directory")
        print("💡 Make sure you have .sql backup files in the same directory as this script")
        return []
    
    print("📁 Available backup files:")
    for i, file in enumerate(sorted(backup_files), 1):
        size = os.path.getsize(file)
        size_str = f"{size / (1024*1024):.2f} MB" if size > 1024*1024 else f"{size / 1024:.2f} KB"
        modified = datetime.fromtimestamp(os.path.getmtime(file)).strftime('%Y-%m-%d %H:%M')
        print(f"  {i}. {file} ({size_str}, modified: {modified})")
    
    return backup_files

def interactive_import():
    """Interactive database import"""
    print("🚀 Better Life Club - Database Import Tool")
    print("=" * 50)
    print()
    
    # List available backups
    backup_files = list_available_backups()
    if not backup_files:
        return
    
    print()
    
    try:
        choice = input(f"Select backup file to import (1-{len(backup_files)}): ").strip()
        choice_idx = int(choice) - 1
        
        if 0 <= choice_idx < len(backup_files):
            selected_file = backup_files[choice_idx]
            
            print(f"\n📁 Selected file: {selected_file}")
            
            # Ask for target database
            target_db = input("Target database name (press Enter for default): ").strip()
            if not target_db:
                target_db = None
            
            print()
            
            # Confirm import
            confirm = input(f"Are you sure you want to import {selected_file}? (y/N): ").strip().lower()
            if confirm in ['y', 'yes']:
                success = import_database(selected_file, target_db)
                if success:
                    print("\n🎉 Import completed successfully!")
                else:
                    print("\n❌ Import failed. Please check the error messages above.")
            else:
                print("👋 Import cancelled")
        else:
            print("❌ Invalid selection")
            
    except ValueError:
        print("❌ Please enter a valid number")
    except KeyboardInterrupt:
        print("\n\n👋 Import cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Command line usage
        sql_file = sys.argv[1]
        target_db = sys.argv[2] if len(sys.argv) > 2 else None
        
        print(f"🚀 Importing database from: {sql_file}")
        if target_db:
            print(f"🗄️  Target database: {target_db}")
        print()
        
        success = import_database(sql_file, target_db)
        if success:
            print("\n🎉 Import completed successfully!")
        else:
            print("\n❌ Import failed. Please check the error messages above.")
    else:
        # Interactive mode
        interactive_import()
