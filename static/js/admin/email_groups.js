// Admin Email Groups JavaScript for Lepsze Życie Club

// Global variables
let currentPage = 1;
let currentPerPage = 10;
let currentGroupId = null;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadGroups();
    
    // Check for viewMembers parameter
    const urlParams = new URLSearchParams(window.location.search);
    const viewMembersId = urlParams.get('viewMembers');
    if (viewMembersId) {
        // Wait a bit for page to load, then open group members modal
        setTimeout(() => {
            viewGroupMembers(parseInt(viewMembersId));
        }, 1000);
    }
    
    // Set up pagination handlers for auto-initialization
    window.paginationHandlers = {
        onPageChange: (page) => {
            currentPage = page;
            loadGroups();
        },
        onPerPageChange: (newPage, perPage) => {
            currentPerPage = perPage;
            currentPage = newPage; // Use the page passed by pagination
            loadGroups();
        }
    };
    
    // Add event listener for modal close to refresh groups list
    const groupMembersModal = document.getElementById('groupMembersModal');
    if (groupMembersModal) {
        groupMembersModal.addEventListener('hidden.bs.modal', function() {
            loadGroups(); // Odśwież listę grup po zamknięciu modala członków
        });
    }
    
    // Add event listener for main group modal close
    const groupModal = document.getElementById('groupModal');
    if (groupModal) {
        groupModal.addEventListener('hidden.bs.modal', function() {
            loadGroups(); // Odśwież listę grup po zamknięciu modala grupy
        });
    }
    
    // Initialize CRUD Refresh Manager for email groups
    if (typeof CRUDRefreshManager !== 'undefined' && window.crudRefreshManager) {
        window.crudRefreshManager.init(loadGroups);
        console.log('CRUD Refresh Manager initialized for email groups');
    }
});


// Load groups
function loadGroups() {
    // Check if we're on the groups page
    const tbody = document.getElementById('groupsTableBody');
    if (!tbody) {
        console.log('Not on groups page - skipping loadGroups');
        return;
    }
    
    const params = new URLSearchParams({
        page: currentPage,
        per_page: currentPerPage
    });
    
    fetch(`/api/email/groups?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayGroups(data.groups);
                if (data.pagination) {
                    updatePagination(data.pagination);
                }
            } else {
                toastManager.error('Błąd ładowania grup: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error loading groups:', error);
            toastManager.error('Błąd ładowania grup');
        });
}

// Update pagination
function updatePagination(paginationData) {
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
                currentPage = page;
                loadGroups();
            });
            
            paginationContainer.paginationInstance.setPerPageChangeCallback((newPage, perPage) => {
                currentPage = newPage;
                currentPerPage = perPage;
                loadGroups();
            });
            
            paginationContainer.paginationInstance.setData(paginationData);
        }
    }
}

// Display groups
function displayGroups(groups) {
    const tbody = document.getElementById('groupsTableBody');
    
    // Check if we're on the groups page
    if (!tbody) {
        console.log('groupsTableBody not found - not on groups page');
        return;
    }
    
    tbody.innerHTML = '';
    
    if (groups.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">Brak grup</td></tr>';
        return;
    }
    
    groups.forEach(group => {
        const row = document.createElement('tr');
        
        // Ukryj checkbox i przyciski dla domyślnych grup i grup wydarzeń
        const isSystemGroup = group.is_default || group.group_type === 'event_based';
        const checkboxHtml = isSystemGroup ? 
            '<input type="checkbox" name="itemIds" value="' + group.id + '" disabled title="Nie można usuwać grup systemowych">' :
            '<input type="checkbox" name="itemIds" value="' + group.id + '">';
        
        const actionButtonsHtml = isSystemGroup ? 
            '<div class="btn-group" role="group">' +
                '<button class="btn btn-sm admin-btn-outline" disabled title="Grupa zarządzana automatycznie przez system"><i class="fas fa-cog"></i></button>' +
                (group.group_type === 'event_based' ? 
                    '<button class="btn btn-sm admin-btn-info" onclick="viewGroupMembers(' + group.id + ')" title="Zarządzaj członkami grupy wydarzenia"><i class="fas fa-users"></i></button>' :
                    '<button class="btn btn-sm admin-btn-outline" disabled title="Członkowie zarządzani automatycznie"><i class="fas fa-users"></i></button>'
                ) +
                '<button class="btn btn-sm admin-btn-outline" disabled title="Nie można usuwać grup systemowych"><i class="fas fa-lock"></i></button>' +
            '</div>' :
            '<div class="btn-group" role="group">' +
                '<button class="btn btn-sm admin-btn-outline" onclick="editGroup(' + group.id + ')" title="Edytuj grupę"><i class="fas fa-edit"></i></button>' +
                '<button class="btn btn-sm admin-btn-info" onclick="viewGroupMembers(' + group.id + ')" title="Zarządzaj członkami"><i class="fas fa-users"></i></button>' +
                '<button class="btn btn-sm admin-btn-danger-outline" onclick="deleteGroup(' + group.id + ')" title="Usuń grupę"><i class="fas fa-trash"></i></button>' +
            '</div>';
        
        row.innerHTML = `
            <td>${checkboxHtml}</td>
            <td><span class="badge admin-badge admin-badge-primary">${group.id}</span></td>
            <td style="word-wrap: break-word; word-break: break-word; max-width: 200px;">${group.name} ${group.is_default ? '<span class="admin-badge admin-badge-info ms-1">Systemowa</span>' : ''} ${group.group_type === 'event_based' ? '<span class="admin-badge admin-badge-warning ms-1">Wydarzenie</span>' : ''}</td>
            <td>
                ${group.template_id ? 
                    `<a href="#" onclick="editTemplate(${group.template_id})" 
                       data-bs-toggle="tooltip" 
                       data-bs-placement="top" 
                       title="${group.template_name || 'Szablon e-mail'}">
                        <span class="badge admin-badge admin-badge-primary">${group.template_id}</span>
                     </a>` : 
                    `<span class="text-muted">${group.group_type}</span>`
                }
            </td>
            <td>${group.member_count}</td>
            <td><span class="admin-badge admin-badge-${group.is_active ? 'success' : 'secondary'}">${group.is_active ? 'Aktywna' : 'Nieaktywna'}</span></td>
            <td>${new Date(group.created_at).toLocaleDateString('pl-PL', {hour12: false})}</td>
            <td>${actionButtonsHtml}</td>
        `;
        
        tbody.appendChild(row);
    });
    
    // Initialize tooltips for template IDs
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize bulk delete after loading groups
    initializeBulkDelete();
}

// Initialize bulk delete functionality
function initializeBulkDelete() {
    const table = document.getElementById('groupsTable');
    if (table) {
        const deleteEndpoint = table.dataset.deleteEndpoint;
        if (deleteEndpoint) {
            // Remove existing bulk delete instance if any
            if (window.groupsBulkDelete) {
                window.groupsBulkDelete = null;
            }
            // Create new bulk delete instance
            window.groupsBulkDelete = new BulkDelete('groupsTable', deleteEndpoint);
        }
    }
}

// Show group modal
function showGroupModal() {
    document.getElementById('groupForm').reset();
    document.getElementById('group_id').value = '';
    const modal = new bootstrap.Modal(document.getElementById('groupModal'));
    modal.show();
}

// Synchronizacja grup systemowych
function syncSystemGroups() {
    if (confirm('Czy na pewno chcesz zsynchronizować grupy systemowe?\n\nTa operacja zaktualizuje listę członków grup "Wszyscy użytkownicy" i "Członkowie klubu" na podstawie aktualnych danych użytkowników.')) {
        fetch('/api/email/groups/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.toastManager.show('Grupy systemowe zostały zsynchronizowane', 'success');
                loadGroups(); // Odśwież listę grup
            } else {
                window.toastManager.show(data.error || 'Błąd synchronizacji', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            window.toastManager.show('Wystąpił błąd podczas synchronizacji grup', 'error');
        });
    }
}

function syncEventGroups() {
    if (confirm('Czy na pewno chcesz zsynchronizować grupy wydarzeń?\n\nTa operacja zaktualizuje listę członków wszystkich grup wydarzeń na podstawie aktualnych rejestracji.')) {
        fetch('/api/email/groups/sync-events', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.toastManager.show('Grupy wydarzeń zostały zsynchronizowane', 'success');
                loadGroups(); // Odśwież listę grup
            } else {
                window.toastManager.show(data.error || 'Błąd synchronizacji', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            window.toastManager.show('Wystąpił błąd podczas synchronizacji grup wydarzeń', 'error');
        });
    }
}

// Make functions globally available
window.showGroupModal = showGroupModal;
window.saveGroup = saveGroup;
window.editGroup = editGroup;
window.deleteGroup = deleteGroup;
window.syncSystemGroups = syncSystemGroups;
window.syncEventGroups = syncEventGroups;
window.viewGroupMembers = viewGroupMembers;
window.toggleGroupTypeFields = toggleGroupTypeFields;
window.updateMemberCountPreview = updateMemberCountPreview;
window.loadGroupMembersForEdit = loadGroupMembersForEdit;

// Save group
function saveGroup() {
    const form = document.getElementById('groupForm');
    const formData = new FormData(form);
    
    const data = {
        name: formData.get('group_name'),
        description: formData.get('group_description'),
        group_type: formData.get('group_type'),
        is_active: formData.get('group_is_active') === 'on'
    };
    
    // Add specific data based on group type
    const groupType = formData.get('group_type');
    if (groupType === 'event_based') {
        const selectedEvent = formData.get('selected_event');
        if (!selectedEvent) {
            toastManager.error('Proszę wybrać wydarzenie');
            return;
        }
        data.event_id = selectedEvent;
    } else if (groupType === 'manual') {
        const selectedUsers = [];
        const checkboxes = document.querySelectorAll('input[name="selected_users"]:checked');
        checkboxes.forEach(checkbox => {
            selectedUsers.push(parseInt(checkbox.value));
        });
        data.user_ids = selectedUsers;
    }
    
    const groupId = document.getElementById('group_id').value;
    const method = groupId ? 'PUT' : 'POST';
    const url = groupId ? `/api/email/groups/${groupId}` : '/api/email/groups';
    
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
            toastManager.success('Grupa zapisana pomyślnie!');
            bootstrap.Modal.getInstance(document.getElementById('groupModal')).hide();
            loadGroups();
        } else {
            toastManager.error('Błąd zapisywania grupy: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error saving group:', error);
        toastManager.error('Błąd zapisywania grupy');
    });
}

// Edit group
function editGroup(groupId) {
    // Exception for group ID 19 - do not open for editing
    if (groupId === 19) {
        console.log('Group ID 19 is excluded from editing');
        toastManager.warning('Ta grupa nie może być edytowana');
        return;
    }
    
    // Check if we're on the groups page
    const groupForm = document.getElementById('groupForm');
    if (!groupForm) {
        console.log('Not on groups page - opening new window for group members management');
        // If not on groups page, open new window and show group members modal
        const newWindow = window.open(`/admin/email-groups?viewMembers=${groupId}`, '_blank');
        return;
    }
    
    fetch(`/api/email/groups/${groupId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const group = data.group;
                
                // Block editing of system groups
                if (group.group_type === 'event_based') {
                    toastManager.error('Nie można edytować grup wydarzeń - są zarządzane automatycznie przez system');
                    return;
                }
                
                // Check if form elements exist before setting values
                const groupIdField = document.getElementById('group_id');
                const groupNameField = document.getElementById('group_name');
                const groupDescField = document.getElementById('group_description');
                const groupTypeField = document.getElementById('group_type');
                const groupActiveField = document.getElementById('group_is_active');
                
                if (groupIdField) groupIdField.value = group.id;
                if (groupNameField) groupNameField.value = group.name;
                if (groupDescField) groupDescField.value = group.description || '';
                if (groupTypeField) groupTypeField.value = group.group_type;
                if (groupActiveField) groupActiveField.checked = group.is_active;
                
                // Load group type specific fields
                if (typeof toggleGroupTypeFields === 'function') {
                    toggleGroupTypeFields();
                }
                
                // If it's a manual group, load current members and pre-select them
                if (group.group_type === 'manual' && typeof loadGroupMembersForEdit === 'function') {
                    loadGroupMembersForEdit(groupId);
                }
                
                // If it's an event-based group, set the selected event
                if (group.group_type === 'event_based' && group.criteria) {
                    try {
                        const criteria = JSON.parse(group.criteria);
                        const eventId = criteria.event_id;
                        if (eventId) {
                            // Wait for events to load, then set the selected event
                            setTimeout(() => {
                                const eventSelect = document.getElementById('selected_event');
                                if (eventSelect) {
                                    eventSelect.value = eventId;
                                }
                            }, 500); // Give time for loadEvents() to complete
                        }
                    } catch (e) {
                        console.error('Error parsing group criteria:', e);
                    }
                }
                
                const groupModal = document.getElementById('groupModal');
                if (groupModal) {
                    const modal = new bootstrap.Modal(groupModal);
                    modal.show();
                }
            } else {
                toastManager.error('Błąd ładowania grupy: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error loading group:', error);
            toastManager.error('Błąd ładowania grupy');
        });
}

// View group members
function viewGroupMembers(groupId) {
    currentGroupId = groupId;
    
    // Get group info to show in modal title and get event_id for filtering
    fetch(`/api/email/groups/${groupId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const group = data.group;
                const modalTitle = document.getElementById('groupMembersModalLabel');
                if (group.group_type === 'event_based') {
                    modalTitle.textContent = `Członkowie grupy wydarzenia: ${group.name}`;
                    
                    // Get event_id from group criteria for filtering users
                    let eventId = null;
                    if (group.criteria) {
                        try {
                            const criteria = JSON.parse(group.criteria);
                            eventId = criteria.event_id;
                        } catch (e) {
                            console.error('Error parsing group criteria:', e);
                        }
                    }
                    
                    // Store event_id globally for use in loadAvailableUsers
                    window.currentEventId = eventId;
                } else {
                    modalTitle.textContent = `Członkowie grupy: ${group.name}`;
                    window.currentEventId = null;
                }
                
                // Load users and members after setting event_id
                loadGroupMembers();
                loadAvailableUsers();
            }
        })
        .catch(error => {
            console.error('Error loading group info:', error);
        });
    
    const modal = new bootstrap.Modal(document.getElementById('groupMembersModal'));
    modal.show();
}

// Load group members
function loadGroupMembers() {
    if (!currentGroupId) return;
    
    fetch(`/api/email/groups/${currentGroupId}/members`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayGroupMembers(data.members);
            } else {
                toastManager.error('Błąd ładowania członków: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error loading group members:', error);
            toastManager.error('Błąd ładowania członków');
        });
}

// Display group members
function displayGroupMembers(members) {
    const container = document.getElementById('groupMembers');
    container.innerHTML = '';
    
    if (members.length === 0) {
        container.innerHTML = '<div class="text-center text-muted">Brak członków</div>';
        return;
    }
    
    members.forEach(member => {
        const item = document.createElement('div');
        item.className = 'list-group-item d-flex justify-content-between align-items-center';
        item.innerHTML = `
            <div>
                <strong>${member.user_name}</strong><br>
                <small class="text-muted">${member.email}</small>
            </div>
            <button class="btn btn-sm admin-btn-danger" onclick="removeGroupMember(${member.id})">
                <i class="fas fa-times"></i>
            </button>
        `;
        container.appendChild(item);
    });
}

// Load available users
function loadAvailableUsers(searchTerm = '') {
    const params = new URLSearchParams();
    if (searchTerm) {
        params.append('search', searchTerm);
    }
    
    // Check if this is an event-based group and we have event_id
    let apiUrl = '/api/users';
    if (window.currentEventId) {
        apiUrl = `/api/users/for-event-group/${window.currentEventId}`;
    }
    
    fetch(`${apiUrl}?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayAvailableUsers(data.users);
            } else {
                toastManager.error('Błąd ładowania użytkowników: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error loading users:', error);
            toastManager.error('Błąd ładowania użytkowników');
        });
}

// Display available users
function displayAvailableUsers(users) {
    const container = document.getElementById('availableUsers');
    container.innerHTML = '';
    
    if (users.length === 0) {
        container.innerHTML = '<div class="text-center text-muted">Brak użytkowników</div>';
        return;
    }
    
    users.forEach(user => {
        const item = document.createElement('div');
        item.className = 'list-group-item d-flex justify-content-between align-items-center';
        
        // Show event information if available
        let eventInfo = '';
        if (user.event_id && user.account_type === 'event_registration') {
            eventInfo = `<br><small class="text-info">Zarejestrowany na wydarzenie ID: ${user.event_id}</small>`;
        }
        
        item.innerHTML = `
            <div>
                <strong>${user.first_name}</strong><br>
                <small class="text-muted">${user.email}</small>${eventInfo}
            </div>
            <button class="btn btn-sm admin-btn" onclick="addGroupMember(${user.id})">
                <i class="fas fa-plus"></i>
            </button>
        `;
        container.appendChild(item);
    });
}

// Add group member
function addGroupMember(userId) {
    if (!currentGroupId) return;
    
    fetch(`/api/email/groups/${currentGroupId}/members`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: userId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toastManager.success('Członek dodany!');
            loadGroupMembers();
            loadAvailableUsers(document.getElementById('searchUsers').value);
            loadGroups(); // Odśwież listę grup aby zaktualizować licznik członków
            
            // Wywołaj globalne odświeżenie
            window.refreshAfterCRUD();
        } else {
            toastManager.error('Błąd dodawania członka: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error adding group member:', error);
        toastManager.error('Błąd dodawania członka');
    });
}

// Remove group member
function removeGroupMember(memberId) {
    window.deleteConfirmation.showSingleDelete(
        'członka z grupy',
        () => {
            fetch(`/api/email/groups/members/${memberId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    toastManager.success('Członek usunięty!');
                    loadGroupMembers();
                    loadAvailableUsers(document.getElementById('searchUsers').value);
                    
                    // Wywołaj globalne odświeżenie
                    if (typeof window.refreshAfterCRUD === 'function') {
                        window.refreshAfterCRUD();
                    } else {
                        console.warn('window.refreshAfterCRUD is not available');
                    }
                    loadGroups(); // Odśwież listę grup aby zaktualizować licznik członków
                } else {
                    toastManager.error('Błąd usuwania członka: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error removing group member:', error);
                toastManager.error('Błąd usuwania członka');
            });
        }
    );
}

// Delete group
function deleteGroup(groupId) {
    window.deleteConfirmation.showSingleDelete(
        'grupę',
        () => {
            fetch(`/api/email/groups/${groupId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    toastManager.success('Grupa usunięta!');
                    loadGroups();
                    
                    // Wywołaj globalne odświeżenie
                    if (typeof window.refreshAfterCRUD === 'function') {
                        window.refreshAfterCRUD();
                    } else {
                        console.warn('window.refreshAfterCRUD is not available');
                    }
                } else {
                    toastManager.error('Błąd usuwania: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error deleting group:', error);
                toastManager.error('Błąd usuwania');
            });
        },
        'grupę'
    );
}

// Toggle group type fields
function toggleGroupTypeFields() {
    const groupType = document.getElementById('group_type').value;
    const eventSelection = document.getElementById('event_selection');
    const userSelection = document.getElementById('user_selection');
    
    // Hide all fields first
    eventSelection.style.display = 'none';
    userSelection.style.display = 'none';
    
    // Show relevant fields based on group type
    if (groupType === 'event_based') {
        eventSelection.style.display = 'block';
        loadEvents();
    } else if (groupType === 'manual') {
        userSelection.style.display = 'block';
        loadUsersForSelection();
    }
}

// Load events for event selection
function loadEvents() {
    fetch('/api/event-schedule')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('selected_event');
            select.innerHTML = '<option value="">Wybierz wydarzenie</option>';
            
            // Check if data has events array
            const events = data.events || data;
            
            if (Array.isArray(events)) {
                events.forEach(event => {
                    const option = document.createElement('option');
                    option.value = event.id;
                    option.textContent = event.title;
                    select.appendChild(option);
                });
            } else {
                console.error('Events data is not an array:', events);
                toastManager.error('Nieprawidłowy format danych wydarzeń');
            }
        })
        .catch(error => {
            console.error('Error loading events:', error);
            toastManager.error('Błąd ładowania wydarzeń');
        });
}

// Load users for manual selection
function loadUsersForSelection() {
    fetch('/api/users')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayUsersForSelection(data.users);
            } else {
                toastManager.error('Błąd ładowania użytkowników: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error loading users:', error);
            toastManager.error('Błąd ładowania użytkowników');
        });
}

// Display users for manual selection
function displayUsersForSelection(users) {
    const container = document.getElementById('users_list');
    container.innerHTML = '';
    
    if (users.length === 0) {
        container.innerHTML = '<div class="text-center text-muted">Brak użytkowników</div>';
        return;
    }
    
    users.forEach(user => {
        const item = document.createElement('div');
        item.className = 'form-check';
        item.innerHTML = `
            <input class="form-check-input" type="checkbox" value="${user.id}" id="user_${user.id}" name="selected_users" onchange="updateMemberCountPreview()">
            <label class="form-check-label" for="user_${user.id}">
                <strong>${user.first_name}</strong> - ${user.email}
            </label>
        `;
        container.appendChild(item);
    });
    
    // Add member count preview
    const previewDiv = document.createElement('div');
    previewDiv.id = 'memberCountPreview';
    previewDiv.className = 'mt-3 p-2 bg-light rounded';
    previewDiv.innerHTML = '<strong>Wybrano: <span id="selectedCount">0</span> użytkowników</strong>';
    container.appendChild(previewDiv);
    
    // Update initial count
    updateMemberCountPreview();
}

// Update member count preview
function updateMemberCountPreview() {
    const checkboxes = document.querySelectorAll('input[name="selected_users"]:checked');
    const countElement = document.getElementById('selectedCount');
    if (countElement) {
        countElement.textContent = checkboxes.length;
    }
}

// Edit template function
function editTemplate(templateId) {
    // Sprawdź czy jesteśmy na stronie szablonów
    if (window.location.pathname.includes('email-templates')) {
        // Jeśli jesteśmy na stronie szablonów, wywołaj funkcję editTemplate
        if (typeof window.editTemplate === 'function') {
            window.editTemplate(templateId);
        } else {
            // Fallback - przekieruj do strony szablonów
            window.location.href = `/admin/email-templates?edit=${templateId}`;
        }
    } else {
        // Jeśli nie jesteśmy na stronie szablonów, otwórz modal w nowym oknie
        const newWindow = window.open('/admin/email-templates', '_blank');
        
        // Poczekaj na załadowanie strony i otwórz modal
        newWindow.addEventListener('load', function() {
            setTimeout(() => {
                if (typeof newWindow.editTemplate === 'function') {
                    newWindow.editTemplate(templateId);
                } else {
                    // Fallback - przekieruj z parametrem
                    newWindow.location.href = `/admin/email-templates?edit=${templateId}`;
                }
            }, 1000);
        });
    }
}

// Edit category function
function editCategory(categoryId) {
    // Sprawdź czy jesteśmy na stronie kategorii
    if (window.location.pathname.includes('blog/admin/categories')) {
        // Jeśli jesteśmy na stronie kategorii, wywołaj funkcję editCategory
        if (typeof window.editCategory === 'function') {
            window.editCategory(categoryId);
        } else {
            // Fallback - przekieruj do strony kategorii
            window.location.href = `/blog/admin/categories?edit=${categoryId}`;
        }
    } else {
        // Jeśli nie jesteśmy na stronie kategorii, otwórz modal w nowym oknie
        const newWindow = window.open('/blog/admin/categories', '_blank');
        
        // Poczekaj na załadowanie strony i otwórz modal
        newWindow.addEventListener('load', function() {
            setTimeout(() => {
                if (typeof newWindow.editCategory === 'function') {
                    newWindow.editCategory(categoryId);
                } else {
                    // Fallback - przekieruj z parametrem
                    newWindow.location.href = `/blog/admin/categories?edit=${categoryId}`;
                }
            }, 1000);
        });
    }
}

// Load group members for editing (pre-select checkboxes)
function loadGroupMembersForEdit(groupId) {
    fetch(`/api/email/groups/${groupId}/members`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Wait a bit for checkboxes to be rendered
                setTimeout(() => {
                    // Clear all checkboxes first
                    const checkboxes = document.querySelectorAll('input[name="selected_users"]');
                    checkboxes.forEach(checkbox => {
                        checkbox.checked = false;
                    });
                    
                    // Check boxes for current members
                    data.members.forEach(member => {
                        const checkbox = document.getElementById(`user_${member.user_id}`);
                        if (checkbox) {
                            checkbox.checked = true;
                        }
                    });
                    
                    // Update count preview
                    updateMemberCountPreview();
                }, 100);
            } else {
                console.log('Nie można załadować członków grupy:', data.error);
            }
        })
        .catch(error => {
            console.error('Error loading group members for edit:', error);
        });
}

// Search users
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchUsers');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            loadAvailableUsers(this.value);
        });
    }
    
    // Add event listener for user search in group creation
    const searchUsersInput = document.getElementById('search_users');
    if (searchUsersInput) {
        searchUsersInput.addEventListener('input', function() {
            searchUsersForSelection(this.value);
        });
    }
});

// Search users for selection
function searchUsersForSelection(searchTerm) {
    const params = new URLSearchParams();
    if (searchTerm) {
        params.append('search', searchTerm);
    }
    
    fetch(`/api/users?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayUsersForSelection(data.users);
            } else {
                toastManager.error('Błąd wyszukiwania użytkowników: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error searching users:', error);
            toastManager.error('Błąd wyszukiwania użytkowników');
        });
}
