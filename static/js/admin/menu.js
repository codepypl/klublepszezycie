// Menu Management JavaScript
// Toast manager is loaded globally from utils/toast.js

class MenuManager {
    constructor() {
        // Toast manager is available globally
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

        // Setup auto-slug generation for menu URLs
        this.setupSlugGeneration();
    }

    setupSlugGeneration() {
        // Use centralized slug generator - always generate URL from name
        SlugGenerator.setupMultipleAutoSlug([
            { 
                titleSelector: '#menuItemName', 
                slugSelector: '#menuItemUrl', 
                alwaysGenerate: true,
                maxLength: 100
            },
            { 
                titleSelector: '#editMenuItemName', 
                slugSelector: '#editMenuItemUrl', 
                alwaysGenerate: true,
                maxLength: 100
            }
        ]);
    }

    showAddMenuItemModal() {
        document.getElementById('addMenuItemForm').reset();
        const modal = new bootstrap.Modal(document.getElementById('addMenuItemModal'));
        modal.show();
    }

    editMenuItem(menuId) {
        fetch('/api/menu')
            .then(response => {
                if (!response.ok) {
                    if (response.status === 401 || response.status === 403) {
                        throw new Error('Brak autoryzacji. Zaloguj się ponownie.');
                    }
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(response => {
                const menuItems = response.menu_items || [];
                const menuItem = menuItems.find(item => item.id === menuId);
                if (menuItem) {
                    document.getElementById('editMenuItemId').value = menuItem.id;
                    document.getElementById('editMenuItemName').value = menuItem.title;
                    document.getElementById('editMenuItemUrl').value = menuItem.url || '';
                    document.getElementById('editMenuItemBlogUrl').value = menuItem.blog_url || '';
                    document.getElementById('editMenuItemOrder').value = menuItem.order || 1;
                    document.getElementById('editMenuItemActive').checked = menuItem.is_active;
                    document.getElementById('editMenuItemBlog').checked = menuItem.blog || false;
                    
                    const modal = new bootstrap.Modal(document.getElementById('editMenuItemModal'));
                    modal.show();
                } else {
                    window.toastManager.error('Element menu nie został znaleziony');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (error.message.includes('Brak autoryzacji')) {
                    window.toastManager.error('Sesja wygasła. Zaloguj się ponownie.');
                    // Przekieruj do logowania
                    window.location.href = '/admin/login';
                } else {
                    window.toastManager.error('Wystąpił błąd podczas ładowania elementu menu: ' + error.message);
                }
            });
    }

    deleteMenuItem(menuId) {
        // Use Bootstrap modal instead of confirm()
        const modal = document.getElementById('bulkDeleteModal');
        const messageElement = document.getElementById('bulkDeleteMessage');
        const confirmButton = document.getElementById('confirmBulkDelete');
        const cancelButton = modal.querySelector('button[data-bs-dismiss="modal"]');
        
        if (modal && messageElement && confirmButton) {
            // Update message
            messageElement.textContent = 'Czy na pewno chcesz usunąć ten element menu? Tej operacji nie można cofnąć.';
            
            // Remove existing event listeners
            const newConfirmButton = confirmButton.cloneNode(true);
            confirmButton.parentNode.replaceChild(newConfirmButton, confirmButton);
            
            // Add new event listener for confirm button
            newConfirmButton.addEventListener('click', () => {
                // Hide modal first
                modal.classList.remove('show');
                modal.style.display = 'none';
                document.body.classList.remove('modal-open');
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) {
                    backdrop.remove();
                }
                
                // Then perform delete
                this.performDeleteMenuItem(menuId);
            });
            
            // Add event listener for cancel button to properly clean up
            if (cancelButton) {
                const newCancelButton = cancelButton.cloneNode(true);
                cancelButton.parentNode.replaceChild(newCancelButton, cancelButton);
                
                newCancelButton.addEventListener('click', () => {
                    // Hide modal
                    modal.classList.remove('show');
                    modal.style.display = 'none';
                    document.body.classList.remove('modal-open');
                    const backdrop = document.querySelector('.modal-backdrop');
                    if (backdrop) {
                        backdrop.remove();
                    }
                });
            }
            
            // Show modal
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        } else {
            // Fallback to confirm() if modal not available
            if (confirm('Czy na pewno chcesz usunąć ten element menu? Tej operacji nie można cofnąć.')) {
                this.performDeleteMenuItem(menuId);
            }
        }
    }

    performDeleteMenuItem(menuId) {
        fetch(`/api/menu/${menuId}`, {
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
                window.toastManager.success('Element menu został usunięty pomyślnie!');
                // Usuń wiersz z tabeli
                const row = document.querySelector(`tr[data-menu-id="${menuId}"]`);
                if (row) {
                    row.remove();
                }
            } else {
                window.toastManager.error('Błąd podczas usuwania: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (error.message.includes('Brak autoryzacji')) {
                window.toastManager.error('Sesja wygasła. Zaloguj się ponownie.');
                window.location.href = '/admin/login';
            } else {
                window.toastManager.error('Wystąpił błąd podczas usuwania elementu menu: ' + error.message);
            }
        });
    }

    handleAddMenuItem(e) {
        e.preventDefault();
        
        const data = {
            title: document.getElementById('menuItemName').value,
            url: document.getElementById('menuItemUrl').value,
            blog_url: document.getElementById('menuItemBlogUrl').value,
            order: parseInt(document.getElementById('menuItemOrder').value) || 1,
            is_active: document.getElementById('menuItemActive').checked,
            blog: document.getElementById('menuItemBlog').checked
        };
        
        fetch('/api/menu', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
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
                window.toastManager.success('Element menu został dodany pomyślnie!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('addMenuItemModal'));
                modal.hide();
                // Odśwież stronę
                window.location.reload();
            } else {
                window.toastManager.error('Błąd podczas dodawania: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (error.message.includes('Brak autoryzacji')) {
                window.toastManager.error('Sesja wygasła. Zaloguj się ponownie.');
                window.location.href = '/admin/login';
            } else {
                window.toastManager.error('Wystąpił błąd podczas dodawania elementu menu: ' + error.message);
            }
        });
    }

    handleEditMenuItem(e) {
        e.preventDefault();
        
        const data = {
            title: document.getElementById('editMenuItemName').value,
            url: document.getElementById('editMenuItemUrl').value,
            blog_url: document.getElementById('editMenuItemBlogUrl').value,
            order: parseInt(document.getElementById('editMenuItemOrder').value) || 1,
            is_active: document.getElementById('editMenuItemActive').checked,
            blog: document.getElementById('editMenuItemBlog').checked
        };
        
        const menuId = document.getElementById('editMenuItemId').value;
        fetch(`/api/menu/${menuId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
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
                window.toastManager.success('Element menu został zaktualizowany pomyślnie!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('editMenuItemModal'));
                modal.hide();
                // Odśwież stronę
                window.location.reload();
            } else {
                window.toastManager.error('Błąd podczas aktualizacji: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (error.message.includes('Brak autoryzacji')) {
                window.toastManager.error('Sesja wygasła. Zaloguj się ponownie.');
                window.location.href = '/admin/login';
            } else {
                window.toastManager.error('Wystąpił błąd podczas aktualizacji elementu menu: ' + error.message);
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
