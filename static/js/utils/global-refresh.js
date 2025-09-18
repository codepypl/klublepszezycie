/**
 * Global Real-time Refresh System
 * Automatycznie aktualizuje wszystkie liczniki i dane na stronie w czasie rzeczywistym
 */

class GlobalRefreshSystem {
    constructor(options = {}) {
        this.options = {
            refreshInterval: 30000, // 30 sekund
            enableConsoleLogs: true,
            enableVisualIndicator: true,
            ...options
        };
        
        this.refreshInterval = null;
        this.isRefreshing = false;
        this.refreshIndicator = null;
        this.lastUpdateTime = null;
        
        // Mapa funkcji aktualizacji dla różnych typów danych
        this.updateFunctions = new Map();
        
        // Zarejestruj domyślne funkcje aktualizacji
        this.registerDefaultUpdateFunctions();
        
        this.init();
    }
    
    init() {
        if (this.options.enableConsoleLogs) {
            console.log('🔄 Global Refresh System initialized');
        }
        
        this.createRefreshIndicator();
        this.startAutoRefresh();
        this.setupVisibilityChange();
    }
    
    registerDefaultUpdateFunctions() {
        // Aktualizacja statusu wydarzenia
        this.registerUpdateFunction('event-status', (data) => {
            this.updateEventStatus(data);
        });
        
        // Aktualizacja licznika rejestracji
        this.registerUpdateFunction('registration-count', (data) => {
            this.updateRegistrationCount(data);
        });
        
        // Aktualizacja licznika członków grupy
        this.registerUpdateFunction('group-members', (data) => {
            this.updateGroupMembers(data);
        });
        
        // Aktualizacja statystyk CRM
        this.registerUpdateFunction('crm-stats', (data) => {
            this.updateCrmStats(data);
        });
        
        // Aktualizacja kolejki emaili
        this.registerUpdateFunction('email-queue', (data) => {
            this.updateEmailQueue(data);
        });
    }
    
    registerUpdateFunction(type, callback) {
        this.updateFunctions.set(type, callback);
        if (this.options.enableConsoleLogs) {
            console.log(`📝 Registered update function: ${type}`);
        }
    }
    
    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        this.refreshInterval = setInterval(() => {
            if (!this.isRefreshing) {
                this.refreshAll();
            }
        }, this.options.refreshInterval);
        
        if (this.options.enableConsoleLogs) {
            console.log(`⏰ Auto-refresh started every ${this.options.refreshInterval / 1000} seconds`);
        }
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
            if (this.options.enableConsoleLogs) {
                console.log('⏹️ Auto-refresh stopped');
            }
        }
    }
    
    async refreshAll() {
        if (this.isRefreshing) return;
        
        this.isRefreshing = true;
        this.showRefreshIndicator();
        
        try {
            // Pobierz aktualne dane z różnych endpointów
            const promises = [];
            
            // Sprawdź czy jesteśmy na stronie z wydarzeniem
            const eventId = this.getCurrentEventId();
            if (eventId) {
                promises.push(this.fetchEventData(eventId));
            }
            
            // Sprawdź czy jesteśmy w panelu administracyjnym
            if (this.isAdminPage()) {
                promises.push(this.fetchAdminData());
            }
            
            // Wykonaj wszystkie zapytania równolegle
            const results = await Promise.allSettled(promises);
            
            // Przetwórz wyniki
            results.forEach((result, index) => {
                if (result.status === 'fulfilled' && result.value) {
                    this.processUpdateData(result.value);
                } else if (result.status === 'rejected') {
                    console.error('❌ Error fetching data:', result.reason);
                }
            });
            
            this.lastUpdateTime = new Date();
            this.updateLastRefreshTime();
            
        } catch (error) {
            console.error('❌ Error in refreshAll:', error);
        } finally {
            this.isRefreshing = false;
            this.hideRefreshIndicator();
        }
    }
    
    async fetchEventData(eventId) {
        try {
            const response = await fetch(`/api/event-status?event_id=${eventId}`);
            const data = await response.json();
            return { type: 'event-data', data };
        } catch (error) {
            console.error('❌ Error fetching event data:', error);
            return null;
        }
    }
    
    async fetchAdminData() {
        try {
            const promises = [];
            
            // Sprawdź czy użytkownik jest zalogowany (sprawdź czy jest token w localStorage)
            const isLoggedIn = localStorage.getItem('auth_token') || document.cookie.includes('session');
            
            if (isLoggedIn) {
                // Pobierz statystyki kolejki CRM (jeśli jesteśmy na stronie CRM)
                if (window.location.pathname.includes('/crm/')) {
                    promises.push(
                        fetch('/api/crm/queue/stats')
                            .then(response => response.json())
                            .then(data => ({ type: 'crm-queue-stats', data }))
                            .catch(() => null)
                    );
                }
                
                // Pobierz dane kolejki emaili
                promises.push(
                    fetch('/api/email/queue-stats')
                        .then(response => response.json())
                        .then(data => ({ type: 'email-queue', data }))
                        .catch(() => null)
                );
            }
            
            const results = await Promise.allSettled(promises);
            return results
                .filter(result => result.status === 'fulfilled' && result.value)
                .map(result => result.value);
        } catch (error) {
            console.error('❌ Error fetching admin data:', error);
            return [];
        }
    }
    
    processUpdateData(updateData) {
        if (Array.isArray(updateData)) {
            updateData.forEach(item => this.processUpdateData(item));
            return;
        }
        
        const { type, data } = updateData;
        if (!type || !data) return;
        
        // Wywołaj odpowiednią funkcję aktualizacji
        const updateFunction = this.updateFunctions.get(type);
        if (updateFunction) {
            try {
                updateFunction(data);
            } catch (error) {
                console.error(`❌ Error in update function ${type}:`, error);
            }
        }
    }
    
    // Funkcje aktualizacji konkretnych elementów
    updateEventStatus(data) {
        if (!data.event_id) return;
        
        const newStatus = data.is_registration_open ? 'upcoming' : 'closed';
        
        // Aktualizuj status wydarzenia
        const statusElement = document.querySelector('.event-status');
        if (statusElement) {
            statusElement.textContent = newStatus === 'upcoming' ? 'Nadchodzące' : 'Zakończone';
        }
        
        // Aktualizuj licznik rejestracji
        this.updateRegistrationCount(data);
        
        // Aktualizuj przycisk rejestracji
        const registerButton = document.querySelector('[data-bs-target="#eventRegistrationModal"]');
        if (registerButton) {
            if (newStatus === 'closed') {
                registerButton.disabled = true;
                registerButton.textContent = 'Rejestracja zamknięta';
            } else {
                registerButton.disabled = false;
                registerButton.innerHTML = '<i class="fas fa-calendar-check me-2"></i>Zarezerwuj miejsce';
            }
        }
        
        if (this.options.enableConsoleLogs) {
            console.log(`📅 Event status updated: ${newStatus}`);
        }
    }
    
    updateRegistrationCount(data) {
        const countElement = document.querySelector('.registration-count');
        if (countElement && data.registration_count !== undefined) {
            if (data.max_participants) {
                countElement.textContent = `${data.registration_count}/${data.max_participants} miejsc`;
            } else {
                countElement.textContent = `${data.registration_count} osób`;
            }
        }
        
        // Aktualizuj progress bar jeśli istnieje
        const progressBar = document.querySelector('.registration-progress');
        if (progressBar && data.max_participants) {
            const percentage = (data.registration_count / data.max_participants) * 100;
            progressBar.style.width = `${Math.min(percentage, 100)}%`;
            progressBar.setAttribute('aria-valuenow', data.registration_count);
        }
    }
    
    updateGroupMembers(data) {
        const memberCountElement = document.querySelector('.group-member-count');
        if (memberCountElement && data.member_count !== undefined) {
            memberCountElement.textContent = data.member_count;
        }
    }
    
    updateCrmStats(data) {
        // Aktualizuj statystyki CRM
        const statsElements = {
            'total-contacts': data.total_contacts,
            'total-calls': data.total_calls,
            'pending-calls': data.pending_calls,
            'completed-calls': data.completed_calls
        };
        
        Object.entries(statsElements).forEach(([selector, value]) => {
            const element = document.querySelector(`.${selector}`);
            if (element && value !== undefined) {
                element.textContent = value;
            }
        });
    }
    
    updateEmailQueue(data) {
        // Aktualizuj kolejkę emaili
        const queueElements = {
            'queue-total': data.total_emails,
            'queue-pending': data.pending_emails,
            'queue-sent': data.sent_emails,
            'queue-failed': data.failed_emails
        };
        
        Object.entries(queueElements).forEach(([selector, value]) => {
            const element = document.querySelector(`.${selector}`);
            if (element && value !== undefined) {
                element.textContent = value;
            }
        });
    }
    
    // Funkcje pomocnicze
    getCurrentEventId() {
        const heroSection = document.getElementById('hero');
        return heroSection ? heroSection.dataset.eventId : null;
    }
    
    isAdminPage() {
        return window.location.pathname.includes('/admin/');
    }
    
    createRefreshIndicator() {
        if (!this.options.enableVisualIndicator) return;
        
        this.refreshIndicator = document.createElement('div');
        this.refreshIndicator.id = 'global-refresh-indicator';
        this.refreshIndicator.innerHTML = `
            <div class="refresh-indicator">
                <i class="fas fa-sync-alt fa-spin"></i>
                <span>Aktualizacja danych...</span>
            </div>
        `;
        
        // Dodaj style
        const style = document.createElement('style');
        style.textContent = `
            #global-refresh-indicator {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
                font-size: 14px;
                display: none;
                align-items: center;
                gap: 10px;
            }
            
            .refresh-indicator i {
                font-size: 16px;
            }
            
            .last-refresh-time {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 9999;
                background: rgba(0, 0, 0, 0.6);
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 12px;
                display: none;
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(this.refreshIndicator);
        
        // Dodaj element czasu ostatniej aktualizacji
        const lastRefreshElement = document.createElement('div');
        lastRefreshElement.className = 'last-refresh-time';
        lastRefreshElement.id = 'last-refresh-time';
        document.body.appendChild(lastRefreshElement);
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
    
    updateLastRefreshTime() {
        const lastRefreshElement = document.getElementById('last-refresh-time');
        if (lastRefreshElement && this.lastUpdateTime) {
            const timeString = this.lastUpdateTime.toLocaleTimeString('pl-PL');
            lastRefreshElement.textContent = `Ostatnia aktualizacja: ${timeString}`;
            lastRefreshElement.style.display = 'block';
            
            // Ukryj po 3 sekundach
            setTimeout(() => {
                lastRefreshElement.style.display = 'none';
            }, 3000);
        }
    }
    
    setupVisibilityChange() {
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                // Strona stała się widoczna - odśwież dane
                this.refreshAll();
            }
        });
    }
    
    // Publiczne metody
    forceRefresh() {
        this.refreshAll();
    }
    
    // Wywołaj odświeżenie po operacji CRUD
    refreshAfterCRUD() {
        if (this.options.enableConsoleLogs) {
            console.log('🔄 Refreshing after CRUD operation');
        }
        this.refreshAll();
    }
    
    setRefreshInterval(interval) {
        this.options.refreshInterval = interval;
        this.stopAutoRefresh();
        this.startAutoRefresh();
    }
    
    destroy() {
        this.stopAutoRefresh();
        if (this.refreshIndicator) {
            this.refreshIndicator.remove();
        }
        const lastRefreshElement = document.getElementById('last-refresh-time');
        if (lastRefreshElement) {
            lastRefreshElement.remove();
        }
    }
}

// Utwórz globalną instancję
window.globalRefreshSystem = new GlobalRefreshSystem({
    refreshInterval: 30000, // 30 sekund
    enableConsoleLogs: true,
    enableVisualIndicator: true
});

// Uniwersalna funkcja do wywołania po operacjach CRUD
window.refreshAfterCRUD = function() {
    if (window.globalRefreshSystem) {
        window.globalRefreshSystem.refreshAfterCRUD();
    }
};

// Eksportuj dla modułów
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GlobalRefreshSystem;
}
