// Blog Posts Manager
class BlogPostsManager {
    constructor() {
        this.posts = [];
        this.categories = [];
        this.tagSelectors = {};
        this.init();
    }

    async init() {
        await this.loadCategories();
        this.setupTagSelectors();
        this.bindEvents();
        this.setupSlugGeneration();
        this.setupImageHandlers();
    }

    async loadCategories() {
        try {
            const response = await fetch('/api/blog/admin/categories', {
                credentials: 'include'
            });
            const result = await response.json();
            if (result.success) {
                this.categories = result.categories;
                this.populateCategoryCheckboxes();
            }
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }

    populateCategoryCheckboxes() {
        const containers = ['postCategories', 'editPostCategories'];
        
        containers.forEach(containerId => {
            const container = document.getElementById(containerId);
            if (container) {
                container.innerHTML = '';
                
                this.categories.forEach(category => {
                    const div = document.createElement('div');
                    div.className = 'form-check';
                    div.innerHTML = `
                        <input class="form-check-input" type="checkbox" value="${category.id}" id="${containerId}_${category.id}" name="categories">
                        <label class="form-check-label" for="${containerId}_${category.id}">
                            ${category.full_path || category.title}
                        </label>
                    `;
                    container.appendChild(div);
                });
            }
        });
    }

    setupTagSelectors() {
        // Check if we're on a page that needs TagSelector
        const addContainer = document.getElementById('postTagsSelector');
        const editContainer = document.getElementById('editPostTagsSelector');
        
        if (!addContainer && !editContainer) {
            // No tag selectors needed on this page
            return;
        }

        // Wait for TagSelector to be available with retry mechanism
        if (typeof TagSelector === 'undefined') {
            console.warn('TagSelector not loaded, retrying in 100ms...');
            setTimeout(() => this.setupTagSelectors(), 100);
            return;
        }

        // Initialize tag selectors for add and edit forms
        try {
            if (!addContainer) {
                console.warn('postTagsSelector container not found');
            } else {
                this.tagSelectors.add = new TagSelector('postTagsSelector', {
                    placeholder: 'Wpisz tagi lub wybierz z listy...',
                    allowNew: true,
                    maxTags: 10
                });
            }

            if (!editContainer) {
                console.warn('editPostTagsSelector container not found');
            } else {
                this.tagSelectors.edit = new TagSelector('editPostTagsSelector', {
                    placeholder: 'Wpisz tagi lub wybierz z listy...',
                    allowNew: true,
                    maxTags: 10
                });
            }
            
        } catch (error) {
            console.error('Error initializing tag selectors:', error);
        }
    }

    bindEvents() {
        // Add post form
        const addForm = document.getElementById('addPostForm');
        if (addForm) {
            addForm.addEventListener('submit', (e) => this.handleAddPost(e));
        }

        // Edit post form
        const editForm = document.getElementById('editPostForm');
        if (editForm) {
            editForm.addEventListener('submit', (e) => this.handleEditPost(e));
        }
    }

    setupSlugGeneration() {
        // Use centralized slug generator - always generate slug
        SlugGenerator.setupMultipleAutoSlug([
            { titleSelector: '#postTitle', slugSelector: '#postSlug', alwaysGenerate: true },
            { titleSelector: '#editPostTitle', slugSelector: '#editPostSlug', alwaysGenerate: true }
        ]);
    }


    async handleAddPost(e) {
        e.preventDefault();
        
        // Validate form
        if (!window.FormValidators.validateBlogPost('add')) {
            return;
        }
        
        const formData = new FormData(e.target);
        
        
        // Get content from TinyMCE
        const content = this.getTinyMCEContent('postContent');
        formData.set('content', content);
        
        // Convert categories array
        const categoryCheckboxes = document.querySelectorAll('#postCategories input[type="checkbox"]:checked');
        const categories = Array.from(categoryCheckboxes).map(cb => parseInt(cb.value));
        formData.delete('categories');
        if (categories.length > 0) {
            formData.append('categories', JSON.stringify(categories));
        }
        
        // Get tags from tag selector
        let tagNames = [];
        if (this.tagSelectors.add && typeof this.tagSelectors.add.getTagNames === 'function') {
            tagNames = this.tagSelectors.add.getTagNames();
        }
        formData.delete('tags');
        if (tagNames.length > 0) {
            formData.append('tags', JSON.stringify(tagNames));
        }

        // Handle allow_comments checkbox
        const allowComments = document.getElementById('postAllowComments').checked;
        formData.set('allow_comments', allowComments);


        try {
            const response = await fetch('/api/blog/admin/posts', {
                method: 'POST',
                body: formData,
                credentials: 'include'
            });

            // Check for 413 error (Content Too Large)
            if (response.status === 413) {
                window.toastManager.error('Artykuł jest za duży. Spróbuj zmniejszyć rozmiar obrazów lub treści.');
                return;
            }

            // Check if response is JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                console.error('Non-JSON response:', text);
                window.toastManager.error('Serwer zwrócił nieprawidłową odpowiedź. Sprawdź logi serwera.');
                return;
            }

            const result = await response.json();
            
            if (result.success) {
                window.toastManager.success(result.message || 'Artykuł został dodany pomyślnie');
                this.closeModal('addPostModal');
                location.reload();
                
                // Wywołaj globalne odświeżenie
                if (typeof window.refreshAfterCRUD === 'function') {
                    window.refreshAfterCRUD();
                }
            } else {
                window.toastManager.error(result.error || 'Błąd podczas dodawania artykułu');
            }
        } catch (error) {
            console.error('Error adding post:', error);
            if (error.message.includes('Unexpected token')) {
                window.toastManager.error('Serwer zwrócił nieprawidłową odpowiedź. Sprawdź czy artykuł nie jest za duży.');
            } else {
                window.toastManager.error('Błąd podczas dodawania artykułu');
            }
        }
    }

    async handleEditPost(e) {
        e.preventDefault();
        
        // Validate form
        if (!window.FormValidators.validateBlogPost('edit')) {
            return;
        }
        
        const formData = new FormData(e.target);
        const postId = formData.get('id');
        
        // Get content from TinyMCE
        const content = this.getTinyMCEContent('editPostContent');
        formData.set('content', content);
        
        // Convert categories array
        const categoryCheckboxes = document.querySelectorAll('#editPostCategories input[type="checkbox"]:checked');
        const categories = Array.from(categoryCheckboxes).map(cb => parseInt(cb.value));
        formData.delete('categories');
        if (categories.length > 0) {
            formData.append('categories', JSON.stringify(categories));
        }
        
        // Get tags from tag selector
        let tagNames = [];
        if (this.tagSelectors.edit && typeof this.tagSelectors.edit.getTagNames === 'function') {
            tagNames = this.tagSelectors.edit.getTagNames();
        }
        formData.delete('tags');
        if (tagNames.length > 0) {
            formData.append('tags', JSON.stringify(tagNames));
        } else {
            formData.append('tags', JSON.stringify([]));
        }

        // Handle allow_comments checkbox
        const allowComments = document.getElementById('editPostAllowComments').checked;
        formData.set('allow_comments', allowComments);

        try {
            const response = await fetch(`/api/blog/admin/posts/${postId}`, {
                method: 'PUT',
                body: formData,
                credentials: 'include'
            });

            // Check for 413 error (Content Too Large)
            if (response.status === 413) {
                window.toastManager.error('Artykuł jest za duży. Spróbuj zmniejszyć rozmiar obrazów lub treści.');
                return;
            }

            // Check if response is JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const text = await response.text();
                console.error('Non-JSON response:', text);
                window.toastManager.error('Serwer zwrócił nieprawidłową odpowiedź. Sprawdź logi serwera.');
                return;
            }

            const result = await response.json();
            
            if (result.success) {
                window.toastManager.success(result.message || 'Artykuł został zaktualizowany pomyślnie');
                this.closeModal('editPostModal');
                location.reload();
                
                // Wywołaj globalne odświeżenie
                if (typeof window.refreshAfterCRUD === 'function') {
                    window.refreshAfterCRUD();
                }
            } else {
                window.toastManager.error(result.error || 'Błąd podczas aktualizacji artykułu');
            }
        } catch (error) {
            console.error('Error updating post:', error);
            if (error.message.includes('Unexpected token')) {
                window.toastManager.error('Serwer zwrócił nieprawidłową odpowiedź. Sprawdź czy artykuł nie jest za duży.');
            } else {
                window.toastManager.error('Błąd podczas aktualizacji artykułu');
            }
        }
    }

    async editPost(postId) {
        try {
            // Check if we're on the posts page (has edit form elements)
            const editPostId = document.getElementById('editPostId');
            if (!editPostId) {
                console.warn('Edit form not available on this page. Opening new window...');
                window.open(`/blog/admin?edit=${postId}`, '_blank');
                return;
            }

            const url = `/api/blog/admin/posts/${postId}`;
            console.log('Fetching post data from:', url);
            
            const response = await fetch(url, {
                credentials: 'include'
            });
            
            console.log('Response status:', response.status);
            console.log('Response headers:', response.headers);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Error response:', errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                const post = result.post;
                
                // Check if edit form elements exist
                const editPostTitle = document.getElementById('editPostTitle');
                const editPostSlug = document.getElementById('editPostSlug');
                const editPostExcerpt = document.getElementById('editPostExcerpt');
                const editPostStatus = document.getElementById('editPostStatus');
                const editPostAllowComments = document.getElementById('editPostAllowComments');
                
                if (!editPostTitle || !editPostSlug || !editPostExcerpt || !editPostStatus || !editPostAllowComments) {
                    console.error('Edit form elements not found. Modal may not be loaded yet.');
                    window.toastManager.error('Formularz edycji nie jest jeszcze załadowany. Spróbuj ponownie.');
                    return;
                }
                
                // Fill edit form
                editPostId.value = post.id;
                editPostTitle.value = post.title;
                editPostSlug.value = post.slug;
                editPostExcerpt.value = post.excerpt || '';
                editPostStatus.value = post.status;
                editPostAllowComments.checked = post.allow_comments || false;
                
                // Set content in TinyMCE
                this.setTinyMCEContent('editPostContent', post.content);
                
                // Set categories
                const categoryCheckboxes = document.querySelectorAll('#editPostCategories input[type="checkbox"]');
                categoryCheckboxes.forEach(checkbox => {
                    checkbox.checked = post.categories && post.categories.some(cat => cat.id === parseInt(checkbox.value));
                });
                
                // Set tags in tag selector
                const tags = post.tags || [];
                if (this.tagSelectors.edit && typeof this.tagSelectors.edit.setTags === 'function') {
                    this.tagSelectors.edit.setTags(tags);
                }
                
                // Set featured image preview
                const currentImageDiv = document.getElementById('currentFeaturedImage');
                const currentImagePreview = document.getElementById('currentFeaturedImagePreview');
                if (post.featured_image) {
                    currentImagePreview.src = post.featured_image;
                    currentImageDiv.style.display = 'block';
                } else {
                    currentImageDiv.style.display = 'none';
                }
                
                // Load post images
                this.currentPostId = post.id;
                await this.loadPostImages(post.id);
                
                // Show modal
                const modalElement = document.getElementById('editPostModal');
                if (!modalElement) {
                    console.error('Edit modal not found in DOM');
                    window.toastManager.error('Modal edycji nie został znaleziony. Odśwież stronę i spróbuj ponownie.');
                    return;
                }
                
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
            } else {
                window.toastManager.error(result.message || 'Błąd podczas ładowania artykułu');
            }
        } catch (error) {
            console.error('Error loading post:', error);
            window.toastManager.error('Błąd podczas ładowania artykułu');
        }
    }

    async deletePost(postId) {
        window.deleteConfirmation.showSingleDelete(
            'artykuł',
            () => {
                // Continue with deletion
                performDeletePost(postId);
            },
            'artykuł'
        );
    }

    async performDeletePost(postId) {
        try {
            const response = await fetch(`/api/blog/admin/posts/${postId}`, {
                method: 'DELETE',
                credentials: 'include'
            });

            const result = await response.json();
            
            if (result.success) {
                window.toastManager.success(result.message || 'Artykuł został usunięty pomyślnie');
                location.reload();
                
                // Wywołaj globalne odświeżenie - temporarily disabled for debugging
                // if (typeof window.refreshAfterCRUD === 'function') {
                //     window.refreshAfterCRUD();
                // } else {
                //     console.warn('window.refreshAfterCRUD is not available');
                // }
            } else {
                window.toastManager.error(result.error || 'Błąd podczas usuwania artykułu');
            }
        } catch (error) {
            console.error('Error deleting post:', error);
            window.toastManager.error('Błąd podczas usuwania artykułu');
        }
    }

    closeModal(modalId) {
        const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
        if (modal) {
            modal.hide();
        }
        
        // Clear tag selectors when closing modals
        if (modalId === 'addPostModal' && this.tagSelectors.add && typeof this.tagSelectors.add.setTags === 'function') {
            this.tagSelectors.add.setTags([]);
        } else if (modalId === 'editPostModal' && this.tagSelectors.edit && typeof this.tagSelectors.edit.setTags === 'function') {
            this.tagSelectors.edit.setTags([]);
        }
    }

    // Image Management Methods
    setupImageHandlers() {
        // Add image button (edit form)
        const addImageBtn = document.getElementById('addImageBtn');
        if (addImageBtn) {
            addImageBtn.addEventListener('click', () => this.showAddImageModal());
        }

        // Save image button
        const saveImageBtn = document.getElementById('saveImageBtn');
        if (saveImageBtn) {
            saveImageBtn.addEventListener('click', () => this.saveImage());
        }

        // Image modal events
        const imageModal = document.getElementById('imageModal');
        if (imageModal) {
            imageModal.addEventListener('hidden.bs.modal', () => this.resetImageForm());
        }
    }

    showAddImageModal() {
        const modal = new bootstrap.Modal(document.getElementById('imageModal'));
        document.getElementById('imageModalTitle').textContent = 'Dodaj Obraz';
        document.getElementById('imageId').value = '';
        document.getElementById('postId').value = this.currentPostId || '';
        modal.show();
    }

    showEditImageModal(imageId, imageData) {
        const modal = new bootstrap.Modal(document.getElementById('imageModal'));
        document.getElementById('imageModalTitle').textContent = 'Edytuj Obraz';
        document.getElementById('imageId').value = imageId;
        document.getElementById('postId').value = this.currentPostId || '';
        document.getElementById('imageUrl').value = imageData.image_url || '';
        document.getElementById('imageAltText').value = imageData.alt_text || '';
        document.getElementById('imageCaption').value = imageData.caption || '';
        document.getElementById('imageOrder').value = imageData.order || 0;
    modal.show();
}

    async saveImage() {
        const form = document.getElementById('imageForm');
        const formData = new FormData(form);
        const imageId = formData.get('image_id');
        const postId = formData.get('post_id');
        const imageFile = formData.get('image_file');
        const imageUrl = formData.get('image_url');

        if (!postId) {
            window.toastManager.error('Błąd: Brak ID posta');
            return;
        }

        // Check if either file or URL is provided
        if (!imageFile && !imageUrl) {
            window.toastManager.error('Musisz podać URL obrazu lub wgrać plik');
            return;
        }
        
        // If file is provided, use FormData for upload
        if (imageFile && imageFile.size > 0) {
            try {
                let response;
                if (imageId) {
                    // Update existing image with file upload
                    response = await fetch(`/api/blog/admin/posts/${postId}/images/${imageId}`, {
                        method: 'PUT',
                        body: formData,
                        credentials: 'include'
                    });
                } else {
                    // Add new image with file upload
                    response = await fetch(`/api/blog/admin/posts/${postId}/images`, {
                        method: 'POST',
                        body: formData,
                        credentials: 'include'
                    });
                }
                
                const result = await response.json();
                
                if (result.success) {
                    window.toastManager.success(result.message);
                    this.closeModal('imageModal');
                    await this.loadPostImages(postId);
                    this.resetImageForm();
                } else {
                    window.toastManager.error(result.error || 'Błąd podczas zapisywania obrazu');
                }
            } catch (error) {
                console.error('Error saving image:', error);
                window.toastManager.error('Błąd podczas zapisywania obrazu');
            }
            return;
        }
        
        // If only URL is provided, use JSON
        const imageData = {
            image_url: imageUrl,
            alt_text: formData.get('alt_text'),
            caption: formData.get('caption'),
            order: parseInt(formData.get('order')) || 0
        };

        try {
            let response;
            if (imageId) {
                // Update existing image
                response = await fetch(`/api/blog/admin/posts/${postId}/images/${imageId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(imageData),
                    credentials: 'include'
                });
            } else {
                // Add new image
                response = await fetch(`/api/blog/admin/posts/${postId}/images`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(imageData),
                    credentials: 'include'
                });
            }

            const result = await response.json();
            
            if (result.success) {
                window.toastManager.success(result.message);
                this.closeModal('imageModal');
                await this.loadPostImages(postId);
                this.resetImageForm();
            } else {
                window.toastManager.error(result.error || 'Błąd podczas zapisywania obrazu');
            }
        } catch (error) {
            console.error('Error saving image:', error);
            window.toastManager.error('Błąd podczas zapisywania obrazu');
        }
    }

    async loadPostImages(postId) {
        try {
            const response = await fetch(`/api/blog/admin/posts/${postId}/images`, {
                credentials: 'include'
            });
            const result = await response.json();
            
            if (result.success) {
                this.renderImages(result.images, postId);
            }
        } catch (error) {
            console.error('Error loading images:', error);
        }
    }

    renderImages(images, postId) {
        const container = document.getElementById('editPostImages');
        if (!container) return;

        if (images.length === 0) {
            container.innerHTML = '';
            return;
        }

        container.innerHTML = images.map(image => `
            <div class="image-item" data-image-id="${image.id}">
                <div class="image-order">${image.order}</div>
                <button class="image-drag-handle" title="Przeciągnij aby zmienić kolejność">
                    <i class="fas fa-grip-vertical"></i>
                </button>
                <img src="${image.image_url}" alt="${image.alt_text || ''}" class="image-preview" 
                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgdmlld0JveD0iMCAwIDIwMCAxNTAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMTUwIiBmaWxsPSIjRjhGQUZDIi8+CjxwYXRoIGQ9Ik04NSAxMDBMMTAwIDg1TDEyMCAxMDBMMTQwIDgwTDE2MCAxMDBWMTMwSDgwVjEwMFoiIGZpbGw9IiNEMUQ1REIiLz4KPHN2Zz4K'">
                <div class="image-info">
                    <div class="image-title">${image.alt_text || 'Brak opisu'}</div>
                    <div class="image-caption">${image.caption || ''}</div>
                    <div class="image-actions">
                        <button class="btn btn-sm admin-btn-outline" onclick="window.blogPostsManager.showEditImageModal(${image.id}, ${JSON.stringify(image).replace(/"/g, '&quot;')})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm admin-btn-danger" onclick="window.blogPostsManager.deleteImage(${image.id}, ${postId})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async deleteImage(imageId, postId) {
        window.deleteConfirmation.showSingleDelete(
            'obraz',
            () => {
                // Continue with deletion
                performDeleteImage(imageId);
            },
            'obraz'
        );
    }

    async performDeleteImage(imageId, postId) {
        try {
            const response = await fetch(`/api/blog/admin/posts/${postId}/images/${imageId}`, {
                method: 'DELETE',
                credentials: 'include'
            });

            const result = await response.json();
            
            if (result.success) {
                window.toastManager.success(result.message);
                await this.loadPostImages(postId);
            } else {
                window.toastManager.error(result.error);
            }
        } catch (error) {
            console.error('Error deleting image:', error);
            window.toastManager.error('Błąd podczas usuwania obrazu');
        }
    }

    resetImageForm() {
        document.getElementById('imageForm').reset();
        document.getElementById('imageId').value = '';
        document.getElementById('postId').value = '';
    }

    // TinyMCE helper functions
    setTinyMCEContent(editorId, content) {
        try {
            const editor = tinymce.get(editorId);
            if (editor) {
                if (editor.initialized) {
                    editor.setContent(content || '');
                } else {
                    editor.on('init', () => {
                        editor.setContent(content || '');
                    });
                }
            } else {
                // Fallback: set content in textarea
                const textarea = document.getElementById(editorId);
                if (textarea) {
                    textarea.value = content || '';
                }
            }
        } catch (error) {
            console.error('Error setting TinyMCE content:', error);
            // Fallback: set content in textarea
            const textarea = document.getElementById(editorId);
            if (textarea) {
                textarea.value = content || '';
            }
        }
    }

    getTinyMCEContent(editorId) {
        try {
            const editor = tinymce.get(editorId);
            if (editor && editor.initialized) {
                return editor.getContent();
            } else {
                // Fallback: get content from textarea
                const textarea = document.getElementById(editorId);
                return textarea ? textarea.value : '';
            }
        } catch (error) {
            console.error('Error getting TinyMCE content:', error);
            // Fallback: get content from textarea
            const textarea = document.getElementById(editorId);
            return textarea ? textarea.value : '';
        }
    }

    // Toast notifications are now handled by window.toastManager
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.blogPostsManager = new BlogPostsManager();
});

// Also try to initialize immediately if DOM is already loaded
if (document.readyState === 'loading') {
    // DOM is still loading, wait for DOMContentLoaded
} else {
    // DOM is already loaded
    window.blogPostsManager = new BlogPostsManager();
}

// Global editPost function
function editPost(postId) {
    if (window.blogPostsManager && typeof window.blogPostsManager.editPost === 'function') {
        window.blogPostsManager.editPost(postId);
    } else {
        console.error('BlogPostsManager not available');
    }
}

// Check for edit parameter in URL or template variable
document.addEventListener('DOMContentLoaded', function() {
    // Check URL parameter first
    const urlParams = new URLSearchParams(window.location.search);
    const editPostId = urlParams.get('edit');
    
    // Check template variable
    const templateEditPostId = window.editPostId;
    
    const postIdToEdit = editPostId || templateEditPostId;
    
    if (postIdToEdit) {
        // Automatically open edit modal for the specified post
        setTimeout(() => {
            editPost(parseInt(postIdToEdit));
        }, 1000); // Wait for posts to load
    }
});