// Admin Email Templates JavaScript for Lepsze Życie Club

// Global variables
let currentPage = 1;
let currentPerPage = 10;
let currentTemplateId = null;
let isTextContentManuallyEdited = false;

// Make isTextContentManuallyEdited globally available
window.isTextContentManuallyEdited = isTextContentManuallyEdited;

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
        }, 500);
    }
});

// Initialize modal listeners
function initializeModalListeners() {
    // Clean up when modal is hidden
    const templateModal = document.getElementById('templateModal');
    if (templateModal) {
        templateModal.addEventListener('hidden.bs.modal', function () {
            isTextContentManuallyEdited = false;
            window.isTextContentManuallyEdited = false; // Update global variable
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
                    window.isTextContentManuallyEdited = true; // Update global variable
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
            if (isTextContentManuallyEdited && window.quillInstances && window.quillInstances['template_html_content'] && !hintShown) {
                window.toastManager.info('Synchronizacja z HTML została wyłączona. Kliknij "Przywróć synchronizację" aby włączyć automatyczne uzupełnianie.');
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
            window.isTextContentManuallyEdited = false; // Update global variable
            hintShown = false;
            this.style.display = 'none';
            
            // Sync current HTML content to text
            if (window.quillInstances && window.quillInstances['template_html_content']) {
                try {
                    // Check if quill instance is fully initialized
                    if (window.quillInstances['template_html_content'].root && typeof window.quillInstances['template_html_content'].root.innerHTML !== 'undefined') {
                const htmlContent = window.quillInstances['template_html_content'].root.innerHTML;
                const textContent = stripHtml(htmlContent);
                textContentField.value = textContent;
                
                window.toastManager.success('Synchronizacja została przywrócona.');
                    } else {
                        console.warn('Quill instance not fully initialized for sync');
                        window.toastManager.warning('Edytor nie jest jeszcze gotowy. Spróbuj ponownie za chwilę.');
                    }
                } catch (error) {
                    console.error('Error syncing content:', error);
                    window.toastManager.error('Błąd synchronizacji treści.');
                }
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

// Wait for Quill.js to be initialized and set content
function waitForQuillAndSetContent(editorId, content, maxRetries = 50) {
    if (window.quillInstances && window.quillInstances[editorId]) {
        // Quill is ready, set content
        console.log('🔍 Setting content for:', editorId, 'Content:', content);
        
        // Clean up content - remove empty paragraphs and normalize whitespace
        let cleanContent = content || '';
        if (cleanContent) {
            // Remove empty paragraphs and divs
            cleanContent = cleanContent.replace(/<p><\/p>/g, '');
            cleanContent = cleanContent.replace(/<div><\/div>/g, '');
            cleanContent = cleanContent.replace(/<p>\s*<\/p>/g, '');
            cleanContent = cleanContent.replace(/<div>\s*<\/div>/g, '');
            
            // If content is empty after cleanup, set a default
            if (cleanContent.trim() === '' || cleanContent.trim() === '<p></p>' || cleanContent.trim() === '<div></div>') {
                cleanContent = '<p>Wpisz treść szablonu...</p>';
            }
        } else {
            cleanContent = '<p>Wpisz treść szablonu...</p>';
        }
        
        console.log('🔍 Cleaned content:', cleanContent);
        
        try {
            // Check if quill instance is fully initialized
            if (window.quillInstances[editorId] && typeof window.quillInstances[editorId].setContents === 'function') {
                // Use Quill's API instead of innerHTML for better HTML handling
                const quill = window.quillInstances[editorId];
                
                // Try to parse content as Delta first, fallback to HTML
                try {
                    // If content looks like HTML, convert it properly
                    if (cleanContent.includes('<') && cleanContent.includes('>')) {
                        // Use clipboard module to handle HTML properly
                        const delta = quill.clipboard.convert(cleanContent);
                        quill.setContents(delta, 'silent');
                    } else {
                        // Plain text
                        quill.setText(cleanContent);
                    }
                } catch (parseError) {
                    console.warn('Error parsing content, using innerHTML fallback:', parseError);
                    quill.root.innerHTML = cleanContent;
                }
                
                console.log('✅ Quill content set for:', editorId);
            } else {
                console.warn('Quill instance not fully initialized, falling back to textarea');
                // Fallback to textarea
                const textarea = document.getElementById(editorId);
                if (textarea) {
                    textarea.value = content || '';
                }
            }
    } catch (error) {
            console.error('Error setting Quill content:', error);
            // Fallback to textarea
            const textarea = document.getElementById(editorId);
            if (textarea) {
                textarea.value = content || '';
            }
        }
        return;
    }
    
    if (maxRetries > 0) {
        // Quill not ready yet, retry after 100ms
        setTimeout(() => {
            waitForQuillAndSetContent(editorId, content, maxRetries - 1);
        }, 100);
    } else {
        console.warn('❌ Quill editor not available for:', editorId);
        // Fallback to textarea
        const textarea = document.getElementById(editorId);
        if (textarea) {
            textarea.value = content || '';
        }
    }
}


// Get content from Quill editor
function getQuillContent(editorId) {
    if (window.quillInstances && window.quillInstances[editorId]) {
        try {
            // Check if quill instance is fully initialized
            if (window.quillInstances[editorId].root && typeof window.quillInstances[editorId].root.innerHTML !== 'undefined') {
        return window.quillInstances[editorId].root.innerHTML;
            } else {
                console.warn('Quill instance not fully initialized, falling back to textarea');
                // Fallback to textarea
                const textarea = document.getElementById(editorId);
                return textarea ? textarea.value : '';
            }
        } catch (error) {
            console.error('Error getting Quill content:', error);
            // Fallback to textarea
            const textarea = document.getElementById(editorId);
            return textarea ? textarea.value : '';
        }
    } else {
        // Fallback to textarea
        const textarea = document.getElementById(editorId);
        return textarea ? textarea.value : '';
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
    
    // Convert HTML to plain text while preserving line breaks and paragraphs
    processedHtml = processedHtml
        // Convert block elements to line breaks
        .replace(/<\/?(div|p|h[1-6]|li|br)[^>]*>/gi, '\n')
        // Convert list items to dashes
        .replace(/<\/?(ul|ol)[^>]*>/gi, '\n')
        // Convert closing tags of other block elements
        .replace(/<\/(article|section|header|footer|nav|aside|main)[^>]*>/gi, '\n')
        // Convert table elements
        .replace(/<\/?(table|tr)[^>]*>/gi, '\n')
        .replace(/<\/?(td|th)[^>]*>/gi, ' | ')
        // Remove remaining HTML tags
        .replace(/<[^>]*>/g, '')
        // Decode HTML entities
        .replace(/&nbsp;/g, ' ')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&amp;/g, '&')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'");
    
    // Clean up whitespace while preserving structure
    let text = processedHtml
        // Replace multiple spaces with single space
        .replace(/[ \t]+/g, ' ')
        // Replace multiple line breaks with double line break (paragraph)
        .replace(/\n\s*\n\s*\n+/g, '\n\n')
        // Remove leading/trailing whitespace from each line
        .split('\n')
        .map(line => line.trim())
        .join('\n')
        // Final trim
        .trim();
    
    // Restore template variables
    Object.keys(variablePlaceholders).forEach(placeholder => {
        text = text.replace(placeholder, variablePlaceholders[placeholder]);
    });
    
    return text;
}

// Load templates
function loadTemplates() {
    console.log('🔍 loadTemplates called with:', { currentPage, currentPerPage });
    
    const params = new URLSearchParams({
        page: currentPage,
        per_page: currentPerPage
    });
    
    console.log('🔍 API params:', params.toString());
    
    fetch(`/api/email/templates?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayTemplates(data.templates);
                if (data.pagination) {
                    updatePagination(data.pagination);
                }
            } else {
                window.toastManager.error('Błąd ładowania szablonów: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error loading templates:', error);
            window.toastManager.error('Błąd ładowania szablonów');
        });
}

// Update pagination
function updatePagination(paginationData) {
    console.log('🔍 updatePagination called with:', paginationData);
    
    const paginationContainer = document.getElementById('pagination');
    if (paginationContainer) {
        if (paginationContainer.paginationInstance) {
            // Update existing pagination
            paginationContainer.paginationInstance.setData(paginationData);
            // Sync global variables with pagination data
            console.log('🔍 Syncing variables from pagination data:', { 
                old: { currentPage, currentPerPage }, 
                new: { page: paginationData.page, per_page: paginationData.per_page } 
            });
            currentPage = paginationData.page || 1;
            currentPerPage = paginationData.per_page || 10;
            console.log('🔍 Variables after sync:', { currentPage, currentPerPage });
        } else {
            // Check if Pagination class is available
            if (typeof Pagination === 'undefined') {
                console.error('Pagination class not available. Make sure paginate.js is loaded.');
                return;
            }
            
            // Initialize pagination for the first time
            paginationContainer.paginationInstance = new Pagination({
                containerId: 'pagination',
                showInfo: true,
                showPerPage: true,
                perPageOptions: [5, 10, 25, 50, 100],
                defaultPerPage: 10,
                maxVisiblePages: 5,
                onPageChange: (page) => {
                    currentPage = page;
                    loadTemplates();
                },
                onPerPageChange: (newPage, perPage) => {
                    console.log('🔍 onPerPageChange called with:', { newPage, perPage });
                    currentPage = newPage;
                    currentPerPage = perPage;
                    console.log('🔍 Updated variables:', { currentPage, currentPerPage });
                    loadTemplates();
                }
            });
            paginationContainer.paginationInstance.setData(paginationData);
        }
    }
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
    window.isTextContentManuallyEdited = false; // Update global variable
    
    // Hide reset sync button
    const resetSyncButton = document.querySelector('button[onclick*="isTextContentManuallyEdited = false"]');
    if (resetSyncButton) {
        resetSyncButton.style.display = 'none';
    }
    
    const modal = new bootstrap.Modal(document.getElementById('templateModal'));
    modal.show();
    
    // Clear Quill editor after modal is shown
    setTimeout(() => {
        waitForQuillAndSetContent('template_html_content', '');
    }, 500);
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
        'change_date': 'Data zmiany hasła',
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
        
        // Show notification
        window.toastManager.success(`Zmienna {{${variable}}} została dodana do szablonu`);
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
        
        // Show notification
        window.toastManager.info(`Zmienna {{${variable}}} została usunięta z szablonu`);
    } catch (e) {
        console.error('Error removing variable:', e);
    }
}

// Insert variable into HTML content
function insertVariable(variable) {
    if (window.quillInstances && window.quillInstances['template_html_content']) {
        // Insert into Quill editor
        const quill = window.quillInstances['template_html_content'];
        
        try {
            // Check if quill instance is fully initialized
            if (typeof quill.getSelection === 'function' && typeof quill.insertText === 'function') {
        const range = quill.getSelection();
        if (range) {
            quill.insertText(range.index, variable);
            quill.setSelection(range.index + variable.length);
        } else {
            quill.insertText(quill.getLength(), variable);
                }
            } else {
                console.warn('Quill instance not fully initialized, falling back to textarea');
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
        } catch (error) {
            console.error('Error inserting variable into Quill:', error);
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
    
    // Get HTML content from Quill if available
    let htmlContent = getQuillContent('template_html_content');
    
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
            window.toastManager.success('Szablon zapisany pomyślnie!');
            bootstrap.Modal.getInstance(document.getElementById('templateModal')).hide();
            loadTemplates();
        } else {
            window.toastManager.error('Błąd zapisywania szablonu: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error saving template:', error);
        window.toastManager.error('Błąd zapisywania szablonu');
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
                // Set content in textarea first
                const htmlTextarea = document.getElementById('template_html_content');
                htmlTextarea.value = template.html_content || '';
                
                document.getElementById('template_text_content').value = template.text_content || '';
                document.getElementById('template_variables').value = template.variables || '';
                document.getElementById('template_is_active').checked = template.is_active;
                document.getElementById('template_is_default').checked = template.is_default || false;
                
                // Load variables display
                loadVariablesDisplay(template.variables);
                isTextContentManuallyEdited = false;
                window.isTextContentManuallyEdited = false; // Update global variable
                
                // Hide reset sync button
                const resetSyncButton = document.querySelector('button[onclick*="isTextContentManuallyEdited = false"]');
                if (resetSyncButton) {
                    resetSyncButton.style.display = 'none';
                }
                
                const modal = new bootstrap.Modal(document.getElementById('templateModal'));
                modal.show();
                
                // Wait for Quill to be initialized and set content
                setTimeout(() => {
                    waitForQuillAndSetContent('template_html_content', template.html_content || '');
                }, 500);
            } else {
                window.toastManager.error('Błąd ładowania szablonu: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error loading template:', error);
            window.toastManager.error('Błąd ładowania szablonu');
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
            window.toastManager.success('Szablon usunięty!');
            loadTemplates();
        } else {
            window.toastManager.error('Błąd usuwania: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error deleting template:', error);
        window.toastManager.error('Błąd usuwania');
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
            window.toastManager.success('Szablony zostały zresetowane do stanu domyślnego!');
            loadTemplates();
        } else {
            window.toastManager.error('Błąd resetowania: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error resetting templates:', error);
        window.toastManager.error('Błąd resetowania szablonów');
    });
}

// Make functions globally available
window.resetTemplates = resetTemplates;
window.deleteTemplate = deleteTemplate;
window.saveTemplate = saveTemplate;
window.showTemplateModal = showTemplateModal;
window.editTemplate = editTemplate;
window.insertVariable = insertVariable;
window.addVariable = addVariable;
window.removeVariable = removeVariable;