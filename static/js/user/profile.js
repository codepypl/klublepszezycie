/**
 * User Profile JavaScript
 * Handles profile management, meeting history, and user interactions
 */

// Global variables
let userProfileData = {};
let meetingHistory = [];

// Initialize profile page
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 Initializing user profile page...');
    
    // Load user data
    loadUserData();
    
    // Initialize meeting history filters
    initializeMeetingFilters();
    
    // Initialize form handlers
    initializeFormHandlers();
    
    console.log('✅ Profile page initialized');
});

/**
 * Load user data from the page
 */
function loadUserData() {
    // Get user data from the page (passed from Flask template)
    const userNameElement = document.getElementById('userName');
    if (userNameElement) {
        userProfileData.name = userNameElement.textContent;
    }
    
    // Get meeting history data
    const meetingItems = document.querySelectorAll('.meeting-item');
    meetingHistory = Array.from(meetingItems).map(item => ({
        element: item,
        status: item.dataset.status,
        title: item.querySelector('.meeting-title h5')?.textContent || '',
        date: item.querySelector('.meeting-date')?.textContent || ''
    }));
    
    console.log('📊 Loaded meeting history:', meetingHistory.length, 'meetings');
}

/**
 * Initialize meeting history filters
 */
function initializeMeetingFilters() {
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', filterMeetings);
        console.log('✅ Meeting filters initialized');
    }
}

/**
 * Filter meetings by status
 */
function filterMeetings() {
    const statusFilter = document.getElementById('statusFilter');
    const selectedStatus = statusFilter ? statusFilter.value : '';
    const meetingItems = document.querySelectorAll('.meeting-item');
    
    let visibleCount = 0;
    
    meetingItems.forEach(item => {
        const itemStatus = item.dataset.status;
        const shouldShow = !selectedStatus || itemStatus === selectedStatus;
        
        if (shouldShow) {
            item.style.display = 'block';
            item.classList.add('fade-in');
            visibleCount++;
        } else {
            item.style.display = 'none';
            item.classList.remove('fade-in');
        }
    });
    
    // Update stats if needed
    updateFilteredStats(selectedStatus, visibleCount);
    
    console.log(`🔍 Filtered meetings: ${visibleCount} visible (status: ${selectedStatus || 'all'})`);
}

/**
 * Update statistics based on filtered results
 */
function updateFilteredStats(selectedStatus, visibleCount) {
    // You can add logic here to update stats display based on filter
    const statsCards = document.querySelectorAll('.stats-card');
    statsCards.forEach(card => {
        if (selectedStatus) {
            card.classList.add('filtered');
        } else {
            card.classList.remove('filtered');
        }
    });
}

/**
 * Copy meeting link to clipboard
 */
function copyMeetingLink(link) {
    if (!link) {
        showNotification('Brak linku do spotkania', 'warning');
        return;
    }
    
    // Create temporary textarea to copy text
    const textarea = document.createElement('textarea');
    textarea.value = link;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    
    try {
        textarea.select();
        document.execCommand('copy');
        showNotification('Link skopiowany do schowka!', 'success');
        console.log('📋 Meeting link copied:', link);
    } catch (err) {
        console.error('❌ Failed to copy link:', err);
        showNotification('Nie udało się skopiować linku', 'error');
    } finally {
        document.body.removeChild(textarea);
    }
}

/**
 * Show notification to user
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getNotificationIcon(type)} me-2"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Hide and remove notification
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
    
    console.log(`📢 Notification (${type}):`, message);
}

/**
 * Get icon for notification type
 */
function getNotificationIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * Initialize form handlers
 */
function initializeFormHandlers() {
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', handleProfileSubmit);
        console.log('✅ Profile form handler initialized');
    }
    
    // Add reset form handler
    const resetButton = document.querySelector('button[onclick="resetForm()"]');
    if (resetButton) {
        resetButton.addEventListener('click', resetProfileForm);
    }
}

/**
 * Handle profile form submission
 */
async function handleProfileSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    
    // Show loading state
    setLoadingState(submitButton, true);
    
    try {
        // Convert FormData to JSON
        const data = {};
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        const response = await fetch('/api/profile', {
            method: 'PUT',
            body: JSON.stringify(data),
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Profil został zaktualizowany pomyślnie!', 'success');
            // Reload page to show updated data
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            showNotification(result.error || 'Wystąpił błąd podczas aktualizacji profilu', 'error');
        }
        
    } catch (error) {
        console.error('❌ Profile update error:', error);
        showNotification('Wystąpił błąd podczas aktualizacji profilu', 'error');
    } finally {
        setLoadingState(submitButton, false);
    }
}

/**
 * Reset profile form
 */
function resetProfileForm() {
    const form = document.getElementById('profileForm');
    if (form) {
        form.reset();
        showNotification('Formularz został zresetowany', 'info');
        console.log('🔄 Profile form reset');
    }
}

/**
 * Set loading state for button
 */
function setLoadingState(button, isLoading) {
    if (!button) return;
    
    if (isLoading) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Zapisywanie...';
        button.classList.add('loading');
    } else {
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-save me-1"></i>Zapisz zmiany';
        button.classList.remove('loading');
    }
}

/**
 * Expand/collapse meeting details
 */
function toggleMeetingDetails(meetingId) {
    const meetingItem = document.getElementById(`meeting-${meetingId}`);
    if (meetingItem) {
        const details = meetingItem.querySelector('.meeting-details');
        const toggleIcon = meetingItem.querySelector('.toggle-icon');
        
        if (details && toggleIcon) {
            const isExpanded = details.style.display !== 'none';
            details.style.display = isExpanded ? 'none' : 'block';
            toggleIcon.className = isExpanded ? 'fas fa-chevron-down' : 'fas fa-chevron-up';
        }
    }
}

/**
 * Search meetings by title or date
 */
function searchMeetings() {
    const searchInput = document.getElementById('meetingSearch');
    if (!searchInput) return;
    
    const searchTerm = searchInput.value.toLowerCase();
    const meetingItems = document.querySelectorAll('.meeting-item');
    
    let visibleCount = 0;
    
    meetingItems.forEach(item => {
        const title = item.querySelector('.meeting-title h5')?.textContent.toLowerCase() || '';
        const date = item.querySelector('.meeting-date')?.textContent.toLowerCase() || '';
        
        const matchesSearch = title.includes(searchTerm) || date.includes(searchTerm);
        
        if (matchesSearch) {
            item.style.display = 'block';
            item.classList.add('fade-in');
            visibleCount++;
        } else {
            item.style.display = 'none';
            item.classList.remove('fade-in');
        }
    });
    
    console.log(`🔍 Search results: ${visibleCount} meetings found for "${searchTerm}"`);
}

/**
 * Export meeting history (future feature)
 */
function exportMeetingHistory() {
    showNotification('Funkcja eksportu będzie dostępna wkrótce', 'info');
    console.log('📤 Export meeting history requested');
}

/**
 * Toggle club membership
 */
async function toggleClubMembership() {
    const switchElement = document.getElementById('clubMemberSwitch');
    if (!switchElement) return;
    
    // Disable switch during request
    switchElement.disabled = true;
    const originalChecked = switchElement.checked;
    
    try {
        const data = {
            club_member: switchElement.checked
        };
        
        const response = await fetch('/api/profile', {
            method: 'PUT',
            body: JSON.stringify(data),
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            if (switchElement.checked) {
                showNotification('Pomyślnie dołączyłeś do klubu!', 'success');
            } else {
                showNotification('Opuszczono klub', 'info');
            }
            // Reload page to show updated status
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            // Revert switch state on error
            switchElement.checked = originalChecked;
            showNotification(result.error || 'Wystąpił błąd podczas zmiany statusu klubu', 'error');
        }
        
    } catch (error) {
        console.error('❌ Club membership error:', error);
        // Revert switch state on error
        switchElement.checked = originalChecked;
        showNotification('Wystąpił błąd podczas zmiany statusu klubu', 'error');
    } finally {
        switchElement.disabled = false;
    }
}

/**
 * Set loading state for button with custom text
 */
function setLoadingState(button, isLoading, loadingText = 'Ładowanie...') {
    if (!button) return;
    
    if (isLoading) {
        button.disabled = true;
        button.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>${loadingText}`;
        button.classList.add('loading');
    } else {
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-users me-2"></i>Dołącz';
        button.classList.remove('loading');
    }
}

/**
 * Show delete account modal
 */
function showDeleteAccountModal() {
    const modal = new bootstrap.Modal(document.getElementById('deleteAccountModal'));
    modal.show();
    console.log('🗑️ Delete account modal opened');
}

/**
 * Delete user account
 */
async function deleteAccount() {
    const password = document.getElementById('deletePassword').value;
    const confirmCheckbox = document.getElementById('confirmDelete');
    const deleteButton = document.querySelector('#deleteAccountModal .btn-danger');
    
    if (!password) {
        showNotification('Wprowadź swoje hasło', 'error');
        return;
    }
    
    if (!confirmCheckbox.checked) {
        showNotification('Potwierdź chęć usunięcia konta', 'error');
        return;
    }
    
    // Show loading state
    setLoadingState(deleteButton, true, 'Usuwanie...');
    
    try {
        const data = {
            password: password,
            confirm_delete: true
        };
        
        const response = await fetch('/api/users/delete-account', {
            method: 'DELETE',
            body: JSON.stringify(data),
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Konto zostało usunięte pomyślnie', 'success');
            // Redirect to home page after successful deletion
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        } else {
            showNotification(result.error || 'Wystąpił błąd podczas usuwania konta', 'error');
        }
        
    } catch (error) {
        console.error('❌ Delete account error:', error);
        showNotification('Wystąpił błąd podczas usuwania konta', 'error');
    } finally {
        setLoadingState(deleteButton, false, 'Usuń konto');
    }
}

/**
 * Global functions for HTML onclick handlers
 */
window.filterMeetings = filterMeetings;
window.copyMeetingLink = copyMeetingLink;
window.resetForm = resetProfileForm;
window.toggleMeetingDetails = toggleMeetingDetails;
window.searchMeetings = searchMeetings;
window.exportMeetingHistory = exportMeetingHistory;
window.toggleClubMembership = toggleClubMembership;
window.showDeleteAccountModal = showDeleteAccountModal;
window.deleteAccount = deleteAccount;
