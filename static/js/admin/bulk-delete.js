/**
 * Universal Bulk Delete Manager
 * Can be used across all admin pages for bulk deletion functionality
 */
class BulkDeleteManager {
    constructor(options = {}) {
        this.options = {
            // Default options
            selectAllCheckboxId: 'selectAll',
            itemCheckboxClass: 'item-checkbox',
            bulkDeleteBtnId: 'bulkDeleteBtn',
            apiEndpoint: '/api/items',
            deleteMethod: 'DELETE',
            confirmMessage: 'Czy na pewno chcesz usunąć zaznaczone elementy? Tej operacji nie można cofnąć.',
            successMessage: 'Elementy zostały usunięte pomyślnie',
            errorMessage: 'Wystąpił błąd podczas usuwania elementów',
            // Override with provided options
            ...options
        };
        
        this.currentModal = null;
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        // Select all checkbox
        const selectAllCheckbox = document.getElementById(this.options.selectAllCheckboxId);
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', () => {
                this.toggleSelectAll();
            });
        }
        
        // Bulk delete button
        const bulkDeleteBtn = document.getElementById(this.options.bulkDeleteBtnId);
        if (bulkDeleteBtn) {
            bulkDeleteBtn.addEventListener('click', () => {
                this.showBulkDeleteModal();
            });
        }
        
        // Listen for checkbox changes to update bulk delete button
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains(this.options.itemCheckboxClass)) {
                this.updateBulkDeleteButton();
            }
        });
    }
    
    toggleSelectAll() {
        const selectAllCheckbox = document.getElementById(this.options.selectAllCheckboxId);
        const itemCheckboxes = document.querySelectorAll(`.${this.options.itemCheckboxClass}`);
        
        if (selectAllCheckbox) {
            itemCheckboxes.forEach(checkbox => {
                checkbox.checked = selectAllCheckbox.checked;
            });
            
            this.updateBulkDeleteButton();
        }
    }
    
    updateBulkDeleteButton() {
        const selectedCheckboxes = document.querySelectorAll(`.${this.options.itemCheckboxClass}:checked`);
        const bulkDeleteBtn = document.getElementById(this.options.bulkDeleteBtnId);
        
        if (bulkDeleteBtn) {
            if (selectedCheckboxes.length > 0) {
                bulkDeleteBtn.style.display = 'inline-block';
            } else {
                bulkDeleteBtn.style.display = 'none';
            }
        }
    }
    
    showBulkDeleteModal() {
        const selectedCheckboxes = document.querySelectorAll(`.${this.options.itemCheckboxClass}:checked`);
        
        if (selectedCheckboxes.length === 0) {
            this.showToast('Proszę zaznaczyć elementy do usunięcia', 'warning');
            return;
        }
        
        // Get modal elements
        const modal = document.getElementById('bulkDeleteModal');
        const messageElement = document.getElementById('bulkDeleteMessage');
        const confirmButton = document.getElementById('confirmBulkDelete');
        const cancelButton = document.getElementById('bulkDeleteCancel');
        const closeButton = document.getElementById('bulkDeleteClose');
        
        if (!modal || !messageElement || !confirmButton) {
            console.error('Modal elements not found');
            return;
        }
        
        // Update message
        messageElement.textContent = `${this.options.confirmMessage}\n\nZaznaczono: ${selectedCheckboxes.length} elementów`;
        
        // Store current modal instance
        this.currentModal = new bootstrap.Modal(modal);
        
        // Clear any existing event listeners by removing and re-adding
        const newConfirmButton = confirmButton.cloneNode(true);
        confirmButton.parentNode.replaceChild(newConfirmButton, confirmButton);
        
        // Add event listener for confirm button
        newConfirmButton.addEventListener('click', () => {
            this.performBulkDelete();
            this.hideModal();
        });
        
        // Add event listeners for cancel and close buttons
        if (cancelButton) {
            const newCancelButton = cancelButton.cloneNode(true);
            cancelButton.parentNode.replaceChild(newCancelButton, cancelButton);
            
            newCancelButton.addEventListener('click', () => {
                this.hideModal();
            });
        }
        
        if (closeButton) {
            const newCloseButton = closeButton.cloneNode(true);
            closeButton.parentNode.replaceChild(newCloseButton, closeButton);
            
            newCloseButton.addEventListener('click', () => {
                this.hideModal();
            });
        }
        
        // Show modal
        this.currentModal.show();
    }
    
    hideModal() {
        if (this.currentModal) {
            this.currentModal.hide();
            this.currentModal = null;
        }
    }
    
    async performBulkDelete() {
        const selectedCheckboxes = document.querySelectorAll(`.${this.options.itemCheckboxClass}:checked`);
        const selectedIds = Array.from(selectedCheckboxes).map(checkbox => checkbox.value);
        
        if (selectedIds.length === 0) {
            this.showToast('Nie wybrano żadnych elementów do usunięcia', 'warning');
            return;
        }
        
        try {
            // Show loading state
            const confirmButton = document.getElementById('confirmBulkDelete');
            if (confirmButton) {
                confirmButton.disabled = true;
                confirmButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Usuwanie...';
            }
            
            // Make API call
            const response = await fetch(this.options.apiEndpoint, {
                method: this.options.deleteMethod,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ ids: selectedIds })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast(this.options.successMessage, 'success');
                // Reload page or refresh data
                if (typeof window.loadData === 'function') {
                    window.loadData();
                } else {
                    window.location.reload();
                }
            } else {
                this.showToast(data.error || this.options.errorMessage, 'error');
            }
            
        } catch (error) {
            console.error('Bulk delete error:', error);
            this.showToast(this.options.errorMessage, 'error');
        } finally {
            // Reset button state
            if (confirmButton) {
                confirmButton.disabled = false;
                confirmButton.innerHTML = 'Usuń';
            }
        }
    }
    
    getCsrfToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }
    
    showToast(message, type) {
        if (window.ToastManager) {
            window.ToastManager.show(type, message);
        } else if (window.toastManager) {
            window.toastManager[type](message);
        } else {
            alert(message);
        }
    }
    
    // Static method to create manager for specific page
    static createForPage(pageType, options = {}) {
        const defaultOptions = {
            itemCheckboxClass: `${pageType}-checkbox`,
            bulkDeleteBtnId: 'bulkDeleteBtn',
            apiEndpoint: `/api/${pageType}`,
            confirmMessage: `Czy na pewno chcesz usunąć zaznaczone ${pageType}? Tej operacji nie można cofnąć.`,
            successMessage: `${pageType} zostały usunięte pomyślnie`,
            errorMessage: `Wystąpił błąd podczas usuwania ${pageType}`
        };
        
        return new BulkDeleteManager({ ...defaultOptions, ...options });
    }
}

// Make globally available
window.BulkDeleteManager = BulkDeleteManager;