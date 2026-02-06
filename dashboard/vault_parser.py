"""Parser for Obsidian Knowledge Vault with graph construction."""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import frontmatter


class VaultParser:
    """Parse Knowledge Vault markdown files and build graph structure."""

    # Default theme colors (can be extended as new themes are created)
    DEFAULT_COLORS = [
        "#3b82f6",  # Blue
        "#10b981",  # Green
        "#f97316",  # Orange
        "#8b5cf6",  # Purple
        "#6366f1",  # Indigo
        "#ec4899",  # Pink
        "#06b6d4",  # Cyan
        "#f59e0b",  # Amber
        "#84cc16",  # Lime
    ]

    def __init__(self, vault_path: str, cache_ttl_seconds: int = 300):
        """
        Initialize vault parser.

        Args:
            vault_path: Path to Obsidian vault root
            cache_ttl_seconds: Cache TTL in seconds (default 5 minutes)
        """
        self.vault_path = Path(vault_path)
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        self.cache = None
        self.cache_time = None
        self.file_index = {}  # filename -> full_path mapping
        self._theme_mapping = None
        self._theme_colors = None

    def _discover_themes(self):
        """Discover themes from vault folder structure."""
        if self._theme_mapping is not None:
            return self._theme_mapping, self._theme_colors

        mapping = {}
        colors = {}
        color_idx = 0

        # Look for numbered folders that contain _INDEX.md
        try:
            for folder in sorted(self.vault_path.iterdir()):
                if not folder.is_dir() or folder.name.startswith('.'):
                    continue

                index_file = folder / "_INDEX.md"
                if index_file.exists():
                    # Extract theme name from folder name
                    folder_name = folder.name
                    # Pattern: NN-Theme-Name -> Theme Name
                    if folder_name[0].isdigit():
                        theme_name = folder_name.split('-', 1)[1].replace('-', ' ')
                    else:
                        theme_name = folder_name.replace('-', ' ')

                    mapping[folder_name] = theme_name

                    # Assign color
                    color = self.DEFAULT_COLORS[color_idx % len(self.DEFAULT_COLORS)]
                    colors[theme_name] = color
                    color_idx += 1
        except Exception as e:
            print(f"Error discovering themes: {e}")

        self._theme_mapping = mapping
        self._theme_colors = colors
        return mapping, colors

    def get_theme_mapping(self):
        """Get folder name -> theme name mapping."""
        mapping, _ = self._discover_themes()
        return mapping

    def get_theme_colors(self):
        """Get theme name -> color mapping."""
        _, colors = self._discover_themes()
        return colors

    def parse_vault(self) -> Dict:
        """
        Parse entire vault and build graph structure.

        Returns:
            Dict with 'nodes', 'edges', 'orphans' keys
        """
        # Check cache
        if self.cache and self.cache_time and datetime.now() - self.cache_time < self.cache_ttl:
            return self.cache

        # Build file index first
        self._index_files()

        # Parse all markdown files
        documents = {}
        for file_path in self.vault_path.rglob("*.md"):
            if file_path.name == "_INDEX.md":
                continue  # Skip index files

            doc_id = self._get_doc_id(file_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    doc = frontmatter.load(f)
                    documents[doc_id] = {
                        'path': file_path,
                        'frontmatter': doc.metadata,
                        'content': doc.content,
                        'filename': file_path.name
                    }
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")

        # Build graph
        nodes = []
        edges = []
        wikilinks_found = {}  # Track all wikilinks for orphan detection

        # Get dynamic theme colors
        theme_colors = self.get_theme_colors()

        for doc_id, doc_data in documents.items():
            # Create node
            themes = doc_data['frontmatter'].get('themes', [])
            primary_theme = themes[0] if themes else "Other"

            # Default color for unknown themes
            default_color = "#64748b"

            node = {
                'id': doc_id,
                'label': doc_data['frontmatter'].get('source_title', doc_id),
                'type': 'insight',
                'theme': primary_theme,
                'color': theme_colors.get(primary_theme, default_color),
                'novelty_score': doc_data['frontmatter'].get('novelty_score', 0.5),
                'concepts': doc_data['frontmatter'].get('concepts', []),
                'tags': doc_data['frontmatter'].get('tags', []),
                'date_added': doc_data['frontmatter'].get('date_added', ''),
                'source_url': doc_data['frontmatter'].get('source_url', ''),
                'filename': doc_data['filename']
            }
            nodes.append(node)

            # Extract wikilinks
            wikilinks = self.extract_wikilinks(doc_data['content'])
            for link_target, link_display in wikilinks:
                if link_target not in wikilinks_found:
                    wikilinks_found[link_target] = []
                wikilinks_found[link_target].append(doc_id)

                # Resolve the link
                resolved = self.resolve_wikilink(link_target, doc_data['path'])
                if resolved:
                    target_id = resolved['id']
                    edges.append({
                        'source': doc_id,
                        'target': target_id,
                        'type': 'wikilink',
                        'display': link_display or link_target
                    })

        # Find orphan links
        orphans = []
        for link_target, referenced_by in wikilinks_found.items():
            # Check if target exists in our documents
            resolved = self.resolve_wikilink(link_target, None)
            if not resolved:
                orphans.append({
                    'link': link_target,
                    'referenced_by': referenced_by
                })

        graph = {
            'nodes': nodes,
            'edges': edges,
            'orphans': orphans
        }

        # Cache result
        self.cache = graph
        self.cache_time = datetime.now()

        return graph

    def _index_files(self):
        """Build index of filename -> path mapping."""
        self.file_index = {}
        for file_path in self.vault_path.rglob("*.md"):
            filename = file_path.stem  # Without .md extension
            self.file_index[filename] = file_path

    def _get_doc_id(self, file_path: Path) -> str:
        """Get document ID from file path (stem without .md)."""
        return file_path.stem

    def extract_wikilinks(self, content: str) -> List[Tuple[str, Optional[str]]]:
        """
        Extract wikilinks from markdown content.

        Handles both formats:
        - [[target]]
        - [[target|display]]

        Args:
            content: Markdown content

        Returns:
            List of (target, display) tuples
        """
        pattern = r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'
        matches = re.findall(pattern, content)
        return [(target.strip(), display.strip() if display else None) for target, display in matches]

    def resolve_wikilink(self, link: str, current_file: Optional[Path]) -> Optional[Dict]:
        """
        Resolve wikilink to actual file.

        Handles:
        - Simple names: [[insight-name]]
        - Relative paths: [[../other-folder/insight]]
        - With display: [[path|display]]

        Args:
            link: Link target
            current_file: Current file path (for relative resolution)

        Returns:
            Dict with 'id' and 'path', or None if not found
        """
        # Ensure file index is built
        if not self.file_index:
            self._index_files()

        # Remove any display text (shouldn't happen if called from extract_wikilinks)
        link = link.split('|')[0].strip()

        # Try direct lookup in file index
        if link in self.file_index:
            return {
                'id': link,
                'path': self.file_index[link]
            }

        # Try with relative path resolution
        if current_file and '/' in link:
            # Handle relative paths like ../other-folder/filename
            base_dir = current_file.parent
            potential_path = (base_dir / link).resolve()

            if potential_path.exists() and potential_path.suffix == '.md':
                return {
                    'id': potential_path.stem,
                    'path': potential_path
                }

        return None

    def get_insights(self, theme: Optional[str] = None, tags: Optional[List[str]] = None,
                     min_novelty: float = 0.0) -> List[Dict]:
        """
        Get list of insights with optional filtering.

        Args:
            theme: Filter by theme
            tags: Filter by tags (any match)
            min_novelty: Minimum novelty score

        Returns:
            List of insight dictionaries
        """
        graph = self.parse_vault()
        insights = graph['nodes']

        # Filter
        if theme:
            insights = [i for i in insights if i['theme'] == theme]
        if tags:
            insights = [i for i in insights if any(t in i['tags'] for t in tags)]
        if min_novelty > 0:
            insights = [i for i in insights if i['novelty_score'] >= min_novelty]

        # Sort by date added (newest first)
        insights.sort(key=lambda x: x['date_added'], reverse=True)
        return insights

    def get_insight_detail(self, doc_id: str) -> Optional[Dict]:
        """
        Get full detail for a single insight including rendered content.

        Args:
            doc_id: Document ID

        Returns:
            Dict with all metadata and content, or None if not found
        """
        # Ensure file index is built
        if not self.file_index:
            self._index_files()

        if doc_id not in self.file_index:
            return None

        file_path = self.file_index[doc_id]

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                doc = frontmatter.load(f)

                return {
                    'id': doc_id,
                    'filename': file_path.name,
                    'filepath': str(file_path.absolute()),
                    'frontmatter': doc.metadata,
                    'content': doc.content,
                    'theme': doc.metadata.get('themes', ['Other'])[0],
                    'novelty_score': doc.metadata.get('novelty_score', 0.5),
                    'concepts': doc.metadata.get('concepts', []),
                    'tags': doc.metadata.get('tags', []),
                    'date_added': doc.metadata.get('date_added', ''),
                    'source_url': doc.metadata.get('source_url', ''),
                    'source_title': doc.metadata.get('source_title', doc_id)
                }
        except Exception as e:
            print(f"Error loading insight {doc_id}: {e}")
            return None

    def get_themes_summary(self) -> Dict:
        """
        Get summary of all themes with counts and latest dates.

        Returns:
            Dict mapping theme name -> {count, latest_date, color}
        """
        insights = self.get_insights()
        summary = {}

        # Get dynamic theme colors
        theme_colors = self.get_theme_colors()

        # Collect all unique themes from insights
        all_themes = set(i['theme'] for i in insights)

        for theme in sorted(all_themes):
            theme_insights = [i for i in insights if i['theme'] == theme]
            if theme_insights:
                latest = max(insight['date_added'] for insight in theme_insights)
                color = theme_colors.get(theme, "#64748b")
                summary[theme] = {
                    'count': len(theme_insights),
                    'latest_date': latest,
                    'color': color
                }

        return summary

    def search(self, query: str, theme: Optional[str] = None) -> List[Dict]:
        """
        Search insights by query string.

        Searches in: title, source_title, concepts, tags, content.

        Args:
            query: Search query
            theme: Optional theme filter

        Returns:
            List of matching insights
        """
        # Ensure file index is built
        if not self.file_index:
            self._index_files()

        query_lower = query.lower()
        insights = self.get_insights(theme=theme)
        results = []

        for insight in insights:
            # Search in multiple fields
            searches = [
                insight['label'].lower(),
                insight.get('source_title', '').lower(),
                ' '.join(insight.get('concepts', [])).lower(),
                ' '.join(insight.get('tags', [])).lower()
            ]

            # Also search content if available
            detail = self.get_insight_detail(insight['id'])
            if detail:
                searches.append(detail['content'].lower())

            if any(query_lower in search for search in searches):
                results.append(insight)

        return results

    def refresh(self):
        """Force refresh of cached data."""
        self.cache = None
        self.cache_time = None
        self.file_index = {}
