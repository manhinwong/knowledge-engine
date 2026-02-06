class KnowledgeEngineApp {
    constructor() {
        this.graph = null;
        this.sidebar = null;
        this.viewer = null;
        this.graphData = null;
    }

    async initialize() {
        console.log('Initializing Knowledge Engine Dashboard...');
        try {
            this.showLoading(true);
            this.sidebar = new Sidebar();
            this.viewer = new InsightViewer();
            this.graph = new KnowledgeGraph('#knowledge-graph');
            await this.initializeData();
            this.setupEventListeners();
            console.log('Dashboard initialized successfully');
        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            this.showError('Failed to load dashboard');
        } finally {
            this.showLoading(false);
        }
    }

    async initializeData() {
        try {
            await this.sidebar.loadThemes();
            const response = await fetch('/api/vault/graph');
            if (!response.ok) throw new Error('Failed to load graph data');
            this.graphData = await response.json();
            this.graph.render(this.graphData, {
                onRender: (stats) => this.updateGraphStats(stats)
            });
        } catch (error) {
            console.error('Error initializing data:', error);
            throw error;
        }
    }

    setupEventListeners() {
        this.graph.setNodeClickCallback((node) => {
            this.viewer.loadInsight(node.id);
        });

        this.sidebar.setThemeClickCallback((theme) => {
            if (theme) {
                this.graph.filterByTheme(theme);
                this.loadGraphByTheme(theme);
            } else {
                this.graph.clearFilter();
                this.graph.render(this.graphData);
            }
        });

        this.sidebar.setSearchCallback((resultNodeIds) => {
            if (resultNodeIds && resultNodeIds.length > 0) {
                this.graph.highlightSearchResults(resultNodeIds);
            } else {
                this.graph.highlightSearchResults([]);
            }
        });

        document.getElementById('zoom-in').addEventListener('click', () => {
            this.graph.svg.transition().duration(300).call(d3.zoom().scaleBy, 1.3);
        });

        document.getElementById('zoom-out').addEventListener('click', () => {
            this.graph.svg.transition().duration(300).call(d3.zoom().scaleBy, 0.77);
        });

        document.getElementById('reset-view').addEventListener('click', () => {
            this.graph.resetView();
        });
    }

    async loadGraphByTheme(theme) {
        try {
            const response = await fetch(`/api/vault/graph?theme=${encodeURIComponent(theme)}`);
            if (!response.ok) throw new Error('Failed to load theme graph');
            const graphData = await response.json();
            this.graph.render(graphData, { onRender: (stats) => this.updateGraphStats(stats) });
        } catch (error) {
            console.error('Error loading theme graph:', error);
        }
    }

    updateGraphStats(stats) {
        const statsEl = document.getElementById('graph-stats');
        if (statsEl) {
            statsEl.textContent = `${stats.nodeCount} nodes • ${stats.linkCount} connections`;
        }
    }

    showLoading(show) {
        const loadingEl = document.getElementById('graph-loading');
        if (loadingEl) {
            if (show) {
                loadingEl.classList.add('active');
            } else {
                loadingEl.classList.remove('active');
            }
        }
    }

    showError(message) {
        const errorEl = document.querySelector('.viewer-empty');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = 'flex';
        }
    }

    async loadInsight(insightId) {
        document.querySelector('.graph-container').scrollTop = 0;
        await this.viewer.loadInsight(insightId);
    }
}

let app = null;

document.addEventListener('DOMContentLoaded', async () => {
    app = new KnowledgeEngineApp();
    await app.initialize();
    window.app = app;
});

window.addEventListener('resize', () => {
    if (app && app.graph) {
        app.graph.onWindowResize();
    }
});