// Form Validators - JavaScript counterpart to app/utils/validation.py
class FormValidators {
    /**
     * Validate TinyMCE content
     * @param {string} editorId - TinyMCE editor ID
     * @param {string} fieldName - Human readable field name for error messages
     * @returns {boolean} - true if valid, false if invalid
     */
    static validateTinyMCE(editorId, fieldName = 'Treść') {
        const content = tinymce.get(editorId) ? tinymce.get(editorId).getContent() : '';
        
        // Check if content is empty or contains only empty paragraphs
        if (!content || content.trim() === '' || content === '<p></p>' || content === '<p><br></p>') {
            window.toastManager.error(`${fieldName} jest wymagana`);
            return false;
        }
        
        return true;
    }

    /**
     * Validate required text field
     * @param {string} fieldId - Field ID
     * @param {string} fieldName - Human readable field name
     * @returns {boolean} - true if valid, false if invalid
     */
    static validateRequired(fieldId, fieldName) {
        const field = document.getElementById(fieldId);
        if (!field || !field.value || field.value.trim() === '') {
            window.toastManager.error(`${fieldName} jest wymagane`);
            return false;
        }
        return true;
    }

    /**
     * Validate email format (consistent with Python validation.py)
     * @param {string} fieldId - Field ID
     * @param {string} fieldName - Human readable field name
     * @returns {boolean} - true if valid, false if invalid
     */
    static validateEmail(fieldId, fieldName = 'Email') {
        const field = document.getElementById(fieldId);
        if (!field || !field.value) {
            window.toastManager.error(`${fieldName} jest wymagany`);
            return false;
        }
        
        // Same regex as Python: r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailRegex.test(field.value)) {
            window.toastManager.error(`${fieldName} ma nieprawidłowy format`);
            return false;
        }
        
        return true;
    }

    /**
     * Validate phone number format (consistent with Python validation.py)
     * @param {string} fieldId - Field ID
     * @param {string} fieldName - Human readable field name
     * @returns {boolean} - true if valid, false if invalid
     */
    static validatePhone(fieldId, fieldName = 'Telefon') {
        const field = document.getElementById(fieldId);
        if (!field || !field.value) {
            return true; // Phone is optional
        }
        
        // Remove all non-digit characters (same as Python)
        const digitsOnly = field.value.replace(/\D/g, '');
        
        // Check if it has 9 digits (Polish phone number)
        if (digitsOnly.length !== 9) {
            window.toastManager.error(`${fieldName} musi mieć 9 cyfr`);
            return false;
        }
        
        return true;
    }

    /**
     * Validate slug format
     * @param {string} fieldId - Field ID
     * @param {string} fieldName - Human readable field name
     * @returns {boolean} - true if valid, false if invalid
     */
    static validateSlug(fieldId, fieldName = 'Slug') {
        const field = document.getElementById(fieldId);
        if (!field || !field.value) {
            window.toastManager.error(`${fieldName} jest wymagany`);
            return false;
        }
        
        const slugRegex = /^[a-z0-9-]+$/;
        if (!slugRegex.test(field.value)) {
            window.toastManager.error(`${fieldName} może zawierać tylko małe litery, cyfry i myślniki`);
            return false;
        }
        
        return true;
    }

    /**
     * Validate file upload (consistent with Python validation.py)
     * @param {string} fieldId - Field ID
     * @param {Array} allowedTypes - Allowed file types (MIME types)
     * @param {number} maxSize - Max file size in MB
     * @param {string} fieldName - Human readable field name
     * @returns {boolean} - true if valid, false if invalid
     */
    static validateFile(fieldId, allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'], maxSize = 100, fieldName = 'Plik') {
        const field = document.getElementById(fieldId);
        if (!field || !field.files || field.files.length === 0) {
            return true; // File is optional
        }
        
        const file = field.files[0];
        
        // Check file type (consistent with Python ALLOWED_EXTENSIONS)
        const allowedExtensions = ['png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'mov'];
        const fileExtension = file.name.split('.').pop().toLowerCase();
        
        if (!allowedExtensions.includes(fileExtension)) {
            window.toastManager.error(`${fieldName} musi być w formacie: ${allowedExtensions.join(', ').toUpperCase()}`);
            return false;
        }
        
        // Check file size (100MB max, consistent with Python)
        const maxSizeBytes = maxSize * 1024 * 1024;
        if (file.size > maxSizeBytes) {
            window.toastManager.error(`${fieldName} nie może być większy niż ${maxSize}MB`);
            return false;
        }
        
        return true;
    }

    /**
     * Validate form with multiple fields
     * @param {Array} validations - Array of validation objects
     * @returns {boolean} - true if all validations pass, false otherwise
     */
    static validateForm(validations) {
        for (const validation of validations) {
            let isValid = false;
            
            switch (validation.type) {
                case 'required':
                    isValid = this.validateRequired(validation.fieldId, validation.fieldName);
                    break;
                case 'email':
                    isValid = this.validateEmail(validation.fieldId, validation.fieldName);
                    break;
                case 'slug':
                    isValid = this.validateSlug(validation.fieldId, validation.fieldName);
                    break;
                case 'tinymce':
                    isValid = this.validateTinyMCE(validation.fieldId, validation.fieldName);
                    break;
                case 'file':
                    isValid = this.validateFile(validation.fieldId, validation.allowedTypes, validation.maxSize, validation.fieldName);
                    break;
                default:
                    console.warn(`Unknown validation type: ${validation.type}`);
                    isValid = true;
            }
            
            if (!isValid) {
                return false;
            }
        }
        
        return true;
    }

    /**
     * Validate blog post form
     * @param {string} formType - 'add' or 'edit'
     * @returns {boolean} - true if valid, false if invalid
     */
    static validateBlogPost(formType = 'add') {
        const contentFieldId = formType === 'add' ? 'postContent' : 'editPostContent';
        const titleFieldId = formType === 'add' ? 'postTitle' : 'editPostTitle';
        const slugFieldId = formType === 'add' ? 'postSlug' : 'editPostSlug';
        const imageFieldId = formType === 'add' ? 'postFeaturedImage' : 'editPostFeaturedImage';
        
        return this.validateForm([
            { type: 'required', fieldId: titleFieldId, fieldName: 'Tytuł artykułu' },
            { type: 'required', fieldId: slugFieldId, fieldName: 'Slug' },
            { type: 'slug', fieldId: slugFieldId, fieldName: 'Slug' },
            { type: 'tinymce', fieldId: contentFieldId, fieldName: 'Treść artykułu' },
            { type: 'file', fieldId: imageFieldId, maxSize: 100, fieldName: 'Zdjęcie główne' }
        ]);
    }
}

// Make validators available globally
window.FormValidators = FormValidators;
