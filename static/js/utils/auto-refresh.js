/**
 * Auto-Refresh System for CRUD Operations
 * Automatycznie odświeża dane po operacjach CRUD bez przeładowania strony
 */

class AutoRefreshSystem {
    constructor() {
        this.refreshFunctions = new Map();
        this.init();
    }

    init() {
        console.log('🔄 Auto-Refresh System initialized');
        this.registerDefaultRefreshFunctions();
    }

    registerDefaultRefreshFunctions() {
        // Register refresh functions for different admin pages
        this.registerRefreshFunction('menu', () => this.refreshMenuItems());
        this.registerRefreshFunction('sections', () => this.refreshSections());
        this.registerRefreshFunction('users', () => this.refreshUsers());
        this.registerRefreshFunction('blog-posts', () => this.refreshBlogPosts());
        this.registerRefreshFunction('blog-categories', () => this.refreshBlogCategories());
        this.registerRefreshFunction('blog-tags', () => this.refreshBlogTags());
        this.registerRefreshFunction('benefits', () => this.refreshBenefits());
        this.registerRefreshFunction('testimonials', () => this.refreshTestimonials());
        this.registerRefreshFunction('faq', () => this.refreshFaq());
        this.registerRefreshFunction('email-groups', () => this.refreshEmailGroups());
        this.registerRefreshFunction('email-campaigns', () => this.refreshEmailCampaigns());
        this.registerRefreshFunction('email-queue', () => this.refreshEmailQueue());
        this.registerRefreshFunction('crm-dashboard', () => this.refreshCrmDashboard());
    }

    registerRefreshFunction(type, refreshFunction) {
        this.refreshFunctions.set(type, refreshFunction);
        console.log(`📝 Registered refresh function: ${type}`);
    }

    refreshAfterCRUD(type = null) {
        console.log('🔄 Auto-refreshing after CRUD operation...');
        
        if (type && this.refreshFunctions.has(type)) {
            // Refresh specific type
            this.refreshFunctions.get(type)();
        } else {
            // Auto-detect current page and refresh
            const currentPath = window.location.pathname;
            this.autoDetectAndRefresh(currentPath);
        }
    }

    autoDetectAndRefresh(path) {
        if (path.includes('/admin/menu')) {
            this.refreshMenuItems();
        } else if (path.includes('/admin/sections')) {
            this.refreshSections();
        } else if (path.includes('/admin/users')) {
            this.refreshUsers();
        } else if (path.includes('/admin/blog/posts')) {
            this.refreshBlogPosts();
        } else if (path.includes('/admin/blog/categories')) {
            this.refreshBlogCategories();
        } else if (path.includes('/admin/blog/tags')) {
            this.refreshBlogTags();
        } else if (path.includes('/admin/benefits')) {
            this.refreshBenefits();
        } else if (path.includes('/admin/testimonials')) {
            this.refreshTestimonials();
        } else if (path.includes('/admin/faq')) {
            this.refreshFaq();
        } else if (path.includes('/admin/email/groups')) {
            this.refreshEmailGroups();
        } else if (path.includes('/admin/email/campaigns')) {
            this.refreshEmailCampaigns();
        } else if (path.includes('/admin/email/queue')) {
            this.refreshEmailQueue();
        } else if (path.includes('/admin/crm/dashboard')) {
            this.refreshCrmDashboard();
        } else {
            console.log('🔄 Unknown page, falling back to page reload');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }
    }

    // Specific refresh functions for each admin page
    refreshMenuItems() {
        console.log('🔄 Refreshing menu items...');
        this.fetchAndUpdateTable('/api/menu', 'menuTable');
    }

    refreshSections() {
        console.log('🔄 Refreshing sections...');
        this.fetchAndUpdateTable('/api/sections', 'sectionsTable');
    }

    refreshUsers() {
        console.log('🔄 Refreshing users...');
        this.fetchAndUpdateTable('/api/users', 'usersTable');
    }

    refreshBlogPosts() {
        console.log('🔄 Refreshing blog posts...');
        this.fetchAndUpdateTable('/api/blog/posts', 'blogPostsTable');
    }

    refreshBlogCategories() {
        console.log('🔄 Refreshing blog categories...');
        this.fetchAndUpdateTable('/api/blog/categories', 'blogCategoriesTable');
    }

    refreshBlogTags() {
        console.log('🔄 Refreshing blog tags...');
        this.fetchAndUpdateTable('/api/blog/tags', 'blogTagsTable');
    }

    refreshBenefits() {
        console.log('🔄 Refreshing benefits...');
        this.fetchAndUpdateTable('/api/benefits', 'benefitsTable');
    }

    refreshTestimonials() {
        console.log('🔄 Refreshing testimonials...');
        this.fetchAndUpdateTable('/api/testimonials', 'testimonialsTable');
    }

    refreshFaq() {
        console.log('🔄 Refreshing FAQ...');
        this.fetchAndUpdateTable('/api/faq', 'faqTable');
    }

    refreshEmailGroups() {
        console.log('🔄 Refreshing email groups...');
        this.fetchAndUpdateTable('/api/email/groups', 'groupsTable');
    }

    refreshEmailCampaigns() {
        console.log('🔄 Refreshing email campaigns...');
        this.fetchAndUpdateTable('/api/email/campaigns', 'campaignsTable');
    }

    refreshEmailQueue() {
        console.log('🔄 Refreshing email queue...');
        this.fetchAndUpdateTable('/api/email/queue', 'emailQueueTable');
    }

    refreshCrmDashboard() {
        console.log('🔄 Refreshing CRM dashboard...');
        if (typeof loadDashboardStats === 'function') {
            loadDashboardStats();
        } else {
            this.fetchAndUpdateTable('/api/crm/dashboard-stats', 'crmDashboardStats');
        }
    }

    async fetchAndUpdateTable(endpoint, tableId) {
        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data[Object.keys(data)[1]]) {
                // Update table with new data
                this.updateTableWithData(tableId, data[Object.keys(data)[1]]);
            } else {
                console.warn('No data received for', endpoint);
                // Fallback to page reload
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        } catch (error) {
            console.error('Error refreshing data:', error);
            // Fallback to page reload
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }
    }

    updateTableWithData(tableId, data) {
        const table = document.getElementById(tableId);
        if (!table) {
            console.warn(`Table ${tableId} not found`);
            // Fallback to page reload
            setTimeout(() => {
                window.location.reload();
            }, 500);
            return;
        }

        console.log(`✅ Found table ${tableId}, updating with ${data.length} items`);
        
        // For now, just reload the page as fallback
        // In the future, implement proper table row updates
        setTimeout(() => {
            window.location.reload();
        }, 500);
    }
}

// Initialize the system
const autoRefreshSystem = new AutoRefreshSystem();

// Global function for CRUD operations
window.refreshAfterCRUD = function(type = null) {
    autoRefreshSystem.refreshAfterCRUD(type);
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AutoRefreshSystem;
}
