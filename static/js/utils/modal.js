// Universal Modal System for Lepsze Życie Club
// Replaces all alert() calls with Bootstrap modals

class ModalManager {
    constructor() {
        this.alertModal = null;
        this.init();
    }

    init() {
        // Initialize alert modal
        const alertModalElement = document.getElementById('alertModal');
        if (alertModalElement) {
            this.alertModal = new bootstrap.Modal(alertModalElement);
        }
    }

    // Show alert modal (replaces alert())
    showAlert(message, type = 'info', title = null) {
        if (!this.alertModal) {
            console.error('Alert modal not initialized');
            return;
        }

        const modalElement = document.getElementById('alertModal');
        const titleElement = document.getElementById('alertModalTitleText');
        const messageElement = document.getElementById('alertModalMessage');
        const iconElement = document.getElementById('alertModalIcon');
        const okButton = document.getElementById('alertModalOk');

        // Set title
        if (title) {
            titleElement.textContent = title;
        } else {
            switch (type) {
                case 'success':
                    titleElement.textContent = 'Sukces';
                    break;
                case 'error':
                case 'danger':
                    titleElement.textContent = 'Błąd';
                    break;
                case 'warning':
                    titleElement.textContent = 'Ostrzeżenie';
                    break;
                case 'info':
                default:
                    titleElement.textContent = 'Informacja';
                    break;
            }
        }

        // Set message
        messageElement.textContent = message;

        // Set icon and colors
        iconElement.className = 'fas me-2';
        okButton.className = 'btn';
        
        switch (type) {
            case 'success':
                iconElement.classList.add('fa-check-circle', 'text-success');
                okButton.classList.add('btn-success');
                break;
            case 'error':
            case 'danger':
                iconElement.classList.add('fa-exclamation-triangle', 'text-danger');
                okButton.classList.add('btn-danger');
                break;
            case 'warning':
                iconElement.classList.add('fa-exclamation-triangle', 'text-warning');
                okButton.classList.add('btn-warning');
                break;
            case 'info':
            default:
                iconElement.classList.add('fa-info-circle', 'text-info');
                okButton.classList.add('btn-primary');
                break;
        }

        // Show modal
        this.alertModal.show();
    }

    // Convenience methods
    success(message, title = null) {
        this.showAlert(message, 'success', title);
    }

    error(message, title = null) {
        this.showAlert(message, 'error', title);
    }

    warning(message, title = null) {
        this.showAlert(message, 'warning', title);
    }

    info(message, title = null) {
        this.showAlert(message, 'info', title);
    }

    // Show confirmation modal (replaces confirm())
    showConfirm(message, title = 'Potwierdź', confirmText = 'Tak', cancelText = 'Nie') {
        return new Promise((resolve) => {
            const modalElement = document.getElementById('bulkDeleteModal');
            const messageElement = document.getElementById('bulkDeleteMessage');
            const confirmButton = document.getElementById('confirmBulkDelete');
            const cancelButton = document.getElementById('bulkDeleteCancel');
            const titleElement = modalElement.querySelector('.modal-title');

            if (!modalElement || !messageElement || !confirmButton) {
                console.error('Confirmation modal not found');
                resolve(false);
                return;
            }

            // Update content
            titleElement.innerHTML = `<i class="fas fa-question-circle me-2 text-warning"></i>${title}`;
            messageElement.textContent = message;
            confirmButton.textContent = confirmText;
            cancelButton.textContent = cancelText;

            // Remove existing event listeners
            const newConfirmButton = confirmButton.cloneNode(true);
            const newCancelButton = cancelButton.cloneNode(true);
            
            // Check if parent nodes exist before replacing
            if (confirmButton.parentNode) {
                confirmButton.parentNode.replaceChild(newConfirmButton, confirmButton);
            } else {
                console.warn('Confirm button parent node not found');
            }
            
            if (cancelButton.parentNode) {
                cancelButton.parentNode.replaceChild(newCancelButton, cancelButton);
            } else {
                console.warn('Cancel button parent node not found');
            }

            // Add new event listeners
            newConfirmButton.addEventListener('click', () => {
                bootstrap.Modal.getInstance(modalElement).hide();
                resolve(true);
            });

            newCancelButton.addEventListener('click', () => {
                bootstrap.Modal.getInstance(modalElement).hide();
                resolve(false);
            });

            // Show modal
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
        });
    }
}

// Global modal manager instance
window.modalManager = new ModalManager();

// Global functions for backward compatibility
window.showAlert = function(message, type = 'info', title = null) {
    window.modalManager.showAlert(message, type, title);
};

window.showSuccess = function(message, title = null) {
    window.modalManager.success(message, title);
};

window.showError = function(message, title = null) {
    window.modalManager.error(message, title);
};

window.showWarning = function(message, title = null) {
    window.modalManager.warning(message, title);
};

window.showInfo = function(message, title = null) {
    window.modalManager.info(message, title);
};

window.showConfirm = function(message, title = 'Potwierdź', confirmText = 'Tak', cancelText = 'Nie') {
    return window.modalManager.showConfirm(message, title, confirmText, cancelText);
};

// Override native alert and confirm functions
window.alert = function(message) {
    window.modalManager.showAlert(message, 'info');
};

window.confirm = function(message) {
    return window.modalManager.showConfirm(message, 'Potwierdź');
};
