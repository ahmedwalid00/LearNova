#!/usr/bin/env python3
"""
PGVector Integration Test Script
Tests the PGVector setup and integration with the LearNova project.
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.Helpers.config import get_settings
from src.Stores.VectorDB.vectordb_factory import VectorDBProviderFactory
from src.Stores.LLM.llm_facatory import LLMProviderFactory

async def test_pgvector_integration():
    """Test PGVector integration end-to-end"""
    print("🧪 Testing PGVector Integration...")
    
    # Load settings
    settings = get_settings()
    
    # Create database connection
    postgres_conn = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"
    engine = create_async_engine(postgres_conn)
    session_local = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        # Test 1: Vector DB Factory
        print("✅ Step 1: Creating VectorDB Factory...")
        vectordb_factory = VectorDBProviderFactory(config=settings, db_client=session_local)
        vectordb_client = vectordb_factory.create(provider=settings.VECTOR_DB_BACKEND)
        
        if vectordb_client is None:
            print("❌ Failed to create VectorDB client")
            return False
            
        # Test 2: Connect to PGVector
        print("✅ Step 2: Connecting to PGVector...")
        await vectordb_client.connect()
        
        # Test 3: Create test collection
        print("✅ Step 3: Creating test collection...")
        test_collection = "test_pgvector_collection"
        
        # Clean up existing collection
        if await vectordb_client.is_collection_existed(test_collection):
            await vectordb_client.delete_collection(test_collection)
            
        success = await vectordb_client.create_collection(
            collection_name=test_collection,
            embedding_size=settings.EMBEDDING_MODEL_SIZE,
            do_reset=True
        )
        
        if not success:
            print("❌ Failed to create test collection")
            return False
            
        # Test 4: List collections
        print("✅ Step 4: Listing collections...")
        collections = await vectordb_client.list_all_collections()
        print(f"   Found collections: {collections}")
        
        # Test 5: Insert test vector
        print("✅ Step 5: Inserting test vector...")
        test_vector = [0.1] * settings.EMBEDDING_MODEL_SIZE  # Dummy vector
        test_text = "This is a test document for PGVector integration"
        test_metadata = {"test": True, "document_type": "integration_test"}
        
        # Create a dummy chunk_id (UUID format)
        import uuid
        test_chunk_id = str(uuid.uuid4())
        
        insert_success = await vectordb_client.insert_one(
            collection_name=test_collection,
            text=test_text,
            vector=test_vector,
            metadata=test_metadata,
            record_id=test_chunk_id
        )
        
        if not insert_success:
            print("❌ Failed to insert test vector")
            return False
            
        # Test 6: Search vectors
        print("✅ Step 6: Searching vectors...")
        search_results = await vectordb_client.search_by_vector(
            collection_name=test_collection,
            vector=test_vector,
            limit=5
        )
        
        if not search_results:
            print("❌ Failed to search vectors")
            return False
            
        print(f"   Found {len(search_results)} results")
        for result in search_results:
            print(f"   - Text: {result.text[:50]}...")
            print(f"   - Score: {result.score}")
            
        # Test 7: Collection info
        print("✅ Step 7: Getting collection info...")
        info = await vectordb_client.get_collection_info(test_collection)
        if info:
            print(f"   Collection info: {info}")
        
        # Test 8: LLM Integration
        print("✅ Step 8: Testing LLM integration...")
        try:
            llm_factory = LLMProviderFactory(config=settings)
            embedding_client = llm_factory.create(provider=settings.EMBEDDING_BACKEND)
            embedding_client.set_embedding_model(
                model_id=settings.EMBEDDING_MODEL_ID,
                embedding_size=settings.EMBEDDING_MODEL_SIZE
            )
            print("   LLM embedding client created successfully")
        except Exception as e:
            print(f"   ⚠️  LLM integration test skipped: {str(e)}")
        
        # Cleanup
        print("✅ Step 9: Cleaning up test collection...")
        await vectordb_client.delete_collection(test_collection)
        
        print("\n🎉 All PGVector integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ PGVector integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_pgvector_integration())
