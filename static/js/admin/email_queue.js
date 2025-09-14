// Admin Email Queue JavaScript for Lepsze Życie Club

// Global variables
let currentPage = 1;
let currentPerPage = 10;
let currentFilter = 'pending';

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
            <td>${email.scheduled_at ? new Date(email.scheduled_at).toLocaleString() : '-'}</td>
            <td>${email.sent_at ? new Date(email.sent_at).toLocaleString() : '-'}</td>
            <td>
                <div class="btn-group" role="group">
                    ${email.status === 'failed' ? `<button class="btn btn-sm admin-btn-warning" onclick="retryEmail(${email.id})" title="Ponów email">
                        <i class="fas fa-redo"></i>
                    </button>` : ''}
                    <button class="btn btn-sm admin-btn-danger" onclick="deleteEmail(${email.id})" title="Usuń email">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// Process queue
function processQueue() {
    fetch('/api/email/process-queue', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toastManager.success('Kolejka przetworzona pomyślnie!');
            loadStats();
            loadQueue(currentFilter);
        } else {
            toastManager.error('Błąd przetwarzania kolejki: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error processing queue:', error);
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
    if (confirm('Czy na pewno chcesz usunąć ten email z kolejki?')) {
        fetch(`/api/email/queue/${emailId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                toastManager.success('Email usunięty!');
                loadStats();
                loadQueue(currentFilter);
            } else {
                toastManager.error('Błąd usuwania: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error deleting email:', error);
            toastManager.error('Błąd usuwania');
        });
    }
}
