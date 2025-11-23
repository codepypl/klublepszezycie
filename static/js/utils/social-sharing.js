/**
 * Social Media Sharing Utility
 * Handles social media sharing for blog posts
 */

class SocialSharing {
    constructor() {
        this.sharingData = null;
        this.sharingLinks = null;
    }

    /**
     * Initialize social sharing for a blog post or event
     * @param {number} postId - Blog post ID (optional)
     * @param {number} eventId - Event ID (optional)
     */
    async init(postId = null, eventId = null) {
        try {
            const body = {};
            if (postId) {
                body.post_id = postId;
            } else if (eventId) {
                body.event_id = eventId;
            } else {
                console.error('Either postId or eventId must be provided');
                return false;
            }
            
            const response = await fetch('/api/social-sharing/generate-links', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(body)
            });

            if (!response.ok) {
                console.error('API response not OK:', response.status, response.statusText);
                return false;
            }

            const data = await response.json();

            if (data.success) {
                this.sharingData = data.sharing_data;
                this.sharingLinks = data.sharing_links;
                console.log('✅ Social sharing initialized:', {
                    platforms: Object.keys(this.sharingLinks),
                    links: this.sharingLinks
                });
                
                // Sprawdź czy Facebook i Twitter są w linkach
                if (!this.sharingLinks.facebook) {
                    console.warn('⚠️ Facebook nie jest w sharing links!');
                }
                if (!this.sharingLinks.twitter) {
                    console.warn('⚠️ Twitter/X nie jest w sharing links!');
                }
                
                return true;
            } else {
                console.error('❌ Error initializing social sharing:', data.error);
                return false;
            }
        } catch (error) {
            console.error('❌ Error initializing social sharing:', error);
            return false;
        }
    }

    /**
     * Generate sharing links for a specific post or event
     * @param {number} postId - Blog post ID (optional)
     * @param {number} eventId - Event ID (optional)
     */
    async generateLinks(postId = null, eventId = null) {
        return await this.init(postId, eventId);
    }

    /**
     * Share to a specific platform
     * @param {string} platform - Platform name (facebook, twitter, linkedin, etc.)
     * @param {boolean} track - Whether to track the share
     */
    async shareTo(platform, track = true) {
        if (!this.sharingLinks || !this.sharingLinks[platform]) {
            console.error('Sharing links not initialized or platform not available');
            return false;
        }

        const link = this.sharingLinks[platform];
        
        // Special handling for Instagram (copy link instead of opening URL)
        if (link.action === 'copy' || platform === 'instagram') {
            const copied = await this.copyToClipboard();
            if (copied && window.toastManager) {
                window.toastManager.show('Link skopiowany! Wklej go w Instagramie.', 'success');
            }
            return copied;
        }
        
        // Track the share if requested
        if (track && this.sharingData) {
            try {
                const trackData = {
                    platform: platform
                };
                
                // Add post_id or event_id depending on what's available
                if (this.sharingData.post_id) {
                    trackData.post_id = this.sharingData.post_id;
                } else if (this.sharingData.event_id) {
                    trackData.event_id = this.sharingData.event_id;
                }
                
                await fetch('/api/social-sharing/track-share', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    credentials: 'include',
                    body: JSON.stringify(trackData)
                });
            } catch (error) {
                console.error('Error tracking share:', error);
            }
        }

        // Open sharing window
        this.openSharingWindow(link.url, platform);
        return true;
    }

    /**
     * Open sharing window
     * @param {string} url - Sharing URL
     * @param {string} platform - Platform name
     */
    openSharingWindow(url, platform) {
        const width = platform === 'facebook' ? 626 : 550;
        const height = platform === 'facebook' ? 436 : 420;
        
        const left = (screen.width - width) / 2;
        const top = (screen.height - height) / 2;

        window.open(
            url,
            `${platform}_share`,
            `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`
        );
    }

    /**
     * Copy post URL or event full text to clipboard
     */
    async copyToClipboard() {
        if (!this.sharingData) {
            console.error('Sharing data not initialized');
            return false;
        }

        // Dla wydarzeń kopiujemy pełny tekst z informacjami, dla postów tylko URL
        let textToCopy = this.sharingData.post_url || this.sharingData.event_url;
        
        // Jeśli to wydarzenie, zbuduj pełny tekst z informacjami
        if (this.sharingData.event_id && this.sharingData.event_title) {
            const parts = [this.sharingData.event_title];
            
            // Użyj danych z sharingData jeśli są dostępne
            if (this.sharingData.event_date) {
                let dateTimeStr = `Data: ${this.sharingData.event_date}`;
                if (this.sharingData.event_time) {
                    dateTimeStr += ` o ${this.sharingData.event_time}`;
                }
                parts.push(dateTimeStr);
            }
            
            if (this.sharingData.event_description && this.sharingData.event_description.trim()) {
                const shortDesc = this.sharingData.event_description.trim().substring(0, 200);
                parts.push(`Opis: ${shortDesc}${this.sharingData.event_description.length > 200 ? '...' : ''}`);
            }
            
            parts.push(`Link: ${textToCopy}`);
            textToCopy = parts.join('\n');
        }

        try {
            await navigator.clipboard.writeText(textToCopy);
            
            // Show success message
            if (window.toastManager) {
                window.toastManager.show('Link został skopiowany do schowka', 'success');
            }
            
            return true;
        } catch (error) {
            console.error('Error copying to clipboard:', error);
            
            // Fallback for older browsers
            try {
                const textArea = document.createElement('textarea');
                textArea.value = textToCopy;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                
                if (window.toastManager) {
                    window.toastManager.show('Link został skopiowany do schowka', 'success');
                }
                
                return true;
            } catch (fallbackError) {
                console.error('Fallback copy failed:', fallbackError);
                if (window.toastManager) {
                    window.toastManager.show('Nie udało się skopiować linku', 'error');
                }
                return false;
            }
        }
    }

    /**
     * Get sharing data
     */
    getSharingData() {
        return this.sharingData;
    }

    /**
     * Get sharing links
     */
    getSharingLinks() {
        return this.sharingLinks;
    }

    /**
     * Create sharing buttons HTML
     * @param {string} containerId - Container element ID
     * @param {Array} platforms - Platforms to show (optional, shows all if not specified)
     */
    createSharingButtons(containerId, platforms = null) {
        if (!this.sharingLinks) {
            console.error('Sharing links not initialized');
            return false;
        }

        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container with ID '${containerId}' not found`);
            return false;
        }

        const platformsToShow = platforms || Object.keys(this.sharingLinks);
        
        let buttonsHtml = '<div class="social-sharing-buttons d-flex gap-2 flex-wrap">';
        
        platformsToShow.forEach(platform => {
            const link = this.sharingLinks[platform];
            if (link) {
                buttonsHtml += `
                    <button 
                        class="btn btn-sm social-sharing-btn" 
                        style="background-color: ${link.color}; color: white; border: none;"
                        onclick="window.socialSharing.shareTo('${platform}')"
                        title="Udostępnij na ${link.name}"
                        data-platform="${platform}"
                    >
                        <i class="${link.icon}"></i>
                        <span class="d-none d-md-inline ms-1">${link.name}</span>
                    </button>
                `;
            }
        });
        
        // Add copy link button
        buttonsHtml += `
            <button 
                class="btn btn-sm btn-outline-secondary" 
                onclick="window.socialSharing.copyToClipboard()"
                title="Kopiuj link"
            >
                <i class="fas fa-link"></i>
                <span class="d-none d-md-inline ms-1">Kopiuj link</span>
            </button>
        `;
        
        buttonsHtml += '</div>';
        
        container.innerHTML = buttonsHtml;
        return true;
    }

    /**
     * Create compact sharing buttons (icons only)
     * @param {string} containerId - Container element ID
     * @param {Array} platforms - Platforms to show (optional, shows all if not specified)
     */
    createCompactSharingButtons(containerId, platforms = null) {
        if (!this.sharingLinks) {
            console.error('Sharing links not initialized');
            return false;
        }

        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container with ID '${containerId}' not found`);
            return false;
        }

        const platformsToShow = platforms || Object.keys(this.sharingLinks);
        
        let buttonsHtml = '<div class="social-sharing-compact d-flex gap-1">';
        
        platformsToShow.forEach(platform => {
            const link = this.sharingLinks[platform];
            if (link) {
                buttonsHtml += `
                    <button 
                        class="btn btn-sm social-sharing-btn-compact" 
                        style="background-color: ${link.color}; color: white; border: none; width: 40px; height: 40px;"
                        onclick="window.socialSharing.shareTo('${platform}')"
                        title="Udostępnij na ${link.name}"
                        data-platform="${platform}"
                    >
                        <i class="${link.icon}"></i>
                    </button>
                `;
            }
        });
        
        // Add copy link button
        buttonsHtml += `
            <button 
                class="btn btn-sm btn-outline-secondary" 
                style="width: 40px; height: 40px;"
                onclick="window.socialSharing.copyToClipboard()"
                title="Kopiuj link"
            >
                <i class="fas fa-link"></i>
            </button>
        `;
        
        buttonsHtml += '</div>';
        
        container.innerHTML = buttonsHtml;
        return true;
    }

    /**
     * Create floating social bar (vertical bar with icons)
     * @param {string} containerId - Container element ID
     * @param {Array} platforms - Platforms to show (optional, shows all if not specified)
     */
    createFloatingBar(containerId, platforms = null) {
        if (!this.sharingLinks) {
            console.error('❌ Sharing links not initialized');
            return false;
        }

        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`❌ Container with ID '${containerId}' not found`);
            return false;
        }

        const platformsToShow = platforms || Object.keys(this.sharingLinks);
        
        console.log('🔍 Creating floating bar with platforms:', platformsToShow);
        console.log('🔍 Available sharing links:', this.sharingLinks);
        
        let buttonsHtml = '<div class="social-floating-bar">';
        
        let buttonsCount = 0;
        platformsToShow.forEach(platform => {
            const link = this.sharingLinks[platform];
            if (link && link.icon && link.color) {
                // Fallback dla ikony X/Twitter - jeśli fa-x-twitter nie działa, użyj fa-twitter
                let iconClass = link.icon;
                if (platform === 'twitter' && iconClass === 'fab fa-x-twitter') {
                    // Sprawdź czy ikona istnieje, jeśli nie - użyj fallback
                    iconClass = 'fab fa-x-twitter'; // FontAwesome 6.5.1+ powinno mieć
                }
                
                buttonsHtml += `
                    <button 
                        class="social-floating-btn" 
                        style="background-color: ${link.color};"
                        onclick="window.socialSharing.shareTo('${platform}')"
                        title="Udostępnij na ${link.name}"
                        data-platform="${platform}"
                    >
                        <i class="${iconClass}"></i>
                    </button>
                `;
                buttonsCount++;
                console.log(`✅ Added button for ${platform}:`, { icon: iconClass, color: link.color, name: link.name });
            } else {
                console.warn(`⚠️ Platform ${platform} missing icon or color:`, link);
            }
        });
        
        // Add copy link button
        buttonsHtml += `
            <button 
                class="social-floating-btn social-floating-btn-copy" 
                onclick="window.socialSharing.copyToClipboard()"
                title="Kopiuj link"
            >
                <i class="fas fa-link"></i>
            </button>
        `;
        
        buttonsHtml += '</div>';
        
        container.innerHTML = buttonsHtml;
        console.log(`✅ Floating bar created with ${buttonsCount} platform buttons`);
        return true;
    }
}

// Global instance
window.socialSharing = new SocialSharing();

// Utility functions for easy use
window.shareToFacebook = (postId) => {
    window.socialSharing.init(postId).then(() => {
        window.socialSharing.shareTo('facebook');
    });
};

window.shareToTwitter = (postId) => {
    window.socialSharing.init(postId).then(() => {
        window.socialSharing.shareTo('twitter');
    });
};

window.shareToLinkedIn = (postId) => {
    window.socialSharing.init(postId).then(() => {
        window.socialSharing.shareTo('linkedin');
    });
};

window.shareToWhatsApp = (postId) => {
    window.socialSharing.init(postId).then(() => {
        window.socialSharing.shareTo('whatsapp');
    });
};

window.copyPostLink = (postId) => {
    window.socialSharing.init(postId).then(() => {
        window.socialSharing.copyToClipboard();
    });
};

