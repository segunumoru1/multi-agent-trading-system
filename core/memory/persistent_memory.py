import numpy as np
from typing import Dict, List, Tuple, Any
from sqlalchemy.orm import Session
from core.db.connection import get_db
from core.db.models import AgentMemory
import uuid
from openai import OpenAI
import os
from core.secrets import get_secret

class PersistentMemory:
    """Persistent vector memory store using PostgreSQL + pgvector."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.client = OpenAI(api_key=get_secret("OPENAI_API_KEY"))
        self.embedding_model = "text-embedding-3-small"
    
    def get_embedding(self, text: str) -> List[float]:
        """Get an embedding vector for the given text."""
        response = self.client.embeddings.create(model=self.embedding_model, input=text)
        return response.data[0].embedding
    
    def add_memory(self, situation: str, recommendation: str) -> bool:
        """Add a new memory to the persistent store."""
        embedding_vector = self.get_embedding(situation)
        embedding_key = str(uuid.uuid4())
        
        try:
            db = next(get_db())
            memory = AgentMemory(
                agent_name=self.agent_name,
                embedding_key=embedding_key,
                situation=situation,
                recommendation=recommendation
            )
            db.add(memory)
            db.commit()
            
            # Store the embedding vector in pgvector (requires pgvector extension)
            # This would be done with a raw SQL query to insert the vector
            conn = db.connection().connection
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO embeddings (key, vector) VALUES (%s, %s)",
                (embedding_key, embedding_vector)
            )
            conn.commit()
            
            return True
        except Exception as e:
            print(f"Error adding memory: {e}")
            return False
    
    def get_similar_memories(self, situation: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar memories based on vector similarity."""
        query_embedding = self.get_embedding(situation)
        
        try:
            db = next(get_db())
            conn = db.connection().connection
            cursor = conn.cursor()
            
            # Perform a similarity search with pgvector
            cursor.execute("""
                SELECT m.* FROM agent_memories m
                JOIN embeddings e ON m.embedding_key = e.key
                WHERE m.agent_name = %s
                ORDER BY e.vector <-> %s
                LIMIT %s
            """, (self.agent_name, query_embedding, limit))
            
            results = cursor.fetchall()
            return [
                {
                    "situation": row["situation"],
                    "recommendation": row["recommendation"],
                    "created_at": row["created_at"].isoformat()
                }
                for row in results
            ]
        except Exception as e:
            print(f"Error retrieving memories: {e}")
            return []