/**
 * Table Column Resizer
 * Allows users to resize table columns by dragging
 */
class TableResizer {
    constructor() {
        this.isResizing = false;
        this.currentColumn = null;
        this.startX = 0;
        this.startWidth = 0;
        this.table = null;
        this.columnIndex = 0;
        this.minWidth = 50; // Minimum column width
        this.maxWidth = 500; // Maximum column width
    }

    /**
     * Initialize resizer for a table
     * @param {string|HTMLElement} tableSelector - Table selector or element
     */
    init(tableSelector) {
        this.table = typeof tableSelector === 'string' 
            ? document.querySelector(tableSelector) 
            : tableSelector;
        
        if (!this.table) {
            console.warn('Table not found for resizer');
            return;
        }

        this.addResizeHandles();
        this.resetColumnWidths(); // Reset to default widths on page load
    }

    /**
     * Add resize handles to table headers
     */
    addResizeHandles() {
        const headers = this.table.querySelectorAll('thead th');
        
        headers.forEach((header, index) => {
            // Skip first column (checkbox) and last column (actions)
            if (index === 0 || index === headers.length - 1) {
                return;
            }

            // Create resize handle
            const handle = document.createElement('div');
            handle.className = 'column-resize-handle';
            handle.innerHTML = '⋮⋮';
            handle.style.cssText = `
                position: absolute;
                right: 0;
                top: 0;
                bottom: 0;
                width: 8px;
                background: transparent;
                cursor: col-resize;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 10px;
                color: #ccc;
                user-select: none;
                z-index: 10;
            `;

            // Make header relative positioned
            header.style.position = 'relative';
            header.appendChild(handle);

            // Add event listeners
            handle.addEventListener('mousedown', (e) => this.startResize(e, index));
        });

        // Add global event listeners
        document.addEventListener('mousemove', (e) => this.handleResize(e));
        document.addEventListener('mouseup', (e) => this.stopResize(e));
    }

    /**
     * Start resizing a column
     * @param {MouseEvent} e - Mouse event
     * @param {number} columnIndex - Column index
     */
    startResize(e, columnIndex) {
        e.preventDefault();
        e.stopPropagation();

        this.isResizing = true;
        this.columnIndex = columnIndex;
        this.currentColumn = this.table.querySelectorAll('thead th')[columnIndex];
        this.startX = e.clientX;
        this.startWidth = this.currentColumn.offsetWidth;

        // Add visual feedback
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        
        // Add resizing class to table
        this.table.classList.add('resizing');
    }

    /**
     * Handle column resizing
     * @param {MouseEvent} e - Mouse event
     */
    handleResize(e) {
        if (!this.isResizing || !this.currentColumn) return;

        e.preventDefault();
        
        const deltaX = e.clientX - this.startX;
        const newWidth = Math.max(this.minWidth, Math.min(this.maxWidth, this.startWidth + deltaX));
        
        // Update column width
        this.currentColumn.style.width = newWidth + 'px';
        this.currentColumn.style.minWidth = newWidth + 'px';
        
        // Update all cells in this column
        const allRows = this.table.querySelectorAll('tbody tr');
        allRows.forEach(row => {
            const cell = row.children[this.columnIndex];
            if (cell) {
                cell.style.width = newWidth + 'px';
                cell.style.minWidth = newWidth + 'px';
            }
        });
    }

    /**
     * Stop resizing
     * @param {MouseEvent} e - Mouse event
     */
    stopResize(e) {
        if (!this.isResizing) return;

        this.isResizing = false;
        this.currentColumn = null;
        
        // Remove visual feedback
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        this.table.classList.remove('resizing');
        
        // Save column widths
        this.saveColumnWidths();
    }

    /**
     * Save column widths to localStorage
     */
    saveColumnWidths() {
        const tableId = this.table.id || 'default-table';
        const widths = {};
        
        const headers = this.table.querySelectorAll('thead th');
        headers.forEach((header, index) => {
            if (index !== 0 && index !== headers.length - 1) {
                widths[index] = header.offsetWidth;
            }
        });
        
        localStorage.setItem(`table-widths-${tableId}`, JSON.stringify(widths));
    }

    /**
     * Load column widths from localStorage
     */
    loadColumnWidths() {
        const tableId = this.table.id || 'default-table';
        const savedWidths = localStorage.getItem(`table-widths-${tableId}`);
        
        if (!savedWidths) return;
        
        try {
            const widths = JSON.parse(savedWidths);
            const headers = this.table.querySelectorAll('thead th');
            
            Object.keys(widths).forEach(index => {
                const columnIndex = parseInt(index);
                const width = widths[index];
                
                if (headers[columnIndex]) {
                    headers[columnIndex].style.width = width + 'px';
                    headers[columnIndex].style.minWidth = width + 'px';
                    
                    // Update all cells in this column
                    const allRows = this.table.querySelectorAll('tbody tr');
                    allRows.forEach(row => {
                        const cell = row.children[columnIndex];
                        if (cell) {
                            cell.style.width = width + 'px';
                            cell.style.minWidth = width + 'px';
                        }
                    });
                }
            });
        } catch (e) {
            console.warn('Failed to load saved column widths:', e);
        }
    }

    /**
     * Reset all column widths to default
     */
    resetColumnWidths() {
        const headers = this.table.querySelectorAll('thead th');
        headers.forEach((header, index) => {
            if (index !== 0 && index !== headers.length - 1) {
                header.style.width = '';
                header.style.minWidth = '';
                
                // Reset all cells in this column
                const allRows = this.table.querySelectorAll('tbody tr');
                allRows.forEach(row => {
                    const cell = row.children[index];
                    if (cell) {
                        cell.style.width = '';
                        cell.style.minWidth = '';
                    }
                });
            }
        });
        
        // Clear saved widths
        const tableId = this.table.id || 'default-table';
        localStorage.removeItem(`table-widths-${tableId}`);
    }
}

// Global instance
window.tableResizer = new TableResizer();

// Auto-initialize for tables with 'resizable-table' class
document.addEventListener('DOMContentLoaded', function() {
    const resizableTables = document.querySelectorAll('.resizable-table');
    resizableTables.forEach(table => {
        window.tableResizer.init(table);
    });
});
