"""
Wine AI Chatbot - RAG Pipeline
This chatbot retrieves relevant wine knowledge and generates expert answers
"""

import os
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize clients
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index("wine-knowledge")

# Configuration
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"  # Cost-effective, high quality
# CHAT_MODEL = "gpt-4o"  # Uncomment for even better quality (more expensive)

def create_embedding(text):
    """Create an embedding vector for text"""
    response = client.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding

def search_wine_knowledge(query, top_k=3):
    """
    Search the wine knowledge base for relevant information
    Returns top_k most relevant chunks
    """
    # Create embedding for the query
    query_embedding = create_embedding(query)
    
    # Search Pinecone
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    
    # Extract relevant chunks
    chunks = []
    for match in results['matches']:
        chunks.append({
            'text': match['metadata']['text'],
            'heading': match['metadata']['heading'],
            'score': match['score']
        })
    
    return chunks

def generate_answer(query, context_chunks):
    """
    Generate an answer using retrieved context and GPT-4
    """
    # Build context from retrieved chunks
    context = "\n\n".join([
        f"Section: {chunk['heading']}\n{chunk['text']}"
        for chunk in context_chunks
    ])
    
    # Create the prompt
    system_prompt = """You are a knowledgeable wine expert with WSET Level 3 certification. 
You answer questions about wine using the provided context from the WSET Level 3 textbook.

Guidelines:
- Provide accurate, educational answers based on the context
- If the context doesn't contain relevant information, say so
- Use wine terminology appropriately
- Be concise but informative
- Cite specific grape varieties, regions, or techniques when relevant"""

    user_prompt = f"""Context from WSET Level 3 textbook:

{context}

Question: {query}

Please answer based on the context provided above."""

    # Call GPT-4
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    return response.choices[0].message.content

def chat(query, verbose=False):
    """
    Main chat function - retrieves context and generates answer
    """
    print(f"\n🍷 Question: {query}\n")
    
    # Step 1: Retrieve relevant chunks
    if verbose:
        print("🔍 Searching wine knowledge base...")
    
    chunks = search_wine_knowledge(query, top_k=3)
    
    if verbose:
        print(f"✓ Found {len(chunks)} relevant sections:\n")
        for i, chunk in enumerate(chunks, 1):
            print(f"   {i}. {chunk['heading']} (relevance: {chunk['score']:.3f})")
        print()
    
    # Step 2: Generate answer
    if verbose:
        print("💭 Generating answer...\n")
    
    answer = generate_answer(query, chunks)
    
    print("📝 Answer:")
    print(answer)
    print()
    
    if verbose:
        print("="*60)
        print("Context used:")
        print("="*60)
        for i, chunk in enumerate(chunks, 1):
            print(f"\n{i}. {chunk['heading']}")
            print(chunk['text'][:200] + "...")
    
    return answer

def interactive_mode():
    """
    Interactive chat mode - keep asking questions
    """
    print("="*60)
    print("🍷 Wine AI Chatbot - Interactive Mode")
    print("="*60)
    print("\nAsk me anything about wine!")
    print("Commands:")
    print("  'quit' or 'exit' - Exit the chatbot")
    print("  'verbose' - Toggle detailed mode")
    print("  'examples' - Show example questions")
    print()
    
    verbose = False
    
    while True:
        query = input("You: ").strip()
        
        if not query:
            continue
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Thanks for chatting! Cheers! 🍷")
            break
        
        if query.lower() == 'verbose':
            verbose = not verbose
            print(f"\n✓ Verbose mode: {'ON' if verbose else 'OFF'}\n")
            continue
        
        if query.lower() == 'examples':
            print("\n📚 Example questions:")
            print("  - What grapes grow well in Burgundy?")
            print("  - What's the difference between Champagne and Prosecco?")
            print("  - How does climate affect Riesling?")
            print("  - What are the characteristics of Pinot Noir?")
            print("  - Explain malolactic fermentation")
            print()
            continue
        
        try:
            chat(query, verbose=verbose)
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    import sys
    
    # Check if question provided as argument
    if len(sys.argv) > 1:
        # Single question mode
        question = " ".join(sys.argv[1:])
        chat(question, verbose=True)
    else:
        # Interactive mode
        interactive_mode()