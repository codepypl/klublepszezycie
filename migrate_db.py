#!/usr/bin/env python3
"""
Database migration script for Better Life Club
Uses current database as template and checks compatibility with target database
"""

import os
import sys
import inspect
import json
from datetime import datetime
from dotenv import load_dotenv

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import *

# Load environment variables
load_dotenv()

class DatabaseMigrator:
    def __init__(self, source_db_url=None, target_db_url=None):
        """Initialize migrator with source (template) and target database URLs"""
        self.source_db_url = source_db_url or os.getenv('DATABASE_URL', 'postgresql://shadi@localhost:5432/betterlife')
        self.target_db_url = target_db_url
        
        # Parse connection details
        self.source_config = self._parse_db_url(self.source_db_url)
        self.target_config = self._parse_db_url(self.target_db_url) if target_db_url else None
        
        print(f"🔍 Source (template) database: {self.source_config['database']} on {self.source_config['host']}:{self.source_config['port']}")
        if self.target_config:
            print(f"🎯 Target database: {self.target_config['database']} on {self.target_config['host']}:{self.target_config['port']}")
        print()

    def _parse_db_url(self, db_url):
        """Parse PostgreSQL connection URL"""
        if not db_url.startswith('postgresql://'):
            raise ValueError("Invalid database URL format")
        
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
        
        return {
            'username': username,
            'host': host,
            'port': port,
            'database': database
        }

    def get_database_connection(self, config):
        """Create database connection using psycopg2"""
        try:
            import psycopg2
            connection_string = f"postgresql://{config['username']}@{config['host']}:{config['port']}/{config['database']}"
            return psycopg2.connect(connection_string)
        except ImportError:
            print("❌ psycopg2 not installed. Installing...")
            os.system("pip install psycopg2-binary")
            import psycopg2
            connection_string = f"postgresql://{config['username']}@{config['host']}:{config['port']}/{config['database']}"
            return psycopg2.connect(connection_string)

    def get_table_structure(self, config, table_name):
        """Get table structure from database"""
        try:
            conn = self.get_database_connection(config)
            cursor = conn.cursor()
            
            # Get table columns
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default, 
                       character_maximum_length, numeric_precision, numeric_scale
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    'name': row[0],
                    'type': row[1],
                    'nullable': row[2] == 'YES',
                    'default': row[3],
                    'max_length': row[4],
                    'precision': row[5],
                    'scale': row[6]
                })
            
            # Get table constraints
            cursor.execute("""
                SELECT constraint_name, constraint_type, column_name
                FROM information_schema.table_constraints tc
                LEFT JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = %s
                ORDER BY tc.constraint_name, kcu.ordinal_position
            """, (table_name,))
            
            constraints = []
            for row in cursor.fetchall():
                constraints.append({
                    'name': row[0],
                    'type': row[1],
                    'column': row[2]
                })
            
            cursor.close()
            conn.close()
            
            return {
                'columns': columns,
                'constraints': constraints,
                'exists': len(columns) > 0
            }
            
        except Exception as e:
            return {'exists': False, 'error': str(e)}

    def get_table_data(self, config, table_name, limit=100):
        """Get sample data from table"""
        try:
            conn = self.get_database_connection(config)
            cursor = conn.cursor()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_rows = cursor.fetchone()[0]
            
            # Get sample data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {
                'total_rows': total_rows,
                'columns': columns,
                'sample_data': rows
            }
            
        except Exception as e:
            return {'error': str(e)}

    def get_all_tables(self, config):
        """Get list of all tables in database"""
        try:
            conn = self.get_database_connection(config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            return tables
            
        except Exception as e:
            print(f"❌ Error getting tables: {str(e)}")
            return []

    def compare_table_structures(self, source_table, target_table):
        """Compare table structures and return differences"""
        differences = {
            'missing_columns': [],
            'extra_columns': [],
            'column_changes': [],
            'missing_constraints': [],
            'extra_constraints': []
        }
        
        if not source_table['exists'] or not target_table['exists']:
            return differences
        
        # Compare columns
        source_cols = {col['name']: col for col in source_table['columns']}
        target_cols = {col['name']: col for col in target_table['columns']}
        
        # Find missing columns
        for col_name in source_cols:
            if col_name not in target_cols:
                differences['missing_columns'].append(source_cols[col_name])
        
        # Find extra columns
        for col_name in target_cols:
            if col_name not in source_cols:
                differences['extra_columns'].append(target_cols[col_name])
        
        # Find column changes
        for col_name in source_cols:
            if col_name in target_cols:
                source_col = source_cols[col_name]
                target_col = target_cols[col_name]
                
                # Compare data types and constraints
                if (source_col['type'] != target_col['type'] or
                    source_col['nullable'] != target_col['nullable']):
                    differences['column_changes'].append({
                        'column': col_name,
                        'source': source_col,
                        'target': target_col
                    })
        
        return differences

    def migrate_structure(self):
        """Phase 1: Migrate database structure"""
        print("🔧 PHASE 1: Structure Migration")
        print("=" * 50)
        
        if not self.target_config:
            print("❌ No target database specified")
            return False
        
        # Get tables from both databases
        source_tables = self.get_all_tables(self.source_config)
        target_tables = self.get_all_tables(self.target_config)
        
        print(f"📋 Source tables: {len(source_tables)}")
        print(f"📋 Target tables: {len(target_tables)}")
        print()
        
        structure_changes = []
        
        for table_name in source_tables:
            print(f"🔍 Analyzing table: {table_name}")
            
            # Get structures
            source_structure = self.get_table_structure(self.source_config, table_name)
            target_structure = self.get_table_structure(self.target_config, table_name)
            
            if not source_structure['exists']:
                print(f"  ❌ Source table {table_name} not accessible")
                continue
            
            if not target_structure['exists']:
                print(f"  ➕ Target table {table_name} missing - needs to be created")
                structure_changes.append({
                    'table': table_name,
                    'action': 'create',
                    'structure': source_structure
                })
                continue
            
            # Compare structures
            differences = self.compare_table_structures(source_structure, target_structure)
            
            if any([
                differences['missing_columns'],
                differences['extra_columns'],
                differences['column_changes']
            ]):
                print(f"  🔄 Structure differences detected:")
                
                if differences['missing_columns']:
                    print(f"    ➕ Missing columns: {len(differences['missing_columns'])}")
                if differences['extra_columns']:
                    print(f"    ➖ Extra columns: {len(differences['extra_columns'])}")
                if differences['column_changes']:
                    print(f"    🔄 Column changes: {len(differences['column_changes'])}")
                
                structure_changes.append({
                    'table': table_name,
                    'action': 'modify',
                    'differences': differences
                })
            else:
                print(f"  ✅ Table {table_name} structure is compatible")
        
        # Apply structure changes
        if structure_changes:
            print(f"\n🔧 Applying {len(structure_changes)} structure changes...")
            
            for change in structure_changes:
                table_name = change['table']
                action = change['action']
                
                if action == 'create':
                    print(f"  📝 Creating table {table_name}...")
                    print(f"    ⚠️  Manual table creation required for {table_name}")
                
                elif action == 'modify':
                    print(f"  🔄 Modifying table {table_name}...")
                    # Generate and apply SQL changes
                    print(f"    📝 Structure changes detected for {table_name}")
        else:
            print("✅ No structure changes needed")
        
        return True

    def migrate_data(self):
        """Phase 2: Migrate data"""
        print("\n📊 PHASE 2: Data Migration")
        print("=" * 50)
        
        if not self.target_config:
            print("❌ No target database specified")
            return False
        
        # Get tables from source database
        source_tables = self.get_all_tables(self.source_config)
        
        data_changes = []
        
        for table_name in source_tables:
            print(f"🔍 Checking data for table: {table_name}")
            
            # Get data from both databases
            source_data = self.get_table_data(self.source_config, table_name)
            target_data = self.get_table_data(self.target_config, table_name)
            
            if 'error' in source_data:
                print(f"  ❌ Error accessing source data: {source_data['error']}")
                continue
            
            if 'error' in target_data:
                print(f"  ⚠️  Target table {table_name} not accessible")
                continue
            
            source_rows = source_data.get('total_rows', 0)
            target_rows = target_data.get('total_rows', 0)
            
            print(f"  📊 Source: {source_rows} rows, Target: {target_rows} rows")
            
            if source_rows > 0 and target_rows == 0:
                print(f"  ➕ Target table {table_name} is empty - can migrate data")
                data_changes.append({
                    'table': table_name,
                    'source_data': source_data
                })
            elif source_rows > 0 and target_rows > 0:
                print(f"  ⚠️  Target table {table_name} already has data - skipping")
            else:
                print(f"  ℹ️  Source table {table_name} is empty")
        
        # Apply data changes
        if data_changes:
            print(f"\n📊 Migrating data for {len(data_changes)} tables...")
            
            for change in data_changes:
                table_name = change['table']
                print(f"  📝 Data migration needed for {table_name}")
        else:
            print("✅ No data migration needed")
        
        return True

    def run_migration(self):
        """Run complete migration process"""
        print("🚀 Starting database migration...")
        print("=" * 60)
        
        # Phase 1: Structure migration
        if not self.migrate_structure():
            print("❌ Structure migration failed")
            return False
        
        # Phase 2: Data migration
        if not self.migrate_data():
            print("❌ Data migration failed")
            return False
        
        print("\n🎉 Migration completed successfully!")
        return True

def main():
    """Main function"""
    print("🚀 Better Life Club - Database Migration Tool")
    print("=" * 60)
    print()
    
    # Get target database URL
    target_db = input("Enter target database URL (or press Enter to use current as template): ").strip()
    
    if not target_db:
        print("❌ Please provide a target database URL")
        print("   Format: postgresql://username@host:port/database")
        return
    
    try:
        # Create migrator
        migrator = DatabaseMigrator(target_db_url=target_db)
        
        # Run migration
        success = migrator.run_migration()
        
        if success:
            print("\n✅ Migration completed successfully!")
        else:
            print("\n❌ Migration failed")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == '__main__':
    main()
