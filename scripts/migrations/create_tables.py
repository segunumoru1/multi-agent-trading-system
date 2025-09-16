import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.db.connection import engine, Base
from core.db.models import AgentMemory, TradeRecord, Portfolio, Position

def create_tables():
    """Create all database tables if they don't exist."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

def create_pgvector_extension():
    """Create the pgvector extension if it doesn't exist."""
    import psycopg2
    from core.db.connection import DB_HOST, DB_PORT, DB_NAME, DB_USERNAME, DB_PASSWORD
    
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USERNAME,
        password=DB_PASSWORD
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    try:
        print("Creating pgvector extension...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("Creating embeddings table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS embeddings (
            id SERIAL PRIMARY KEY,
            key VARCHAR(255) UNIQUE NOT NULL,
            vector vector(1536)
        );
        """)
        print("Creating index on embeddings...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings USING hnsw (vector vector_l2_ops);")
        print("pgvector extension and embeddings table created successfully.")
    except Exception as e:
        print(f"Error creating pgvector extension: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_pgvector_extension()
    create_tables()