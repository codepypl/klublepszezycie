// Blog Comments Management
class BlogCommentsManager {
    constructor() {
        this.bulkDeleteManager = null;
        this.init();
    }

    init() {
        // Initialize bulk delete manager
        this.bulkDeleteManager = new BulkDeleteManager({
            itemSelector: '.comment-checkbox',
            selectAllSelector: '#selectAll',
            bulkDeleteBtnSelector: '#bulkDeleteBtn',
            deleteEndpoint: '/api/blog/comments/bulk-delete',
            getSelectedIds: () => this.getSelectedCommentIds(),
            onDeleteSuccess: () => this.loadComments()
        });

        // Bind events
        this.bindEvents();
    }

    bindEvents() {
        // Edit comment form
        const editForm = document.getElementById('editCommentForm');
        if (editForm) {
            editForm.addEventListener('submit', (e) => this.handleEditComment(e));
        }
    }

    getSelectedCommentIds() {
        const checkboxes = document.querySelectorAll('.comment-checkbox:checked');
        return Array.from(checkboxes).map(cb => cb.value);
    }

    async loadComments(page = 1) {
        try {
            const response = await fetch(`/blog/admin/comments?page=${page}`);
            if (response.ok) {
                window.location.href = `/blog/admin/comments?page=${page}`;
            }
        } catch (error) {
            console.error('Error loading comments:', error);
            window.toastManager.show('Błąd podczas ładowania komentarzy', 'error');
        }
    }

    async handleEditComment(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);
        const commentId = data.id;
        
        // Convert boolean fields
        data.is_approved = document.getElementById('editCommentIsApproved').checked;

        try {
            const response = await fetch(`/api/blog/comments/${commentId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            
            if (result.success) {
                window.toastManager.show(result.message || 'Komentarz został zaktualizowany pomyślnie', 'success');
                this.closeModal('editCommentModal');
                this.loadComments();
            } else {
                window.toastManager.show(result.message || 'Błąd podczas aktualizacji komentarza', 'error');
            }
        } catch (error) {
            console.error('Error updating comment:', error);
            window.toastManager.show('Błąd podczas aktualizacji komentarza', 'error');
        }
    }

    async editComment(commentId) {
        try {
            const response = await fetch(`/api/blog/comments/${commentId}`);
            const result = await response.json();
            
            if (result.success) {
                const comment = result.comment;
                
                // Fill edit form
                document.getElementById('editCommentId').value = comment.id;
                document.getElementById('editCommentAuthorName').value = comment.author_name;
                document.getElementById('editCommentAuthorEmail').value = comment.author_email;
                document.getElementById('editCommentAuthorWebsite').value = comment.author_website || '';
                document.getElementById('editCommentContent').value = comment.content;
                document.getElementById('editCommentIsApproved').checked = comment.is_approved;
                
                // Show modal
                const modal = new bootstrap.Modal(document.getElementById('editCommentModal'));
                modal.show();
            } else {
                window.toastManager.show(result.message || 'Błąd podczas ładowania komentarza', 'error');
            }
        } catch (error) {
            console.error('Error loading comment:', error);
            window.toastManager.show('Błąd podczas ładowania komentarza', 'error');
        }
    }

    async deleteComment(commentId) {
        if (!confirm('Czy na pewno chcesz usunąć ten komentarz?')) {
            return;
        }

        try {
            const response = await fetch(`/api/blog/comments/${commentId}`, {
                method: 'DELETE'
            });

            const result = await response.json();
            
            if (result.success) {
                window.toastManager.show(result.message || 'Komentarz został usunięty pomyślnie', 'success');
                this.loadComments();
            } else {
                window.toastManager.show(result.message || 'Błąd podczas usuwania komentarza', 'error');
            }
        } catch (error) {
            console.error('Error deleting comment:', error);
            window.toastManager.show('Błąd podczas usuwania komentarza', 'error');
        }
    }

    async approveComment(commentId) {
        try {
            const response = await fetch(`/api/blog/comments/${commentId}/approve`, {
                method: 'POST'
            });

            const result = await response.json();
            
            if (result.success) {
                window.toastManager.show(result.message || 'Komentarz został zatwierdzony pomyślnie', 'success');
                this.loadComments();
            } else {
                window.toastManager.show(result.message || 'Błąd podczas zatwierdzania komentarza', 'error');
            }
        } catch (error) {
            console.error('Error approving comment:', error);
            window.toastManager.show('Błąd podczas zatwierdzania komentarza', 'error');
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
function editComment(commentId) {
    if (window.blogCommentsManager) {
        window.blogCommentsManager.editComment(commentId);
    }
}

function deleteComment(commentId) {
    if (window.blogCommentsManager) {
        window.blogCommentsManager.deleteComment(commentId);
    }
}

function approveComment(commentId) {
    if (window.blogCommentsManager) {
        window.blogCommentsManager.approveComment(commentId);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.blogCommentsManager = new BlogCommentsManager();
});

