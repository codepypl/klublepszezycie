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
            container.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 20px;
                z-index: 9999;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
        return container;
    }

    show(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `alert alert-dismissible fade show`;
        
        // Custom styling based on type
        let bgColor, textColor, borderColor;
        switch(type) {
            case 'success':
                bgColor = '#000000';
                textColor = '#ffffff';
                borderColor = '#28a745';
                break;
            case 'error':
            case 'danger':
                bgColor = '#dc3545';
                textColor = '#ffffff';
                borderColor = '#dc3545';
                break;
            case 'warning':
                bgColor = '#ffc107';
                textColor = '#000000';
                borderColor = '#ffc107';
                break;
            case 'info':
            default:
                bgColor = '#17a2b8';
                textColor = '#ffffff';
                borderColor = '#17a2b8';
                break;
        }
        
        toast.style.cssText = `
            background-color: ${bgColor};
            color: ${textColor};
            border: 1px solid ${borderColor};
            border-radius: 0.375rem;
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
            box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        `;
        
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
