#!/usr/bin/env python3
"""
Knowledge Engine CLI - Interact with the Letta-powered knowledge accumulation agent.

Usage:
    ke process <url>          Process article and extract unique insights
    ke explain <concept>      Get explanation from knowledge base
    ke relevance <url>        Quick relevance check before processing
    ke connect <concept>      Find cross-article connections
    ke unique <text>          Check if concept is novel
    ke themes [--theme X]     Show theme status
    ke synthesize <theme>     Generate synthesis document
"""

import os
import sys

import click
from dotenv import load_dotenv

from agent import KnowledgeAgent

# Load environment variables from .env file
load_dotenv()

# Global agent instance
_agent = None


def get_agent():
    """Get or create the knowledge agent."""
    global _agent
    if _agent is None:
        _agent = KnowledgeAgent()
    return _agent


def send_message(message: str):
    """Send message to agent and print response."""
    agent = get_agent()

    try:
        response = agent.send_message(message)
        click.echo(response)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@click.group()
def cli():
    """Knowledge Engine - Letta-powered learning assistant."""
    pass


@cli.command()
@click.argument('url')
def process(url):
    """Process a URL and extract unique insights.

    Fetches the article, extracts novel insights (filtering out known concepts),
    maps them to learning themes, and saves to Obsidian vault.
    """
    click.echo(f"Processing: {url}\n")

    send_message(f"""Process this article for unique insights: {url}

Instructions:
1. Fetch and parse the article using fetch_and_parse_article
2. Search archival memory for related existing concepts
3. Extract only NOVEL insights (filter out anything in known_concepts_summary or archival memory)
4. For each unique insight:
   - Assign a novelty_score (0-1)
   - Map to relevant themes
   - Find potential connections to existing insights
5. Save insights to Obsidian vault with proper frontmatter and wikilinks
6. Update the theme _INDEX.md files
7. Update known_concepts_summary in core memory with new concepts learned

Provide a summary of what was extracted and saved.""")


@cli.command()
@click.argument('concept')
def explain(concept):
    """Get explanation of a concept from knowledge base.

    Searches archival memory for all related insights and synthesizes
    a clear explanation with connections to learning themes.
    """
    send_message(f"""Explain this concept from my knowledge base: {concept}

Search archival memory for all insights related to this concept.
Synthesize a clear explanation with:
- Definition and key aspects
- How it connects to my learning themes
- Source articles for deeper reading
- Related concepts in the knowledge base""")


@cli.command()
@click.argument('url')
def relevance(url):
    """Quick relevance check before full processing.

    Fetches the article and provides relevance scores for each theme
    along with a recommendation on whether to process fully.
    """
    click.echo(f"Checking relevance: {url}\n")

    send_message(f"""Quick relevance check for: {url}

Fetch the article and provide:
- Relevance score (0-10) for each of my 4 learning themes
- Estimated unique insights (vs concepts I already know)
- Key topics covered
- Recommendation: PROCESS (high value), SKIM (moderate), or SKIP (low relevance/novelty)""")


@cli.command()
@click.argument('concept')
def connect(concept):
    """Find connections for a concept across the knowledge base.

    Searches archival memory to find related insights from different
    articles and themes, identifying synthesis opportunities.
    """
    send_message(f"""Find all connections for: {concept}

Search archival memory and show:
- Related insights across different articles
- Cross-theme connections (how this concept bridges themes)
- Potential synthesis opportunities
- Suggested wikilinks to create in Obsidian""")


@cli.command()
@click.argument('text')
def unique(text):
    """Check if a concept/insight is novel to the knowledge base.

    Returns a novelty score and shows any existing related entries.
    """
    send_message(f"""Novelty check: {text}

Search archival memory and determine:
- Is this concept/insight already captured?
- If yes, show the existing entries
- If partially known, what's the new angle?
- Novelty score: 0 (fully known) to 1 (completely new)""")


@cli.command()
@click.option('--theme', '-t', default=None, help='Specific theme to analyze')
def themes(theme):
    """Show theme status and recent insights.

    Without --theme: shows overview of all themes
    With --theme: shows detailed status for that theme
    """
    if theme:
        query = f"Show detailed status for theme: {theme}"
    else:
        query = "Show status of all 4 learning themes"

    send_message(f"""{query}

Include:
- Insight count per theme (from archival memory)
- Recent additions (last 7 days if any)
- Key concepts covered
- Gaps or areas needing more exploration
- Suggested next readings or topics to explore""")


@cli.command()
@click.argument('theme')
def synthesize(theme):
    """Generate synthesis document for a theme.

    Creates a comprehensive synthesis of all insights for a theme,
    identifying patterns, connections, and knowledge gaps.
    """
    click.echo(f"Generating synthesis for: {theme}\n")

    send_message(f"""Create a synthesis document for theme: {theme}

Search all insights for this theme in archival memory and create:
1. Executive summary of key learnings
2. Main concepts and their relationships
3. Patterns and principles discovered across articles
4. Open questions and knowledge gaps
5. Cross-theme connections

Save to Obsidian as a synthesis note in 05-Cross-Theme-Synthesis/ with:
- Filename: YYYY-MM-DD-synthesis-{theme.lower().replace(' ', '-')}.md
- Proper frontmatter with theme tags
- Wikilinks to all referenced insights""")


@cli.command()
def status():
    """Show agent status and memory stats."""
    client = get_client()
    agent_id = get_agent_id()

    try:
        agent = client.agents.get(agent_id)
        click.echo(f"Agent: {agent.name}")
        click.echo(f"ID: {agent.id}")
        click.echo(f"Model: {agent.model}")

        # Get memory stats
        memory = client.agents.core_memory.get_block(agent_id, "known_concepts_summary")
        click.echo(f"\nKnown Concepts Summary:")
        click.echo(memory.value)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.argument('title')
@click.argument('url')
@click.option('--notes', '-n', required=True, help='Your notes and reactions')
@click.option('--points', '-p', multiple=True, help='Key points (can specify multiple times)')
@click.option('--themes', '-t', multiple=True, help='Related themes (can specify multiple times)')
def add(title, url, notes, points, themes):
    """Add a reading with manual notes and key points.

    Example:
        ke add "RAG Systems" "https://example.com" \\
            --notes "Interesting approach to reducing hallucinations" \\
            --points "Uses semantic search" \\
            --points "Retrieval augments generation" \\
            --themes "AI Infrastructure Moats"
    """
    # Convert tuples to comma-separated strings for the tool
    key_points_str = ', '.join(points) if points else ''
    themes_str = ', '.join(themes) if themes else ''

    click.echo(f"Adding reading: {title}\n")

    send_message(f"""Add this manual reading using add_manual_reading tool:

Title: {title}
URL: {url}
User Notes: {notes}
Key Points: {key_points_str}
Themes: {themes_str}

After storing, tell me the reading_id that was generated.""")


@cli.command()
@click.argument('query')
@click.option('--limit', '-l', default=10, help='Maximum results to return')
def search(query, limit):
    """Search for readings matching the query.

    Searches across titles, key points, user notes, and themes.

    Example:
        ke search "RAG systems"
        ke search "retrieval" --limit 5
    """
    send_message(f"""Search for readings using search_readings tool with:
Query: {query}
Limit: {limit}

Display the results in a clear format showing:
- Reading ID
- Title
- Themes
- Excerpt from notes
- Source URL""")


@cli.command()
@click.argument('reading_id')
def get(reading_id):
    """Retrieve a specific reading by its ID.

    Example:
        ke get reading-20260127-rag-systems
    """
    send_message(f"""Retrieve the reading using get_reading_by_id tool:
Reading ID: {reading_id}

Display the complete reading with all fields:
- Title
- Source URL
- Date Added
- Key Points (all of them)
- User Notes (full text)
- Themes""")


if __name__ == "__main__":
    cli()
