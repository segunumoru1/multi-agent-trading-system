import chromadb
from openai import OpenAI
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class FinancialSituationMemory:
    def __init__(self, name: str, config: Dict[str, Any]):
        self.embedding_model = "text-embedding-3-small"
        self.client = OpenAI(base_url=config.get("backend_url", "https://api.openai.com/v1"))
        self.chroma_client = chromadb.Client()
        self.situation_collection = self.chroma_client.create_collection(name=name)

    def get_embedding(self, text: str) -> List[float]:
        try:
            response = self.client.embeddings.create(model=self.embedding_model, input=text)
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return []

    def add_situations(self, situations_and_advice: List[tuple[str, str]]):
        if not situations_and_advice:
            return
        try:
            offset = self.situation_collection.count()
            ids = [str(offset + i) for i, _ in enumerate(situations_and_advice)]
            situations = [s for s, r in situations_and_advice]
            recommendations = [r for s, r in situations_and_advice]
            embeddings = [self.get_embedding(s) for s in situations]
            self.situation_collection.add(
                documents=situations,
                metadatas=[{"recommendation": rec} for rec in recommendations],
                embeddings=embeddings,
                ids=ids,
            )
        except Exception as e:
            logger.error(f"Error adding situations to memory: {e}")

    def get_memories(self, current_situation: str, n_matches: int = 1) -> List[Dict[str, str]]:
        if self.situation_collection.count() == 0:
            return []
        try:
            query_embedding = self.get_embedding(current_situation)
            results = self.situation_collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_matches, self.situation_collection.count()),
                include=["metadatas"],
            )
            return [{'recommendation': meta['recommendation']} for meta in results['metadatas'][0]]
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []