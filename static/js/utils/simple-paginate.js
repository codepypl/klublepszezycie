/**
 * Simple Pagination - Nowa, uproszczona implementacja paginacji
 */
class SimplePagination {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.options = {
            showInfo: true,
            showPerPage: true,
            perPageOptions: [5, 10, 25, 50, 100],
            defaultPerPage: 10,
            maxVisiblePages: 5,
            showFirstLast: true,
            showPrevNext: true,
            prevText: 'Poprzednia',
            nextText: 'Następna',
            firstText: 'Pierwsza',
            lastText: 'Ostatnia',
            infoText: 'Strona {page} z {pages} ({total} elementów)',
            ...options
        };
        
        this.currentPage = 1;
        this.totalPages = 1;
        this.totalItems = 0;
        this.perPage = this.options.defaultPerPage;
        
        this.onPageChange = null;
        this.onPerPageChange = null;
        
        this.init();
    }
    
    init() {
        this.render();
        this.bindEvents();
    }
    
    setData(data) {
        console.log('🔍 SimplePagination setData called with:', data);
        
        this.currentPage = data.page || 1;
        this.totalPages = Math.max(data.pages || 1, 1);
        this.totalItems = data.total || 0;
        this.perPage = data.per_page || this.options.defaultPerPage;
        
        console.log('🔍 SimplePagination state after setData:', {
            currentPage: this.currentPage,
            totalPages: this.totalPages,
            totalItems: this.totalItems,
            perPage: this.perPage
        });
        
        this.render();
    }
    
    render() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error('❌ SimplePagination container not found:', this.containerId);
            return;
        }
        
        container.innerHTML = this.generateHTML();
        this.bindEvents();
        
        console.log('🔍 SimplePagination rendered');
    }
    
    generateHTML() {
        let html = '<div class="simple-pagination">';
        
        // Per page selector
        if (this.options.showPerPage) {
            html += `
                <div class="d-flex justify-content-center align-items-center mb-3">
                    <div class="text-center">
                        <label for="simplePerPageSelect" class="form-label me-2">Elementów na stronę:</label>
                        <select id="simplePerPageSelect" class="form-select d-inline-block" style="width: auto;">
                            ${this.options.perPageOptions.map(option => 
                                `<option value="${option}" ${option === this.perPage ? 'selected' : ''}>${option}</option>`
                            ).join('')}
                        </select>
                    </div>
                </div>
            `;
        }
        
        // Pagination controls
        if (this.totalPages > 1) {
            html += '<nav aria-label="Paginacja"><ul class="pagination justify-content-center">';
            
            // First page
            if (this.options.showFirstLast && this.currentPage > 1) {
                html += `<li class="page-item">
                    <a class="page-link simple-page-link" href="#" data-page="1">${this.options.firstText}</a>
                </li>`;
            }
            
            // Previous page
            if (this.options.showPrevNext && this.currentPage > 1) {
                html += `<li class="page-item">
                    <a class="page-link simple-page-link" href="#" data-page="${this.currentPage - 1}">${this.options.prevText}</a>
                </li>`;
            }
            
            // Page numbers
            const pages = this.generatePageNumbers();
            pages.forEach(page => {
                if (page === this.currentPage) {
                    html += `<li class="page-item active">
                        <span class="page-link">${page}</span>
                    </li>`;
                } else {
                    html += `<li class="page-item">
                        <a class="page-link simple-page-link" href="#" data-page="${page}">${page}</a>
                    </li>`;
                }
            });
            
            // Next page
            if (this.options.showPrevNext && this.currentPage < this.totalPages) {
                html += `<li class="page-item">
                    <a class="page-link simple-page-link" href="#" data-page="${this.currentPage + 1}">${this.options.nextText}</a>
                </li>`;
            }
            
            // Last page
            if (this.options.showFirstLast && this.currentPage < this.totalPages) {
                html += `<li class="page-item">
                    <a class="page-link simple-page-link" href="#" data-page="${this.totalPages}">${this.options.lastText}</a>
                </li>`;
            }
            
            html += '</ul></nav>';
        }
        
        // Info text
        if (this.options.showInfo) {
            const infoText = this.options.infoText
                .replace('{page}', this.currentPage)
                .replace('{pages}', this.totalPages)
                .replace('{total}', this.totalItems);
            
            html += `<div class="text-center text-muted mt-2">${infoText}</div>`;
        }
        
        html += '</div>';
        
        return html;
    }
    
    generatePageNumbers() {
        const pages = [];
        const maxVisible = this.options.maxVisiblePages;
        const current = this.currentPage;
        const total = this.totalPages;
        
        if (total <= maxVisible) {
            // Show all pages if total is less than max visible
            for (let i = 1; i <= total; i++) {
                pages.push(i);
            }
        } else {
            // Calculate start and end pages
            let start = Math.max(1, current - Math.floor(maxVisible / 2));
            let end = Math.min(total, start + maxVisible - 1);
            
            // Adjust start if we're near the end
            if (end - start + 1 < maxVisible) {
                start = Math.max(1, end - maxVisible + 1);
            }
            
            for (let i = start; i <= end; i++) {
                pages.push(i);
            }
        }
        
        return pages;
    }
    
    bindEvents() {
        const container = document.getElementById(this.containerId);
        if (!container) return;
        
        // Page links
        container.querySelectorAll('.simple-page-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(e.target.getAttribute('data-page'));
                this.goToPage(page);
            });
        });
        
        // Per page selector
        const perPageSelect = container.querySelector('#simplePerPageSelect');
        if (perPageSelect) {
            perPageSelect.addEventListener('change', (e) => {
                const perPage = parseInt(e.target.value);
                this.changePerPage(perPage);
            });
        }
        
        console.log('🔍 SimplePagination events bound');
    }
    
    goToPage(page) {
        if (page < 1 || page > this.totalPages || page === this.currentPage) {
            return;
        }
        
        console.log('🔍 SimplePagination goToPage:', page);
        
        this.currentPage = page;
        
        if (this.onPageChange) {
            console.log('🔍 SimplePagination calling onPageChange:', page);
            this.onPageChange(page);
        }
        
        this.render();
    }
    
    changePerPage(perPage) {
        if (perPage === this.perPage) {
            return;
        }
        
        console.log('🔍 SimplePagination changePerPage:', perPage);
        
        this.perPage = perPage;
        this.currentPage = 1; // Reset to first page
        
        if (this.onPerPageChange) {
            console.log('🔍 SimplePagination calling onPerPageChange:', this.currentPage, perPage);
            this.onPerPageChange(this.currentPage, perPage);
        }
        
        this.render();
    }
    
    // Public methods
    setPageChangeCallback(callback) {
        this.onPageChange = callback;
    }
    
    setPerPageChangeCallback(callback) {
        this.onPerPageChange = callback;
    }
    
    getCurrentPage() {
        return this.currentPage;
    }
    
    getPerPage() {
        return this.perPage;
    }
    
    getTotalPages() {
        return this.totalPages;
    }
    
    getTotalItems() {
        return this.totalItems;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SimplePagination;
}
