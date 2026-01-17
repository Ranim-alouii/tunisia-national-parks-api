/**
 * UI Module - Common UI utilities and components
 */

class UIUtils {
    static showLoading(element, message = 'Loading...') {
        const loader = document.createElement('div');
        loader.className = 'ui-loader';
        loader.innerHTML = `
            <div class="spinner"></div>
            <p>${message}</p>
        `;
        element.appendChild(loader);
        return loader;
    }

    static hideLoading(loader) {
        if (loader && loader.parentNode) {
            loader.parentNode.removeChild(loader);
        }
    }

    static showError(message, container = document.body) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-error';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span>${message}</span>
            <button onclick="this.parentNode.remove()" class="alert-close">&times;</button>
        `;
        container.insertBefore(errorDiv, container.firstChild);

        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }

    static showSuccess(message, container = document.body) {
        const successDiv = document.createElement('div');
        successDiv.className = 'alert alert-success';
        successDiv.innerHTML = `
            <i class="fas fa-check-circle"></i>
            <span>${message}</span>
            <button onclick="this.parentNode.remove()" class="alert-close">&times;</button>
        `;
        container.insertBefore(successDiv, container.firstChild);

        // Auto-hide after 3 seconds
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.parentNode.removeChild(successDiv);
            }
        }, 3000);
    }

    static createParkCard(park) {
        const card = document.createElement('div');
        card.className = 'card hover-lift';
        card.innerHTML = `
            <div class="zoom-container">
                <img src="${park.images && park.images.length > 0 ? park.images[0] : '/static/images/placeholder-park.jpg'}"
                     alt="${park.name}" class="card-image">
            </div>
            <div class="card-content">
                <h3 class="card-title">${park.name}</h3>
                <div class="card-meta">
                    <span><i class="fas fa-map-marker-alt"></i> ${park.governorate}</span>
                    <span><i class="fas fa-ruler-combined"></i> ${park.area_km2} km²</span>
                </div>
                <p class="card-description">${park.description.substring(0, 120)}...</p>
                <a href="/parks/${park.id}" class="btn btn-primary" style="width: 100%;">
                    <i class="fas fa-arrow-right"></i> Découvrir
                </a>
            </div>
        `;
        return card;
    }

    static createSpeciesCard(species) {
        const card = document.createElement('div');
        card.className = 'card hover-lift';
        card.innerHTML = `
            <div class="zoom-container">
                <img src="${species.image_url || '/static/images/placeholder-species.jpg'}"
                     alt="${species.name}" style="width: 100%; height: 200px; object-fit: cover;">
            </div>
            <div class="card-content">
                <span class="badge ${species.type === 'animal' ? 'badge-info' : 'badge-success'}">
                    <i class="fas fa-${species.type === 'animal' ? 'paw' : 'leaf'}"></i>
                    ${species.type === 'animal' ? 'Animal' : 'Plante'}
                </span>
                <h4 style="margin-top: 0.5rem;">${species.name}</h4>
                <p style="font-style: italic; color: var(--text-secondary); font-size: 0.875rem;">
                    ${species.scientific_name}
                </p>
            </div>
        `;
        return card;
    }

    static formatDate(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('fr-FR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        } catch (error) {
            return dateString;
        }
    }

    static formatArea(area) {
        if (area >= 1000) {
            return `${(area / 1000).toFixed(1)}k km²`;
        }
        return `${area} km²`;
    }

    static debounce(func, wait) {
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

    static throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        }
    }
}

// Add CSS for alerts
const style = document.createElement('style');
style.textContent = `
.alert {
    padding: 1rem;
    margin-bottom: 1rem;
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 500;
}

.alert-error {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.2);
    color: #dc2626;
}

.alert-success {
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.2);
    color: #16a34a;
}

.alert-close {
    background: none;
    border: none;
    font-size: 1.25rem;
    cursor: pointer;
    margin-left: auto;
    opacity: 0.7;
}

.alert-close:hover {
    opacity: 1;
}

.ui-loader {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    gap: 1rem;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid rgba(34, 197, 94, 0.3);
    border-top: 4px solid var(--primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
`;
document.head.appendChild(style);

// Export for use in other modules
window.UIUtils = UIUtils;
