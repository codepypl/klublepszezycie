// CRM Calls Management JavaScript

document.addEventListener('DOMContentLoaded', function() {
    loadQueueStats();
    loadNextContact();
    
    // Setup call form submission
    const callForm = document.getElementById('callForm');
    if (callForm) {
        callForm.addEventListener('submit', handleCallSubmission);
    }
    
    // Setup auto-refresh
    setupAutoRefresh();
});

function loadQueueStats() {
    fetch('/api/crm/queue/stats', {
        credentials: 'include'
    })
        .then(response => safeJsonParse(response))
        .then(data => {
            if (data.success) {
                updateQueueStats(data.stats);
            }
        })
        .catch(error => {
            console.error('Error loading queue stats:', error);
        });
}

function loadNextContact() {
    fetch('/api/crm/queue/next', {
        credentials: 'include'
    })
        .then(response => safeJsonParse(response))
        .then(data => {
            if (data.success) {
                updateNextContact(data.contact);
            }
        })
        .catch(error => {
            console.error('Error loading next contact:', error);
        });
}

function updateQueueStats(stats) {
    // Update stats cards
    const highElement = document.querySelector('.text-danger');
    const mediumElement = document.querySelector('.text-warning');
    const lowElement = document.querySelector('.text-info');
    const totalElement = document.querySelector('.text-primary');
    
    if (highElement) highElement.textContent = stats.pending_high || 0;
    if (mediumElement) mediumElement.textContent = stats.pending_medium || 0;
    if (lowElement) lowElement.textContent = stats.pending_low || 0;
    if (totalElement) totalElement.textContent = stats.total_pending || 0;
}

function updateNextContact(contact) {
    const container = document.getElementById('nextContactContainer');
    
    if (contact) {
        container.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h4>${contact.name}</h4>
                    <p class="mb-1"><strong>Telefon:</strong> ${contact.phone || 'Brak numeru'}</p>
                    ${contact.email ? `<p class="mb-1"><strong>Email:</strong> ${contact.email}</p>` : ''}
                    ${contact.company ? `<p class="mb-1"><strong>Firma:</strong> ${contact.company}</p>` : ''}
                    <p class="mb-1"><strong>Próby:</strong> ${contact.call_attempts}/${contact.max_call_attempts}</p>
                </div>
                <div class="col-md-6">
                    <div class="d-grid gap-2">
                        ${contact.phone ? `<a href="tel:${contact.phone}" class="btn admin-btn">
                            <i class="fas fa-phone me-2"></i>Zadzwoń
                        </a>` : ''}
                        <button class="btn admin-btn-secondary" onclick="startCall(${contact.id})">
                            <i class="fas fa-play me-2"></i>Rozpocznij połączenie
                        </button>
                        <button class="btn btn-sm admin-btn-outline refresh-button" onclick="refreshQueueData()">
                            <i class="fas fa-sync-alt me-2"></i>Odśwież kolejkę
                        </button>
                    </div>
                </div>
            </div>
        `;
    } else {
        container.innerHTML = `
            <div class="text-center">
                <i class="fas fa-check-circle fa-3x text-success mb-3"></i>
                <p class="text-muted">Brak kontaktów w kolejce</p>
                <button class="btn btn-sm admin-btn-outline refresh-button" onclick="refreshQueueData()" style="margin-top: 10px;">
                    <i class="fas fa-sync-alt me-2"></i>Odśwież kolejkę
                </button>
            </div>
        `;
    }
}

function startCall(contactId) {
    // Show call form
    const callForm = document.getElementById('callForm');
    if (callForm) {
        callForm.style.display = 'block';
        const contactIdInput = document.getElementById('contactId');
        if (contactIdInput) {
            contactIdInput.value = contactId;
        }
    }
}

function handleCallSubmission(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {
        contact_id: formData.get('contactId'),
        callStatus: formData.get('callStatus'),
        eventId: formData.get('eventId'),
        callbackDate: formData.get('callbackDate'),
        callNotes: formData.get('callNotes')
    };
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Zapisywanie...';
    submitBtn.disabled = true;
    
    fetch('/api/crm/calls/process', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(data)
    })
    .then(response => safeJsonParse(response))
    .then(data => {
        if (data.success) {
            // Show success message
            if (window.toastManager) {
                window.toastManager.success('Połączenie przetworzone pomyślnie!');
            } else {
                alert('Połączenie przetworzone pomyślnie!');
            }
            
            // Hide form and refresh data instead of reloading page
            const callForm = document.getElementById('callForm');
            if (callForm) {
                callForm.style.display = 'none';
                callForm.reset();
            }
            isFormVisible = false;
            
            // Refresh queue data
            refreshQueueData();
        } else {
            if (window.toastManager) {
                window.toastManager.error('Błąd: ' + data.error);
            } else {
                alert('Błąd: ' + data.error);
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if (window.toastManager) {
            window.toastManager.error('Wystąpił błąd podczas przetwarzania połączenia');
        } else {
            alert('Wystąpił błąd podczas przetwarzania połączenia');
        }
    })
    .finally(() => {
        // Reset button
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

// Handle callback date field visibility
function toggleCallbackDate() {
    const callStatus = document.getElementById('callStatus');
    const callbackDateGroup = document.getElementById('callbackDateGroup');
    
    if (callStatus && callbackDateGroup) {
        if (callStatus.value === 'callback') {
            callbackDateGroup.style.display = 'block';
        } else {
            callbackDateGroup.style.display = 'none';
        }
    }
}

// Initialize callback date toggle
document.addEventListener('DOMContentLoaded', function() {
    const callStatus = document.getElementById('callStatus');
    if (callStatus) {
        callStatus.addEventListener('change', toggleCallbackDate);
        toggleCallbackDate(); // Initial call
    }
});

// Auto-refresh functionality
let refreshInterval;
let isFormVisible = false;

function setupAutoRefresh() {
    // Refresh every 30 seconds
    refreshInterval = setInterval(() => {
        // Only refresh if form is not visible (user is not in the middle of a call)
        if (!isFormVisible) {
            refreshQueueData();
        }
    }, 30000); // 30 seconds
    
    // Add visual indicator for auto-refresh
    addRefreshIndicator();
}

function refreshQueueData() {
    // Show subtle loading indicator
    showRefreshIndicator();
    
    // Load both stats and next contact
    Promise.all([
        fetch('/api/crm/queue/stats', { credentials: 'include' }).then(response => safeJsonParse(response)),
        fetch('/api/crm/queue/next', { credentials: 'include' }).then(response => safeJsonParse(response))
    ])
    .then(([statsData, contactData]) => {
        if (statsData.success) {
            updateQueueStats(statsData.stats);
        }
        if (contactData.success) {
            updateNextContact(contactData.contact);
        }
        hideRefreshIndicator();
    })
    .catch(error => {
        console.error('Error refreshing queue data:', error);
        hideRefreshIndicator();
    });
}

function addRefreshIndicator() {
    // Add refresh indicator to the page
    const indicator = document.createElement('div');
    indicator.id = 'refreshIndicator';
    indicator.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i>';
    indicator.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(0, 0, 0, 0.7);
        color: white;
        padding: 8px 12px;
        border-radius: 20px;
        font-size: 14px;
        z-index: 1000;
        display: none;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
    `;
    document.body.appendChild(indicator);
}

function showRefreshIndicator() {
    const indicator = document.getElementById('refreshIndicator');
    if (indicator) {
        indicator.style.display = 'block';
    }
}

function hideRefreshIndicator() {
    const indicator = document.getElementById('refreshIndicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
}

function startCall(contactId) {
    // Show call form
    const callForm = document.getElementById('callForm');
    if (callForm) {
        callForm.style.display = 'block';
        const contactIdInput = document.getElementById('contactId');
        if (contactIdInput) {
            contactIdInput.value = contactId;
        }
        // Mark form as visible to pause auto-refresh
        isFormVisible = true;
    }
}

// Override the original startCall function to track form visibility
function handleCallFormVisibility() {
    const callForm = document.getElementById('callForm');
    if (callForm) {
        // Check if form is visible
        const isVisible = callForm.style.display !== 'none' && callForm.offsetParent !== null;
        isFormVisible = isVisible;
        
        if (!isVisible) {
            // Form is hidden, refresh data immediately
            refreshQueueData();
        }
    }
}

// Monitor form visibility changes
document.addEventListener('DOMContentLoaded', function() {
    // Check form visibility every 5 seconds
    setInterval(handleCallFormVisibility, 5000);
});

// Manual refresh button functionality
function addManualRefreshButton() {
    const nextContactContainer = document.getElementById('nextContactContainer');
    if (nextContactContainer) {
        const refreshButton = document.createElement('button');
        refreshButton.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Odśwież kolejkę';
        refreshButton.className = 'btn btn-sm admin-btn-outline';
        refreshButton.style.marginTop = '10px';
        refreshButton.onclick = function() {
            refreshQueueData();
        };
        
        // Add button to the next contact container
        const existingButton = nextContactContainer.querySelector('.refresh-button');
        if (!existingButton) {
            refreshButton.classList.add('refresh-button');
            nextContactContainer.appendChild(refreshButton);
        }
    }
}

// Add manual refresh button when page loads
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(addManualRefreshButton, 1000);
});
