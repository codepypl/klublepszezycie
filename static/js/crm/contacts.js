// CRM Contacts Management JavaScript

document.addEventListener('DOMContentLoaded', function() {
    loadContacts();
    loadImportHistory();
    
    // Setup import form submission
    const importForm = document.getElementById('importForm');
    if (importForm) {
        importForm.addEventListener('submit', handleImportSubmission);
    }
    
    // Setup auto-refresh for contacts
    setupContactsAutoRefresh();
});

function loadContacts() {
    fetch('/api/crm/contacts', {
        credentials: 'include'
    })
        .then(response => safeJsonParse(response))
        .then(data => {
            if (data.success) {
                updateContactsTable(data.contacts);
            }
        })
        .catch(error => {
            console.error('Error loading contacts:', error);
        });
}

function loadImportHistory() {
    fetch('/api/crm/imports', {
        credentials: 'include'
    })
        .then(response => safeJsonParse(response))
        .then(data => {
            if (data.success) {
                updateImportHistory(data.imports);
            }
        })
        .catch(error => {
            console.error('Error loading import history:', error);
        });
}

function updateContactsTable(contacts) {
    const tbody = document.querySelector('#contactsTable tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (contacts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Brak kontaktów</td></tr>';
        return;
    }
    
    contacts.forEach(contact => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${contact.name}</td>
            <td>${contact.phone || 'Brak'}</td>
            <td>${contact.email || 'Brak'}</td>
            <td>${contact.company || 'Brak'}</td>
            <td>
                <span class="badge ${getStatusBadgeClass(contact.status)}">${getStatusText(contact.status)}</span>
            </td>
            <td>${contact.call_attempts}/${contact.max_call_attempts}</td>
            <td>${formatDate(contact.created_at)}</td>
        `;
        tbody.appendChild(row);
    });
}

function updateImportHistory(imports) {
    const tbody = document.querySelector('#importHistoryTable tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (imports.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Brak historii importów</td></tr>';
        return;
    }
    
    imports.forEach(importLog => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${importLog.filename}</td>
            <td>${importLog.total_records}</td>
            <td>${importLog.successful_records}</td>
            <td>${importLog.failed_records}</td>
            <td>${formatDate(importLog.created_at)}</td>
        `;
        tbody.appendChild(row);
    });
}

function handleImportSubmission(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('importFile');
    const file = fileInput.files[0];
    
    if (!file) {
        if (window.toastManager) {
            window.toastManager.error('Proszę wybrać plik');
        } else {
            showWarning('Proszę wybrać plik');
        }
        return;
    }
    
    // Validate file type
    const allowedTypes = ['.xlsx', '.xls'];
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    
    if (!allowedTypes.includes(fileExtension)) {
        if (window.toastManager) {
            window.toastManager.error('Proszę wybrać plik XLSX lub XLS');
        } else {
            showWarning('Proszę wybrać plik XLSX lub XLS');
        }
        return;
    }
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Importowanie...';
    submitBtn.disabled = true;
    
    // Create form data
    const formData = new FormData();
    formData.append('file', file);
    
    fetch('/api/crm/contacts/import', {
        method: 'POST',
        body: formData,
        credentials: 'include'
    })
    .then(response => safeJsonParse(response))
    .then(data => {
        if (data.success) {
            if (window.toastManager) {
                window.toastManager.success(`Pomyślnie zaimportowano ${data.imported_count} kontaktów`);
            } else {
                showSuccess(`Pomyślnie zaimportowano ${data.imported_count} kontaktów`);
            }
            // Refresh contacts and import history
            refreshContactsData();
            // Reset form
            e.target.reset();
        } else {
            if (window.toastManager) {
                window.toastManager.error('Błąd: ' + data.error);
            } else {
                showError('Błąd: ' + data.error);
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if (window.toastManager) {
            window.toastManager.error('Wystąpił błąd podczas importu');
        } else {
            showError('Wystąpił błąd podczas importu');
        }
    })
    .finally(() => {
        // Reset button
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

function getStatusBadgeClass(status) {
    switch(status) {
        case 'ready': return 'bg-success';
        case 'blacklisted': return 'bg-danger';
        case 'limit_reached': return 'bg-warning';
        default: return 'bg-secondary';
    }
}

function getStatusText(status) {
    switch(status) {
        case 'ready': return 'Gotowy';
        case 'blacklisted': return 'Czarna lista';
        case 'limit_reached': return 'Limit osiągnięty';
        default: return 'Nieznany';
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('pl-PL');
}

// Auto-refresh functionality for contacts
let contactsRefreshInterval;

function setupContactsAutoRefresh() {
    // Refresh every 60 seconds (less frequent than calls page)
    contactsRefreshInterval = setInterval(() => {
        refreshContactsData();
    }, 60000); // 60 seconds
    
    // Add manual refresh button
    addContactsRefreshButton();
}

function refreshContactsData() {
    // Show subtle loading indicator
    showContactsRefreshIndicator();
    
    // Load both contacts and import history
    Promise.all([
        fetch('/api/crm/contacts', { credentials: 'include' }).then(response => safeJsonParse(response)),
        fetch('/api/crm/imports', { credentials: 'include' }).then(response => safeJsonParse(response))
    ])
    .then(([contactsData, importsData]) => {
        if (contactsData.success) {
            updateContactsTable(contactsData.contacts);
        }
        if (importsData.success) {
            updateImportHistory(importsData.imports);
        }
        hideContactsRefreshIndicator();
    })
    .catch(error => {
        console.error('Error refreshing contacts data:', error);
        hideContactsRefreshIndicator();
    });
}

function addContactsRefreshButton() {
    // Add refresh button to the contacts section
    const contactsCard = document.querySelector('.card.admin-card');
    if (contactsCard) {
        const cardHeader = contactsCard.querySelector('.card-header');
        if (cardHeader) {
            const refreshButton = document.createElement('button');
            refreshButton.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Odśwież';
            refreshButton.className = 'btn btn-sm admin-btn-outline';
            refreshButton.style.float = 'right';
            refreshButton.onclick = function() {
                refreshContactsData();
            };
            
            // Add button to header if it doesn't exist
            const existingButton = cardHeader.querySelector('.contacts-refresh-button');
            if (!existingButton) {
                refreshButton.classList.add('contacts-refresh-button');
                cardHeader.appendChild(refreshButton);
            }
        }
    }
}

function showContactsRefreshIndicator() {
    // Show a subtle indicator in the contacts table
    const contactsTable = document.querySelector('#contactsTable');
    if (contactsTable) {
        const indicator = document.createElement('div');
        indicator.id = 'contactsRefreshIndicator';
        indicator.innerHTML = '<i class="fas fa-sync-alt fa-spin me-2"></i>Odświeżanie...';
        indicator.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0, 123, 255, 0.1);
            color: #007bff;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            z-index: 100;
        `;
        contactsTable.style.position = 'relative';
        contactsTable.appendChild(indicator);
    }
}

function hideContactsRefreshIndicator() {
    const indicator = document.getElementById('contactsRefreshIndicator');
    if (indicator) {
        indicator.remove();
    }
}
