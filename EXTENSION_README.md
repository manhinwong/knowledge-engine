# Knowledge Engine Browser Extension

Browser extension for capturing articles and PDFs to your Obsidian knowledge vault with one click.

## Installation

### 1. Start the Server

```bash
cd ~/Desktop/claude\ code/knowledge-engine
source venv/bin/activate
python3 server.py
```

Server will run on `http://localhost:8284`

### 2. Load Extension in Chrome

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right)
3. Click "Load unpacked"
4. Select the `extension/` folder:
   ```
   ~/Desktop/claude code/knowledge-engine/extension
   ```
5. Extension should appear in your toolbar

### 3. Load Extension in Firefox

1. Open Firefox and go to `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on"
3. Select any file in the `extension/` folder (e.g., `manifest.json`)
4. Extension will be loaded temporarily (until Firefox restarts)

## Usage

### Capture Web Articles

1. Browse to any article page
2. Click the Knowledge Engine extension icon
3. Click "Save Current Page"
4. Extension will:
   - Extract article content
   - Send to local server
   - Process with AI agent
   - Extract insights
   - Save to appropriate Obsidian theme folder
   - Update index files

### Upload PDFs

1. Click the Knowledge Engine extension icon
2. Click "Upload PDF"
3. Select a PDF file from your computer
4. Extension will:
   - Upload PDF to server
   - Extract text content
   - Process with AI agent
   - Save insights to Obsidian

## Features

- One-click article capture
- PDF upload and processing
- Automatic theme categorization
- Insight extraction
- Obsidian vault integration
- Recent saves history
- Server health monitoring

## Architecture

```
Browser Extension (popup.js)
    ↓
Content Script (content.js) - Extracts article HTML
    ↓
FastAPI Server (server.py) - Port 8284
    ↓
Knowledge Agent (agent.py) - Anthropic Claude SDK
    ↓
Tools:
  - fetch.py - Article fetching
  - pdf_parser.py - PDF extraction
  - obsidian.py - Vault operations
    ↓
Obsidian Vault (~/Desktop/Knowledge/)
```

## Endpoints

- `GET /health` - Check server status
- `GET /themes` - Get current themes and insights count
- `POST /process` - Process URL, HTML, or PDF
- `POST /upload-pdf` - Upload and process PDF file

## Settings

Click the extension icon to configure:
- **Server URL**: Default `http://localhost:8284`
- View recent saves (last 5)

## Troubleshooting

**Extension shows "Server offline":**
- Make sure server.py is running
- Check server URL in extension settings
- Verify server is on port 8284

**Article not saving:**
- Check server logs for errors
- Verify Obsidian vault path is correct
- Ensure ANTHROPIC_API_KEY is set in .env

**PDF upload fails:**
- Check PDF file is not corrupted
- Ensure file is under 50MB
- Check server has write permissions for temp files

## Development

**Reload extension after changes:**
- Chrome: Go to `chrome://extensions/` and click the refresh icon
- Firefox: Go to `about:debugging#/runtime/this-firefox` and click "Reload"

**View extension logs:**
- Right-click extension icon > "Inspect popup"
- Check Console tab for errors

**View server logs:**
- Check terminal where server.py is running
- Look for error messages and stack traces
