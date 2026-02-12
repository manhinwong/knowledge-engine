"""FastAPI routes for Knowledge Engine dashboard."""

import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
import markdown2

from dashboard.vault_parser import VaultParser
from dashboard.embedding_index import build_index, index_status, search_semantic


router = APIRouter(tags=["dashboard"])

# Initialize vault parser (lazy load on first request)
_parser: Optional[VaultParser] = None


def get_parser() -> VaultParser:
    """Get or initialize vault parser."""
    global _parser
    if _parser is None:
        vault_path = os.environ.get(
            'OBSIDIAN_VAULT_PATH',
            '/data/vault'
        )
        _parser = VaultParser(vault_path)
    return _parser


@router.get("/dashboard")
async def dashboard_home():
    """Serve dashboard homepage."""
    dashboard_path = os.path.join(
        os.path.dirname(__file__),
        "static",
        "index.html"
    )
    return FileResponse(dashboard_path)


@router.get("/api/vault/graph")
async def get_graph(theme: Optional[str] = Query(None)):
    """
    Get knowledge graph data (nodes, edges, orphans).

    Args:
        theme: Optional theme filter

    Returns:
        Graph structure with nodes, edges, orphans
    """
    try:
        parser = get_parser()
        graph = parser.parse_vault()

        # Filter by theme if requested
        if theme:
            filtered_nodes = [n for n in graph['nodes'] if n['theme'] == theme]
            node_ids = {n['id'] for n in filtered_nodes}

            # Filter edges to only include connections within theme
            filtered_edges = [e for e in graph['edges'] if e['source'] in node_ids or e['target'] in node_ids]

            return {
                'nodes': filtered_nodes,
                'edges': filtered_edges,
                'orphans': graph['orphans']
            }

        return graph

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing vault: {str(e)}")


@router.get("/api/vault/insights")
async def get_insights(
    theme: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    min_novelty: float = Query(0.0)
):
    """
    Get list of insights with optional filters.

    Args:
        theme: Filter by theme
        tag: Filter by tag
        min_novelty: Minimum novelty score

    Returns:
        List of insights
    """
    try:
        parser = get_parser()
        tags = [tag] if tag else None
        insights = parser.get_insights(theme=theme, tags=tags, min_novelty=min_novelty)
        return {'insights': insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/vault/insight/{insight_id}")
async def get_insight_detail(insight_id: str):
    """
    Get full detail for a specific insight.

    Args:
        insight_id: Document ID

    Returns:
        Full insight detail with rendered HTML
    """
    try:
        parser = get_parser()
        insight = parser.get_insight_detail(insight_id)

        if not insight:
            raise HTTPException(status_code=404, detail=f"Insight {insight_id} not found")

        # Convert markdown to HTML
        html_content = markdown2.markdown(
            insight['content'],
            extras=['fenced-code-blocks', 'tables', 'task_lists']
        )

        # Convert wikilinks in HTML
        html_content = _process_wikilinks_in_html(html_content, parser)

        insight['html_content'] = html_content

        return insight

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/vault/themes")
async def get_themes_summary():
    """
    Get summary of all themes with counts.

    Returns:
        Theme summary with counts and latest dates
    """
    try:
        parser = get_parser()
        summary = parser.get_themes_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/vault/search")
async def search_insights(
    q: str = Query(...),
    theme: Optional[str] = Query(None),
    semantic: bool = Query(True),
    limit: int = Query(25, le=100)
):
    """Search insights by query with optional semantic search."""
    try:
        parser = get_parser()

        if semantic and index_status(parser).get('built'):
            results = search_semantic(parser, q, theme=theme, limit=limit)
            return {'results': results, 'count': len(results), 'semantic': True}
        else:
            results = parser.search(q, theme=theme)[:limit]
            formatted = []
            for r in results:
                formatted.append({
                    'id': r['id'],
                    'label': r.get('label', r['id']),
                    'theme': r.get('theme', 'Other'),
                    'score': None,
                    'snippet': None
                })
            return {'results': formatted, 'count': len(formatted), 'semantic': False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/vault/embedding-index/status")
async def embedding_index_status():
    """Get embedding index status."""
    try:
        parser = get_parser()
        return index_status(parser)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/vault/embedding-index/build")
async def build_embedding_index():
    """Build or rebuild the embedding index."""
    from server import DEMO_MODE
    if DEMO_MODE:
        raise HTTPException(status_code=403, detail="Demo mode: write operations disabled")
    try:
        parser = get_parser()
        parser.refresh()
        count = build_index(parser)
        return {'status': 'success', 'count': count, 'message': f'Indexed {count} insights'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/vault/refresh")
async def refresh_vault():
    """Force refresh of vault parsing cache."""
    from server import DEMO_MODE
    if DEMO_MODE:
        raise HTTPException(status_code=403, detail="Demo mode: write operations disabled")
    try:
        parser = get_parser()
        parser.refresh()
        return {'status': 'success', 'message': 'Vault cache refreshed'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _process_wikilinks_in_html(html: str, parser: VaultParser) -> str:
    """
    Convert wikilinks in HTML to clickable links.

    Args:
        html: HTML content
        parser: VaultParser instance

    Returns:
        HTML with wikilinks converted to links
    """
    import re

    # Pattern for wikilinks: [[target|display]] or [[target]]
    pattern = r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'

    def replace_link(match):
        target = match.group(1).strip()
        display = (match.group(2) or target).strip()

        # Try to resolve the link
        resolved = parser.resolve_wikilink(target, None)
        if resolved:
            # Create link to insight viewer
            href = f"javascript:app.loadInsight('{resolved['id']}')"
            return f'<a href="{href}" class="wikilink">{display}</a>'
        else:
            # Orphan link
            return f'<span class="wikilink-orphan">{display}</span>'

    return re.sub(pattern, replace_link, html)
