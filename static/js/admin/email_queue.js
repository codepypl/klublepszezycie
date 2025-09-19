// Admin Email Queue JavaScript for Lepsze Życie Club

// Global variables
let currentPage = 1;
let currentPerPage = 10;
let currentFilter = 'pending';
let progressInterval = null;
let progressStartTime = null;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadStats();
    loadQueue('pending');
    
    // Set up pagination handlers for auto-initialization
    window.paginationHandlers = {
        onPageChange: (page) => {
            currentPage = page;
            loadQueue(currentFilter);
        },
        onPerPageChange: (newPage, perPage) => {
            currentPerPage = perPage;
            currentPage = newPage; // Use the page passed by pagination
            loadQueue(currentFilter);
        }
    };
    
    // Setup auto-refresh
    setupEmailQueueAutoRefresh();
    
    // Make functions globally available
    window.processQueue = processQueue;
    window.retryFailed = retryFailed;
    window.retryEmail = retryEmail;
    window.deleteEmail = deleteEmail;
    window.loadQueue = loadQueue;
    window.showProgressBar = showProgressBar;
    window.hideProgressBar = hideProgressBar;
    window.startProgressMonitoring = startProgressMonitoring;
    window.updateProgress = updateProgress;
});


// Load statistics
function loadStats() {
    fetch('/api/email/queue-stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('totalEmails').textContent = data.stats.total;
                document.getElementById('pendingEmails').textContent = data.stats.pending;
                document.getElementById('sentEmails').textContent = data.stats.sent;
                document.getElementById('failedEmails').textContent = data.stats.failed;
            }
        })
        .catch(error => {
            console.error('Error loading stats:', error);
        });
}

// Load queue
function loadQueue(filter) {
    currentFilter = filter;
    
    // Update filter buttons
    document.querySelectorAll('[id^="filter"]').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`filter${filter.charAt(0).toUpperCase() + filter.slice(1)}`).classList.add('active');
    
    const params = new URLSearchParams({
        page: currentPage,
        per_page: currentPerPage,
        filter: filter
    });
    
    fetch(`/api/email/queue?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayQueue(data.emails);
                if (data.pagination) {
                    // Update pagination if it exists
                    const paginationElement = document.getElementById('pagination');
                    if (paginationElement && paginationElement.paginationInstance) {
                        paginationElement.paginationInstance.setData(data.pagination);
                    }
                }
            } else {
                toastManager.error('Błąd ładowania kolejki: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error loading queue:', error);
            toastManager.error('Błąd ładowania kolejki');
        });
}

// Display queue
function displayQueue(emails) {
    const tbody = document.getElementById('queueTableBody');
    tbody.innerHTML = '';
    
    if (emails.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Brak emaili</td></tr>';
        return;
    }
    
    emails.forEach(email => {
        const row = document.createElement('tr');
        
        let statusClass = 'secondary';
        if (email.status === 'sent') statusClass = 'success';
        else if (email.status === 'failed') statusClass = 'danger';
        else if (email.status === 'pending') statusClass = 'warning';
        
        row.innerHTML = `
            <td>${email.id}</td>
            <td>${email.to_email}</td>
            <td>${email.subject}</td>
            <td><span class="admin-badge admin-badge-${statusClass}">${email.status}</span></td>
            <td>${email.scheduled_at ? new Date(email.scheduled_at + 'Z').toLocaleString('pl-PL', {hour12: false, timeZone: 'Europe/Warsaw'}) : '-'}</td>
            <td>${email.sent_at ? new Date(email.sent_at + 'Z').toLocaleString('pl-PL', {hour12: false, timeZone: 'Europe/Warsaw'}) : '-'}</td>
            <td>
                <div class="btn-group" role="group">
                    ${email.status === 'failed' ? `<button class="btn btn-sm admin-btn-warning" onclick="retryEmail(${email.id})" title="Ponów email">
                        <i class="fas fa-redo"></i>
                    </button>` : ''}
                    ${email.status === 'sent' ? `<button class="btn btn-sm admin-btn-outline" disabled title="Nie można usuwać wysłanych e-maili">
                        <i class="fas fa-lock"></i>
                    </button>` : `<button class="btn btn-sm admin-btn-danger" onclick="deleteEmail(${email.id})" title="Usuń email">
                        <i class="fas fa-trash"></i>
                    </button>`}
                </div>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// Process queue
function processQueue() {
    // Show progress bar
    showProgressBar();
    
    // Start processing
    fetch('/api/email/process-queue', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Start progress monitoring
            startProgressMonitoring();
        } else {
            hideProgressBar();
            toastManager.error('Błąd przetwarzania kolejki: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error processing queue:', error);
        hideProgressBar();
        toastManager.error('Błąd przetwarzania kolejki');
    });
}

// Retry failed emails
function retryFailed() {
    fetch('/api/email/retry-failed', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toastManager.success('Nieudane emaile ponowione!');
            loadStats();
            loadQueue(currentFilter);
            
            // Wywołaj globalne odświeżenie
            window.refreshAfterCRUD();
        } else {
            toastManager.error('Błąd ponawiania: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error retrying failed emails:', error);
        toastManager.error('Błąd ponawiania');
    });
}

// Retry single email
function retryEmail(emailId) {
    fetch(`/api/email/retry/${emailId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toastManager.success('Email ponowiony!');
            loadQueue(currentFilter);
            
            // Wywołaj globalne odświeżenie
            window.refreshAfterCRUD();
        } else {
            toastManager.error('Błąd ponawiania: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error retrying email:', error);
        toastManager.error('Błąd ponawiania');
    });
}

// Delete email
function deleteEmail(emailId) {
    window.deleteConfirmation.showSingleDelete(
        'email z kolejki',
        () => {
            // Continue with deletion
            performDeleteEmail(emailId);
        },
        'email z kolejki'
    );
}

function performDeleteEmail(emailId) {
    fetch(`/api/email/queue/${emailId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toastManager.success('Email usunięty!');
            loadStats();
            loadQueue(currentFilter);
            
            // Wywołaj globalne odświeżenie
            window.refreshAfterCRUD();
        } else {
            toastManager.error('Błąd usuwania: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error deleting email:', error);
        toastManager.error('Błąd usuwania');
    });
}

// Progress bar functions
function showProgressBar() {
    const container = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressDetails = document.getElementById('progressDetails');
    const progressTime = document.getElementById('progressTime');
    
    container.style.display = 'block';
    progressBar.style.width = '0%';
    progressText.textContent = '0%';
    progressDetails.textContent = 'Przygotowywanie...';
    progressTime.textContent = '00:00';
    
    progressStartTime = new Date();
}

function hideProgressBar() {
    const container = document.getElementById('progressContainer');
    container.style.display = 'none';
    
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
}

function startProgressMonitoring() {
    // Update progress every 5 seconds
    progressInterval = setInterval(updateProgress, 5000);
    
    // Initial update
    updateProgress();
}

function updateProgress() {
    fetch('/api/email/queue-progress')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const progress = data.progress;
                updateProgressBar(progress);
                
                // Check if processing is complete
                if (progress.percent >= 100 || (progress.pending === 0 && progress.processing === 0)) {
                    hideProgressBar();
                    loadStats();
                    loadQueue(currentFilter);
                    toastManager.success(`Przetwarzanie zakończone! Wysłano: ${progress.sent}, Błędy: ${progress.failed}`);
                }
            }
        })
        .catch(error => {
            console.error('Error updating progress:', error);
        });
}

function updateProgressBar(progress) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressDetails = document.getElementById('progressDetails');
    const progressTime = document.getElementById('progressTime');
    
    // Update progress bar
    progressBar.style.width = progress.percent + '%';
    progressText.textContent = progress.percent + '%';
    
    // Update details
    progressDetails.textContent = `Przetworzono: ${progress.processed}/${progress.total} | Oczekujące: ${progress.pending} | Wysłane: ${progress.sent} | Błędy: ${progress.failed}`;
    
    // Update time
    if (progressStartTime) {
        const elapsed = Math.floor((new Date() - progressStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        progressTime.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
}

// Auto-refresh functionality for email queue
let emailQueueRefreshInterval;
let isProcessing = false;

function setupEmailQueueAutoRefresh() {
    // Refresh every 15 seconds (more frequent than CRM pages)
    emailQueueRefreshInterval = setInterval(() => {
        // Only refresh if not currently processing
        if (!isProcessing) {
            refreshEmailQueueData();
        }
    }, 15000); // 15 seconds
    
    // Add refresh indicator
    addEmailQueueRefreshIndicator();
    
    // Add manual refresh button
    addEmailQueueRefreshButton();
}

function refreshEmailQueueData() {
    // Show subtle loading indicator
    showEmailQueueRefreshIndicator();
    
    // Load both stats and queue
    Promise.all([
        fetch('/api/email/queue-stats').then(response => response.json()),
        fetch(`/api/email/queue?page=${currentPage}&per_page=${currentPerPage}&filter=${currentFilter}`).then(response => response.json())
    ])
    .then(([statsData, queueData]) => {
        if (statsData.success) {
            updateEmailQueueStats(statsData.stats);
        }
        if (queueData.success) {
            displayQueue(queueData.emails);
            // Update pagination if it exists
            if (queueData.pagination) {
                const paginationElement = document.getElementById('pagination');
                if (paginationElement && paginationElement.paginationInstance) {
                    paginationElement.paginationInstance.setData(queueData.pagination);
                }
            }
        }
        hideEmailQueueRefreshIndicator();
    })
    .catch(error => {
        console.error('Error refreshing email queue data:', error);
        hideEmailQueueRefreshIndicator();
    });
}

function updateEmailQueueStats(stats) {
    // Update stats cards
    const totalElement = document.getElementById('totalEmails');
    const pendingElement = document.getElementById('pendingEmails');
    const sentElement = document.getElementById('sentEmails');
    const failedElement = document.getElementById('failedEmails');
    
    if (totalElement) totalElement.textContent = stats.total || 0;
    if (pendingElement) pendingElement.textContent = stats.pending || 0;
    if (sentElement) sentElement.textContent = stats.sent || 0;
    if (failedElement) failedElement.textContent = stats.failed || 0;
}

function addEmailQueueRefreshIndicator() {
    // Add refresh indicator to the page
    const indicator = document.createElement('div');
    indicator.id = 'emailQueueRefreshIndicator';
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

function showEmailQueueRefreshIndicator() {
    const indicator = document.getElementById('emailQueueRefreshIndicator');
    if (indicator) {
        indicator.style.display = 'block';
    }
}

function hideEmailQueueRefreshIndicator() {
    const indicator = document.getElementById('emailQueueRefreshIndicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
}

function addEmailQueueRefreshButton() {
    // Add refresh button to the page actions
    const pageActions = document.querySelector('.page-actions .d-flex');
    if (pageActions) {
        const refreshButton = document.createElement('button');
        refreshButton.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Odśwież kolejkę';
        refreshButton.className = 'btn admin-btn-outline';
        refreshButton.onclick = function() {
            refreshEmailQueueData();
        };
        
        // Add button if it doesn't exist
        const existingButton = pageActions.querySelector('.email-queue-refresh-button');
        if (!existingButton) {
            refreshButton.classList.add('email-queue-refresh-button');
            pageActions.appendChild(refreshButton);
        }
    }
}

// Override processQueue to track processing state
const originalProcessQueue = processQueue;
processQueue = function() {
    isProcessing = true;
    originalProcessQueue();
    
    // Reset processing state after 30 seconds
    setTimeout(() => {
        isProcessing = false;
        // Refresh data after processing
        refreshEmailQueueData();
    }, 30000);
};

// Override retryFailed to track processing state
const originalRetryFailed = retryFailed;
retryFailed = function() {
    isProcessing = true;
    originalRetryFailed();
    
    // Reset processing state after 30 seconds
    setTimeout(() => {
        isProcessing = false;
        // Refresh data after processing
        refreshEmailQueueData();
    }, 30000);
};
