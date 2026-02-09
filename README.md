# Knowledge Accumulation Engine

An AI-powered agent that extracts unique insights from articles, connects them to learning themes, and outputs to an Obsidian-style vault. Deployed on Fly.io.

## Quick Start

### Local Development

```bash
cd ~/knowledge-engine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Set your API key:

```bash
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY and OBSIDIAN_VAULT_PATH
```

Run the server:

```bash
python server.py
```

### Production (Fly.io)

The app is deployed at https://knowledge-engine.fly.dev

```bash
fly deploy
```

## Chrome Extension

The browser extension lets you save articles directly to the knowledge engine.

1. Go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked" and select the `extension/` folder
4. Set the server URL in the extension settings

## CLI Commands

```bash
# Process an article
python cli.py process "https://example.com/article"

# Get explanation of a concept
python cli.py explain "data flywheels"

# Check relevance before processing
python cli.py relevance "https://example.com/article"

# Find connections
python cli.py connect "context windows"

# Check if something is novel
python cli.py unique "RAG improves retrieval accuracy"

# Show theme status
python cli.py themes
python cli.py themes --theme "AI Infrastructure Moats"

# Generate synthesis
python cli.py synthesize "AI Infrastructure Moats"

# Add a reading with notes
python cli.py add "Article Title" "https://url.com" \
    --notes "Your thoughts" \
    --points "Key point 1" \
    --themes "AI Infrastructure Moats"

# Search readings
python cli.py search "RAG systems"

# Get a specific reading
python cli.py get reading-20260127-contextual-retrieval
```

## Learning Themes

1. **AI Infrastructure Moats** - What creates defensibility? Data flywheels? Network effects?
2. **VC Pattern Recognition** - Frameworks for evaluating startup defensibility
3. **Enterprise AI Adoption** - How context graphs/agents get adopted in orgs
4. **Agentic Systems Architecture** - MCP, state management, memory systems

## Architecture

- **Agent** (`agent.py`) — Anthropic SDK with tool calling for processing articles
- **Server** (`server.py`) — FastAPI REST API for the Chrome extension and dashboard
- **Dashboard** (`dashboard/`) — Web UI with knowledge graph visualization
- **Tools** (`tools/`) — Article fetching, PDF parsing, Obsidian vault operations
- **Extension** (`extension/`) — Chrome extension for saving articles

## Vault Structure

```
/data/vault/  (Fly.io) or ~/Documents/KnowledgeVault/ (local)
├── 01-AI-Infrastructure-Moats/
├── 02-VC-Pattern-Recognition/
├── 03-Enterprise-AI-Adoption/
├── 04-Agentic-Systems/
├── 05-Cross-Theme-Synthesis/
└── Sources/
```

Each theme folder contains:
- `_INDEX.md` - Map of Content linking all insights
- Individual insight files with frontmatter and wikilinks
