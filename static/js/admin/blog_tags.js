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

        // Auto-generate slug from name
        const nameInput = document.getElementById('tagName');
        const slugInput = document.getElementById('tagSlug');
        if (nameInput && slugInput) {
            nameInput.addEventListener('input', () => {
                if (!slugInput.value) {
                    slugInput.value = this.slugify(nameInput.value);
                }
            });
        }

        const editNameInput = document.getElementById('editTagName');
        const editSlugInput = document.getElementById('editTagSlug');
        if (editNameInput && editSlugInput) {
            editNameInput.addEventListener('input', () => {
                if (!editSlugInput.value) {
                    editSlugInput.value = this.slugify(editNameInput.value);
                }
            });
        }
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
                // Reload page with new data
                window.location.href = `/blog/admin/tags?page=${page}&per_page=${perPage}`;
            }
        } catch (error) {
            console.error('Error loading tags:', error);
            window.toastManager.show('Błąd podczas ładowania tagów', 'error');
        }
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
                document.getElementById('editTagId').value = tag.id;
                document.getElementById('editTagName').value = tag.name;
                document.getElementById('editTagSlug').value = tag.slug;
                document.getElementById('editTagDescription').value = tag.description || '';
                document.getElementById('editTagIsActive').checked = tag.is_active;
                
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

    async deleteTag(tagId) {
        window.deleteConfirmation.showSingleDelete(
            'tag',
            () => {
                // Continue with deletion
                performDeleteTag(tagId);
            },
            'tag'
        );
    }

    async performDeleteTag(tagId) {
        try {
            const response = await fetch(`/api/blog/tags/${tagId}`, {
                method: 'DELETE'
            });

            const result = await response.json();
            
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

    slugify(text) {
        return text
            .toString()
            .toLowerCase()
            .replace(/\s+/g, '-')
            .replace(/[^\w\-]+/g, '')
            .replace(/\-\-+/g, '-')
            .replace(/^-+/, '')
            .replace(/-+$/, '');
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
                showError('Błąd: Menedżer tagów nie jest jeszcze załadowany. Spróbuj ponownie.');
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
                showError('Błąd: Menedżer tagów nie jest jeszcze załadowany. Spróbuj ponownie.');
            }
        }, 100);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.blogTagsManager = new BlogTagsManager();
    console.log('BlogTagsManager initialized:', window.blogTagsManager);
});

