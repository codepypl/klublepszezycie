/**
 * Universal Delete Confirmation Modal
 * Provides consistent delete confirmation across all admin pages
 */

class DeleteConfirmation {
    constructor() {
        this.modalElement = document.getElementById('bulkDeleteModal');
        this.messageElement = document.getElementById('bulkDeleteMessage');
        this.confirmBtn = document.getElementById('confirmBulkDelete');
        this.cancelBtn = document.getElementById('bulkDeleteCancel');
        
        if (!this.modalElement || !this.messageElement || !this.confirmBtn) {
            console.error('Delete confirmation modal elements not found');
        }
    }
    
    /**
     * Show delete confirmation modal
     * @param {string} message - Confirmation message
     * @param {function} onConfirm - Callback function to execute on confirm
     * @param {string} confirmText - Text for confirm button (default: "Usuń")
     * @param {string} cancelText - Text for cancel button (default: "Anuluj")
     */
    show(message, onConfirm, confirmText = 'Usuń', cancelText = 'Anuluj') {
        if (!this.modalElement || !this.messageElement || !this.confirmBtn) {
            console.error('Delete confirmation modal not available');
            return;
        }
        
        // Set message
        this.messageElement.innerHTML = message;
        
        // Update button texts
        this.confirmBtn.textContent = confirmText;
        if (this.cancelBtn) {
            this.cancelBtn.textContent = cancelText;
        }
        
        // Show modal
        const modal = new bootstrap.Modal(this.modalElement);
        modal.show();
        
        // Set up confirm button
        this.setupConfirmButton(onConfirm, modal);
        
        // Cancel button uses standard Bootstrap behavior with data-bs-dismiss="modal"
    }
    
    /**
     * Set up confirm button with callback
     * @param {function} onConfirm - Callback function to execute on confirm
     * @param {object} modal - Bootstrap modal instance
     */
    setupConfirmButton(onConfirm, modal) {
        // Clone the button to remove existing event listeners
        const newConfirmBtn = this.confirmBtn.cloneNode(true);
        
        // Check if parent node exists before replacing
        if (this.confirmBtn.parentNode) {
            this.confirmBtn.parentNode.replaceChild(newConfirmBtn, this.confirmBtn);
            // Update reference
            this.confirmBtn = newConfirmBtn;
        } else {
            console.warn('Confirm button parent node not found, using original button');
            this.confirmBtn = this.confirmBtn; // Keep original reference
        }
        
        // Set up new event listener
        this.confirmBtn.onclick = () => {
            // Hide modal using Bootstrap method
            modal.hide();
            
            // Execute callback
            if (typeof onConfirm === 'function') {
                onConfirm();
            }
        };
    }
    
    /**
     * Show confirmation for single item deletion
     * @param {string} itemName - Name of the item to delete
     * @param {function} onConfirm - Callback function to execute on confirm
     * @param {string} itemType - Type of item (optional, for better message)
     */
    showSingleDelete(itemName, onConfirm, itemType = 'element') {
        const message = `Czy na pewno chcesz usunąć ${itemType} "${itemName}"?<br><small class="text-muted">Ta operacja nie może być cofnięta.</small>`;
        this.show(message, onConfirm);
    }
    
    /**
     * Show confirmation for bulk deletion
     * @param {number} count - Number of items to delete
     * @param {function} onConfirm - Callback function to execute on confirm
     * @param {string} itemType - Type of items (optional, for better message)
     */
    showBulkDelete(count, onConfirm, itemType = 'elementy') {
        const message = `Czy na pewno chcesz usunąć ${count} ${itemType}?<br><small class="text-muted">Ta operacja nie może być cofnięta.</small>`;
        this.show(message, onConfirm);
    }
    
    /**
     * Show confirmation for reset operation
     * @param {string} description - Description of what will be reset
     * @param {function} onConfirm - Callback function to execute on confirm
     */
    showReset(description, onConfirm) {
        const message = `Czy na pewno chcesz zresetować ${description}?<br><small class="text-muted">Ta operacja zastąpi wszystkie istniejące dane domyślnymi. Tej operacji nie można cofnąć.</small>`;
        this.show(message, onConfirm, 'Resetuj', 'Anuluj');
    }
}

// Create global instance
window.deleteConfirmation = new DeleteConfirmation();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DeleteConfirmation;
}
