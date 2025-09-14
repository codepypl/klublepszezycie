// Users Management JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Obsługa filtrów
    const filtersCollapse = document.getElementById('filtersCollapse');
    const filtersIcon = document.getElementById('filtersIcon');
    const applyFiltersBtn = document.getElementById('applyFilters');
    const clearFiltersBtn = document.getElementById('clearFilters');
    
    if (filtersCollapse && filtersIcon) {
        // Obsługa rozwijania/zwijania filtrów
        filtersCollapse.addEventListener('show.bs.collapse', function() {
            filtersIcon.classList.remove('fa-chevron-down');
            filtersIcon.classList.add('fa-chevron-up');
        });
        
        filtersCollapse.addEventListener('hide.bs.collapse', function() {
            filtersIcon.classList.remove('fa-chevron-up');
            filtersIcon.classList.add('fa-chevron-down');
        });
    }
    
    if (applyFiltersBtn) {
        // Obsługa przycisku filtrowania
        applyFiltersBtn.addEventListener('click', function() {
            applyFilters();
        });
    }
    
    if (clearFiltersBtn) {
        // Obsługa przycisku czyszczenia filtrów
        clearFiltersBtn.addEventListener('click', function() {
            clearFilters();
        });
    }
    
    // Obsługa Enter w polach tekstowych
    const filterName = document.getElementById('filterName');
    const filterEmail = document.getElementById('filterEmail');
    
    if (filterName) {
        filterName.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                applyFilters();
            }
        });
    }
    
    if (filterEmail) {
        filterEmail.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                applyFilters();
            }
        });
    }
    
    // Załaduj filtry z URL
    loadFiltersFromURL();
    
    // Obsługa formularza edycji użytkownika
    const editUserForm = document.getElementById('editUserForm');
    if (editUserForm) {
        editUserForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const userId = document.getElementById('editUserId').value;
            const userData = {
                name: document.getElementById('editUserName').value,
                email: document.getElementById('editUserEmail').value,
                phone: document.getElementById('editUserPhone').value,
                club_member: document.getElementById('editUserClub').value === 'true',
                is_active: document.getElementById('editUserActive').value === 'true',
                role: document.getElementById('editUserRole').value
            };
            
            // Wyślij żądanie aktualizacji
            fetch(`/api/user/${userId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.toastManager.success('Użytkownik został zaktualizowany pomyślnie!');
                    // Przekieruj z powrotem do listy użytkowników
                    window.location.href = window.location.pathname;
                } else {
                    window.toastManager.error('Błąd podczas aktualizacji: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                window.toastManager.error('Wystąpił błąd podczas aktualizacji użytkownika');
            });
        });
    }
});

function applyFilters() {
    const name = document.getElementById('filterName').value.trim();
    const email = document.getElementById('filterEmail').value.trim();
    const role = document.getElementById('filterRole').value;
    const status = document.getElementById('filterStatus').value;
    const clubMember = document.getElementById('filterClubMember').value;
    
    // Buduj URL z parametrami
    const params = new URLSearchParams();
    
    if (name) params.append('name', name);
    if (email) params.append('email', email);
    if (role) params.append('role', role);
    if (status) params.append('status', status);
    if (clubMember) params.append('club_member', clubMember);
    
    // Przekieruj z filtrami
    const currentUrl = new URL(window.location);
    const newUrl = `${currentUrl.pathname}?${params.toString()}`;
    window.location.href = newUrl;
}

function clearFilters() {
    document.getElementById('filterName').value = '';
    document.getElementById('filterEmail').value = '';
    document.getElementById('filterRole').value = '';
    document.getElementById('filterStatus').value = '';
    document.getElementById('filterClubMember').value = '';
    
    // Przekieruj bez parametrów
    const currentUrl = new URL(window.location);
    window.location.href = currentUrl.pathname;
}

function loadFiltersFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    
    if (urlParams.get('name')) {
        document.getElementById('filterName').value = urlParams.get('name');
    }
    if (urlParams.get('email')) {
        document.getElementById('filterEmail').value = urlParams.get('email');
    }
    if (urlParams.get('role')) {
        document.getElementById('filterRole').value = urlParams.get('role');
    }
    if (urlParams.get('status')) {
        document.getElementById('filterStatus').value = urlParams.get('status');
    }
    if (urlParams.get('club_member')) {
        document.getElementById('filterClubMember').value = urlParams.get('club_member');
    }
    
    // Jeśli są aktywne filtry, rozwiń sekcję
    if (urlParams.toString()) {
        const filtersCollapse = new bootstrap.Collapse(document.getElementById('filtersCollapse'), { show: true });
    }
}

// Funkcje do edycji i usuwania użytkowników (jeśli są używane w innych miejscach)
function editUser(userId) {
    // Znajdź użytkownika po ID i przekieruj do edycji
    const userRow = document.querySelector(`tr[data-user-id="${userId}"]`);
    if (userRow) {
        // Email jest w 4. kolumnie (po checkbox, ID, imię)
        const email = userRow.querySelector('td:nth-child(4) a').textContent.trim();
        window.location.href = `${window.location.pathname}?edit_user=${encodeURIComponent(email)}`;
    }
}

function deleteUser(userId) {
    if (confirm('Czy na pewno chcesz usunąć tego użytkownika? Tej operacji nie można cofnąć.')) {
        fetch(`/api/user/${userId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.toastManager.success('Użytkownik został usunięty pomyślnie!');
                // Usuń wiersz z tabeli
                const row = document.querySelector(`tr[data-user-id="${userId}"]`);
                if (row) {
                    row.remove();
                }
            } else {
                window.toastManager.error('Błąd podczas usuwania: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            window.toastManager.error('Wystąpił błąd podczas usuwania użytkownika');
        });
    }
}
