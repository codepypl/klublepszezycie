/**
 * Real-time refresh system for CRM and other admin pages
 */
class RealtimeRefresh {
    constructor(options = {}) {
        this.options = {
            refreshInterval: 30000, // 30 seconds
            enableAutoRefresh: true,
            showRefreshIndicator: true,
            refreshOnFocus: true,
            refreshOnVisibility: true,
            ...options
        };
        
        this.refreshInterval = null;
        this.isRefreshing = false;
        this.lastRefreshTime = null;
        this.refreshCallbacks = new Map();
        this.refreshIndicator = null;
        
        this.init();
    }
    
    init() {
        if (this.options.enableAutoRefresh) {
            this.startAutoRefresh();
        }
        
        if (this.options.refreshOnFocus) {
            this.setupFocusRefresh();
        }
        
        if (this.options.refreshOnVisibility) {
            this.setupVisibilityRefresh();
        }
        
        if (this.options.showRefreshIndicator) {
            this.createRefreshIndicator();
        }
    }
    
    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            if (!this.isRefreshing) {
                this.refreshAll();
            }
        }, this.options.refreshInterval);
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    setupFocusRefresh() {
        window.addEventListener('focus', () => {
            if (this.shouldRefreshOnFocus()) {
                this.refreshAll();
            }
        });
    }
    
    setupVisibilityRefresh() {
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.shouldRefreshOnVisibility()) {
                this.refreshAll();
            }
        });
    }
    
    shouldRefreshOnFocus() {
        if (!this.lastRefreshTime) return true;
        
        const timeSinceLastRefresh = Date.now() - this.lastRefreshTime;
        return timeSinceLastRefresh > 10000; // Refresh if more than 10 seconds ago
    }
    
    shouldRefreshOnVisibility() {
        if (!this.lastRefreshTime) return true;
        
        const timeSinceLastRefresh = Date.now() - this.lastRefreshTime;
        return timeSinceLastRefresh > 30000; // Refresh if more than 30 seconds ago
    }
    
    createRefreshIndicator() {
        this.refreshIndicator = document.createElement('div');
        this.refreshIndicator.id = 'refreshIndicator';
        this.refreshIndicator.className = 'refresh-indicator';
        this.refreshIndicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            background: rgba(0, 123, 255, 0.9);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
            display: none;
            align-items: center;
            gap: 8px;
            backdrop-filter: blur(10px);
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        `;
        
        const icon = document.createElement('i');
        icon.className = 'fas fa-sync-alt fa-spin';
        icon.style.fontSize = '12px';
        
        const text = document.createElement('span');
        text.textContent = 'Odświeżanie...';
        
        this.refreshIndicator.appendChild(icon);
        this.refreshIndicator.appendChild(text);
        document.body.appendChild(this.refreshIndicator);
    }
    
    showRefreshIndicator() {
        if (this.refreshIndicator) {
            this.refreshIndicator.style.display = 'flex';
        }
    }
    
    hideRefreshIndicator() {
        if (this.refreshIndicator) {
            this.refreshIndicator.style.display = 'none';
        }
    }
    
    registerRefreshCallback(name, callback) {
        this.refreshCallbacks.set(name, callback);
    }
    
    unregisterRefreshCallback(name) {
        this.refreshCallbacks.delete(name);
    }
    
    async refreshAll() {
        if (this.isRefreshing) return;
        
        this.isRefreshing = true;
        this.lastRefreshTime = Date.now();
        
        if (this.options.showRefreshIndicator) {
            this.showRefreshIndicator();
        }
        
        try {
            const promises = Array.from(this.refreshCallbacks.values()).map(callback => {
                try {
                    return Promise.resolve(callback());
                } catch (error) {
                    console.error('Refresh callback error:', error);
                    return Promise.resolve();
                }
            });
            
            await Promise.all(promises);
        } catch (error) {
            console.error('Refresh error:', error);
        } finally {
            this.isRefreshing = false;
            
            if (this.options.showRefreshIndicator) {
                setTimeout(() => {
                    this.hideRefreshIndicator();
                }, 1000);
            }
        }
    }
    
    async refreshSingle(name) {
        const callback = this.refreshCallbacks.get(name);
        if (!callback) return;
        
        try {
            await Promise.resolve(callback());
        } catch (error) {
            console.error(`Refresh callback error for ${name}:`, error);
        }
    }
    
    setRefreshInterval(interval) {
        this.options.refreshInterval = interval;
        
        if (this.refreshInterval) {
            this.stopAutoRefresh();
            this.startAutoRefresh();
        }
    }
    
    enableAutoRefresh() {
        this.options.enableAutoRefresh = true;
        if (!this.refreshInterval) {
            this.startAutoRefresh();
        }
    }
    
    disableAutoRefresh() {
        this.options.enableAutoRefresh = false;
        this.stopAutoRefresh();
    }
    
    getStatus() {
        return {
            isRefreshing: this.isRefreshing,
            lastRefreshTime: this.lastRefreshTime,
            refreshInterval: this.options.refreshInterval,
            autoRefreshEnabled: this.options.enableAutoRefresh,
            registeredCallbacks: Array.from(this.refreshCallbacks.keys())
        };
    }
}

// Global realtime refresh instance
window.globalRealtimeRefresh = null;

// Initialize global realtime refresh
document.addEventListener('DOMContentLoaded', function() {
    window.globalRealtimeRefresh = new RealtimeRefresh({
        refreshInterval: 30000, // 30 seconds
        enableAutoRefresh: true,
        showRefreshIndicator: true,
        refreshOnFocus: true,
        refreshOnVisibility: true
    });
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RealtimeRefresh;
}


