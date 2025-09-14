/**
 * Internationalization (i18n) System for CropAI Platform
 * Supports 27+ Indian regional languages with RTL support
 */

class I18nManager {
    constructor() {
        this.translations = {};
        this.languages = {};
        this.currentLanguage = 'en';
        this.rtlLanguages = ['ur', 'ks', 'sd'];  // RTL languages
        this.fallbackLanguage = 'en';
        this.storageKey = 'cropai_language';
        this.isLoading = false;
        
        // Initialize
        this.init();
    }

    async init() {
        try {
            // Load comprehensive translations
            await this.loadTranslationData();
            
            // Set initial language (from storage, browser, or fallback)
            const savedLang = this.getStoredLanguage();
            const browserLang = this.detectBrowserLanguage();
            const initialLang = savedLang || browserLang || this.fallbackLanguage;
            
            await this.changeLanguage(initialLang);
            
            console.log(`🌐 i18n initialized with language: ${this.currentLanguage}`);
        } catch (error) {
            console.error('❌ i18n initialization failed:', error);
            this.currentLanguage = this.fallbackLanguage;
        }
    }

    async loadTranslationData() {
        try {
            const response = await fetch('/static/data/comprehensive_translations.json');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.languages = data.languages || {};
            this.translations = data.translations || {};
            
            console.log(`✅ Loaded translations for ${Object.keys(this.translations).length} languages`);
        } catch (error) {
            console.error('❌ Failed to load translation data:', error);
            // Fallback to minimal English
            this.translations = { en: { app_name: 'CropAI Platform' } };
            this.languages = { english: { code: 'en', native: 'English' } };
        }
    }

    /**
     * Change the current language and update UI
     * @param {string} langCode - Language code (e.g., 'hi', 'bn', 'te')
     */
    async changeLanguage(langCode) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        
        try {
            // Validate language code
            if (!this.translations[langCode]) {
                console.warn(`⚠️ Language ${langCode} not found, falling back to ${this.fallbackLanguage}`);
                langCode = this.fallbackLanguage;
            }

            const previousLang = this.currentLanguage;
            this.currentLanguage = langCode;
            
            // Store language preference
            this.storeLanguage(langCode);
            
            // Update HTML attributes for RTL support
            this.updateDocumentDirection();
            
            // Update all translatable elements
            this.updatePageText();
            
            // Trigger custom event for other components
            this.dispatchLanguageChangeEvent(previousLang, langCode);
            
            console.log(`🔄 Language changed from ${previousLang} to ${langCode}`);
        } catch (error) {
            console.error('❌ Language change failed:', error);
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Translate a key to current language
     * @param {string} key - Translation key (supports dot notation)
     * @param {Object} params - Parameters for interpolation
     * @returns {string} Translated text
     */
    t(key, params = {}) {
        try {
            const translation = this.getNestedTranslation(key, this.currentLanguage) || 
                              this.getNestedTranslation(key, this.fallbackLanguage) || 
                              key;
            
            return this.interpolate(translation, params);
        } catch (error) {
            console.warn(`⚠️ Translation failed for key: ${key}`, error);
            return key;
        }
    }

    /**
     * Get nested translation from object using dot notation
     * @param {string} key - Key like 'crops.rice' or 'actions.generate_prediction'
     * @param {string} langCode - Language code
     * @returns {string|null} Translation or null if not found
     */
    getNestedTranslation(key, langCode) {
        const translations = this.translations[langCode];
        if (!translations) return null;

        return key.split('.').reduce((obj, k) => obj && obj[k], translations);
    }

    /**
     * Interpolate parameters into translation string
     * @param {string} text - Text with {{param}} placeholders
     * @param {Object} params - Parameters to interpolate
     * @returns {string} Interpolated text
     */
    interpolate(text, params) {
        if (typeof text !== 'string') return text;
        
        return text.replace(/\{\{(\w+)\}\}/g, (match, key) => {
            return params[key] !== undefined ? params[key] : match;
        });
    }

    /**
     * Update document direction for RTL languages
     */
    updateDocumentDirection() {
        const isRTL = this.rtlLanguages.includes(this.currentLanguage);
        const htmlElement = document.documentElement;
        
        if (isRTL) {
            htmlElement.setAttribute('dir', 'rtl');
            htmlElement.classList.add('rtl');
        } else {
            htmlElement.setAttribute('dir', 'ltr');
            htmlElement.classList.remove('rtl');
        }
    }

    /**
     * Update all elements with data-i18n attributes
     */
    updatePageText() {
        // Update elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);
            
            if (element.tagName === 'INPUT' && (element.type === 'text' || element.type === 'search')) {
                element.placeholder = translation;
            } else if (element.tagName === 'INPUT' && element.type === 'submit') {
                element.value = translation;
            } else {
                element.textContent = translation;
            }
        });

        // Update elements with data-i18n-html attribute (for HTML content)
        document.querySelectorAll('[data-i18n-html]').forEach(element => {
            const key = element.getAttribute('data-i18n-html');
            const translation = this.t(key);
            element.innerHTML = translation;
        });

        // Update elements with data-i18n-title attribute
        document.querySelectorAll('[data-i18n-title]').forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            const translation = this.t(key);
            element.title = translation;
        });
    }

    /**
     * Get all available languages with their metadata
     * @returns {Array} Array of language objects
     */
    getAvailableLanguages() {
        return Object.entries(this.languages).map(([key, lang]) => ({
            ...lang,
            key: key,
            isRTL: this.rtlLanguages.includes(lang.code),
            hasTranslation: !!this.translations[lang.code]
        })).sort((a, b) => {
            // Sort with English first, then by region and native name
            if (a.code === 'en') return -1;
            if (b.code === 'en') return 1;
            if (a.region !== b.region) return a.region.localeCompare(b.region);
            return a.native.localeCompare(b.native);
        });
    }

    /**
     * Get current language information
     * @returns {Object} Current language object
     */
    getCurrentLanguageInfo() {
        const langEntry = Object.entries(this.languages).find(([_, lang]) => lang.code === this.currentLanguage);
        return langEntry ? { ...langEntry[1], key: langEntry[0] } : null;
    }

    /**
     * Store language preference in localStorage
     * @param {string} langCode - Language code to store
     */
    storeLanguage(langCode) {
        try {
            localStorage.setItem(this.storageKey, langCode);
        } catch (error) {
            console.warn('⚠️ Failed to store language preference:', error);
        }
    }

    /**
     * Get stored language from localStorage
     * @returns {string|null} Stored language code or null
     */
    getStoredLanguage() {
        try {
            return localStorage.getItem(this.storageKey);
        } catch (error) {
            console.warn('⚠️ Failed to retrieve stored language:', error);
            return null;
        }
    }

    /**
     * Detect browser language preference
     * @returns {string|null} Browser language code or null
     */
    detectBrowserLanguage() {
        try {
            const browserLang = navigator.language || navigator.languages[0];
            const langCode = browserLang.split('-')[0].toLowerCase();
            
            // Check if we support this language
            const supported = Object.values(this.languages).find(lang => lang.code === langCode);
            return supported ? langCode : null;
        } catch (error) {
            console.warn('⚠️ Failed to detect browser language:', error);
            return null;
        }
    }

    /**
     * Dispatch custom event when language changes
     * @param {string} previousLang - Previous language code
     * @param {string} newLang - New language code
     */
    dispatchLanguageChangeEvent(previousLang, newLang) {
        const event = new CustomEvent('languageChanged', {
            detail: {
                previous: previousLang,
                current: newLang,
                languageInfo: this.getCurrentLanguageInfo()
            }
        });
        document.dispatchEvent(event);
    }

    /**
     * Format number according to current locale
     * @param {number} number - Number to format
     * @param {Object} options - Intl.NumberFormat options
     * @returns {string} Formatted number
     */
    formatNumber(number, options = {}) {
        try {
            const currentLang = this.getCurrentLanguageInfo();
            const locale = currentLang ? `${currentLang.code}-IN` : 'en-IN';
            return new Intl.NumberFormat(locale, options).format(number);
        } catch (error) {
            return number.toString();
        }
    }

    /**
     * Format currency according to current locale
     * @param {number} amount - Amount to format
     * @param {string} currency - Currency code (default: INR)
     * @returns {string} Formatted currency
     */
    formatCurrency(amount, currency = 'INR') {
        return this.formatNumber(amount, {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        });
    }

    /**
     * Get text direction for current language
     * @returns {string} 'rtl' or 'ltr'
     */
    getTextDirection() {
        return this.rtlLanguages.includes(this.currentLanguage) ? 'rtl' : 'ltr';
    }
}

// Global instance
window.i18n = new I18nManager();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = I18nManager;
}

// Convenience global function
window.t = (key, params) => window.i18n.t(key, params);