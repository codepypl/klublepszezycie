// Admin Email Campaigns JavaScript for Lepsze Życie Club

// Global variables
let currentPage = 1;
let currentPerPage = 10;
let availableTemplates = [];
let availableGroups = [];

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadCampaigns();
    loadTemplates();
    loadGroups();
    
    // Set up pagination handlers for auto-initialization
    window.paginationHandlers = {
        onPageChange: (page) => {
            currentPage = page;
            loadCampaigns();
        },
        onPerPageChange: (newPage, perPage) => {
            currentPerPage = perPage;
            currentPage = newPage; // Use the page passed by pagination
            loadCampaigns();
        }
    };
    
    // Add event listener for campaign modal close to refresh campaigns list
    const campaignModal = document.getElementById('campaignModal');
    if (campaignModal) {
        campaignModal.addEventListener('hidden.bs.modal', function() {
            loadCampaigns(); // Odśwież listę kampanii po zamknięciu modala
        });
    }
});


// Load campaigns
function loadCampaigns() {
    const params = new URLSearchParams({
        page: currentPage,
        per_page: currentPerPage
    });
    
    fetch(`/api/email/campaigns?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayCampaigns(data.campaigns);
                if (data.pagination) {
                    // Update pagination if it exists
                    const paginationElement = document.getElementById('pagination');
                    if (paginationElement && paginationElement.paginationInstance) {
                        paginationElement.paginationInstance.setData(data.pagination);
                    }
                }
            } else {
                toastManager.error('Błąd ładowania kampanii: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error loading campaigns:', error);
            toastManager.error('Błąd ładowania kampanii');
        });
}

// Display campaigns
function displayCampaigns(campaigns) {
    const tbody = document.getElementById('campaignsTableBody');
    tbody.innerHTML = '';
    
    if (campaigns.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Brak kampanii</td></tr>';
        return;
    }
    
    campaigns.forEach(campaign => {
        const row = document.createElement('tr');
        
        let statusClass = 'secondary';
        if (campaign.status === 'completed') statusClass = 'success';
        else if (campaign.status === 'sending') statusClass = 'warning';
        else if (campaign.status === 'cancelled') statusClass = 'danger';
        
        row.innerHTML = `
            <td>
                ${campaign.status !== 'sending' && campaign.status !== 'sent' && campaign.status !== 'completed' ? `<input type="checkbox" name="itemIds" value="${campaign.id}">` : ''}
            </td>
            <td>${campaign.name}</td>
            <td>${campaign.subject}</td>
            <td><span class="admin-badge admin-badge-${statusClass}">${campaign.status}</span></td>
            <td>${campaign.total_recipients}</td>
            <td>${campaign.sent_count}</td>
            <td>${new Date(campaign.created_at + 'Z').toLocaleDateString('pl-PL', {hour12: false, timeZone: 'Europe/Warsaw'})}</td>
            <td>
                <div class="btn-group" role="group">
                    <button class="btn btn-sm admin-btn-outline" onclick="editCampaign(${campaign.id})" title="Edytuj kampanię">
                        <i class="fas fa-edit"></i>
                    </button>
                    ${campaign.status === 'draft' ? `<button class="btn btn-sm admin-btn-info" onclick="sendCampaign(${campaign.id})" title="Wyślij kampanię">
                        <i class="fas fa-paper-plane"></i>
                    </button>` : ''}
                    ${campaign.status !== 'sending' && campaign.status !== 'sent' && campaign.status !== 'completed' ? `<button class="btn btn-sm admin-btn-danger" onclick="deleteCampaign(${campaign.id})" title="Usuń kampanię">
                        <i class="fas fa-trash"></i>
                    </button>` : ''}
                </div>
            </td>
        `;
        
        tbody.appendChild(row);
    });
    
    // Initialize bulk delete after loading campaigns
    initializeBulkDelete();
}

// Initialize bulk delete functionality
function initializeBulkDelete() {
    const table = document.getElementById('campaignsTable');
    const deleteEndpoint = table.dataset.deleteEndpoint;
    
    if (table && deleteEndpoint) {
        // Remove existing bulk delete instance if any
        if (window.campaignsBulkDelete) {
            window.campaignsBulkDelete = null;
        }
        
        // Create new bulk delete instance
        window.campaignsBulkDelete = new BulkDelete('campaignsTable', deleteEndpoint);
    }
}

// Show campaign modal
function showCampaignModal() {
    document.getElementById('campaignForm').reset();
    document.getElementById('campaign_id').value = '';
    loadGroupsForCampaign();
    const modal = new bootstrap.Modal(document.getElementById('campaignModal'));
    modal.show();
}

// Load groups for campaign
function loadGroupsForCampaign() {
    return fetch('/api/email/groups')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const select = document.getElementById('campaign_groups');
                select.innerHTML = '';
                
                data.groups.forEach(group => {
                    const option = document.createElement('option');
                    option.value = group.id;
                    option.textContent = `${group.name} (${group.member_count} członków)`;
                    select.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading groups for campaign:', error);
        });
}

// Save campaign
function saveCampaign() {
    const form = document.getElementById('campaignForm');
    const formData = new FormData(form);
    
    const selectedGroups = Array.from(document.getElementById('campaign_groups').selectedOptions)
        .map(option => parseInt(option.value));
    
    // Collect content variables
    const contentVariables = {};
    const templateId = formData.get('campaign_template');
    if (templateId) {
        const template = availableTemplates.find(t => t.id == templateId);
        if (template && template.variables) {
            // Parse variables if it's a string
            let variables = template.variables;
            if (typeof variables === 'string') {
                try {
                    variables = JSON.parse(variables);
                } catch (e) {
                    console.error('Error parsing template variables:', e);
                    variables = {};
                }
            }
            
            if (variables && Object.keys(variables).length > 0) {
                Object.keys(variables).forEach(variable => {
                    const input = document.getElementById(`var_${variable}`);
                    if (input) {
                        contentVariables[variable] = input.value;
                    }
                });
            }
        }
    }
    
    const data = {
        name: formData.get('campaign_name'),
        subject: formData.get('campaign_subject'),
        template_id: templateId ? parseInt(templateId) : null,
        content_variables: contentVariables,
        recipient_groups: selectedGroups
    };
    
    const campaignId = document.getElementById('campaign_id').value;
    const method = campaignId ? 'PUT' : 'POST';
    const url = campaignId ? `/api/email/campaigns/${campaignId}` : '/api/email/campaigns';
    
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
            toastManager.success('Kampania zapisana pomyślnie!');
            bootstrap.Modal.getInstance(document.getElementById('campaignModal')).hide();
            loadCampaigns();
            
            // Wywołaj globalne odświeżenie
            if (typeof window.refreshAfterCRUD === 'function') {
                window.refreshAfterCRUD();
            } else {
                console.warn('window.refreshAfterCRUD is not available');
            }
        } else {
            toastManager.error('Błąd zapisywania kampanii: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error saving campaign:', error);
        toastManager.error('Błąd zapisywania kampanii');
    });
}

// Edit campaign
function editCampaign(campaignId) {
    fetch(`/api/email/campaigns/${campaignId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const campaign = data.campaign;
                document.getElementById('campaign_id').value = campaign.id;
                document.getElementById('campaign_name').value = campaign.name;
                document.getElementById('campaign_subject').value = campaign.subject;
                
                // Set template
                if (campaign.template_id) {
                    document.getElementById('campaign_template').value = campaign.template_id;
                    handleTemplateChange();
                    
                    // Set content variables
                    if (campaign.content_variables) {
                        setTimeout(() => {
                            Object.keys(campaign.content_variables).forEach(key => {
                                const input = document.getElementById(`var_${key}`);
                                if (input) {
                                    input.value = campaign.content_variables[key];
                                }
                            });
                        }, 100);
                    }
                }
                
                // Load groups and select current ones
                loadGroupsForCampaign().then(() => {
                    if (campaign.recipient_groups) {
                        campaign.recipient_groups.forEach(groupId => {
                            const option = document.querySelector(`#campaign_groups option[value="${groupId}"]`);
                            if (option) option.selected = true;
                        });
                    }
                });
                
                const modal = new bootstrap.Modal(document.getElementById('campaignModal'));
                modal.show();
            } else {
                toastManager.error('Błąd ładowania kampanii: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error loading campaign:', error);
            toastManager.error('Błąd ładowania kampanii');
        });
}

// Send campaign
function sendCampaign(campaignId) {
    if (confirm('Czy na pewno chcesz wysłać tę kampanię?')) {
        fetch(`/api/email/campaigns/${campaignId}/send`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                toastManager.success('Kampania wysłana!');
                loadCampaigns();
                
                // Wywołaj globalne odświeżenie
                window.refreshAfterCRUD();
            } else {
                toastManager.error('Błąd wysyłania: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error sending campaign:', error);
            toastManager.error('Błąd wysyłania');
        });
    }
}

// Delete campaign
function deleteCampaign(campaignId) {
    window.deleteConfirmation.showSingleDelete(
        'kampanię',
        () => {
            fetch(`/api/email/campaigns/${campaignId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    toastManager.success('Kampania usunięta!');
                    loadCampaigns();
                    
                    // Wywołaj globalne odświeżenie
                    window.refreshAfterCRUD();
                } else {
                    toastManager.error('Błąd usuwania: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error deleting campaign:', error);
                toastManager.error('Błąd usuwania');
            });
        },
        'kampanię'
    );
}

// Load templates
function loadTemplates() {
    fetch('/api/email/campaigns/templates')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                availableTemplates = data.templates;
                populateTemplateSelect();
            } else {
                console.error('Error loading templates:', data.error);
            }
        })
        .catch(error => {
            console.error('Error loading templates:', error);
        });
}

// Load groups
function loadGroups() {
    fetch('/api/email/groups')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                availableGroups = data.groups;
                populateGroupSelect();
            } else {
                console.error('Error loading groups:', data.error);
            }
        })
        .catch(error => {
            console.error('Error loading groups:', error);
        });
}

// Populate template select
function populateTemplateSelect() {
    const select = document.getElementById('campaign_template');
    select.innerHTML = '<option value="">Wybierz szablon</option>';
    
    availableTemplates.forEach(template => {
        const option = document.createElement('option');
        option.value = template.id;
        option.textContent = template.name;
        select.appendChild(option);
    });
}

// Populate group select
function populateGroupSelect() {
    const select = document.getElementById('campaign_groups');
    select.innerHTML = '<option value="">Wybierz grupy</option>';
    
    availableGroups.forEach(group => {
        const option = document.createElement('option');
        option.value = group.id;
        option.textContent = group.name;
        select.appendChild(option);
    });
}

// Handle template change
function handleTemplateChange() {
    const templateId = document.getElementById('campaign_template').value;
    const variablesContainer = document.getElementById('variablesContainer');
    const templateVariables = document.getElementById('templateVariables');
    
    if (templateId) {
        const template = availableTemplates.find(t => t.id == templateId);
        if (template && template.variables) {
            // Parse variables if it's a string
            let variables = template.variables;
            if (typeof variables === 'string') {
                try {
                    variables = JSON.parse(variables);
                } catch (e) {
                    console.error('Error parsing template variables:', e);
                    variables = {};
                }
            }
            
            if (variables && Object.keys(variables).length > 0) {
                variablesContainer.innerHTML = '';
                Object.keys(variables).forEach(variable => {
                    const div = document.createElement('div');
                    div.className = 'mb-2';
                    div.innerHTML = `
                        <label for="var_${variable}" class="form-label">${variable}</label>
                        <input type="text" class="form-control" id="var_${variable}" name="var_${variable}" 
                               placeholder="Wpisz treść dla ${variable}" oninput="debounceUpdatePreview()">
                        <div class="form-text">${variables[variable]}</div>
                    `;
                    variablesContainer.appendChild(div);
                });
                templateVariables.style.display = 'block';
                updateEmailPreview();
            } else {
                templateVariables.style.display = 'none';
                updateEmailPreview();
            }
        } else {
            templateVariables.style.display = 'none';
            updateEmailPreview();
        }
    } else {
        templateVariables.style.display = 'none';
        document.getElementById('emailPreview').innerHTML = '<p class="text-muted">Wybierz szablon aby zobaczyć podgląd</p>';
    }
}

// Sanitize email preview HTML to prevent CSS leakage
function sanitizeEmailPreview(htmlContent) {
    // Create a temporary div to parse the HTML
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlContent;
    
    // Remove style tags and style attributes that could affect the page
    const styleTags = tempDiv.querySelectorAll('style');
    styleTags.forEach(style => style.remove());
    
    // Remove style attributes from all elements
    const allElements = tempDiv.querySelectorAll('*');
    allElements.forEach(element => {
        element.removeAttribute('style');
    });
    
    // Add scoped styles to prevent CSS leakage
    const scopedContent = tempDiv.innerHTML;
    
    return scopedContent;
}

// Debounced update email preview
let previewTimeout;
function debounceUpdatePreview() {
    clearTimeout(previewTimeout);
    previewTimeout = setTimeout(updateEmailPreview, 300);
}

// Update email preview
function updateEmailPreview() {
    const templateId = document.getElementById('campaign_template').value;
    const preview = document.getElementById('emailPreview');
    
    if (templateId) {
        const template = availableTemplates.find(t => t.id == templateId);
        if (template && template.html_content) {
            let htmlContent = template.html_content;
            let subject = template.subject || '';
            
            // Replace variables with form values
            if (template.variables) {
                let variables = template.variables;
                // Parse variables if it's a string
                if (typeof variables === 'string') {
                    try {
                        variables = JSON.parse(variables);
                    } catch (e) {
                        console.error('Error parsing template variables:', e);
                        variables = {};
                    }
                }
                
                // Handle both array and object formats
                if (Array.isArray(variables)) {
                    variables.forEach(variable => {
                        const input = document.getElementById(`var_${variable}`);
                        const value = input ? input.value : `{{${variable}}}`;
                        htmlContent = htmlContent.replace(new RegExp(`{{${variable}}}`, 'g'), value);
                        subject = subject.replace(new RegExp(`{{${variable}}}`, 'g'), value);
                    });
                } else if (typeof variables === 'object' && variables !== null) {
                    Object.keys(variables).forEach(variable => {
                        const input = document.getElementById(`var_${variable}`);
                        const value = input ? input.value : `{{${variable}}}`;
                        htmlContent = htmlContent.replace(new RegExp(`{{${variable}}}`, 'g'), value);
                        subject = subject.replace(new RegExp(`{{${variable}}}`, 'g'), value);
                    });
                }
            }
            
            // Sanitize HTML content to prevent CSS leakage
            const sanitizedContent = sanitizeEmailPreview(htmlContent);
            
            preview.innerHTML = `
                <div class="mb-2">
                    <strong>Temat:</strong> ${subject}
                </div>
                <div class="border-top pt-2" style="max-height: 400px; overflow-y: auto;">
                    <div class="email-preview-container" style="isolation: isolate; contain: layout style;">
                        ${sanitizedContent}
                    </div>
                </div>
            `;
        }
    } else {
        preview.innerHTML = '<p class="text-muted">Wybierz szablon aby zobaczyć podgląd</p>';
    }
}

// Make functions globally available
window.showCampaignModal = showCampaignModal;
window.saveCampaign = saveCampaign;
window.editCampaign = editCampaign;
window.deleteCampaign = deleteCampaign;
window.handleTemplateChange = handleTemplateChange;
window.updateEmailPreview = updateEmailPreview;
