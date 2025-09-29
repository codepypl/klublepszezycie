// Admin Email Logs JavaScript for Lepsze Życie Club

// Global variables
let currentPage = 1;
let currentPerPage = 20;
let currentFilters = {};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Load stats and logs
    loadLogsStats();
    loadLogs();
    
    // Pagination handlers are now set up in updatePagination function
    
    // Initialize CRUD Refresh Manager for email logs
    if (typeof CRUDRefreshManager !== 'undefined' && window.crudRefreshManager) {
        window.crudRefreshManager.init(() => {
            loadLogsStats();
            loadLogs();
        });
        console.log('CRUD Refresh Manager initialized for email logs');
    }
    
    // Initialize table resizer
    if (window.tableResizer) {
        window.tableResizer.init('#logsTable');
    }
    
    // Setup auto-refresh for email logs
    setupEmailLogsAutoRefresh();
    
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
    fetch('/admin/logs/stats/refresh')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Stats API Response:', data); // Debug log
            if (data.success) {
                updateLogsStats(data.stats);
            } else {
                console.error('Error in stats response:', data.error);
                window.toastManager.show('Błąd ładowania statystyk: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error loading logs stats:', error);
            window.toastManager.show('Błąd ładowania statystyk logów', 'error');
        });
}

// Update stats display
function updateLogsStats(stats) {
    document.getElementById('totalLogs').textContent = stats.total_emails || 0;
    document.getElementById('sentLogs').textContent = stats.status_breakdown?.sent || 0;
    document.getElementById('failedLogs').textContent = stats.status_breakdown?.failed || 0;
    document.getElementById('bouncedLogs').textContent = stats.status_breakdown?.bounced || 0;
}

// Load logs
function loadLogs() {
    const params = new URLSearchParams({
        page: currentPage,
        per_page: currentPerPage,
        ...currentFilters
    });
    
    fetch(`/api/logs?${params}`)
        .then(response => response.json())
        .then(data => {
            console.log('API Response:', data); // Debug log
            if (data.success) {
                displayLogs(data.logs);
                if (data.pagination) {
                    console.log('Pagination data:', data.pagination); // Debug log
                    // Update currentPerPage from server response
                    currentPerPage = data.pagination.per_page;
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
        
        // Event info
        let eventInfo = '-';
        if (log.event_id) {
            if (log.event_info) {
                eventInfo = `<a href="/admin/events/${log.event_id}" class="text-decoration-none" title="${log.event_info.title}">
                    <span class="badge admin-badge admin-badge-info">${log.event_id}</span>
                </a>`;
            } else {
                eventInfo = `<span class="badge admin-badge admin-badge-secondary" title="Usunięte wydarzenie">${log.event_id}</span>`;
            }
        }
        
        // Template info
        let templateInfo = '-';
        if (log.template_id) {
            const templateName = log.template_name || 'Usunięty szablon';
            templateInfo = `<span class="badge admin-badge admin-badge-primary" style="cursor: pointer;" 
                onclick="openTemplateModal(${log.template_id})" title="${templateName}">${log.template_id}</span>`;
        }
        
        // Campaign info
        let campaignInfo = '-';
        if (log.campaign_id) {
            const campaignName = log.campaign_name || 'Usunięta kampania';
            campaignInfo = `<a href="/admin/email-campaigns/${log.campaign_id}" class="text-decoration-none" title="${campaignName}">
                <span class="badge admin-badge admin-badge-warning">${log.campaign_id}</span>
            </a>`;
        }
        
        row.innerHTML = `
            <td><span class="badge admin-badge admin-badge-primary">${log.id}</span></td>
            <td>${log.email}</td>
            <td>${eventInfo}</td>
            <td><span class="admin-badge admin-badge-${statusClass}">${statusText}</span></td>
            <td>${log.sent_at ? new Date(log.sent_at).toLocaleString('pl-PL', {hour12: false}) : '-'}</td>
            <td title="${log.error_message || ''}">${errorMessage}</td>
            <td>${templateInfo}</td>
            <td>${campaignInfo}</td>
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
        event_id: document.getElementById('eventIdFilter').value,
        template_id: document.getElementById('templateIdFilter').value,
        campaign_id: document.getElementById('campaignIdFilter').value,
        date_from: document.getElementById('dateFrom').value,
        date_to: document.getElementById('dateTo').value,
        time_from: document.getElementById('timeFrom').value,
        time_to: document.getElementById('timeTo').value
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
    document.getElementById('eventIdFilter').value = '';
    document.getElementById('templateIdFilter').value = '';
    document.getElementById('campaignIdFilter').value = '';
    document.getElementById('dateFrom').value = '';
    document.getElementById('dateTo').value = '';
    document.getElementById('timeFrom').value = '';
    document.getElementById('timeTo').value = '';
    
    currentFilters = {};
    currentPage = 1;
    loadLogs();
}

// Open template modal
function openTemplateModal(templateId) {
    // Redirect to email templates page with modal
    window.location.href = `/admin/email-templates?modal=${templateId}`;
}

// Refresh logs
function refreshLogs() {
    loadLogsStats();
    loadLogs();
}

// Setup auto-refresh for email logs
let emailLogsRefreshInterval;

function setupEmailLogsAutoRefresh() {
    // Refresh every 30 seconds (less frequent than queue since logs don't change as often)
    emailLogsRefreshInterval = setInterval(() => {
        refreshLogs();
    }, 30000); // 30 seconds
    
    console.log('Email logs auto-refresh setup: every 30 seconds');
    
    // Initial refresh after 2 seconds
    setTimeout(() => {
        console.log('🚀 Initial email logs refresh...');
        refreshLogs();
    }, 2000);
}

// View log details
function viewLogDetails(logId) {
    fetch(`/api/logs/${logId}`)
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
    
    // Event info
    let eventInfo = '-';
    if (log.event_info) {
        eventInfo = `<a href="/admin/events/${log.event_info.id}" class="text-decoration-none">
            <span class="badge admin-badge admin-badge-info">${log.event_info.id}</span>
            ${log.event_info.title}
        </a>`;
    } else if (log.event_id) {
        eventInfo = `<span class="badge admin-badge admin-badge-secondary">${log.event_id}</span>`;
    }
    
    // Template info
    let templateInfo = '-';
    if (log.template_info) {
        templateInfo = `<a href="/admin/email-templates/${log.template_info.id}" class="text-decoration-none">
            <span class="badge admin-badge admin-badge-primary">${log.template_info.id}</span>
            ${log.template_info.name}
        </a>`;
    } else if (log.template_id) {
        templateInfo = `<span class="badge admin-badge admin-badge-secondary">${log.template_id}</span>`;
    }
    
    // Campaign info
    let campaignInfo = '-';
    if (log.campaign_info) {
        campaignInfo = `<a href="/admin/email-campaigns/${log.campaign_info.id}" class="text-decoration-none">
            <span class="badge admin-badge admin-badge-warning">${log.campaign_info.id}</span>
            ${log.campaign_info.name}
        </a>`;
    } else if (log.campaign_id) {
        campaignInfo = `<span class="badge admin-badge admin-badge-secondary">${log.campaign_id}</span>`;
    }
    
    content.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6>Podstawowe informacje</h6>
                <table class="table table-sm">
                    <tr><td><strong>ID:</strong></td><td>${log.id}</td></tr>
                    <tr><td><strong>Email:</strong></td><td>${log.email}</td></tr>
                    <tr><td><strong>Temat:</strong></td><td>${log.subject}</td></tr>
                    <tr><td><strong>Status:</strong></td><td><span class="admin-badge admin-badge-${log.status === 'sent' ? 'success' : log.status === 'failed' ? 'danger' : 'warning'}">${log.status}</span></td></tr>
                    <tr><td><strong>Wysłano:</strong></td><td>${log.sent_at ? new Date(log.sent_at).toLocaleString('pl-PL', {hour12: false}) : '-'}</td></tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6>Szczegóły</h6>
                <table class="table table-sm">
                    <tr><td><strong>Wydarzenie:</strong></td><td>${eventInfo}</td></tr>
                    <tr><td><strong>ID Wydarzenia:</strong></td><td>${log.event_id || '-'}</td></tr>
                    <tr><td><strong>Szablon:</strong></td><td>${templateInfo}</td></tr>
                    <tr><td><strong>Kampania:</strong></td><td>${campaignInfo}</td></tr>
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
            // Check if SimplePagination class is available
            if (typeof SimplePagination === 'undefined') {
                console.error('SimplePagination class not available. Make sure simple-paginate.js is loaded.');
                return;
            }
            
            // If pagination instance doesn't exist, create it
            const options = {
                showInfo: true,
                showPerPage: true,
                defaultPerPage: parseInt(paginationElement.dataset.defaultPerPage) || 20,
                maxVisiblePages: parseInt(paginationElement.dataset.maxVisiblePages) || 5,
                perPageOptions: [5, 10, 25, 50, 100]
            };
            
            const paginationInstance = new SimplePagination('pagination', options);
            paginationElement.paginationInstance = paginationInstance;
            
            // Set up callbacks
            paginationInstance.setPageChangeCallback((page) => {
                console.log('Page change callback:', page);
                currentPage = page;
                loadLogs();
            });
            
            paginationInstance.setPerPageChangeCallback((page, perPage) => {
                console.log('Per page change callback:', page, perPage);
                currentPerPage = perPage;
                currentPage = page;
                loadLogs();
            });
            
            paginationInstance.setData(pagination);
        }
    }
}

// Clear old logs
function clearOldLogs() {
    // Use modal confirmation instead of confirm()
    document.getElementById('bulkDeleteMessage').innerHTML = 'Czy na pewno chcesz wyczyścić stare logi (starsze niż 48 godzin)?<br><small class="text-muted">Tej operacji nie można cofnąć.</small>';
    
    const modal = new bootstrap.Modal(document.getElementById('bulkDeleteModal'));
    modal.show();
    
    // Update confirm button
    const confirmBtn = document.getElementById('confirmBulkDelete');
    confirmBtn.onclick = function() {
        fetch('/api/logs/cleanup', {
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
        modal.hide();
    };
}

