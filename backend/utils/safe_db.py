"""
Database helper utilities for safe data access
"""

from typing import Any, Dict, List, Optional


def safe_get_first(data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Safely get the first item from a database query result

    Args:
        data: List of dictionaries from database query

    Returns:
        First item if exists, None otherwise
    """
    if data and len(data) > 0:
        return data[0]
    return None
