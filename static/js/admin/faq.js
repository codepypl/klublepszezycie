// Admin FAQ JavaScript for Lepsze Życie Club

// Toast manager is loaded globally from utils/toast.js

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
        fetch(`/api/faq/${faqId}`)
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
                    window.toastManager.error('Błąd podczas ładowania pytania: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (error.message === 'Unauthorized') {
                    window.location.href = '/admin/login';
                } else {
                    window.toastManager.error('Wystąpił błąd podczas ładowania pytania');
                }
            });
    }

    deleteFaq(faqId) {
        // Use Bootstrap modal instead of confirm()
        const modal = document.getElementById('bulkDeleteModal');
        const messageElement = document.getElementById('bulkDeleteMessage');
        const confirmButton = document.getElementById('confirmBulkDelete');
        const cancelButton = modal.querySelector('button[data-bs-dismiss="modal"]');
        
        if (modal && messageElement && confirmButton) {
            // Update message
            messageElement.textContent = 'Czy na pewno chcesz usunąć to pytanie? Tej operacji nie można cofnąć.';
            
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
                this.performDeleteFaq(faqId);
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
            const self = this;
            window.deleteConfirmation.showSingleDelete(
                'pytanie',
                () => {
                    // Continue with deletion - use class method
                    self.performDeleteFaq(faqId);
                },
                'pytanie'
            );
        }
    }

    performDeleteFaq(faqId) {
        fetch(`/api/faq/${faqId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
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
                window.toastManager.success('Pytanie zostało usunięte pomyślnie!');
                // Usuń wiersz z tabeli
                const row = document.querySelector(`tr[data-faq-id="${faqId}"]`);
                if (row) {
                    row.remove();
                }
                
                // Wywołaj globalne odświeżenie
                window.refreshAfterCRUD();
            } else {
                window.toastManager.error('Błąd podczas usuwania: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (error.message === 'Unauthorized') {
                window.location.href = '/admin/login';
            } else {
                window.toastManager.error('Wystąpił błąd podczas usuwania pytania');
            }
        });
    }

    handleAddFaq(e) {
        e.preventDefault();
        
        const jsonData = {
            question: document.getElementById('faqQuestion').value,
            answer: document.getElementById('faqAnswer').value,
            order: parseInt(document.getElementById('faqOrder').value) || 0,
            is_active: document.getElementById('faqActive').checked
        };
        
        fetch('/api/faq', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(jsonData)
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
                window.toastManager.success('Pytanie zostało dodane pomyślnie!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('addFaqModal'));
                modal.hide();
                // Wywołaj globalne odświeżenie
                window.refreshAfterCRUD();
            } else {
                window.toastManager.error('Błąd podczas dodawania: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (error.message === 'Unauthorized') {
                window.location.href = '/admin/login';
            } else {
                window.toastManager.error('Wystąpił błąd podczas dodawania pytania');
            }
        });
    }

    handleEditFaq(e) {
        e.preventDefault();
        
        const faqId = document.getElementById('editFaqId').value;
        const jsonData = {
            question: document.getElementById('editFaqQuestion').value,
            answer: document.getElementById('editFaqAnswer').value,
            order: parseInt(document.getElementById('editFaqOrder').value) || 0,
            is_active: document.getElementById('editFaqActive').checked
        };
        
        fetch(`/api/faq/${faqId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(jsonData)
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
                window.toastManager.success('Pytanie zostało zaktualizowane pomyślnie!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('editFaqModal'));
                modal.hide();
                // Wywołaj globalne odświeżenie
                window.refreshAfterCRUD();
            } else {
                window.toastManager.error('Błąd podczas aktualizacji: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (error.message === 'Unauthorized') {
                window.location.href = '/admin/login';
            } else {
                window.toastManager.error('Wystąpił błąd podczas aktualizacji pytania');
            }
        });
    }

    // Load FAQs data from paginated API response
    loadFAQsData(faqs) {
        console.log('🔍 loadFAQsData called with:', faqs);
        // This method can be used to update the FAQs display
        // The existing faq.js already handles FAQ management
        // We just need to ensure the data is available for the pagination system
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
    // Check if toastManager is available
    if (typeof window.toastManager === 'undefined') {
        console.error('ToastManager not loaded! Make sure toast.js is loaded before faq.js');
    }
    window.faqManager = new FAQManager();
});
