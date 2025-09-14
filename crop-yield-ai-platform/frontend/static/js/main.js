// Main JavaScript file for Crop Yield AI Platform

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in');
        }, index * 100);
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.classList.contains('show')) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });
});

// Utility Functions
const Utils = {
    // Format currency
    formatCurrency: (amount) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    },

    // Format numbers with Indian numbering system
    formatNumber: (num) => {
        return new Intl.NumberFormat('en-IN').format(num);
    },

    // Show loading spinner
    showLoading: (element) => {
        const spinner = '<div class="spinner-border spinner-border-sm me-2" role="status"><span class="visually-hidden">Loading...</span></div>';
        element.innerHTML = spinner + element.textContent;
        element.disabled = true;
    },

    // Hide loading spinner
    hideLoading: (element, originalText) => {
        element.innerHTML = originalText;
        element.disabled = false;
    },

    // Show toast notification
    showToast: (message, type = 'info', duration = 5000) => {
        const toastContainer = document.getElementById('toast-container') || createToastContainer();
        
        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center text-white bg-${type} border-0`;
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');
        
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toastEl);
        
        const toast = new bootstrap.Toast(toastEl, { delay: duration });
        toast.show();
        
        // Remove toast element after it's hidden
        toastEl.addEventListener('hidden.bs.toast', () => {
            toastEl.remove();
        });
    },

    // Validate form data
    validateForm: (formData) => {
        const errors = [];
        
        // Required fields validation
        const requiredFields = ['crop_type', 'area', 'rainfall', 'temperature', 'soil_ph'];
        requiredFields.forEach(field => {
            if (!formData.get(field) || formData.get(field).trim() === '') {
                errors.push(`${field.replace('_', ' ')} is required`);
            }
        });
        
        // Numeric validations
        const numericFields = {
            'area': { min: 0.1, max: 1000 },
            'rainfall': { min: 0, max: 10000 },
            'temperature': { min: -10, max: 60 },
            'soil_ph': { min: 0, max: 14 },
            'fertilizer_usage': { min: 0, max: 1000 },
            'pest_control': { min: 1, max: 10 }
        };
        
        Object.entries(numericFields).forEach(([field, limits]) => {
            const value = parseFloat(formData.get(field));
            if (isNaN(value)) {
                errors.push(`${field.replace('_', ' ')} must be a valid number`);
            } else if (value < limits.min || value > limits.max) {
                errors.push(`${field.replace('_', ' ')} must be between ${limits.min} and ${limits.max}`);
            }
        });
        
        return errors;
    },

    // Get geolocation
    getCurrentLocation: () => {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Geolocation is not supported'));
                return;
            }
            
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    resolve({
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude
                    });
                },
                (error) => {
                    reject(error);
                },
                { timeout: 10000, enableHighAccuracy: true }
            );
        });
    }
};

// Create toast container if it doesn't exist
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    container.style.zIndex = '1055';
    document.body.appendChild(container);
    return container;
}

// Weather API Integration
const WeatherAPI = {
    // Get weather data (placeholder for actual API integration)
    getCurrentWeather: async (lat = null, lng = null) => {
        try {
            const response = await fetch('/api/weather');
            if (!response.ok) {
                throw new Error('Weather data unavailable');
            }
            return await response.json();
        } catch (error) {
            console.error('Weather API error:', error);
            // Return dummy data as fallback
            return {
                temperature: 25,
                humidity: 70,
                rainfall_forecast: 0,
                wind_speed: 5,
                alert: 'Weather data unavailable'
            };
        }
    },

    // Get weather forecast
    getForecast: async (days = 7) => {
        try {
            const response = await fetch(`/api/weather/forecast?days=${days}`);
            if (!response.ok) {
                throw new Error('Forecast data unavailable');
            }
            return await response.json();
        } catch (error) {
            console.error('Forecast API error:', error);
            return null;
        }
    }
};

// Market Price API Integration
const MarketAPI = {
    // Get current market prices
    getCurrentPrices: async () => {
        try {
            const response = await fetch('/api/market_prices');
            if (!response.ok) {
                throw new Error('Market data unavailable');
            }
            return await response.json();
        } catch (error) {
            console.error('Market API error:', error);
            return null;
        }
    },

    // Get price history
    getPriceHistory: async (crop, days = 30) => {
        try {
            const response = await fetch(`/api/market_prices/history?crop=${crop}&days=${days}`);
            if (!response.ok) {
                throw new Error('Price history unavailable');
            }
            return await response.json();
        } catch (error) {
            console.error('Price history API error:', error);
            return null;
        }
    }
};

// Form Handlers
const FormHandlers = {
    // Handle prediction form submission
    handlePredictionForm: (formElement) => {
        formElement.addEventListener('submit', async function(e) {
            const submitBtn = formElement.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            
            // Show loading state
            Utils.showLoading(submitBtn);
            
            try {
                const formData = new FormData(formElement);
                
                // Validate form data
                const errors = Utils.validateForm(formData);
                if (errors.length > 0) {
                    e.preventDefault();
                    Utils.showToast('Please correct the form errors: ' + errors.join(', '), 'danger');
                    Utils.hideLoading(submitBtn, originalText);
                    return;
                }
                
                // Form is valid, let it submit normally
                Utils.showToast('Analyzing your data...', 'info', 3000);
                
            } catch (error) {
                e.preventDefault();
                Utils.showToast('An error occurred. Please try again.', 'danger');
                Utils.hideLoading(submitBtn, originalText);
            }
        });
    },

    // Handle cost calculator form
    handleCostCalculator: (formElement) => {
        const inputs = formElement.querySelectorAll('input, select');
        
        inputs.forEach(input => {
            input.addEventListener('input', debounce(() => {
                calculateCostBenefit();
            }, 300));
        });
    }
};

// Debounce function for performance optimization
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

// Language Support
const LanguageSupport = {
    // Translations object (placeholder)
    translations: {
        'english': {},
        'hindi': {},
        'odia': {}
    },

    // Get translation
    translate: (key, language = 'english') => {
        return LanguageSupport.translations[language][key] || key;
    },

    // Apply translations to page
    applyTranslations: (language) => {
        const elements = document.querySelectorAll('[data-translate]');
        elements.forEach(element => {
            const key = element.getAttribute('data-translate');
            element.textContent = LanguageSupport.translate(key, language);
        });
    }
};

// Performance Monitoring
const Performance = {
    // Measure page load time
    measurePageLoad: () => {
        window.addEventListener('load', () => {
            const navigation = performance.getEntriesByType('navigation')[0];
            const loadTime = navigation.loadEventEnd - navigation.loadEventStart;
            console.log(`Page load time: ${loadTime}ms`);
        });
    },

    // Monitor form submission time
    measureFormSubmission: (formElement, formName) => {
        const startTime = performance.now();
        formElement.addEventListener('submit', () => {
            const endTime = performance.now();
            console.log(`${formName} submission time: ${endTime - startTime}ms`);
        });
    }
};

// Initialize performance monitoring
Performance.measurePageLoad();

// Global error handler
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    Utils.showToast('An unexpected error occurred. Please refresh the page.', 'danger');
});

// Service Worker registration (for PWA features)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then((registration) => {
                console.log('SW registered: ', registration);
            })
            .catch((registrationError) => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}

// Export utilities for use in other scripts
window.CropAI = {
    Utils,
    WeatherAPI,
    MarketAPI,
    FormHandlers,
    LanguageSupport,
    Performance
};