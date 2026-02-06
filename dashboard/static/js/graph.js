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

        // Calculate connection count for each node
        const connectionCount = {};
        this.nodes.forEach(node => {
            connectionCount[node.id] = 0;
        });
        this.links.forEach(link => {
            connectionCount[link.source]++;
            connectionCount[link.target]++;
        });
        this.nodes.forEach(node => {
            node.connections = connectionCount[node.id] || 0;
        });

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
            .attr('fill', d => d.color || '#3b82f6')
            .attr('stroke', d => d.connections === 0 ? '#cbd5e1' : '#ffffff')
            .attr('stroke-width', 2)
            .attr('stroke-dasharray', d => d.connections === 0 ? '4,4' : '0')
            .attr('opacity', d => d.connections === 0 ? 0.6 : 1)
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
            const connectionText = node.connections === 0 ? 'Orphaned (0 connections)' : `${node.connections} connections`;
            tooltip.innerHTML = `<strong>${node.label}</strong><br>${node.theme}<br>Connections: ${connectionText}<br>Novelty: ${node.novelty_score.toFixed(2)}`;
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
        // Size based on number of connections (development level)
        // More connections = larger node = well-developed topic
        const connections = node.connections || 0;
        const baseRadius = 6;
        const maxRadius = 25;
        const radius = baseRadius + Math.min(connections, 15) * (maxRadius - baseRadius) / 15;
        return radius;
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
        console.log('Highlighting search results:', nodeIds);

        // Reset all nodes first
        this.nodesGroup.selectAll('circle.node-circle')
            .attr('stroke-width', 2)
            .attr('stroke', '#ffffff')
            .attr('r', d => this.getNodeRadius(d))
            .attr('opacity', 0.7);

        // Highlight matching nodes by iterating through nodeIds
        nodeIds.forEach(nodeId => {
            const nodeElement = this.svg.select(`#node-${nodeId}`);
            console.log(`Looking for node #node-${nodeId}, found: ${!nodeElement.empty()}`);
            if (!nodeElement.empty()) {
                nodeElement.select('circle.node-circle')
                    .attr('stroke-width', 20)
                    .attr('stroke', '#ffd700')
                    .attr('r', d => this.getNodeRadius(d) + 6)
                    .attr('opacity', 1)
                    .attr('filter', 'brightness(1.2)');
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