// ========== GLOBAL VARIABLES ==========
const API_BASE = '/api';
let currentUser = null;
let loadingStates = new Set();

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
    setupScrollEffects();
    setupMobileMenu();
});

function initializeApp() {
    console.log('🌲 Tunisia Parks App Initialized');

    // Check authentication
    checkAuth();

    // Initialize form validation
    initializeForms();

    // Setup smooth scrolling
    setupSmoothScrolling();

    // Initialize scroll animations
    observeElements();

    // Update navbar with user info if authenticated
    if (currentUser) {
        updateNavbarWithUser();
    }
}

// ========== AUTHENTICATION ==========
function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (token) {
        currentUser = { token };
        console.log('✅ User authenticated');
    }
}

async function login(username, password) {
    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await fetch(`${API_BASE}/auth/token`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Login failed');
        
        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        currentUser = { token: data.access_token };
        
        showNotification('Connexion réussie!', 'success');
        return true;
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Échec de la connexion', 'error');
        return false;
    }
}

function logout() {
    localStorage.removeItem('access_token');
    currentUser = null;
    showNotification('Déconnexion réussie', 'info');
    window.location.reload();
}

// ========== API HELPERS ==========
async function apiRequest(endpoint, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    // Add auth token if available
    if (currentUser?.token) {
        defaultOptions.headers['Authorization'] = `Bearer ${currentUser.token}`;
    }
    
    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, finalOptions);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || 'API request failed');
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ========== UI COMPONENTS ==========

// Enhanced Loading States with Nature Theme
function showApiLoading(message = 'Chargement en cours...', type = 'nature') {
    const existing = document.querySelector('.api-loading-spinner');
    if (existing) return;

    const spinner = document.createElement('div');
    spinner.className = 'api-loading-spinner active';
    spinner.innerHTML = `
        <div class="api-spinner"></div>
        <div class="api-loading-text">${message}</div>
    `;

    // Nature-themed styling
    spinner.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(34, 197, 94, 0.2);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        z-index: 10000;
    `;

    document.body.appendChild(spinner);
}

function hideApiLoading() {
    const spinner = document.querySelector('.api-loading-spinner');
    if (spinner) {
        spinner.classList.remove('active');
        setTimeout(() => spinner.remove(), 300);
    }
}

// Enhanced Notification System with Nature Theme
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `toast toast-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        padding: 1rem 1.5rem;
        max-width: 400px;
        z-index: 10000;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        animation: slideInRight 0.3s ease;
        border-left: 4px solid ${getNotificationColor(type)};
    `;

    const icons = {
        success: 'leaf',
        error: 'exclamation-triangle',
        warning: 'sun',
        info: 'info-circle'
    };

    notification.innerHTML = `
        <i class="fas fa-${icons[type]}" style="color: ${getNotificationColor(type)};"></i>
        <span style="color: #1e293b; font-weight: 500;">${message}</span>
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

    document.body.appendChild(notification);

    // Auto-hide after 4 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

function getNotificationColor(type) {
    const colors = {
        success: '#22c55e', // Deep forest green
        error: '#dc2626',   // Terracotta red
        warning: '#ea580c', // Sunny orange
        info: '#06b6d4'     // Sky blue
    };
    return colors[type] || colors.info;
}

// Enhanced Loading Overlay with Nature Theme
function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.background = 'rgba(27, 67, 50, 0.8)'; // Deep forest green overlay
        overlay.style.backdropFilter = 'blur(8px)';
        overlay.style.webkitBackdropFilter = 'blur(8px)';
        overlay.classList.add('active');
    }
}

function hideLoading() {
    document.getElementById('loadingOverlay')?.classList.remove('active');
}

// Confirmation Dialog
function confirm(message, callback) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay active';
    
    overlay.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <h3 class="modal-title">Confirmation</h3>
            </div>
            <div class="modal-body">
                <p>${message}</p>
            </div>
            <div class="modal-footer">
                <button class="btn btn-outline" onclick="this.closest('.modal-overlay').remove()">
                    Annuler
                </button>
                <button class="btn btn-primary" id="confirmBtn">
                    Confirmer
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    
    document.getElementById('confirmBtn').addEventListener('click', () => {
        callback();
        overlay.remove();
    });
}

// ========== SCROLL EFFECTS ==========

function setupScrollEffects() {
    // Navbar scroll effect
    const navbar = document.querySelector('.navbar');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar?.classList.add('scrolled');
        } else {
            navbar?.classList.remove('scrolled');
        }
        
        // Scroll to top button
        const scrollBtn = document.getElementById('scrollToTop');
        if (scrollBtn) {
            if (window.scrollY > 300) {
                scrollBtn.classList.add('visible');
            } else {
                scrollBtn.classList.remove('visible');
            }
        }
    });
    
    // Scroll to top
    document.getElementById('scrollToTop')?.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Smooth scrolling for anchor links
function setupSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#') return;
            
            e.preventDefault();
            const target = document.querySelector(href);
            
            if (target) {
                const offsetTop = target.offsetTop - 100;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Intersection Observer for scroll animations
function observeElements() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    document.querySelectorAll('.reveal').forEach(el => {
        observer.observe(el);
    });
}

// ========== MOBILE MENU ==========

function setupMobileMenu() {
    const toggle = document.getElementById('mobileMenuToggle');
    const menu = document.getElementById('navMenu');
    
    toggle?.addEventListener('click', () => {
        menu?.classList.toggle('active');
        const icon = toggle.querySelector('i');
        if (icon) {
            icon.classList.toggle('fa-bars');
            icon.classList.toggle('fa-times');
        }
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (menu?.classList.contains('active')) {
            if (!menu.contains(e.target) && !toggle?.contains(e.target)) {
                menu.classList.remove('active');
                const icon = toggle?.querySelector('i');
                if (icon) {
                    icon.classList.add('fa-bars');
                    icon.classList.remove('fa-times');
                }
            }
        }
    });
    
    // Close menu when clicking nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            menu?.classList.remove('active');
            const icon = toggle?.querySelector('i');
            if (icon) {
                icon.classList.add('fa-bars');
                icon.classList.remove('fa-times');
            }
        });
    });
}

// ========== EVENT LISTENERS ==========

function setupEventListeners() {
    // Close modals on background click
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal-overlay')) {
            e.target.classList.remove('active');
        }
    });

    // Escape key to close modals
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay.active').forEach(modal => {
                modal.classList.remove('active');
            });
        }
    });

    // Unified Search Functionality
    setupUnifiedSearch();
}

// Unified Search Implementation
function setupUnifiedSearch() {
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

        if (searchTerm.length < 2) return;

        searchTimeout = setTimeout(() => {
            performUnifiedSearch(searchTerm);
        }, 300);
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
            apiRequest(`/search/parks?query=${encodeURIComponent(searchTerm)}&limit=3`),
            apiRequest(`/species?search=${encodeURIComponent(searchTerm)}&limit=3`)
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
    // Redirect to search results page (you can implement this)
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

// ========== FORM VALIDATION & AUTH INTEGRATION ==========

// Enhanced Form Validation with Nature Theme
class FormValidator {
    constructor(form) {
        this.form = form;
        this.fields = {};
        this.errors = {};
        this.initialize();
    }

    initialize() {
        // Find all form inputs
        const inputs = this.form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            this.fields[input.name] = input;
            this.setupFieldValidation(input);
        });

        // Setup form submission
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    setupFieldValidation(field) {
        const validate = debounce(() => this.validateField(field), 300);

        field.addEventListener('blur', validate);
        field.addEventListener('input', () => this.clearFieldError(field));
    }

    validateField(field) {
        const name = field.name;
        const value = field.value.trim();
        const rules = this.getValidationRules(name);

        for (const rule of rules) {
            const error = this.checkRule(field, rule, value);
            if (error) {
                this.showFieldError(field, error);
                this.errors[name] = error;
                return false;
            }
        }

        this.clearFieldError(field);
        delete this.errors[name];
        return true;
    }

    getValidationRules(fieldName) {
        const rules = [];

        switch (fieldName) {
            case 'username':
                rules.push({ type: 'required' }, { type: 'minLength', value: 3 });
                break;
            case 'email':
                rules.push({ type: 'required' }, { type: 'email' });
                break;
            case 'password':
                rules.push({ type: 'required' }, { type: 'minLength', value: 8 });
                break;
            case 'name':
                rules.push({ type: 'required' }, { type: 'minLength', value: 2 });
                break;
            case 'latitude':
                rules.push({ type: 'required' }, { type: 'range', min: -90, max: 90 });
                break;
            case 'longitude':
                rules.push({ type: 'required' }, { type: 'range', min: -180, max: 180 });
                break;
            case 'area_km2':
                rules.push({ type: 'required' }, { type: 'min', value: 0 });
                break;
        }

        return rules;
    }

    checkRule(field, rule, value) {
        switch (rule.type) {
            case 'required':
                return value === '' ? 'Ce champ est obligatoire' : null;
            case 'minLength':
                return value.length < rule.value ? `Minimum ${rule.value} caractères` : null;
            case 'email':
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                return !emailRegex.test(value) ? 'Email invalide' : null;
            case 'range':
                const num = parseFloat(value);
                if (isNaN(num)) return 'Valeur numérique requise';
                if (num < rule.min || num > rule.max) return `Doit être entre ${rule.min} et ${rule.max}`;
                return null;
            case 'min':
                const numVal = parseFloat(value);
                return isNaN(numVal) || numVal < rule.value ? `Doit être supérieur à ${rule.value}` : null;
        }
        return null;
    }

    showFieldError(field, message) {
        this.clearFieldError(field);

        // Add error styling
        field.style.borderColor = '#dc2626'; // Terracotta red
        field.style.boxShadow = '0 0 0 3px rgba(220, 38, 38, 0.1)';

        // Create error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.textContent = message;
        errorDiv.style.cssText = `
            color: #dc2626;
            font-size: 0.875rem;
            margin-top: 0.25rem;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        `;
        errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${message}`;

        field.parentNode.insertBefore(errorDiv, field.nextSibling);
    }

    clearFieldError(field) {
        // Reset styling
        field.style.borderColor = '';
        field.style.boxShadow = '';

        // Remove error message
        const errorDiv = field.parentNode.querySelector('.field-error');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        // Validate all fields
        let isValid = true;
        Object.values(this.fields).forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });

        if (!isValid) {
            showNotification('Veuillez corriger les erreurs dans le formulaire', 'error');
            return;
        }

        // Show loading state
        const submitBtn = this.form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Chargement...';

        try {
            // Handle form submission based on form action
            await this.submitForm();

        } catch (error) {
            showNotification('Erreur lors de l\'envoi du formulaire', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }

    async submitForm() {
        const formData = new FormData(this.form);
        const data = Object.fromEntries(formData.entries());

        // Handle different form types
        if (this.form.id === 'loginForm') {
            const success = await login(data.username, data.password);
            if (success) {
                window.location.href = '/';
            }
        } else if (this.form.id === 'registerForm') {
            await this.submitRegistration(data);
        } else if (this.form.action.includes('/parks')) {
            await this.submitParkCreation(data);
        } else if (this.form.action.includes('/species')) {
            await this.submitSpeciesCreation(data);
        }
    }

    async submitRegistration(data) {
        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                showNotification('Inscription réussie! Vous pouvez maintenant vous connecter.', 'success');
                // Switch to login form or redirect
                setTimeout(() => window.location.href = '/auth/login', 2000);
            } else {
                const error = await response.json();
                showNotification(error.error?.message || 'Erreur d\'inscription', 'error');
            }
        } catch (error) {
            showNotification('Erreur réseau', 'error');
        }
    }

    async submitParkCreation(data) {
        try {
            const response = await apiRequest('/parks', {
                method: 'POST',
                body: JSON.stringify(data)
            });

            showNotification('Parc créé avec succès!', 'success');
            setTimeout(() => window.location.href = '/parks', 1500);
        } catch (error) {
            showNotification('Erreur lors de la création du parc', 'error');
        }
    }

    async submitSpeciesCreation(data) {
        try {
            const response = await apiRequest('/species', {
                method: 'POST',
                body: JSON.stringify(data)
            });

            showNotification('Espèce créée avec succès!', 'success');
            setTimeout(() => window.location.href = '/species', 1500);
        } catch (error) {
            showNotification('Erreur lors de la création de l\'espèce', 'error');
        }
    }
}

// Auth Integration - Update Navbar with User Info
function updateNavbarWithUser() {
    const navbar = document.querySelector('.navbar-nav');
    if (!navbar || !currentUser) return;

    // Find user menu or create one
    let userMenu = navbar.querySelector('.user-menu');
    if (!userMenu) {
        userMenu = document.createElement('div');
        userMenu.className = 'nav-dropdown user-menu';
        userMenu.innerHTML = `
            <button class="nav-link-professional dropdown-toggle" aria-haspopup="true" aria-expanded="false">
                <i class="fas fa-user-circle" aria-hidden="true"></i>
                <span>Mon Compte</span>
                <i class="fas fa-chevron-down dropdown-icon" aria-hidden="true"></i>
            </button>
            <div class="dropdown-menu" role="menu">
                <a href="/auth/profile" class="dropdown-item" role="menuitem">
                    <i class="fas fa-user"></i> Profil
                </a>
                <a href="/auth/favorites" class="dropdown-item" role="menuitem">
                    <i class="fas fa-heart"></i> Favoris
                </a>
                <div class="dropdown-divider"></div>
                <a href="#" onclick="logout()" class="dropdown-item" role="menuitem">
                    <i class="fas fa-sign-out-alt"></i> Déconnexion
                </a>
            </div>
        `;
        navbar.appendChild(userMenu);
    }
}

// Initialize form validation on forms
function initializeForms() {
    document.querySelectorAll('form').forEach(form => {
        if (form.id) { // Only initialize forms with IDs
            new FormValidator(form);
        }
    });
}

// Enhanced Empty States with Nature Theme
function showEmptyState(container, type = 'parks', searchQuery = '') {
    if (!container) return;

    const emptyStates = {
        parks: {
            icon: 'tree',
            title: 'Aucun parc trouvé',
            description: searchQuery ?
                `Aucun parc ne correspond à "${searchQuery}". Essayez d'autres termes de recherche.` :
                'Découvrez bientôt les magnifiques parcs nationaux de Tunisie.',
            action: { text: 'Explorer la carte', href: '/map', icon: 'map-marked-alt' }
        },
        species: {
            icon: 'paw',
            title: 'Aucune espèce trouvée',
            description: searchQuery ?
                `Aucune espèce ne correspond à "${searchQuery}". Essayez d'autres termes de recherche.` :
                'Découvrez bientôt la biodiversité exceptionnelle de Tunisie.',
            action: { text: 'Voir les parcs', href: '/parks', icon: 'tree' }
        },
        trails: {
            icon: 'hiking',
            title: 'Aucun sentier trouvé',
            description: 'Les sentiers de randonnée seront bientôt disponibles.',
            action: { text: 'Voir les parcs', href: '/parks', icon: 'tree' }
        }
    };

    const state = emptyStates[type] || emptyStates.parks;

    container.innerHTML = `
        <div class="empty-state-professional">
            <div class="empty-state-icon">
                <i class="fas fa-${state.icon}"></i>
            </div>
            <h3 class="empty-state-title">${state.title}</h3>
            <p class="empty-state-description">${state.description}</p>
            <div class="empty-state-actions">
                <a href="${state.action.href}" class="btn btn-primary">
                    <i class="fas fa-${state.action.icon || 'arrow-right'}"></i>
                    ${state.action.text}
                </a>
            </div>
        </div>
    `;
}

// Add null checks and error handling throughout
function safeStringOperation(str, operation, fallback = '') {
    if (!str || typeof str !== 'string') return fallback;
    try {
        return operation(str);
    } catch (error) {
        console.warn('String operation failed:', error);
        return fallback;
    }
}

// ========== UTILITY FUNCTIONS ==========

// Enhanced Image Error Handling - Prevent Infinite Loops
document.addEventListener('error', function(e) {
    if (e.target.tagName === 'IMG') {
        const img = e.target;
        const currentSrc = img.src;

        // Prevent infinite loops by checking if we've already tried a fallback
        if (img.hasAttribute('data-fallback-applied')) {
            return;
        }

        // Apply fallback image only once
        img.setAttribute('data-fallback-applied', 'true');
        img.src = 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?q=80&w=400';

        console.log(`Image fallback applied for: ${currentSrc}`);
    }
}, true);

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }).format(date);
}

// Format time ago
function timeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    const intervals = {
        année: 31536000,
        mois: 2592000,
        semaine: 604800,
        jour: 86400,
        heure: 3600,
        minute: 60
    };
    
    for (const [name, value] of Object.entries(intervals)) {
        const interval = Math.floor(seconds / value);
        if (interval >= 1) {
            return `Il y a ${interval} ${name}${interval > 1 ? 's' : ''}`;
        }
    }
    
    return 'À l\'instant';
}

// Debounce function
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

// Generate star rating HTML
function generateStars(rating) {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
    
    let html = '<div class="rating-stars">';
    
    for (let i = 0; i < fullStars; i++) {
        html += '<i class="fas fa-star"></i>';
    }
    
    if (hasHalfStar) {
        html += '<i class="fas fa-star-half-alt"></i>';
    }
    
    for (let i = 0; i < emptyStars; i++) {
        html += '<i class="far fa-star"></i>';
    }
    
    html += '</div>';
    return html;
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copié dans le presse-papiers!', 'success');
    }).catch(() => {
        showNotification('Erreur lors de la copie', 'error');
    });
}

// Share functionality
function share(title, text, url) {
    if (navigator.share) {
        navigator.share({
            title,
            text,
            url
        }).catch(err => console.log('Share error:', err));
    } else {
        copyToClipboard(url);
    }
}

// ========== GEOLOCATION ==========

function getCurrentLocation() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error('Geolocation not supported'));
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            position => {
                resolve({
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                });
            },
            error => reject(error),
            {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0
            }
        );
    });
}

// Calculate distance between two points (Haversine formula)
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth's radius in km
    const dLat = toRadians(lat2 - lat1);
    const dLon = toRadians(lon2 - lon1);
    
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c; // Distance in km
}

function toRadians(degrees) {
    return degrees * (Math.PI / 180);
}

// ========== IMAGE HANDLING ==========

// Lazy load images
function lazyLoadImages() {
    const images = document.querySelectorAll('img[data-src]');

    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
}

// ========== EXPORT FUNCTIONS ==========
window.appUtils = {
    apiRequest,
    showNotification,
    showLoading,
    hideLoading,
    confirm,
    formatDate,
    timeAgo,
    generateStars,
    share,
    getCurrentLocation,
    calculateDistance,
    debounce
};

console.log('✅ App utilities loaded');
// ---------- END OF FILE ----------
