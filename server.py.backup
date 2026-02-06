#!/usr/bin/env python3
"""
FastAPI server for Knowledge Engine browser extension.
Provides REST API endpoints for processing articles and PDFs.
"""

import json
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from agent import KnowledgeAgent


app = FastAPI(title="Knowledge Engine API", version="1.0.0")

# Configure CORS for browser extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://*",
        "moz-extension://*",
        "http://localhost:*",
        "http://127.0.0.1:*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent
agent = KnowledgeAgent()


class ProcessRequest(BaseModel):
    """Request model for processing content."""
    type: str  # "url", "html", or "pdf"
    content: str  # URL, HTML string, or PDF URL
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

            prompt = f"""I have extracted the following article content:

{json.dumps(content_data, indent=2)}

Please process this article, extract insights, and save to the appropriate theme folder."""

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
async def upload_pdf(file: UploadFile = File(...)):
    """
    Handle PDF file upload and process through knowledge engine.

    Args:
        file: Uploaded PDF file

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
        prompt = f"Please extract and process this PDF file: {tmp_path}\n\nOriginal filename: {file.filename}"
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


def main():
    """Run the server."""
    print("Starting Knowledge Engine API server on http://localhost:8284")
    print("Press Ctrl+C to stop")
    uvicorn.run(app, host="127.0.0.1", port=8284, log_level="info")


if __name__ == "__main__":
    main()
