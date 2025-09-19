/**
 * Universal bulk delete functionality for admin panels
 */
class BulkDelete {
    constructor(tableId, deleteEndpoint, options = {}) {
        this.tableId = tableId;
        this.deleteEndpoint = deleteEndpoint;
        this.options = {
            selectAllId: 'selectAll',
            deleteButtonId: 'bulkDeleteBtn',
            confirmMessage: 'Czy na pewno chcesz usunąć wybrane elementy?',
            successMessage: 'Elementy zostały usunięte pomyślnie',
            errorMessage: 'Wystąpił błąd podczas usuwania',
            ...options
        };
        
        this.selectedIds = new Set();
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.updateDeleteButton();
        
        // Initially hide the delete button
        const deleteBtn = document.getElementById(this.options.deleteButtonId);
        if (deleteBtn) {
            deleteBtn.style.display = 'none';
        }
    }
    
    bindEvents() {
        // Select all checkbox
        const selectAll = document.getElementById(this.options.selectAllId);
        if (selectAll) {
            selectAll.addEventListener('change', (e) => {
                this.toggleAll(e.target.checked);
            });
        }
        
        // Individual checkboxes
        const checkboxes = document.querySelectorAll(`#${this.tableId} input[type="checkbox"][name="itemIds"]`);
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                this.toggleItem(e.target.value, e.target.checked);
            });
        });
        
        // Delete button
        const deleteBtn = document.getElementById(this.options.deleteButtonId);
        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.deleteSelected();
            });
        }
    }
    
    toggleAll(checked) {
        const checkboxes = document.querySelectorAll(`#${this.tableId} input[type="checkbox"][name="itemIds"]`);
        checkboxes.forEach(checkbox => {
            checkbox.checked = checked;
            this.toggleItem(checkbox.value, checked);
        });
    }
    
    toggleItem(id, checked) {
        if (checked) {
            this.selectedIds.add(id);
        } else {
            this.selectedIds.delete(id);
        }
        this.updateDeleteButton();
        this.updateSelectAllState();
    }
    
    updateSelectAllState() {
        const selectAll = document.getElementById(this.options.selectAllId);
        if (!selectAll) return;
        
        const checkboxes = document.querySelectorAll(`#${this.tableId} input[type="checkbox"][name="itemIds"]`);
        const checkedCount = Array.from(checkboxes).filter(cb => cb.checked).length;
        
        if (checkedCount === 0) {
            selectAll.indeterminate = false;
            selectAll.checked = false;
        } else if (checkedCount === checkboxes.length) {
            selectAll.indeterminate = false;
            selectAll.checked = true;
        } else {
            selectAll.indeterminate = true;
            selectAll.checked = false;
        }
    }
    
    updateDeleteButton() {
        const deleteBtn = document.getElementById(this.options.deleteButtonId);
        if (!deleteBtn) return;
        
        if (this.selectedIds.size === 0) {
            deleteBtn.disabled = true;
            deleteBtn.style.display = 'none';
            deleteBtn.textContent = 'Usuń wybrane (0)';
        } else {
            deleteBtn.disabled = false;
            deleteBtn.style.display = 'inline-block';
            deleteBtn.textContent = `Usuń wybrane (${this.selectedIds.size})`;
        }
    }
    
    async deleteSelected() {
        if (this.selectedIds.size === 0) {
            this.showMessage('Nie wybrano żadnych elementów do usunięcia', 'warning');
            return;
        }
        
        // Show Bootstrap modal instead of confirm()
        this.showConfirmModal();
    }
    
    showConfirmModal() {
        const modal = document.getElementById('bulkDeleteModal');
        const message = document.getElementById('bulkDeleteMessage');
        const confirmBtn = document.getElementById('confirmBulkDelete');
        const cancelBtn = document.getElementById('bulkDeleteCancel');
        const closeBtn = document.getElementById('bulkDeleteClose');
        
        if (!modal || !message || !confirmBtn || !cancelBtn || !closeBtn) {
            console.error('Bulk delete modal elements not found');
            return;
        }
        
        // Update message
        message.textContent = this.options.confirmMessage;
        
        // Show modal
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
        
        // Handle confirm button click
        const handleConfirm = () => {
            bootstrapModal.hide();
            // Remove event listeners
            confirmBtn.removeEventListener('click', handleConfirm);
            cancelBtn.removeEventListener('click', handleCancel);
            closeBtn.removeEventListener('click', handleCancel);
            // Perform delete after modal is hidden
            setTimeout(() => {
                this.performDelete();
            }, 300); // Wait for modal animation to complete
        };
        
        // Handle cancel button click
        const handleCancel = () => {
            bootstrapModal.hide();
            // Remove event listeners
            confirmBtn.removeEventListener('click', handleConfirm);
            cancelBtn.removeEventListener('click', handleCancel);
            closeBtn.removeEventListener('click', handleCancel);
        };
        
        // Add event listeners
        confirmBtn.addEventListener('click', handleConfirm);
        cancelBtn.addEventListener('click', handleCancel);
        closeBtn.addEventListener('click', handleCancel);
    }
    
    async performDelete() {
        try {
            const response = await fetch(this.deleteEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ids: Array.from(this.selectedIds)
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showMessage(data.message || this.options.successMessage, 'success');
                this.refreshTable();
            } else {
                this.showMessage(data.error || this.options.errorMessage, 'error');
            }
        } catch (error) {
            console.error('Bulk delete error:', error);
            this.showMessage(this.options.errorMessage, 'error');
        }
    }
    
    refreshTable() {
        // Use auto-refresh system instead of page reload
        if (typeof window.refreshAfterCRUD === 'function') {
            // Determine the type based on the table ID or current page
            let refreshType = null;
            const currentPath = window.location.pathname;
            
            if (currentPath.includes('/admin/users')) {
                refreshType = 'users';
            } else if (currentPath.includes('/admin/email/queue')) {
                refreshType = 'email-queue';
            } else if (currentPath.includes('/admin/email/groups')) {
                refreshType = 'email-groups';
            }
            
            console.log(`🔄 Refreshing table with type: ${refreshType || 'auto-detect'}`);
            window.refreshAfterCRUD(refreshType);
        } else {
            // Fallback to page reload if auto-refresh is not available
            window.location.reload();
        }
    }
    
    showMessage(message, type) {
        // Use global toast manager if available
        if (window.toastManager) {
            switch (type) {
                case 'success':
                    window.toastManager.success(message);
                    break;
                case 'error':
                case 'danger':
                    window.toastManager.error(message);
                    break;
                case 'warning':
                    window.toastManager.warning(message);
                    break;
                default:
                    window.toastManager.info(message);
            }
        } else {
            // Fallback to alert if toast manager is not available
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }
}

// Auto-initialize bulk delete for tables with bulk-delete class
document.addEventListener('DOMContentLoaded', function() {
    const tables = document.querySelectorAll('.bulk-delete-table');
    
    tables.forEach(table => {
        const tableId = table.id;
        const deleteEndpoint = table.dataset.deleteEndpoint;
        
        if (tableId && deleteEndpoint) {
            new BulkDelete(tableId, deleteEndpoint);
        }
    });
});

