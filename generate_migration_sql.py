#!/usr/bin/env python3
"""
Generate SQL migration scripts for Better Life Club database
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_structure_migration_sql(table_name, differences):
    """Generate SQL statements for structure migration"""
    sql_statements = []
    
    # Add missing columns
    for column in differences['missing_columns']:
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column['name']} {column['type']}"
        
        if not column['nullable']:
            sql += " NOT NULL"
        
        if column['default']:
            sql += f" DEFAULT {column['default']}"
        
        sql_statements.append(sql + ";")
    
    # Drop extra columns (commented out for safety)
    for column in differences['extra_columns']:
        sql = f"-- ALTER TABLE {table_name} DROP COLUMN {column['name']}; -- UNCOMMENT TO DROP EXTRA COLUMNS"
        sql_statements.append(sql)
    
    # Modify existing columns
    for change in differences['column_changes']:
        source = change['source']
        target = change['target']
        
        # Change data type if needed
        if source['type'] != target['type']:
            sql = f"ALTER TABLE {table_name} ALTER COLUMN {change['column']} TYPE {source['type']};"
            sql_statements.append(sql)
        
        # Change nullable constraint if needed
        if source['nullable'] != target['nullable']:
            if source['nullable']:
                sql = f"ALTER TABLE {table_name} ALTER COLUMN {change['column']} DROP NOT NULL;"
            else:
                sql = f"ALTER TABLE {table_name} ALTER COLUMN {change['column']} SET NOT NULL;"
            sql_statements.append(sql)
    
    return sql_statements

def generate_data_migration_sql(table_name, source_data, target_data):
    """Generate SQL statements for data migration"""
    sql_statements = []
    
    if not source_data or 'error' in source_data:
        return sql_statements
    
    # Check if target table has data
    if target_data and target_data.get('total_rows', 0) > 0:
        print(f"  ⚠️  Table {table_name} already has {target_data['total_rows']} rows")
        print(f"     Skipping data migration for safety")
        return sql_statements
    
    # Generate INSERT statements for sample data
    if source_data.get('sample_data'):
        for row in source_data['sample_data']:
            columns = source_data['columns']
            values = []
            
            for value in row:
                if value is None:
                    values.append('NULL')
                elif isinstance(value, str):
                    values.append(f"'{value.replace("'", "''")}'")
                elif isinstance(value, datetime):
                    values.append(f"'{value.isoformat()}'")
                else:
                    values.append(str(value))
            
            sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});"
            sql_statements.append(sql)
    
    return sql_statements

def generate_create_table_sql(table_name, structure):
    """Generate CREATE TABLE SQL statement"""
    sql = f"CREATE TABLE {table_name} (\n"
    
    column_definitions = []
    for column in structure['columns']:
        col_def = f"    {column['name']} {column['type']}"
        
        if not column['nullable']:
            col_def += " NOT NULL"
        
        if column['default']:
            col_def += f" DEFAULT {column['default']}"
        
        column_definitions.append(col_def)
    
    sql += ",\n".join(column_definitions)
    sql += "\n);"
    
    return sql

def save_migration_file(filename, content):
    """Save migration SQL to file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    full_filename = f"migration_{timestamp}_{filename}.sql"
    
    with open(full_filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"📁 Migration file saved: {full_filename}")
    return full_filename

def main():
    """Main function to generate migration SQL"""
    print("🔧 Better Life Club - Migration SQL Generator")
    print("=" * 50)
    print()
    
    print("This script generates SQL migration files based on detected differences.")
    print("You can then review and apply these SQL statements manually.")
    print()
    
    # Example usage
    print("Example usage:")
    print("1. Run migrate_db.py to detect differences")
    print("2. Use this script to generate SQL files")
    print("3. Review and apply SQL manually")
    print()
    
    print("Available functions:")
    print("- generate_structure_migration_sql()")
    print("- generate_data_migration_sql()")
    print("- generate_create_table_sql()")
    print("- save_migration_file()")
    print()
    
    print("Import this module in your migration scripts to use these functions.")

if __name__ == '__main__':
    main()
