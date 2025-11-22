/**
 * Theme Switcher for Admin Panel
 * Handles switching between light, dark, and midnight themes
 */

(function() {
    'use strict';

    const ThemeSwitcher = {
        STORAGE_KEY: 'admin_theme',
        THEMES: {
            light: {
                name: 'Jasny',
                icon: 'fa-sun',
                cssFile: 'admin-light.css'
            },
            dark: {
                name: 'Ciemny',
                icon: 'fa-moon',
                cssFile: 'admin-dark.css'
            },
            midnight: {
                name: 'Midnight',
                icon: 'fa-star',
                cssFile: 'admin-midnight.css'
            }
        },

        /**
         * Initialize theme switcher
         */
        init: function() {
            // Load theme from server first, then fallback to localStorage
            this.loadThemeFromServer().then((serverTheme) => {
                // Use server theme if available, otherwise use localStorage
                const savedTheme = serverTheme || this.getSavedTheme();
                this.applyTheme(savedTheme);

                // Setup event listeners
                this.setupEventListeners();

                // Update UI to reflect current theme
                this.updateUI(savedTheme);
            }).catch(() => {
                // If server load fails, use localStorage
                const savedTheme = this.getSavedTheme();
                this.applyTheme(savedTheme);
                this.setupEventListeners();
                this.updateUI(savedTheme);
            });
        },

        /**
         * Get saved theme from localStorage
         */
        getSavedTheme: function() {
            const saved = localStorage.getItem(this.STORAGE_KEY);
            return saved && this.THEMES[saved] ? saved : 'light';
        },

        /**
         * Load theme from server
         */
        loadThemeFromServer: function() {
            return fetch('/api/users/admin-theme')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success && data.theme && this.THEMES[data.theme]) {
                        // Update localStorage
                        localStorage.setItem(this.STORAGE_KEY, data.theme);
                        return data.theme;
                    }
                    return null;
                })
                .catch(error => {
                    console.warn('Could not load theme from server:', error);
                    return null;
                });
        },

        /**
         * Save theme to localStorage and server
         */
        saveTheme: function(theme) {
            if (this.THEMES[theme]) {
                // Save to localStorage immediately
                localStorage.setItem(this.STORAGE_KEY, theme);
                
                // Save to server
                fetch('/api/users/admin-theme', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ theme: theme })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log('Theme saved to server:', theme);
                    } else {
                        console.warn('Failed to save theme to server:', data.message);
                    }
                })
                .catch(error => {
                    console.warn('Error saving theme to server:', error);
                });
            }
        },

        /**
         * Apply theme to document
         */
        applyTheme: function(theme) {
            if (!this.THEMES[theme]) {
                theme = 'light';
            }

            // Get theme CSS file
            const themeInfo = this.THEMES[theme];
            const cssFile = themeInfo.cssFile;

            // Find and update the theme CSS link
            const themeLink = document.getElementById('admin-theme-css');
            if (themeLink) {
                // Get base path from current href (e.g., /static/css/)
                const currentHref = themeLink.getAttribute('href');
                const basePath = currentHref.substring(0, currentHref.lastIndexOf('/') + 1);
                const newHref = basePath + cssFile;
                
                // Update href
                themeLink.setAttribute('href', newHref);
                
                // Force reload by removing and re-adding the link
                // This ensures the new CSS is loaded immediately
                const parent = themeLink.parentNode;
                const newLink = document.createElement('link');
                newLink.rel = 'stylesheet';
                newLink.href = newHref;
                newLink.id = 'admin-theme-css';
                parent.removeChild(themeLink);
                parent.appendChild(newLink);
            }

            // Save theme
            this.saveTheme(theme);

            // Update UI
            this.updateUI(theme);
        },

        /**
         * Update UI to reflect current theme
         */
        updateUI: function(theme) {
            const themeInfo = this.THEMES[theme];
            if (!themeInfo) return;

            // Update dropdown label
            const label = document.getElementById('themeSwitcherLabel');
            if (label) {
                label.textContent = themeInfo.name;
            }

            // Update dropdown button icon
            const button = document.getElementById('themeSwitcherDropdown');
            if (button) {
                const icon = button.querySelector('i');
                if (icon) {
                    icon.className = `fas ${themeInfo.icon} me-1`;
                }
            }

            // Update active state in dropdown
            document.querySelectorAll('.theme-option').forEach(option => {
                option.classList.remove('active');
                if (option.dataset.theme === theme) {
                    option.classList.add('active');
                }
            });
        },

        /**
         * Setup event listeners
         */
        setupEventListeners: function() {
            // Handle theme option clicks
            document.querySelectorAll('.theme-option').forEach(option => {
                option.addEventListener('click', (e) => {
                    e.preventDefault();
                    const theme = option.dataset.theme;
                    if (theme && this.THEMES[theme]) {
                        this.applyTheme(theme);
                        
                        // Close dropdown
                        const dropdown = bootstrap.Dropdown.getInstance(document.getElementById('themeSwitcherDropdown'));
                        if (dropdown) {
                            dropdown.hide();
                        }
                    }
                });
            });
        }
    };

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => ThemeSwitcher.init());
    } else {
        ThemeSwitcher.init();
    }

    // Make ThemeSwitcher globally available
    window.ThemeSwitcher = ThemeSwitcher;
})();

