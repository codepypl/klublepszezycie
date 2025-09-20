// Admin Email Templates JavaScript for Lepsze Życie Club

// Global variables
let currentPage = 1;
let currentPerPage = 10;
let currentTemplateId = null;
let tinymceInstance = null;
let isTextContentManuallyEdited = false;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadTemplates();
    initializeModalListeners();
    
    // Check for edit parameter in URL
    const urlParams = new URLSearchParams(window.location.search);
    const editTemplateId = urlParams.get('edit');
    if (editTemplateId) {
        // Automatically open edit modal for the specified template
        setTimeout(() => {
            editTemplate(parseInt(editTemplateId));
        }, 1000); // Wait for templates to load
    }
    
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
    // Clean up TinyMCE when modal is hidden
    const templateModal = document.getElementById('templateModal');
    if (templateModal) {
        templateModal.addEventListener('hidden.bs.modal', function () {
            if (tinymceInstance) {
                tinymceInstance.destroy();
                tinymceInstance = null;
            }
            isTextContentManuallyEdited = false;
        });
    }
    
    // Track manual editing of text content
    const textContentField = document.getElementById('template_text_content');
    if (textContentField) {
        // Only set manual edit flag if user actually types something
        let userTyping = false;
        let typingTimeout;
        
        textContentField.addEventListener('input', function() {
            userTyping = true;
            clearTimeout(typingTimeout);
            typingTimeout = setTimeout(() => {
                if (userTyping) {
                    isTextContentManuallyEdited = true;
                }
            }, 1000); // Set manual edit flag only after 1 second of no typing
        });
        
        // Reset flag when field is focused (user might want to edit)
        textContentField.addEventListener('focus', function() {
            // Don't immediately set manual edit flag on focus
        });
        
        // Show hint when user starts editing (only once)
        let hintShown = false;
        textContentField.addEventListener('input', function() {
            if (isTextContentManuallyEdited && tinymceInstance && !hintShown) {
                tinymceInstance.notificationManager.open({
                    text: 'Synchronizacja z HTML została wyłączona. Kliknij "Przywróć synchronizację" aby włączyć automatyczne uzupełnianie.',
                    type: 'info',
                    timeout: 5000
                });
                hintShown = true;
            }
        });
        
        // Add button to reset manual edit flag
        const resetSyncButton = document.createElement('button');
        resetSyncButton.type = 'button';
        resetSyncButton.className = 'btn btn-sm btn-outline-secondary ms-2';
        resetSyncButton.innerHTML = '<i class="fas fa-sync me-1"></i>Przywróć synchronizację';
        resetSyncButton.style.display = 'none';
        resetSyncButton.onclick = function() {
            isTextContentManuallyEdited = false;
            hintShown = false;
            this.style.display = 'none';
            
            // Sync current HTML content to text
            if (tinymceInstance) {
                const htmlContent = tinymceInstance.getContent();
                const textContent = stripHtml(htmlContent);
                textContentField.value = textContent;
                
                tinymceInstance.notificationManager.open({
                    text: 'Synchronizacja została przywrócona.',
                    type: 'success',
                    timeout: 2000
                });
            }
        };
        
        // Show reset button when manual edit is detected
        textContentField.addEventListener('input', function() {
            if (isTextContentManuallyEdited) {
                resetSyncButton.style.display = 'inline-block';
            }
        });
        
        // Insert button after text content field
        textContentField.parentNode.insertBefore(resetSyncButton, textContentField.nextSibling);
    }
}

// Initialize TinyMCE
function initializeTinyMCE() {
    if (tinymceInstance) {
        tinymceInstance.destroy();
    }
    
    tinymce.init({
        selector: '#template_html_content',
        height: 400,
        menubar: false,
        plugins: [
            'advlist', 'autolink', 'lists', 'link', 'charmap', 'preview',
            'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
            'insertdatetime', 'table', 'help', 'wordcount', 'emoticons'
        ],
        toolbar: 'undo redo | blocks | ' +
            'bold italic underline strikethrough | forecolor backcolor | ' +
            'alignleft aligncenter alignright alignjustify | ' +
            'bullist numlist outdent indent | ' +
            'link table | variables | syncTextContent | removeformat | code | help',
        content_style: 'body { font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; }',
        branding: false,
        promotion: false,
        setup: function (editor) {
            tinymceInstance = editor;
            
            // Add variables button
            editor.ui.registry.addButton('variables', {
                text: 'Zmienne',
                tooltip: 'Wstaw zmienną szablonu',
                onAction: function () {
                    showVariablesDialog(editor);
                }
            });
            
            // Synchronize with text content on change
            editor.on('input change keyup', function () {
                if (!isTextContentManuallyEdited) {
                    const htmlContent = editor.getContent();
                    const textContent = stripHtml(htmlContent);
                    document.getElementById('template_text_content').value = textContent;
                }
            });
            
            // Add manual sync button to TinyMCE toolbar
            editor.ui.registry.addButton('syncTextContent', {
                text: 'Sync Text',
                tooltip: 'Synchronizuj z wersją tekstową',
                onAction: function () {
                    const htmlContent = editor.getContent();
                    const textContent = stripHtml(htmlContent);
                    const textField = document.getElementById('template_text_content');
                    if (textField) {
                        textField.value = textContent;
                        editor.notificationManager.open({
                            text: 'Wersja tekstowa została zsynchronizowana z HTML.',
                            type: 'success',
                            timeout: 2000
                        });
                    }
                }
            });
            
            // Also sync on paste and undo/redo
            editor.on('paste undo redo', function () {
                if (!isTextContentManuallyEdited) {
                    setTimeout(() => {
                        const htmlContent = editor.getContent();
                        const textContent = stripHtml(htmlContent);
                        document.getElementById('template_text_content').value = textContent;
                    }, 100);
                }
            });
        }
    });
}

// Show variables dialog in TinyMCE
function showVariablesDialog(editor) {
    const currentVariables = getCurrentVariables();
    
    if (currentVariables.length === 0) {
        editor.notificationManager.open({
            text: 'Brak zmiennych w szablonie. Dodaj zmienne w sekcji poniżej.',
            type: 'warning'
        });
        return;
    }
    
    const variablesList = currentVariables.map(variable => 
        `<div class="variable-item" style="padding: 8px; border-bottom: 1px solid #eee; cursor: pointer;" onclick="insertVariableIntoEditor('${variable}')">
            <code>{{${variable}}}</code>
        </div>`
    ).join('');
    
    editor.windowManager.open({
        title: 'Wstaw zmienną',
        body: {
            type: 'panel',
            items: [
                {
                    type: 'htmlpanel',
                    html: `<div style="max-height: 300px; overflow-y: auto;">${variablesList}</div>`
                }
            ]
        },
        buttons: [
            {
                type: 'cancel',
                text: 'Anuluj'
            }
        ]
    });
}

// Insert variable into TinyMCE editor
function insertVariableIntoEditor(variable) {
    if (tinymceInstance) {
        tinymceInstance.insertContent(`{{${variable}}}`);
        tinymceInstance.windowManager.close();
    }
}

// Strip HTML tags to create plain text
function stripHtml(html) {
    // First, preserve template variables by replacing them with placeholders
    const variablePlaceholders = {};
    let processedHtml = html;
    let placeholderIndex = 0;
    
    // Find and replace template variables with placeholders
    processedHtml = processedHtml.replace(/\{\{([^}]+)\}\}/g, (match, variable) => {
        const placeholder = `__TEMPLATE_VAR_${placeholderIndex++}__`;
        variablePlaceholders[placeholder] = match;
        return placeholder;
    });
    
    // Now strip HTML tags
    const tmp = document.createElement('div');
    tmp.innerHTML = processedHtml;
    let text = tmp.textContent || tmp.innerText || '';
    
    // Clean up extra whitespace but preserve line breaks
    text = text.replace(/[ \t]+/g, ' '); // Replace multiple spaces/tabs with single space
    text = text.replace(/\n\s+/g, '\n'); // Remove leading spaces from lines
    text = text.replace(/\s+\n/g, '\n'); // Remove trailing spaces from lines
    text = text.trim();
    
    // Restore template variables
    Object.keys(variablePlaceholders).forEach(placeholder => {
        text = text.replace(placeholder, variablePlaceholders[placeholder]);
    });
    
    return text;
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
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">Brak szablonów</td></tr>';
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
            '<button class="btn btn-sm admin-btn-danger-outline" onclick="deleteTemplate(' + template.id + ')" title="Usuń szablon"><i class="fas fa-trash"></i></button>';
        
        row.innerHTML = `
            <td>${checkboxHtml}</td>
            <td><span class="badge admin-badge admin-badge-primary">${template.id}</span></td>
            <td>${template.name} ${template.is_default ? '<span class="admin-badge admin-badge-info ms-1">Domyślny</span>' : ''}</td>
            <td>${template.subject}</td>
            <td>${template.template_type}</td>
            <td><span class="admin-badge admin-badge-${template.is_active ? 'success' : 'secondary'}">${template.is_active ? 'Aktywny' : 'Nieaktywny'}</span></td>
            <td>${new Date(template.created_at + 'Z').toLocaleDateString('pl-PL', {hour12: false, timeZone: 'Europe/Warsaw'})}</td>
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
    
    // Initialize bulk delete after loading templates
    initializeBulkDelete();
}

// Initialize bulk delete functionality
function initializeBulkDelete() {
    const table = document.getElementById('templatesTable');
    const deleteEndpoint = table.dataset.deleteEndpoint;
    
    if (table && deleteEndpoint) {
        // Remove existing bulk delete instance if any
        if (window.templatesBulkDelete) {
            window.templatesBulkDelete = null;
        }
        
        // Create new bulk delete instance
        window.templatesBulkDelete = new BulkDelete('templatesTable', deleteEndpoint);
    }
}

// Show template modal
function showTemplateModal() {
    document.getElementById('templateForm').reset();
    document.getElementById('template_id').value = '';
    loadVariablesDisplay('[]'); // Load empty variables
    isTextContentManuallyEdited = false;
    
    // Hide reset sync button
    const resetSyncButton = document.querySelector('button[onclick*="isTextContentManuallyEdited = false"]');
    if (resetSyncButton) {
        resetSyncButton.style.display = 'none';
    }
    
    const modal = new bootstrap.Modal(document.getElementById('templateModal'));
    modal.show();
    
    // Initialize TinyMCE after modal is shown
    setTimeout(() => {
        initializeTinyMCE();
    }, 300);
}

// Load variables display
function loadVariablesDisplay(variablesJson) {
    const container = document.getElementById('variablesContainer');
    container.innerHTML = '';
    
    try {
        const variables = JSON.parse(variablesJson || '{}');
        const existingVariables = Object.keys(variables);
        
        // Show current variables first
        if (existingVariables.length > 0) {
            const currentSection = document.createElement('div');
            currentSection.innerHTML = '<h6 class="text-primary">Zmienne w szablonie:</h6>';
            
            existingVariables.forEach(variable => {
                const variableElement = document.createElement('div');
                variableElement.className = 'd-flex justify-content-between align-items-center p-2 border-bottom';
                variableElement.innerHTML = `
                    <div>
                        <code class="text-primary cursor-pointer" onclick="insertVariable('{{${variable}}}')">{{${variable}}}</code>
                        <small class="text-muted ms-2">${variables[variable]}</small>
                    </div>
                    <button class="btn btn-sm btn-outline-danger" onclick="removeVariable('${variable}')" title="Usuń zmienną">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                currentSection.appendChild(variableElement);
            });
            
            container.appendChild(currentSection);
        }
        
        // Show available variables to add
        loadDefaultVariables();
        
    } catch (e) {
        container.innerHTML = '<div class="text-danger">Błąd parsowania zmiennych</div>';
    }
}

// Load default variables
function loadDefaultVariables() {
    const container = document.getElementById('variablesContainer');
    const defaultVariables = {
        'user_name': 'Imię użytkownika',
        'user_email': 'Email użytkownika',
        'temporary_password': 'Hasło tymczasowe',
        'login_url': 'Link do logowania',
        'unsubscribe_url': 'Link do wypisania się',
        'delete_account_url': 'Link do usunięcia konta',
        'post_title': 'Tytuł artykułu',
        'post_url': 'Link do artykułu',
        'comment_author': 'Autor komentarza',
        'comment_email': 'Email autora komentarza',
        'comment_content': 'Treść komentarza',
        'comment_date': 'Data komentarza',
        'comment_ip': 'Adres IP autora',
        'comment_browser': 'Przeglądarka autora',
        'moderation_url': 'Link do panelu moderacji',
        'event_title': 'Tytuł wydarzenia',
        'event_date': 'Data wydarzenia',
        'event_time': 'Godzina wydarzenia',
        'event_location': 'Lokalizacja wydarzenia',
        'club_name': 'Nazwa klubu',
        'base_url': 'URL strony głównej'
    };
    
    const existingVariables = getCurrentVariables();
    const availableVariables = Object.entries(defaultVariables).filter(([variable, description]) => {
        return !existingVariables.includes(variable);
    });
    
    if (availableVariables.length > 0) {
        const defaultSection = document.createElement('div');
        defaultSection.className = 'mt-3';
        defaultSection.innerHTML = '<h6 class="text-success">Dostępne zmienne do dodania:</h6>';
        
        availableVariables.forEach(([variable, description]) => {
            const variableElement = document.createElement('div');
            variableElement.className = 'd-flex justify-content-between align-items-center p-2 border-bottom';
            variableElement.innerHTML = `
                <div>
                    <code class="text-success cursor-pointer" onclick="addVariable('${variable}', '${description}')">{{${variable}}}</code>
                    <small class="text-muted ms-2">${description}</small>
                </div>
                <button class="btn btn-sm btn-outline-success" onclick="addVariable('${variable}', '${description}')" title="Dodaj zmienną">
                    <i class="fas fa-plus"></i>
                </button>
            `;
            defaultSection.appendChild(variableElement);
        });
        
        container.appendChild(defaultSection);
    } else {
        const noMoreSection = document.createElement('div');
        noMoreSection.className = 'mt-3 text-muted';
        noMoreSection.innerHTML = '<small>Wszystkie dostępne zmienne zostały już dodane do szablonu.</small>';
        container.appendChild(noMoreSection);
    }
}

// Get current variables
function getCurrentVariables() {
    try {
        const variablesJson = document.getElementById('template_variables').value;
        const variables = JSON.parse(variablesJson || '{}');
        return Object.keys(variables);
    } catch (e) {
        console.error('Error parsing variables:', e);
        return [];
    }
}

// Add variable
function addVariable(variable, description) {
    try {
        const variablesJson = document.getElementById('template_variables').value;
        const variables = JSON.parse(variablesJson || '{}');
        variables[variable] = description;
        document.getElementById('template_variables').value = JSON.stringify(variables);
        loadVariablesDisplay(JSON.stringify(variables));
        
        // Show notification in TinyMCE if available
        if (tinymceInstance) {
            tinymceInstance.notificationManager.open({
                text: `Zmienna {{${variable}}} została dodana do szablonu`,
                type: 'success',
                timeout: 2000
            });
        }
    } catch (e) {
        console.error('Error adding variable:', e);
    }
}

// Remove variable
function removeVariable(variable) {
    try {
        const variablesJson = document.getElementById('template_variables').value;
        const variables = JSON.parse(variablesJson || '{}');
        delete variables[variable];
        document.getElementById('template_variables').value = JSON.stringify(variables);
        loadVariablesDisplay(JSON.stringify(variables));
        
        // Show notification in TinyMCE if available
        if (tinymceInstance) {
            tinymceInstance.notificationManager.open({
                text: `Zmienna {{${variable}}} została usunięta z szablonu`,
                type: 'info',
                timeout: 2000
            });
        }
    } catch (e) {
        console.error('Error removing variable:', e);
    }
}

// Insert variable into HTML content
function insertVariable(variable) {
    if (tinymceInstance) {
        // Insert into TinyMCE editor
        tinymceInstance.insertContent(variable);
    } else {
        // Fallback to textarea
        const textarea = document.getElementById('template_html_content');
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const text = textarea.value;
        const before = text.substring(0, start);
        const after = text.substring(end, text.length);
        
        textarea.value = before + variable + after;
        textarea.focus();
        textarea.setSelectionRange(start + variable.length, start + variable.length);
    }
}

// Save template
function saveTemplate() {
    const form = document.getElementById('templateForm');
    const formData = new FormData(form);
    
    // Get HTML content from TinyMCE if available
    let htmlContent = formData.get('template_html_content');
    if (tinymceInstance) {
        htmlContent = tinymceInstance.getContent();
    }
    
    const data = {
        name: formData.get('template_name'),
        subject: formData.get('template_subject'),
        template_type: formData.get('template_type'),
        html_content: htmlContent,
        text_content: formData.get('template_text_content'),
        variables: formData.get('template_variables'),
        is_active: formData.get('template_is_active') === 'on',
        is_default: formData.get('template_is_default') === 'on'
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
                document.getElementById('template_is_default').checked = template.is_default || false;
                
                // Load variables display
                loadVariablesDisplay(template.variables);
                isTextContentManuallyEdited = false;
                
                // Hide reset sync button
                const resetSyncButton = document.querySelector('button[onclick*="isTextContentManuallyEdited = false"]');
                if (resetSyncButton) {
                    resetSyncButton.style.display = 'none';
                }
                
                const modal = new bootstrap.Modal(document.getElementById('templateModal'));
                modal.show();
                
                // Initialize TinyMCE after modal is shown and set content
                setTimeout(() => {
                    initializeTinyMCE();
                    // Set content in TinyMCE after initialization
                    setTimeout(() => {
                        if (tinymceInstance) {
                            tinymceInstance.setContent(template.html_content || '');
                        }
                    }, 100);
                }, 300);
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
    // Check if parent node exists before replacing
    if (confirmBtn.parentNode) {
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    } else {
        console.warn('Confirm button parent node not found');
    }
    
    newConfirmBtn.onclick = function() {
        // Hide modal using Bootstrap method
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
        }
        
        // Then perform delete
        performDeleteTemplate(templateId);
    };
    
    // Cancel button will use standard Bootstrap behavior with data-bs-dismiss="modal"
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
    // Check if parent node exists before replacing
    if (confirmBtn.parentNode) {
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    } else {
        console.warn('Confirm button parent node not found');
    }
    
    newConfirmBtn.onclick = function() {
        // Hide modal using Bootstrap method
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
        }
        
        // Then perform reset
        performResetTemplates();
    };
    
    // Cancel button will use standard Bootstrap behavior with data-bs-dismiss="modal"
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