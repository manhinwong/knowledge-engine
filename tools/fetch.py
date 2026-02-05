"""Article fetching and parsing tools for Letta agent."""

import json
import requests
from readability import Document
from bs4 import BeautifulSoup


def fetch_and_parse_article(url: str) -> str:
    """
    Fetches a web article and extracts clean text content.

    Args:
        url: The URL of the article to fetch and parse.

    Returns:
        JSON string containing title, author, date, and clean article text.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        doc = Document(response.text)
        soup = BeautifulSoup(doc.summary(), 'html.parser')
        text = soup.get_text(separator='\n', strip=True)

        # Try to extract metadata
        full_soup = BeautifulSoup(response.text, 'html.parser')

        author = None
        author_meta = full_soup.find('meta', attrs={'name': 'author'})
        if author_meta:
            author = author_meta.get('content')

        date = None
        date_meta = full_soup.find('meta', attrs={'property': 'article:published_time'})
        if date_meta:
            date = date_meta.get('content')

        return json.dumps({
            "status": "success",
            "url": url,
            "title": doc.title(),
            "author": author,
            "published_date": date,
            "content": text[:15000],  # Limit to avoid context overflow
            "word_count": len(text.split())
        }, indent=2)

    except requests.RequestException as e:
        return json.dumps({
            "status": "error",
            "url": url,
            "error": str(e)
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "url": url,
            "error": f"Parsing error: {str(e)}"
        })


# Tool source code for Letta registration
FETCH_TOOL_SOURCE = '''
import json
import requests
from readability import Document
from bs4 import BeautifulSoup

def fetch_and_parse_article(url: str) -> str:
    """
    Fetches a web article and extracts clean text content.

    Args:
        url: The URL of the article to fetch and parse.

    Returns:
        JSON string containing title, author, date, and clean article text.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        doc = Document(response.text)
        soup = BeautifulSoup(doc.summary(), 'html.parser')
        text = soup.get_text(separator='\\n', strip=True)

        full_soup = BeautifulSoup(response.text, 'html.parser')

        author = None
        author_meta = full_soup.find('meta', attrs={'name': 'author'})
        if author_meta:
            author = author_meta.get('content')

        date = None
        date_meta = full_soup.find('meta', attrs={'property': 'article:published_time'})
        if date_meta:
            date = date_meta.get('content')

        return json.dumps({
            "status": "success",
            "url": url,
            "title": doc.title(),
            "author": author,
            "published_date": date,
            "content": text[:15000],
            "word_count": len(text.split())
        }, indent=2)

    except requests.RequestException as e:
        return json.dumps({
            "status": "error",
            "url": url,
            "error": str(e)
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "url": url,
            "error": f"Parsing error: {str(e)}"
        })
'''
