from __future__ import annotations
"""Simple Chroma vector store wrapper.

Abstracts basic add & similarity search operations. Assumes embeddings handled
externally (e.g., via OpenAIEmbeddings) to keep this module lean.
"""
from typing import List, Optional, Sequence, Any
import chromadb
from chromadb.utils import embedding_functions
import time, uuid
from config.config import settings


class VectorStore:
    def __init__(self, collection: str = "research_insights"):
        persist_dir = settings.vector_db_dir
        self.client = chromadb.PersistentClient(path=persist_dir)
        default_ef = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name=collection,
            embedding_function=default_ef,
        )

    def add_texts(self, texts: Sequence[str], metadatas: Optional[Sequence[dict]] = None) -> List[str]:
        ts = int(time.time() * 1000)
        ids = [f"doc_{ts}_{uuid.uuid4().hex[:8]}_{i}" for i, _ in enumerate(texts)]
        # Convert to list explicitly for chroma client compatibility
        self.collection.add(ids=list(ids), documents=list(texts), metadatas=list(metadatas) if metadatas else None)
        return ids

    def similarity_search(self, query: str, k: int = 3) -> List[dict[str, Any]]:
        res = self.collection.query(query_texts=[query], n_results=k)
        ids = res.get("ids") or []
        documents = res.get("documents") or []
        metadatas = res.get("metadatas") or []
        distances = res.get("distances") or []
        if not ids or not ids[0]:
            return []
        out: List[dict[str, Any]] = []
        for i, doc_id in enumerate(ids[0]):
            out.append({
                "id": doc_id,
                "document": documents[0][i] if documents and documents[0] else None,
                "metadata": metadatas[0][i] if metadatas and metadatas[0] else {},
                "distance": distances[0][i] if distances and distances[0] else None,
            })
        return out


__all__ = ["VectorStore"]
