class Sidebar {
    constructor() {
        this.themeNavEl = document.getElementById('theme-nav');
        this.searchInputEl = document.getElementById('search-input');
        this.searchClearEl = document.getElementById('search-clear');
        this.refreshBtnEl = document.getElementById('refresh-btn');
        this.refreshStatusEl = document.getElementById('refresh-status');
        this.totalInsightsEl = document.getElementById('total-insights');

        this.themes = {};
        this.selectedTheme = null;
        this.searchQuery = '';
        this.searchResults = [];
        this.searchTimeout = null;

        this.onThemeClick = null;
        this.onSearch = null;
        this.onRefresh = null;

        this.setupEventListeners();
    }

    setupEventListeners() {
        this.searchInputEl.addEventListener('input', (e) => {
            this.searchQuery = e.target.value;
            if (this.searchQuery) {
                this.searchClearEl.classList.add('active');
            } else {
                this.searchClearEl.classList.remove('active');
            }
            clearTimeout(this.searchTimeout);
            if (this.searchQuery) {
                this.searchTimeout = setTimeout(() => this.performSearch(), 300);
            } else {
                if (this.onSearch) this.onSearch(null);
            }
        });

        this.searchClearEl.addEventListener('click', () => {
            this.searchInputEl.value = '';
            this.searchQuery = '';
            this.searchClearEl.classList.remove('active');
            if (this.onSearch) this.onSearch(null);
        });

        this.refreshBtnEl.addEventListener('click', () => this.refresh());
    }

    async loadThemes() {
        try {
            const response = await fetch('/api/vault/themes');
            this.themes = await response.json();
            this.renderThemes();
            this.updateStats();
        } catch (error) {
            console.error('Error loading themes:', error);
            this.refreshStatusEl.textContent = 'Error loading themes';
            this.refreshStatusEl.classList.add('error');
        }
    }

    renderThemes() {
        this.themeNavEl.innerHTML = '';
        Object.entries(this.themes).forEach(([themeName, themeData]) => {
            const themeEl = document.createElement('div');
            themeEl.className = 'theme-item';
            if (this.selectedTheme === themeName) themeEl.classList.add('active');
            themeEl.innerHTML = `<div class="theme-color-dot" style="background-color: ${themeData.color}"></div>
                <div class="theme-info">
                    <span class="theme-name">${themeName}</span>
                    <span class="theme-count">${themeData.count}</span>
                </div>`;
            themeEl.addEventListener('click', () => this.selectTheme(themeName));
            this.themeNavEl.appendChild(themeEl);
        });

        const allEl = document.createElement('div');
        allEl.className = 'theme-item';
        if (!this.selectedTheme) allEl.classList.add('active');
        const totalCount = Object.values(this.themes).reduce((sum, t) => sum + t.count, 0);
        allEl.innerHTML = `<div class="theme-color-dot" style="background-color: #6366f1; opacity: 0.5;"></div>
            <div class="theme-info"><span class="theme-name">All Themes</span><span class="theme-count">${totalCount}</span></div>`;
        allEl.addEventListener('click', () => this.selectTheme(null));
        this.themeNavEl.insertBefore(allEl, this.themeNavEl.firstChild);
    }

    selectTheme(themeName) {
        this.selectedTheme = themeName;
        this.searchInputEl.value = '';
        this.searchQuery = '';
        this.searchClearEl.classList.remove('active');
        document.querySelectorAll('.theme-item').forEach(el => el.classList.remove('active'));
        if (themeName === null) {
            document.querySelectorAll('.theme-item')[0].classList.add('active');
        } else {
            document.querySelectorAll('.theme-item').forEach(el => {
                if (el.textContent.includes(themeName)) el.classList.add('active');
            });
        }
        if (this.onThemeClick) this.onThemeClick(themeName);
    }

    async performSearch() {
        if (!this.searchQuery) {
            if (this.onSearch) this.onSearch(null);
            return;
        }
        try {
            const theme = this.selectedTheme ? `&theme=${this.selectedTheme}` : '';
            const response = await fetch(`/api/vault/search?q=${encodeURIComponent(this.searchQuery)}${theme}`);
            const data = await response.json();
            this.searchResults = data.results.map(r => r.id);
            if (this.onSearch) this.onSearch(this.searchResults);
        } catch (error) {
            console.error('Error searching:', error);
        }
    }

    async refresh() {
        this.refreshBtnEl.classList.add('loading');
        this.refreshStatusEl.textContent = 'Refreshing...';
        this.refreshStatusEl.classList.remove('success', 'error');
        try {
            await fetch('/api/vault/refresh', { method: 'POST' });
            if (window.app) await window.app.initializeData();
            this.refreshStatusEl.textContent = 'Refreshed ✓';
            this.refreshStatusEl.classList.add('success');
            setTimeout(() => {
                this.refreshStatusEl.textContent = '';
                this.refreshStatusEl.classList.remove('success');
            }, 3000);
        } catch (error) {
            console.error('Error refreshing vault:', error);
            this.refreshStatusEl.textContent = 'Error refreshing';
            this.refreshStatusEl.classList.add('error');
        } finally {
            this.refreshBtnEl.classList.remove('loading');
        }
    }

    updateStats() {
        const total = Object.values(this.themes).reduce((sum, t) => sum + t.count, 0);
        this.totalInsightsEl.textContent = total;
    }

    setThemeClickCallback(callback) { this.onThemeClick = callback; }
    setSearchCallback(callback) { this.onSearch = callback; }
    setRefreshCallback(callback) { this.onRefresh = callback; }
}