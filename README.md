# Knowledge Accumulation Engine

A Letta-powered agent that extracts unique insights from articles, connects them to learning themes, and outputs to an Obsidian vault.

## Quick Start

### 1. Setup Python Environment

```bash
cd ~/knowledge-engine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set API Keys

```bash
export ANTHROPIC_API_KEY=your_key_here
export OPENAI_API_KEY=your_key_here  # For embeddings
```

### 3. Database and Letta Server

The Letta server uses PostgreSQL and needs tables created once. **pgvector** is required; on Homebrew it only supports Postgres 17/18 (not 15).

**If you use Postgres 15:** upgrade to 17, then recreate the letta DB:

```bash
brew install postgresql@17
brew services stop postgresql@15   # if it was running
brew services start postgresql@17
```

**One-time setup:**

```bash
# Create letta role and database (no psql needed)
python scripts/setup_postgres_for_letta.py

# Create Letta tables (requires pgvector; Postgres 17/18 on Homebrew)
python scripts/init_letta_db.py
```

**Start the server** (loads `.env` so `LETTA_PG_URI` is used):

```bash
./run_server.sh
```

### 4. Create the Agent (in another terminal)

```bash
cd ~/knowledge-engine
source venv/bin/activate
python setup_agent.py
```

This will print an agent ID. Export it:

```bash
export KNOWLEDGE_ENGINE_AGENT_ID=<agent-id-from-setup>
```

### 5. Test

```bash
python cli.py themes
```

## CLI Commands

### Automatic Article Processing

```bash
# Process an article (auto-extracts insights)
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
```

### Manual Reading Entry (New)

```bash
# Add a reading with your own notes
python cli.py add "Article Title" "https://url.com" \
    --notes "Your thoughts and reactions" \
    --points "Key point 1" \
    --points "Key point 2" \
    --themes "AI Infrastructure Moats"

# Search for readings
python cli.py search "RAG systems"
python cli.py search "network effects" --limit 5

# Get a specific reading by ID
python cli.py get reading-20260127-contextual-retrieval
```

## Shell Alias (Optional)

Add to `~/.zshrc`:

```bash
alias ke="python ~/knowledge-engine/cli.py"
export KNOWLEDGE_ENGINE_AGENT_ID=<your-agent-id>
```

Then use: `ke process <url>`

## Learning Themes

1. **AI Infrastructure Moats** - What creates defensibility? Data flywheels? Network effects?
2. **VC Pattern Recognition** - Frameworks for evaluating startup defensibility
3. **Enterprise AI Adoption** - How context graphs/agents get adopted in orgs
4. **Agentic Systems Architecture** - MCP, state management, memory systems

## Obsidian Vault Structure

```
~/Documents/KnowledgeVault/
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

## How It Works

1. **Novelty Detection**: Before saving any insight, the agent searches its archival memory for similar concepts. Only genuinely novel insights (novelty_score > 0.5) are saved.

2. **Theme Mapping**: Each insight is mapped to relevant learning themes and connected via wikilinks.

3. **Compounding Knowledge**: The agent updates its `known_concepts_summary` after each article, building a personalized filter for what's truly new to you.

4. **Obsidian Integration**: Insights are saved as markdown files with YAML frontmatter, enabling Obsidian's graph view and backlink features.
