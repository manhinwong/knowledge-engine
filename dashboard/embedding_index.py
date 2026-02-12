"""Semantic embedding index for vault insights."""

import os
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional


_model = None
STATE_DIR = Path(os.environ.get(
    'KNOWLEDGE_ENGINE_STATE_DIR',
    os.path.expanduser('~/.knowledge-engine')
))
INDEX_FILE = STATE_DIR / 'embedding_index.npz'
META_FILE = STATE_DIR / 'embedding_index_meta.json'


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def _build_text(insight_detail: Dict) -> str:
    """Build a single text string from an insight for embedding."""
    parts = []
    parts.append(insight_detail.get('source_title', ''))
    parts.append(' '.join(insight_detail.get('concepts', [])))
    parts.append(' '.join(insight_detail.get('tags', [])))
    content = insight_detail.get('content', '')
    parts.append(content[:4000])
    return ' '.join(p for p in parts if p)


def index_status(parser) -> Dict:
    """Check whether the embedding index exists and is valid."""
    if not INDEX_FILE.exists() or not META_FILE.exists():
        return {'built': False}
    try:
        with open(META_FILE, 'r') as f:
            meta = json.load(f)
        if str(parser.vault_path) != meta.get('vault_path'):
            return {'built': False}
        return {'built': True, 'count': meta.get('count', 0)}
    except Exception:
        return {'built': False}


def build_index(parser) -> int:
    """Build the embedding index from all vault insights. Returns count."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    model = _get_model()

    insights = parser.get_insights()
    ids = []
    texts = []

    for insight in insights:
        detail = parser.get_insight_detail(insight['id'])
        if not detail:
            continue
        ids.append(insight['id'])
        texts.append(_build_text(detail))

    if not texts:
        return 0

    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)

    np.savez(INDEX_FILE, ids=np.array(ids), embeddings=np.array(embeddings))
    with open(META_FILE, 'w') as f:
        json.dump({
            'vault_path': str(parser.vault_path),
            'count': len(ids)
        }, f)

    return len(ids)


def search_semantic(parser, query: str, theme: Optional[str] = None, limit: int = 20) -> List[Dict]:
    """Search vault using semantic similarity. Returns list of result dicts."""
    if not INDEX_FILE.exists():
        return []

    model = _get_model()
    data = np.load(INDEX_FILE, allow_pickle=True)
    ids = data['ids']
    embeddings = data['embeddings']

    query_embedding = model.encode([query], normalize_embeddings=True)
    scores = (embeddings @ query_embedding.T).flatten()

    # Get theme info for filtering
    graph = parser.parse_vault()
    node_map = {n['id']: n for n in graph['nodes']}

    ranked = []
    for idx in np.argsort(scores)[::-1]:
        doc_id = str(ids[idx])
        node = node_map.get(doc_id)
        if not node:
            continue
        if theme and node.get('theme') != theme:
            continue

        # Build snippet from content
        snippet = ''
        detail = parser.get_insight_detail(doc_id)
        if detail:
            content = detail.get('content', '')
            # Strip frontmatter-style lines and get clean text
            lines = [l for l in content.split('\n') if l.strip() and not l.startswith('#')]
            snippet = ' '.join(lines)[:160].strip()
            if len(' '.join(lines)) > 160:
                snippet += '...'

        ranked.append({
            'id': doc_id,
            'label': node.get('label', doc_id),
            'theme': node.get('theme', 'Other'),
            'score': round(float(scores[idx]), 4),
            'snippet': snippet
        })

        if len(ranked) >= limit:
            break

    return ranked
