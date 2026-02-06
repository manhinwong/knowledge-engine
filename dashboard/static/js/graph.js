/**
 * Knowledge Graph Visualization using D3.js v7
 */

class KnowledgeGraph {
    constructor(svgSelector) {
        this.svgSelector = svgSelector;
        this.svg = d3.select(svgSelector);
        this.width = this.svg.node().clientWidth;
        this.height = this.svg.node().clientHeight;
        this.simulation = null;
        this.nodes = [];
        this.links = [];
        this.graph = null;
        this.currentTheme = null;
        this.highlightedNode = null;
        this.nodeClickCallback = null;
        this.zoomBehavior = null;

        this.createSvgElements();
        this.setupZoom();
        window.addEventListener('resize', () => this.onWindowResize());
    }

    createSvgElements() {
        this.svg.selectAll('*').remove();
        this.svg.append('rect').attr('width', this.width).attr('height', this.height).style('fill', 'white');
        this.mainGroup = this.svg.append('g').attr('class', 'graph-main');
        this.linksGroup = this.mainGroup.append('g').attr('class', 'links');
        this.nodesGroup = this.mainGroup.append('g').attr('class', 'nodes');
        this.labelsGroup = this.mainGroup.append('g').attr('class', 'labels');
    }

    setupZoom() {
        this.zoomBehavior = d3.zoom().on('zoom', (event) => {
            this.mainGroup.attr('transform', event.transform);
        }).scaleExtent([0.5, 5]);
        this.svg.call(this.zoomBehavior);
    }

    render(graphData, options = {}) {
        this.graph = graphData;
        this.nodes = graphData.nodes.map(d => ({ ...d }));
        this.links = graphData.edges.map(d => ({
            source: d.source,
            target: d.target,
            display: d.display,
            type: d.type
        }));

        this.simulation = d3.forceSimulation(this.nodes)
            .force('link', d3.forceLink(this.links).id(d => d.id).distance(120).strength(0.3))
            .force('charge', d3.forceManyBody().strength(-400).distanceMax(500))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(d => this.getNodeRadius(d) + 10));

        this.renderLinks();
        this.renderNodes();
        this.renderLabels();
        this.simulation.on('tick', () => this.onSimulationTick());

        if (options.onRender) {
            options.onRender({
                nodeCount: this.nodes.length,
                linkCount: this.links.length,
                orphanCount: graphData.orphans.length
            });
        }
    }

    renderLinks() {
        const links = this.linksGroup.selectAll('line')
            .data(this.links, d => `${d.source.id || d.source}-${d.target.id || d.target}`)
            .join('line').attr('class', 'link').attr('stroke-width', 1.5).attr('stroke', '#e2e8f0').attr('opacity', 0.6);
        this.linkElements = links;
    }

    renderNodes() {
        const nodes = this.nodesGroup.selectAll('g.node').data(this.nodes, d => d.id)
            .join(enter => enter.append('g').attr('class', 'node').attr('id', d => `node-${d.id}`), update => update, exit => exit.remove());
        nodes.append('circle').attr('class', 'node-circle').attr('r', d => this.getNodeRadius(d))
            .attr('fill', d => d.color || '#3b82f6').attr('stroke', '#ffffff').attr('stroke-width', 2)
            .style('cursor', 'pointer')
            .on('click', (e, d) => this.onNodeClick(d))
            .on('mouseenter', (e, d) => this.onNodeHover(d, true))
            .on('mouseleave', (e, d) => this.onNodeHover(d, false));
        nodes.call(this.createDragBehavior());
        this.nodeElements = nodes;
    }

    renderLabels() {
        const labels = this.labelsGroup.selectAll('text.node-label').data(this.nodes, d => d.id)
            .join(enter => enter.append('text').attr('class', 'node-label').attr('text-anchor', 'middle').attr('dy', '.35em'), update => update, exit => exit.remove())
            .text(d => this.truncateLabel(d.label, 15)).attr('font-size', '11px').attr('fill', '#1e293b').style('pointer-events', 'none');
        this.labelElements = labels;
    }

    createDragBehavior() {
        return d3.drag()
            .on('start', (e, d) => { if (!e.active) this.simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
            .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y; })
            .on('end', (e, d) => { if (!e.active) this.simulation.alphaTarget(0); d.fx = null; d.fy = null; });
    }

    onSimulationTick() {
        if (this.linkElements) this.linkElements.attr('x1', d => d.source.x).attr('y1', d => d.source.y).attr('x2', d => d.target.x).attr('y2', d => d.target.y);
        if (this.nodeElements) this.nodeElements.attr('transform', d => `translate(${d.x},${d.y})`);
        if (this.labelElements) this.labelElements.attr('x', d => d.x).attr('y', d => d.y);
    }

    onNodeClick(node) {
        this.highlightedNode = node;
        if (this.nodeClickCallback) this.nodeClickCallback(node);
        this.updateHighlight();
    }

    onNodeHover(node, isHovering) {
        if (isHovering) {
            const tooltip = document.querySelector('.tooltip') || this.createTooltip();
            tooltip.innerHTML = `<strong>${node.label}</strong><br>${node.theme}<br>Novelty: ${node.novelty_score.toFixed(2)}`;
            tooltip.style.display = 'block';
        }
    }

    createTooltip() {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        document.body.appendChild(tooltip);
        return tooltip;
    }

    getNodeRadius(node) {
        const score = Math.max(0.5, Math.min(1.0, node.novelty_score || 0.5));
        return 5 + (score - 0.5) * 20;
    }

    truncateLabel(text, length) {
        if (text.length <= length) return text;
        return text.substring(0, length) + '...';
    }

    highlightNode(nodeId) {
        const node = this.nodes.find(n => n.id === nodeId);
        if (node) this.onNodeClick(node);
    }

    filterByTheme(theme) {
        this.currentTheme = theme;
        this.updateHighlight();
    }

    clearFilter() {
        this.currentTheme = null;
        this.updateHighlight();
    }

    updateHighlight() {
        if (this.nodeElements) this.nodeElements.classed('dimmed', d => this.currentTheme && d.theme !== this.currentTheme);
        if (this.labelElements) this.labelElements.classed('dimmed', d => this.currentTheme && d.theme !== this.currentTheme);
        if (this.linkElements) this.linkElements.classed('dimmed', d => {
            if (this.currentTheme) return d.source.theme !== this.currentTheme && d.target.theme !== this.currentTheme;
            return false;
        });
    }

    highlightSearchResults(nodeIds) {
        // Reset all nodes first
        this.nodesGroup.selectAll('circle.node-circle')
            .style('stroke-width', 2)
            .style('stroke', '#ffffff')
            .style('filter', 'none');

        // Highlight matching nodes by iterating through nodeIds
        nodeIds.forEach(nodeId => {
            const nodeElement = this.svg.select(`#node-${nodeId}`);
            if (!nodeElement.empty()) {
                nodeElement.select('circle.node-circle')
                    .style('stroke-width', 4)
                    .style('stroke', '#fbbf24')
                    .style('filter', 'brightness(1.3) drop-shadow(0 0 8px rgba(251, 191, 36, 0.6))');
            }
        });
    }

    resetView() {
        this.svg.transition().duration(750).call(d3.zoom().transform, d3.zoomIdentity.translate(10, 10));
    }

    onWindowResize() {
        const newWidth = this.svg.node().clientWidth;
        const newHeight = this.svg.node().clientHeight;
        if (newWidth !== this.width || newHeight !== this.height) {
            this.width = newWidth;
            this.height = newHeight;
            this.svg.attr('width', this.width).attr('height', this.height);
            if (this.simulation) {
                this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2)).alpha(0.3).restart();
            }
        }
    }

    setNodeClickCallback(callback) {
        this.nodeClickCallback = callback;
    }
}