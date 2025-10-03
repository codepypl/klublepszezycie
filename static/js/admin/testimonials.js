// Toast manager is loaded globally from utils/toast.js

class TestimonialsManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initBulkDelete();
    }

    setupEventListeners() {
        // Form submissions
        document.getElementById('addTestimonialForm').addEventListener('submit', (e) => this.handleAddTestimonial(e));
        document.getElementById('editTestimonialForm').addEventListener('submit', (e) => this.handleEditTestimonial(e));
    }

    initBulkDelete() {
        if (typeof BulkDeleteManager !== 'undefined') {
            this.bulkDeleteManager = new BulkDeleteManager('testimonials', '/api/testimonials');
        }
    }

    showAddTestimonialModal() {
        document.getElementById('addTestimonialForm').reset();
        const modal = new bootstrap.Modal(document.getElementById('addTestimonialModal'));
        modal.show();
    }

    editTestimonial(testimonialId) {
        fetch(`/api/testimonials/${testimonialId}`)
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
                    const testimonial = data.testimonial;
                    document.getElementById('editTestimonialId').value = testimonial.id;
                    document.getElementById('editTestimonialAuthor').value = testimonial.author_name;
                    document.getElementById('editTestimonialContent').value = testimonial.content;
                    document.getElementById('editTestimonialMemberSince').value = testimonial.member_since;
                    document.getElementById('editTestimonialRating').value = testimonial.rating;
                    document.getElementById('editTestimonialOrder').value = testimonial.order || 0;
                    document.getElementById('editTestimonialActive').checked = testimonial.is_active;
                    
                    const modal = new bootstrap.Modal(document.getElementById('editTestimonialModal'));
                    modal.show();
                } else {
                    window.toastManager.error('Błąd podczas ładowania opinii: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                window.toastManager.error('Wystąpił błąd podczas ładowania opinii');
            });
    }

    deleteTestimonial(testimonialId) {
        window.deleteConfirmation.showSingleDelete(
            'opinię',
            () => {
                // Continue with deletion
                performDeleteTestimonial(testimonialId);
            },
            'opinię'
        );
    }

    performDeleteTestimonial(testimonialId) {
        fetch(`/api/testimonials/${testimonialId}`, {
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
                window.toastManager.success('Opinia została usunięta pomyślnie!');
                
                // Wywołaj globalne odświeżenie
                window.refreshAfterCRUD();
            } else {
                window.toastManager.error('Błąd podczas usuwania: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            window.toastManager.error('Wystąpił błąd podczas usuwania opinii');
        });
    }

    handleAddTestimonial(e) {
        e.preventDefault();
        
        const jsonData = {
            author_name: document.getElementById('testimonialAuthor').value,
            content: document.getElementById('testimonialContent').value,
            member_since: document.getElementById('testimonialMemberSince').value,
            rating: parseInt(document.getElementById('testimonialRating').value) || 5,
            order: parseInt(document.getElementById('testimonialOrder').value) || 0,
            is_active: document.getElementById('testimonialActive').checked
        };
        
        fetch('/api/testimonials', {
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
                window.toastManager.success('Opinia została dodana pomyślnie!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('addTestimonialModal'));
                modal.hide();
                
                // Wywołaj globalne odświeżenie
                window.refreshAfterCRUD();
            } else {
                window.toastManager.error('Błąd podczas dodawania: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            window.toastManager.error('Wystąpił błąd podczas dodawania opinii');
        });
    }

    handleEditTestimonial(e) {
        e.preventDefault();
        
        const testimonialId = document.getElementById('editTestimonialId').value;
        const jsonData = {
            author_name: document.getElementById('editTestimonialAuthor').value,
            content: document.getElementById('editTestimonialContent').value,
            member_since: document.getElementById('editTestimonialMemberSince').value,
            rating: parseInt(document.getElementById('editTestimonialRating').value) || 5,
            order: parseInt(document.getElementById('editTestimonialOrder').value) || 0,
            is_active: document.getElementById('editTestimonialActive').checked
        };
        
        fetch(`/api/testimonials/${testimonialId}`, {
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
                window.toastManager.success('Opinia została zaktualizowana pomyślnie!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('editTestimonialModal'));
                modal.hide();
                
                // Wywołaj globalne odświeżenie
                window.refreshAfterCRUD();
            } else {
                window.toastManager.error('Błąd podczas aktualizacji: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            window.toastManager.error('Wystąpił błąd podczas aktualizacji opinii');
        });
    }

    // Load testimonials data from paginated API response
    loadTestimonialsData(testimonials) {
        console.log('🔍 loadTestimonialsData called with:', testimonials);
        // This method can be used to update the testimonials display
        // The existing testimonials.js already handles testimonial management
        // We just need to ensure the data is available for the pagination system
    }
}

// Global functions for template onclick handlers
let testimonialsManager;

function showAddTestimonialModal() {
    if (testimonialsManager) {
        testimonialsManager.showAddTestimonialModal();
    }
}

function editTestimonial(testimonialId) {
    if (testimonialsManager) {
        testimonialsManager.editTestimonial(testimonialId);
    }
}

function deleteTestimonial(testimonialId) {
    if (testimonialsManager) {
        testimonialsManager.deleteTestimonial(testimonialId);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.testimonialsManager = new TestimonialsManager();
    testimonialsManager = window.testimonialsManager; // For backward compatibility
});
