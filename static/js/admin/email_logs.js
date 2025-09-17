// Admin Email Logs JavaScript for Lepsze Życie Club

// Global variables
let currentPage = 1;
let currentPerPage = 20;
let currentFilters = {};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    loadLogsStats();
    loadLogs();
    
    // Set up pagination handlers for auto-initialization
    window.paginationHandlers = {
        onPageChange: (page) => {
            currentPage = page;
            loadLogs();
        },
        onPerPageChange: (newPage, perPage) => {
            console.log('Per page changed:', { newPage, perPage, currentPerPage }); // Debug log
            currentPerPage = perPage;
            currentPage = newPage; // Use the page passed by pagination
            loadLogs();
        }
    };
    
    // Set up event listeners
    document.getElementById('searchInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchLogs();
        }
    });
    
    // Set default date range (last 30 days)
    const today = new Date();
    const thirtyDaysAgo = new Date(today.getTime() - (30 * 24 * 60 * 60 * 1000));
    document.getElementById('dateFrom').value = thirtyDaysAgo.toISOString().split('T')[0];
    document.getElementById('dateTo').value = today.toISOString().split('T')[0];
});

// Load logs statistics
function loadLogsStats() {
    fetch('/api/email/logs/stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateLogsStats(data.stats);
            }
        })
        .catch(error => {
            console.error('Error loading logs stats:', error);
        });
}

// Update stats display
function updateLogsStats(stats) {
    document.getElementById('totalLogs').textContent = stats.total || 0;
    document.getElementById('sentLogs').textContent = stats.sent || 0;
    document.getElementById('failedLogs').textContent = stats.failed || 0;
    document.getElementById('bouncedLogs').textContent = stats.bounced || 0;
}

// Load logs
function loadLogs() {
    const params = new URLSearchParams({
        page: currentPage,
        per_page: currentPerPage,
        ...currentFilters
    });
    
    fetch(`/api/email/logs?${params}`)
        .then(response => response.json())
        .then(data => {
            console.log('API Response:', data); // Debug log
            if (data.success) {
                displayLogs(data.logs);
                if (data.pagination) {
                    console.log('Pagination data:', data.pagination); // Debug log
                    updatePagination(data.pagination);
                }
            } else {
                window.toastManager.show('Błąd ładowania logów: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error loading logs:', error);
            window.toastManager.show('Błąd ładowania logów', 'error');
        });
}

// Display logs
function displayLogs(logs) {
    const tbody = document.getElementById('logsTableBody');
    tbody.innerHTML = '';
    
    if (logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">Brak logów</td></tr>';
        return;
    }
    
    logs.forEach(log => {
        const row = document.createElement('tr');
        
        let statusClass = 'secondary';
        let statusText = log.status;
        if (log.status === 'sent') {
            statusClass = 'success';
            statusText = 'Wysłane';
        } else if (log.status === 'failed') {
            statusClass = 'danger';
            statusText = 'Nieudane';
        } else if (log.status === 'bounced') {
            statusClass = 'warning';
            statusText = 'Odrzucone';
        }
        
        const errorMessage = log.error_message ? 
            (log.error_message.length > 50 ? log.error_message.substring(0, 50) + '...' : log.error_message) : 
            '-';
        
        row.innerHTML = `
            <td>${log.id}</td>
            <td>${log.email}</td>
            <td>${log.subject}</td>
            <td><span class="admin-badge admin-badge-${statusClass}">${statusText}</span></td>
            <td>${log.sent_at ? new Date(log.sent_at + 'Z').toLocaleString('pl-PL', {hour12: false, timeZone: 'Europe/Warsaw'}) : '-'}</td>
            <td title="${log.error_message || ''}">${errorMessage}</td>
            <td>${log.template_name || '-'}</td>
            <td>${log.campaign_name || '-'}</td>
            <td>
                <div class="btn-group" role="group">
                    <button class="btn btn-sm admin-btn-outline" onclick="viewLogDetails(${log.id})" title="Zobacz szczegóły">
                        <i class="fas fa-eye"></i>
                    </button>
                </div>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// Search logs
function searchLogs() {
    currentFilters = {
        search: document.getElementById('searchInput').value,
        status: document.getElementById('statusFilter').value,
        date_from: document.getElementById('dateFrom').value,
        date_to: document.getElementById('dateTo').value
    };
    
    // Remove empty filters
    Object.keys(currentFilters).forEach(key => {
        if (!currentFilters[key] || currentFilters[key] === 'all') {
            delete currentFilters[key];
        }
    });
    
    currentPage = 1;
    loadLogs();
}

// Clear filters
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('statusFilter').value = 'all';
    document.getElementById('dateFrom').value = '';
    document.getElementById('dateTo').value = '';
    
    currentFilters = {};
    currentPage = 1;
    loadLogs();
}

// Refresh logs
function refreshLogs() {
    loadLogsStats();
    loadLogs();
}

// View log details
function viewLogDetails(logId) {
    fetch(`/api/email/logs/${logId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayLogDetails(data.log);
            } else {
                window.toastManager.show('Błąd ładowania szczegółów: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error loading log details:', error);
            window.toastManager.show('Błąd ładowania szczegółów', 'error');
        });
}

// Display log details in modal
function displayLogDetails(log) {
    const content = document.getElementById('logDetailsContent');
    
    content.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6>Podstawowe informacje</h6>
                <table class="table table-sm">
                    <tr><td><strong>ID:</strong></td><td>${log.id}</td></tr>
                    <tr><td><strong>Email:</strong></td><td>${log.email}</td></tr>
                    <tr><td><strong>Temat:</strong></td><td>${log.subject}</td></tr>
                    <tr><td><strong>Status:</strong></td><td><span class="admin-badge admin-badge-${log.status === 'sent' ? 'success' : log.status === 'failed' ? 'danger' : 'warning'}">${log.status}</span></td></tr>
                    <tr><td><strong>Wysłano:</strong></td><td>${log.sent_at ? new Date(log.sent_at + 'Z').toLocaleString('pl-PL', {hour12: false, timeZone: 'Europe/Warsaw'}) : '-'}</td></tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6>Szczegóły</h6>
                <table class="table table-sm">
                    <tr><td><strong>Szablon:</strong></td><td>${log.template_name || '-'}</td></tr>
                    <tr><td><strong>Kampania:</strong></td><td>${log.campaign_name || '-'}</td></tr>
                    <tr><td><strong>Błąd:</strong></td><td>${log.error_message || '-'}</td></tr>
                </table>
            </div>
        </div>
        ${log.recipient_data ? `
        <div class="row mt-3">
            <div class="col-12">
                <h6>Dane odbiorcy</h6>
                <pre class="bg-light p-3 rounded">${JSON.stringify(JSON.parse(log.recipient_data), null, 2)}</pre>
            </div>
        </div>
        ` : ''}
    `;
    
    const modal = new bootstrap.Modal(document.getElementById('logDetailsModal'));
    modal.show();
}

// Update pagination
function updatePagination(pagination) {
    console.log('Updating pagination with data:', pagination); // Debug log
    const paginationElement = document.getElementById('pagination');
    if (paginationElement) {
        if (paginationElement.paginationInstance) {
            paginationElement.paginationInstance.setData(pagination);
        } else {
            // If pagination instance doesn't exist, create it
            const options = {
                containerId: 'pagination',
                showInfo: true,
                showPerPage: true,
                defaultPerPage: parseInt(paginationElement.dataset.defaultPerPage) || 20,
                maxVisiblePages: parseInt(paginationElement.dataset.maxVisiblePages) || 5
            };
            
            const paginationInstance = new Pagination(options);
            paginationElement.paginationInstance = paginationInstance;
            paginationInstance.setData(pagination);
        }
    }
}

// Clear old logs
function clearOldLogs() {
    if (confirm('Czy na pewno chcesz wyczyścić stare logi (starsze niż 30 dni)? Tej operacji nie można cofnąć.')) {
        fetch('/api/email/logs/clear-old', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.toastManager.show(data.message, 'success');
                refreshLogs();
            } else {
                window.toastManager.show('Błąd czyszczenia: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error clearing logs:', error);
            window.toastManager.show('Błąd czyszczenia logów', 'error');
        });
    }
}

