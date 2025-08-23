#!/bin/bash

# Skrypt do poprawienia formatowania plików admin

for file in templates/admin/*.html; do
    if [ "$(basename "$file")" != "sidebar.html" ]; then
        echo "Poprawiam formatowanie $file..."
        
        # Poprawiam formatowanie HTML
        sed -i '' 's/            <!-- Sidebar -->/            <!-- Sidebar -->/' "$file"
        sed -i '' 's/            {% include/            {% include/' "$file"
        sed -i '' 's/                <!-- Main Content -->/                <!-- Main Content -->/' "$file"
        
        echo "Zakończono $file"
    fi
done

echo "Formatowanie zostało poprawione!"
