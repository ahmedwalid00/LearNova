# PGVector Setup and Integration Guide

## Overview
This guide covers the setup and integration of PGVector with the LearNova project for vector similarity search capabilities.

## Prerequisites
- Docker and Docker Compose installed
- PostgreSQL knowledge (basic)
- OpenAI API key (for embeddings)

## Quick Start

### 1. Environment Configuration
Copy the PGVector environment example:
```bash
cp .env.pgvector.example .env.docker
```

Edit `.env.docker` and add your OpenAI API key:
```env
OPENAI_API_KEY=your_actual_openai_api_key_here
```

### 2. Start the Services
Start PostgreSQL with PGVector support:
```bash
cd Docker
docker-compose up -d db redis
```

### 3. Apply Database Migrations
```bash
cd ..  # Back to project root
alembic upgrade head
```

### 4. Test PGVector Integration
```bash
python test_pgvector.py
```

### 5. Start the Application
```bash
# Option 1: Run locally
uvicorn src.main:app --reload

# Option 2: Run with Docker Compose
cd Docker
docker-compose up -d app
```

## Architecture

### Components
1. **PostgreSQL + PGVector**: Vector database for similarity search
2. **VectorDB Factory**: Abstraction layer for vector database operations
3. **LLM Factory**: Handles embedding generation via OpenAI
4. **PGVector Provider**: Implements vector operations for PostgreSQL

### Vector Table Schema
```sql
CREATE TABLE {collection_name} (
    id bigserial PRIMARY KEY,
    text text,
    vector vector({embedding_size}),
    metadata jsonb DEFAULT '{}',
    chunk_id uuid,
    FOREIGN KEY (chunk_id) REFERENCES lesson_chunks(chunk_id)
);
```

## Configuration Options

### Vector Database Settings
- `VECTOR_DB_BACKEND`: Set to "PGVECTOR"
- `VECTOR_DB_DISTANCE_METHOD`: "cosine" or "dot"
- `VECTOR_DB_PGVEC_INDEX_THRESHOLD`: Minimum records before creating index (default: 100)

### Embedding Settings
- `EMBEDDING_BACKEND`: "openai" (currently supported)
- `EMBEDDING_MODEL_ID`: "text-embedding-ada-002" (recommended)
- `EMBEDDING_MODEL_SIZE`: 1536 (for text-embedding-ada-002)

## Usage Examples

### Basic Vector Operations
```python
from src.Stores.VectorDB.vectordb_factory import VectorDBProviderFactory
from src.Helpers.config import get_settings

settings = get_settings()
factory = VectorDBProviderFactory(config=settings, db_client=session_local)
vectordb = factory.create(provider="PGVECTOR")

# Connect
await vectordb.connect()

# Create collection
await vectordb.create_collection("my_collection", embedding_size=1536)

# Insert vector
await vectordb.insert_one(
    collection_name="my_collection",
    text="Sample document text",
    vector=[0.1, 0.2, ...],  # 1536-dimensional vector
    metadata={"source": "document.pdf"},
    record_id="chunk-uuid"
)

# Search
results = await vectordb.search_by_vector(
    collection_name="my_collection",
    vector=[0.1, 0.2, ...],
    limit=5
)
```

### Integration with Lessons
The PGVector setup is designed to work with the lesson chunking system:

1. **Lesson Upload**: PDF lessons are processed and chunked
2. **Embedding Generation**: Each chunk gets embedded using OpenAI
3. **Vector Storage**: Embeddings stored in PGVector collections
4. **Similarity Search**: Find similar content across lessons

## Troubleshooting

### Common Issues

1. **Extension not installed**
   ```
   Error: extension "vector" does not exist
   ```
   **Solution**: Ensure you're using the `pgvector/pgvector:pg16` Docker image

2. **Foreign key constraint fails**
   ```
   Error: relation "lesson_chunks" does not exist
   ```
   **Solution**: Run `alembic upgrade head` to create required tables

3. **Connection refused**
   ```
   Error: could not connect to server
   ```
   **Solution**: Ensure PostgreSQL container is running: `docker-compose up -d db`

### Verification Steps
1. Check container status: `docker-compose ps`
2. Verify extension: `docker-compose exec db psql -U [username] -d [database] -c "SELECT * FROM pg_extension WHERE extname = 'vector';"`
3. Run test script: `python test_pgvector.py`

## Performance Considerations

### Indexing
- Automatic index creation when collection reaches threshold
- HNSW index for better performance on large datasets
- Index types: HNSW (default), IVFFlat

### Scaling
- Consider partitioning for very large datasets
- Monitor index size and query performance
- Adjust `VECTOR_DB_PGVEC_INDEX_THRESHOLD` based on usage

## Security
- PGVector inherits PostgreSQL security features
- Use strong credentials for database access
- Consider SSL connections for production
- Secure API keys in environment variables

## Next Steps
1. Implement lesson processing pipeline
2. Add embedding generation for uploaded content
3. Create search API endpoints
4. Add vector similarity features to chatbot
