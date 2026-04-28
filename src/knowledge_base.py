"""
knowledge_base.py
Retrieves relevant music context from data/music_knowledge.json.

This is the second data source in the RAG pipeline. Before Gemini interprets
a user query, we look up matching entries from the knowledge base and inject
them into the prompt so Gemini has domain-specific guidance on genres, moods,
and energy ranges for common activities and feelings.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

_KB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "music_knowledge.json")
_KNOWLEDGE_BASE = None


def _load() -> list[dict]:
    global _KNOWLEDGE_BASE
    if _KNOWLEDGE_BASE is None:
        with open(_KB_PATH, encoding="utf-8") as f:
            _KNOWLEDGE_BASE = json.load(f)
        logger.debug("Loaded %d knowledge base entries", len(_KNOWLEDGE_BASE))
    return _KNOWLEDGE_BASE


def retrieve_context(query: str, top_k: int = 2) -> str:
    """
    Score each knowledge base entry by keyword overlap with the query,
    return the top_k entries formatted as plain-text context for prompt injection.
    Returns an empty string if no entries match.
    """
    query_lower = query.lower()
    scored = []

    for entry in _load():
        hits = sum(1 for kw in entry["keywords"] if kw in query_lower)
        if hits > 0:
            scored.append((hits, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [entry for _, entry in scored[:top_k]]

    if not top:
        logger.debug("No knowledge base entries matched query: %r", query)
        return ""

    matched_ids = [e["id"] for e in top]
    logger.info("Knowledge base matched entries: %s for query: %r", matched_ids, query)
    return "\n".join(e["context"] for e in top)
