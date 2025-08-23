#!/bin/bash

# Skrypt do usunięcia starych elementów nawigacji z plików admin

for file in templates/admin/*.html; do
    if [ "$(basename "$file")" != "sidebar.html" ]; then
        echo "Czyszczę $file..."
        
        # Tworzę plik tymczasowy
        temp_file=$(mktemp)
        
        # Usuwam stare elementy nawigacji
        awk '
        /<nav class="navbar navbar-expand-lg admin-top-nav">/ {
            in_top_nav = 1
            next
        }
        in_top_nav && /<\/nav>/ {
            in_top_nav = 0
            next
        }
        in_top_nav {
            next
        }
        /<div class="container-fluid">/ && !in_main_container {
            in_main_container = 1
            print
            next
        }
        /<div class="row">/ && in_main_container {
            in_main_container = 0
            print
            next
        }
        { print }
        ' "$file" > "$temp_file"
        
        # Zastępuję oryginalny plik
        mv "$temp_file" "$file"
        
        echo "Zakończono $file"
    fi
done

echo "Wszystkie pliki zostały wyczyszczone!"
