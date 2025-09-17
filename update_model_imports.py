#!/usr/bin/env python3
"""
Script to update all model imports from 'models' to 'app.models'
"""
import os
import re

def update_imports_in_file(file_path):
    """Update imports in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match 'from app.models import' statements
        pattern = r'from app.models import'
        replacement = 'from app.models import'
        
        # Replace all occurrences
        new_content = re.sub(pattern, replacement, content)
        
        # Only write if changes were made
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ Updated: {file_path}")
            return True
        else:
            print(f"ℹ️  No changes: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def main():
    """Update all Python files in the project"""
    project_root = "/Volumes/Dane/Projekty/devs/klublepszezycie"
    updated_files = 0
    
    # Walk through all Python files
    for root, dirs, files in os.walk(project_root):
        # Skip certain directories
        if any(skip_dir in root for skip_dir in ['.git', '__pycache__', '.venv', 'node_modules']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if update_imports_in_file(file_path):
                    updated_files += 1
    
    print(f"\n🎉 Updated {updated_files} files!")

if __name__ == "__main__":
    main()
