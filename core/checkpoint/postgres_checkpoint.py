from langgraph.checkpoint.postgres import PostgresSaver
from sqlalchemy import create_engine
import os
import logging

logger = logging.getLogger(__name__)

def create_postgres_checkpoint():
    """Create a PostgreSQL checkpoint saver for LangGraph."""
    # Database configuration from environment variables
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "financial_agents")
    db_username = os.getenv("DB_USERNAME", "postgres")
    db_password = os.getenv("DB_PASSWORD", "password")
    
    # Create database URL
    database_url = f"postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    try:
        # Create SQLAlchemy engine
        engine = create_engine(database_url, pool_pre_ping=True)
        
        # Create the checkpoint saver
        checkpointer = PostgresSaver(engine)
        
        # Initialize the database schema
        checkpointer.setup()
        
        logger.info("PostgreSQL checkpoint saver created successfully")
        return checkpointer
        
    except Exception as e:
        logger.error(f"Failed to create PostgreSQL checkpoint: {e}")
        raise

# Global checkpoint instance
postgres_checkpoint = None

def get_postgres_checkpoint():
    """Get or create the PostgreSQL checkpoint instance."""
    global postgres_checkpoint
    if postgres_checkpoint is None:
        postgres_checkpoint = create_postgres_checkpoint()
    return postgres_checkpoint