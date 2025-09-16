from typing import Dict, List, Any
from sqlalchemy.orm import Session
from core.db.connection import get_db
from core.db.models import AgentMemory
import logging

logger = logging.getLogger(__name__)

class SimpleMemory:
    """Simple persistent memory store using PostgreSQL (no vectors)."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
    
    def add_memory(self, situation: str, recommendation: str) -> bool:
        """Add a new memory to the persistent store."""
        try:
            db = next(get_db())
            memory = AgentMemory(
                agent_name=self.agent_name,
                situation=situation,
                recommendation=recommendation
            )
            db.add(memory)
            db.commit()
            
            logger.info(f"Memory added successfully for agent {self.agent_name}")
            return True
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            return False
    
    def get_recent_memories(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent memories for this agent."""
        try:
            db = next(get_db())
            memories = db.query(AgentMemory).filter(
                AgentMemory.agent_name == self.agent_name
            ).order_by(AgentMemory.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "situation": memory.situation,
                    "recommendation": memory.recommendation,
                    "created_at": memory.created_at.isoformat()
                }
                for memory in memories
            ]
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []
    
    def get_all_memories(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all memories for this agent."""
        try:
            db = next(get_db())
            memories = db.query(AgentMemory).filter(
                AgentMemory.agent_name == self.agent_name
            ).order_by(AgentMemory.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "situation": memory.situation,
                    "recommendation": memory.recommendation,
                    "created_at": memory.created_at.isoformat()
                }
                for memory in memories
            ]
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []
    
    def clear_memories(self) -> bool:
        """Clear all memories for this agent."""
        try:
            db = next(get_db())
            db.query(AgentMemory).filter(AgentMemory.agent_name == self.agent_name).delete()
            db.commit()
            
            logger.info(f"Cleared all memories for agent {self.agent_name}")
            return True
        except Exception as e:
            logger.error(f"Error clearing memories: {e}")
            return False