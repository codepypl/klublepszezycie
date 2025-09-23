#!/usr/bin/env python3
"""
Script to clean up old log files
Removes log files older than 30 days
"""
import os
import glob
import time
from datetime import datetime, timedelta

def cleanup_old_logs():
    """Clean up log files older than 30 days"""
    logs_dir = 'logs'
    
    if not os.path.exists(logs_dir):
        print(f"❌ Katalog {logs_dir} nie istnieje")
        return
    
    # Calculate cutoff date (30 days ago)
    cutoff_date = datetime.now() - timedelta(days=30)
    cutoff_timestamp = cutoff_date.timestamp()
    
    print(f"🧹 Czyszczenie logów starszych niż {cutoff_date.strftime('%Y-%m-%d')}")
    print("=" * 60)
    
    # Find all log files
    log_patterns = [
        os.path.join(logs_dir, 'wsgi_*.log'),
        os.path.join(logs_dir, 'app_console_*.log'),
        os.path.join(logs_dir, '*.log.*'),  # Rotated files
    ]
    
    deleted_count = 0
    total_size_freed = 0
    
    for pattern in log_patterns:
        for log_file in glob.glob(pattern):
            try:
                # Get file modification time
                file_mtime = os.path.getmtime(log_file)
                file_size = os.path.getsize(log_file)
                
                # Check if file is older than cutoff
                if file_mtime < cutoff_timestamp:
                    print(f"🗑️  Usuwam: {log_file} ({file_size} bytes)")
                    os.remove(log_file)
                    deleted_count += 1
                    total_size_freed += file_size
                else:
                    print(f"✅ Zachowuję: {log_file} (nowy)")
                    
            except Exception as e:
                print(f"❌ Błąd podczas przetwarzania {log_file}: {e}")
    
    print("=" * 60)
    print(f"✅ Usunięto {deleted_count} plików")
    print(f"💾 Zwolniono {total_size_freed / 1024 / 1024:.2f} MB")
    
    # Show current log files
    print("\n📁 Aktualne pliki logów:")
    current_logs = glob.glob(os.path.join(logs_dir, '*.log'))
    for log_file in current_logs:
        file_size = os.path.getsize(log_file)
        file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
        print(f"   {log_file} ({file_size} bytes, {file_mtime.strftime('%Y-%m-%d %H:%M')})")

if __name__ == "__main__":
    cleanup_old_logs()
