// Admin Panel JavaScript for Lepsze Życie Club

document.addEventListener('DOMContentLoaded', function() {
    // Initialize admin panel functionality
    initializeAdminPanel();
});

function initializeAdminPanel() {
    // Add event listeners for form changes
    addFormChangeListeners();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize auto-save functionality
    initializeAutoSave();
}

function addFormChangeListeners() {
    // Add change listeners to all form inputs
    const formInputs = document.querySelectorAll('input, textarea, select');
    formInputs.forEach(input => {
        input.addEventListener('change', function() {
            markFieldAsChanged(this);
        });
        
        input.addEventListener('input', function() {
            markFieldAsChanged(this);
        });
    });
}

function markFieldAsChanged(field) {
    // Add visual indication that field has changed
    field.classList.add('is-changed');
    field.style.borderColor = '#10b981';
    
    // Remove the class after a delay
    setTimeout(() => {
        field.classList.remove('is-changed');
        field.style.borderColor = '';
    }, 2000);
}

function initializeTooltips() {
    // Initialize Bootstrap tooltips if available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

function initializeAutoSave() {
    // Auto-save functionality every 30 seconds
    setInterval(() => {
        const changedFields = document.querySelectorAll('.is-changed');
        if (changedFields.length > 0) {
            console.log('Auto-saving changes...');
            // You can implement auto-save here if needed
        }
    }, 30000);
}

// Content Management Functions
function saveAllChanges() {
    const saveButton = document.querySelector('button[onclick="saveAllChanges()"]');
    const originalText = saveButton.innerHTML;
    
    // Show loading state
    saveButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Zapisywanie...';
    saveButton.disabled = true;
    
    // Collect all content changes
    const contentUpdates = collectContentUpdates();
    
    // Save all changes
    Promise.all(contentUpdates.map(update => saveContentSection(update)))
        .then(results => {
            const successCount = results.filter(result => result.success).length;
            const totalCount = results.length;
            
            if (successCount === totalCount) {
                showSuccessMessage('Wszystkie zmiany zostały zapisane pomyślnie!');
                // Remove changed indicators
                document.querySelectorAll('.is-changed').forEach(field => {
                    field.classList.remove('is-changed');
                });
            } else {
                showErrorMessage(`Zapisano ${successCount} z ${totalCount} zmian. Sprawdź błędy i spróbuj ponownie.`);
            }
        })
        .catch(error => {
            console.error('Error saving content:', error);
            showErrorMessage('Wystąpił błąd podczas zapisywania. Spróbuj ponownie.');
        })
        .finally(() => {
            // Reset button
            saveButton.innerHTML = originalText;
            saveButton.disabled = false;
        });
}

function collectContentUpdates() {
    const updates = [];
    const contentFields = document.querySelectorAll('[data-section]');
    
    contentFields.forEach(field => {
        const sectionName = field.dataset.section;
        let title = null;
        let content = null;
        
        // Determine if this is a title or content field
        if (sectionName.includes('title')) {
            title = field.value;
        } else {
            content = field.value;
        }
        
        // Find existing update or create new one
        let existingUpdate = updates.find(update => update.section_name === sectionName);
        if (existingUpdate) {
            if (title) existingUpdate.title = title;
            if (content) existingUpdate.content = content;
        } else {
            updates.push({
                section_name: sectionName,
                title: title,
                content: content
            });
        }
    });
    
    return updates;
}

function saveContentSection(updateData) {
    return fetch('/admin/api/update-content', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log(`Content section ${updateData.section_name} updated successfully`);
            return { success: true, section: updateData.section_name };
        } else {
            console.error(`Error updating content section ${updateData.section_name}:`, data.message);
            return { success: false, section: updateData.section_name, error: data.message };
        }
    })
    .catch(error => {
        console.error(`Network error updating content section ${updateData.section_name}:`, error);
        return { success: false, section: updateData.section_name, error: error.message };
    });
}

// Testimonial Management Functions
function addTestimonial() {
    const form = document.getElementById('testimonialForm');
    const formData = new FormData(form);
    
    const testimonialData = {
        author_name: formData.get('author_name'),
        content: formData.get('content'),
        member_since: formData.get('member_since')
    };
    
    fetch('/admin/api/testimonials', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(testimonialData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccessMessage('Opinia została dodana pomyślnie!');
            form.reset();
            // Optionally refresh the testimonials list
            location.reload();
        } else {
            showErrorMessage('Błąd podczas dodawania opinii: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error adding testimonial:', error);
        showErrorMessage('Wystąpił błąd podczas dodawania opinii.');
    });
}

function updateTestimonial(testimonialId) {
    const form = document.getElementById(`testimonialForm${testimonialId}`);
    const formData = new FormData(form);
    
    const testimonialData = {
        author_name: formData.get('author_name'),
        content: formData.get('content'),
        member_since: formData.get('member_since'),
        is_active: formData.get('is_active') === 'on'
    };
    
    fetch(`/admin/api/testimonials/${testimonialId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(testimonialData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccessMessage('Opinia została zaktualizowana pomyślnie!');
        } else {
            showErrorMessage('Błąd podczas aktualizacji opinii: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error updating testimonial:', error);
        showErrorMessage('Wystąpił błąd podczas aktualizacji opinii.');
    });
}

function deleteTestimonial(testimonialId) {
    // Use Bootstrap modal instead of confirm()
    const modal = document.getElementById('bulkDeleteModal');
    const messageElement = document.getElementById('bulkDeleteMessage');
    const confirmButton = document.getElementById('confirmBulkDelete');
    
    if (modal && messageElement && confirmButton) {
        // Update message
        messageElement.textContent = 'Czy na pewno chcesz usunąć tę opinię? Tej operacji nie można cofnąć.';
        
        // Remove existing event listeners
        const newConfirmButton = confirmButton.cloneNode(true);
        confirmButton.parentNode.replaceChild(newConfirmButton, confirmButton);
        
        // Add new event listener
        newConfirmButton.addEventListener('click', () => {
            bootstrap.Modal.getInstance(modal).hide();
            performDeleteTestimonial(testimonialId);
        });
        
        // Show modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    } else {
        // Fallback to confirm() if modal not available
        if (confirm('Czy na pewno chcesz usunąć tę opinię? Tej operacji nie można cofnąć.')) {
            performDeleteTestimonial(testimonialId);
        }
    }
}

function performDeleteTestimonial(testimonialId) {
    fetch(`/admin/api/testimonials/${testimonialId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccessMessage('Opinia została usunięta pomyślnie!');
            // Remove the testimonial from the DOM
            const testimonialElement = document.getElementById(`testimonial${testimonialId}`);
            if (testimonialElement) {
                testimonialElement.remove();
            }
        } else {
            showErrorMessage('Błąd podczas usuwania opinii: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error deleting testimonial:', error);
        showErrorMessage('Wystąpił błąd podczas usuwania opinii.');
    });
}

// Utility Functions
function showSuccessMessage(message) {
    const successModal = new bootstrap.Modal(document.getElementById('successModal'));
    document.getElementById('successMessage').textContent = message;
    successModal.show();
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        successModal.hide();
    }, 3000);
}

function showErrorMessage(message) {
    // Create a temporary error alert
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed';
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Export functionality
function exportRegistrations() {
    fetch('/admin/registrations/export')
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'registrations.csv';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        })
        .catch(error => {
            console.error('Error exporting registrations:', error);
            showErrorMessage('Błąd podczas eksportowania rejestracji.');
        });
}

// Search and filter functionality
function filterTestimonials(searchTerm) {
    const testimonials = document.querySelectorAll('.testimonial-item');
    const searchLower = searchTerm.toLowerCase();
    
    testimonials.forEach(testimonial => {
        const text = testimonial.textContent.toLowerCase();
        if (text.includes(searchLower)) {
            testimonial.style.display = '';
        } else {
            testimonial.style.display = 'none';
        }
    });
}

function filterRegistrations(searchTerm) {
    const registrations = document.querySelectorAll('.registration-item');
    const searchLower = searchTerm.toLowerCase();
    
    registrations.forEach(registration => {
        const text = registration.textContent.toLowerCase();
        if (text.includes(searchLower)) {
            registration.style.display = '';
        } else {
            registration.style.display = 'none';
        }
    });
}

// Add CSS for changed fields
const style = document.createElement('style');
style.textContent = `
    .is-changed {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 0.2rem rgba(16, 185, 129, 0.25) !important;
    }
    
    .admin-card {
        transition: all 0.3s ease;
    }
    
    .admin-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .form-control:focus {
        border-color: #10b981;
        box-shadow: 0 0 0 0.2rem rgba(16, 185, 129, 0.25);
    }
`;

document.head.appendChild(style);

// Sidebar Toggle Functionality
function toggleSidebar() {
    const sidebar = document.getElementById('adminSidebar');
    const mainContent = document.querySelector('.admin-content');
    
    if (sidebar.classList.contains('collapsed')) {
        // Expand sidebar
        sidebar.classList.remove('collapsed');
        if (mainContent) {
            mainContent.style.marginLeft = '280px';
            mainContent.style.marginRight = '';
            mainContent.style.maxWidth = '';
        }
        localStorage.setItem('sidebarCollapsed', 'false');
    } else {
        // Collapse sidebar
        sidebar.classList.add('collapsed');
        if (mainContent) {
            mainContent.style.marginLeft = 'auto';
            mainContent.style.marginRight = 'auto';
            mainContent.style.maxWidth = 'calc(100vw - 70px)';
        }
        localStorage.setItem('sidebarCollapsed', 'true');
    }
}

// Initialize sidebar state from localStorage
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('adminSidebar');
    const mainContent = document.querySelector('.admin-content');
    const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    
    if (isCollapsed) {
        sidebar.classList.add('collapsed');
        if (mainContent) {
            mainContent.style.marginLeft = 'auto';
            mainContent.style.marginRight = 'auto';
            mainContent.style.maxWidth = 'calc(100vw - 70px)';
        }
    } else {
        if (mainContent) {
            mainContent.style.marginLeft = '280px';
            mainContent.style.marginRight = '';
            mainContent.style.maxWidth = '';
        }
    }
});

