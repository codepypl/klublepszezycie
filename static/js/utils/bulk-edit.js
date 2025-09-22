/**
 * Universal bulk edit functionality for admin panels
 */
class BulkEdit {
    constructor(tableId, editEndpoint, options = {}) {
        this.tableId = tableId;
        this.editEndpoint = editEndpoint;
        this.options = {
            selectAllId: 'selectAll',
            editButtonId: 'bulkEditBtn',
            modalId: 'bulkEditModal',
            formId: 'bulkEditForm',
            confirmButtonId: 'confirmBulkEdit',
            selectedCountId: 'selectedCount',
            successMessage: 'Elementy zostały zaktualizowane pomyślnie',
            errorMessage: 'Wystąpił błąd podczas aktualizacji',
            ...options
        };
        
        this.selectedIds = new Set();
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.updateEditButton();
        
        // Initially hide the edit button
        const editBtn = document.getElementById(this.options.editButtonId);
        if (editBtn) {
            editBtn.style.display = 'none';
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
        
        // Edit button
        const editBtn = document.getElementById(this.options.editButtonId);
        if (editBtn) {
            editBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.showEditModal();
            });
        }
        
        // Confirm edit button
        const confirmBtn = document.getElementById(this.options.confirmButtonId);
        if (confirmBtn) {
            confirmBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.performEdit();
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
        this.updateEditButton();
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
    
    updateEditButton() {
        const editBtn = document.getElementById(this.options.editButtonId);
        if (!editBtn) return;
        
        if (this.selectedIds.size === 0) {
            editBtn.disabled = true;
            editBtn.style.display = 'none';
        } else {
            editBtn.disabled = false;
            editBtn.style.display = 'inline-block';
            editBtn.innerHTML = `<i class="fas fa-edit me-2"></i>Edytuj Zaznaczone (${this.selectedIds.size})`;
        }
    }
    
    showEditModal() {
        if (this.selectedIds.size === 0) {
            this.showMessage('Nie wybrano żadnych elementów do edycji', 'warning');
            return;
        }
        
        const modal = document.getElementById(this.options.modalId);
        const selectedCount = document.getElementById(this.options.selectedCountId);
        const form = document.getElementById(this.options.formId);
        
        if (!modal || !selectedCount || !form) {
            console.error('Bulk edit modal elements not found');
            return;
        }
        
        // Update selected count
        selectedCount.textContent = this.selectedIds.size;
        
        // Reset form
        form.reset();
        
        // Show modal
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }
    
    async performEdit() {
        const form = document.getElementById(this.options.formId);
        if (!form) {
            console.error('Bulk edit form not found');
            return;
        }
        
        // Collect form data
        const formData = new FormData(form);
        const editData = {};
        
        // Only include fields that have values (not empty)
        for (const [key, value] of formData.entries()) {
            if (value && value.trim() !== '') {
                editData[key] = value;
            }
        }
        
        // Check if at least one field is provided
        if (Object.keys(editData).length === 0) {
            this.showMessage('Wybierz przynajmniej jedno pole do edycji', 'warning');
            return;
        }
        
        // Add selected IDs
        editData.ids = Array.from(this.selectedIds);
        
        // Show loading state
        const confirmBtn = document.getElementById(this.options.confirmButtonId);
        const originalText = confirmBtn.innerHTML;
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Zapisywanie...';
        
        try {
            const response = await fetch(this.editEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(editData)
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showMessage(data.message || this.options.successMessage, 'success');
                this.refreshTable();
                
                // Close modal
                const modal = document.getElementById(this.options.modalId);
                const bootstrapModal = bootstrap.Modal.getInstance(modal);
                if (bootstrapModal) {
                    bootstrapModal.hide();
                }
                
                // Clear selections
                this.clearSelections();
            } else {
                this.showMessage(data.error || this.options.errorMessage, 'error');
            }
        } catch (error) {
            console.error('Bulk edit error:', error);
            this.showMessage(this.options.errorMessage, 'error');
        } finally {
            // Reset button state
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = originalText;
        }
    }
    
    clearSelections() {
        // Uncheck all checkboxes
        const checkboxes = document.querySelectorAll(`#${this.tableId} input[type="checkbox"][name="itemIds"]`);
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // Clear selected IDs
        this.selectedIds.clear();
        
        // Update UI
        this.updateEditButton();
        this.updateSelectAllState();
    }
    
    refreshTable() {
        // Use auto-refresh system instead of page reload
        if (typeof window.refreshAfterCRUD === 'function') {
            // Determine the type based on the table ID or current page
            let refreshType = null;
            const currentPath = window.location.pathname;
            
            if (currentPath.includes('/admin/users')) {
                refreshType = 'users';
            } else if (currentPath.includes('/admin/events')) {
                refreshType = 'events';
            } else if (currentPath.includes('/admin/benefits')) {
                refreshType = 'benefits';
            } else if (currentPath.includes('/admin/sections')) {
                refreshType = 'sections';
            } else if (currentPath.includes('/admin/faq')) {
                refreshType = 'faq';
            } else if (currentPath.includes('/admin/testimonials')) {
                refreshType = 'testimonials';
            } else if (currentPath.includes('/admin/menu')) {
                refreshType = 'menu';
            } else if (currentPath.includes('/admin/seo')) {
                refreshType = 'seo';
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

// Auto-initialize bulk edit for tables with bulk-edit class
document.addEventListener('DOMContentLoaded', function() {
    const tables = document.querySelectorAll('.bulk-edit-table');
    
    tables.forEach(table => {
        const tableId = table.id;
        const editEndpoint = table.dataset.editEndpoint;
        
        if (tableId && editEndpoint) {
            new BulkEdit(tableId, editEndpoint);
        }
    });
});
