/**
 * Helper functions for safe API calls
 */

/**
 * Safely parse JSON response, handling HTML redirects and errors
 * @param {Response} response - The fetch response object
 * @returns {Promise<Object>} Parsed JSON data
 * @throws {Error} If response is not JSON or contains error
 */
async function safeJsonParse(response) {
    const contentType = response.headers.get('content-type');
    
    if (!contentType || !contentType.includes('application/json')) {
        if (response.status === 401 || response.status === 403) {
            throw new Error('Brak uprawnień. Zaloguj się ponownie.');
        } else if (response.status >= 400) {
            throw new Error(`Błąd serwera (${response.status}). Spróbuj ponownie.`);
        } else {
            throw new Error('Serwer zwrócił nieprawidłową odpowiedź. Sprawdź czy jesteś zalogowany.');
        }
    }
    
    return await response.json();
}

/**
 * Make a safe API call with automatic JSON parsing and error handling
 * @param {string} url - The API endpoint URL
 * @param {Object} options - Fetch options
 * @returns {Promise<Object>} Parsed JSON response
 */
async function safeApiCall(url, options = {}) {
    const defaultOptions = {
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    };
    
    const response = await fetch(url, { ...defaultOptions, ...options });
    
    if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
            throw new Error('Brak uprawnień. Zaloguj się ponownie.');
        } else if (response.status >= 500) {
            throw new Error('Błąd serwera. Spróbuj ponownie później.');
        } else {
            throw new Error(`Błąd ${response.status}. Spróbuj ponownie.`);
        }
    }
    
    return await safeJsonParse(response);
}

// Export functions for use in other scripts
window.safeJsonParse = safeJsonParse;
window.safeApiCall = safeApiCall;
