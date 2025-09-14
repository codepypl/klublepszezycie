// Admin Email Templates JavaScript for Lepsze Życie Club

// Global variables
let currentPage = 1;
let currentPerPage = 10;
let currentTemplateId = null;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadTemplates();
    initializeModalListeners();
    
    // Set up pagination handlers for auto-initialization
    window.paginationHandlers = {
        onPageChange: (page) => {
            currentPage = page;
            loadTemplates();
        },
        onPerPageChange: (newPage, perPage) => {
            currentPerPage = perPage;
            currentPage = newPage; // Use the page passed by pagination
            loadTemplates();
        }
    };
});


// Initialize modal listeners
function initializeModalListeners() {
    // No specific modal listeners needed - using universal bulk delete modal
}

// Load templates
function loadTemplates() {
    const params = new URLSearchParams({
        page: currentPage,
        per_page: currentPerPage
    });
    
    fetch(`/api/email/templates?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayTemplates(data.templates);
                if (data.pagination) {
                    // Update pagination if it exists
                    const paginationElement = document.getElementById('pagination');
                    if (paginationElement && paginationElement.paginationInstance) {
                        paginationElement.paginationInstance.setData(data.pagination);
                    }
                }
            } else {
                toastManager.error('Błąd ładowania szablonów: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error loading templates:', error);
            toastManager.error('Błąd ładowania szablonów');
        });
}

// Display templates
function displayTemplates(templates) {
    const tbody = document.getElementById('templatesTableBody');
    tbody.innerHTML = '';
    
    if (templates.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Brak szablonów</td></tr>';
        return;
    }
    
    templates.forEach(template => {
        const row = document.createElement('tr');
        
        // Debug: sprawdź flagę is_default dla szablonu password_reset
        if (template.name === 'password_reset') {
            console.log('🔍 Debug password_reset template:', {
                name: template.name,
                is_default: template.is_default,
                type: typeof template.is_default
            });
        }
        
        // Ukryj checkbox i przycisk usuwania dla domyślnych szablonów
        const checkboxHtml = template.is_default ? 
            '<input type="checkbox" name="itemIds" value="' + template.id + '" disabled title="Nie można usuwać szablonów domyślnych">' :
            '<input type="checkbox" name="itemIds" value="' + template.id + '">';
        
        const deleteButtonHtml = template.is_default ? 
            '<button class="btn btn-sm admin-btn-outline" disabled title="Nie można usuwać szablonów domyślnych"><i class="fas fa-lock"></i></button>' :
            '<button class="btn btn-sm admin-btn-danger" onclick="deleteTemplate(' + template.id + ')" title="Usuń szablon"><i class="fas fa-trash"></i></button>';
        
        row.innerHTML = `
            <td>${checkboxHtml}</td>
            <td>${template.name} ${template.is_default ? '<span class="admin-badge admin-badge-info ms-1">Domyślny</span>' : ''}</td>
            <td>${template.subject}</td>
            <td>${template.template_type}</td>
            <td><span class="admin-badge admin-badge-${template.is_active ? 'success' : 'secondary'}">${template.is_active ? 'Aktywny' : 'Nieaktywny'}</span></td>
            <td>${new Date(template.created_at).toLocaleDateString()}</td>
            <td>
                <div class="btn-group" role="group">
                    <button class="btn btn-sm admin-btn-outline" onclick="editTemplate(${template.id})" title="Edytuj szablon">
                        <i class="fas fa-edit"></i>
                    </button>
                    ${deleteButtonHtml}
                </div>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// Show template modal
function showTemplateModal() {
    document.getElementById('templateForm').reset();
    document.getElementById('template_id').value = '';
    const modal = new bootstrap.Modal(document.getElementById('templateModal'));
    modal.show();
}

// Save template
function saveTemplate() {
    const form = document.getElementById('templateForm');
    const formData = new FormData(form);
    
    const data = {
        name: formData.get('template_name'),
        subject: formData.get('template_subject'),
        template_type: formData.get('template_type'),
        html_content: formData.get('template_html_content'),
        text_content: formData.get('template_text_content'),
        variables: formData.get('template_variables'),
        is_active: formData.get('template_is_active') === 'on'
    };
    
    const templateId = document.getElementById('template_id').value;
    const method = templateId ? 'PUT' : 'POST';
    const url = templateId ? `/api/email/templates/${templateId}` : '/api/email/templates';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toastManager.success('Szablon zapisany pomyślnie!');
            bootstrap.Modal.getInstance(document.getElementById('templateModal')).hide();
            loadTemplates();
        } else {
            toastManager.error('Błąd zapisywania szablonu: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error saving template:', error);
        toastManager.error('Błąd zapisywania szablonu');
    });
}

// Edit template
function editTemplate(templateId) {
    fetch(`/api/email/templates/${templateId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const template = data.template;
                document.getElementById('template_id').value = template.id;
                document.getElementById('template_name').value = template.name;
                document.getElementById('template_subject').value = template.subject;
                document.getElementById('template_type').value = template.template_type;
                document.getElementById('template_html_content').value = template.html_content;
                document.getElementById('template_text_content').value = template.text_content || '';
                document.getElementById('template_variables').value = template.variables || '';
                document.getElementById('template_is_active').checked = template.is_active;
                
                const modal = new bootstrap.Modal(document.getElementById('templateModal'));
                modal.show();
            } else {
                toastManager.error('Błąd ładowania szablonu: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error loading template:', error);
            toastManager.error('Błąd ładowania szablonu');
        });
}

// Delete template
function deleteTemplate(templateId) {
    currentTemplateId = templateId;
    
    // Set up modal for single delete
    document.getElementById('bulkDeleteMessage').innerHTML = 'Czy na pewno chcesz usunąć ten szablon?<br><small class="text-muted">Ta operacja nie może być cofnięta.</small>';
    
    const modalElement = document.getElementById('bulkDeleteModal');
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
    
    // Update confirm button
    const confirmBtn = document.getElementById('confirmBulkDelete');
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    
    newConfirmBtn.onclick = function() {
        // Hide modal first
        modalElement.classList.remove('show');
        modalElement.style.display = 'none';
        document.body.classList.remove('modal-open');
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.remove();
        }
        
        // Then perform delete
        performDeleteTemplate(templateId);
    };
    
    // Update cancel button to properly clean up
    const cancelBtn = modalElement.querySelector('button[data-bs-dismiss="modal"]');
    if (cancelBtn) {
        const newCancelBtn = cancelBtn.cloneNode(true);
        cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
        
        newCancelBtn.onclick = function() {
            // Hide modal
            modalElement.classList.remove('show');
            modalElement.style.display = 'none';
            document.body.classList.remove('modal-open');
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) {
                backdrop.remove();
            }
        };
    }
}

// Perform actual delete operation
function performDeleteTemplate(templateId) {
    fetch(`/api/email/templates/${templateId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toastManager.success('Szablon usunięty!');
            loadTemplates();
        } else {
            toastManager.error('Błąd usuwania: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error deleting template:', error);
        toastManager.error('Błąd usuwania');
    });
}

// Reset templates to default
function resetTemplates() {
    // Set up modal for reset
    document.getElementById('bulkDeleteMessage').innerHTML = 'Czy na pewno chcesz zresetować wszystkie szablony do stanu domyślnego?<br><small class="text-muted">Ta operacja usunie wszystkie istniejące szablony i zastąpi je domyślnymi. Tej operacji nie można cofnąć.</small>';
    
    const modalElement = document.getElementById('bulkDeleteModal');
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
    
    // Update confirm button
    const confirmBtn = document.getElementById('confirmBulkDelete');
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    
    newConfirmBtn.onclick = function() {
        // Hide modal first
        modalElement.classList.remove('show');
        modalElement.style.display = 'none';
        document.body.classList.remove('modal-open');
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.remove();
        }
        
        // Then perform reset
        performResetTemplates();
    };
    
    // Update cancel button to properly clean up
    const cancelBtn = modalElement.querySelector('button[data-bs-dismiss="modal"]');
    if (cancelBtn) {
        const newCancelBtn = cancelBtn.cloneNode(true);
        cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
        
        newCancelBtn.onclick = function() {
            // Hide modal
            modalElement.classList.remove('show');
            modalElement.style.display = 'none';
            document.body.classList.remove('modal-open');
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) {
                backdrop.remove();
            }
        };
    }
}

// Perform actual reset operation
function performResetTemplates() {
    fetch('/api/email/templates/reset', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toastManager.success('Szablony zostały zresetowane do stanu domyślnego!');
            loadTemplates();
        } else {
            toastManager.error('Błąd resetowania: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error resetting templates:', error);
        toastManager.error('Błąd resetowania szablonów');
    });
}

// Make functions globally available
window.resetTemplates = resetTemplates;
window.deleteTemplate = deleteTemplate;

// Cache buster: 1757820821