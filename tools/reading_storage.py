"""Manual reading storage and retrieval tools for Letta agent."""

import json
from datetime import datetime
import re


def add_manual_reading(
    self,
    title: str,
    source_url: str,
    user_notes: str,
    key_points: str,
    themes: str
) -> str:
    """
    Store a reading with user-provided notes and key points directly to archival memory.

    Args:
        title: The title of the reading
        source_url: URL of the source article or resource
        user_notes: User's personal notes and reactions
        key_points: Comma-separated key points from the reading
        themes: Comma-separated themes this reading relates to

    Returns:
        JSON string with status and the generated reading_id
    """
    try:
        # Generate reading_id with timestamp and slug
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:40]
        reading_id = f"reading-{timestamp}-{slug}"

        # Parse comma-separated strings to lists
        key_points_list = [p.strip() for p in key_points.split(',') if p.strip()]
        themes_list = [t.strip() for t in themes.split(',') if t.strip()]

        # Create structured reading entry
        reading_entry = {
            "type": "manual_reading",
            "reading_id": reading_id,
            "title": title,
            "source_url": source_url,
            "date_added": datetime.now().isoformat(),
            "key_points": key_points_list,
            "user_notes": user_notes,
            "themes": themes_list
        }

        # Store to archival memory
        reading_json = json.dumps(reading_entry, indent=2)
        self.archival_memory_insert(reading_json)

        return json.dumps({
            "status": "success",
            "reading_id": reading_id,
            "message": f"Stored reading '{title}' with {len(key_points_list)} key points"
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })


def search_readings(self, query: str, limit: int = 10) -> str:
    """
    Search for readings in archival memory matching the query.

    Args:
        query: Search query to match against title, key_points, user_notes, and themes
        limit: Maximum number of results to return (default 10)

    Returns:
        JSON string with matching readings and their metadata
    """
    try:
        # Search archival memory
        results = self.archival_memory_search(query, page=0)

        # Parse and filter for manual_reading type
        readings = []
        for passage in results:
            try:
                data = json.loads(passage)
                if data.get("type") == "manual_reading":
                    readings.append({
                        "reading_id": data.get("reading_id"),
                        "title": data.get("title"),
                        "source_url": data.get("source_url"),
                        "date_added": data.get("date_added"),
                        "themes": data.get("themes", []),
                        "excerpt": data.get("user_notes", "")[:200]  # Preview of notes
                    })
                    if len(readings) >= limit:
                        break
            except json.JSONDecodeError:
                continue

        return json.dumps({
            "status": "success",
            "query": query,
            "count": len(readings),
            "results": readings
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })


def get_reading_by_id(self, reading_id: str) -> str:
    """
    Retrieve a specific reading by its ID from archival memory.

    Args:
        reading_id: The unique reading ID to retrieve

    Returns:
        JSON string with the complete reading data or error if not found
    """
    try:
        # Search for the specific reading_id
        results = self.archival_memory_search(reading_id, page=0)

        # Find the exact match
        for passage in results:
            try:
                data = json.loads(passage)
                if data.get("reading_id") == reading_id and data.get("type") == "manual_reading":
                    return json.dumps({
                        "status": "success",
                        "reading": data
                    }, indent=2)
            except json.JSONDecodeError:
                continue

        # Not found
        return json.dumps({
            "status": "not_found",
            "reading_id": reading_id,
            "message": f"No reading found with ID: {reading_id}"
        })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })


# Tool source codes for Letta registration
ADD_MANUAL_READING_TOOL_SOURCE = '''
import json
from datetime import datetime
import re

def add_manual_reading(
    self,
    title: str,
    source_url: str,
    user_notes: str,
    key_points: str,
    themes: str
) -> str:
    """
    Store a reading with user-provided notes and key points directly to archival memory.

    Args:
        title: The title of the reading
        source_url: URL of the source article or resource
        user_notes: User's personal notes and reactions
        key_points: Comma-separated key points from the reading
        themes: Comma-separated themes this reading relates to

    Returns:
        JSON string with status and the generated reading_id
    """
    try:
        # Generate reading_id with timestamp and slug
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:40]
        reading_id = f"reading-{timestamp}-{slug}"

        # Parse comma-separated strings to lists
        key_points_list = [p.strip() for p in key_points.split(',') if p.strip()]
        themes_list = [t.strip() for t in themes.split(',') if t.strip()]

        # Create structured reading entry
        reading_entry = {
            "type": "manual_reading",
            "reading_id": reading_id,
            "title": title,
            "source_url": source_url,
            "date_added": datetime.now().isoformat(),
            "key_points": key_points_list,
            "user_notes": user_notes,
            "themes": themes_list
        }

        # Store to archival memory
        reading_json = json.dumps(reading_entry, indent=2)
        self.archival_memory_insert(reading_json)

        return json.dumps({
            "status": "success",
            "reading_id": reading_id,
            "message": f"Stored reading '{title}' with {len(key_points_list)} key points"
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })
'''

SEARCH_READINGS_TOOL_SOURCE = '''
import json

def search_readings(self, query: str, limit: int = 10) -> str:
    """
    Search for readings in archival memory matching the query.

    Args:
        query: Search query to match against title, key_points, user_notes, and themes
        limit: Maximum number of results to return (default 10)

    Returns:
        JSON string with matching readings and their metadata
    """
    try:
        # Search archival memory
        results = self.archival_memory_search(query, page=0)

        # Parse and filter for manual_reading type
        readings = []
        for passage in results:
            try:
                data = json.loads(passage)
                if data.get("type") == "manual_reading":
                    readings.append({
                        "reading_id": data.get("reading_id"),
                        "title": data.get("title"),
                        "source_url": data.get("source_url"),
                        "date_added": data.get("date_added"),
                        "themes": data.get("themes", []),
                        "excerpt": data.get("user_notes", "")[:200]
                    })
                    if len(readings) >= limit:
                        break
            except json.JSONDecodeError:
                continue

        return json.dumps({
            "status": "success",
            "query": query,
            "count": len(readings),
            "results": readings
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })
'''

GET_READING_TOOL_SOURCE = '''
import json

def get_reading_by_id(self, reading_id: str) -> str:
    """
    Retrieve a specific reading by its ID from archival memory.

    Args:
        reading_id: The unique reading ID to retrieve

    Returns:
        JSON string with the complete reading data or error if not found
    """
    try:
        # Search for the specific reading_id
        results = self.archival_memory_search(reading_id, page=0)

        # Find the exact match
        for passage in results:
            try:
                data = json.loads(passage)
                if data.get("reading_id") == reading_id and data.get("type") == "manual_reading":
                    return json.dumps({
                        "status": "success",
                        "reading": data
                    }, indent=2)
            except json.JSONDecodeError:
                continue

        # Not found
        return json.dumps({
            "status": "not_found",
            "reading_id": reading_id,
            "message": f"No reading found with ID: {reading_id}"
        })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })
'''
