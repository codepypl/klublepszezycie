// Admin Events JavaScript for Lepsze Życie Club

// Events management functions
class EventsManager {
    constructor() {
        this.currentEventId = null;
        this.currentPage = 1;
        this.currentPerPage = 10;
        this.initializeEventListeners();
        this.loadEvents();
        this.setMinDates();
    }

    initializeEventListeners() {
        // Form submissions
        const addEventForm = document.getElementById('addEventForm');
        const editEventForm = document.getElementById('editEventForm');
        const confirmDeleteBtn = document.getElementById('confirmDeleteEvent');
        
        if (addEventForm) {
            addEventForm.addEventListener('submit', (e) => this.handleAddEvent(e));
        }
        
        if (editEventForm) {
            editEventForm.addEventListener('submit', (e) => this.handleEditEvent(e));
        }
        
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', () => this.handleDeleteEvent());
        }
    }

    showAddEventModal() {
        document.getElementById('addEventForm').reset();
        
        // Clear Quill editor
        if (window.quillInstances && window.quillInstances['eventDescription']) {
            window.quillInstances['eventDescription'].root.innerHTML = '';
        }
        
        // Set today's date as default
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('eventDate').value = today;
        document.getElementById('eventTime').value = '18:00';
        
        const modal = new bootstrap.Modal(document.getElementById('addEventModal'));
        modal.show();
    }

    editEvent(eventId) {
        fetch(`/api/event-schedule/${eventId}`)
            .then(response => {
                if (!response.ok) {
                    if (response.status === 401 || response.status === 403) {
                        throw new Error('Unauthorized');
                    }
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    const event = data.event;
                    this.populateEditForm(event);
                    
                    const modal = new bootstrap.Modal(document.getElementById('editEventModal'));
                    modal.show();
                } else {
                    window.toastManager.error(data.message || 'Błąd podczas ładowania wydarzenia');
                }
            })
            .catch(error => {
                console.error('Error loading event:', error);
                window.toastManager.error('Wystąpił błąd podczas ładowania wydarzenia');
            });
    }

    populateEditForm(event) {
        document.getElementById('editEventId').value = event.id;
        document.getElementById('editEventTitle').value = event.title || '';
        
        // Set event type
        const eventTypeSelect = document.getElementById('editEventType');
        if (eventTypeSelect) {
            eventTypeSelect.value = event.event_type || '';
        } else {
            console.error('❌ editEventType element not found!');
        }
        
        // Format dates - handle both ISO strings and Date objects
        if (event.event_date) {
            const eventDate = new Date(event.event_date);
            if (!isNaN(eventDate.getTime())) {
                document.getElementById('editEventDate').value = eventDate.toISOString().split('T')[0];
                document.getElementById('editEventTime').value = eventDate.toTimeString().slice(0, 5);
            }
        }
        
        if (event.end_date) {
            const endDate = new Date(event.end_date);
            if (!isNaN(endDate.getTime())) {
                document.getElementById('editEndDate').value = endDate.toISOString().split('T')[0];
                document.getElementById('editEndTime').value = endDate.toTimeString().slice(0, 5);
            }
        }
        
        document.getElementById('editEventLocation').value = event.location || '';
        document.getElementById('editMeetingLink').value = event.meeting_link || '';
        document.getElementById('editMaxParticipants').value = event.max_participants || '';
        document.getElementById('editHeroBackgroundType').value = event.hero_background_type || 'image';
        // Set description in Quill editor
        if (window.quillInstances && window.quillInstances['editEventDescription']) {
            window.quillInstances['editEventDescription'].root.innerHTML = event.description || '';
        } else {
            // Fallback to textarea
            document.getElementById('editEventDescription').value = event.description || '';
        }
        document.getElementById('editEventActive').checked = event.is_active === true;
        document.getElementById('editEventPublished').checked = event.is_published === true;
        
        // Set minimum dates for date inputs
        this.setMinDates();
    }

    deleteEvent(eventId) {
        this.currentEventId = eventId;
        const modal = new bootstrap.Modal(document.getElementById('deleteEventModal'));
        modal.show();
    }

    handleAddEvent(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const eventData = {
            title: formData.get('title'),
            event_type: formData.get('event_type'),
            event_date: this.combineDateTime(formData.get('event_date'), formData.get('event_time')),
            end_date: this.combineDateTime(formData.get('end_date'), formData.get('end_time')),
            location: formData.get('location'),
            meeting_link: formData.get('meeting_link'),
            max_participants: formData.get('max_participants') ? parseInt(formData.get('max_participants')) : null,
            hero_background_type: formData.get('hero_background_type'),
            description: formData.get('description'),
            is_active: formData.get('is_active') === 'on',
            is_published: formData.get('is_published') === 'on'
        };

        // Validate dates
        const validationErrors = this.validateEventDates(eventData);
        if (validationErrors.length > 0) {
            window.toastManager.error(validationErrors.join('<br>'));
            return;
        }

        // Remove null/empty values, but keep required fields
        const requiredFields = ['event_type']; // Fields that should not be removed even if empty
        Object.keys(eventData).forEach(key => {
            if (eventData[key] === null || eventData[key] === '') {
                if (!requiredFields.includes(key)) {
                    delete eventData[key];
                }
            }
        });

        fetch('/api/event-schedule', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(eventData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.toastManager.success(data.message || 'Wydarzenie zostało dodane pomyślnie');
                this.loadEvents();
                bootstrap.Modal.getInstance(document.getElementById('addEventModal')).hide();
            } else {
                window.toastManager.error(data.message || 'Błąd podczas dodawania wydarzenia');
            }
        })
        .catch(error => {
            console.error('Error adding event:', error);
            window.toastManager.error('Wystąpił błąd podczas dodawania wydarzenia');
        });
    }

    handleEditEvent(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        
        const eventData = {
            title: formData.get('title'),
            event_type: formData.get('event_type'),
            event_date: this.combineDateTime(formData.get('event_date'), formData.get('event_time')),
            end_date: this.combineDateTime(formData.get('end_date'), formData.get('end_time')),
            location: formData.get('location'),
            meeting_link: formData.get('meeting_link'),
            max_participants: formData.get('max_participants') ? parseInt(formData.get('max_participants')) : null,
            hero_background_type: formData.get('hero_background_type'),
            description: formData.get('description'),
            is_active: formData.get('is_active') === 'on',
            is_published: formData.get('is_published') === 'on'
        };

        // Validate dates
        const validationErrors = this.validateEventDates(eventData);
        if (validationErrors.length > 0) {
            window.toastManager.error(validationErrors.join('<br>'));
            return;
        }

        // Remove null/empty values, but keep required fields
        const requiredFields = ['event_type']; // Fields that should not be removed even if empty
        Object.keys(eventData).forEach(key => {
            if (eventData[key] === null || eventData[key] === '') {
                if (!requiredFields.includes(key)) {
                    delete eventData[key];
                }
            }
        });

        const eventId = formData.get('id');

        fetch(`/api/event-schedule/${eventId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(eventData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.toastManager.success(data.message || 'Wydarzenie zostało zaktualizowane pomyślnie');
                this.loadEvents();
                bootstrap.Modal.getInstance(document.getElementById('editEventModal')).hide();
            } else {
                window.toastManager.error(data.message || 'Błąd podczas aktualizacji wydarzenia');
            }
        })
        .catch(error => {
            console.error('Error updating event:', error);
            window.toastManager.error('Wystąpił błąd podczas aktualizacji wydarzenia');
        });
    }

    handleDeleteEvent() {
        if (!this.currentEventId) return;

        fetch(`/api/event-schedule/${this.currentEventId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.toastManager.success(data.message || 'Wydarzenie zostało usunięte pomyślnie');
                this.loadEvents();
                bootstrap.Modal.getInstance(document.getElementById('deleteEventModal')).hide();
            } else {
                window.toastManager.error(data.message || 'Błąd podczas usuwania wydarzenia');
            }
        })
        .catch(error => {
            console.error('Error deleting event:', error);
            window.toastManager.error('Wystąpił błąd podczas usuwania wydarzenia');
        });
    }

    loadEvents() {
        // Build query parameters from filters
        const params = new URLSearchParams();
        
        const searchValue = document.getElementById('searchInput')?.value?.trim();
        const archivedFilter = document.getElementById('archivedFilter')?.value;
        const publishedFilter = document.getElementById('publishedFilter')?.value;
        
        if (searchValue) {
            params.append('search', searchValue);
        }
        
        if (archivedFilter === 'true') {
            params.append('show_archived', 'true');
        } else if (archivedFilter === 'all') {
            params.append('show_archived', 'true'); // Show all means show archived too
        }
        
        if (publishedFilter !== 'all') {
            params.append('show_published', publishedFilter);
        }
        
        // Add pagination parameters
        params.append('page', this.currentPage);
        params.append('per_page', this.currentPerPage);
        
        const url = `/api/event-schedule${params.toString() ? '?' + params.toString() : ''}`;
        
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success && data.events) {
                    this.displayEvents(data.events);
                    // Update pagination if data provided
                    if (data.pagination) {
                        this.updatePagination(data.pagination);
                    }
                    // Update active filters count after successful load
                    if (typeof updateActiveFiltersCount === 'function') {
                        updateActiveFiltersCount();
                    }
                } else {
                    console.error('API returned error:', data.message);
                    this.displayError(data.message || 'Wystąpił błąd podczas ładowania wydarzeń');
                }
            })
            .catch(error => {
                console.error('Error loading events:', error);
                this.displayError('Wystąpił błąd podczas ładowania wydarzeń');
            });
    }

    displayEvents(events) {
        const container = document.getElementById('eventsTableContainer');
        
        if (!events || events.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-calendar-alt fa-3x text-muted mb-3"></i>
                    <p class="text-muted">Brak wydarzeń w systemie</p>
                </div>
            `;
            return;
        }

        const tableHTML = `
            <div class="table-responsive">
                <table id="eventsTable" class="table admin-table bulk-delete-table" data-delete-endpoint="/api/bulk-delete/events">
                    <thead>
                        <tr>
                            <th>
                                <input type="checkbox" id="selectAll">
                            </th>
                            <th>ID</th>
                            <th>Tytuł</th>
                            <th>Typ</th>
                            <th>Data</th>
                            <th>Lokalizacja</th>
                            <th>Status</th>
                            <th>Akcje</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${events.map(event => this.createEventRow(event)).join('')}
                    </tbody>
                </table>
            </div>
        `;
        
        container.innerHTML = tableHTML;
        
        // Initialize bulk delete for the dynamically created table
        this.initializeBulkDelete();
    }
    
    initializeBulkDelete() {
        const table = document.getElementById('eventsTable');
        if (table && table.classList.contains('bulk-delete-table')) {
            const deleteEndpoint = table.dataset.deleteEndpoint;
            if (deleteEndpoint) {
                new BulkDelete('eventsTable', deleteEndpoint);
            }
        }
    }
    
    updatePagination(paginationData) {
        const paginationContainer = document.getElementById('pagination');
        if (paginationContainer) {
            if (paginationContainer.paginationInstance) {
                // Update existing pagination
                paginationContainer.paginationInstance.setData(paginationData);
            } else {
                // Check if SimplePagination class is available
                if (typeof SimplePagination === 'undefined') {
                    console.error('SimplePagination class not available. Make sure simple-paginate.js is loaded.');
                    return;
                }
                
                // Initialize pagination for the first time
                paginationContainer.paginationInstance = new SimplePagination('pagination', {
                    showInfo: true,
                    showPerPage: true,
                    perPageOptions: [5, 10, 25, 50, 100],
                    defaultPerPage: 10,
                    maxVisiblePages: 5
                });
                
                // Set callbacks
                paginationContainer.paginationInstance.setPageChangeCallback((page) => {
                    this.currentPage = page;
                    this.loadEvents();
                });
                
                paginationContainer.paginationInstance.setPerPageChangeCallback((newPage, perPage) => {
                    this.currentPage = newPage;
                    this.currentPerPage = perPage;
                    this.loadEvents();
                });
                
                paginationContainer.paginationInstance.setData(paginationData);
            }
        }
    }

    createEventRow(event) {
        const eventDate = new Date(event.event_date);
        const formattedDate = eventDate.toLocaleDateString('pl-PL', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
            timeZone: 'Europe/Warsaw'
        });

        const statusBadges = [];
        
        // Archival status (highest priority)
        if (event.is_archived) {
            statusBadges.push('<span class="badge admin-badge admin-badge-secondary"><i class="fas fa-archive me-1"></i>Archiwalne</span>');
        } else {
            // Active/Inactive status
            if (event.is_active) {
                statusBadges.push('<span class="badge admin-badge admin-badge-success"><i class="fas fa-check-circle me-1"></i>Aktywne</span>');
            } else {
                statusBadges.push('<span class="badge admin-badge admin-badge-danger"><i class="fas fa-times-circle me-1"></i>Nieaktywne</span>');
            }
        }
        
        // Published status
        if (event.is_published) {
            statusBadges.push('<span class="badge admin-badge admin-badge-primary"><i class="fas fa-eye me-1"></i>Opublikowane</span>');
        } else {
            statusBadges.push('<span class="badge admin-badge admin-badge-secondary"><i class="fas fa-eye-slash me-1"></i>Nieopublikowane</span>');
        }

        return `
            <tr data-event-id="${event.id}" data-item-id="${event.id}">
                <td>
                    <input type="checkbox" name="itemIds" value="${event.id}">
                </td>
                <td>
                    <span class="badge admin-badge admin-badge-primary">${event.id}</span>
                </td>
                <td>
                    <strong>${event.title}</strong>
                </td>
                <td>
                    <span class="badge admin-badge admin-badge-secondary">${this.getEventTypeLabel(event.event_type)}</span>
                </td>
                <td>${formattedDate}</td>
                <td>${event.location || '-'}</td>
                <td>${statusBadges.join(' ')}</td>
                <td>
                    <div class="btn-group" role="group">
                        <button class="btn btn-sm admin-btn-outline" onclick="eventsManager.editEvent(${event.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm admin-btn-danger-outline" onclick="eventsManager.deleteEvent(${event.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    getEventTypeLabel(type) {
        const types = {
            'workshop': 'Warsztat',
            'webinar': 'Webinar',
            'meeting': 'Spotkanie',
            'conference': 'Konferencja',
            'other': 'Inne'
        };
        return types[type] || (type || 'Nieokreślony');
    }

    displayError(message) {
        const container = document.getElementById('eventsTableContainer');
        container.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                <p class="text-danger">${message}</p>
                <button class="btn admin-btn" onclick="eventsManager.loadEvents()">
                    <i class="fas fa-refresh me-2"></i>Spróbuj ponownie
                </button>
            </div>
        `;
    }

    combineDateTime(date, time) {
        if (!date || !time) return null;
        return `${date}T${time}`;
    }
    
    validateEventDates(eventData) {
        const now = new Date();
        const errors = [];
        
        // Validate event date
        if (eventData.event_date) {
            const eventDate = new Date(eventData.event_date);
            if (eventDate < now) {
                errors.push('Data rozpoczęcia wydarzenia nie może być w przeszłości');
            }
        }
        
        // Validate end date
        if (eventData.end_date) {
            const endDate = new Date(eventData.end_date);
            if (endDate < now) {
                errors.push('Data zakończenia wydarzenia nie może być w przeszłości');
            }
            
            // Check if end date is after event date
            if (eventData.event_date) {
                const eventDate = new Date(eventData.event_date);
                if (endDate < eventDate) {
                    errors.push('Data zakończenia wydarzenia nie może być wcześniejsza niż data rozpoczęcia');
                }
            }
        }
        
        return errors;
    }
    
    setMinDates() {
        // Set minimum date to today for all date inputs
        const today = new Date().toISOString().split('T')[0];
        const now = new Date();
        const currentTime = now.toTimeString().slice(0, 5);
        
        const dateInputs = [
            'eventDate', 'endDate', 'editEventDate', 'editEndDate'
        ];
        
        const timeInputs = [
            'eventTime', 'endTime', 'editEventTime', 'editEndTime'
        ];
        
        dateInputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.min = today;
            }
        });
        
        // Set minimum time for time inputs
        timeInputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                // For today's date, set minimum time to current time
                const dateInput = input.id.replace('Time', 'Date').replace('edit', 'edit');
                const dateInputElement = document.getElementById(dateInput);
                if (dateInputElement && dateInputElement.value === today) {
                    input.min = currentTime;
                } else {
                    input.min = '00:00';
                }
            }
        });
    }
}

// Global functions for onclick handlers
function showAddEventModal() {
    if (window.eventsManager) {
        window.eventsManager.showAddEventModal();
    }
}

function editEvent(eventId) {
    if (window.eventsManager) {
        window.eventsManager.editEvent(eventId);
    }
}

// Filter functions
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('archivedFilter').value = 'false';
    document.getElementById('publishedFilter').value = 'all';
    
    // Hide active filters count
    const activeFiltersCount = document.getElementById('activeFiltersCount');
    if (activeFiltersCount) {
        activeFiltersCount.style.display = 'none';
    }
    
    if (window.eventsManager) {
        window.eventsManager.loadEvents();
    }
}

function applyFilters() {
    if (window.eventsManager) {
        window.eventsManager.loadEvents();
        updateActiveFiltersCount();
    }
}

function updateActiveFiltersCount() {
    const searchValue = document.getElementById('searchInput')?.value?.trim();
    const archivedFilter = document.getElementById('archivedFilter')?.value;
    const publishedFilter = document.getElementById('publishedFilter')?.value;
    
    let activeCount = 0;
    
    if (searchValue) activeCount++;
    if (archivedFilter && archivedFilter !== 'false') activeCount++;
    if (publishedFilter && publishedFilter !== 'all') activeCount++;
    
    const activeFiltersCount = document.getElementById('activeFiltersCount');
    if (activeFiltersCount) {
        if (activeCount > 0) {
            activeFiltersCount.textContent = `${activeCount} aktywny`;
            activeFiltersCount.style.display = 'inline';
        } else {
            activeFiltersCount.style.display = 'none';
        }
    }
}

// Add event listeners for filters
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const archivedFilter = document.getElementById('archivedFilter');
    const publishedFilter = document.getElementById('publishedFilter');
    const applyFiltersBtn = document.getElementById('applyFilters');
    const clearFiltersBtn = document.getElementById('clearFilters');
    
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', applyFilters);
    }
    
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearFilters);
    }
    
    // Auto-apply filters on change (optional - you can remove this if you prefer manual apply)
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                applyFilters();
            }, 500); // Debounce search
        });
    }
    
    if (archivedFilter) {
        archivedFilter.addEventListener('change', applyFilters);
    }
    
    if (publishedFilter) {
        publishedFilter.addEventListener('change', applyFilters);
    }
});

function deleteEvent(eventId) {
    if (window.eventsManager) {
        window.eventsManager.deleteEvent(eventId);
    }
}


