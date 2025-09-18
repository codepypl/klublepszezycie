// Blog Comments Management
class BlogCommentsManager {
    constructor() {
        this.bulkDeleteManager = null;
        this.init();
    }

    init() {
        // Bulk delete is now handled by the BulkDeleteManager in the template
        // Bind events
        this.bindEvents();
    }

    bindEvents() {
        // Reject comment form
        const rejectForm = document.getElementById('rejectCommentForm');
        if (rejectForm) {
            rejectForm.addEventListener('submit', (e) => this.handleRejectComment(e));
        }
    }

    getSelectedCommentIds() {
        const checkboxes = document.querySelectorAll('input[name="itemIds"]:checked');
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

    async handleRejectComment(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);
        const commentId = data.comment_id;
        const reason = data.reason.trim();

        if (!reason) {
            window.toastManager.show('Powód odrzucenia jest wymagany', 'error');
            return;
        }

        try {
            const response = await fetch(`/api/blog/comments/${commentId}/reject`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ reason: reason })
            });

            const result = await response.json();
            
            if (result.success) {
                window.toastManager.show(result.message || 'Komentarz został odrzucony pomyślnie', 'success');
                this.closeModal('rejectCommentModal');
                this.loadComments();
            } else {
                window.toastManager.show(result.message || 'Błąd podczas odrzucania komentarza', 'error');
            }
        } catch (error) {
            console.error('Error rejecting comment:', error);
            window.toastManager.show('Błąd podczas odrzucania komentarza', 'error');
        }
    }

    async viewComment(commentId) {
        try {
            const response = await fetch(`/api/blog/comments/${commentId}`);
            const result = await response.json();
            
            if (result.success) {
                const comment = result.comment;
                
                // Build comment details HTML
                let detailsHtml = `
                    <div class="row">
                        <div class="col-md-8">
                            <h6 class="text-primary mb-3">
                                <i class="fas fa-comment me-2"></i>Treść komentarza
                            </h6>
                            <div class="border rounded p-3 bg-light mb-4">
                                <p class="mb-0">${comment.content}</p>
                            </div>
                            
                            <h6 class="text-primary mb-3">
                                <i class="fas fa-user me-2"></i>Informacje o autorze
                            </h6>
                            <div class="row mb-4">
                                <div class="col-md-6">
                                    <strong>Imię i nazwisko:</strong><br>
                                    <span class="text-muted">${comment.author_name}</span>
                                </div>
                                <div class="col-md-6">
                                    <strong>Email:</strong><br>
                                    <a href="mailto:${comment.author_email}" class="text-decoration-none">${comment.author_email}</a>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-4">
                            <h6 class="text-primary mb-3">
                                <i class="fas fa-info-circle me-2"></i>Szczegóły techniczne
                            </h6>
                            <div class="mb-3">
                                <strong>Data utworzenia:</strong><br>
                                <span class="text-muted">${comment.created_at ? new Date(comment.created_at).toLocaleString('pl-PL') : 'Brak'}</span>
                            </div>
                            <div class="mb-3">
                                <strong>Adres IP:</strong><br>
                                <span class="text-muted">${comment.ip_address || 'Nieznany'}</span>
                            </div>
                            <div class="mb-3">
                                <strong>Przeglądarka:</strong><br>
                                <span class="text-muted">${comment.browser || 'Nieznana'}</span>
                            </div>
                            <div class="mb-3">
                                <strong>System operacyjny:</strong><br>
                                <span class="text-muted">${comment.operating_system || 'Nieznany'}</span>
                            </div>
                            <div class="mb-3">
                                <strong>Lokalizacja:</strong><br>
                                <span class="text-muted">${comment.location_city || ''}${comment.location_city && comment.location_country ? ', ' : ''}${comment.location_country || 'Nieznana'}</span>
                            </div>
                        </div>
                    </div>
                `;
                
                // If it's a reply, show parent comment
                if (comment.parent_id) {
                    try {
                        const parentResponse = await fetch(`/api/blog/comments/${comment.parent_id}`);
                        const parentResult = await parentResponse.json();
                        
                        if (parentResult.success) {
                            const parentComment = parentResult.comment;
                            detailsHtml += `
                                <hr class="my-4">
                                <h6 class="text-secondary mb-3">
                                    <i class="fas fa-reply me-2"></i>Odpowiedź na komentarz
                                </h6>
                                <div class="border-start border-3 border-secondary ps-3">
                                    <div class="mb-2">
                                        <strong>Autor:</strong> ${parentComment.author_name}<br>
                                        <strong>Data:</strong> ${parentComment.created_at ? new Date(parentComment.created_at).toLocaleString('pl-PL') : 'Brak'}
                                    </div>
                                    <div class="bg-light p-2 rounded">
                                        <small class="text-muted">${parentComment.content}</small>
                                    </div>
                                </div>
                            `;
                        }
                    } catch (error) {
                        console.error('Error loading parent comment:', error);
                    }
                }
                
                // Fill modal content
                document.getElementById('commentDetails').innerHTML = detailsHtml;
                
                // Show modal
                const modal = new bootstrap.Modal(document.getElementById('viewCommentModal'));
                modal.show();
            } else {
                window.toastManager.show(result.message || 'Błąd podczas ładowania komentarza', 'error');
            }
        } catch (error) {
            console.error('Error loading comment:', error);
            window.toastManager.show('Błąd podczas ładowania komentarza', 'error');
        }
    }

    async rejectComment(commentId) {
        // Fill reject form
        document.getElementById('rejectCommentId').value = commentId;
        document.getElementById('rejectReason').value = '';
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('rejectCommentModal'));
        modal.show();
    }

    closeModal(modalId) {
        const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
        if (modal) {
            modal.hide();
        }
    }
}

// Global functions for onclick handlers

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

function rejectComment(commentId) {
    if (window.blogCommentsManager) {
        window.blogCommentsManager.rejectComment(commentId);
    }
}

function viewComment(commentId) {
    if (window.blogCommentsManager) {
        window.blogCommentsManager.viewComment(commentId);
    }
}

function confirmReject() {
    if (window.blogCommentsManager) {
        const form = document.getElementById('rejectCommentForm');
        if (form) {
            form.dispatchEvent(new Event('submit'));
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.blogCommentsManager = new BlogCommentsManager();
});

