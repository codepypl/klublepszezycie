// Admin Sections JavaScript for Lepsze Życie Club

// Global variables
let pillarsData = [];
let floatingCardsData = [];

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
        fetch(`/admin/api/sections/${sectionId}`)
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
                    
                    // Set content in TinyMCE
                    if (tinymce.get('editSectionContent')) {
                        tinymce.get('editSectionContent').setContent(section.content || '');
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
                    toastManager.error('Błąd podczas ładowania sekcji: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                toastManager.error('Wystąpił błąd podczas ładowania sekcji');
            });
    }

    deleteSection(sectionId) {
        if (confirm('Czy na pewno chcesz usunąć tę sekcję? Tej operacji nie można cofnąć.')) {
            fetch(`/admin/api/sections?id=${sectionId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    toastManager.success('Sekcja została usunięta pomyślnie!');
                    // Usuń wiersz z tabeli
                    const row = document.querySelector(`tr[data-section-id="${sectionId}"]`);
                    if (row) {
                        row.remove();
                    }
                } else {
                    toastManager.error('Błąd podczas usuwania: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                toastManager.error('Wystąpił błąd podczas usuwania sekcji');
            });
        }
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
        
        fetch('/admin/api/sections', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                toastManager.success('Sekcja została dodana pomyślnie!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('addSectionModal'));
                modal.hide();
                // Odśwież stronę
                window.location.reload();
            } else {
                toastManager.error('Błąd podczas dodawania: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            toastManager.error('Wystąpił błąd podczas dodawania sekcji');
        });
    }

    handleEditSection(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        // Always send is_active field as string
        formData.set('is_active', document.getElementById('editSectionActive').checked ? 'true' : 'false');
        formData.set('enable_pillars', document.getElementById('editSectionEnablePillars').checked ? 'true' : 'false');
        formData.set('enable_floating_cards', document.getElementById('editSectionEnableFloatingCards').checked ? 'true' : 'false');
        
        // Get content from TinyMCE
        if (tinymce.get('editSectionContent')) {
            formData.set('content', tinymce.get('editSectionContent').getContent());
        }
        
        // Remove hidden fields to avoid conflicts
        formData.delete('enable_pillars_hidden');
        formData.delete('enable_floating_cards_hidden');
        
        fetch('/admin/api/sections', {
            method: 'PUT',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                toastManager.success('Sekcja została zaktualizowana pomyślnie!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('editSectionModal'));
                modal.hide();
                // Odśwież stronę
                window.location.reload();
            } else {
                toastManager.error('Błąd podczas aktualizacji: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            toastManager.error('Wystąpił błąd podczas aktualizacji sekcji');
        });
    }
}

// Helper function to get pages for dropdown
async function getPagesOptions(selectedPage = '') {
    try {
        // Try to fetch pages from the database
        const response = await fetch('/admin/api/pages');
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.success && Array.isArray(data.pages)) {
                // Filter only active and published pages
                const activePages = data.pages.filter(page => page.is_active && page.is_published);
                
                if (activePages.length > 0) {
                    return activePages.map(page => 
                        `<option value="${page.slug}" ${page.slug === selectedPage ? 'selected' : ''}>${page.title}</option>`
                    ).join('');
                } else {
                    // No active and published pages found
                    return `<option value="" disabled>Brak dostępnych podstron</option>`;
                }
            }
        }
        
        // Fallback to static pages if API fails
        console.warn('Could not fetch pages from API, using fallback');
        const fallbackPages = [
            { slug: 'o-nas', title: 'O nas' },
            { slug: 'korzysci', title: 'Korzyści' },
            { slug: 'kontakt', title: 'Kontakt' },
            { slug: 'faq', title: 'FAQ' }
        ];
        
        return fallbackPages.map(page => 
            `<option value="${page.slug}" ${page.slug === selectedPage ? 'selected' : ''}>${page.title}</option>`
        ).join('');
        
    } catch (error) {
        console.error('Error fetching pages:', error);
        
        // Fallback to static pages on error
        const fallbackPages = [
            { slug: 'o-nas', title: 'O nas' },
            { slug: 'korzysci', title: 'Korzyści' },
            { slug: 'kontakt', title: 'Kontakt' },
            { slug: 'faq', title: 'FAQ' }
        ];
        
        return fallbackPages.map(page => 
            `<option value="${page.slug}" ${page.slug === selectedPage ? 'selected' : ''}>${page.title}</option>`
        ).join('');
    }
}

// Pillars and Floating Cards Management
async function editPillars(sectionId) {
    try {
        const response = await fetch(`/admin/api/sections/${sectionId}`);
        const data = await response.json();
        
        if (data.success) {
            const section = data.section;
            document.getElementById('editPillarsSectionId').value = section.id;
            
            // Parse existing pillars data
            pillarsData = section.pillars_data ? JSON.parse(section.pillars_data) : [];
            
            // Set final text
            document.getElementById('editPillarsFinalText').value = section.final_text || '';
            
            // Render pillars
            await renderPillars();
            
            const modal = new bootstrap.Modal(document.getElementById('editPillarsModal'));
            modal.show();
        } else {
            toastManager.error('Błąd podczas ładowania filarów: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        toastManager.error('Wystąpił błąd podczas ładowania filarów');
    }
}

async function editFloatingCards(sectionId) {
    try {
        const response = await fetch(`/admin/api/sections/${sectionId}`);
        const data = await response.json();
        
        if (data.success) {
            const section = data.section;
            document.getElementById('editFloatingCardsSectionId').value = section.id;
            
            // Parse existing floating cards data
            floatingCardsData = section.floating_cards_data ? JSON.parse(section.floating_cards_data) : [];
            
            // Set final text
            document.getElementById('editFloatingCardsFinalText').value = section.final_text || '';
            
            // Render floating cards
            await renderFloatingCards();
            
            const modal = new bootstrap.Modal(document.getElementById('editFloatingCardsModal'));
            modal.show();
        } else {
            toastManager.error('Błąd podczas ładowania kart: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        toastManager.error('Wystąpił błąd podczas ładowania kart');
    }
}

async function renderPillars() {
    const container = document.getElementById('pillarsContainer');
    container.innerHTML = '';
    
    for (let i = 0; i < pillarsData.length; i++) {
        const pillar = pillarsData[i];
        const pillarElement = await createPillarElement(pillar, i);
        container.appendChild(pillarElement);
    }
}

async function renderFloatingCards() {
    const container = document.getElementById('floatingCardsContainer');
    container.innerHTML = '';
    
    for (let i = 0; i < floatingCardsData.length; i++) {
        const card = floatingCardsData[i];
        const cardElement = await createFloatingCardElement(card, i);
        container.appendChild(cardElement);
    }
}

async function createPillarElement(pillar, index) {
    const div = document.createElement('div');
    div.className = 'card mb-3 pillar-card';
    
    // Get pages options asynchronously
    const pagesOptions = await getPagesOptions(pillar.page_link || '');
    
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
                        <label class="form-label">Link do podstrony</label>
                        <select class="form-control" name="pillar_page_link_${index}">
                            <option value="">-- Wybierz podstronę --</option>
                            ${pagesOptions}
                        </select>
                        <div class="form-text">Opcjonalny link do podstrony</div>
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
    
    // Get pages options asynchronously
    const pagesOptions = await getPagesOptions(card.page_link || '');
    
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
                        <label class="form-label">Link do podstrony</label>
                        <select class="form-control" name="card_page_link_${index}">
                            <option value="">-- Wybierz podstrony --</option>
                            ${pagesOptions}
                        </select>
                        <div class="form-text">Opcjonalny link do podstrony</div>
                    </div>
                </div>
            </div>
        </div>
    `;
    return div;
}

async function addPillar() {
    pillarsData.push({ 
        title: '', 
        description: '', 
        icon: '', 
        icon_color: '#007bff', 
        page_link: '' 
    });
    await renderPillars();
}

async function addFloatingCard() {
    floatingCardsData.push({ 
        title: '', 
        description: '', 
        icon: '', 
        icon_color: '#007bff', 
        page_link: '',
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

// Initialize TinyMCE
function initTinyMCE() {
    if (typeof tinymce !== 'undefined') {
        tinymce.init({
            selector: '#sectionContent, #editSectionContent',
            height: 300,
            plugins: 'anchor autolink charmap codesample emoticons image link lists media searchreplace table visualblocks wordcount',
            toolbar: 'undo redo | blocks fontfamily fontsize | bold italic underline strikethrough | link image media table | align lineheight | numlist bullist indent outdent | emoticons charmap | removeformat',
            content_style: 'body { font-family: -apple-system, BlinkMacSystemFont, San Francisco, Segoe UI, Roboto, Helvetica Neue, sans-serif; font-size: 14px; }',
            setup: function (editor) {
                editor.on('init', function () {
                    console.log('TinyMCE initialized for:', editor.id);
                });
                editor.on('ready', function () {
                    console.log('TinyMCE instance ready for:', editor.id);
                });
            }
        });
    }
}

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
        const page_link = formData.get(`pillar_page_link_${i}`);
        
        if (title) {
            pillars.push({ 
                title, 
                description: description || '', 
                icon: icon || '', 
                icon_color: icon_color || '#007bff', 
                page_link: page_link || '' 
            });
        }
    }
    
    // Get final text
    const finalText = formData.get('final_text') || '';
    
    // Send to API
    fetch(`/admin/api/sections/${sectionId}/pillars`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            pillars_data: JSON.stringify(pillars),
            final_text: finalText
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toastManager.success('Filary zostały zaktualizowane pomyślnie!');
            const modal = bootstrap.Modal.getInstance(document.getElementById('editPillarsModal'));
            modal.hide();
        } else {
            toastManager.error('Błąd podczas aktualizacji filarów: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        toastManager.error('Wystąpił błąd podczas aktualizacji filarów');
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
        const page_link = formData.get(`card_page_link_${i}`);
        const position = formData.get(`card_position_${i}`);
        
        if (title) {
            cards.push({ 
                title, 
                description: description || '', 
                icon: icon || '', 
                icon_color: icon_color || '#007bff', 
                page_link: page_link || '',
                position: position ? parseInt(position) : 300
            });
        }
    }
    
    // Get final text
    const finalText = formData.get('final_text') || '';
    
    // Send to API
    fetch(`/admin/api/sections/${sectionId}/floating-cards`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            floating_cards_data: JSON.stringify(cards),
            final_text: finalText
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            toastManager.success('Karty zostały zaktualizowane pomyślnie!');
            const modal = bootstrap.Modal.getInstance(document.getElementById('editFloatingCardsModal'));
            modal.hide();
        } else {
            toastManager.error('Błąd podczas aktualizacji kart: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        toastManager.error('Wystąpił błąd podczas aktualizacji kart');
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.sectionsManager = new SectionsManager();
    
    // Initialize TinyMCE
    initTinyMCE();
    
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
