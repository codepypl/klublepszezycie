// Menu Management JavaScript
class ToastManager {
    constructor() {
        this.createToastContainer();
    }

    createToastContainer() {
        if (!document.getElementById('toast-container')) {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 20px;
                z-index: 9999;
                max-width: 350px;
            `;
            document.body.appendChild(container);
        }
    }

    show(message, type = 'info', duration = 5000) {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        
        const iconMap = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        const colorMap = {
            success: 'success',
            error: 'danger',
            warning: 'warning',
            info: 'info'
        };

        toast.className = `alert alert-${colorMap[type]} alert-dismissible fade show`;
        toast.innerHTML = `
            <i class="${iconMap[type]} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        container.appendChild(toast);

        // Auto-hide after duration
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, duration);

        return toast;
    }

    success(message) {
        return this.show(message, 'success');
    }

    error(message) {
        return this.show(message, 'error');
    }

    warning(message) {
        return this.show(message, 'warning');
    }

    info(message) {
        return this.show(message, 'info');
    }
}

class MenuManager {
    constructor() {
        this.toastManager = new ToastManager();
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Add menu item form
        const addForm = document.getElementById('addMenuItemForm');
        if (addForm) {
            addForm.addEventListener('submit', (e) => this.handleAddMenuItem(e));
        }

        // Edit menu item form
        const editForm = document.getElementById('editMenuItemForm');
        if (editForm) {
            editForm.addEventListener('submit', (e) => this.handleEditMenuItem(e));
        }
    }

    showAddMenuItemModal() {
        document.getElementById('addMenuItemForm').reset();
        const modal = new bootstrap.Modal(document.getElementById('addMenuItemModal'));
        modal.show();
    }

    editMenuItem(menuId) {
        fetch('/admin/api/menu')
            .then(response => {
                if (!response.ok) {
                    if (response.status === 401 || response.status === 403) {
                        throw new Error('Brak autoryzacji. Zaloguj się ponownie.');
                    }
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(menuItems => {
                const menuItem = menuItems.find(item => item.id === menuId);
                if (menuItem) {
                    document.getElementById('editMenuItemId').value = menuItem.id;
                    document.getElementById('editMenuItemName').value = menuItem.title;
                    document.getElementById('editMenuItemUrl').value = menuItem.url || '';
                    document.getElementById('editMenuItemOrder').value = menuItem.order || 1;
                    document.getElementById('editMenuItemActive').checked = menuItem.is_active;
                    
                    const modal = new bootstrap.Modal(document.getElementById('editMenuItemModal'));
                    modal.show();
                } else {
                    this.toastManager.error('Element menu nie został znaleziony');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (error.message.includes('Brak autoryzacji')) {
                    this.toastManager.error('Sesja wygasła. Zaloguj się ponownie.');
                    // Przekieruj do logowania
                    window.location.href = '/admin/login';
                } else {
                    this.toastManager.error('Wystąpił błąd podczas ładowania elementu menu: ' + error.message);
                }
            });
    }

    deleteMenuItem(menuId) {
        if (confirm('Czy na pewno chcesz usunąć ten element menu? Tej operacji nie można cofnąć.')) {
            fetch(`/admin/api/menu?id=${menuId}`, {
                method: 'DELETE'
            })
            .then(response => {
                if (!response.ok) {
                    if (response.status === 401 || response.status === 403) {
                        throw new Error('Brak autoryzacji. Zaloguj się ponownie.');
                    }
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    this.toastManager.success('Element menu został usunięty pomyślnie!');
                    // Usuń wiersz z tabeli
                    const row = document.querySelector(`tr[data-menu-id="${menuId}"]`);
                    if (row) {
                        row.remove();
                    }
                } else {
                    this.toastManager.error('Błąd podczas usuwania: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (error.message.includes('Brak autoryzacji')) {
                    this.toastManager.error('Sesja wygasła. Zaloguj się ponownie.');
                    window.location.href = '/admin/login';
                } else {
                    this.toastManager.error('Wystąpił błąd podczas usuwania elementu menu: ' + error.message);
                }
            });
        }
    }

    handleAddMenuItem(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        formData.append('is_active', document.getElementById('menuItemActive').checked);
        
        fetch('/admin/api/menu', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                if (response.status === 401 || response.status === 403) {
                    throw new Error('Brak autoryzacji. Zaloguj się ponownie.');
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                this.toastManager.success('Element menu został dodany pomyślnie!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('addMenuItemModal'));
                modal.hide();
                // Odśwież stronę
                window.location.reload();
            } else {
                this.toastManager.error('Błąd podczas dodawania: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (error.message.includes('Brak autoryzacji')) {
                this.toastManager.error('Sesja wygasła. Zaloguj się ponownie.');
                window.location.href = '/admin/login';
            } else {
                this.toastManager.error('Wystąpił błąd podczas dodawania elementu menu: ' + error.message);
            }
        });
    }

    handleEditMenuItem(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        formData.append('is_active', document.getElementById('editMenuItemActive').checked);
        
        fetch('/admin/api/menu', {
            method: 'PUT',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                if (response.status === 401 || response.status === 403) {
                    throw new Error('Brak autoryzacji. Zaloguj się ponownie.');
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                this.toastManager.success('Element menu został zaktualizowany pomyślnie!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('editMenuItemModal'));
                modal.hide();
                // Odśwież stronę
                window.location.reload();
            } else {
                this.toastManager.error('Błąd podczas aktualizacji: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (error.message.includes('Brak autoryzacji')) {
                this.toastManager.error('Sesja wygasła. Zaloguj się ponownie.');
                window.location.href = '/admin/login';
            } else {
                this.toastManager.error('Wystąpił błąd podczas aktualizacji elementu menu: ' + error.message);
            }
        });
    }
}

// Global functions for backward compatibility
function showAddMenuItemModal() {
    window.menuManager.showAddMenuItemModal();
}

function editMenuItem(menuId) {
    window.menuManager.editMenuItem(menuId);
}

function deleteMenuItem(menuId) {
    window.menuManager.deleteMenuItem(menuId);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.menuManager = new MenuManager();
});
