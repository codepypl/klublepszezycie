// Admin Email Queue JavaScript for Lepsze Życie Club

// Global variables
let currentPage = 1;
let currentPerPage = 10;
let currentFilter = 'pending';
let progressInterval = null;
let progressStartTime = null;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    if (!window.location.pathname.includes('email-queue')) {
        return;
    }
    
    loadStats();
    loadQueue('pending');
    
    // BulkDelete will auto-initialize due to bulk-delete-table class
    console.log('🔍 BulkDelete should auto-initialize for queueTable');
    
    
    // Setup auto-refresh
    setupEmailQueueAutoRefresh();
    
    // Clean up interval when leaving page
    window.addEventListener('beforeunload', function() {
        if (emailQueueRefreshInterval) {
            console.log('🧹 Cleaning up email queue auto-refresh interval');
            clearInterval(emailQueueRefreshInterval);
        }
    });
    
    // Make functions globally available
    window.processQueue = processQueue;
    window.retryFailed = retryFailed;
    window.retryEmail = retryEmail;
    window.deleteEmail = deleteEmail;
    window.loadQueue = loadQueue;
    window.showProgressBar = showProgressBar;
    window.hideProgressBar = hideProgressBar;
    window.startProgressMonitoring = startProgressMonitoring;
    window.restartEmailQueueAutoRefresh = restartEmailQueueAutoRefresh;
    
    // Initialize CRUD Refresh Manager for email queue
    if (typeof CRUDRefreshManager !== 'undefined' && window.crudRefreshManager) {
        window.crudRefreshManager.init(() => {
            loadStats();
            loadQueue(currentFilter || 'pending');
        });
        console.log('CRUD Refresh Manager initialized for email queue');
    }
    window.updateProgress = updateProgress;
    window.showTestRow = () => {
        const testRow = document.getElementById('testRow');
        if (testRow) {
            testRow.style.display = '';
            console.log('🧪 Test row shown');
            // Reinitialize bulk delete
            if (window.emailQueueBulkDelete) {
                window.emailQueueBulkDelete = null;
            }
            window.emailQueueBulkDelete = new BulkDelete('queueTable', '/api/bulk-delete/email-queue', {
                selectAllId: 'selectAll',
                deleteButtonId: 'bulkDeleteBtn',
                confirmMessage: 'Czy na pewno chcesz usunąć wybrane emaile z kolejki?',
                successMessage: 'Emaile zostały usunięte z kolejki pomyślnie',
                errorMessage: 'Wystąpił błąd podczas usuwania emaili'
            });
        }
    };
    
    // Test functions
    window.testStats = () => {
        console.log('🧪 Testing stats...');
        loadStats();
    };
    
    window.testQueue = () => {
        console.log('🧪 Testing queue...');
        loadQueue('pending');
    };
    
    window.testPagination = () => {
        console.log('🧪 Testing pagination...');
        const paginationElement = document.getElementById('pagination');
        console.log('Pagination element:', paginationElement);
        console.log('Pagination instance:', paginationElement?.paginationInstance);
    };
});


// Load statistics
function loadStats() {
    console.log('📊 Loading email queue stats...');
    fetch('/api/email/queue-stats')
        .then(response => {
            console.log('📡 Stats API response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('📊 Stats API response data:', data);
            if (data.success) {
                document.getElementById('totalEmails').textContent = data.stats.total;
                document.getElementById('pendingEmails').textContent = data.stats.pending;
                document.getElementById('sentEmails').textContent = data.stats.sent;
                document.getElementById('failedEmails').textContent = data.stats.failed;
                console.log('✅ Stats updated:', data.stats);
            } else {
                console.log('❌ Stats API error:', data.error);
                toastManager.error('Błąd ładowania statystyk: ' + data.error);
            }
        })
        .catch(error => {
            console.error('❌ Error loading stats:', error);
            toastManager.error('Błąd ładowania statystyk');
        });
}

// Load queue
function loadQueue(filter) {
    currentFilter = filter;
    
    // Map filter names to button IDs
    const filterMap = {
        'pending': 'filterPending',
        'sent': 'filterSent', 
        'failed': 'filterFailed',
        'all': 'filterAll'
    };
    
    const buttonId = filterMap[filter];
    
    if (buttonId) {
        const button = document.getElementById(buttonId);
        if (button) {
            // Remove active class from all filter buttons first
            document.querySelectorAll('[id^="filter"]').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Add active class to current button
            button.classList.add('active');
        }
    }
    
    const params = new URLSearchParams({
        page: currentPage,
        per_page: currentPerPage,
        filter: filter
    });
    
    fetch(`/api/email/queue?${params}`)
        .then(response => {
            console.log('📡 Queue API response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('📊 Queue API response data:', data);
            if (data.success) {
                displayQueue(data.emails);
                if (data.pagination) {
                    console.log('📄 Pagination data:', data.pagination);
                    // Initialize or update pagination
                    const paginationElement = document.getElementById('pagination');
                    if (paginationElement) {
                        if (paginationElement.paginationInstance) {
                            console.log('🔄 Updating existing pagination');
                            paginationElement.paginationInstance.setData(data.pagination);
                        } else {
                            console.log('🆕 Initializing new pagination');
                            // Check if SimplePagination class is available
                            if (typeof SimplePagination === 'undefined') {
                                console.error('SimplePagination class not available. Make sure simple-paginate.js is loaded.');
                                return;
                            }
                            
                            // Initialize pagination for the first time
                            paginationElement.paginationInstance = new SimplePagination('pagination', {
                                showInfo: true,
                                showPerPage: true,
                                perPageOptions: [5, 10, 25, 50, 100],
                                defaultPerPage: 10,
                                maxVisiblePages: 5
                            });
                            
                            // Set callbacks
                            paginationElement.paginationInstance.setPageChangeCallback((page) => {
                                console.log('📄 Page changed to:', page);
                                currentPage = page;
                                loadQueue(currentFilter);
                            });
                            
                            paginationElement.paginationInstance.setPerPageChangeCallback((newPage, perPage) => {
                                console.log('📄 Per page changed to:', perPage, 'page:', newPage);
                                currentPerPage = perPage;
                                currentPage = newPage;
                                loadQueue(currentFilter);
                            });
                            
                            paginationElement.paginationInstance.setData(data.pagination);
                        }
                    } else {
                        console.log('❌ Pagination element not found');
                    }
                } else {
                    console.log('❌ No pagination data received');
                }
            } else {
                console.log('❌ Queue API error:', data.error);
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
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">Brak emaili</td></tr>';
        return;
    }
    
    emails.forEach(email => {
        const row = document.createElement('tr');
        
        let statusClass = 'secondary';
        if (email.status === 'sent') statusClass = 'success';
        else if (email.status === 'failed') statusClass = 'danger';
        else if (email.status === 'pending') statusClass = 'warning';
        
        const checkboxHtml = email.status !== 'sent' ? `<input type="checkbox" name="itemIds" value="${email.id}">` : '';
        console.log(`📧 Email ${email.id} (${email.status}): checkbox = ${checkboxHtml ? 'YES' : 'NO'}`);
        
        row.innerHTML = `
            <td>
                ${checkboxHtml}
            </td>
            <td><span class="badge admin-badge admin-badge-primary">${email.id}</span></td>
            <td>${email.to_email}</td>
            <td style="word-wrap: break-word; word-break: break-word; max-width: 200px;">${email.subject}</td>
            <td><span class="admin-badge admin-badge-${statusClass}">${email.status}</span></td>
            <td>${email.scheduled_at ? new Date(email.scheduled_at).toLocaleString('pl-PL', {hour12: false}) : '-'}</td>
            <td>${email.sent_at ? new Date(email.sent_at).toLocaleString('pl-PL', {hour12: false}) : '-'}</td>
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
    
    // Reinitialize bulk delete after table update
    console.log('🔄 Reinitializing BulkDelete after table update...');
    
    // Check if checkboxes exist
    const checkboxes = document.querySelectorAll('#queueTable input[type="checkbox"][name="itemIds"]');
    console.log(`🔍 Found ${checkboxes.length} checkboxes in table`);
    
    // Create new BulkDelete instance
    if (window.emailQueueBulkDelete) {
        window.emailQueueBulkDelete = null;
    }
    
    window.emailQueueBulkDelete = new BulkDelete('queueTable', '/api/bulk-delete/email-queue', {
        selectAllId: 'selectAll',
        deleteButtonId: 'bulkDeleteBtn',
        confirmMessage: 'Czy na pewno chcesz usunąć wybrane emaile z kolejki?',
        successMessage: 'Emaile zostały usunięte z kolejki pomyślnie',
        errorMessage: 'Wystąpił błąd podczas usuwania emaili'
    });
    
    console.log('✅ BulkDelete reinitialized');
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
    console.log('🔄 Setting up email queue auto-refresh...');
    
    // Clear any existing interval
    if (emailQueueRefreshInterval) {
        clearInterval(emailQueueRefreshInterval);
    }
    
    // Refresh every 15 seconds (more frequent than CRM pages)
    emailQueueRefreshInterval = setInterval(() => {
        console.log('⏰ Auto-refresh triggered, isProcessing:', isProcessing);
        // Only refresh if not currently processing
        if (!isProcessing) {
            console.log('🔄 Refreshing email queue data...');
            refreshEmailQueueData();
        } else {
            console.log('⏸️ Skipping refresh - processing in progress');
        }
    }, 15000); // 15 seconds
    
    console.log('✅ Auto-refresh interval set:', emailQueueRefreshInterval);
    
    // Add refresh indicator
    addEmailQueueRefreshIndicator();
    
    // Add manual refresh button
    addEmailQueueRefreshButton();
    
    // Initial refresh after 2 seconds
    setTimeout(() => {
        console.log('🚀 Initial auto-refresh...');
        refreshEmailQueueData();
    }, 2000);
}

function refreshEmailQueueData() {
    console.log('📊 Starting email queue data refresh...');
    
    // Show subtle loading indicator
    showEmailQueueRefreshIndicator();
    
    // Load both stats and queue
    Promise.all([
        fetch('/api/email/queue-stats').then(response => {
            console.log('📡 Stats API response status:', response.status);
            
            // Sprawdź czy response to JSON czy HTML (strona logowania)
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return response.json();
            } else {
                console.warn('⚠️ Stats API zwróciło HTML zamiast JSON - prawdopodobnie sesja wygasła');
                throw new Error('Sesja wygasła - wymagane ponowne logowanie');
            }
        }),
        fetch(`/api/email/queue?page=${currentPage}&per_page=${currentPerPage}&filter=${currentFilter}`).then(response => {
            console.log('📡 Queue API response status:', response.status);
            
            // Sprawdź czy response to JSON czy HTML (strona logowania)
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return response.json();
            } else {
                console.warn('⚠️ Queue API zwróciło HTML zamiast JSON - prawdopodobnie sesja wygasła');
                throw new Error('Sesja wygasła - wymagane ponowne logowanie');
            }
        })
    ])
    .then(([statsData, queueData]) => {
        console.log('📊 Stats data received:', statsData);
        console.log('📋 Queue data received:', queueData);
        
        if (statsData.success) {
            console.log('✅ Updating stats:', statsData.stats);
            updateEmailQueueStats(statsData.stats);
        } else {
            console.error('❌ Stats API error:', statsData.error);
        }
        
        if (queueData.success) {
            console.log('✅ Updating queue display with', queueData.emails.length, 'emails');
            displayQueue(queueData.emails);
            // Update pagination if it exists
            if (queueData.pagination) {
                const paginationElement = document.getElementById('pagination');
                if (paginationElement && paginationElement.paginationInstance) {
                    paginationElement.paginationInstance.setData(queueData.pagination);
                }
            }
        } else {
            console.error('❌ Queue API error:', queueData.error);
        }
        
        hideEmailQueueRefreshIndicator();
        console.log('✅ Email queue refresh completed');
    })
    .catch(error => {
        console.error('❌ Error refreshing email queue data:', error);
        hideEmailQueueRefreshIndicator();
        
        // Sprawdź czy to błąd sesji
        if (error.message && error.message.includes('Sesja wygasła')) {
            console.warn('🔐 Sesja wygasła - zatrzymuję automatyczne odświeżanie');
            
            // Zatrzymaj automatyczne odświeżanie
            if (emailQueueRefreshInterval) {
                clearInterval(emailQueueRefreshInterval);
                emailQueueRefreshInterval = null;
            }
            
            // Pokaż powiadomienie użytkownikowi
            if (window.toastManager) {
                window.toastManager.warning('Sesja wygasła - zaloguj się ponownie aby kontynuować automatyczne odświeżanie');
            }
        }
    });
}

function updateEmailQueueStats(stats) {
    console.log('📊 Updating email queue stats:', stats);
    
    // Update stats cards
    const totalElement = document.getElementById('totalEmails');
    const pendingElement = document.getElementById('pendingEmails');
    const sentElement = document.getElementById('sentEmails');
    const failedElement = document.getElementById('failedEmails');
    
    console.log('🔍 DOM elements found:', {
        total: !!totalElement,
        pending: !!pendingElement,
        sent: !!sentElement,
        failed: !!failedElement
    });
    
    if (totalElement) {
        const oldValue = totalElement.textContent;
        totalElement.textContent = stats.total || 0;
        console.log('📈 Total updated:', oldValue, '->', stats.total || 0);
    }
    if (pendingElement) {
        const oldValue = pendingElement.textContent;
        pendingElement.textContent = stats.pending || 0;
        console.log('⏳ Pending updated:', oldValue, '->', stats.pending || 0);
    }
    if (sentElement) {
        const oldValue = sentElement.textContent;
        sentElement.textContent = stats.sent || 0;
        console.log('✅ Sent updated:', oldValue, '->', stats.sent || 0);
    }
    if (failedElement) {
        const oldValue = failedElement.textContent;
        failedElement.textContent = stats.failed || 0;
        console.log('❌ Failed updated:', oldValue, '->', stats.failed || 0);
    }
    
    console.log('✅ Stats update completed');
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

// Restart auto-refresh after login
function restartEmailQueueAutoRefresh() {
    console.log('🔄 Restarting email queue auto-refresh after login...');
    
    // Clear existing interval
    if (emailQueueRefreshInterval) {
        clearInterval(emailQueueRefreshInterval);
    }
    
    // Setup auto-refresh again
    setupEmailQueueAutoRefresh();
}

// Clear all emails from queue (except sent ones)
function clearAllQueue() {
    if (confirm('⚠️ UWAGA: Czy na pewno chcesz wyczyścić całą kolejkę emaili?\n\nTo usunie wszystkie oczekujące, nieudane i przetwarzane emaile.\nWysłane emaile zostaną zachowane jako historia.\n\nTa operacja jest nieodwracalna!')) {
        fetch('/api/email/queue/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                toastManager.success(data.message);
                // Refresh stats and queue
                loadStats();
                loadQueue(currentFilter);
            } else {
                toastManager.error('Błąd czyszczenia kolejki: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error clearing queue:', error);
            toastManager.error('Błąd czyszczenia kolejki');
        });
    }
}

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

// Restart auto-refresh after login
function restartEmailQueueAutoRefresh() {
    console.log('🔄 Restarting email queue auto-refresh after login...');
    
    // Clear existing interval
    if (emailQueueRefreshInterval) {
        clearInterval(emailQueueRefreshInterval);
    }
    
    // Setup auto-refresh again
    setupEmailQueueAutoRefresh();
}
