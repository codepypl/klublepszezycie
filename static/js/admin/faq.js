// Admin FAQ JavaScript for Lepsze Życie Club

// Toast notification system (reused from other admin panels)
class ToastManager {
    constructor() {
        this.container = this.createToastContainer();
    }

    createToastContainer() {
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
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${this.getIcon(type)} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        this.container.appendChild(toast);
        
        // Initialize Bootstrap toast
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: duration
        });
        
        bsToast.show();
        
        // Remove from DOM after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    getIcon(type) {
        const icons = {
            'success': 'check-circle',
            'danger': 'exclamation-triangle',
            'warning': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    success(message, duration = 5000) {
        this.show(message, 'success', duration);
    }

    error(message, duration = 7000) {
        this.show(message, 'danger', duration);
    }

    warning(message, duration = 6000) {
        this.show(message, 'warning', duration);
    }

    info(message, duration = 5000) {
        this.show(message, 'info', duration);
    }
}

// Initialize toast manager
const toastManager = new ToastManager();

// FAQ management functions
class FAQManager {
    constructor() {
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Form submissions
        const addFaqForm = document.getElementById('addFaqForm');
        const editFaqForm = document.getElementById('editFaqForm');
        
        if (addFaqForm) {
            addFaqForm.addEventListener('submit', (e) => this.handleAddFaq(e));
        }
        
        if (editFaqForm) {
            editFaqForm.addEventListener('submit', (e) => this.handleEditFaq(e));
        }
    }

    showAddFaqModal() {
        document.getElementById('addFaqForm').reset();
        const modal = new bootstrap.Modal(document.getElementById('addFaqModal'));
        modal.show();
    }

    editFaq(faqId) {
        fetch(`/admin/api/faq/${faqId}`)
            .then(response => {
                if (!response.ok) {
                    if (response.status === 401 || response.status === 403) {
                        throw new Error('Unauthorized');
                    }
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    const faq = data.faq;
                    document.getElementById('editFaqId').value = faq.id;
                    document.getElementById('editFaqQuestion').value = faq.question;
                    document.getElementById('editFaqAnswer').value = faq.answer;
                    document.getElementById('editFaqOrder').value = faq.order || 1;
                    document.getElementById('editFaqActive').checked = faq.is_active;
                    
                    const modal = new bootstrap.Modal(document.getElementById('editFaqModal'));
                    modal.show();
                } else {
                    toastManager.error('Błąd podczas ładowania pytania: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (error.message === 'Unauthorized') {
                    window.location.href = '/admin/login';
                } else {
                    toastManager.error('Wystąpił błąd podczas ładowania pytania');
                }
            });
    }

    deleteFaq(faqId) {
        if (confirm('Czy na pewno chcesz usunąć to pytanie? Tej operacji nie można cofnąć.')) {
            fetch(`/admin/api/faq?id=${faqId}`, {
                method: 'DELETE'
            })
            .then(response => {
                if (!response.ok) {
                    if (response.status === 401 || response.status === 403) {
                        throw new Error('Unauthorized');
                    }
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    toastManager.success('Pytanie zostało usunięte pomyślnie!');
                    // Usuń wiersz z tabeli
                    const row = document.querySelector(`tr[data-faq-id="${faqId}"]`);
                    if (row) {
                        row.remove();
                    }
                } else {
                    toastManager.error('Błąd podczas usuwania: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (error.message === 'Unauthorized') {
                    window.location.href = '/admin/login';
                } else {
                    toastManager.error('Wystąpił błąd podczas usuwania pytania');
                }
            });
        }
    }

    handleAddFaq(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        formData.append('is_active', document.getElementById('faqActive').checked);
        
        fetch('/admin/api/faq', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                if (response.status === 401 || response.status === 403) {
                    throw new Error('Unauthorized');
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                toastManager.success('Pytanie zostało dodane pomyślnie!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('addFaqModal'));
                modal.hide();
                // Odśwież stronę
                window.location.reload();
            } else {
                toastManager.error('Błąd podczas dodawania: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (error.message === 'Unauthorized') {
                window.location.href = '/admin/login';
            } else {
                toastManager.error('Wystąpił błąd podczas dodawania pytania');
            }
        });
    }

    handleEditFaq(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        formData.append('is_active', document.getElementById('editFaqActive').checked);
        
        fetch('/admin/api/faq', {
            method: 'PUT',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                if (response.status === 401 || response.status === 403) {
                    throw new Error('Unauthorized');
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                toastManager.success('Pytanie zostało zaktualizowane pomyślnie!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('editFaqModal'));
                modal.hide();
                // Odśwież stronę
                window.location.reload();
            } else {
                toastManager.error('Błąd podczas aktualizacji: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (error.message === 'Unauthorized') {
                window.location.href = '/admin/login';
            } else {
                toastManager.error('Wystąpił błąd podczas aktualizacji pytania');
            }
        });
    }
}

// Global functions for backward compatibility
function showAddFaqModal() {
    faqManager.showAddFaqModal();
}

function editFaq(faqId) {
    faqManager.editFaq(faqId);
}

function deleteFaq(faqId) {
    faqManager.deleteFaq(faqId);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.faqManager = new FAQManager();
});
