// Toast Manager class
class ToastManager {
    constructor() {
        this.container = this.createContainer();
    }

    createContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            document.body.appendChild(container);
        }
        return container;
    }

    show(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show`;
        
        // Use white close button for dark backgrounds
        const closeButtonClass = (type === 'success' || type === 'danger' || type === 'error') 
            ? 'btn-close btn-close-white' 
            : 'btn-close';
        
        toast.innerHTML = `
            ${message}
            <button type="button" class="${closeButtonClass}" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        this.container.appendChild(toast);
        
        // Auto remove after duration
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, duration);
    }

    success(message) {
        this.show(message, 'success');
    }

    error(message) {
        this.show(message, 'danger');
    }

    info(message) {
        this.show(message, 'info');
    }

    warning(message) {
        this.show(message, 'warning');
    }
}

// Initialize global toast manager
window.toastManager = new ToastManager();
