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
            deleteBtn.textContent = 'Usuń wybrane (0)';
        } else {
            deleteBtn.disabled = false;
            deleteBtn.textContent = `Usuń wybrane (${this.selectedIds.size})`;
        }
    }
    
    async deleteSelected() {
        if (this.selectedIds.size === 0) {
            this.showMessage('Nie wybrano żadnych elementów do usunięcia', 'warning');
            return;
        }
        
        if (!confirm(this.options.confirmMessage)) {
            return;
        }
        
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
        // Reload the page to refresh the table
        window.location.reload();
    }
    
    showMessage(message, type) {
        // Create or update message element
        let messageEl = document.getElementById('bulk-delete-message');
        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.id = 'bulk-delete-message';
            messageEl.className = 'alert';
            document.body.insertBefore(messageEl, document.body.firstChild);
        }
        
        messageEl.textContent = message;
        messageEl.className = `alert alert-${type}`;
        messageEl.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            messageEl.style.display = 'none';
        }, 5000);
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

