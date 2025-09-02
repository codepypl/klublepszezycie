// Pages Management JavaScript for Lepsze Życie Club

// Toast notification system
class ToastManager {
    constructor() {
        this.container = this.createToastContainer();
    }

    createToastContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 20px;
                z-index: 9999;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
        return container;
    }

    show(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${this.getIcon(type)} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        this.container.appendChild(toast);
        
        // Initialize Bootstrap toast
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: duration
        });
        
        bsToast.show();
        
        // Remove from DOM after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    getIcon(type) {
        const icons = {
            'success': 'check-circle',
            'danger': 'exclamation-triangle',
            'warning': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    success(message, duration = 5000) {
        this.show(message, 'success', duration);
    }

    error(message, duration = 7000) {
        this.show(message, 'danger', duration);
    }

    warning(message, duration = 6000) {
        this.show(message, 'warning', duration);
    }

    info(message, duration = 5000) {
        this.show(message, 'info', duration);
    }
}

// Initialize toast manager
const toastManager = new ToastManager();

// Pages management functions
class PagesManager {
    constructor() {
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Form submissions
        const addPageForm = document.getElementById('addPageForm');
        const editPageForm = document.getElementById('editPageForm');
        
        if (addPageForm) {
            addPageForm.addEventListener('submit', (e) => this.handleAddPage(e));
        }
        
        if (editPageForm) {
            editPageForm.addEventListener('submit', (e) => this.handleEditPage(e));
        }
    }

    // Initialize TinyMCE
    initTinyMCE() {
        if (typeof tinymce !== 'undefined') {
            tinymce.init({
                selector: '#pageContent, #editPageContent',
                height: 400,
                plugins: 'anchor autolink charmap codesample emoticons image link lists media searchreplace table visualblocks wordcount checklist mediaembed casechange export formatpainter pageembed linkchecker a11ychecker tinymcespellchecker permanentpen powerpaste advtable advcode editimage tinycomments tableofcontents footnotes mergetags autocorrect typography inlinecss',
                toolbar: 'undo redo | blocks fontfamily fontsize | bold italic underline strikethrough | link image media table mergetags | addcomment showcomments | spellcheckdialog a11ycheck typography | align lineheight | checklist numlist bullist indent outdent | emoticons charmap | removeformat',
                tinycomments_mode: 'embedded',
                tinycomments_author: 'Author name',
                mergetags_list: [
                    { value: 'First.Name', title: 'First Name' },
                    { value: 'Email', title: 'Email' },
                ],
                ai_request: (request, respondWith) => respondWith.string(() => Promise.reject("See docs to implement AI Assistant")),
                setup: function(editor) {
                    console.log('TinyMCE initialized for:', editor.id);
                },
                init_instance_callback: function(editor) {
                    console.log('TinyMCE instance ready for:', editor.id);
                }
            });
        }
    }

    // Helper function to check if TinyMCE is ready
    isTinyMCEReady(editorId) {
        return tinymce.get(editorId) && tinymce.get(editorId).initialized;
    }

    loadPages() {
        fetch('/admin/api/pages')
            .then(response => {
                if (!response.ok) {
                    if (response.status === 401 || response.status === 403) {
                        throw new Error('Brak autoryzacji. Zaloguj się ponownie.');
                    }
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    this.displayPages(data.pages);
                    this.updateStats();
                } else {
                    console.error('Error loading pages:', data.error);
                    toastManager.error('Błąd podczas ładowania podstron: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (error.message.includes('Brak autoryzacji')) {
                    toastManager.error('Sesja wygasła. Zaloguj się ponownie.');
                    window.location.href = '/admin/login';
                } else {
                    toastManager.error('Wystąpił błąd podczas ładowania podstron');
                }
            });
    }

    displayPages(pages) {
        const tbody = document.getElementById('pagesTableBody');
        tbody.innerHTML = '';

        pages.forEach(page => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><span class="badge admin-badge admin-badge-primary">${page.order}</span></td>
                <td><strong>${page.title}</strong></td>
                <td><code>${page.slug}</code></td>
                <td>
                    <span class="badge admin-badge admin-badge-${this.getStatusBadgeClass(page.status)}">
                        ${this.getStatusText(page.status)}
                    </span>
                </td>
                <td>${this.formatDate(page.created_at)}</td>
                <td>${this.formatDate(page.updated_at)}</td>
                <td>
                    <div class="btn-group" role="group">
                        <button class="btn btn-sm admin-btn-outline" onclick="editPage(${page.id})" title="Edytuj podstronę">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm admin-btn-danger" onclick="deletePage(${page.id})" title="Usuń podstronę">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    getStatusBadgeClass(status) {
        switch(status) {
            case 'published': return 'success';
            case 'draft': return 'warning';
            case 'archived': return 'secondary';
            default: return 'secondary';
        }
    }

    getStatusText(status) {
        switch(status) {
            case 'published': return 'Opublikowana';
            case 'draft': return 'Szkic';
            case 'archived': return 'Zarchiwizowana';
            default: return status;
        }
    }

    formatDate(dateString) {
        if (!dateString) return 'Brak';
        const date = new Date(dateString);
        return date.toLocaleDateString('pl-PL');
    }

    updateStats() {
        fetch('/admin/api/pages')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    const pages = data.pages;
                    document.getElementById('totalPages').textContent = pages.length;
                    document.getElementById('publishedPages').textContent = pages.filter(p => p.status === 'published').length;
                    document.getElementById('activePages').textContent = pages.filter(p => p.status === 'published').length;
                    document.getElementById('draftPages').textContent = pages.filter(p => p.status === 'draft').length;
                }
            })
            .catch(error => {
                console.error('Error updating stats:', error);
            });
    }

    showAddPageModal() {
        document.getElementById('addPageForm').reset();
        const modal = new bootstrap.Modal(document.getElementById('addPageModal'));
        modal.show();
    }

    editPage(pageId) {
        fetch(`/admin/api/pages/${pageId}`)
            .then(response => {
                if (!response.ok) {
                    if (response.status === 401 || response.status === 403) {
                        throw new Error('Brak autoryzacji. Zaloguj się ponownie.');
                    }
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    const page = data.page;
                    document.getElementById('editPageId').value = page.id;
                    document.getElementById('editPageTitle').value = page.title;
                    document.getElementById('editPageSlug').value = page.slug;
                    document.getElementById('editPageOrder').value = page.order || 0;
                    document.getElementById('editPageActive').checked = page.is_active;
                    document.getElementById('editPagePublished').checked = page.is_published;
                    document.getElementById('editPageMetaDescription').value = page.meta_description || '';
                    
                    // Update TinyMCE content
                    if (tinymce.get('editPageContent')) {
                        tinymce.get('editPageContent').setContent(page.content || '');
                    }
                    
                    // Show modal
                    const modal = new bootstrap.Modal(document.getElementById('editPageModal'));
                    modal.show();
                } else {
                    toastManager.error('Błąd podczas ładowania strony: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (error.message.includes('Brak autoryzacji')) {
                    toastManager.error('Sesja wygasła. Zaloguj się ponownie.');
                    window.location.href = '/admin/login';
                } else {
                    toastManager.error('Wystąpił błąd podczas ładowania strony');
                }
            });
    }

    deletePage(pageId) {
        if (confirm('Czy na pewno chcesz usunąć tę podstronę? Tej operacji nie można cofnąć.')) {
            fetch(`/admin/api/pages?id=${pageId}`, {
                method: 'DELETE'
            })
            .then(response => {
                if (!response.ok) {
                    if (response.status === 401 || response.status === 403) {
                        throw new Error('Brak autoryzacji. Zaloguj się ponownie.');
                    }
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    toastManager.success('Podstrona została usunięta pomyślnie!');
                    this.loadPages();
                } else {
                    toastManager.error('Błąd podczas usuwania: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (error.message.includes('Brak autoryzacji')) {
                    toastManager.error('Sesja wygasła. Zaloguj się ponownie.');
                    window.location.href = '/admin/login';
                } else {
                    toastManager.error('Wystąpił błąd podczas usuwania podstrony');
                }
            });
        }
    }

    handleAddPage(e) {
        e.preventDefault();
        
        // Validate required fields
        const title = document.getElementById('pageTitle').value.trim();
        const slug = document.getElementById('pageSlug').value.trim();
        
        if (!title) {
            toastManager.warning('Proszę wprowadzić tytuł podstrony');
            document.getElementById('pageTitle').focus();
            return;
        }
        
        if (!slug) {
            toastManager.warning('Proszę wprowadzić slug podstrony');
            document.getElementById('pageSlug').focus();
            return;
        }
        
        // Check if TinyMCE is ready
        if (!this.isTinyMCEReady('pageContent')) {
            toastManager.warning('Edytor treści nie jest jeszcze gotowy. Proszę poczekać chwilę i spróbować ponownie.');
            return;
        }
        
        const content = tinymce.get('pageContent').getContent().trim();
        if (!content) {
            toastManager.warning('Proszę wprowadzić treść podstrony');
            tinymce.get('pageContent').focus();
            return;
        }
        
        const formData = new FormData(e.target);
        formData.append('content', content);
        // Always send checkbox values as strings
        formData.set('is_active', document.getElementById('pageActive').checked ? 'true' : 'false');
        formData.set('is_published', document.getElementById('pagePublished').checked ? 'true' : 'false');
        // Add order field
        formData.set('order', document.getElementById('pageOrder').value || 0);
        
        fetch('/admin/api/pages', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                if (response.status === 401 || response.status === 403) {
                    throw new Error('Brak autoryzacji. Zaloguj się ponownie.');
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                toastManager.success('Podstrona została utworzona pomyślnie!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('addPageModal'));
                modal.hide();
                this.loadPages();
            } else {
                toastManager.error('Błąd podczas tworzenia: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (error.message.includes('Brak autoryzacji')) {
                toastManager.error('Sesja wygasła. Zaloguj się ponownie.');
                window.location.href = '/admin/login';
            } else {
                toastManager.error('Wystąpił błąd podczas tworzenia podstrony');
            }
        });
    }

    handleEditPage(e) {
        e.preventDefault();
        
        // Validate required fields
        const title = document.getElementById('editPageTitle').value.trim();
        const slug = document.getElementById('editPageSlug').value.trim();
        
        if (!title) {
            toastManager.warning('Proszę wprowadzić tytuł podstrony');
            document.getElementById('editPageTitle').focus();
            return;
        }
        
        if (!slug) {
            toastManager.warning('Proszę wprowadzić slug podstrony');
            document.getElementById('editPageSlug').focus();
            return;
        }
        
        // Check if TinyMCE is ready
        if (!this.isTinyMCEReady('editPageContent')) {
            toastManager.warning('Edytor treści nie jest jeszcze gotowy. Proszę poczekać chwilę i spróbować ponownie.');
            return;
        }
        
        const content = tinymce.get('editPageContent').getContent().trim();
        if (!content) {
            toastManager.warning('Proszę wprowadzić treść podstrony');
            tinymce.get('editPageContent').focus();
            return;
        }
        
        const formData = new FormData(e.target);
        formData.append('content', content);
        // Always send checkbox values as strings
        formData.set('is_active', document.getElementById('editPageActive').checked ? 'true' : 'false');
        formData.set('is_published', document.getElementById('editPagePublished').checked ? 'true' : 'false');
        // Add order field
        formData.set('order', document.getElementById('editPageOrder').value || 0);
        
        fetch('/admin/api/pages', {
            method: 'PUT',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                if (response.status === 401 || response.status === 403) {
                    throw new Error('Brak autoryzacji. Zaloguj się ponownie.');
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                toastManager.success('Podstrona została zaktualizowana pomyślnie!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('editPageModal'));
                modal.hide();
                this.loadPages();
            } else {
                toastManager.error('Błąd podczas aktualizacji: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (error.message.includes('Brak autoryzacji')) {
                toastManager.error('Sesja wygasła. Zaloguj się ponownie.');
                window.location.href = '/admin/login';
            } else {
                toastManager.error('Wystąpił błąd podczas aktualizacji podstrony');
            }
        });
    }
}

// Global functions for backward compatibility
function showAddPageModal() {
    window.pagesManager.showAddPageModal();
}

function editPage(pageId) {
    window.pagesManager.editPage(pageId);
}

function deletePage(pageId) {
    window.pagesManager.deletePage(pageId);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.pagesManager = new PagesManager();
    
    // Initialize TinyMCE
    window.pagesManager.initTinyMCE();
    
    // Load pages and update stats
    window.pagesManager.loadPages();
});
