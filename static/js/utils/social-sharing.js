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
     * Initialize social sharing for a blog post
     * @param {number} postId - Blog post ID
     */
    async init(postId) {
        try {
            const response = await fetch('/api/social-sharing/generate-links', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({ post_id: postId })
            });

            const data = await response.json();

            if (data.success) {
                this.sharingData = data.sharing_data;
                this.sharingLinks = data.sharing_links;
                return true;
            } else {
                console.error('Error initializing social sharing:', data.error);
                return false;
            }
        } catch (error) {
            console.error('Error initializing social sharing:', error);
            return false;
        }
    }

    /**
     * Generate sharing links for a specific post
     * @param {number} postId - Blog post ID
     */
    async generateLinks(postId) {
        return await this.init(postId);
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
        
        // Track the share if requested
        if (track && this.sharingData) {
            try {
                await fetch('/api/social-sharing/track-share', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    credentials: 'include',
                    body: JSON.stringify({
                        post_id: this.sharingData.post_id,
                        platform: platform
                    })
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
     * Copy post URL to clipboard
     */
    async copyToClipboard() {
        if (!this.sharingData) {
            console.error('Sharing data not initialized');
            return false;
        }

        try {
            await navigator.clipboard.writeText(this.sharingData.post_url);
            
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
                textArea.value = this.sharingData.post_url;
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

