#!/usr/bin/env python3
"""
Test script for manual reading storage and retrieval.

This validates the end-to-end workflow:
1. Add multiple readings with user notes
2. Search for them by keywords
3. Retrieve specific readings by ID
4. Verify all data is stored and retrieved correctly

Prerequisites:
- Letta server running: letta server
- Agent created with new tools: python setup_agent.py
- KNOWLEDGE_ENGINE_AGENT_ID environment variable set

Usage:
    python test_manual_readings.py
"""

import os
import sys
import time
from letta_client import Letta


def test_manual_readings():
    """Test the manual reading workflow."""
    # Setup
    base_url = os.environ.get("LETTA_BASE_URL", "http://localhost:8283")
    agent_id = os.environ.get("KNOWLEDGE_ENGINE_AGENT_ID")

    if not agent_id:
        print("Error: KNOWLEDGE_ENGINE_AGENT_ID not set")
        print("Run: python setup_agent.py")
        sys.exit(1)

    client = Letta(base_url=base_url)
    print(f"Connected to Letta at {base_url}")
    print(f"Using agent: {agent_id}\n")

    # Test 1: Add first reading
    print("=" * 60)
    print("TEST 1: Adding reading about RAG systems")
    print("=" * 60)

    response1 = client.agents.messages.create(
        agent_id=agent_id,
        messages=[{
            "role": "user",
            "content": """Add this manual reading using add_manual_reading:

Title: Contextual Retrieval for RAG
URL: https://www.anthropic.com/news/contextual-retrieval
User Notes: Anthropic's approach adds context to chunks before embedding. Reduces failed retrievals by 67%. Could be huge for enterprise RAG systems.
Key Points: Contextual embeddings improve retrieval accuracy, BM25 + semantic search hybrid works well, Reranking as post-processing step
Themes: AI Infrastructure Moats, Agentic Systems Architecture

Just respond with the reading_id that was generated."""
        }]
    )

    reading_id_1 = None
    for msg in response1.messages:
        if hasattr(msg, 'content') and msg.role == 'assistant':
            print(msg.content)
            # Extract reading_id from response
            if 'reading-' in msg.content:
                reading_id_1 = msg.content.strip().split('\n')[-1].strip()

    time.sleep(2)  # Give archival memory time to index

    # Test 2: Add second reading
    print("\n" + "=" * 60)
    print("TEST 2: Adding reading about VC pattern recognition")
    print("=" * 60)

    response2 = client.agents.messages.create(
        agent_id=agent_id,
        messages=[{
            "role": "user",
            "content": """Add this manual reading using add_manual_reading:

Title: Signals That Predict Breakout Startups
URL: https://www.nfx.com/post/network-effects-guide
User Notes: Network effects create winner-take-all dynamics. Need to identify them early in B2B SaaS. Look for viral loops and data network effects.
Key Points: 13 types of network effects, Data network effects undervalued, Viral growth compounds
Themes: VC Pattern Recognition, AI Infrastructure Moats

Just respond with the reading_id."""
        }]
    )

    reading_id_2 = None
    for msg in response2.messages:
        if hasattr(msg, 'content') and msg.role == 'assistant':
            print(msg.content)
            if 'reading-' in msg.content:
                reading_id_2 = msg.content.strip().split('\n')[-1].strip()

    time.sleep(2)

    # Test 3: Search for "RAG"
    print("\n" + "=" * 60)
    print("TEST 3: Searching for 'RAG'")
    print("=" * 60)

    response3 = client.agents.messages.create(
        agent_id=agent_id,
        messages=[{
            "role": "user",
            "content": """Search for readings using search_readings:
Query: RAG
Limit: 10

Display the results showing titles, themes, and excerpts from notes."""
        }]
    )

    for msg in response3.messages:
        if hasattr(msg, 'content') and msg.role == 'assistant':
            print(msg.content)

    time.sleep(2)

    # Test 4: Search for "network effects"
    print("\n" + "=" * 60)
    print("TEST 4: Searching for 'network effects'")
    print("=" * 60)

    response4 = client.agents.messages.create(
        agent_id=agent_id,
        messages=[{
            "role": "user",
            "content": """Search for readings using search_readings:
Query: network effects
Limit: 10

Display the results."""
        }]
    )

    for msg in response4.messages:
        if hasattr(msg, 'content') and msg.role == 'assistant':
            print(msg.content)

    # Test 5: Retrieve specific reading
    if reading_id_1:
        time.sleep(2)
        print("\n" + "=" * 60)
        print(f"TEST 5: Retrieving reading by ID: {reading_id_1}")
        print("=" * 60)

        response5 = client.agents.messages.create(
            agent_id=agent_id,
            messages=[{
                "role": "user",
                "content": f"""Retrieve reading using get_reading_by_id:
Reading ID: {reading_id_1}

Display the complete reading with ALL fields."""
            }]
        )

        for msg in response5.messages:
            if hasattr(msg, 'content') and msg.role == 'assistant':
                print(msg.content)

    print("\n" + "=" * 60)
    print("TESTS COMPLETE")
    print("=" * 60)
    print("\nVerify that:")
    print("- Both readings were added successfully")
    print("- Searches returned the expected readings")
    print("- User notes are visible in search results")
    print("- Get by ID returns complete reading data")


if __name__ == "__main__":
    try:
        test_manual_readings()
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
