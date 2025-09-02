// Admin Benefits JavaScript for Lepsze Życie Club

// Toast notification system (reused from sections)
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

// Benefits management functions
class BenefitsManager {
    constructor() {
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Form submissions
        const addBenefitForm = document.getElementById('addBenefitForm');
        const editBenefitForm = document.getElementById('editBenefitForm');
        
        if (addBenefitForm) {
            addBenefitForm.addEventListener('submit', (e) => this.handleAddBenefit(e));
        }
        
        if (editBenefitForm) {
            editBenefitForm.addEventListener('submit', (e) => this.handleEditBenefit(e));
        }
    }

    showAddBenefitModal() {
        document.getElementById('addBenefitForm').reset();
        const modal = new bootstrap.Modal(document.getElementById('addBenefitModal'));
        modal.show();
    }

    editBenefit(benefitId) {
        fetch(`/admin/api/benefits/${benefitId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const benefit = data.benefit;
                    document.getElementById('editBenefitId').value = benefit.id;
                    document.getElementById('editBenefitTitle').value = benefit.title;
                    document.getElementById('editBenefitDescription').value = benefit.description;
                    document.getElementById('editBenefitIcon').value = benefit.icon || '';
                    document.getElementById('editBenefitOrder').value = benefit.order || 1;
                    document.getElementById('editBenefitActive').checked = benefit.is_active;
                    
                    // Show current image if exists
                    const currentImagePreview = document.getElementById('currentImagePreview');
                    const currentImage = document.getElementById('currentImage');
                    if (benefit.image) {
                        currentImage.src = `/static/${benefit.image}`;
                        currentImagePreview.style.display = 'block';
                    } else {
                        currentImagePreview.style.display = 'none';
                    }
                    
                    const modal = new bootstrap.Modal(document.getElementById('editBenefitModal'));
                    modal.show();
                } else {
                    toastManager.error('Błąd podczas ładowania korzyści: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                toastManager.error('Wystąpił błąd podczas ładowania korzyści');
            });
    }

    deleteBenefit(benefitId) {
        if (confirm('Czy na pewno chcesz usunąć tę korzyść? Tej operacji nie można cofnąć.')) {
            fetch(`/admin/api/benefits?id=${benefitId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    toastManager.success('Korzyść została usunięta pomyślnie!');
                    // Usuń wiersz z tabeli
                    const row = document.querySelector(`tr[data-benefit-id="${benefitId}"]`);
                    if (row) {
                        row.remove();
                    }
                } else {
                    toastManager.error('Błąd podczas usuwania: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                toastManager.error('Wystąpił błąd podczas usuwania korzyści');
            });
        }
    }

    handleAddBenefit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        formData.append('is_active', document.getElementById('benefitActive').checked);
        
        fetch('/admin/api/benefits', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                toastManager.success('Korzyść została dodana pomyślnie!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('addBenefitModal'));
                modal.hide();
                // Odśwież stronę
                window.location.reload();
            } else {
                toastManager.error('Błąd podczas dodawania: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            toastManager.error('Wystąpił błąd podczas dodawania korzyści');
        });
    }

    handleEditBenefit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        formData.append('is_active', document.getElementById('editBenefitActive').checked);
        
        fetch('/admin/api/benefits', {
            method: 'PUT',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                toastManager.success('Korzyść została zaktualizowana pomyślnie!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('editBenefitModal'));
                modal.hide();
                // Odśwież stronę
                window.location.reload();
            } else {
                toastManager.error('Błąd podczas aktualizacji: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            toastManager.error('Wystąpił błąd podczas aktualizacji korzyści');
        });
    }
}

// Global functions for backward compatibility
function showAddBenefitModal() {
    benefitsManager.showAddBenefitModal();
}

function editBenefit(benefitId) {
    benefitsManager.editBenefit(benefitId);
}

function deleteBenefit(benefitId) {
    benefitsManager.deleteBenefit(benefitId);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.benefitsManager = new BenefitsManager();
});
