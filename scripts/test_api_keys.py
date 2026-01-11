"""
Quick API Key Test
Run this first to make sure your keys are set up correctly
"""

import os
from dotenv import load_dotenv

print("🔑 Testing API Keys...\n")

# Load .env file
load_dotenv()

# Check OpenAI key
openai_key = os.getenv('OPENAI_API_KEY')
if openai_key and openai_key.startswith('sk-'):
    print("✅ OpenAI API key found")
    print(f"   Key starts with: {openai_key[:20]}...")
    
    # Test OpenAI connection
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        
        # Simple test
        response = client.embeddings.create(
            input="test",
            model="text-embedding-3-small"
        )
        print("✅ OpenAI API working!")
        print(f"   Test embedding dimension: {len(response.data[0].embedding)}")
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
else:
    print("❌ OpenAI API key not found or invalid")
    print("   Expected format: sk-...")

print()

# Check Pinecone key
pinecone_key = os.getenv('PINECONE_API_KEY')
if pinecone_key:
    print("✅ Pinecone API key found")
    print(f"   Key starts with: {pinecone_key[:20]}...")
    
    # Test Pinecone connection
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=pinecone_key)
        
        # List indexes
        indexes = pc.list_indexes()
        print("✅ Pinecone API working!")
        print(f"   Existing indexes: {[idx['name'] for idx in indexes]}")
    except Exception as e:
        print(f"❌ Pinecone API error: {e}")
else:
    print("❌ Pinecone API key not found")

print("\n" + "="*60)

if openai_key and pinecone_key:
    print("✅ All API keys configured! Ready to create embeddings.")
else:
    print("⚠️  Please add missing API keys to .env file")
