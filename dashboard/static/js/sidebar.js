class Sidebar {
    constructor(demoMode = false) {
        this.demoMode = demoMode;
        this.themeNavEl = document.getElementById('theme-nav');
        this.searchInputEl = document.getElementById('search-input');
        this.searchClearEl = document.getElementById('search-clear');
        this.refreshBtnEl = document.getElementById('refresh-btn');
        this.refreshStatusEl = document.getElementById('refresh-status');
        this.totalInsightsEl = document.getElementById('total-insights');
        this.searchResultsEl = document.getElementById('search-results');
        this.searchResultsListEl = document.getElementById('search-results-list');
        this.searchResultsCountEl = document.getElementById('search-results-count');
        this.searchResultsModeEl = document.getElementById('search-results-mode');
        this.semanticToggleEl = document.getElementById('semantic-toggle');
        this.buildIndexBtnEl = document.getElementById('build-index-btn');
        this.indexStatusTextEl = document.getElementById('index-status-text');

        this.themes = {};
        this.selectedTheme = null;
        this.searchQuery = '';
        this.searchResults = [];
        this.searchTimeout = null;

        this.onThemeClick = null;
        this.onSearch = null;
        this.onRefresh = null;

        if (this.demoMode) {
            this.refreshBtnEl.style.display = 'none';
            this.buildIndexBtnEl.style.display = 'none';
        }

        this.setupEventListeners();
        this.loadIndexStatus();
    }

    setupEventListeners() {
        this.searchInputEl.addEventListener('input', (e) => {
            this.searchQuery = e.target.value;
            if (this.searchQuery) {
                this.searchClearEl.classList.add('active');
            } else {
                this.searchClearEl.classList.remove('active');
                this.hideSearchResults();
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
            this.hideSearchResults();
            if (this.onSearch) this.onSearch(null);
        });

        this.refreshBtnEl.addEventListener('click', () => this.refresh());

        this.semanticToggleEl.addEventListener('change', () => {
            if (this.searchQuery) this.performSearch();
        });

        this.buildIndexBtnEl.addEventListener('click', () => this.buildIndex());
    }

    async loadIndexStatus() {
        try {
            const response = await fetch('/api/vault/embedding-index/status');
            const status = await response.json();
            if (status.built) {
                this.indexStatusTextEl.textContent = `Semantic search ready (${status.count} notes)`;
                this.buildIndexBtnEl.style.display = 'none';
                this.semanticToggleEl.checked = true;
            } else {
                this.indexStatusTextEl.textContent = 'Build index to enable semantic search';
                this.buildIndexBtnEl.style.display = this.demoMode ? 'none' : 'inline-block';
                this.semanticToggleEl.checked = false;
            }
        } catch (error) {
            console.error('Error loading index status:', error);
        }
    }

    async buildIndex() {
        this.buildIndexBtnEl.disabled = true;
        this.buildIndexBtnEl.textContent = 'Building...';
        this.indexStatusTextEl.textContent = 'Building index...';
        try {
            const response = await fetch('/api/vault/embedding-index/build', { method: 'POST' });
            const data = await response.json();
            this.indexStatusTextEl.textContent = `Semantic search ready (${data.count} notes)`;
            this.buildIndexBtnEl.style.display = 'none';
            this.semanticToggleEl.checked = true;
            if (this.searchQuery) this.performSearch();
        } catch (error) {
            console.error('Error building index:', error);
            this.indexStatusTextEl.textContent = 'Error building index';
        } finally {
            this.buildIndexBtnEl.disabled = false;
            this.buildIndexBtnEl.textContent = 'Build Index';
        }
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
        this.hideSearchResults();
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
            this.hideSearchResults();
            return;
        }
        try {
            const theme = this.selectedTheme ? `&theme=${encodeURIComponent(this.selectedTheme)}` : '';
            const semantic = this.semanticToggleEl.checked ? '&semantic=true' : '&semantic=false';
            const response = await fetch(
                `/api/vault/search?q=${encodeURIComponent(this.searchQuery)}${theme}${semantic}&limit=25`
            );
            const data = await response.json();
            this.searchResults = data.results;
            const resultIds = data.results.map(r => r.id);
            if (this.onSearch) this.onSearch(resultIds);
            this.renderSearchResults(data);
        } catch (error) {
            console.error('Error searching:', error);
        }
    }

    renderSearchResults(data) {
        this.searchResultsCountEl.textContent = `${data.count} result${data.count !== 1 ? 's' : ''}`;
        this.searchResultsModeEl.textContent = data.semantic ? 'semantic' : 'keyword';
        this.searchResultsListEl.innerHTML = '';

        for (const result of data.results) {
            const card = document.createElement('div');
            card.className = 'search-result-card';
            card.addEventListener('click', () => {
                if (window.app) window.app.loadInsight(result.id);
            });

            let scoreHtml = '';
            if (result.score !== null && result.score !== undefined) {
                const pct = Math.round(result.score * 100);
                scoreHtml = `<span class="result-score">${pct}%</span>`;
            }

            const themeColor = this.themes[result.theme]?.color || '#64748b';
            const snippetHtml = result.snippet
                ? `<p class="result-snippet">${this._escapeHtml(result.snippet)}</p>`
                : '';

            card.innerHTML = `
                <div class="result-card-header">
                    <span class="result-title">${this._escapeHtml(result.label)}</span>
                    ${scoreHtml}
                </div>
                <div class="result-card-meta">
                    <span class="result-theme-pill" style="background-color: ${themeColor}">${this._escapeHtml(result.theme)}</span>
                </div>
                ${snippetHtml}
            `;
            this.searchResultsListEl.appendChild(card);
        }

        this.searchResultsEl.style.display = 'block';
    }

    hideSearchResults() {
        this.searchResultsEl.style.display = 'none';
        this.searchResultsListEl.innerHTML = '';
    }

    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async refresh() {
        this.refreshBtnEl.classList.add('loading');
        this.refreshStatusEl.textContent = 'Refreshing...';
        this.refreshStatusEl.classList.remove('success', 'error');
        try {
            await fetch('/api/vault/refresh', { method: 'POST' });
            if (window.app) await window.app.initializeData();
            this.refreshStatusEl.textContent = 'Refreshed';
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
