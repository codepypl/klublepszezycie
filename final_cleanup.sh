#!/bin/bash

# Finalny skrypt do czyszczenia plików admin

for file in templates/admin/*.html; do
    if [ "$(basename "$file")" != "sidebar.html" ]; then
        echo "Finalne czyszczenie $file..."
        
        # Usuwam stare komentarze i puste linie
        sed -i '' '/<!-- Top Navigation Bar -->/d' "$file"
        sed -i '' '/^[[:space:]]*$/d' "$file"
        
        # Usuwam duplikujące się container-fluid
        sed -i '' '/<div class="container-fluid">/,/<div class="row">/c\
        <div class="container-fluid">\
            <div class="row">' "$file"
        
        echo "Zakończono $file"
    fi
done

echo "Finalne czyszczenie zakończone!"
