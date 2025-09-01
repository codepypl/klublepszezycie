#!/usr/bin/env python3
"""
Skrypt do synchronizacji bazy danych między lokalną a zdalną instancją
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def get_db_config():
    """Pobierz konfigurację bazy danych z pliku .env"""
    from dotenv import load_dotenv
    load_dotenv()
    
    # Domyślna konfiguracja dla lokalnej bazy
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'klub'),
        'user': os.getenv('DB_USER', 'shadi'),
        'password': os.getenv('DB_PASSWORD', 'Das5ahec')
    }

def backup_database(config, backup_file):
    """Utwórz backup bazy danych"""
    print(f"📦 Tworzenie backupu bazy danych...")
    
    cmd = [
        'pg_dump',
        '-h', config['host'],
        '-p', config['port'],
        '-U', config['user'],
        '-d', config['database'],
        '-f', backup_file,
        '--verbose'
    ]
    
    env = os.environ.copy()
    env['PGPASSWORD'] = config['password']
    
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        print(f"✅ Backup utworzony: {backup_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Błąd podczas tworzenia backupu: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def restore_database(config, backup_file):
    """Przywróć bazę danych z backupu"""
    print(f"🔄 Przywracanie bazy danych z backupu...")
    
    cmd = [
        'psql',
        '-h', config['host'],
        '-p', config['port'],
        '-U', config['user'],
        '-d', config['database'],
        '-f', backup_file,
        '--verbose'
    ]
    
    env = os.environ.copy()
    env['PGPASSWORD'] = config['password']
    
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        print(f"✅ Baza danych przywrócona z: {backup_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Błąd podczas przywracania: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def export_data_only(config, export_file):
    """Eksportuj tylko dane (bez struktury)"""
    print(f"📤 Eksportowanie tylko danych...")
    
    cmd = [
        'pg_dump',
        '-h', config['host'],
        '-p', config['port'],
        '-U', config['user'],
        '-d', config['database'],
        '--data-only',
        '--disable-triggers',
        '-f', export_file,
        '--verbose'
    ]
    
    env = os.environ.copy()
    env['PGPASSWORD'] = config['password']
    
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        print(f"✅ Dane wyeksportowane: {export_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Błąd podczas eksportu danych: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def import_data_only(config, import_file):
    """Importuj tylko dane"""
    print(f"📥 Importowanie danych...")
    
    cmd = [
        'psql',
        '-h', config['host'],
        '-p', config['port'],
        '-U', config['user'],
        '-d', config['database'],
        '-f', import_file,
        '--verbose'
    ]
    
    env = os.environ.copy()
    env['PGPASSWORD'] = config['password']
    
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        print(f"✅ Dane zaimportowane z: {import_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Błąd podczas importu danych: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def sync_local_to_remote():
    """Synchronizuj z lokalnej do zdalnej bazy"""
    print("🔄 Synchronizacja: LOKALNA → ZDALNA")
    
    # Konfiguracja lokalnej bazy
    local_config = get_db_config()
    
    # Konfiguracja zdalnej bazy (zakładamy, że masz zmienne środowiskowe z prefiksem REMOTE_)
    remote_config = {
        'host': os.getenv('REMOTE_DB_HOST'),
        'port': os.getenv('REMOTE_DB_PORT', '5432'),
        'database': os.getenv('REMOTE_DB_NAME'),
        'user': os.getenv('REMOTE_DB_USER'),
        'password': os.getenv('REMOTE_DB_PASSWORD')
    }
    
    # Sprawdź czy mamy konfigurację zdalnej bazy
    if not all(remote_config.values()):
        print("❌ Brak konfiguracji zdalnej bazy danych.")
        print("Ustaw zmienne środowiskowe:")
        print("  REMOTE_DB_HOST, REMOTE_DB_PORT, REMOTE_DB_NAME, REMOTE_DB_USER, REMOTE_DB_PASSWORD")
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Backup zdalnej bazy
    remote_backup = f"remote_backup_{timestamp}.sql"
    if not backup_database(remote_config, remote_backup):
        return False
    
    # 2. Eksport danych z lokalnej bazy
    local_export = f"local_export_{timestamp}.sql"
    if not export_data_only(local_config, local_export):
        return False
    
    # 3. Import danych do zdalnej bazy
    if not import_data_only(remote_config, local_export):
        print("⚠️  Import nie powiódł się. Backup zdalnej bazy jest dostępny w pliku:", remote_backup)
        return False
    
    print("✅ Synchronizacja zakończona pomyślnie!")
    print(f"📁 Backup zdalnej bazy: {remote_backup}")
    print(f"📁 Eksport lokalnej bazy: {local_export}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Synchronizacja bazy danych')
    parser.add_argument('--action', choices=['backup', 'restore', 'export', 'import', 'sync'], 
                       default='sync', help='Akcja do wykonania')
    parser.add_argument('--file', help='Plik do importu/eksportu')
    parser.add_argument('--remote', action='store_true', help='Użyj konfiguracji zdalnej bazy')
    
    args = parser.parse_args()
    
    config = get_db_config()
    
    if args.remote:
        config = {
            'host': os.getenv('REMOTE_DB_HOST'),
            'port': os.getenv('REMOTE_DB_PORT', '5432'),
            'database': os.getenv('REMOTE_DB_NAME'),
            'user': os.getenv('REMOTE_DB_USER'),
            'password': os.getenv('REMOTE_DB_PASSWORD')
        }
    
    if args.action == 'backup':
        if not args.file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            args.file = f"backup_{timestamp}.sql"
        backup_database(config, args.file)
    
    elif args.action == 'restore':
        if not args.file:
            print("❌ Musisz podać plik do przywrócenia (--file)")
            return
        restore_database(config, args.file)
    
    elif args.action == 'export':
        if not args.file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            args.file = f"export_{timestamp}.sql"
        export_data_only(config, args.file)
    
    elif args.action == 'import':
        if not args.file:
            print("❌ Musisz podać plik do importu (--file)")
            return
        import_data_only(config, args.file)
    
    elif args.action == 'sync':
        sync_local_to_remote()

if __name__ == "__main__":
    main()
