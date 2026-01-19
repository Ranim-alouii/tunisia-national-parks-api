// ===== TUNISIA NATIONAL PARKS - PREMIUM JAVASCRIPT =====

// ===== GLOBAL CONFIGURATION =====
const CONFIG = {
    animation: {
        duration: 800,
        easing: 'ease-out-cubic',
        once: true,
        offset: 50
    },
    scroll: {
        threshold: 50,
        offset: 100
    },
    search: {
        debounce: 300,
        minLength: 2
    }
};

// ===== UTILITY FUNCTIONS =====

// Debounce function for performance
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

// Check if element is in viewport
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// Smooth scroll to element
function smoothScrollTo(element, offset = 0) {
    const elementPosition = element.offsetTop;
    const offsetPosition = elementPosition - offset;

    window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
    });
}

// ===== NAVIGATION SYSTEM =====

// Navbar scroll detection and effects
function initializeNavbar() {
    const navbar = document.querySelector('.professional-navbar');
    const navLinks = document.querySelectorAll('.nav-link-professional');
    const mobileToggle = document.querySelector('.navbar-mobile-toggle');
    const navMenu = document.querySelector('.navbar-nav');

    if (!navbar) return;

    // Scroll detection
    const handleScroll = debounce(() => {
        if (window.scrollY > CONFIG.scroll.threshold) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }

        // Update active nav link based on scroll position
        updateActiveNavLink(navLinks);
    }, 10);

    window.addEventListener('scroll', handleScroll);

    // Mobile menu toggle
    if (mobileToggle && navMenu) {
        mobileToggle.addEventListener('click', () => {
            const isExpanded = mobileToggle.getAttribute('aria-expanded') === 'true';
            mobileToggle.setAttribute('aria-expanded', !isExpanded);
            navMenu.classList.toggle('active');

            // Update icon
            const icon = mobileToggle.querySelector('i');
            if (icon) {
                icon.classList.toggle('fa-bars');
                icon.classList.toggle('fa-times');
            }
        });

        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!navbar.contains(e.target) && navMenu.classList.contains('active')) {
                navMenu.classList.remove('active');
                mobileToggle.setAttribute('aria-expanded', 'false');
                const icon = mobileToggle.querySelector('i');
                if (icon) {
                    icon.classList.add('fa-bars');
                    icon.classList.remove('fa-times');
                }
            }
        });

        // Close mobile menu on nav link click
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
                mobileToggle.setAttribute('aria-expanded', 'false');
                const icon = mobileToggle.querySelector('i');
                if (icon) {
                    icon.classList.add('fa-bars');
                    icon.classList.remove('fa-times');
                }
            });
        });
    }

    // Dropdown menus
    initializeDropdowns();
}

// Update active navigation link based on scroll position
function updateActiveNavLink(navLinks) {
    const sections = document.querySelectorAll('section[id]');
    const scrollPosition = window.scrollY + CONFIG.scroll.offset;

    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.offsetHeight;
        const sectionId = section.getAttribute('id');

        if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
            navLinks.forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === `#${sectionId}`) {
                    link.classList.add('active');
                }
            });
        }
    });
}

// Dropdown menu functionality
function initializeDropdowns() {
    const dropdowns = document.querySelectorAll('.nav-dropdown');

    dropdowns.forEach(dropdown => {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        const menu = dropdown.querySelector('.dropdown-menu');

        if (!toggle || !menu) return;

        // Click handler
        toggle.addEventListener('click', (e) => {
            e.preventDefault();
            const isExpanded = toggle.getAttribute('aria-expanded') === 'true';

            // Close other dropdowns
            document.querySelectorAll('.dropdown-menu.active').forEach(otherMenu => {
                if (otherMenu !== menu) {
                    otherMenu.classList.remove('active');
                    const otherToggle = otherMenu.previousElementSibling;
                    if (otherToggle) otherToggle.setAttribute('aria-expanded', 'false');
                }
            });

            // Toggle current dropdown
            toggle.setAttribute('aria-expanded', !isExpanded);
            menu.classList.toggle('active');
        });

        // Hover handlers for desktop
        if (window.innerWidth > 768) {
            dropdown.addEventListener('mouseenter', () => {
                toggle.setAttribute('aria-expanded', 'true');
                menu.classList.add('active');
            });

            dropdown.addEventListener('mouseleave', () => {
                toggle.setAttribute('aria-expanded', 'false');
                menu.classList.remove('active');
            });
        }

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!dropdown.contains(e.target)) {
                toggle.setAttribute('aria-expanded', 'false');
                menu.classList.remove('active');
            }
        });
    });
}

// ===== SEARCH SYSTEM =====

// Unified search functionality
function initializeSearch() {
    const searchInput = document.getElementById('globalSearchInput');
    const searchForm = document.getElementById('globalSearchForm');
    const searchSuggestions = document.getElementById('searchSuggestions');

    if (!searchInput || !searchForm) return;

    let searchTimeout;
    let currentSearchTerm = '';

    // Real-time search with debouncing
    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.trim();

        clearTimeout(searchTimeout);

        if (searchTerm.length === 0) {
            hideSearchSuggestions();
            return;
        }

        if (searchTerm.length < CONFIG.search.minLength) return;

        searchTimeout = setTimeout(() => {
            performUnifiedSearch(searchTerm);
        }, CONFIG.search.debounce);
    });

    // Form submission
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const searchTerm = searchInput.value.trim();
        if (searchTerm) {
            performSearchRedirect(searchTerm);
        }
    });

    // Click outside to close
    document.addEventListener('click', (e) => {
        if (!searchForm.contains(e.target)) {
            hideSearchSuggestions();
        }
    });

    // Keyboard navigation
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideSearchSuggestions();
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            focusFirstSuggestion();
        }
    });
}

async function performUnifiedSearch(searchTerm) {
    try {
        showSearchLoading();

        // Search multiple endpoints simultaneously
        const [parksResults, speciesResults] = await Promise.all([
            fetch(`/api/search/parks?query=${encodeURIComponent(searchTerm)}&limit=3`).then(r => r.json()),
            fetch(`/api/species?search=${encodeURIComponent(searchTerm)}&limit=3`).then(r => r.json())
        ]);

        displaySearchResults(searchTerm, parksResults, speciesResults);

    } catch (error) {
        console.error('Unified search error:', error);
        showSearchError();
    } finally {
        hideSearchLoading();
    }
}

function displaySearchResults(searchTerm, parksResults, speciesResults) {
    const searchSuggestions = document.getElementById('searchSuggestions');
    if (!searchSuggestions) return;

    const parks = parksResults?.results || [];
    const species = speciesResults || [];

    let html = '';

    // Parks results
    if (parks.length > 0) {
        html += `<div class="search-results-section">
            <div class="search-section-header">
                <i class="fas fa-tree"></i>
                <span>Parcs Nationaux</span>
            </div>`;

        parks.forEach(park => {
            html += `
                <div class="search-suggestion-item" data-type="park" data-id="${park.id}">
                    <div class="search-suggestion-icon">
                        <i class="fas fa-tree"></i>
                    </div>
                    <div class="search-suggestion-content">
                        <div class="search-suggestion-title">${highlightSearchTerm(park.name, searchTerm)}</div>
                        <div class="search-suggestion-subtitle">${park.governorate} • ${park.area_km2} km²</div>
                    </div>
                    <div class="search-suggestion-category">
                        <i class="fas fa-map-marker-alt"></i>
                        Parc
                    </div>
                </div>`;
        });

        html += `<div class="search-see-all">
            <a href="/parks?search=${encodeURIComponent(searchTerm)}">Voir tous les parcs →</a>
        </div></div>`;
    }

    // Species results
    if (species.length > 0) {
        html += `<div class="search-results-section">
            <div class="search-section-header">
                <i class="fas fa-paw"></i>
                <span>Espèces</span>
            </div>`;

        species.forEach(specie => {
            html += `
                <div class="search-suggestion-item" data-type="species" data-id="${specie.id}">
                    <div class="search-suggestion-icon">
                        <i class="fas fa-paw"></i>
                    </div>
                    <div class="search-suggestion-content">
                        <div class="search-suggestion-title">${highlightSearchTerm(specie.name, searchTerm)}</div>
                        <div class="search-suggestion-subtitle">${specie.scientific_name} • ${specie.type}</div>
                    </div>
                    <div class="search-suggestion-category">
                        <i class="fas fa-dna"></i>
                        ${specie.type === 'animal' ? 'Faune' : 'Flore'}
                    </div>
                </div>`;
        });

        html += `<div class="search-see-all">
            <a href="/species?search=${encodeURIComponent(searchTerm)}">Voir toutes les espèces →</a>
        </div></div>`;
    }

    // No results
    if (parks.length === 0 && species.length === 0) {
        html = `
            <div class="search-no-results">
                <i class="fas fa-search"></i>
                <p>Aucun résultat trouvé pour "${searchTerm}"</p>
                <small>Essayez d'autres termes de recherche</small>
            </div>`;
    }

    searchSuggestions.innerHTML = html;
    searchSuggestions.classList.add('active');

    // Add click handlers
    setupSearchResultClicks();
}

function highlightSearchTerm(text, searchTerm) {
    if (!text || !searchTerm) return text;

    const regex = new RegExp(`(${searchTerm})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

function setupSearchResultClicks() {
    document.querySelectorAll('.search-suggestion-item').forEach(item => {
        item.addEventListener('click', () => {
            const type = item.dataset.type;
            const id = item.dataset.id;

            if (type === 'park') {
                window.location.href = `/parks/${id}`;
            } else if (type === 'species') {
                window.location.href = `/species/${id}`;
            }

            hideSearchSuggestions();
        });
    });
}

function performSearchRedirect(searchTerm) {
    window.location.href = `/search?q=${encodeURIComponent(searchTerm)}`;
    hideSearchSuggestions();
}

function showSearchLoading() {
    const searchSuggestions = document.getElementById('searchSuggestions');
    if (!searchSuggestions) return;

    searchSuggestions.innerHTML = `
        <div class="search-loading active">
            <div class="search-spinner"></div>
            <div class="search-loading-text">Recherche en cours...</div>
        </div>`;
    searchSuggestions.classList.add('active');
}

function hideSearchLoading() {
    const loading = document.querySelector('.search-loading');
    if (loading) {
        loading.classList.remove('active');
    }
}

function showSearchError() {
    const searchSuggestions = document.getElementById('searchSuggestions');
    if (!searchSuggestions) return;

    searchSuggestions.innerHTML = `
        <div class="search-error">
            <i class="fas fa-exclamation-triangle"></i>
            <p>Erreur de recherche</p>
            <small>Réessayez dans quelques instants</small>
        </div>`;
    searchSuggestions.classList.add('active');
}

function hideSearchSuggestions() {
    const searchSuggestions = document.getElementById('searchSuggestions');
    if (searchSuggestions) {
        searchSuggestions.classList.remove('active');
    }
}

function focusFirstSuggestion() {
    const firstSuggestion = document.querySelector('.search-suggestion-item');
    if (firstSuggestion) {
        firstSuggestion.focus();
    }
}

// ===== FILTER TAGS =====

// Interactive filter tags
function initializeFilterTags() {
    const filterTags = document.querySelectorAll('.filter-tag');

    filterTags.forEach(tag => {
        tag.addEventListener('click', () => {
            const isActive = tag.classList.contains('active');

            // Remove active class from all tags in the same group
            const siblings = tag.parentElement.querySelectorAll('.filter-tag');
            siblings.forEach(sibling => sibling.classList.remove('active'));

            // Toggle active class
            if (!isActive) {
                tag.classList.add('active');
            }

            // Trigger filter update
            updateFilters();
        });
    });
}

function updateFilters() {
    const activeFilters = {};

    // Collect active filters
    document.querySelectorAll('.filter-tag.active').forEach(tag => {
        const filterType = tag.dataset.filter;
        const filterValue = tag.dataset.value;

        if (!activeFilters[filterType]) {
            activeFilters[filterType] = [];
        }
        activeFilters[filterType].push(filterValue);
    });

    // Update URL or trigger content update
    updateContentBasedOnFilters(activeFilters);
}

function updateContentBasedOnFilters(filters) {
    // Implementation depends on specific content
    // For now, just log the filters
    console.log('Active filters:', filters);
}

// ===== TOAST NOTIFICATIONS =====

// Enhanced toast notification system
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.className = 'toast-container';
        container.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            z-index: 10000;
            pointer-events: none;
        `;
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.style.cssText = `
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        padding: 1rem 1.5rem;
        max-width: 400px;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        animation: slideInRight 0.3s ease;
        border-left: 4px solid ${getToastColor(type)};
        pointer-events: auto;
        opacity: 0;
        transform: translateX(400px);
    `;

    const icons = {
        success: 'leaf',
        error: 'exclamation-triangle',
        warning: 'sun',
        info: 'info-circle'
    };

    toast.innerHTML = `
        <i class="fas fa-${icons[type]}" style="color: ${getToastColor(type)};"></i>
        <span style="color: #1e293b; font-weight: 500; flex: 1;">${message}</span>
        <button onclick="this.parentElement.remove()" style="
            background: none;
            border: none;
            font-size: 1.25rem;
            color: #64748b;
            cursor: pointer;
            padding: 0;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 4px;
            transition: all 0.2s ease;
        ">&times;</button>
    `;

    document.querySelector('.toast-container').appendChild(toast);

    // Animate in
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    }, 10);

    // Auto-hide after 4 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function getToastColor(type) {
    const colors = {
        success: '#22c55e',
        error: '#dc2626',
        warning: '#ea580c',
        info: '#06b6d4'
    };
    return colors[type] || colors.info;
}

// ===== INTERSECTION OBSERVER ANIMATIONS =====

// Scroll-triggered animations
function initializeScrollAnimations() {
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

    // Observe stagger animation containers
    document.querySelectorAll('.stagger-children').forEach(container => {
        observer.observe(container);

        // Add animation delays to children
        const children = container.querySelectorAll('> *');
        children.forEach((child, index) => {
            child.style.animationDelay = `${index * 0.1}s`;
        });
    });

    // Observe individual animated elements
    document.querySelectorAll('.reveal').forEach(el => {
        observer.observe(el);
    });

    // Count-up animations for statistics
    initializeCountUpAnimations();
}

function initializeCountUpAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !entry.target.hasAttribute('data-animated')) {
                entry.target.setAttribute('data-animated', 'true');
                animateNumber(entry.target);
            }
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('[data-count-up]').forEach(el => {
        observer.observe(el);
    });
}

function animateNumber(element) {
    // Add null checks and library availability checks
    if (!element || typeof element.dataset === 'undefined' || !element.dataset.countUp) {
        console.warn('animateNumber: Invalid element or missing data-count-up attribute');
        return;
    }

    const target = parseInt(element.dataset.countUp) || 0;

    // Check if countUp library is available and use it
    if (element && typeof element.countUp === 'function') {
        // Use countUp library if available
        element.countUp(target);
    } else {
        // Fallback to custom animation
        const duration = 2000;
        const start = performance.now();

        // Ensure element has textContent property
        if (typeof element.textContent === 'undefined') {
            console.warn('animateNumber: Element does not support textContent');
            return;
        }

        function update(currentTime) {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const current = Math.floor(target * easeOutQuart);

            element.textContent = current.toLocaleString();

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }

        requestAnimationFrame(update);
    }
}

// ===== SMOOTH SCROLLING =====

// Enhanced smooth scrolling for anchor links
function initializeSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#') return;

            e.preventDefault();
            const target = document.querySelector(href);

            if (target) {
                const offsetTop = target.offsetTop - CONFIG.scroll.offset;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// ===== SCROLL TO TOP =====

// Scroll to top functionality
function initializeScrollToTop() {
    const scrollBtn = document.getElementById('scrollToTop');
    if (!scrollBtn) return;

    window.addEventListener('scroll', debounce(() => {
        if (window.scrollY > 300) {
            scrollBtn.classList.add('visible');
        } else {
            scrollBtn.classList.remove('visible');
        }
    }, 100));

    scrollBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// ===== LOADING STATES =====

// Professional loading states
function showProfessionalLoader(message = 'Chargement en cours...') {
    const existing = document.querySelector('.professional-loader');
    if (existing) return;

    const loader = document.createElement('div');
    loader.className = 'professional-loader';
    loader.innerHTML = `
        <div class="loader-content">
            <div class="loader-spinner"></div>
            <div class="loader-text">${message}</div>
            <div class="loader-subtitle">Veuillez patienter</div>
        </div>
    `;

    document.body.appendChild(loader);
}

function hideProfessionalLoader() {
    const loader = document.querySelector('.professional-loader');
    if (loader) {
        loader.classList.add('hidden');
        setTimeout(() => loader.remove(), 500);
    }
}

// ===== ACCESSIBILITY =====

// Keyboard navigation enhancements
function initializeAccessibility() {
    // Skip to main content
    const skipLink = document.querySelector('.skip-to-main');
    if (skipLink) {
        skipLink.addEventListener('focus', () => {
            skipLink.style.top = '6px';
        });

        skipLink.addEventListener('blur', () => {
            skipLink.style.top = '-40px';
        });
    }

    // Enhanced focus management
    document.addEventListener('keydown', (e) => {
        // Close modals with Escape
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay.active, .dropdown-menu.active').forEach(el => {
                el.classList.remove('active');
            });
        }
    });
}

// ===== PERFORMANCE =====

// Lazy loading for images
function initializeLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        imageObserver.unobserve(img);
                    }
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
}

// ===== INITIALIZATION =====

// Initialize all components when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🌲 Tunisia National Parks - Premium JavaScript Initialized');

    // Core functionality
    initializeNavbar();
    initializeSearch();
    initializeFilterTags();
    initializeScrollAnimations();
    initializeSmoothScrolling();
    initializeScrollToTop();
    initializeAccessibility();
    initializeLazyLoading();

    // Add global toast function
    window.showToast = showToast;

    // Performance monitoring
    if ('performance' in window && 'PerformanceObserver' in window) {
        // Monitor LCP
        const observer = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
                if (entry.entryType === 'largest-contentful-paint') {
                    console.log('LCP:', entry.startTime);
                }
            }
        });
        observer.observe({ entryTypes: ['largest-contentful-paint'] });
    }
});

// ===== GLOBAL UTILITIES =====

// Add utility functions to window object
window.TunisiaParks = {
    showToast,
    showProfessionalLoader,
    hideProfessionalLoader,
    smoothScrollTo,
    isInViewport,
    debounce
};
