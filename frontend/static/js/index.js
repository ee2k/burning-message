import { i18n } from './utils/i18n.js';
import { LanguageSelector } from './components/languageSelector.js';

class IndexPage {
    constructor() {
        this.init();
    }

    async init() {
        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', async () => {
                await this.initializePage();
            });
        } else {
            // DOM is already loaded
            await this.initializePage();
        }
    }

    async initializePage() {
        try {
            // Load header component
            await i18n.loadTranslations(i18n.currentLocale, 'index', 'header');
            i18n.updateTranslations();
            new LanguageSelector('languageSelector');
        } catch (error) {
            console.error('Failed to initialize page:', error);
        }
    }
}

// Create instance when script loads
new IndexPage();