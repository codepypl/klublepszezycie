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
    
    // Obsługa bulk edit
    initializeBulkEdit();
    
    // Obsługa formularza edycji użytkownika
    const editUserForm = document.getElementById('editUserForm');
    if (editUserForm) {
        editUserForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const userId = document.getElementById('editUserId').value;
            const password = document.getElementById('editUserPassword').value;
            const passwordConfirm = document.getElementById('editUserPasswordConfirm').value;
            
            // Sprawdź czy hasła się zgadzają
            if (password && password !== passwordConfirm) {
                window.toastManager.error('Hasła nie są identyczne!');
                return;
            }
            
            // Sprawdź długość hasła
            if (password && password.length < 6) {
                window.toastManager.error('Hasło musi mieć co najmniej 6 znaków!');
                return;
            }
            
            const userData = {
                first_name: document.getElementById('editUserName').value,
                email: document.getElementById('editUserEmail').value,
                phone: document.getElementById('editUserPhone').value,
                club_member: document.getElementById('editUserClub').value === 'true',
                is_active: document.getElementById('editUserActive').value === 'true',
                account_type: document.getElementById('editUserAccountType').value
            };
            
            // Dodaj hasło tylko jeśli zostało ustawione
            if (password) {
                userData.password = password;
            }
            
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
                    // Wyczyść pola hasła
                    document.getElementById('editUserPassword').value = '';
                    document.getElementById('editUserPasswordConfirm').value = '';
                    // Zamknij modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('editUserModal'));
                    if (modal) {
                        modal.hide();
                    }
                    
                    // Wywołaj globalne odświeżenie
                    if (typeof window.refreshAfterCRUD === 'function') {
                        window.refreshAfterCRUD();
                    } else {
                        console.warn('window.refreshAfterCRUD is not available');
                    }
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
    const accountType = document.getElementById('filterAccountType').value;
    const status = document.getElementById('filterStatus').value;
    const clubMember = document.getElementById('filterClubMember').value;
    const event = document.getElementById('filterEvent').value;
    const group = document.getElementById('filterGroup').value;
    
    // Buduj URL z parametrami
    const params = new URLSearchParams();
    
    if (name) params.append('name', name);
    if (email) params.append('email', email);
    if (accountType) params.append('account_type', accountType);
    if (status) params.append('status', status);
    if (clubMember && clubMember !== '') {
        console.log('Adding club_member filter:', clubMember);
        params.append('club_member', clubMember);
    }
    if (event) params.append('event', event);
    if (group) params.append('group', group);
    
    // Przekieruj z filtrami
    const currentUrl = new URL(window.location);
    const newUrl = `${currentUrl.pathname}?${params.toString()}`;
    window.location.href = newUrl;
}

function clearFilters() {
    document.getElementById('filterName').value = '';
    document.getElementById('filterEmail').value = '';
    document.getElementById('filterAccountType').value = '';
    document.getElementById('filterStatus').value = '';
    document.getElementById('filterClubMember').value = '';
    document.getElementById('filterEvent').value = '';
    document.getElementById('filterGroup').value = '';
    
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
    if (urlParams.get('account_type')) {
        document.getElementById('filterAccountType').value = urlParams.get('account_type');
    }
    if (urlParams.get('status')) {
        document.getElementById('filterStatus').value = urlParams.get('status');
    }
    if (urlParams.get('club_member')) {
        document.getElementById('filterClubMember').value = urlParams.get('club_member');
    }
    if (urlParams.get('event')) {
        document.getElementById('filterEvent').value = urlParams.get('event');
    }
    if (urlParams.get('group')) {
        document.getElementById('filterGroup').value = urlParams.get('group');
    }
    
    // Jeśli są aktywne filtry, rozwiń sekcję
    if (urlParams.toString()) {
        const filtersCollapse = new bootstrap.Collapse(document.getElementById('filtersCollapse'), { show: true });
    }
}

// Funkcje do edycji i usuwania użytkowników (jeśli są używane w innych miejscach)
function editUser(userId) {
    // Przekieruj do strony użytkowników z parametrem edycji
    console.log('editUser called with userId:', userId);
    const url = `/admin/users?edit_user=${userId}`;
    console.log('Redirecting to:', url);
    window.location.href = url;
}

function deleteUser(userId) {
    window.deleteConfirmation.showSingleDelete(
        'użytkownika',
        () => {
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
                    
                    // Wywołaj globalne odświeżenie
                    if (typeof window.refreshAfterCRUD === 'function') {
                        window.refreshAfterCRUD();
                    } else {
                        console.warn('window.refreshAfterCRUD is not available');
                    }
                } else {
                    window.toastManager.error('Błąd podczas usuwania: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                window.toastManager.error('Wystąpił błąd podczas usuwania użytkownika');
            });
        },
        'użytkownika'
    );
}

function generatePassword() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
    let password = '';
    
    // Generuj hasło o długości 12 znaków
    for (let i = 0; i < 12; i++) {
        password += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    
    // Ustaw wygenerowane hasło w obu polach
    document.getElementById('editUserPassword').value = password;
    document.getElementById('editUserPasswordConfirm').value = password;
    
    // Pokaż hasło przez chwilę
    const passwordField = document.getElementById('editUserPassword');
    passwordField.type = 'text';
    setTimeout(() => {
        passwordField.type = 'password';
    }, 2000);
    
    window.toastManager.success('Hasło zostało wygenerowane!');
}

// Initialize bulk edit functionality
function initializeBulkEdit() {
    const bulkEditBtn = document.getElementById('bulkEditBtn');
    const bulkEditModal = document.getElementById('bulkEditModal');
    const confirmBulkEditBtn = document.getElementById('confirmBulkEdit');
    
    if (!bulkEditBtn || !bulkEditModal || !confirmBulkEditBtn) {
        return;
    }
    
    // Show bulk edit button when users are selected
    function updateBulkEditButton() {
        const selectedCheckboxes = document.querySelectorAll('input[name="itemIds"]:checked');
        const selectedCount = selectedCheckboxes.length;
        
        if (selectedCount > 0) {
            bulkEditBtn.style.display = 'inline-block';
            bulkEditBtn.innerHTML = `<i class="fas fa-edit me-2"></i>Edytuj Zaznaczone (${selectedCount})`;
        } else {
            bulkEditBtn.style.display = 'none';
        }
    }
    
    // Listen for checkbox changes
    document.addEventListener('change', function(e) {
        if (e.target.name === 'itemIds') {
            updateBulkEditButton();
        }
    });
    
    // Open bulk edit modal
    bulkEditBtn.addEventListener('click', function() {
        const selectedCheckboxes = document.querySelectorAll('input[name="itemIds"]:checked');
        const selectedCount = selectedCheckboxes.length;
        
        if (selectedCount === 0) {
            window.toastManager.error('Nie zaznaczono żadnych użytkowników');
            return;
        }
        
        // Update selected count in modal
        document.getElementById('selectedCount').textContent = selectedCount;
        
        // Reset form
        document.getElementById('bulkEditForm').reset();
        
        // Show modal
        const modal = new bootstrap.Modal(bulkEditModal);
        modal.show();
    });
    
    // Confirm bulk edit
    confirmBulkEditBtn.addEventListener('click', function() {
        const selectedCheckboxes = document.querySelectorAll('input[name="itemIds"]:checked');
        const userIds = Array.from(selectedCheckboxes).map(cb => cb.value);
        
        if (userIds.length === 0) {
            window.toastManager.error('Nie zaznaczono żadnych użytkowników');
            return;
        }
        
        // Get form data
        const formData = {
            user_ids: userIds,
            club_member: document.getElementById('bulkClubMember').value || null,
            is_active: document.getElementById('bulkStatus').value || null,
            account_type: document.getElementById('bulkAccountType').value || null
        };
        
        // Check if at least one field is selected
        if (formData.club_member === null && formData.is_active === null && formData.account_type === null) {
            window.toastManager.error('Wybierz przynajmniej jedno pole do edycji');
            return;
        }
        
        // Confirm action
        const changes = [];
        if (formData.club_member !== null) {
            changes.push(`Członkostwo w klubie: ${formData.club_member === 'true' ? 'Tak' : 'Nie'}`);
        }
        if (formData.is_active !== null) {
            changes.push(`Status: ${formData.is_active === 'true' ? 'Aktywny' : 'Nieaktywny'}`);
        }
        if (formData.account_type !== null) {
            changes.push(`Typ konta: ${formData.account_type}`);
        }
        
        if (!confirm(`Czy na pewno chcesz zaktualizować ${userIds.length} użytkowników?\n\nZmiany:\n${changes.join('\n')}`)) {
            return;
        }
        
        // Show loading state
        confirmBulkEditBtn.disabled = true;
        confirmBulkEditBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Zapisywanie...';
        
        // Send request
        fetch('/api/bulk-edit/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.toastManager.success(data.message);
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(bulkEditModal);
                modal.hide();
                
                // Uncheck all checkboxes
                selectedCheckboxes.forEach(cb => cb.checked = false);
                updateBulkEditButton();
                
                // Refresh page or update UI
                if (typeof window.refreshAfterCRUD === 'function') {
                    window.refreshAfterCRUD();
                } else {
                    location.reload();
                }
            } else {
                window.toastManager.error('Błąd podczas aktualizacji: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            window.toastManager.error('Wystąpił błąd podczas aktualizacji użytkowników');
        })
        .finally(() => {
            // Reset button state
            confirmBulkEditBtn.disabled = false;
            confirmBulkEditBtn.innerHTML = '<i class="fas fa-save me-2"></i>Zapisz zmiany';
        });
    });
}
