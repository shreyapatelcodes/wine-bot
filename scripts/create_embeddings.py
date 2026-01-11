"""
Step 2: Create Embeddings and Upload to Pinecone
This script reads your wine chunks and creates a searchable vector database
"""

import json
import os
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
from tqdm import tqdm
import time

# Load environment variables
load_dotenv()

# Initialize clients
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

# Configuration
INDEX_NAME = "wine-knowledge"
EMBEDDING_MODEL = "text-embedding-3-small"  # Cost-effective, good quality
DIMENSION = 1536  # Dimension for text-embedding-3-small

def create_embedding(text):
    """Create an embedding vector for a piece of text"""
    response = client.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding

def create_pinecone_index():
    """Create or connect to Pinecone index"""
    print(f"🔍 Checking for existing index '{INDEX_NAME}'...")
    
    # Check if index exists
    existing_indexes = pc.list_indexes()
    index_names = [idx['name'] for idx in existing_indexes]
    
    if INDEX_NAME not in index_names:
        print(f"📝 Creating new index '{INDEX_NAME}'...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=DIMENSION,
            metric="cosine",  # Good for semantic similarity
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"  # Change if needed
            )
        )
        # Wait for index to be ready
        print("⏳ Waiting for index to be ready...")
        time.sleep(10)
    else:
        print(f"✓ Index '{INDEX_NAME}' already exists")
    
    return pc.Index(INDEX_NAME)

def process_chunks(chunks_file, batch_size=100):
    """
    Read chunks, create embeddings, and upload to Pinecone
    """
    print(f"\n🍷 Processing wine knowledge chunks...\n")
    
    # Load chunks
    print(f"📖 Loading chunks from {chunks_file}...")
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    print(f"✓ Loaded {len(chunks)} chunks\n")
    
    # Create Pinecone index
    index = create_pinecone_index()
    
    # Process in batches
    print(f"🔄 Creating embeddings and uploading to Pinecone...")
    print(f"   This will take ~2-3 minutes for {len(chunks)} chunks\n")
    
    vectors_to_upsert = []
    total_cost = 0
    
    for i, chunk in enumerate(tqdm(chunks, desc="Processing chunks")):
        # Create embedding
        embedding = create_embedding(chunk['text'])
        
        # Prepare metadata (Pinecone stores this with the vector)
        metadata = {
            'text': chunk['text'][:1000],  # Pinecone has metadata size limits
            'heading': chunk['heading'],
            'chunk_id': chunk['chunk_id'],
            **chunk.get('metadata', {})
        }
        
        # Prepare vector for upsert
        vector = {
            'id': f"chunk_{chunk['chunk_id']}",
            'values': embedding,
            'metadata': metadata
        }
        
        vectors_to_upsert.append(vector)
        
        # Upload in batches
        if len(vectors_to_upsert) >= batch_size or i == len(chunks) - 1:
            index.upsert(vectors=vectors_to_upsert)
            vectors_to_upsert = []
        
        # Small delay to avoid rate limits
        if i % 50 == 0 and i > 0:
            time.sleep(0.5)
    
    # Calculate approximate cost
    total_tokens = sum(len(chunk['text'].split()) * 1.3 for chunk in chunks)  # Rough estimate
    cost = (total_tokens / 1_000_000) * 0.02  # $0.02 per 1M tokens
    
    print(f"\n✅ Upload complete!")
    print(f"   Vectors in index: {index.describe_index_stats()['total_vector_count']}")
    print(f"   Estimated cost: ${cost:.3f}")
    
    return index

def test_search(index, query="What grapes grow well in Burgundy?"):
    """
    Test the vector database with a sample query
    """
    print(f"\n🔍 Testing search with query: '{query}'\n")
    
    # Create embedding for query
    query_embedding = create_embedding(query)
    
    # Search Pinecone
    results = index.query(
        vector=query_embedding,
        top_k=3,
        include_metadata=True
    )
    
    print("Top 3 results:\n")
    for i, match in enumerate(results['matches'], 1):
        print(f"{i}. Score: {match['score']:.4f}")
        print(f"   Heading: {match['metadata']['heading']}")
        print(f"   Text: {match['metadata']['text'][:200]}...")
        print()
    
    return results

if __name__ == "__main__":
    print("="*60)
    print("🍷 Wine AI - Embedding Creation & Vector Database Setup")
    print("="*60)
    
    # Check for API keys
    if not os.getenv('OPENAI_API_KEY') or not os.getenv('PINECONE_API_KEY'):
        print("\n❌ Error: API keys not found!")
        print("\nPlease:")
        print("1. Copy .env.template to .env")
        print("2. Add your OpenAI and Pinecone API keys")
        print("3. Run this script again")
        exit(1)
    
    # Process chunks
    chunks_file = '../chunks/wine_chunks.json'  # Update path if needed
    
    
    if not os.path.exists(chunks_file):
        print(f"\n❌ Error: {chunks_file} not found!")
        print("Please make sure wine_chunks.json is in the same directory.")
        exit(1)
    
    index = process_chunks(chunks_file)
    
    # Test search
    test_search(index)
    
    print("\n" + "="*60)
    print("✅ Setup complete! Your wine knowledge base is ready.")
    print("="*60)
    print("\nNext steps:")
    print("1. Try more test queries")
    print("2. Build the RAG chatbot (next script)")
    print("3. Create a chat interface")
