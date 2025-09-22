/**
 * SEO Management JavaScript
 * Handles SEO settings CRUD operations, form validation, and character counting
 */

// Character counters
function updateCount(input, counter, maxLength) {
    const remaining = maxLength - input.value.length;
    counter.textContent = remaining;
    if (remaining < 0) {
        counter.classList.add('text-danger');
    } else {
        counter.classList.remove('text-danger');
    }
}

// Add SEO
function addSeo() {
    const form = document.getElementById('addSeoForm');
    const formData = new FormData(form);
    
    // Convert FormData to JSON
    const jsonData = {
        page_type: formData.get('page_type'),
        title: formData.get('page_title'),  // Map page_title to title
        description: formData.get('meta_description'),  // Map meta_description to description
        keywords: formData.get('meta_keywords'),  // Map meta_keywords to keywords
        og_title: formData.get('og_title'),
        og_description: formData.get('og_description'),
        og_image: formData.get('og_image'),
        og_type: formData.get('og_type'),
        twitter_card: formData.get('twitter_card'),
        twitter_title: formData.get('twitter_title'),
        twitter_description: formData.get('twitter_description'),
        canonical_url: formData.get('canonical_url'),
        structured_data: formData.get('structured_data'),
        is_active: formData.get('is_active') === 'on'
    };
    
    fetch('/api/seo', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify(jsonData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.toastManager.success('Ustawienia SEO zostały dodane pomyślnie!');
            const modal = bootstrap.Modal.getInstance(document.getElementById('addSeoModal'));
            modal.hide();
            location.reload();
        } else {
            window.toastManager.error('Błąd podczas dodawania: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        window.toastManager.error('Wystąpił błąd podczas dodawania ustawień SEO');
    });
}

// Edit SEO
function editSeo(id, pageType, pageTitle, metaDescription, ogTitle, ogDescription, ogImage, twitterCard, twitterTitle, twitterDescription, structuredData) {
    document.getElementById('edit_id').value = id;
    document.getElementById('edit_page_type').value = pageType;
    document.getElementById('edit_page_title').value = pageTitle;
    document.getElementById('edit_meta_description').value = metaDescription;
    document.getElementById('edit_meta_keywords').value = ''; // Will be filled from API
    document.getElementById('edit_og_title').value = ogTitle;
    document.getElementById('edit_og_description').value = ogDescription;
    document.getElementById('edit_og_image').value = ogImage;
    document.getElementById('edit_og_type').value = 'website'; // Default value
    document.getElementById('edit_twitter_card').value = twitterCard;
    document.getElementById('edit_twitter_title').value = twitterTitle;
    document.getElementById('edit_twitter_description').value = twitterDescription;
    document.getElementById('edit_canonical_url').value = ''; // Will be filled from API
    document.getElementById('edit_structured_data').value = structuredData;
    
    // Update character counts
    updateCount(document.getElementById('edit_page_title'), document.getElementById('edit_title_count'), 60);
    updateCount(document.getElementById('edit_meta_description'), document.getElementById('edit_desc_count'), 160);
    
    new bootstrap.Modal(document.getElementById('editSeoModal')).show();
}

// Save SEO
function saveSeo() {
    const form = document.getElementById('editSeoForm');
    const formData = new FormData(form);
    
    // Convert FormData to JSON
    const jsonData = {
        title: formData.get('page_title'),  // Map page_title to title
        description: formData.get('meta_description'),  // Map meta_description to description
        keywords: formData.get('meta_keywords'),  // Map meta_keywords to keywords
        og_title: formData.get('og_title'),
        og_description: formData.get('og_description'),
        og_image: formData.get('og_image'),
        og_type: formData.get('og_type'),
        twitter_card: formData.get('twitter_card'),
        twitter_title: formData.get('twitter_title'),
        twitter_description: formData.get('twitter_description'),
        canonical_url: formData.get('canonical_url'),
        structured_data: formData.get('structured_data'),
        is_active: formData.get('is_active') === 'on'
    };
    
    const seoId = formData.get('id');
    
    fetch(`/api/seo/${seoId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify(jsonData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.toastManager.success('Ustawienia SEO zostały zaktualizowane pomyślnie!');
            const modal = bootstrap.Modal.getInstance(document.getElementById('editSeoModal'));
            modal.hide();
            location.reload();
        } else {
            window.toastManager.error('Błąd podczas zapisywania: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        window.toastManager.error('Wystąpił błąd podczas zapisywania zmian');
    });
}

// Delete SEO
function deleteSeo(id) {
    if (confirm('Czy na pewno chcesz usunąć te ustawienia SEO?')) {
        fetch(`/api/seo/${id}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.toastManager.success('Ustawienia SEO zostały usunięte pomyślnie!');
                location.reload();
            } else {
                window.toastManager.error('Błąd podczas usuwania: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            window.toastManager.error('Wystąpił błąd podczas usuwania ustawień SEO');
        });
    }
}

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (!window.location.pathname.includes('seo')) {
        console.log('Not on SEO page, skipping initialization');
        return;
    }
    
    // Form submissions
    const addSeoForm = document.getElementById('addSeoForm');
    if (addSeoForm) {
        addSeoForm.addEventListener('submit', function(e) {
            e.preventDefault();
            addSeo();
        });
    }
    
    const editSeoForm = document.getElementById('editSeoForm');
    if (editSeoForm) {
        editSeoForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveSeo();
        });
    }
    
    // Character count listeners
    const pageTitle = document.getElementById('page_title');
    if (pageTitle) {
        pageTitle.addEventListener('input', function() {
            updateCount(this, document.getElementById('title_count'), 60);
        });
    }
    
    const metaDescription = document.getElementById('meta_description');
    if (metaDescription) {
        metaDescription.addEventListener('input', function() {
            updateCount(this, document.getElementById('desc_count'), 160);
        });
    }
    
    const editPageTitle = document.getElementById('edit_page_title');
    if (editPageTitle) {
        editPageTitle.addEventListener('input', function() {
            updateCount(this, document.getElementById('edit_title_count'), 60);
        });
    }
    
    const editMetaDescription = document.getElementById('edit_meta_description');
    if (editMetaDescription) {
        editMetaDescription.addEventListener('input', function() {
            updateCount(this, document.getElementById('edit_desc_count'), 160);
        });
    }
    
    // Sidebar toggle functionality
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            const sidebar = document.getElementById('sidebar');
            if (sidebar) {
                sidebar.classList.toggle('show');
            }
        });
    }
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
        const sidebar = document.getElementById('sidebar');
        const sidebarToggle = document.getElementById('sidebarToggle');
        if (window.innerWidth < 992 && 
            sidebar && sidebarToggle &&
            !sidebar.contains(event.target) && 
            !sidebarToggle.contains(event.target)) {
            sidebar.classList.remove('show');
        }
    });
});
