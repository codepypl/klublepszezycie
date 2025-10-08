// CRUD Operations Refresh Manager - Global Admin System
// This file provides automatic screen refresh functionality for all admin pages

class CRUDRefreshManager {
    constructor() {
        this.pendingRefresh = false;
        this.refreshCallbacks = [];
        this.pageRefreshCallback = null;
        this.isInitialized = false;
    }
    
    // Initialize the refresh manager for a specific page
    init(pageRefreshCallback) {
        this.pageRefreshCallback = pageRefreshCallback;
        this.isInitialized = true;
        
        // Register the main page refresh callback
        if (typeof pageRefreshCallback === 'function') {
            this.registerCallback(pageRefreshCallback);
        }
        
        console.log('CRUD Refresh Manager initialized for:', pageRefreshCallback.name || 'anonymous function');
    }
    
    // Register a callback to be called after CRUD operations
    registerCallback(callback) {
        if (typeof callback === 'function') {
            this.refreshCallbacks.push(callback);
        }
    }
    
    // Unregister a callback
    unregisterCallback(callback) {
        const index = this.refreshCallbacks.indexOf(callback);
        if (index > -1) {
            this.refreshCallbacks.splice(index, 1);
        }
    }
    
    // Mark that a refresh is needed (for modal operations)
    markPendingRefresh() {
        this.pendingRefresh = true;
        console.log('CRUD Refresh Manager: Pending refresh marked');
    }
    
    // Execute refresh immediately (for non-modal operations)
    executeRefresh() {
        if (!this.isInitialized) {
            console.warn('CRUD Refresh Manager: Not initialized');
            return;
        }
        
        console.log('CRUD Refresh Manager: Executing refresh...');
        this.refreshCallbacks.forEach(callback => {
            try {
                callback();
            } catch (error) {
                console.error('CRUD Refresh Manager: Error in refresh callback:', error);
            }
        });
        this.pendingRefresh = false;
    }
    
    // Execute refresh if pending (for modal operations)
    executePendingRefresh() {
        if (this.pendingRefresh) {
            console.log('CRUD Refresh Manager: Executing pending refresh...');
            this.executeRefresh();
        }
    }
    
    // Get status information
    getStatus() {
        return {
            isInitialized: this.isInitialized,
            pendingRefresh: this.pendingRefresh,
            callbacksCount: this.refreshCallbacks.length,
            hasPageCallback: this.pageRefreshCallback !== null
        };
    }
    
    // Reset the manager
    reset() {
        this.pendingRefresh = false;
        this.refreshCallbacks = [];
        this.pageRefreshCallback = null;
        this.isInitialized = false;
    }
}

// Create global CRUD refresh manager instance
window.crudRefreshManager = new CRUDRefreshManager();

// Global refresh function for backward compatibility
window.refreshAfterCRUD = function() {
    window.crudRefreshManager.executeRefresh();
};

// Auto-initialize common admin page patterns
document.addEventListener('DOMContentLoaded', function() {
    // Try to auto-detect common admin page refresh functions
    const commonRefreshFunctions = [
        'loadUsers', 'loadEvents', 'loadCampaigns', 'loadTemplates', 
        'loadGroups', 'loadPosts', 'loadCategories', 'loadTags',
        'loadEmailQueue', 'loadSettings', 'loadDashboard'
    ];
    
    commonRefreshFunctions.forEach(funcName => {
        if (typeof window[funcName] === 'function') {
            console.log(`CRUD Refresh Manager: Auto-detected function ${funcName}`);
            // Don't auto-register, just log for manual initialization
        }
    });
    
    // Set up modal event listeners for common admin modals
    const commonModals = [
        'userModal', 'eventModal', 'campaignModal', 'templateModal',
        'groupModal', 'postModal', 'categoryModal', 'tagModal',
        'bulkDeleteModal', 'deleteModal', 'editModal', 'addPostModal', 'editPostModal'
    ];
    
    commonModals.forEach(modalId => {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.addEventListener('hidden.bs.modal', function() {
                // Execute pending refresh when modal closes
                window.crudRefreshManager.executePendingRefresh();
            });
        }
    });
    
    console.log('CRUD Refresh Manager: Auto-initialization complete');
});

// Export for module systems (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CRUDRefreshManager;
}
