// Blog Categories Management
class BlogCategoriesManager {
    constructor() {
        this.bulkDeleteManager = null;
        this.pagination = null;
        this.init();
    }

    init() {
        // Initialize bulk delete manager
        this.bulkDeleteManager = new BulkDeleteManager({
            itemSelector: '.category-checkbox',
            selectAllSelector: '#selectAll',
            bulkDeleteBtnSelector: '#bulkDeleteBtn',
            deleteEndpoint: '/api/blog/admin/categories/bulk-delete',
            getSelectedIds: () => this.getSelectedCategoryIds(),
            onDeleteSuccess: () => this.loadCategories()
        });

        // Initialize pagination if needed
        this.initPagination();

        // Bind events
        this.bindEvents();
    }

    bindEvents() {
        // Add category form
        const addForm = document.getElementById('addCategoryForm');
        if (addForm) {
            addForm.addEventListener('submit', (e) => this.handleAddCategory(e));
        }

        // Edit category form
        const editForm = document.getElementById('editCategoryForm');
        if (editForm) {
            editForm.addEventListener('submit', (e) => this.handleEditCategory(e));
        }

        // Use centralized slug generator - always generate slug
        SlugGenerator.setupMultipleAutoSlug([
            { titleSelector: '#categoryTitle', slugSelector: '#categorySlug', alwaysGenerate: true },
            { titleSelector: '#editCategoryTitle', slugSelector: '#editCategorySlug', alwaysGenerate: true }
        ]);
    }

    initPagination() {
        // Initialize pagination if container exists
        const container = document.getElementById('paginationContainer');
        if (container && window.categoriesPagination) {
            this.pagination = new Pagination({
                container: container,
                currentPage: window.categoriesPagination.current_page,
                totalPages: window.categoriesPagination.total_pages,
                totalItems: window.categoriesPagination.total,
                itemsPerPage: window.categoriesPagination.per_page,
                onPageChange: (page) => this.loadCategories(page),
                onPerPageChange: (perPage) => this.loadCategories(1, perPage)
            });
        }
    }

    getSelectedCategoryIds() {
        const checkboxes = document.querySelectorAll('.category-checkbox:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    async loadCategories(page = 1, perPage = 10) {
        try {
            const response = await fetch(`/api/blog/admin/categories?page=${page}&per_page=${perPage}`);
            const data = await response.json();
            
            if (data.success) {
                // Reload page with new data
                window.location.href = `/blog/admin/categories?page=${page}&per_page=${perPage}`;
            }
        } catch (error) {
            console.error('Error loading categories:', error);
            window.toastManager.show('Błąd podczas ładowania kategorii', 'error');
        }
    }

    async handleAddCategory(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);
        
        // Convert boolean fields
        data.is_active = document.getElementById('categoryIsActive').checked;
        data.sort_order = parseInt(data.sort_order) || 0;
        if (data.parent_id === '') data.parent_id = null;

        try {
            const response = await fetch('/api/blog/admin/categories', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            
            if (result.success) {
                window.toastManager.show(result.message || 'Kategoria została dodana pomyślnie', 'success');
                this.closeModal('addCategoryModal');
                e.target.reset();
                this.loadCategories();
            } else {
                window.toastManager.show(result.message || 'Błąd podczas dodawania kategorii', 'error');
            }
        } catch (error) {
            console.error('Error adding category:', error);
            window.toastManager.show('Błąd podczas dodawania kategorii', 'error');
        }
    }

    async handleEditCategory(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);
        const categoryId = data.id;
        
        // Convert boolean fields
        data.is_active = document.getElementById('editCategoryIsActive').checked;
        data.sort_order = parseInt(data.sort_order) || 0;
        if (data.parent_id === '') data.parent_id = null;

        try {
            const response = await fetch(`/api/blog/admin/categories/${categoryId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            
            if (result.success) {
                window.toastManager.show(result.message || 'Kategoria została zaktualizowana pomyślnie', 'success');
                this.closeModal('editCategoryModal');
                this.loadCategories();
            } else {
                window.toastManager.show(result.message || 'Błąd podczas aktualizacji kategorii', 'error');
            }
        } catch (error) {
            console.error('Error updating category:', error);
            window.toastManager.show('Błąd podczas aktualizacji kategorii', 'error');
        }
    }

    async editCategory(categoryId) {
        try {
            const response = await fetch(`/api/blog/admin/categories/${categoryId}`);
            const result = await response.json();
            
            if (result.success) {
                const category = result.category;
                
                // Fill edit form
                document.getElementById('editCategoryId').value = category.id;
                document.getElementById('editCategoryTitle').value = category.title;
                document.getElementById('editCategorySlug').value = category.slug;
                document.getElementById('editCategoryDescription').value = category.description || '';
                document.getElementById('editCategorySortOrder').value = category.sort_order || 0;
                document.getElementById('editCategoryIsActive').checked = category.is_active;
                
                // Set parent category
                const parentSelect = document.getElementById('editCategoryParent');
                parentSelect.value = category.parent_id || '';
                
                // Show modal
                const modal = new bootstrap.Modal(document.getElementById('editCategoryModal'));
                modal.show();
            } else {
                window.toastManager.show(result.message || 'Błąd podczas ładowania kategorii', 'error');
            }
        } catch (error) {
            console.error('Error loading category:', error);
            window.toastManager.show('Błąd podczas ładowania kategorii', 'error');
        }
    }

    async deleteCategory(categoryId) {
        if (!confirm('Czy na pewno chcesz usunąć tę kategorię?')) {
            return;
        }

        try {
            const response = await fetch(`/api/blog/admin/categories/${categoryId}`, {
                method: 'DELETE'
            });

            const result = await response.json();
            
            if (result.success) {
                window.toastManager.show(result.message || 'Kategoria została usunięta pomyślnie', 'success');
                this.loadCategories();
            } else {
                window.toastManager.show(result.message || 'Błąd podczas usuwania kategorii', 'error');
            }
        } catch (error) {
            console.error('Error deleting category:', error);
            window.toastManager.show('Błąd podczas usuwania kategorii', 'error');
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
function showAddCategoryModal() {
    const modal = new bootstrap.Modal(document.getElementById('addCategoryModal'));
    modal.show();
}

function editCategory(categoryId) {
    if (window.blogCategoriesManager) {
        window.blogCategoriesManager.editCategory(categoryId);
    }
}

function deleteCategory(categoryId) {
    if (window.blogCategoriesManager) {
        window.blogCategoriesManager.deleteCategory(categoryId);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.blogCategoriesManager = new BlogCategoriesManager();
});
