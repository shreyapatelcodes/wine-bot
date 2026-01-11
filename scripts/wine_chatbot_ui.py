"""
Wine AI Chatbot - Streamlit Web Interface
Run with: streamlit run wine_chatbot_ui.py
"""

import streamlit as st
import os
from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Wine AI Chatbot",
    page_icon="🍷",
    layout="centered"
)

# Initialize clients (with caching)
@st.cache_resource
def init_clients():
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
    index = pc.Index("wine-knowledge")
    return client, index

client, index = init_clients()

# Configuration
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

def create_embedding(text):
    """Create an embedding vector for text"""
    response = client.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding

def search_wine_knowledge(query, top_k=3):
    """Search the wine knowledge base"""
    query_embedding = create_embedding(query)
    
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    
    chunks = []
    for match in results['matches']:
        chunks.append({
            'text': match['metadata']['text'],
            'heading': match['metadata']['heading'],
            'score': match['score']
        })
    
    return chunks

def generate_answer(query, context_chunks):
    """Generate an answer using retrieved context"""
    context = "\n\n".join([
        f"Section: {chunk['heading']}\n{chunk['text']}"
        for chunk in context_chunks
    ])
    
    system_prompt = """You are a knowledgeable wine expert with WSET Level 3 certification. 
You answer questions about wine using the provided context from the WSET Level 3 textbook.

Guidelines:
- Provide accurate, educational answers based on the context
- If the context doesn't contain relevant information, say so politely
- Use wine terminology appropriately
- Be concise but informative
- Cite specific grape varieties, regions, or techniques when relevant"""

    user_prompt = f"""Context from WSET Level 3 textbook:

{context}

Question: {query}

Please answer based on the context provided above."""

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    return response.choices[0].message.content, context_chunks

# App title and description
st.title("🍷 Wine AI Chatbot")
st.markdown("""
Ask me anything about wine! I'm trained on WSET Level 3 knowledge.

**Example questions:**
- What grapes grow well in Burgundy?
- How does climate affect Riesling?
- What's the difference between Champagne and Prosecco?
- Explain malolactic fermentation
""")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show sources if available
        if "sources" in message:
            with st.expander("📚 Sources from WSET textbook"):
                for i, source in enumerate(message["sources"], 1):
                    st.markdown(f"**{i}. {source['heading']}** (relevance: {source['score']:.3f})")
                    st.text(source['text'][:300] + "...")
                    st.markdown("---")

# Chat input
if prompt := st.chat_input("Ask about wine..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Consulting the cellar..."):
            # Search knowledge base
            chunks = search_wine_knowledge(prompt, top_k=3)
            
            # Generate answer
            answer, sources = generate_answer(prompt, chunks)
            
            # Display answer
            st.markdown(answer)
            
            # Show sources
            with st.expander("📚 Sources from WSET textbook"):
                for i, source in enumerate(sources, 1):
                    st.markdown(f"**{i}. {source['heading']}** (relevance: {source['score']:.3f})")
                    st.text(source['text'][:300] + "...")
                    st.markdown("---")
    
    # Add assistant message to chat history
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources
    })

# Sidebar
with st.sidebar:
    st.markdown("## About")
    st.markdown("""
    This chatbot uses:
    - **RAG** (Retrieval Augmented Generation)
    - **OpenAI** embeddings & GPT-4
    - **Pinecone** vector database
    - **WSET Level 3** knowledge base
    """)
    
    st.markdown("## Settings")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("Built with ❤️ and 🍷")