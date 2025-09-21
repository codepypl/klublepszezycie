/**
 * Universal pagination functionality for admin panels
 */
class Pagination {
    constructor(options = {}) {
        this.options = {
            containerId: 'pagination',
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
        this.onPageChange = this.options.onPageChange || null;
        this.onPerPageChange = this.options.onPerPageChange || null;
        
        this.init();
    }
    
    init() {
        this.render();
        this.bindEvents();
    }
    
    setData(data) {
        this.currentPage = data.page || 1;
        this.totalPages = Math.max(data.pages || 1, 1); // Always at least 1 page
        this.totalItems = data.total || 0;
        this.perPage = data.per_page || this.options.defaultPerPage;
        this.render();
    }
    
    render() {
        const container = document.getElementById(this.options.containerId);
        if (!container) return;
        
        container.innerHTML = this.generateHTML();
        this.bindEvents();
    }
    
    generateHTML() {
        let html = '<nav aria-label="Paginacja">';
        
        // Per page selector (if enabled)
        if (this.options.showPerPage) {
            html += `<div class="d-flex justify-content-center align-items-center mb-3">
                <div class="text-center">
                    <label for="perPageSelect" class="form-label me-2">Elementów na stronę:</label>
                    <select id="perPageSelect" class="form-select d-inline-block w-auto">
                        ${this.options.perPageOptions.map(option => 
                            `<option value="${option}" ${option === this.perPage ? 'selected' : ''}>${option}</option>`
                        ).join('')}
                    </select>
                </div>
            </div>`;
        }
        
        // Pagination controls
        html += '<ul class="pagination justify-content-center">';
        
        // First page
        if (this.options.showFirstLast && this.currentPage > 1) {
            html += `<li class="page-item">
                <a class="page-link" href="#" data-page="1">${this.options.firstText}</a>
            </li>`;
        }
        
        // Previous page
        if (this.options.showPrevNext && this.currentPage > 1) {
            html += `<li class="page-item">
                <a class="page-link" href="#" data-page="${this.currentPage - 1}">${this.options.prevText}</a>
            </li>`;
        }
        
        // Page numbers
        const pages = this.generatePageNumbers();
        pages.forEach(page => {
            if (page === '...') {
                html += '<li class="page-item disabled"><span class="page-link">…</span></li>';
            } else if (page === this.currentPage) {
                html += `<li class="page-item active">
                    <span class="page-link">${page}</span>
                </li>`;
            } else {
                html += `<li class="page-item">
                    <a class="page-link" href="#" data-page="${page}">${page}</a>
                </li>`;
            }
        });
        
        // Next page
        if (this.options.showPrevNext && this.currentPage < this.totalPages) {
            html += `<li class="page-item">
                <a class="page-link" href="#" data-page="${this.currentPage + 1}">${this.options.nextText}</a>
            </li>`;
        }
        
        // Last page
        if (this.options.showFirstLast && this.currentPage < this.totalPages) {
            html += `<li class="page-item">
                <a class="page-link" href="#" data-page="${this.totalPages}">${this.options.lastText}</a>
            </li>`;
        }
        
        html += '</ul>';
        
        // Info text
        if (this.options.showInfo) {
            const infoText = this.options.infoText
                .replace('{page}', this.currentPage)
                .replace('{pages}', this.totalPages)
                .replace('{total}', this.totalItems);
            
            html += `<div class="text-center text-muted mt-2">${infoText}</div>`;
        }
        
        
        html += '</nav>';
        
        return html;
    }
    
    generatePageNumbers() {
        const pages = [];
        const maxVisible = this.options.maxVisiblePages;
        const current = this.currentPage;
        const total = this.totalPages;
        
        // Handle case when there are no items (total = 0)
        if (total === 0) {
            pages.push(1); // Show at least page 1
            return pages;
        }
        
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
            
            // Add first page and ellipsis if needed
            if (start > 1) {
                pages.push(1);
                if (start > 2) {
                    pages.push('...');
                }
            }
            
            // Add middle pages
            for (let i = start; i <= end; i++) {
                pages.push(i);
            }
            
            // Add ellipsis and last page if needed
            if (end < total) {
                if (end < total - 1) {
                    pages.push('...');
                }
                pages.push(total);
            }
        }
        
        return pages;
    }
    
    bindEvents() {
        const container = document.getElementById(this.options.containerId);
        if (!container) return;
        
        // Page links
        container.querySelectorAll('a[data-page]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(e.target.getAttribute('data-page'));
                this.goToPage(page);
            });
        });
        
        // Per page selector
        const perPageSelect = container.querySelector('#perPageSelect');
        if (perPageSelect) {
            perPageSelect.addEventListener('change', (e) => {
                const perPage = parseInt(e.target.value);
                this.changePerPage(perPage);
            });
        }
    }
    
    goToPage(page) {
        if (page < 1 || page > this.totalPages || page === this.currentPage) {
            return;
        }
        
        this.currentPage = page;
        
        if (this.onPageChange) {
            this.onPageChange(page, this.perPage);
        }
        
        this.render();
    }
    
    changePerPage(perPage) {
        if (perPage === this.perPage) {
            return;
        }
        
        this.perPage = perPage;
        this.currentPage = 1; // Reset to first page
        
        if (this.onPerPageChange) {
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

// Helper function to create pagination from Flask-SQLAlchemy pagination object
function createPaginationFromFlask(flaskPagination, containerId, options = {}) {
    const pagination = new Pagination({
        containerId,
        ...options
    });
    
    pagination.setData({
        page: flaskPagination.page,
        pages: flaskPagination.pages,
        total: flaskPagination.total,
        per_page: flaskPagination.per_page
    });
    
    return pagination;
}

// Auto-initialize pagination for elements with pagination-container class
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for other scripts to set up data
    setTimeout(() => {
        const paginationContainers = document.querySelectorAll('.pagination-container');
        
        paginationContainers.forEach(container => {
            const containerId = container.id || 'pagination';
            const options = {};
            
            // Get options from data attributes
            if (container.dataset.showInfo !== undefined) {
                options.showInfo = container.dataset.showInfo === 'true';
            }
            if (container.dataset.showPerPage !== undefined) {
                options.showPerPage = container.dataset.showPerPage === 'true';
            }
            if (container.dataset.defaultPerPage) {
                options.defaultPerPage = parseInt(container.dataset.defaultPerPage);
            }
            if (container.dataset.maxVisiblePages) {
                options.maxVisiblePages = parseInt(container.dataset.maxVisiblePages);
            }
            
            // Check if there's Flask pagination data
            const flaskPagination = window.flaskPaginationData;
            let paginationInstance;
            
            if (flaskPagination && flaskPagination.page) {
                // Use Flask pagination data
                paginationInstance = createPaginationFromFlask(flaskPagination, containerId, options);
            } else {
                // Create basic pagination with default data
                paginationInstance = new Pagination({
                    containerId: containerId,
                    ...options
                });
                
                // Set default data to make pagination visible
                paginationInstance.setData({
                    page: 1,
                    pages: 1,
                    total: 0,
                    per_page: options.defaultPerPage || 10
                });
            }
            
            // Set up event handlers if they exist
            if (window.paginationHandlers) {
                paginationInstance.onPageChange = window.paginationHandlers.onPageChange;
                paginationInstance.onPerPageChange = window.paginationHandlers.onPerPageChange;
            }
            
            // Store instance in container element for later access
            container.paginationInstance = paginationInstance;
        });
    }, 100);
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Pagination, createPaginationFromFlask };
}
