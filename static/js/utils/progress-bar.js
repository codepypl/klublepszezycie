/**
 * Universal Progress Bar component for CRM and other admin pages
 */
class ProgressBar {
    constructor(options = {}) {
        this.options = {
            containerId: 'progressContainer',
            showPercentage: true,
            showSpinner: true,
            showMessage: true,
            autoHide: true,
            hideDelay: 2000,
            ...options
        };
        
        this.container = null;
        this.progressBar = null;
        this.messageElement = null;
        this.percentageElement = null;
        this.spinnerElement = null;
        this.isVisible = false;
        
        this.init();
    }
    
    init() {
        this.createContainer();
    }
    
    createContainer() {
        // Create progress bar container
        this.container = document.createElement('div');
        this.container.id = this.options.containerId;
        this.container.className = 'progress-bar-container';
        this.container.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 9999;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(5px);
            border-bottom: 1px solid #e0e0e0;
            display: none;
            padding: 15px 20px;
        `;
        
        // Create progress bar
        this.progressBar = document.createElement('div');
        this.progressBar.className = 'progress';
        this.progressBar.style.cssText = `
            height: 6px;
            background-color: #f0f0f0;
            border-radius: 3px;
            overflow: hidden;
            margin-bottom: 10px;
        `;
        
        const progressFill = document.createElement('div');
        progressFill.className = 'progress-fill';
        progressFill.style.cssText = `
            height: 100%;
            background: linear-gradient(90deg, #007bff, #0056b3);
            border-radius: 3px;
            transition: width 0.3s ease;
            width: 0%;
        `;
        
        this.progressBar.appendChild(progressFill);
        this.container.appendChild(this.progressBar);
        
        // Create message container
        const messageContainer = document.createElement('div');
        messageContainer.className = 'd-flex align-items-center justify-content-between';
        
        // Create message element
        if (this.options.showMessage) {
            this.messageElement = document.createElement('div');
            this.messageElement.className = 'progress-message';
            this.messageElement.style.cssText = `
                font-size: 14px;
                color: #333;
                font-weight: 500;
            `;
            messageContainer.appendChild(this.messageElement);
        }
        
        // Create percentage and spinner container
        const rightContainer = document.createElement('div');
        rightContainer.className = 'd-flex align-items-center gap-3';
        
        // Create percentage element
        if (this.options.showPercentage) {
            this.percentageElement = document.createElement('div');
            this.percentageElement.className = 'progress-percentage';
            this.percentageElement.style.cssText = `
                font-size: 14px;
                color: #666;
                font-weight: 600;
                min-width: 40px;
                text-align: right;
            `;
            rightContainer.appendChild(this.percentageElement);
        }
        
        // Create spinner element
        if (this.options.showSpinner) {
            this.spinnerElement = document.createElement('div');
            this.spinnerElement.className = 'spinner-border spinner-border-sm';
            this.spinnerElement.style.cssText = `
                width: 16px;
                height: 16px;
                border-width: 2px;
                color: #007bff;
            `;
            rightContainer.appendChild(this.spinnerElement);
        }
        
        messageContainer.appendChild(rightContainer);
        this.container.appendChild(messageContainer);
        
        // Add to page
        document.body.appendChild(this.container);
    }
    
    show(message = 'Ładowanie...', progress = 0) {
        this.isVisible = true;
        this.container.style.display = 'block';
        
        if (this.messageElement) {
            this.messageElement.textContent = message;
        }
        
        this.setProgress(progress);
        
        // Add some padding to body to prevent content jump
        document.body.style.paddingTop = '60px';
    }
    
    hide() {
        this.isVisible = false;
        this.container.style.display = 'none';
        document.body.style.paddingTop = '';
        
        if (this.options.autoHide) {
            setTimeout(() => {
                if (!this.isVisible) {
                    this.container.style.display = 'none';
                }
            }, this.options.hideDelay);
        }
    }
    
    setProgress(progress, message = null) {
        const progressFill = this.progressBar.querySelector('.progress-fill');
        const clampedProgress = Math.max(0, Math.min(100, progress));
        
        progressFill.style.width = clampedProgress + '%';
        
        if (this.percentageElement) {
            this.percentageElement.textContent = Math.round(clampedProgress) + '%';
        }
        
        if (message && this.messageElement) {
            this.messageElement.textContent = message;
        }
    }
    
    setMessage(message) {
        if (this.messageElement) {
            this.messageElement.textContent = message;
        }
    }
    
    setIndeterminate(message = 'Przetwarzanie...') {
        const progressFill = this.progressBar.querySelector('.progress-fill');
        progressFill.style.width = '100%';
        progressFill.style.background = 'linear-gradient(90deg, #007bff, #0056b3, #007bff)';
        progressFill.style.backgroundSize = '200% 100%';
        progressFill.style.animation = 'progressIndeterminate 2s linear infinite';
        
        if (this.percentageElement) {
            this.percentageElement.textContent = '...';
        }
        
        if (this.messageElement) {
            this.messageElement.textContent = message;
        }
        
        // Add CSS animation if not exists
        if (!document.getElementById('progressIndeterminateCSS')) {
            const style = document.createElement('style');
            style.id = 'progressIndeterminateCSS';
            style.textContent = `
                @keyframes progressIndeterminate {
                    0% { background-position: 200% 0; }
                    100% { background-position: -200% 0; }
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    setError(message = 'Wystąpił błąd') {
        const progressFill = this.progressBar.querySelector('.progress-fill');
        progressFill.style.width = '100%';
        progressFill.style.background = '#dc3545';
        progressFill.style.animation = 'none';
        
        if (this.percentageElement) {
            this.percentageElement.textContent = '!';
        }
        
        if (this.messageElement) {
            this.messageElement.textContent = message;
        }
        
        if (this.spinnerElement) {
            this.spinnerElement.style.display = 'none';
        }
    }
    
    setSuccess(message = 'Zakończono pomyślnie') {
        const progressFill = this.progressBar.querySelector('.progress-fill');
        progressFill.style.width = '100%';
        progressFill.style.background = '#28a745';
        progressFill.style.animation = 'none';
        
        if (this.percentageElement) {
            this.percentageElement.textContent = '✓';
        }
        
        if (this.messageElement) {
            this.messageElement.textContent = message;
        }
        
        if (this.spinnerElement) {
            this.spinnerElement.style.display = 'none';
        }
    }
}

// Global progress bar instance
window.globalProgressBar = null;

// Initialize global progress bar
document.addEventListener('DOMContentLoaded', function() {
    window.globalProgressBar = new ProgressBar({
        containerId: 'globalProgressBar',
        showPercentage: true,
        showSpinner: true,
        showMessage: true,
        autoHide: true,
        hideDelay: 2000
    });
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProgressBar;
}


