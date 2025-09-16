from __future__ import annotations
"""Wrapper for Tavily search API via langchain-community tool if available."""
from typing import List, Dict, Any
import os

try:
    from langchain_community.tools.tavily_search import TavilySearchResults
except Exception:  # pragma: no cover - optional dependency path
    TavilySearchResults = None  # type: ignore


def search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY not set in environment")
    if TavilySearchResults is None:
        raise RuntimeError("TavilySearchResults tool not available - ensure langchain-community installed")
    tool = TavilySearchResults(max_results=max_results)
    results = tool.run(query)
    if isinstance(results, list):
        return results
    return [results]


__all__ = ["search"]
