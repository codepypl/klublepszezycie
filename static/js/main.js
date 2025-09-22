/**
 * Main JavaScript file for Klub Lepsze Życie
 * Simple, clean, and maintainable code
 */

// Global variables
let observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
};

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Main.js loaded');
    
    // Initialize all components
    console.log('🚀 Starting component initialization...');
    initializeAnimations();
    initializeCounters();
    initializeSmoothScrolling();
    initializeClubRegistration();
    console.log('🎯 About to initialize event registration...');
    initializeEventRegistration();
    initializeCountdown();
    initializeTooltips();
    
    console.log('✅ All components initialized');
});

/**
 * Initialize AOS animations
 */
function initializeAnimations() {
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 1000,
            once: true,
            offset: 100
        });
        console.log('✅ AOS animations initialized');
    }
}

/**
 * Initialize counter animations
 */
function initializeCounters() {
    const counters = document.querySelectorAll('.counter');
    
    if (counters.length === 0) {
        return;
    }
    
    const animateCounter = (counter) => {
        const target = parseInt(counter.getAttribute('data-target'));
        const increment = target / 100;
        let current = 0;
        
        const updateCounter = () => {
            if (current < target) {
                current += increment;
                counter.textContent = Math.ceil(current);
                requestAnimationFrame(updateCounter);
            } else {
                counter.textContent = target;
            }
        };
        
        updateCounter();
    };
    
    // Use Intersection Observer to trigger animations
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                counterObserver.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    counters.forEach(counter => {
        counterObserver.observe(counter);
    });
    
    console.log('✅ Counter animations initialized');
}

/**
 * Initialize smooth scrolling for anchor links
 */
function initializeSmoothScrolling() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            
            // Skip if it's just '#'
            if (href === '#') {
                return;
            }
            
            const target = document.querySelector(href);
            
            if (target) {
                e.preventDefault();
                
                const offsetTop = target.offsetTop - 80; // Account for fixed navbar
                
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    console.log('✅ Smooth scrolling initialized');
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        console.log('✅ Tooltips initialized');
    }
}

/**
 * Utility function to show error messages
 * @param {string} message - Error message to display
 */
function showError(message) {
    showAlert(message, 'danger');
}

/**
 * Utility function to show success messages
 * @param {string} message - Success message to display
 */
function showSuccess(message) {
    showAlert(message, 'success');
}

/**
 * Show alert message
 * @param {string} message - Message to display
 * @param {string} type - Alert type (success, danger, warning, info)
 */
function showAlert(message, type = 'info') {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert-positioned');
    existingAlerts.forEach(alert => alert.remove());
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show alert-positioned`;
    alertDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px; max-width: 500px;';
    
    const iconClass = type === 'success' ? 'fa-check-circle' : 
                     type === 'danger' ? 'fa-exclamation-circle' :
                     type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle';
    
    alertDiv.innerHTML = `
        <i class="fas ${iconClass} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.classList.remove('show');
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.parentNode.removeChild(alertDiv);
                }
            }, 150);
        }
    }, 5000);
}

/**
 * Utility function to format date
 * @param {Date} date - Date to format
 * @param {string} locale - Locale for formatting
 * @returns {string} Formatted date string
 */
function formatDate(date, locale = 'pl-PL') {
    if (!date) return '';
    
    const d = new Date(date);
    return d.toLocaleDateString(locale, {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Utility function to debounce function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Utility function to throttle function calls
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function} Throttled function
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Initialize Event Registration Modal
 */
function initializeEventRegistration() {
    console.log('🔍 Looking for event registration elements...');
    
    const eventRegistrationModal = document.getElementById('eventRegistrationModal');
    const modalEventId = document.getElementById('modalEventId');
    const submitBtn = document.getElementById('submitEventRegistration');
    
    console.log('🔍 Elements found:');
    console.log('  - eventRegistrationModal:', eventRegistrationModal ? '✅' : '❌');
    console.log('  - modalEventId:', modalEventId ? '✅' : '❌');
    console.log('  - submitBtn:', submitBtn ? '✅' : '❌');
    
    if (!eventRegistrationModal || !modalEventId || !submitBtn) {
        console.log('❌ Event registration modal not found, skipping initialization');
        return;
    }
    
    console.log('🎯 Initializing event registration modal');
    
    // Check if modal elements exist
    const modalEventTitleText = document.getElementById('modalEventTitleText');
    const modalEventStartDate = document.getElementById('modalEventStartDate');
    const modalEventEndDate = document.getElementById('modalEventEndDate');
    const modalEventLocation = document.getElementById('modalEventLocation');
    
    // Handle modal show
    eventRegistrationModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        const eventId = button.getAttribute('data-event-id');
        const eventTitle = button.getAttribute('data-event-title');
        
        // Reset form first
        const form = document.getElementById('eventRegistrationForm');
        if (form) {
            form.reset();
        }
        
        // Set basic data
        modalEventId.value = eventId;
        
        // Set event title
        const modalEventTitle = document.getElementById('modalEventTitle');
        if (modalEventTitle) {
            modalEventTitle.textContent = eventTitle || 'Wydarzenie';
        }
        
        // Fetch full event details from API
        if (eventId) {
            fetch(`/api/event-schedule/${eventId}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(eventData => {
                    if (eventData.success && eventData.event) {
                        const event = eventData.event;
                        
                        // Update modal with event details
                        if (modalEventTitleText) {
                            modalEventTitleText.textContent = event.title;
                        }
                        
                        // Update dates
                        if (event.event_date && modalEventStartDate) {
                            const startDate = new Date(event.event_date);
                            const formattedStart = startDate.toLocaleDateString('pl-PL') + ' o ' + 
                                startDate.toLocaleTimeString('pl-PL', {hour: '2-digit', minute: '2-digit'});
                            modalEventStartDate.textContent = formattedStart;
                        }
                        
                        if (event.end_date && modalEventEndDate) {
                            const endDate = new Date(event.end_date);
                            const formattedEnd = endDate.toLocaleDateString('pl-PL') + ' o ' + 
                                endDate.toLocaleTimeString('pl-PL', {hour: '2-digit', minute: '2-digit'});
                            modalEventEndDate.textContent = formattedEnd;
                        } else if (modalEventEndDate) {
                            modalEventEndDate.textContent = 'Nie określono';
                        }
                        
                        // Update location
                        if (modalEventLocation) {
                            modalEventLocation.textContent = event.location || 'Nie podano';
                        }
                    }
                })
                .catch(error => {
                    console.error('Error fetching event details:', error);
                    showError('Nie udało się pobrać danych wydarzenia. Spróbuj ponownie.');
                });
        }
    });
    
    // Handle form submission
    submitBtn.addEventListener('click', function() {
        // Prevent multiple submissions
        if (submitBtn.disabled) {
            return;
        }
        
        const form = document.getElementById('eventRegistrationForm');
        const formData = new FormData(form);
        
        // Convert FormData to JSON
        const data = {
            first_name: formData.get('first_name'),
            email: formData.get('email'),
            phone: formData.get('phone'),
            wants_club_news: formData.get('wants_club_news') === 'true',
            event_id: modalEventId.value
        };
        
        // Validate required fields
        if (!data.first_name || !data.email || !data.event_id) {
            showError('Wszystkie wymagane pola muszą być wypełnione.');
            return;
        }
        
        // Disable submit button immediately
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Zapisuję...';
        
        console.log('📤 Sending event registration data:', data);
        console.log('📤 URL:', `/register-event/${data.event_id}`);
        
        fetch(`/register-event/${data.event_id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            console.log('📡 Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(responseData => {
            console.log('📊 Response data:', responseData);
            if (responseData.success) {
                showSuccess('Dziękujemy! Zostałeś zapisany na wydarzenie. Sprawdź swój email.');
                const modal = bootstrap.Modal.getInstance(eventRegistrationModal);
                modal.hide();
            } else {
                showError('Wystąpił błąd: ' + (responseData.message || 'Spróbuj ponownie.'));
            }
        })
        .catch(error => {
            console.error('Registration error:', error);
            showError('Wystąpił błąd podczas rejestracji. Spróbuj ponownie.');
        })
        .finally(() => {
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-calendar-check me-2"></i>Zarezerwuj miejsce';
        });
    });
}

/**
 * Initialize Countdown Timer
 */
function initializeCountdown() {
    const countdownElement = document.querySelector('.countdown-timer');
    if (!countdownElement) {
        console.log('Countdown timer not found, skipping initialization');
        return;
    }
    
    console.log('🎯 Initializing countdown timer');
    
    function updateCountdown() {
        const eventDate = new Date(countdownElement.dataset.eventDate);
        const now = new Date();
        const timeDiff = eventDate - now;
        
        if (timeDiff <= 0) {
            countdownElement.innerHTML = '<div class="alert alert-warning"><strong>Wydarzenie się rozpoczęło!</strong></div>';
            return;
        }
        
        const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((timeDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeDiff % (1000 * 60)) / 1000);
        
        // Update countdown display
        const daysEl = document.getElementById('days');
        const hoursEl = document.getElementById('hours');
        const minutesEl = document.getElementById('minutes');
        const secondsEl = document.getElementById('seconds');
        
        if (daysEl) daysEl.textContent = days.toString().padStart(2, '0');
        if (hoursEl) hoursEl.textContent = hours.toString().padStart(2, '0');
        if (minutesEl) minutesEl.textContent = minutes.toString().padStart(2, '0');
        if (secondsEl) secondsEl.textContent = seconds.toString().padStart(2, '0');
    }
    
    updateCountdown();
    setInterval(updateCountdown, 1000);
}

/**
 * Initialize Club Registration Form
 */
function initializeClubRegistration() {
    const clubRegistrationForm = document.getElementById('clubRegistrationForm');
    const clubRegistrationBtn = document.getElementById('clubRegistrationBtn');
    
    if (!clubRegistrationForm || !clubRegistrationBtn) {
        console.log('Club registration form not found, skipping initialization');
        return;
    }
    
    console.log('🎯 Initializing club registration form');
    
    clubRegistrationForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Prevent multiple submissions
        if (clubRegistrationBtn.disabled) {
            console.log('Club registration form already submitting, ignoring');
            return;
        }
        
        const formData = new FormData(clubRegistrationForm);
        const data = {
            first_name: formData.get('first_name'),
            email: formData.get('email'),
            phone: formData.get('phone') || ''
        };
        
        // Validate required fields
        if (!data.first_name || !data.email) {
            showError('Imię i email są wymagane.');
            return;
        }
        
        // Disable button and show loading
        clubRegistrationBtn.disabled = true;
        const originalText = clubRegistrationBtn.innerHTML;
        clubRegistrationBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Zapisuję...';
        
        // Send registration request
        fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccess(data.message || 'Dziękujemy! Zostałeś dodany do Klubu Lepsze Życie.');
                clubRegistrationForm.reset();
            } else {
                showError(data.message || 'Wystąpił błąd podczas rejestracji. Spróbuj ponownie.');
            }
        })
        .catch(error => {
            console.error('Club registration error:', error);
            showError('Wystąpił błąd podczas rejestracji. Spróbuj ponownie.');
        })
        .finally(() => {
            // Re-enable button
            clubRegistrationBtn.disabled = false;
            clubRegistrationBtn.innerHTML = originalText;
        });
    });
}

// Export functions for use in other scripts
window.showError = showError;
window.showSuccess = showSuccess;
window.formatDate = formatDate;
window.debounce = debounce;
window.throttle = throttle;