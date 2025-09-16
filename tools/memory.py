from __future__ import annotations
"""Memory layer that persists research insights into a vector store."""
from typing import List
from .vectorstore import VectorStore


class ResearchMemory:
    def __init__(self, collection: str = "research_insights"):
        self.vs = VectorStore(collection=collection)

    def remember_insights(self, insights: List[str]):
        if not insights:
            return []
        return self.vs.add_texts(insights, metadatas=[{"type": "research"} for _ in insights])

    def recall(self, query: str, k: int = 3):
        return self.vs.similarity_search(query, k=k)


__all__ = ["ResearchMemory"]
