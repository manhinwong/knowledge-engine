"""Obsidian vault operations for Letta agent."""

import json
import os
from datetime import datetime

import yaml


def save_to_obsidian(
    content: str,
    filename: str,
    folder: str,
    frontmatter: str,
    mode: str = "create"
) -> str:
    """
    Saves or appends content to an Obsidian vault markdown file.

    Args:
        content: Markdown content to write.
        filename: Target filename (e.g., '2026-01-27-insight-title.md').
        folder: Theme folder path (e.g., '01-AI-Infrastructure-Moats').
        frontmatter: YAML frontmatter as JSON string to convert.
        mode: 'create' for new file, 'append' to add to existing file.

    Returns:
        JSON string with success status and file path.
    """
    vault_path = os.environ.get(
        'OBSIDIAN_VAULT_PATH',
        '/Users/marcuswong/Documents/KnowledgeVault'
    )

    full_path = os.path.join(vault_path, folder, filename)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    try:
        fm_dict = json.loads(frontmatter)
        fm_yaml = yaml.dump(fm_dict, default_flow_style=False, allow_unicode=True)

        if mode == "create":
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(f"---\n{fm_yaml}---\n\n{content}")
        elif mode == "append":
            with open(full_path, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                f.write(f"\n\n---\n*Added: {timestamp}*\n\n{content}")

        return json.dumps({
            "status": "success",
            "path": full_path,
            "mode": mode,
            "filename": filename
        })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "path": full_path
        })


def update_theme_index(theme: str, new_insight_file: str, insight_summary: str) -> str:
    """
    Updates the theme index file (MOC) with a new insight reference.

    Args:
        theme: Theme name to update index for.
        new_insight_file: Filename of the new insight to link (without .md).
        insight_summary: One-line summary for the index entry.

    Returns:
        JSON string confirming the update.
    """
    vault_path = os.environ.get(
        'OBSIDIAN_VAULT_PATH',
        '/Users/marcuswong/Documents/KnowledgeVault'
    )

    theme_folders = {
        "AI Infrastructure Moats": "01-AI-Infrastructure-Moats",
        "VC Pattern Recognition": "02-VC-Pattern-Recognition",
        "Enterprise AI Adoption": "03-Enterprise-AI-Adoption",
        "Agentic Systems Architecture": "04-Agentic-Systems",
    }

    folder = theme_folders.get(theme, "05-Cross-Theme-Synthesis")
    index_path = os.path.join(vault_path, folder, "_INDEX.md")

    try:
        date_str = datetime.now().strftime("%Y-%m-%d")
        entry = f"- [[{new_insight_file}]] - {insight_summary} ({date_str})\n"

        with open(index_path, 'a', encoding='utf-8') as f:
            f.write(entry)

        return json.dumps({
            "status": "success",
            "index_path": index_path,
            "entry_added": entry.strip()
        })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "index_path": index_path
        })


# Tool source codes for Letta registration
SAVE_OBSIDIAN_TOOL_SOURCE = '''
import json
import os
from datetime import datetime
import yaml

def save_to_obsidian(
    content: str,
    filename: str,
    folder: str,
    frontmatter: str,
    mode: str = "create"
) -> str:
    """
    Saves or appends content to an Obsidian vault markdown file.

    Args:
        content: Markdown content to write.
        filename: Target filename (e.g., '2026-01-27-insight-title.md').
        folder: Theme folder path (e.g., '01-AI-Infrastructure-Moats').
        frontmatter: YAML frontmatter as JSON string to convert.
        mode: 'create' for new file, 'append' to add to existing file.

    Returns:
        JSON string with success status and file path.
    """
    vault_path = os.environ.get(
        'OBSIDIAN_VAULT_PATH',
        '/Users/marcuswong/Documents/KnowledgeVault'
    )

    full_path = os.path.join(vault_path, folder, filename)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    try:
        fm_dict = json.loads(frontmatter)
        fm_yaml = yaml.dump(fm_dict, default_flow_style=False, allow_unicode=True)

        if mode == "create":
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(f"---\\n{fm_yaml}---\\n\\n{content}")
        elif mode == "append":
            with open(full_path, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                f.write(f"\\n\\n---\\n*Added: {timestamp}*\\n\\n{content}")

        return json.dumps({
            "status": "success",
            "path": full_path,
            "mode": mode,
            "filename": filename
        })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "path": full_path
        })
'''

UPDATE_INDEX_TOOL_SOURCE = '''
import json
import os
from datetime import datetime

def update_theme_index(theme: str, new_insight_file: str, insight_summary: str) -> str:
    """
    Updates the theme index file (MOC) with a new insight reference.

    Args:
        theme: Theme name to update index for.
        new_insight_file: Filename of the new insight to link (without .md).
        insight_summary: One-line summary for the index entry.

    Returns:
        JSON string confirming the update.
    """
    vault_path = os.environ.get(
        'OBSIDIAN_VAULT_PATH',
        '/Users/marcuswong/Documents/KnowledgeVault'
    )

    theme_folders = {
        "AI Infrastructure Moats": "01-AI-Infrastructure-Moats",
        "VC Pattern Recognition": "02-VC-Pattern-Recognition",
        "Enterprise AI Adoption": "03-Enterprise-AI-Adoption",
        "Agentic Systems Architecture": "04-Agentic-Systems",
    }

    folder = theme_folders.get(theme, "05-Cross-Theme-Synthesis")
    index_path = os.path.join(vault_path, folder, "_INDEX.md")

    try:
        date_str = datetime.now().strftime("%Y-%m-%d")
        entry = f"- [[{new_insight_file}]] - {insight_summary} ({date_str})\\n"

        with open(index_path, 'a', encoding='utf-8') as f:
            f.write(entry)

        return json.dumps({
            "status": "success",
            "index_path": index_path,
            "entry_added": entry.strip()
        })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
            "index_path": index_path
        })
'''
