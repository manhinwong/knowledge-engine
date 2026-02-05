"""PDF parsing tools for knowledge engine."""

import json
import os
import tempfile
from pathlib import Path
from typing import Optional

import requests
from pypdf import PdfReader


def extract_pdf_content(source: str, is_url: bool = False) -> str:
    """
    Extract text content and metadata from a PDF file.

    Args:
        source: Either a local file path or URL to a PDF
        is_url: If True, source is treated as a URL to download

    Returns:
        JSON string containing title, author, page count, and extracted text.
    """
    try:
        pdf_path = source

        # Download PDF if URL provided
        if is_url:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(source, headers=headers, timeout=60)
            response.raise_for_status()

            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(response.content)
                pdf_path = tmp.name

        # Extract text from PDF
        reader = PdfReader(pdf_path)

        # Extract metadata
        metadata = reader.metadata or {}
        title = metadata.get('/Title', None)
        author = metadata.get('/Author', None)
        subject = metadata.get('/Subject', None)

        # Extract text from all pages
        full_text = []
        page_count = len(reader.pages)

        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            if text.strip():
                full_text.append(f"--- Page {page_num} ---\n{text}")

        combined_text = "\n\n".join(full_text)

        # Clean up temp file if we downloaded it
        if is_url and pdf_path != source:
            try:
                os.unlink(pdf_path)
            except:
                pass

        # If no title in metadata, try to infer from filename or first page
        if not title:
            if is_url:
                title = source.split('/')[-1].replace('.pdf', '').replace('-', ' ').replace('_', ' ')
            else:
                title = Path(source).stem.replace('-', ' ').replace('_', ' ')

        return json.dumps({
            "status": "success",
            "source": source,
            "title": title,
            "author": author,
            "subject": subject,
            "page_count": page_count,
            "content": combined_text[:20000],  # Limit to avoid context overflow
            "word_count": len(combined_text.split()),
            "type": "pdf"
        }, indent=2)

    except requests.RequestException as e:
        return json.dumps({
            "status": "error",
            "source": source,
            "error": f"Download error: {str(e)}"
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "source": source,
            "error": f"PDF extraction error: {str(e)}"
        })
