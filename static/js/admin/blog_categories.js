// Blog Categories Management
class BlogCategoriesManager {
    constructor() {
        this.bulkDeleteManager = null;
        this.pagination = null;
        this.init();
    }

    init() {
        // Bulk delete is now handled by the BulkDeleteManager in the template
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
        const checkboxes = document.querySelectorAll('input[name="itemIds"]:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    async loadCategories(page = 1, perPage = 10) {
        try {
            const response = await fetch(`/api/blog/admin/categories?page=${page}&per_page=${perPage}`);
            const data = await response.json();
            
            if (data.success) {
                // Update the categories table
                this.updateCategoriesTable(data.categories);
            } else {
                window.toastManager.show('Błąd podczas ładowania kategorii', 'error');
            }
        } catch (error) {
            console.error('Error loading categories:', error);
            window.toastManager.show('Błąd podczas ładowania kategorii', 'error');
        }
    }

    updateCategoriesTable(categories) {
        const tbody = document.querySelector('#categoriesTable tbody');
        if (!tbody) return;

        tbody.innerHTML = '';
        
        categories.forEach(category => {
            const row = document.createElement('tr');
            row.setAttribute('data-category-id', category.id);
            
            // Format description
            const description = category.description ? 
                (category.description.length > 100 ? 
                    category.description.substring(0, 100) + '...' : 
                    category.description) : '';
            
            // Format path (parent category)
            const path = category.parent ? 
                `<span class="text-muted">${category.parent.title} / </span>${category.title}` : 
                category.title;
            
            // Format created date
            const createdDate = category.created_at ? 
                new Date(category.created_at).toLocaleDateString('pl-PL') : '';
            
            row.innerHTML = `
                <td>
                    <input type="checkbox" name="itemIds" value="${category.id}">
                </td>
                <td>
                    <strong>${category.title}</strong>
                    ${description ? `<br><small class="text-muted">${description}</small>` : ''}
                </td>
                <td>
                    <code>${category.slug}</code>
                </td>
                <td>
                    ${path}
                </td>
                <td>
                    <span class="badge admin-badge admin-badge-info">${category.posts_count || 0}</span>
                </td>
                <td>
                    <span class="badge admin-badge ${category.is_active ? 'admin-badge-success' : 'admin-badge-danger'}">
                        ${category.is_active ? 'Aktywna' : 'Nieaktywna'}
                    </span>
                </td>
                <td>
                    ${createdDate}
                </td>
                <td>
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-sm btn-outline-primary" onclick="window.blogCategoriesManager.editCategory(${category.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button type="button" class="btn btn-sm btn-outline-danger" onclick="window.blogCategoriesManager.deleteCategory(${category.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
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
                
                // Wywołaj globalne odświeżenie
                if (typeof window.refreshAfterCRUD === 'function') {
                    window.refreshAfterCRUD();
                } else {
                    console.warn('window.refreshAfterCRUD is not available');
                }
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
                
                // Wywołaj globalne odświeżenie
                if (typeof window.refreshAfterCRUD === 'function') {
                    window.refreshAfterCRUD();
                } else {
                    console.warn('window.refreshAfterCRUD is not available');
                }
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
        window.deleteConfirmation.showSingleDelete(
            'kategorię',
            () => {
                // Continue with deletion
                performDeleteCategory(categoryId);
            },
            'kategorię'
        );
    }

    async performDeleteCategory(categoryId) {
        try {
            const response = await fetch(`/api/blog/admin/categories/${categoryId}`, {
                method: 'DELETE'
            });

            const result = await response.json();
            
            if (result.success) {
                window.toastManager.show(result.message || 'Kategoria została usunięta pomyślnie', 'success');
                this.loadCategories();
                
                // Wywołaj globalne odświeżenie
                if (typeof window.refreshAfterCRUD === 'function') {
                    window.refreshAfterCRUD();
                } else {
                    console.warn('window.refreshAfterCRUD is not available');
                }
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
    
    // Check for edit parameter in URL
    const urlParams = new URLSearchParams(window.location.search);
    const editCategoryId = urlParams.get('edit');
    if (editCategoryId) {
        // Automatically open edit modal for the specified category
        setTimeout(() => {
            editCategory(parseInt(editCategoryId));
        }, 1000); // Wait for categories to load
    }
});
