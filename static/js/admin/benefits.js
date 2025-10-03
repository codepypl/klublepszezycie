// Admin Benefits JavaScript for Lepsze Życie Club

// Toast manager is loaded globally from utils/toast.js

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
        fetch(`/api/benefits/${benefitId}`)
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
                    window.toastManager.error('Błąd podczas ładowania korzyści: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                window.toastManager.error('Wystąpił błąd podczas ładowania korzyści');
            });
    }

    deleteBenefit(benefitId) {
        // Use Bootstrap modal instead of confirm()
        const modal = document.getElementById('bulkDeleteModal');
        const messageElement = document.getElementById('bulkDeleteMessage');
        const confirmButton = document.getElementById('confirmBulkDelete');
        const cancelButton = modal.querySelector('button[data-bs-dismiss="modal"]');
        
        if (modal && messageElement && confirmButton) {
            // Update message
            messageElement.textContent = 'Czy na pewno chcesz usunąć tę korzyść? Tej operacji nie można cofnąć.';
            
            // Remove existing event listeners
            const newConfirmButton = confirmButton.cloneNode(true);
            // Check if parent node exists before replacing
if (confirmButton.parentNode) {
    confirmButton.parentNode.replaceChild(newConfirmButton, confirmButton);
} else {
    console.warn('Confirm button parent node not found');
}
            
            // Add new event listener for confirm button
            newConfirmButton.addEventListener('click', () => {
                // Hide modal first
                modal.classList.remove('show');
                modal.style.display = 'none';
                document.body.classList.remove('modal-open');
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) {
                    backdrop.remove();
                }
                
                // Then perform delete
                this.performDeleteBenefit(benefitId);
            });
            
            // Add event listener for cancel button to properly clean up
            if (cancelButton) {
                const newCancelButton = cancelButton.cloneNode(true);
                // Check if parent node exists before replacing
if (cancelButton.parentNode) {
    cancelButton.parentNode.replaceChild(newCancelButton, cancelButton);
} else {
    console.warn('Cancel button parent node not found');
}
                
                newCancelButton.addEventListener('click', () => {
                    // Hide modal
                    modal.classList.remove('show');
                    modal.style.display = 'none';
                    document.body.classList.remove('modal-open');
                    const backdrop = document.querySelector('.modal-backdrop');
                    if (backdrop) {
                        backdrop.remove();
                    }
                });
            }
            
            // Show modal
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        } else {
            // Fallback to confirm() if modal not available
            window.deleteConfirmation.showSingleDelete(
                'korzyść',
                () => {
                    // Continue with deletion
                    performDeleteBenefit(benefitId);
                },
                'korzyść'
            );
        }
    }

    performDeleteBenefit(benefitId) {
        fetch(`/api/benefits/${benefitId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.toastManager.success('Korzyść została usunięta pomyślnie!');
                // Usuń wiersz z tabeli
                const row = document.querySelector(`tr[data-benefit-id="${benefitId}"]`);
                if (row) {
                    row.remove();
                }
                
                // Wywołaj globalne odświeżenie
                if (typeof window.refreshAfterCRUD === 'function') {
                    window.refreshAfterCRUD();
                } else {
                    console.warn('window.refreshAfterCRUD is not available');
                }
            } else {
                window.toastManager.error('Błąd podczas usuwania: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            window.toastManager.error('Wystąpił błąd podczas usuwania korzyści');
        });
    }

    handleAddBenefit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const data = {
            title: formData.get('title'),
            description: formData.get('description'),
            icon: formData.get('icon'),
            order: parseInt(formData.get('order')) || 0,
            is_active: formData.get('is_active') === 'on'
        };
        
        fetch('/api/benefits', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.toastManager.success('Korzyść została dodana pomyślnie!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('addBenefitModal'));
                modal.hide();
                // Wywołaj globalne odświeżenie
                if (typeof window.refreshAfterCRUD === 'function') {
                    window.refreshAfterCRUD();
                } else {
                    console.warn('window.refreshAfterCRUD is not available');
                }
            } else {
                window.toastManager.error('Błąd podczas dodawania: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            window.toastManager.error('Wystąpił błąd podczas dodawania korzyści');
        });
    }

    handleEditBenefit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const benefitId = formData.get('editBenefitId');
        const data = {
            title: formData.get('title'),
            description: formData.get('description'),
            icon: formData.get('icon'),
            order: parseInt(formData.get('order')) || 0,
            is_active: formData.get('is_active') === 'on'
        };
        
        fetch(`/api/benefits/${benefitId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.toastManager.success('Korzyść została zaktualizowana pomyślnie!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('editBenefitModal'));
                modal.hide();
                // Wywołaj globalne odświeżenie
                if (typeof window.refreshAfterCRUD === 'function') {
                    window.refreshAfterCRUD();
                } else {
                    console.warn('window.refreshAfterCRUD is not available');
                }
            } else {
                window.toastManager.error('Błąd podczas aktualizacji: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            window.toastManager.error('Wystąpił błąd podczas aktualizacji korzyści');
        });
    }

    // Load benefits data from paginated API response
    loadBenefitsData(benefits) {
        console.log('🔍 loadBenefitsData called with:', benefits);
        // This method can be used to update the benefits display
        // The existing benefits.js already handles benefit management
        // We just need to ensure the data is available for the pagination system
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
