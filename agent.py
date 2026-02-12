#!/usr/bin/env python3
"""
Knowledge Engine agent using Anthropic SDK with tool calling.
"""

import json
import os
from pathlib import Path
from typing import Any

import anthropic
from dotenv import load_dotenv

load_dotenv()

# Load system prompt
PROMPT_PATH = Path(__file__).parent / "prompts" / "system_prompt.txt"
with open(PROMPT_PATH, "r") as f:
    SYSTEM_PROMPT = f.read()

# State file
_state_dir = Path(os.environ.get("KNOWLEDGE_ENGINE_STATE_DIR", str(Path.home() / ".knowledge-engine")))
_state_dir.mkdir(parents=True, exist_ok=True)
STATE_FILE = _state_dir / "state.json"


class KnowledgeAgent:
    """Simple agent using Anthropic SDK with tool calling."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-sonnet-4-5-20250929"
        self.state = self._load_state()
        self.tools = self._define_tools()

    def _load_state(self) -> dict:
        """Load agent state from disk."""
        if STATE_FILE.exists():
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        return {
            "messages": [],
            "memory": {
                "user_profile": "Marcus Wong, VC/AI Investor",
                "active_themes": ["AI Infrastructure Moats", "VC Pattern Recognition",
                                 "Enterprise AI Adoption", "Startup Relationships", "ECON 157"],
                "known_concepts_count": 0,
                "readings": []
            }
        }

    def _save_state(self):
        """Save agent state to disk."""
        with open(STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=2)

    def _define_tools(self) -> list[dict]:
        """Define available tools for the agent."""
        return [
            {
                "name": "fetch_and_parse_article",
                "description": "Fetch and parse an article from a URL, returning clean markdown content",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL of the article to fetch"}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "extract_pdf",
                "description": "Extract text and metadata from a PDF file or URL",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "source": {"type": "string", "description": "Local file path or URL to PDF"},
                        "is_url": {"type": "boolean", "description": "True if source is a URL, False if local path", "default": False}
                    },
                    "required": ["source"]
                }
            },
            {
                "name": "save_to_obsidian",
                "description": "Save processed insights to Obsidian vault",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Markdown content (without frontmatter)"},
                        "filename": {"type": "string", "description": "Filename like '2026-02-04-trolley-problem.md'"},
                        "folder": {"type": "string", "description": "Theme folder (e.g., '03-Enterprise-AI-Adoption')"},
                        "frontmatter": {"type": "string", "description": "JSON string of frontmatter metadata"},
                        "mode": {"type": "string", "description": "Either 'create' or 'append'", "enum": ["create", "append"]}
                    },
                    "required": ["content", "filename", "folder", "frontmatter"]
                }
            },
            {
                "name": "search_readings",
                "description": "Search through saved readings by title or URL",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "search_vault",
                "description": "Search your Obsidian vault for insights by meaning (semantic) or keyword. Use this to ground explain, connect, and synthesize in actual saved notes. Returns insight id, title, theme, relevance score, and a short snippet.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query to find relevant vault insights"},
                        "theme": {"type": "string", "description": "Optional theme to filter results"},
                        "limit": {"type": "integer", "description": "Max results to return (default 15)"}
                    },
                    "required": ["query"]
                }
            }
        ]

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool and return the result."""
        if tool_name == "fetch_and_parse_article":
            from tools.fetch import fetch_and_parse_article
            return fetch_and_parse_article(tool_input["url"])

        elif tool_name == "extract_pdf":
            from tools.pdf_parser import extract_pdf_content
            return extract_pdf_content(
                source=tool_input["source"],
                is_url=tool_input.get("is_url", False)
            )

        elif tool_name == "save_to_obsidian":
            from tools.obsidian import save_to_obsidian
            return save_to_obsidian(
                content=tool_input["content"],
                filename=tool_input["filename"],
                folder=tool_input["folder"],
                frontmatter=tool_input["frontmatter"],
                mode=tool_input.get("mode", "create")
            )

        elif tool_name == "search_readings":
            readings = self.state["memory"]["readings"]
            query = tool_input["query"].lower()
            matches = [r for r in readings if query in r.get("title", "").lower()
                      or query in r.get("url", "").lower()]
            return json.dumps(matches, indent=2)

        elif tool_name == "search_vault":
            return self._search_vault(tool_input)

        return f"Unknown tool: {tool_name}"

    def _search_vault(self, tool_input: dict) -> str:
        """Search Obsidian vault using semantic or keyword search."""
        vault_path = os.environ.get("OBSIDIAN_VAULT_PATH")
        if not vault_path:
            return "OBSIDIAN_VAULT_PATH is not set; cannot search vault."

        from dashboard.vault_parser import VaultParser
        from dashboard.embedding_index import index_status, search_semantic

        query = tool_input["query"]
        theme = tool_input.get("theme")
        limit = tool_input.get("limit", 15)

        parser = VaultParser(vault_path)
        status = index_status(parser)

        if status.get("built"):
            results = search_semantic(parser, query, theme=theme, limit=limit)
        else:
            raw = parser.search(query, theme=theme)[:limit]
            results = []
            for item in raw:
                detail = parser.get_insight_detail(item["id"])
                snippet = ""
                if detail:
                    content = detail.get("content", "")
                    lines = [l for l in content.split("\n") if l.strip() and not l.startswith("#")]
                    snippet = " ".join(lines)[:160].strip()
                    if len(" ".join(lines)) > 160:
                        snippet += "..."
                results.append({
                    "id": item["id"],
                    "label": item.get("label", item["id"]),
                    "theme": item.get("theme", "Other"),
                    "score": None,
                    "snippet": snippet
                })

        # Add content_excerpt for top 3 results
        for r in results[:3]:
            detail = parser.get_insight_detail(r["id"])
            if detail:
                content = detail.get("content", "")
                lines = [l for l in content.split("\n") if l.strip()]
                excerpt = " ".join(lines)[:600].strip()
                if len(" ".join(lines)) > 600:
                    excerpt += "..."
                r["content_excerpt"] = excerpt

        return json.dumps(results, indent=2)

    def send_message(self, user_message: str) -> str:
        """Send a message to the agent and get response."""
        # Add user message to history
        self.state["messages"].append({
            "role": "user",
            "content": user_message
        })

        max_iterations = 5
        final_text = []

        for iteration in range(max_iterations):
            # Call Claude with tools
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT + f"\n\n# Agent Memory\n{json.dumps(self.state['memory'], indent=2)}",
                messages=self.state["messages"],
                tools=self.tools
            )

            # Add assistant message to history
            assistant_content = []
            has_tool_use = False

            for block in response.content:
                if block.type == "text":
                    final_text.append(block.text)
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    has_tool_use = True
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })

            self.state["messages"].append({
                "role": "assistant",
                "content": assistant_content
            })

            # If no tool use, we're done
            if not has_tool_use:
                break

            # Execute tools and add results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = self._execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            # Add tool results as user message
            self.state["messages"].append({
                "role": "user",
                "content": tool_results
            })

        self._save_state()
        return "\n".join(final_text)
