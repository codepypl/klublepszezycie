#!/usr/bin/env python3
"""
Fix API paths in api.py - change /endpoint to /api/endpoint
"""

import re

# Read api.py
with open('app/blueprints/api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all @api_bp.route patterns that don't start with /api/
pattern = r'@api_bp\.route\([\'"](?!api/)([^\'"]*)[\'"]'
matches = re.findall(pattern, content)

print(f"Found {len(matches)} routes to fix:")

# Fix each route
for match in matches:
    if not match.startswith('/api/'):
        old_route = f"@api_bp.route('{match}'"
        new_route = f"@api_bp.route('/api{match}'"
        content = content.replace(old_route, new_route)
        print(f"  Fixed: {match} -> /api{match}")

# Write back to api.py
with open('app/blueprints/api.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("All API paths fixed!")
