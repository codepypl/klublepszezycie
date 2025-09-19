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
        
        // Add a small delay to ensure DOM is ready
        setTimeout(() => {
            if (type && this.refreshFunctions.has(type)) {
                // Refresh specific type
                this.refreshFunctions.get(type)();
            } else {
                // Auto-detect current page and refresh
                const currentPath = window.location.pathname;
                this.autoDetectAndRefresh(currentPath);
            }
        }, 100);
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
        console.log('🔍 Current file version should be updated - looking for menuTable');
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
        this.fetchAndUpdateTable('/api/email/groups', 'emailGroupsTable');
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
        console.log(`🔍 Looking for table with ID: ${tableId}`);
        console.log(`🔍 Available tables on page:`, document.querySelectorAll('table[id]'));
        
        const table = document.getElementById(tableId);
        if (!table) {
            console.warn(`❌ Table ${tableId} not found`);
            console.log(`🔍 All tables on page:`, Array.from(document.querySelectorAll('table')).map(t => t.id || 'no-id'));
            console.log(`🔍 All elements with ID:`, Array.from(document.querySelectorAll('[id]')).map(e => e.id));
            
            // Check if table might be in a conditional block
            if (tableId === 'menuTable') {
                console.log(`🔍 Checking if menu_items is empty...`);
                const menuItemsContainer = document.querySelector('.admin-card-body');
                if (menuItemsContainer) {
                    console.log(`🔍 Menu items container found:`, menuItemsContainer.innerHTML.substring(0, 200));
                }
            }
            
            // Fallback to page reload
            setTimeout(() => {
                window.location.reload();
            }, 500);
            return;
        }

        console.log(`✅ Found table ${tableId}, updating with ${data.length} items`);
        
        // Implement proper table row updates based on table type
        if (tableId === 'usersTable') {
            this.updateUsersTable(table, data);
        } else if (tableId === 'emailQueueTable') {
            this.updateEmailQueueTable(table, data);
        } else if (tableId === 'emailGroupsTable') {
            this.updateEmailGroupsTable(table, data);
        } else {
            // For other tables, use fallback to page reload
            setTimeout(() => {
                window.location.reload();
            }, 500);
        }
    }

    // Update users table with new data
    updateUsersTable(table, users) {
        console.log(`🔄 Updating users table with ${users.length} users`);
        
        const tbody = table.querySelector('tbody');
        if (!tbody) {
            console.warn('No tbody found in users table');
            return;
        }

        // Clear existing rows
        tbody.innerHTML = '';

        // Add new rows
        users.forEach(user => {
            const row = this.createUserRow(user);
            tbody.appendChild(row);
        });

        console.log(`✅ Updated users table with ${users.length} rows`);
    }

    // Create a user table row
    createUserRow(user) {
        const row = document.createElement('tr');
        row.setAttribute('data-user-id', user.id);
        
        // Format dates
        const createdDate = user.created_at ? this.formatDate(user.created_at) : '-';
        const lastLoginDate = user.last_login ? this.formatDate(user.last_login) : '-';
        
        // Get event name if user is registered for an event
        let eventInfo = '-';
        if (user.event_id) {
            // We'll need to fetch event details or pass them from the API
            eventInfo = `Wydarzenie ID: ${user.event_id}`;
        }

        row.innerHTML = `
            <td>
                <input type="checkbox" class="form-check-input" value="${user.id}">
            </td>
            <td>${user.id}</td>
            <td>${user.first_name || '-'}</td>
            <td>${user.email}</td>
            <td>${eventInfo}</td>
            <td>${user.group_id || '-'}</td>
            <td>
                ${this.getAccountTypeBadge(user.account_type)}
            </td>
            <td>
                ${user.is_active ? 
                    '<span class="badge admin-badge admin-badge-success">Aktywny</span>' : 
                    '<span class="badge admin-badge admin-badge-danger">Nieaktywny</span>'
                }
            </td>
            <td>
                <div class="btn-group" role="group">
                    <button type="button" class="btn btn-sm admin-btn-outline" 
                            onclick="viewUserProfile(${user.id})" 
                            title="Podgląd profilu">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button type="button" class="btn btn-sm admin-btn-outline" 
                            onclick="editUser(${user.id})" 
                            title="Edytuj użytkownika">
                        <i class="fas fa-edit"></i>
                    </button>
                    ${!user.is_admin ? `
                        <button type="button" class="btn btn-sm admin-btn-danger" 
                                onclick="deleteUser(${user.id})" 
                                title="Usuń użytkownika">
                            <i class="fas fa-trash"></i>
                        </button>
                    ` : ''}
                </div>
            </td>
        `;
        
        return row;
    }

    // Get account type badge
    getAccountTypeBadge(accountType) {
        switch(accountType) {
            case 'admin':
                return '<span class="badge admin-badge admin-badge-danger">Administrator</span>';
            case 'club_member':
                return '<span class="badge admin-badge admin-badge-success">Członek klubu</span>';
            case 'ankieter':
                return '<span class="badge admin-badge admin-badge-warning">Ankieter</span>';
            case 'event_registration':
                return '<span class="badge admin-badge admin-badge-info">Rejestracja na wydarzenia</span>';
            default:
                return '<span class="badge admin-badge admin-badge-secondary">Użytkownik</span>';
        }
    }

    // Format date for display
    formatDate(dateString) {
        if (!dateString) return '-';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleString('pl-PL', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            console.error('Error formatting date:', error);
            return '-';
        }
    }

    // Update email queue table
    updateEmailQueueTable(table, emails) {
        console.log(`🔄 Updating email queue table with ${emails.length} emails`);
        
        const tbody = table.querySelector('tbody');
        if (!tbody) {
            console.warn('No tbody found in email queue table');
            return;
        }

        // Clear existing rows
        tbody.innerHTML = '';

        // Add new rows
        emails.forEach(email => {
            const row = this.createEmailQueueRow(email);
            tbody.appendChild(row);
        });

        console.log(`✅ Updated email queue table with ${emails.length} rows`);
    }

    // Create email queue row
    createEmailQueueRow(email) {
        const row = document.createElement('tr');
        row.setAttribute('data-email-id', email.id);
        
        row.innerHTML = `
            <td>${email.id}</td>
            <td>${email.recipient_email}</td>
            <td>${email.subject}</td>
            <td>${this.getEmailStatusBadge(email.status)}</td>
            <td>${this.formatDate(email.created_at)}</td>
            <td>${this.formatDate(email.sent_at)}</td>
            <td>
                <div class="btn-group" role="group">
                    <button type="button" class="btn btn-sm admin-btn-outline" 
                            onclick="viewEmail(${email.id})" 
                            title="Podgląd emaila">
                        <i class="fas fa-eye"></i>
                    </button>
                    ${email.status === 'pending' ? `
                        <button type="button" class="btn btn-sm admin-btn-success" 
                                onclick="sendEmail(${email.id})" 
                                title="Wyślij email">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    ` : ''}
                </div>
            </td>
        `;
        
        return row;
    }

    // Get email status badge
    getEmailStatusBadge(status) {
        switch(status) {
            case 'pending':
                return '<span class="badge admin-badge admin-badge-warning">Oczekujący</span>';
            case 'sent':
                return '<span class="badge admin-badge admin-badge-success">Wysłany</span>';
            case 'failed':
                return '<span class="badge admin-badge admin-badge-danger">Błąd</span>';
            default:
                return '<span class="badge admin-badge admin-badge-secondary">Nieznany</span>';
        }
    }

    // Update email groups table
    updateEmailGroupsTable(table, groups) {
        console.log(`🔄 Updating email groups table with ${groups.length} groups`);
        
        const tbody = table.querySelector('tbody');
        if (!tbody) {
            console.warn('No tbody found in email groups table');
            return;
        }

        // Clear existing rows
        tbody.innerHTML = '';

        // Add new rows
        groups.forEach(group => {
            const row = this.createEmailGroupRow(group);
            tbody.appendChild(row);
        });

        console.log(`✅ Updated email groups table with ${groups.length} rows`);
    }

    // Create email group row
    createEmailGroupRow(group) {
        const row = document.createElement('tr');
        row.setAttribute('data-group-id', group.id);
        
        row.innerHTML = `
            <td>${group.id}</td>
            <td>${group.name}</td>
            <td>${group.description || '-'}</td>
            <td>${group.member_count || 0}</td>
            <td>${this.getGroupTypeBadge(group.group_type)}</td>
            <td>${this.formatDate(group.created_at)}</td>
            <td>
                <div class="btn-group" role="group">
                    <button type="button" class="btn btn-sm admin-btn-outline" 
                            onclick="viewGroupMembers(${group.id})" 
                            title="Podgląd członków">
                        <i class="fas fa-users"></i>
                    </button>
                    <button type="button" class="btn btn-sm admin-btn-outline" 
                            onclick="editGroup(${group.id})" 
                            title="Edytuj grupę">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button type="button" class="btn btn-sm admin-btn-danger" 
                            onclick="deleteGroup(${group.id})" 
                            title="Usuń grupę">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        
        return row;
    }

    // Get group type badge
    getGroupTypeBadge(groupType) {
        switch(groupType) {
            case 'club_members':
                return '<span class="badge admin-badge admin-badge-success">Członkowie klubu</span>';
            case 'event_based':
                return '<span class="badge admin-badge admin-badge-info">Wydarzenie</span>';
            case 'manual':
                return '<span class="badge admin-badge admin-badge-secondary">Ręczna</span>';
            default:
                return '<span class="badge admin-badge admin-badge-secondary">Nieznany</span>';
        }
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
