/**
 * Centralized slug generation utility
 * Provides consistent slug generation across all admin pages
 */
class SlugGenerator {
    /**
     * Create a URL-friendly slug from text
     * @param {string} text - Input text to convert to slug
     * @param {number} maxLength - Maximum length of the slug (default: 200)
     * @returns {string} URL-friendly slug
     */
    static createSlug(text, maxLength = 200) {
        if (!text) return '';
        
        // Convert to lowercase
        let slug = text.toString().toLowerCase().trim();
        
        // Remove Polish diacritics
        const diacritics = {
            'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
            'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'
        };
        
        slug = slug.replace(/[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]/g, char => diacritics[char] || char);
        
        // Replace spaces and special characters with hyphens
        slug = slug.replace(/[^\w\s-]/g, '');
        slug = slug.replace(/[-\s]+/g, '-');
        
        // Remove leading/trailing hyphens
        slug = slug.replace(/^-+|-+$/g, '');
        
        // Truncate to maxLength
        if (slug.length > maxLength) {
            slug = slug.substring(0, maxLength).replace(/-+$/, '');
        }
        
        return slug;
    }

    /**
     * Setup auto-slug generation for title/slug input pairs
     * @param {string} titleSelector - CSS selector for title input
     * @param {string} slugSelector - CSS selector for slug input
     * @param {number} maxLength - Maximum slug length
     * @param {boolean} alwaysGenerate - If true, always generate slug (default: false)
     */
    static setupAutoSlug(titleSelector, slugSelector, maxLength = 200, alwaysGenerate = false) {
        const titleInput = document.querySelector(titleSelector);
        const slugInput = document.querySelector(slugSelector);
        
        if (titleInput && slugInput) {
            titleInput.addEventListener('input', () => {
                if (alwaysGenerate || !slugInput.value) {
                    slugInput.value = this.createSlug(titleInput.value, maxLength);
                }
            });
        }
    }

    /**
     * Setup auto-slug generation for multiple title/slug pairs
     * @param {Array} pairs - Array of {titleSelector, slugSelector, maxLength, alwaysGenerate} objects
     */
    static setupMultipleAutoSlug(pairs) {
        pairs.forEach(pair => {
            this.setupAutoSlug(
                pair.titleSelector, 
                pair.slugSelector, 
                pair.maxLength || 200,
                pair.alwaysGenerate || false
            );
        });
    }
}

// Make it globally available
window.SlugGenerator = SlugGenerator;
