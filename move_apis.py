#!/usr/bin/env python3
"""
Simple script to move API endpoints from admin.py to api.py
"""

# Read admin.py
with open('app/blueprints/admin.py', 'r', encoding='utf-8') as f:
    admin_content = f.read()

# Read api.py
with open('app/blueprints/api.py', 'r', encoding='utf-8') as f:
    api_content = f.read()

# Find all API routes in admin.py
import re

# Pattern to find API routes
api_pattern = r'@admin_bp\.route\([\'"][^\'"]*api[^\'"]*[\'"][^)]*\)\s*@login_required\s*def\s+[^:]+:.*?(?=@admin_bp\.route|\Z)'

api_endpoints = re.findall(api_pattern, admin_content, re.DOTALL)

print(f"Found {len(api_endpoints)} API endpoints to move")

# Clean and convert endpoints
cleaned_endpoints = []
for endpoint in api_endpoints:
    # Change @admin_bp.route to @api_bp.route
    cleaned = re.sub(r'@admin_bp\.route', '@api_bp.route', endpoint)
    cleaned_endpoints.append(cleaned)

# Add to api.py
new_endpoints = '\n\n'.join(cleaned_endpoints)
api_content += '\n\n# Moved from admin.py\n' + new_endpoints

# Write back to api.py
with open('app/blueprints/api.py', 'w', encoding='utf-8') as f:
    f.write(api_content)

print("API endpoints moved successfully!")

# Now remove them from admin.py
for endpoint in api_endpoints:
    admin_content = admin_content.replace(endpoint, '')

# Write back to admin.py
with open('app/blueprints/admin.py', 'w', encoding='utf-8') as f:
    f.write(admin_content)

print("API endpoints removed from admin.py!")
