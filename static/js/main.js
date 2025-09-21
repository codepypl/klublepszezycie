// Main JavaScript for Lepsze Życie Club Landing Page

document.addEventListener('DOMContentLoaded', function() {
    // Initialize AOS (Animate On Scroll) - disabled to avoid conflicts
    // AOS.init({
    //     duration: 800,
    //     easing: 'ease-in-out',
    //     once: true,
    //     offset: 100
    // });

    // Initialize counters
    initializeCounters();
    
    // Initialize smooth scrolling for navigation links
    initializeSmoothScrolling();
    
    // Initialize form validation and submission
    initializeFormHandling();
    
    // Initialize navbar scroll effects
    initializeNavbarEffects();
    
    // Initialize floating elements
    initializeFloatingElements();
    
    // Initialize parallax effects
    initializeParallaxEffects();
    
    // Initialize loading animations
    initializeLoadingAnimations();
});

// Counter Animation
function initializeCounters() {
    const counters = document.querySelectorAll('.counter');
    
    const animateCounter = (counter) => {
        const target = parseInt(counter.textContent.replace(/\D/g, ''));
        const increment = target / 100;
        let current = 0;
        
        const updateCounter = () => {
            if (current < target) {
                current += increment;
                if (current > target) current = target;
                
                if (counter.textContent.includes('+')) {
                    counter.textContent = Math.ceil(current) + '+';
                } else if (counter.textContent.includes('%')) {
                    counter.textContent = Math.ceil(current) + '%';
                } else {
                    counter.textContent = Math.ceil(current);
                }
                
                requestAnimationFrame(updateCounter);
            }
        };
        
        updateCounter();
    };
    
    // Intersection Observer for counters
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                counterObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });
    
    counters.forEach(counter => counterObserver.observe(counter));
}

// Smooth Scrolling
function initializeSmoothScrolling() {
    const navLinks = document.querySelectorAll('a[href^="#"]');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            if (targetSection) {
                const offsetTop = targetSection.offsetTop - 80; // Account for fixed navbar
                
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
                
                // Close mobile menu if open
                const navbarCollapse = document.querySelector('.navbar-collapse');
                if (navbarCollapse.classList.contains('show')) {
                    const bsCollapse = new bootstrap.Collapse(navbarCollapse);
                    bsCollapse.hide();
                }
            }
        });
    });
}

// Form Handling
function initializeFormHandling() {
    const form = document.querySelector('.registration-form');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault(); // Blokujemy domyślne wysłanie
            
            const submitButton = this.querySelector('button[type="submit"]');
            const originalText = submitButton.innerHTML;
            
            // Show loading state
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Wysyłanie...';
            submitButton.disabled = true;
            
            // Get form data as JSON
            const wantsClubNewsInput = this.querySelector('input[name="wants_club_news"]');
            const jsonData = {
                first_name: this.querySelector('input[name="first_name"]').value,
                email: this.querySelector('input[name="email"]').value,
                phone: this.querySelector('input[name="phone"]').value || '',
                wants_club_news: wantsClubNewsInput ? wantsClubNewsInput.checked : false
            };
            
            // Send AJAX request
            console.log('Sending registration request to: /register');
            console.log('Form data:', jsonData);
            
            fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(jsonData)
            })
            .then(response => {
                console.log('Response status:', response.status);
                console.log('Response headers:', response.headers);
                return response.json();
            })
            .then(data => {
                console.log('Response data:', data);
                if (data.success) {
                    // Show success message
                    showNotification(data.message, 'success');
                    // Reset form
                    this.reset();
                    // Reset button
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                } else {
                    // Show error message
                    showNotification(data.error || 'Wystąpił błąd podczas rejestracji.', 'error');
                    // Reset button
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                }
            })
            .catch(error => {
                console.error('Fetch error:', error);
                showNotification('Wystąpił błąd podczas rejestracji. Spróbuj ponownie.', 'error');
                // Reset button
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            });
        });
        
        // Real-time form validation
        const inputs = form.querySelectorAll('input[required]');
        inputs.forEach(input => {
            input.addEventListener('blur', validateField);
            input.addEventListener('input', clearFieldError);
        });
    }
    
    // Initialize timeline event registration forms
    initializeTimelineForms();
}

// Field Validation
function validateField(e) {
    const field = e.target;
    const value = field.value.trim();
    
    // Remove existing error styling
    field.classList.remove('is-invalid');
    
    // Check if field is empty
    if (!value) {
        field.classList.add('is-invalid');
        showFieldError(field, 'To pole jest wymagane.');
        return false;
    }
    
    // Email validation
    if (field.type === 'email' && !isValidEmail(value)) {
        field.classList.add('is-invalid');
        showFieldError(field, 'Proszę wprowadzić poprawny adres email.');
        return false;
    }
    
    return true;
}

// Email validation helper
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Show field error
function showFieldError(field, message) {
    // Remove existing error message
    const existingError = field.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
    
    // Create and show error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);
}

// Clear field error
function clearFieldError(e) {
    const field = e.target;
    field.classList.remove('is-invalid');
    
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// Notification System
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.custom-notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `custom-notification alert alert-${type} alert-dismissible fade show`;
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Navbar Effects
function initializeNavbarEffects() {
    const navbar = document.querySelector('.navbar');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 100) {
            navbar.classList.add('navbar-scrolled');
        } else {
            navbar.classList.remove('navbar-scrolled');
        }
    });
}

// Floating Elements Animation
function initializeFloatingElements() {
    const floatingCards = document.querySelectorAll('.floating-card');
    
    floatingCards.forEach((card, index) => {
        // Add random delay for more natural movement
        const randomDelay = Math.random() * 2;
        card.style.animationDelay = `${randomDelay}s`;
        
        // Add hover effect
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05) translateY(-10px)';
            this.style.zIndex = '10';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1) translateY(0)';
            this.style.zIndex = '1';
        });
    });
}

// Parallax Effects
function initializeParallaxEffects() {
    const parallaxElements = document.querySelectorAll('.hero-bg-animation');
    
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        
        parallaxElements.forEach(element => {
            const speed = 0.5;
            element.style.transform = `translateY(${scrolled * speed}px)`;
        });
    });
}

// Loading Animations
function initializeLoadingAnimations() {
    // Add loading class to elements
    const loadingElements = document.querySelectorAll('.benefit-card, .testimonial-card, .pillar-item');
    
    loadingElements.forEach((element, index) => {
        element.classList.add('loading');
        
        // Stagger the loading animation
        setTimeout(() => {
            element.classList.add('loaded');
        }, index * 100);
    });
}

// Intersection Observer for animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate-in');
        }
    });
}, observerOptions);

// Observe elements for animation
document.addEventListener('DOMContentLoaded', () => {
    const animateElements = document.querySelectorAll('.benefit-card, .testimonial-card, .pillar-item');
    animateElements.forEach(el => observer.observe(el));
});

// Add CSS for loading animations
const style = document.createElement('style');
style.textContent = `
    .loading {
        opacity: 0;
        transform: translateY(30px);
        transition: all 0.6s ease;
    }
    
    .loading.loaded {
        opacity: 1;
        transform: translateY(0);
    }
    
    .navbar-scrolled {
        background-color: rgba(255, 255, 255, 0.98) !important;
        box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1) !important;
    }
    
    .animate-in {
        animation: slideInUp 0.6s ease forwards;
    }
    
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .invalid-feedback {
        display: block;
        color: #dc3545;
        font-size: 0.875rem;
        margin-top: 0.25rem;
    }
    
    .form-control.is-invalid {
        border-color: #dc3545;
        box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25);
    }
`;

document.head.appendChild(style);

// Performance optimization: Debounce scroll events
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

// Apply debouncing to scroll events
const debouncedScrollHandler = debounce(() => {
    // Handle scroll events here
}, 16); // ~60fps

window.addEventListener('scroll', debouncedScrollHandler);

// Add some interactive hover effects for cards
document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.benefit-card, .testimonial-card');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
});

// Initialize tooltips if Bootstrap is available
if (typeof bootstrap !== 'undefined') {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Add some Easter eggs for fun
document.addEventListener('keydown', (e) => {
    // Konami code: ↑↑↓↓←→←→BA
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown' || e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
        // You could add some fun effects here
        console.log('🎮 Easter egg detected!');
    }
});

// Smooth reveal animation for sections
const revealSections = () => {
    const sections = document.querySelectorAll('section');
    
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.offsetHeight;
        const windowHeight = window.innerHeight;
        const scrollY = window.scrollY;
        
        if (scrollY + windowHeight > sectionTop + 100) {
            section.classList.add('revealed');
        }
    });
};

window.addEventListener('scroll', debounce(revealSections, 16));

// Add CSS for reveal animation
const revealStyle = document.createElement('style');
revealStyle.textContent = `
    section {
        opacity: 0;
        transform: translateY(20px);
        transition: all 0.8s ease;
    }
    
    section.revealed {
        opacity: 1;
        transform: translateY(0);
    }
    
    /* Hero section should be visible immediately */
    section#hero {
        opacity: 1 !important;
        transform: translateY(0) !important;
    }
    
    /* Blog pages main content should be visible immediately */
    main {
        opacity: 1 !important;
        transform: translateY(0) !important;
    }
    
    /* Blog post hero section should be visible immediately */
    section.blog-post-hero {
        opacity: 1 !important;
        transform: translateY(0) !important;
    }
    
    /* Blog index hero section should be visible immediately */
    section.blog-hero {
        opacity: 1 !important;
        transform: translateY(0) !important;
    }
    
    /* Blog header should be visible immediately */
    .blog-header {
        opacity: 1 !important;
        transform: translateY(0) !important;
    }
    
    /* Search header should be visible immediately */
    section.search-header {
        opacity: 1 !important;
        transform: translateY(0) !important;
    }
    
    /* Search header content should be visible immediately */
    .search-header-content {
        opacity: 1 !important;
        transform: translateY(0) !important;
    }
    
    section:first-child {
        opacity: 1;
        transform: translateY(0);
    }
`;

document.head.appendChild(revealStyle);

// Timeline Event Registration Forms
function initializeTimelineForms() {
    const timelineForms = document.querySelectorAll('.event-registration-form');
    
    timelineForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitButton = this.querySelector('button[type="submit"]');
            const originalText = submitButton.innerHTML;
            const eventId = this.getAttribute('data-event-id');
            
            // Show loading state
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Wysyłanie...';
            submitButton.disabled = true;
            
            // Get form data
            const formData = {
                first_name: this.querySelector('input[name="first_name"]').value,
                email: this.querySelector('input[name="email"]').value,
                event_id: eventId
            };
            
            // Send registration request
            fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification(data.message, 'success');
                    this.reset();
                } else {
                    showNotification(data.error || 'Wystąpił błąd podczas rejestracji.', 'error');
                }
            })
            .catch(error => {
                console.error('Registration error:', error);
                showNotification('Wystąpił błąd podczas rejestracji. Spróbuj ponownie.', 'error');
            })
            .finally(() => {
                // Reset button
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            });
        });
    });
}

