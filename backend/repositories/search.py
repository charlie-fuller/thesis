"""Repository for unified vector search.

Wraps vec_client to provide search across multiple collections.
"""

import vec_client as vec


def search_all(query: str, *, collections: list[str] | None = None,
               limit: int = 5) -> list[dict]:
    """Search across multiple vector collections and return top results by similarity."""
    targets = collections or ["document_chunks", "help_chunks", "disco_document_chunks"]
    results = []
    for coll in targets:
        results.extend(vec.search(coll, query, limit=limit))
    results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
    return results[:limit]


def search_documents(query: str, *, limit: int = 5) -> list[dict]:
    """Search document chunks."""
    return vec.search("document_chunks", query, limit=limit)


def search_help(query: str, *, limit: int = 5) -> list[dict]:
    """Search help chunks."""
    return vec.search("help_chunks", query, limit=limit)


def search_disco(query: str, *, limit: int = 5) -> list[dict]:
    """Search DISCO document chunks."""
    return vec.search("disco_document_chunks", query, limit=limit)
