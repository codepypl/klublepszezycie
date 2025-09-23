// Admin Sections JavaScript for Lepsze Życie Club

// Global variables
let pillarsData = [];
let floatingCardsData = [];
let maxPillarsCount = 4;
let maxFloatingCardsCount = 3;

// Toast manager is loaded globally from utils/toast.js

// Sections management functions
class SectionsManager {
    constructor() {
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Add Section Modal
        const sectionEnablePillars = document.getElementById('sectionEnablePillars');
        const sectionEnableFloatingCards = document.getElementById('sectionEnableFloatingCards');
        const pillarsConfig = document.getElementById('pillarsConfig');
        const floatingCardsConfig = document.getElementById('floatingCardsConfig');
        
        if (sectionEnablePillars) {
            sectionEnablePillars.addEventListener('change', function() {
                pillarsConfig.style.display = this.checked ? 'block' : 'none';
            });
        }
        
        if (sectionEnableFloatingCards) {
            sectionEnableFloatingCards.addEventListener('change', function() {
                floatingCardsConfig.style.display = this.checked ? 'block' : 'none';
            });
        }
        
        // Edit Section Modal
        const editSectionEnablePillars = document.getElementById('editSectionEnablePillars');
        const editSectionEnableFloatingCards = document.getElementById('editSectionEnableFloatingCards');
        const editPillarsConfig = document.getElementById('editPillarsConfig');
        const editFloatingCardsConfig = document.getElementById('editFloatingCardsConfig');
        
        if (editSectionEnablePillars) {
            editSectionEnablePillars.addEventListener('change', function() {
                editPillarsConfig.style.display = this.checked ? 'block' : 'none';
            });
        }
        
        if (editSectionEnableFloatingCards) {
            editSectionEnableFloatingCards.addEventListener('change', function() {
                editFloatingCardsConfig.style.display = this.checked ? 'block' : 'none';
            });
        }

        // Form submissions
        const addSectionForm = document.getElementById('addSectionForm');
        const editSectionForm = document.getElementById('editSectionForm');
        
        if (addSectionForm) {
            addSectionForm.addEventListener('submit', (e) => this.handleAddSection(e));
        }
        
        if (editSectionForm) {
            editSectionForm.addEventListener('submit', (e) => this.handleEditSection(e));
        }
    }

    showAddSectionModal() {
        document.getElementById('addSectionForm').reset();
        const modal = new bootstrap.Modal(document.getElementById('addSectionModal'));
        modal.show();
    }

    editSection(sectionId) {
        fetch(`/api/sections/${sectionId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const section = data.section;
                    document.getElementById('editSectionId').value = section.id;
                    document.getElementById('editSectionName').value = section.name;
                    document.getElementById('editSectionTitle').value = section.title || '';
                    document.getElementById('editSectionSubtitle').value = section.subtitle || '';
                    document.getElementById('editSectionOrder').value = section.order || 1;
                    document.getElementById('editSectionActive').checked = section.is_active;
                    
                    // Set content in Quill
                    if (window.quillInstances && window.quillInstances['editSectionContent']) {
                        window.quillInstances['editSectionContent'].root.innerHTML = section.content || '';
                    }
                    
                    // Pillars configuration
                    document.getElementById('editSectionEnablePillars').checked = section.enable_pillars || false;
                    document.getElementById('editSectionPillarsCount').value = section.pillars_count || 4;
                    document.getElementById('editPillarsConfig').style.display = section.enable_pillars ? 'block' : 'none';
                    
                    // Floating cards configuration
                    document.getElementById('editSectionEnableFloatingCards').checked = section.enable_floating_cards || false;
                    document.getElementById('editSectionFloatingCardsCount').value = section.floating_cards_count || 3;
                    document.getElementById('editFloatingCardsConfig').style.display = section.enable_floating_cards ? 'block' : 'none';
                    
                    const modal = new bootstrap.Modal(document.getElementById('editSectionModal'));
                    modal.show();
                } else {
                    window.toastManager.error('Błąd podczas ładowania sekcji: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                window.toastManager.error('Wystąpił błąd podczas ładowania sekcji');
            });
    }

    deleteSection(sectionId) {
        // Use Bootstrap modal instead of confirm()
        const modal = document.getElementById('bulkDeleteModal');
        const messageElement = document.getElementById('bulkDeleteMessage');
        const confirmButton = document.getElementById('confirmBulkDelete');
        const cancelButton = modal.querySelector('button[data-bs-dismiss="modal"]');
        
        if (modal && messageElement && confirmButton) {
            // Update message
            messageElement.textContent = 'Czy na pewno chcesz usunąć tę sekcję? Tej operacji nie można cofnąć.';
            
            // Remove existing event listeners
            const newConfirmButton = confirmButton.cloneNode(true);
            
            // Check if parent node exists before replacing
            if (confirmButton.parentNode) {
                confirmButton.parentNode.replaceChild(newConfirmButton, confirmButton);
            } else {
                console.warn('Confirm button parent node not found');
            }
            
            // Add new event listener for confirm button
            newConfirmButton.addEventListener('click', () => {
                // Hide modal first
                modal.classList.remove('show');
                modal.style.display = 'none';
                document.body.classList.remove('modal-open');
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) {
                    backdrop.remove();
                }
                
                // Then perform delete
                this.performDeleteSection(sectionId);
            });
            
            // Add event listener for cancel button to properly clean up
            if (cancelButton) {
                const newCancelButton = cancelButton.cloneNode(true);
                
                // Check if parent node exists before replacing
                if (cancelButton.parentNode) {
                    cancelButton.parentNode.replaceChild(newCancelButton, cancelButton);
                } else {
                    console.warn('Cancel button parent node not found');
                }
                
                newCancelButton.addEventListener('click', () => {
                    // Hide modal
                    modal.classList.remove('show');
                    modal.style.display = 'none';
                    document.body.classList.remove('modal-open');
                    const backdrop = document.querySelector('.modal-backdrop');
                    if (backdrop) {
                        backdrop.remove();
                    }
                });
            }
            
            // Show modal
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        } else {
            // Fallback to confirm() if modal not available
            window.deleteConfirmation.showSingleDelete(
                'sekcję',
                () => {
                    // Continue with deletion
                    performDeleteSection(sectionId);
                },
                'sekcję'
            );
        }
    }

    performDeleteSection(sectionId) {
        fetch(`/api/sections/${sectionId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.toastManager.success('Sekcja została usunięta pomyślnie!');
                // Usuń wiersz z tabeli
                const row = document.querySelector(`tr[data-section-id="${sectionId}"]`);
                if (row) {
                    row.remove();
                }
                
                // Wywołaj globalne odświeżenie
                if (typeof window.refreshAfterCRUD === 'function') {
                    window.refreshAfterCRUD();
                } else {
                    console.warn('window.refreshAfterCRUD is not available');
                }
            } else {
                window.toastManager.error('Błąd podczas usuwania: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            window.toastManager.error('Wystąpił błąd podczas usuwania sekcji');
        });
    }

    handleAddSection(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        // Always send is_active field as string
        formData.set('is_active', document.getElementById('sectionActive').checked ? 'true' : 'false');
        formData.set('enable_pillars', document.getElementById('sectionEnablePillars').checked ? 'true' : 'false');
        formData.set('enable_floating_cards', document.getElementById('sectionEnableFloatingCards').checked ? 'true' : 'false');
        
        // Remove hidden fields to avoid conflicts
        formData.delete('enable_pillars_hidden');
        formData.delete('enable_floating_cards_hidden');
        
        fetch('/api/sections', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(Object.fromEntries(formData))
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.toastManager.success('Sekcja została dodana pomyślnie!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('addSectionModal'));
                modal.hide();
                // Wywołaj globalne odświeżenie
                if (typeof window.refreshAfterCRUD === 'function') {
                    window.refreshAfterCRUD();
                } else {
                    console.warn('window.refreshAfterCRUD is not available');
                }
            } else {
                window.toastManager.error('Błąd podczas dodawania: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            window.toastManager.error('Wystąpił błąd podczas dodawania sekcji');
        });
    }

    handleEditSection(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        // Always send is_active field as string
        formData.set('is_active', document.getElementById('editSectionActive').checked ? 'true' : 'false');
        formData.set('enable_pillars', document.getElementById('editSectionEnablePillars').checked ? 'true' : 'false');
        formData.set('enable_floating_cards', document.getElementById('editSectionEnableFloatingCards').checked ? 'true' : 'false');
        
        // Get content from Quill
        if (window.quillInstances && window.quillInstances['editSectionContent']) {
            formData.set('content', window.quillInstances['editSectionContent'].root.innerHTML);
        }
        
        // Remove hidden fields to avoid conflicts
        formData.delete('enable_pillars_hidden');
        formData.delete('enable_floating_cards_hidden');
        
        const sectionId = document.getElementById('editSectionId').value;
        fetch(`/api/sections/${sectionId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(Object.fromEntries(formData))
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.toastManager.success('Sekcja została zaktualizowana pomyślnie!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('editSectionModal'));
                modal.hide();
                // Wywołaj globalne odświeżenie
                if (typeof window.refreshAfterCRUD === 'function') {
                    window.refreshAfterCRUD();
                } else {
                    console.warn('window.refreshAfterCRUD is not available');
                }
            } else {
                window.toastManager.error('Błąd podczas aktualizacji: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            window.toastManager.error('Wystąpił błąd podczas aktualizacji sekcji');
        });
    }
}

// Helper function to get blog link options for dropdown
async function getBlogLinkOptions(selectedLink = '') {
    try {
        console.log('getBlogLinkOptions called with selectedLink:', selectedLink);
        // Get blog categories and posts
        const [categoriesResponse, postsResponse] = await Promise.all([
            fetch('/api/blog/categories'),
            fetch('/api/blog/posts')
        ]);
        console.log('Fetch responses received');
        
        let options = '<option value="">-- Wybierz link --</option>';
        
        // Add menu options
        options += '<optgroup label="Menu">';
        options += '<option value="menu:blog" ' + (selectedLink === 'menu:blog' ? 'selected' : '') + '>Blog (#blog)</option>';
        options += '</optgroup>';
        
        // Add blog index
        options += '<optgroup label="Blog">';
        options += '<option value="blog_index" ' + (selectedLink === 'blog_index' ? 'selected' : '') + '>Strona główna bloga</option>';
        options += '</optgroup>';
        
        // Add categories if available
        if (categoriesResponse.ok) {
            try {
                const categoriesData = await categoriesResponse.json();
                console.log('Categories response:', categoriesData); // Debug log
                if (categoriesData.success && Array.isArray(categoriesData.categories)) {
                    console.log('Found categories:', categoriesData.categories.length); // Debug log
                    options += '<optgroup label="Kategorie">';
                    categoriesData.categories.forEach(category => {
                        const value = `category:${category.slug}`;
                        options += `<option value="${value}" ${value === selectedLink ? 'selected' : ''}>${category.full_path || category.title}</option>`;
                    });
                    options += '</optgroup>';
                } else {
                    console.warn('Categories data format issue:', categoriesData);
                }
            } catch (error) {
                console.warn('Error parsing categories response:', error);
            }
        } else {
            console.warn('Categories response not ok:', categoriesResponse.status, categoriesResponse.statusText);
        }
        
        // Add posts if available
        if (postsResponse.ok) {
            try {
                const postsData = await postsResponse.json();
                console.log('Posts response:', postsData); // Debug log
                if (postsData.success && Array.isArray(postsData.posts)) {
                    console.log('Found posts:', postsData.posts.length); // Debug log
                    options += '<optgroup label="Artykuły">';
                    postsData.posts.forEach(post => {
                        const value = `post:${post.slug}`;
                        options += `<option value="${value}" ${value === selectedLink ? 'selected' : ''}>${post.title}</option>`;
                    });
                    options += '</optgroup>';
                } else {
                    console.warn('Posts data format issue:', postsData);
                }
            } catch (error) {
                console.warn('Error parsing posts response:', error);
            }
        } else {
            console.warn('Posts response not ok:', postsResponse.status, postsResponse.statusText);
        }
        
        return options;
    } catch (error) {
        console.error('Error fetching blog options:', error);
        return '<option value="" disabled>Błąd ładowania opcji bloga</option>';
    }
}

// Pillars and Floating Cards Management
async function editPillars(sectionId) {
    try {
        const response = await fetch(`/api/sections/${sectionId}`);
        const data = await response.json();
        
        if (data.success) {
            const section = data.section;
            document.getElementById('editPillarsSectionId').value = section.id;
            
            // Set max pillars count
            maxPillarsCount = section.pillars_count || 4;
            
            // Parse existing pillars data
            let existingPillars = section.pillars_data ? JSON.parse(section.pillars_data) : [];
            
            // Ensure we have exactly maxPillarsCount pillars (fill with empty ones if needed)
            pillarsData = [];
            for (let i = 0; i < maxPillarsCount; i++) {
                if (existingPillars[i]) {
                    pillarsData.push(existingPillars[i]);
                } else {
                    pillarsData.push({
                        title: '',
                        description: '',
                        icon: '',
                        icon_color: '#007bff',
                        blog_link: ''
                    });
                }
            }
            
            // Set final text
            document.getElementById('editPillarsFinalText').value = section.final_text || '';
            
            // Render pillars
            await renderPillars();
            
            const modal = new bootstrap.Modal(document.getElementById('editPillarsModal'));
            modal.show();
        } else {
            window.toastManager.error('Błąd podczas ładowania filarów: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        window.toastManager.error('Wystąpił błąd podczas ładowania filarów');
    }
}

async function editFloatingCards(sectionId) {
    try {
        const response = await fetch(`/api/sections/${sectionId}`);
        const data = await response.json();
        
        if (data.success) {
            const section = data.section;
            document.getElementById('editFloatingCardsSectionId').value = section.id;
            
            // Set max floating cards count
            maxFloatingCardsCount = section.floating_cards_count || 3;
            
            // Parse existing floating cards data
            let existingCards = section.floating_cards_data ? JSON.parse(section.floating_cards_data) : [];
            
            // Ensure we have exactly maxFloatingCardsCount cards (fill with empty ones if needed)
            floatingCardsData = [];
            for (let i = 0; i < maxFloatingCardsCount; i++) {
                if (existingCards[i]) {
                    floatingCardsData.push(existingCards[i]);
                } else {
                    floatingCardsData.push({
                        title: '',
                        description: '',
                        icon: '',
                        icon_color: '#007bff',
                        blog_link: '',
                        position: 300
                    });
                }
            }
            
            // Set final text
            document.getElementById('editFloatingCardsFinalText').value = section.final_text || '';
            
            // Render floating cards
            await renderFloatingCards();
            
            const modal = new bootstrap.Modal(document.getElementById('editFloatingCardsModal'));
            modal.show();
        } else {
            window.toastManager.error('Błąd podczas ładowania kart: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        window.toastManager.error('Wystąpił błąd podczas ładowania kart');
    }
}

async function renderPillars() {
    const container = document.getElementById('pillarsContainer');
    container.innerHTML = '';
    
    // Render all pillars (we already have exactly maxPillarsCount)
    for (let i = 0; i < pillarsData.length; i++) {
        const pillar = pillarsData[i];
        const pillarElement = await createPillarElement(pillar, i);
        container.appendChild(pillarElement);
    }
    
    // Update count info
    const countInfo = document.getElementById('pillarsCountInfo');
    if (countInfo) {
        countInfo.textContent = `${pillarsData.length}/${maxPillarsCount} filarów`;
    }
}

async function renderFloatingCards() {
    const container = document.getElementById('floatingCardsContainer');
    container.innerHTML = '';
    
    // Render all floating cards (we already have exactly maxFloatingCardsCount)
    for (let i = 0; i < floatingCardsData.length; i++) {
        const card = floatingCardsData[i];
        const cardElement = await createFloatingCardElement(card, i);
        container.appendChild(cardElement);
    }
    
    // Update count info
    const countInfo = document.getElementById('floatingCardsCountInfo');
    if (countInfo) {
        countInfo.textContent = `${floatingCardsData.length}/${maxFloatingCardsCount} kart`;
    }
}

async function createPillarElement(pillar, index) {
    const div = document.createElement('div');
    div.className = 'card mb-3 pillar-card';
    
    // Get blog link options asynchronously
    const blogLinkOptions = await getBlogLinkOptions(pillar.blog_link || '');
    
    div.innerHTML = `
        <div class="card-header d-flex justify-content-between align-items-center">
            <h6 class="mb-0">Filar ${index + 1}</h6>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="removePillar(${index})">
                <i class="fas fa-trash"></i>
            </button>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-6">
                    <div class="mb-3">
                        <label class="form-label">Tytuł *</label>
                        <input type="text" class="form-control" name="pillar_title_${index}" value="${pillar.title || ''}" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Opis</label>
                        <textarea class="form-control" name="pillar_description_${index}" rows="3">${pillar.description || ''}</textarea>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="mb-3">
                        <label class="form-label">Ikona (FontAwesome)</label>
                        <input type="text" class="form-control" name="pillar_icon_${index}" value="${pillar.icon || ''}" placeholder="np. star, heart, check">
                        <div class="form-text">Nazwa ikony FontAwesome (bez fa-)</div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Kolor ikony</label>
                        <input type="color" class="form-control form-control-color" name="pillar_icon_color_${index}" value="${pillar.icon_color || '#007bff'}" title="Wybierz kolor ikony">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Link do bloga</label>
                        <select class="form-control" name="pillar_blog_link_${index}">
                            ${blogLinkOptions}
                        </select>
                        <div class="form-text">Opcjonalny link do bloga (kategoria, artykuł, menu)</div>
                    </div>
                </div>
            </div>
        </div>
    `;
    return div;
}

async function createFloatingCardElement(card, index) {
    const div = document.createElement('div');
    div.className = 'card mb-3 floating-card-card';
    
    // Get blog link options asynchronously
    const blogLinkOptions = await getBlogLinkOptions(card.blog_link || '');
    
    div.innerHTML = `
        <div class="card-header d-flex justify-content-between align-items-center">
            <h6 class="mb-0">Karta ${index + 1}</h6>
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeFloatingCard(${index})">
                <i class="fas fa-trash"></i>
            </button>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-6">
                    <div class="mb-3">
                        <label class="form-label">Tytuł *</label>
                        <input type="text" class="form-control" name="card_title_${index}" value="${card.title || ''}" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Opis</label>
                        <textarea class="form-control" name="card_description_${index}" rows="3">${card.description || ''}</textarea>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Pozycja (px)</label>
                        <input type="number" class="form-control" name="card_position_${index}" value="${card.position || 300}" placeholder="300" min="0" max="1000">
                        <div class="form-text">Pozycja karty w pikselach (np. 300, 500, 700)</div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="mb-3">
                        <label class="form-label">Ikona (FontAwesome)</label>
                        <input type="text" class="form-control" name="card_icon_${index}" value="${card.icon || ''}" placeholder="np. star, heart, check">
                        <div class="form-text">Nazwa ikony FontAwesome (bez fa-)</div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Kolor ikony</label>
                        <input type="color" class="form-control form-control-color" name="card_icon_color_${index}" value="${card.icon_color || '#007bff'}" title="Wybierz kolor ikony">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Link do bloga</label>
                        <select class="form-control" name="card_blog_link_${index}">
                            ${blogLinkOptions}
                        </select>
                        <div class="form-text">Opcjonalny link do bloga (kategoria, artykuł, menu)</div>
                    </div>
                </div>
            </div>
        </div>
    `;
    return div;
}

async function addPillar() {
    if (pillarsData.length >= maxPillarsCount) {
        window.toastManager.error(`Nie można dodać więcej filarów. Maksymalna liczba to ${maxPillarsCount}.`);
        return;
    }
    
    pillarsData.push({ 
        title: '', 
        description: '', 
        icon: '', 
        icon_color: '#007bff', 
        blog_link: '' 
    });
    await renderPillars();
}

async function addFloatingCard() {
    if (floatingCardsData.length >= maxFloatingCardsCount) {
        window.toastManager.error(`Nie można dodać więcej kart unoszących się. Maksymalna liczba to ${maxFloatingCardsCount}.`);
        return;
    }
    
    floatingCardsData.push({ 
        title: '', 
        description: '', 
        icon: '', 
        icon_color: '#007bff', 
        blog_link: '',
        position: 300
    });
    await renderFloatingCards();
}

async function removePillar(index) {
    pillarsData.splice(index, 1);
    await renderPillars();
}

async function removeFloatingCard(index) {
    floatingCardsData.splice(index, 1);
    await renderFloatingCards();
}

// Global functions for backward compatibility
function showAddSectionModal() {
    sectionsManager.showAddSectionModal();
}

function editSection(sectionId) {
    sectionsManager.editSection(sectionId);
}

function deleteSection(sectionId) {
    sectionsManager.deleteSection(sectionId);
}

// Quill is now initialized globally in admin/base.html

// Form handlers for pillars and floating cards
function handlePillarsForm(e) {
    e.preventDefault();
    
    const sectionId = document.getElementById('editPillarsSectionId').value;
    const formData = new FormData(e.target);
    
    // Collect pillars data from form
    const pillars = [];
    for (let i = 0; i < pillarsData.length; i++) {
        const title = formData.get(`pillar_title_${i}`);
        const description = formData.get(`pillar_description_${i}`);
        const icon = formData.get(`pillar_icon_${i}`);
        const icon_color = formData.get(`pillar_icon_color_${i}`);
        const blog_link = formData.get(`pillar_blog_link_${i}`);
        
        if (title) {
            pillars.push({ 
                title, 
                description: description || '', 
                icon: icon || '', 
                icon_color: icon_color || '#007bff', 
                blog_link: blog_link || '' 
            });
        }
    }
    
    // Get final text
    const finalText = formData.get('final_text') || '';
    
    // Send to API
    fetch(`/api/sections/${sectionId}/pillars`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            pillars: pillars,
            final_text: finalText
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.toastManager.success('Filary zostały zaktualizowane pomyślnie!');
            const modal = bootstrap.Modal.getInstance(document.getElementById('editPillarsModal'));
            modal.hide();
            // Odśwież stronę
            window.location.reload();
        } else {
            window.toastManager.error('Błąd podczas aktualizacji filarów: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        window.toastManager.error('Wystąpił błąd podczas aktualizacji filarów');
    });
}

function handleFloatingCardsForm(e) {
    e.preventDefault();
    
    const sectionId = document.getElementById('editFloatingCardsSectionId').value;
    const formData = new FormData(e.target);
    
    // Collect floating cards data from form
    const cards = [];
    for (let i = 0; i < floatingCardsData.length; i++) {
        const title = formData.get(`card_title_${i}`);
        const description = formData.get(`card_description_${i}`);
        const icon = formData.get(`card_icon_${i}`);
        const icon_color = formData.get(`card_icon_color_${i}`);
        const blog_link = formData.get(`card_blog_link_${i}`);
        const position = formData.get(`card_position_${i}`);
        
        if (title) {
            cards.push({ 
                title, 
                description: description || '', 
                icon: icon || '', 
                icon_color: icon_color || '#007bff', 
                blog_link: blog_link || '',
                position: position ? parseInt(position) : 300
            });
        }
    }
    
    // Get final text
    const finalText = formData.get('final_text') || '';
    
    // Send to API
    fetch(`/api/sections/${sectionId}/floating-cards`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            floating_cards: cards,
            final_text: finalText
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.toastManager.success('Karty zostały zaktualizowane pomyślnie!');
            const modal = bootstrap.Modal.getInstance(document.getElementById('editFloatingCardsModal'));
            modal.hide();
            // Odśwież stronę
            window.location.reload();
        } else {
            window.toastManager.error('Błąd podczas aktualizacji kart: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        window.toastManager.error('Wystąpił błąd podczas aktualizacji kart');
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.sectionsManager = new SectionsManager();
    
    // Initialize Quill
    // Quill is now initialized globally
    
    // Add form event listeners
    const pillarsForm = document.getElementById('editPillarsForm');
    const floatingCardsForm = document.getElementById('editFloatingCardsForm');
    
    if (pillarsForm) {
        pillarsForm.addEventListener('submit', handlePillarsForm);
    }
    
    if (floatingCardsForm) {
        floatingCardsForm.addEventListener('submit', handleFloatingCardsForm);
    }
});
