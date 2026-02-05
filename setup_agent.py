#!/usr/bin/env python3
"""
Setup script to create the Knowledge Engine Letta agent.

Run this after starting the Letta server:
    letta server

Then run:
    python setup_agent.py

This will create the agent and print the AGENT_ID to set in your environment.
"""

import os
import sys
from pathlib import Path

from letta_client import Letta

# Tool source codes
from tools.fetch import FETCH_TOOL_SOURCE
from tools.obsidian import SAVE_OBSIDIAN_TOOL_SOURCE, UPDATE_INDEX_TOOL_SOURCE
from tools.reading_storage import (
    ADD_MANUAL_READING_TOOL_SOURCE,
    SEARCH_READINGS_TOOL_SOURCE,
    GET_READING_TOOL_SOURCE
)

# Load system prompt
PROMPT_PATH = Path(__file__).parent / "prompts" / "system_prompt.txt"
with open(PROMPT_PATH, "r") as f:
    SYSTEM_PROMPT = f.read()

# Memory block contents
USER_PROFILE = """USER: Marcus Wong
ROLE: VC/AI Investor
LEARNING FOCUS: Building pattern recognition for early-stage AI infrastructure deals
KNOWLEDGE LEVEL: Intermediate ML/AI, Strong software engineering background
PREFERRED DEPTH: Technical but connected to business implications
"""

ACTIVE_THEMES = """THEME 1: AI Infrastructure Moats
- Key questions: What creates defensibility? Data flywheels? Network effects?
- Known frameworks: Gradient Ventures moat taxonomy, a16z infrastructure stack

THEME 2: VC Pattern Recognition
- Key questions: What signals predict breakout? Team vs market vs product?
- Known frameworks: PMF indicators, founder-market fit criteria

THEME 3: Enterprise AI Adoption
- Key questions: Build vs buy? Integration patterns? Change management?
- Known frameworks: Crossing the Chasm, Technology Adoption Lifecycle

THEME 4: Agentic Systems Architecture
- Key questions: Memory patterns? Tool use? Multi-agent coordination?
- Known frameworks: ReAct, MemGPT/Letta, AutoGPT limitations
"""

KNOWN_CONCEPTS_SUMMARY = """HIGH-FREQUENCY CONCEPTS (skip unless new angle):
- RAG basics, vector databases, embeddings fundamentals
- Transformer architecture basics, attention mechanisms
- Prompt engineering 101, few-shot learning
- Basic VC terminology (seed, Series A, term sheets)
- LLM scaling laws, chinchilla optimal

RECENTLY LEARNED (last 7 days):
- (none yet - update after processing articles)

CONCEPT COUNT: 0 insights in archival memory
"""

OBSIDIAN_CONFIG = """VAULT_PATH: /Users/marcuswong/Documents/KnowledgeVault
THEME_FOLDERS:
  - 01-AI-Infrastructure-Moats/
  - 02-VC-Pattern-Recognition/
  - 03-Enterprise-AI-Adoption/
  - 04-Agentic-Systems/
  - 05-Cross-Theme-Synthesis/
NAMING: YYYY-MM-DD-slug-title.md
"""


def main():
    # Connect to local Letta server
    base_url = os.environ.get("LETTA_BASE_URL", "http://localhost:8283")
    client = Letta(base_url=base_url)

    print(f"Connected to Letta server at {base_url}")

    # Check if agent already exists
    existing_agents = client.agents.list()
    for agent in existing_agents:
        if agent.name == "knowledge-engine":
            print(f"\nAgent 'knowledge-engine' already exists!")
            print(f"AGENT_ID: {agent.id}")
            print(f"\nTo use: export KNOWLEDGE_ENGINE_AGENT_ID={agent.id}")
            return agent.id

    # Create custom tools
    print("\nCreating custom tools...")

    tools = []

    # Fetch tool
    fetch_tool = client.tools.create(source_code=FETCH_TOOL_SOURCE)
    tools.append(fetch_tool.name)
    print(f"  Created: {fetch_tool.name}")

    # Save to Obsidian tool
    save_tool = client.tools.create(source_code=SAVE_OBSIDIAN_TOOL_SOURCE)
    tools.append(save_tool.name)
    print(f"  Created: {save_tool.name}")

    # Update index tool
    index_tool = client.tools.create(source_code=UPDATE_INDEX_TOOL_SOURCE)
    tools.append(index_tool.name)
    print(f"  Created: {index_tool.name}")

    # Add manual reading tool
    add_reading_tool = client.tools.create(source_code=ADD_MANUAL_READING_TOOL_SOURCE)
    tools.append(add_reading_tool.name)
    print(f"  Created: {add_reading_tool.name}")

    # Search readings tool
    search_tool = client.tools.create(source_code=SEARCH_READINGS_TOOL_SOURCE)
    tools.append(search_tool.name)
    print(f"  Created: {search_tool.name}")

    # Get reading tool
    get_tool = client.tools.create(source_code=GET_READING_TOOL_SOURCE)
    tools.append(get_tool.name)
    print(f"  Created: {get_tool.name}")

    # Create the agent
    print("\nCreating agent...")

    agent = client.agents.create(
        name="knowledge-engine",
        model="openai/gpt-4o",
        embedding="openai/text-embedding-3-small",
        memory_blocks=[
            {"label": "user_profile", "value": USER_PROFILE},
            {"label": "active_themes", "value": ACTIVE_THEMES},
            {"label": "known_concepts_summary", "value": KNOWN_CONCEPTS_SUMMARY},
            {"label": "obsidian_config", "value": OBSIDIAN_CONFIG},
        ],
        tools=tools,
        system=SYSTEM_PROMPT,
        tool_exec_environment_variables={
            "OBSIDIAN_VAULT_PATH": "/Users/marcuswong/Documents/KnowledgeVault"
        }
    )

    print(f"\nAgent created successfully!")
    print(f"Name: {agent.name}")
    print(f"ID: {agent.id}")
    print(f"Model: {agent.model}")
    print(f"Tools: {tools}")

    print(f"\n{'='*60}")
    print("SETUP COMPLETE!")
    print(f"{'='*60}")
    print(f"\nAdd this to your shell config (~/.zshrc):")
    print(f"  export KNOWLEDGE_ENGINE_AGENT_ID={agent.id}")
    print(f"\nOr run:")
    print(f"  export KNOWLEDGE_ENGINE_AGENT_ID={agent.id}")
    print(f"\nThen test with:")
    print(f"  python cli.py themes")

    return agent.id


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure the Letta server is running:")
        print("  letta server")
        sys.exit(1)
