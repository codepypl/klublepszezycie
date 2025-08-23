#!/bin/bash

# Skrypt do zastąpienia sidebara we wszystkich plikach admin

for file in templates/admin/*.html; do
    if [ "$(basename "$file")" != "sidebar.html" ]; then
        echo "Przetwarzam $file..."
        
        # Tworzę plik tymczasowy
        temp_file=$(mktemp)
        
        # Zastępuję sidebar
        awk '
        /<!-- Sidebar -->/ {
            print "            <!-- Sidebar -->"
            print "            {% include '\''admin/sidebar.html'\'' %}"
            in_sidebar = 1
            next
        }
        in_sidebar && /<\/nav>/ {
            in_sidebar = 0
            next
        }
        in_sidebar {
            next
        }
        { print }
        ' "$file" > "$temp_file"
        
        # Zastępuję oryginalny plik
        mv "$temp_file" "$file"
        
        echo "Zakończono $file"
    fi
done

echo "Wszystkie pliki zostały zaktualizowane!"
