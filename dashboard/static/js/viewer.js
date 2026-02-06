class InsightViewer {
    constructor() {
        this.viewerEl = document.querySelector('.viewer');
        this.emptyEl = document.querySelector('.viewer-empty');
        this.detailEl = document.getElementById('insight-detail');
        this.titleEl = document.getElementById('insight-title');
        this.themeEl = document.getElementById('insight-theme');
        this.noveltyStarsEl = document.getElementById('insight-novelty-stars');
        this.noveltyScoreEl = document.getElementById('insight-novelty-score');
        this.dateEl = document.getElementById('insight-date');
        this.sourceEl = document.getElementById('insight-source');
        this.sourceRowEl = document.getElementById('source-row');
        this.conceptsEl = document.getElementById('insight-concepts');
        this.conceptsListEl = document.getElementById('concepts-list');
        this.tagsEl = document.getElementById('insight-tags');
        this.tagsListEl = document.getElementById('tags-list');
        this.contentEl = document.getElementById('insight-content');
        this.closeBtn = document.getElementById('close-insight');
        this.copyLinkBtn = document.getElementById('copy-link');
        this.openVaultBtn = document.getElementById('open-vault');
        this.currentInsight = null;
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.closeBtn.addEventListener('click', () => this.clear());
        this.copyLinkBtn.addEventListener('click', () => {
            if (this.currentInsight) {
                const url = `${window.location.href}#insight=${this.currentInsight.id}`;
                navigator.clipboard.writeText(url);
                const original = this.copyLinkBtn.textContent;
                this.copyLinkBtn.textContent = '✓ Copied';
                setTimeout(() => { this.copyLinkBtn.textContent = original; }, 2000);
            }
        });
        this.openVaultBtn.addEventListener('click', () => {
            if (this.currentInsight) {
                window.location.href = `obsidian://open?path=${this.currentInsight.filename}`;
            }
        });
    }

    async loadInsight(insightId) {
        try {
            const response = await fetch(`/api/vault/insight/${insightId}`);
            if (!response.ok) throw new Error('Insight not found');
            const insight = await response.json();
            this.currentInsight = insight;
            this.render(insight);
        } catch (error) {
            console.error('Error loading insight:', error);
            this.showError('Failed to load insight');
        }
    }

    render(insight) {
        this.titleEl.textContent = insight.source_title || insight.id;
        this.themeEl.textContent = insight.theme;
        this.themeEl.style.color = this.getThemeColor(insight.theme);
        const stars = this.getNoveltyStars(insight.novelty_score);
        this.noveltyStarsEl.textContent = stars;
        this.noveltyScoreEl.textContent = insight.novelty_score.toFixed(2);
        this.dateEl.textContent = this.formatDate(insight.date_added);
        
        if (insight.source_url && insight.source_url !== 'local-pdf' && insight.source_url !== 'unknown') {
            this.sourceRowEl.style.display = 'flex';
            const sourceLink = document.createElement('a');
            sourceLink.href = insight.source_url;
            sourceLink.target = '_blank';
            sourceLink.textContent = 'View Source';
            sourceLink.className = 'metadata-value';
            sourceLink.style.color = '#3b82f6';
            sourceLink.style.textDecoration = 'underline';
            this.sourceEl.replaceWith(sourceLink);
        } else {
            this.sourceRowEl.style.display = 'none';
        }

        if (insight.concepts && insight.concepts.length > 0) {
            this.conceptsEl.style.display = 'block';
            this.conceptsListEl.innerHTML = '';
            insight.concepts.forEach(concept => {
                const tag = document.createElement('span');
                tag.className = 'tag';
                tag.textContent = concept;
                this.conceptsListEl.appendChild(tag);
            });
        } else {
            this.conceptsEl.style.display = 'none';
        }

        if (insight.tags && insight.tags.length > 0) {
            this.tagsEl.style.display = 'block';
            this.tagsListEl.innerHTML = '';
            insight.tags.forEach(tag => {
                const tagEl = document.createElement('span');
                tagEl.className = 'tag';
                tagEl.textContent = tag;
                this.tagsListEl.appendChild(tagEl);
            });
        } else {
            this.tagsEl.style.display = 'none';
        }

        if (insight.html_content) {
            this.contentEl.innerHTML = insight.html_content;
        } else {
            const html = marked.parse(insight.content || '');
            this.contentEl.innerHTML = html;
        }
        this.processWikilinks();
        this.emptyEl.style.display = 'none';
        this.detailEl.style.display = 'block';
        this.viewerEl.scrollTop = 0;
    }

    processWikilinks() {
        const pattern = /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g;
        const contentText = this.contentEl.innerHTML;
        let result = contentText.replace(pattern, (match, target, display) => {
            const displayText = (display || target).trim();
            const targetClean = target.trim();
            return `<a href="javascript:app.loadInsight('${targetClean}')" class="wikilink">${displayText}</a>`;
        });
        this.contentEl.innerHTML = result;
    }

    getThemeColor(theme) {
        const colors = {
            'AI Infrastructure Moats': '#3b82f6',
            'VC Pattern Recognition': '#10b981',
            'Enterprise AI Adoption': '#f97316',
            'Agentic Systems': '#8b5cf6',
            'Cross-Theme Synthesis': '#6366f1',
            'Sources': '#64748b'
        };
        return colors[theme] || '#64748b';
    }

    getNoveltyStars(score) {
        const stars = Math.round(score * 5);
        return '★'.repeat(stars) + '☆'.repeat(5 - stars);
    }

    formatDate(dateStr) {
        if (!dateStr) return 'Unknown';
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
        } catch {
            return dateStr;
        }
    }

    clear() {
        this.currentInsight = null;
        this.emptyEl.style.display = 'flex';
        this.detailEl.style.display = 'none';
        this.contentEl.innerHTML = '';
    }

    showError(message) {
        this.emptyEl.textContent = message;
        this.emptyEl.style.display = 'flex';
        this.detailEl.style.display = 'none';
    }
}