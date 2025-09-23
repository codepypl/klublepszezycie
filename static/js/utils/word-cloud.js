/**
 * Word Cloud Positioning Script
 * Positions tags in a circular/cloud-like pattern
 */
class WordCloud {
    constructor(container) {
        this.container = container;
        this.tags = container.querySelectorAll('.tag-cloud-item');
        this.centerX = 0;
        this.centerY = 0;
        this.radius = 80;
        this.init();
    }

    init() {
        console.log('WordCloud init - tags found:', this.tags.length);
        if (this.tags.length === 0) {
            console.log('No tags found, skipping initialization');
            return;
        }
        
        this.calculateCenter();
        this.positionTags();
        this.addEventListeners();
        console.log('WordCloud initialized successfully');
    }

    calculateCenter() {
        const rect = this.container.getBoundingClientRect();
        this.centerX = rect.width / 2;
        this.centerY = rect.height / 2;
    }

    positionTags() {
        const totalTags = this.tags.length;
        console.log(`Positioning ${totalTags} tags`);
        
        this.tags.forEach((tag, index) => {
            // Create different patterns based on tag count
            let x, y;
            
            if (totalTags <= 3) {
                // Simple linear arrangement for few tags
                x = this.centerX + (index - (totalTags - 1) / 2) * 60;
                y = this.centerY;
            } else if (totalTags <= 6) {
                // Circular arrangement
                const angle = (index / totalTags) * 2 * Math.PI;
                const radius = this.radius * 0.8;
                x = this.centerX + Math.cos(angle) * radius;
                y = this.centerY + Math.sin(angle) * radius;
            } else {
                // Spiral arrangement for many tags
                const angle = (index / totalTags) * 4 * Math.PI;
                const radius = this.radius * (0.3 + (index / totalTags) * 0.7);
                x = this.centerX + Math.cos(angle) * radius;
                y = this.centerY + Math.sin(angle) * radius;
            }

            // Add some randomness to make it look more natural
            const randomOffset = 20;
            x += (Math.random() - 0.5) * randomOffset;
            y += (Math.random() - 0.5) * randomOffset;

            // Apply position
            tag.style.left = `${x}px`;
            tag.style.top = `${y}px`;
            tag.style.transform = 'translate(-50%, -50%)';
            
            console.log(`Tag ${index + 1}: ${tag.textContent} positioned at (${x}, ${y})`);
        });
    }

    addEventListeners() {
        // Reposition on window resize
        window.addEventListener('resize', () => {
            this.calculateCenter();
            this.positionTags();
        });
    }
}

// Initialize word clouds when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeWordClouds();
});

// Also initialize if DOM is already loaded
if (document.readyState !== 'loading') {
    initializeWordClouds();
}

// Function to initialize word clouds
function initializeWordClouds() {
    const tagClouds = document.querySelectorAll('.tag-cloud-container');
    console.log('Found tag cloud containers:', tagClouds.length);
    
    tagClouds.forEach((container, index) => {
        console.log(`Initializing word cloud ${index + 1}`);
        new WordCloud(container);
    });
}

// Re-initialize on window resize
window.addEventListener('resize', function() {
    setTimeout(initializeWordClouds, 100);
});
