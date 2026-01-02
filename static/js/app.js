// ========== GLOBAL VARIABLES ==========
const API_BASE = '/api';
let currentUser = null;

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
    
    // Setup smooth scrolling
    setupSmoothScrolling();
    
    // Initialize scroll animations
    observeElements();
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

// Notification System
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    const icons = {
        success: 'check-circle',
        error: 'times-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    
    notification.innerHTML = `
        <i class="fas fa-${icons[type]}"></i>
        <span>${message}</span>
    `;
    
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: var(--radius-md);
        background: white;
        box-shadow: var(--shadow-lg);
        z-index: 10000;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        animation: slideInRight 0.3s ease;
        max-width: 400px;
    `;
    
    const colors = {
        success: '#52b788',
        error: '#e63946',
        warning: '#f4a261',
        info: '#4895ef'
    };
    
    notification.style.borderLeft = `4px solid ${colors[type]}`;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Loading Overlay
function showLoading() {
    document.getElementById('loadingOverlay')?.classList.add('active');
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
}

// ========== UTILITY FUNCTIONS ==========

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

// Image error fallback
document.addEventListener('error', (e) => {
    if (e.target.tagName === 'IMG') {
        e.target.src = 'https://via.placeholder.com/400x300?text=Image+Non+Disponible';
    }
}, true);

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