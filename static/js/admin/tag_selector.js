// Tag Selector Component
class TagSelector {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            placeholder: 'Wpisz tagi lub wybierz z listy...',
            allowNew: true,
            maxTags: 10,
            ...options
        };
        this.selectedTags = [];
        this.availableTags = [];
        this.init();
    }

    async init() {
        await this.loadAvailableTags();
        this.render();
        this.bindEvents();
    }

    async loadAvailableTags() {
        try {
            const response = await fetch('/api/blog/tags/all', {
                credentials: 'include'
            });
            const result = await response.json();
            
            if (result.success) {
                this.availableTags = result.tags;
            } else {
                console.error('Failed to load tags:', result.message);
            }
        } catch (error) {
            console.error('Error loading tags:', error);
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="tag-selector-container" style="position: relative;">
                <div class="mb-2">
                    <small class="text-muted">
                        <i class="fas fa-info-circle me-1"></i>
                        Wpisz nazwę tagu i naciśnij Enter, aby go dodać
                    </small>
                </div>
                <div class="tag-input-container" style="position: relative;">
                    <input type="text" class="form-control tag-input" placeholder="${this.options.placeholder}" autocomplete="off">
                    <div class="tag-suggestions" style="display: none;"></div>
                </div>
                <div class="selected-tags"></div>
                <input type="hidden" class="tag-values" name="tags">
            </div>
        `;
        
        // Add CSS for tag styling
        this.addTagStyles();
    }
    
    addTagStyles() {
        if (document.getElementById('tag-selector-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'tag-selector-styles';
        style.textContent = `
            .selected-tag {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                background: var(--admin-primary, #1e3a8a);
                color: var(--admin-white, #ffffff);
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 0.5rem;
                font-weight: 500;
                font-size: 0.875rem;
                margin: 0.25rem;
                transition: all 0.3s ease;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            
            .selected-tag:hover {
                background: #1e40af;
                transform: translateY(-1px);
                box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
            }
            
            .tag-remove {
                background: none;
                border: none;
                color: var(--admin-white, #ffffff);
                cursor: pointer;
                padding: 0;
                margin-left: 0.25rem;
                border-radius: 50%;
                width: 1.25rem;
                height: 1.25rem;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
            }
            
            .tag-remove:hover {
                background: rgba(255, 255, 255, 0.2);
                transform: scale(1.1);
            }
            
            .tag-suggestions {
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 0.5rem;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                z-index: 1000;
                max-height: 200px;
                overflow-y: auto;
            }
            
            .suggestion-item {
                padding: 0.75rem 1rem;
                cursor: pointer;
                border-bottom: 1px solid #f3f4f6;
                transition: background-color 0.2s ease;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .suggestion-item:hover {
                background-color: #f8fafc;
            }
            
            .suggestion-item:last-child {
                border-bottom: none;
            }
            
            .suggestion-item.add-new {
                color: var(--admin-primary, #1e3a8a);
                font-weight: 500;
            }
        `;
        document.head.appendChild(style);
    }

    bindEvents() {
        const input = this.container.querySelector('.tag-input');

        // Input events
        input.addEventListener('input', (e) => this.handleInput(e));
        input.addEventListener('keydown', (e) => this.handleKeydown(e));
        input.addEventListener('blur', () => {
            // Delay hiding suggestions to allow click events to be processed
            setTimeout(() => this.hideSuggestions(), 150);
        });
        input.addEventListener('focus', () => this.showSuggestions());

        // Use event delegation on the main container for suggestion clicks
        this.container.addEventListener('mousedown', (e) => {
            // Check if click is on a suggestion item
            const item = e.target.closest('.suggestion-item');
            if (item) {
                e.preventDefault();
                e.stopPropagation();
                
                if (item.classList.contains('add-new')) {
                    this.addNewTag(item.dataset.query);
                } else {
                    this.selectTag(JSON.parse(item.dataset.tag));
                }
            }
        });

        // Click outside to hide suggestions
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.hideSuggestions();
            }
        });
    }

    handleInput(e) {
        const query = e.target.value.toLowerCase().trim();
        
        if (query.length === 0) {
            this.hideSuggestions();
            return;
        }

        // Filter available tags
        const filtered = this.availableTags.filter(tag => {
            const nameMatch = tag.name.toLowerCase().includes(query);
            const notSelected = !this.selectedTags.some(selected => String(selected.id) === String(tag.id));
            return nameMatch && notSelected;
        });
        

        this.showSuggestions(filtered, query);
    }

    handleKeydown(e) {
        const suggestions = this.container.querySelector('.tag-suggestions');
        const activeItem = suggestions.querySelector('.suggestion-item.active');
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            this.navigateSuggestions(1);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            this.navigateSuggestions(-1);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (activeItem) {
                this.selectTag(JSON.parse(activeItem.dataset.tag));
            } else {
                this.addNewTag(e.target.value);
            }
        } else if (e.key === 'Escape') {
            this.hideSuggestions();
        }
    }

    navigateSuggestions(direction) {
        const suggestions = this.container.querySelector('.tag-suggestions');
        const items = suggestions.querySelectorAll('.suggestion-item');
        const activeItem = suggestions.querySelector('.suggestion-item.active');
        
        if (items.length === 0) return;

        let newIndex = 0;
        if (activeItem) {
            const currentIndex = Array.from(items).indexOf(activeItem);
            newIndex = Math.max(0, Math.min(items.length - 1, currentIndex + direction));
        }

        items.forEach((item, index) => {
            item.classList.toggle('active', index === newIndex);
        });
    }

    showSuggestions(tags = [], query = '') {
        const suggestions = this.container.querySelector('.tag-suggestions');
        
        if (tags.length === 0 && !this.options.allowNew) {
            this.hideSuggestions();
            return;
        }

        let html = '';
        
        // Show matching tags
        tags.forEach(tag => {
            html += `
                <div class="suggestion-item" data-tag='${JSON.stringify(tag)}'>
                    <i class="fas fa-tag me-2"></i>
                    ${tag.name}
                </div>
            `;
        });

        // Show "Add new" option if allowed and query is not empty
        if (this.options.allowNew && query.length > 0 && !tags.some(tag => tag.name.toLowerCase() === query.toLowerCase())) {
            html += `
                <div class="suggestion-item add-new" data-query="${query}">
                    <i class="fas fa-plus me-2"></i>
                    Dodaj "${query}"
                </div>
            `;
        }

        suggestions.innerHTML = html;
        suggestions.style.display = 'block';
    }

    hideSuggestions() {
        const suggestions = this.container.querySelector('.tag-suggestions');
        suggestions.style.display = 'none';
        suggestions.innerHTML = '';
    }

    selectTag(tag) {
        if (this.selectedTags.length >= this.options.maxTags) {
            showWarning(`Maksymalnie ${this.options.maxTags} tagów`);
            return;
        }

        if (!this.selectedTags.some(selected => String(selected.id) === String(tag.id))) {
            this.selectedTags.push(tag);
            this.updateDisplay();
            this.clearInput();
        }
    }

    addNewTag(name) {
        if (this.selectedTags.length >= this.options.maxTags) {
            showWarning(`Maksymalnie ${this.options.maxTags} tagów`);
            return;
        }

        const trimmedName = name.trim();
        if (trimmedName.length === 0) return;

        // Check if tag already exists
        const existingTag = this.availableTags.find(tag => 
            tag.name.toLowerCase() === trimmedName.toLowerCase()
        );

        if (existingTag) {
            this.selectTag(existingTag);
        } else {
            // Create new tag object
            const newTag = {
                id: `new_${Date.now()}`,
                name: trimmedName,
                slug: this.slugify(trimmedName)
            };
            
            this.selectedTags.push(newTag);
            this.updateDisplay();
            this.clearInput();
        }
    }

    removeTag(tagId) {
        this.selectedTags = this.selectedTags.filter(tag => String(tag.id) !== String(tagId));
        this.updateDisplay();
    }

    updateDisplay() {
        const container = this.container.querySelector('.selected-tags');
        const hiddenInput = this.container.querySelector('.tag-values');
        
        if (!container) {
            console.error('Selected tags container not found!');
            return;
        }
        
        if (!hiddenInput) {
            console.error('Hidden input not found!');
            return;
        }
        
        // Clear container
        container.innerHTML = '';
        
        // Render selected tags
        this.selectedTags.forEach(tag => {
            const tagElement = document.createElement('div');
            tagElement.className = 'selected-tag';
            tagElement.innerHTML = `
                <span class="tag-name">${tag.name}</span>
                <button type="button" class="tag-remove" data-tag-id="${tag.id}">
                    <i class="fas fa-times"></i>
                </button>
            `;
            container.appendChild(tagElement);
        });

        // Update hidden input
        const tagNames = this.selectedTags.map(tag => tag.name);
        hiddenInput.value = JSON.stringify(tagNames);

        // Bind remove events
        container.querySelectorAll('.tag-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.removeTag(btn.dataset.tagId);
            });
        });
    }

    clearInput() {
        const input = this.container.querySelector('.tag-input');
        input.value = '';
        this.hideSuggestions();
    }

    setTags(tags) {
        this.selectedTags = Array.isArray(tags) ? tags : [];
        this.updateDisplay();
    }

    getTags() {
        return this.selectedTags;
    }

    getTagNames() {
        const tagNames = this.selectedTags.map(tag => tag.name);
        return tagNames;
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

// CSS styles
const tagSelectorStyles = `
<style>
.tag-selector-container {
    position: relative;
}

.tag-input-container {
    position: relative;
}

.tag-input {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

.tag-suggestions {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #ddd;
    border-top: none;
    border-radius: 0 0 4px 4px;
    max-height: 200px;
    overflow-y: auto;
    z-index: 1000;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.suggestion-item {
    padding: 8px 12px;
    cursor: pointer;
    border-bottom: 1px solid #f0f0f0;
    display: flex;
    align-items: center;
}

.suggestion-item:hover,
.suggestion-item.active {
    background-color: #f8f9fa;
}

.suggestion-item.add-new {
    color: #007bff;
    font-style: italic;
}

.selected-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-top: 8px;
}

.selected-tag {
    display: inline-flex;
    align-items: center;
    background-color: #e9ecef;
    border: 1px solid #ced4da;
    border-radius: 16px;
    padding: 4px 8px;
    font-size: 12px;
    gap: 4px;
}

.tag-name {
    color: #495057;
}

.tag-remove {
    background: none;
    border: none;
    color: #6c757d;
    cursor: pointer;
    padding: 0;
    width: 16px;
    height: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
}

.tag-remove:hover {
    background-color: #dc3545;
    color: white;
}
</style>
`;

// Inject styles
if (!document.querySelector('#tag-selector-styles')) {
    const styleElement = document.createElement('div');
    styleElement.id = 'tag-selector-styles';
    styleElement.innerHTML = tagSelectorStyles;
    document.head.appendChild(styleElement);
}
