// Blog Tags Management
class BlogTagsManager {
    constructor() {
        this.bulkDeleteManager = null;
        this.pagination = null;
        this.init();
    }

    init() {
        // Bulk delete is now handled by the BulkDelete in the template

        // Initialize pagination if needed
        this.initPagination();

        // Initialize table resizer
        if (window.tableResizer) {
            window.tableResizer.init('#tagsTable');
        }

        // Bind events
        this.bindEvents();
    }

    bindEvents() {
        // Add tag form
        const addForm = document.getElementById('addTagForm');
        if (addForm) {
            addForm.addEventListener('submit', (e) => this.handleAddTag(e));
        }

        // Edit tag form
        const editForm = document.getElementById('editTagForm');
        if (editForm) {
            editForm.addEventListener('submit', (e) => this.handleEditTag(e));
        }

        // Use centralized slug generator - always generate slug
        SlugGenerator.setupMultipleAutoSlug([
            { titleSelector: '#tagName', slugSelector: '#tagSlug', alwaysGenerate: true },
            { titleSelector: '#editTagName', slugSelector: '#editTagSlug', alwaysGenerate: true }
        ]);
    }

    initPagination() {
        // Initialize pagination if container exists
        const container = document.getElementById('paginationContainer');
        if (container && window.tagsPagination) {
            this.pagination = new Pagination({
                container: container,
                currentPage: window.tagsPagination.current_page,
                totalPages: window.tagsPagination.total_pages,
                totalItems: window.tagsPagination.total,
                itemsPerPage: window.tagsPagination.per_page,
                onPageChange: (page) => this.loadTags(page),
                onPerPageChange: (perPage) => this.loadTags(1, perPage)
            });
        }
    }

    getSelectedTagIds() {
        const checkboxes = document.querySelectorAll('.tag-checkbox:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    async loadTags(page = 1, perPage = 10) {
        try {
            const response = await fetch(`/api/blog/tags?page=${page}&per_page=${perPage}`);
            const data = await response.json();
            
            if (data.success) {
                // Update the tags table
                this.updateTagsTable(data.tags);
                // Update pagination if provided
                if (data.pagination) {
                    this.updatePagination(data.pagination);
                }
            } else {
                window.toastManager.show('Błąd podczas ładowania tagów', 'error');
            }
        } catch (error) {
            console.error('Error loading tags:', error);
            window.toastManager.show('Błąd podczas ładowania tagów', 'error');
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
                    this.loadTags(page);
                });
                
                paginationContainer.paginationInstance.setPerPageChangeCallback((newPage, perPage) => {
                    this.loadTags(newPage, perPage);
                });
                
                paginationContainer.paginationInstance.setData(paginationData);
            }
        }
    }

    updateTagsTable(tags) {
        const tbody = document.querySelector('#tagsTable tbody');
        if (!tbody) return;

        tbody.innerHTML = '';
        
        tags.forEach(tag => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <input type="checkbox" name="itemIds" value="${tag.id}">
                </td>
                <td>
                    <span class="badge admin-badge admin-badge-primary">${tag.id}</span>
                </td>
                <td>${tag.name}</td>
                <td>${tag.posts_count || 0}</td>
                <td>
                    <span class="badge ${tag.is_active ? 'bg-success' : 'bg-secondary'}">
                        ${tag.is_active ? 'Aktywny' : 'Nieaktywny'}
                    </span>
                </td>
                <td>${tag.created_at ? new Date(tag.created_at).toLocaleDateString('pl-PL') : '-'}</td>
                <td>
                    <div class="btn-group" role="group">
                        <button class="btn btn-sm admin-btn-outline" onclick="editTag(${tag.id})" title="Edytuj">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm admin-btn-danger" onclick="deleteTag(${tag.id})" title="Usuń">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async handleAddTag(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);
        
        // Convert boolean fields
        data.is_active = document.getElementById('tagIsActive').checked;

        try {
            const response = await fetch('/api/blog/tags', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            
            if (result.success) {
                window.toastManager.show(result.message || 'Tag został dodany pomyślnie', 'success');
                this.closeModal('addTagModal');
                e.target.reset();
                this.loadTags();
                
                // Wywołaj globalne odświeżenie
                if (typeof window.refreshAfterCRUD === 'function') {
                    window.refreshAfterCRUD();
                } else {
                    console.warn('window.refreshAfterCRUD is not available');
                }
            } else {
                window.toastManager.show(result.message || 'Błąd podczas dodawania tagu', 'error');
            }
        } catch (error) {
            console.error('Error adding tag:', error);
            window.toastManager.show('Błąd podczas dodawania tagu', 'error');
        }
    }

    async handleEditTag(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);
        const tagId = data.id;
        
        // Convert boolean fields
        data.is_active = document.getElementById('editTagIsActive').checked;

        try {
            const response = await fetch(`/api/blog/tags/${tagId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            
            if (result.success) {
                window.toastManager.show(result.message || 'Tag został zaktualizowany pomyślnie', 'success');
                this.closeModal('editTagModal');
                this.loadTags();
                
                // Wywołaj globalne odświeżenie
                if (typeof window.refreshAfterCRUD === 'function') {
                    window.refreshAfterCRUD();
                } else {
                    console.warn('window.refreshAfterCRUD is not available');
                }
            } else {
                window.toastManager.show(result.message || 'Błąd podczas aktualizacji tagu', 'error');
            }
        } catch (error) {
            console.error('Error updating tag:', error);
            window.toastManager.show('Błąd podczas aktualizacji tagu', 'error');
        }
    }

    async editTag(tagId) {
        try {
            const response = await fetch(`/api/blog/tags/${tagId}`);
            const result = await response.json();
            
            if (result.success) {
                const tag = result.tag;
                
                // Fill edit form
                const editTagId = document.getElementById('editTagId');
                const editTagName = document.getElementById('editTagName');
                const editTagSlug = document.getElementById('editTagSlug');
                const editTagDescription = document.getElementById('editTagDescription');
                const editTagIsActive = document.getElementById('editTagIsActive');
                
                if (editTagId) editTagId.value = tag.id;
                if (editTagName) editTagName.value = tag.name;
                if (editTagSlug) editTagSlug.value = tag.slug;
                if (editTagDescription) editTagDescription.value = tag.description || '';
                if (editTagIsActive) editTagIsActive.checked = tag.is_active;
                
                // Show modal
                const modal = new bootstrap.Modal(document.getElementById('editTagModal'));
                modal.show();
            } else {
                window.toastManager.show(result.message || 'Błąd podczas ładowania tagu', 'error');
            }
        } catch (error) {
            console.error('Error loading tag:', error);
            window.toastManager.show('Błąd podczas ładowania tagu', 'error');
        }
    }

    deleteTag(tagId) {
        window.deleteConfirmation.showSingleDelete(
            'tag',
            () => this.performDeleteTag(tagId),
            'tag'
        );
    }

    async performDeleteTag(tagId) {
        try {
            console.log(`🔍 Attempting to delete tag ${tagId}`);
            
            const response = await fetch(`/api/blog/tags/${tagId}`, {
                method: 'DELETE',
                credentials: 'include'
            });

            console.log(`🔍 Delete response status: ${response.status}`);
            
            const result = await response.json();
            console.log(`🔍 Delete response:`, result);
            
            if (result.success) {
                window.toastManager.show(result.message || 'Tag został usunięty pomyślnie', 'success');
                this.loadTags();
                
                // Wywołaj globalne odświeżenie
                if (typeof window.refreshAfterCRUD === 'function') {
                    window.refreshAfterCRUD();
                } else {
                    console.warn('window.refreshAfterCRUD is not available');
                }
            } else {
                window.toastManager.show(result.message || 'Błąd podczas usuwania tagu', 'error');
            }
        } catch (error) {
            console.error('Error deleting tag:', error);
            window.toastManager.show('Błąd podczas usuwania tagu', 'error');
        }
    }

    closeModal(modalId) {
        const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
        if (modal) {
            modal.hide();
        }
    }

}

// Global functions for onclick handlers
function showAddTagModal() {
    const modal = new bootstrap.Modal(document.getElementById('addTagModal'));
    modal.show();
}

function editTag(tagId) {
    if (window.blogTagsManager) {
        window.blogTagsManager.editTag(tagId);
    } else {
        console.error('blogTagsManager not initialized yet');
        // Retry after a short delay
        setTimeout(() => {
            if (window.blogTagsManager) {
                window.blogTagsManager.editTag(tagId);
            } else {
                window.toastManager.error('Błąd: Menedżer tagów nie jest jeszcze załadowany. Spróbuj ponownie.');
            }
        }, 100);
    }
}

function deleteTag(tagId) {
    if (window.blogTagsManager) {
        window.blogTagsManager.deleteTag(tagId);
    } else {
        console.error('blogTagsManager not initialized yet');
        // Retry after a short delay
        setTimeout(() => {
            if (window.blogTagsManager) {
                window.blogTagsManager.deleteTag(tagId);
            } else {
                window.toastManager.error('Błąd: Menedżer tagów nie jest jeszcze załadowany. Spróbuj ponownie.');
            }
        }, 100);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.blogTagsManager = new BlogTagsManager();
    console.log('BlogTagsManager initialized:', window.blogTagsManager);
    
    // Initialize CRUD Refresh Manager for blog tags
    if (typeof CRUDRefreshManager !== 'undefined' && window.crudRefreshManager) {
        window.crudRefreshManager.init(() => {
            window.blogTagsManager.loadTags();
        });
        console.log('CRUD Refresh Manager initialized for blog tags');
    }
});

