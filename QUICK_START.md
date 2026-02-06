# Knowledge Engine - Quick Start Guide

## What You've Built

A complete browser extension + API server system for capturing web articles and PDFs into your Obsidian knowledge vault with AI-powered insight extraction.

## File Structure

```
knowledge-engine/
├── server.py              # NEW - FastAPI server on port 8284
├── agent.py              # UPDATED - Added PDF tool support
├── tools/
│   ├── fetch.py          # Existing - Article fetching
│   ├── pdf_parser.py     # NEW - PDF extraction
│   ├── obsidian.py       # Existing - Vault operations
│   └── reading_storage.py
├── extension/            # NEW - Browser extension
│   ├── manifest.json     # Extension config (Manifest v3)
│   ├── popup.html        # Extension UI
│   ├── popup.js          # Frontend logic
│   ├── content.js        # Page content extraction
│   ├── background.js     # Background processing
│   └── icons/            # Extension icons (16, 48, 128px)
└── requirements.txt      # UPDATED - Added fastapi, uvicorn, pypdf
```

## Setup (One Time)

### 1. Install Dependencies

```bash
cd ~/Desktop/claude\ code/knowledge-engine
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Load Extension in Chrome

1. Open Chrome: `chrome://extensions/`
2. Enable "Developer mode" (top-right toggle)
3. Click "Load unpacked"
4. Navigate to and select:
   ```
   ~/Desktop/claude code/knowledge-engine/extension
   ```
5. Extension icon appears in toolbar

## Daily Usage

### Start the Server

Every time before using the extension:

```bash
cd ~/Desktop/claude\ code/knowledge-engine
source venv/bin/activate
python3 server.py
```

Leave this terminal running. You'll see:
```
Starting Knowledge Engine API server on http://localhost:8284
Press Ctrl+C to stop
```

### Capture Articles

1. Browse to any article (Medium, blog, news site, etc.)
2. Click Knowledge Engine extension icon
3. Click "Save Current Page"
4. Wait for "Saved successfully!" message
5. Check your Obsidian vault - new file created in appropriate theme folder

### Process PDFs

1. Click Knowledge Engine extension icon
2. Click "Upload PDF"
3. Select PDF file
4. Wait for "PDF processed successfully!"
5. Check Obsidian vault for extracted insights

### Stop the Server

When done:
```bash
# In the server terminal, press Ctrl+C
```

## What Happens Behind the Scenes

1. **Extension** extracts article content or PDF
2. **Server** receives content via HTTP POST
3. **Agent** processes with Claude Sonnet 4.5:
   - Extracts unique insights
   - Categorizes by theme
   - Generates structured notes
4. **Obsidian Tool** saves to vault:
   - Creates markdown file with frontmatter
   - Updates theme index (_INDEX.md)
   - Tracks concepts in agent memory

## Server Endpoints

Test directly with curl:

```bash
# Health check
curl http://localhost:8284/health

# Get themes
curl http://localhost:8284/themes

# Process URL
curl -X POST http://localhost:8284/process \
  -H "Content-Type: application/json" \
  -d '{"type": "url", "content": "https://example.com/article"}'

# Process HTML
curl -X POST http://localhost:8284/process \
  -H "Content-Type: application/json" \
  -d '{"type": "html", "content": "<article>...</article>", "metadata": {"title": "Test", "url": "http://test.com"}}'
```

## Verification Checklist

- [ ] Server starts without errors
- [ ] Health endpoint returns `{"status": "healthy"}`
- [ ] Extension loads in Chrome without errors
- [ ] Extension icon shows green dot (server online)
- [ ] Can save an article from any website
- [ ] Can upload and process a PDF
- [ ] Files appear in Obsidian vault
- [ ] Index files are updated

## Tips

- **Server must be running** before using extension
- Extension shows server status (green/red dot)
- Recent saves are cached (last 10 in extension)
- Agent memory persists across sessions
- PDFs are temporarily stored during processing then deleted
- Content is limited to 15-20k chars to avoid API limits

## Next Steps

1. Try capturing your first article
2. Upload a PDF (research paper, class notes, etc.)
3. Check your Obsidian vault to see the results
4. Review the structured insights extracted by the AI

## Troubleshooting

**"Server offline" in extension:**
```bash
# Make sure server is running:
cd ~/Desktop/claude\ code/knowledge-engine
source venv/bin/activate
python3 server.py
```

**Import errors when starting server:**
```bash
# Reinstall dependencies:
pip install -r requirements.txt
```

**Extension not appearing in Chrome:**
- Refresh the extensions page
- Check for errors in the extension details
- Try removing and re-adding the extension

**Articles not saving:**
- Check server terminal for error logs
- Verify ANTHROPIC_API_KEY in .env file
- Ensure Obsidian vault path exists
