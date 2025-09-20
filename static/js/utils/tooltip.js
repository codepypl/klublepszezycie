/**
 * Universal Tooltip Manager
 * Handles Bootstrap tooltips initialization and management across the application
 */
class TooltipManager {
    constructor() {
        this.tooltips = new Map();
        this.init();
    }

    /**
     * Initialize tooltips on page load
     */
    init() {
        this.initializeTooltips();
        this.setupEventListeners();
    }

    /**
     * Initialize all tooltips on the page
     * @param {string} selector - CSS selector for tooltip elements (optional)
     * @returns {Array} Array of initialized tooltip instances
     */
    initializeTooltips(selector = '[data-bs-toggle="tooltip"]') {
        const tooltipElements = document.querySelectorAll(selector);
        const newTooltips = [];

        tooltipElements.forEach(element => {
            // Skip if already initialized
            if (element.hasAttribute('data-tooltip-initialized')) {
                return;
            }

            try {
                const tooltip = new bootstrap.Tooltip(element, {
                    trigger: 'hover focus',
                    placement: element.getAttribute('data-bs-placement') || 'top',
                    delay: {
                        show: 300,
                        hide: 100
                    }
                });

                // Mark as initialized
                element.setAttribute('data-tooltip-initialized', 'true');
                
                // Store reference
                const elementId = this.getElementId(element);
                this.tooltips.set(elementId, tooltip);
                
                newTooltips.push(tooltip);
            } catch (error) {
                console.warn('Failed to initialize tooltip for element:', element, error);
            }
        });

        return newTooltips;
    }

    /**
     * Re-initialize tooltips for dynamically added content
     * @param {string} container - Container selector to search within
     * @returns {Array} Array of newly initialized tooltip instances
     */
    reinitializeTooltips(container = document) {
        const selector = '[data-bs-toggle="tooltip"]:not([data-tooltip-initialized])';
        const elements = container.querySelectorAll(selector);
        
        if (elements.length === 0) {
            return [];
        }

        return this.initializeTooltips(selector);
    }

    /**
     * Destroy specific tooltip
     * @param {string|HTMLElement} element - Element or element ID
     */
    destroyTooltip(element) {
        const elementId = typeof element === 'string' ? element : this.getElementId(element);
        const tooltip = this.tooltips.get(elementId);
        
        if (tooltip) {
            tooltip.dispose();
            this.tooltips.delete(elementId);
        }
    }

    /**
     * Destroy all tooltips
     */
    destroyAllTooltips() {
        this.tooltips.forEach(tooltip => {
            tooltip.dispose();
        });
        this.tooltips.clear();
    }

    /**
     * Update tooltip content
     * @param {string|HTMLElement} element - Element or element ID
     * @param {string} content - New tooltip content
     */
    updateTooltipContent(element, content) {
        const elementId = typeof element === 'string' ? element : this.getElementId(element);
        const tooltip = this.tooltips.get(elementId);
        
        if (tooltip) {
            tooltip.setContent({ '.tooltip-inner': content });
        }
    }

    /**
     * Show tooltip programmatically
     * @param {string|HTMLElement} element - Element or element ID
     */
    showTooltip(element) {
        const elementId = typeof element === 'string' ? element : this.getElementId(element);
        const tooltip = this.tooltips.get(elementId);
        
        if (tooltip) {
            tooltip.show();
        }
    }

    /**
     * Hide tooltip programmatically
     * @param {string|HTMLElement} element - Element or element ID
     */
    hideTooltip(element) {
        const elementId = typeof element === 'string' ? element : this.getElementId(element);
        const tooltip = this.tooltips.get(elementId);
        
        if (tooltip) {
            tooltip.hide();
        }
    }

    /**
     * Setup event listeners for dynamic content
     */
    setupEventListeners() {
        // Listen for DOM changes to auto-initialize new tooltips
        if (window.MutationObserver) {
            const observer = new MutationObserver((mutations) => {
                let shouldReinitialize = false;
                
                mutations.forEach((mutation) => {
                    if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                        // Check if any added nodes contain tooltip elements
                        mutation.addedNodes.forEach((node) => {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                if (node.matches && node.matches('[data-bs-toggle="tooltip"]')) {
                                    shouldReinitialize = true;
                                } else if (node.querySelector && node.querySelector('[data-bs-toggle="tooltip"]')) {
                                    shouldReinitialize = true;
                                }
                            }
                        });
                    }
                });
                
                if (shouldReinitialize) {
                    // Debounce reinitialization
                    clearTimeout(this.reinitTimeout);
                    this.reinitTimeout = setTimeout(() => {
                        this.reinitializeTooltips();
                    }, 100);
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
    }

    /**
     * Generate unique ID for element
     * @param {HTMLElement} element - DOM element
     * @returns {string} Unique element ID
     */
    getElementId(element) {
        if (!element.id) {
            element.id = 'tooltip-' + Math.random().toString(36).substr(2, 9);
        }
        return element.id;
    }

    /**
     * Get tooltip instance
     * @param {string|HTMLElement} element - Element or element ID
     * @returns {Object|null} Tooltip instance or null
     */
    getTooltip(element) {
        const elementId = typeof element === 'string' ? element : this.getElementId(element);
        return this.tooltips.get(elementId) || null;
    }

    /**
     * Check if tooltip exists
     * @param {string|HTMLElement} element - Element or element ID
     * @returns {boolean} True if tooltip exists
     */
    hasTooltip(element) {
        const elementId = typeof element === 'string' ? element : this.getElementId(element);
        return this.tooltips.has(elementId);
    }
}

// Create global instance
window.tooltipManager = new TooltipManager();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TooltipManager;
}

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.tooltipManager.init();
    });
} else {
    window.tooltipManager.init();
}
