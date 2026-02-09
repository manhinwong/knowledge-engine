#!/usr/bin/env python3
"""
FastAPI server for Knowledge Engine browser extension.
Provides REST API endpoints for processing articles and PDFs.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from agent import KnowledgeAgent
from fastapi.staticfiles import StaticFiles
from dashboard.routes import router as dashboard_router


app = FastAPI(title="Knowledge Engine API", version="1.0.0")

# Configure CORS for browser extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://*",
        "moz-extension://*",
        "http://localhost:*",
        "http://127.0.0.1:*",
        "https://knowledge-engine.fly.dev",
        "https://*.fly.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount static files for dashboard
static_path = Path(__file__).parent / "dashboard" / "static"
if static_path.exists():
    app.mount("/dashboard/static", StaticFiles(directory=str(static_path)), name="static")

# Mount dashboard routes
app.include_router(dashboard_router)

# Initialize agent
agent = KnowledgeAgent()


class ProcessRequest(BaseModel):
    """Request model for processing content."""
    type: str  # "url", "html", or "pdf"
    content: str  # URL, HTML string, or PDF URL
    theme: Optional[str] = None  # Theme to save to
    metadata: Optional[dict] = None


class ProcessResponse(BaseModel):
    """Response model for processing requests."""
    status: str
    message: str
    insights_count: Optional[int] = None
    file_path: Optional[str] = None


@app.get("/health")
async def health_check():
    """Health check endpoint for extension to verify server is running."""
    return {
        "status": "healthy",
        "service": "knowledge-engine",
        "version": "1.0.0"
    }


@app.get("/themes")
async def get_themes():
    """Get current themes and status."""
    try:
        response = agent.send_message("List all themes with their insight counts")
        return {
            "status": "success",
            "themes": agent.state["memory"]["active_themes"],
            "total_concepts": agent.state["memory"]["known_concepts_count"],
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process", response_model=ProcessResponse)
async def process_content(request: ProcessRequest):
    """
    Process content (URL, HTML, or PDF) through the knowledge engine.

    Args:
        request: ProcessRequest with type and content

    Returns:
        ProcessResponse with status and results
    """
    try:
        if request.type == "url":
            # Process URL directly
            prompt = f"Please fetch and process this article: {request.content}"
            response = agent.send_message(prompt)

        elif request.type == "html":
            # Process provided HTML content
            metadata = request.metadata or {}
            title = metadata.get("title", "Untitled Article")
            url = metadata.get("url", "unknown")

            # Create structured content for agent
            content_data = {
                "status": "success",
                "url": url,
                "title": title,
                "author": metadata.get("author"),
                "published_date": metadata.get("date"),
                "content": request.content[:15000],
                "word_count": len(request.content.split())
            }

            theme_instruction = f" Save to the '{request.theme}' theme." if request.theme else " Determine the most appropriate theme and save there."

            prompt = f"""I have extracted the following article content:

{json.dumps(content_data, indent=2)}

Please process this article, extract insights, and save to the appropriate theme folder.{theme_instruction}"""

            response = agent.send_message(prompt)

        elif request.type == "pdf":
            # Process PDF URL
            prompt = f"Please extract and process this PDF: {request.content}"
            response = agent.send_message(prompt)

        else:
            raise HTTPException(status_code=400, detail=f"Invalid type: {request.type}")

        return ProcessResponse(
            status="success",
            message=response,
            insights_count=None,  # Could parse from response if needed
            file_path=None  # Could extract from agent state if needed
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-pdf", response_model=ProcessResponse)
async def upload_pdf(file: UploadFile = File(...), theme: Optional[str] = Form(None)):
    """
    Handle PDF file upload and process through knowledge engine.

    Args:
        file: Uploaded PDF file
        theme: Optional theme to save to

    Returns:
        ProcessResponse with status and results
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")

        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Process PDF with agent
        theme_instruction = f" Save to the '{theme}' theme." if theme else " Determine the most appropriate theme and save there."
        prompt = f"Please extract and process this PDF file: {tmp_path}\n\nOriginal filename: {file.filename}{theme_instruction}"
        response = agent.send_message(prompt)

        # Clean up temp file
        try:
            Path(tmp_path).unlink()
        except:
            pass

        return ProcessResponse(
            status="success",
            message=response,
            insights_count=None,
            file_path=None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CreateThemeRequest(BaseModel):
    """Request model for creating a new theme."""
    theme_name: str


@app.post("/create-theme", response_model=ProcessResponse)
async def create_theme(request: CreateThemeRequest):
    """
    Create a new theme folder in the vault.

    Args:
        request: CreateThemeRequest with theme_name

    Returns:
        ProcessResponse with status
    """
    try:
        from pathlib import Path
        from dashboard.vault_parser import VaultParser

        theme_name = request.theme_name.strip()
        if not theme_name:
            raise HTTPException(status_code=400, detail="Theme name cannot be empty")

        # Create theme folder
        vault_path = Path(os.environ.get('OBSIDIAN_VAULT_PATH', '/data/vault'))

        # Find next available number
        existing_dirs = [d.name for d in vault_path.iterdir() if d.is_dir()]
        max_num = 0
        for dir_name in existing_dirs:
            if dir_name[0].isdigit():
                try:
                    num = int(dir_name.split('-')[0])
                    max_num = max(max_num, num)
                except:
                    pass

        next_num = max_num + 1
        theme_folder_name = f"{next_num:02d}-{theme_name.replace(' ', '-')}"
        theme_path = vault_path / theme_folder_name

        if theme_path.exists():
            raise HTTPException(status_code=400, detail=f"Theme folder already exists: {theme_folder_name}")

        # Create folder
        theme_path.mkdir(parents=True, exist_ok=True)

        # Create _INDEX.md for the new theme
        index_content = f"""---
insight_count: 0
last_updated: '{Path(vault_path).name}'
theme: {theme_name}
type: index
---

# {theme_name} - Index

## Overview
New theme for organizing insights about {theme_name.lower()}.

---

## Recent Insights

No insights yet.

---

## Key Concepts

(To be populated as you add insights)

---

## Related Themes

"""

        index_path = theme_path / "_INDEX.md"
        index_path.write_text(index_content)

        # Refresh vault parser cache
        parser = VaultParser(str(vault_path))
        parser.refresh()

        return ProcessResponse(
            status="success",
            message=f"Theme '{theme_name}' created successfully in folder {theme_folder_name}",
            file_path=str(theme_path)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Run the server."""
    port = int(os.environ.get("PORT", 8284))
    host = "0.0.0.0"  # Listen on all interfaces for Railway/production
    print(f"Starting Knowledge Engine API server on http://0.0.0.0:{port}")
    print("Press Ctrl+C to stop")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
