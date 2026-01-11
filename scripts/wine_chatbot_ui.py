"""
Wine AI Chatbot - Modern Wine Bar Interface
Run with: streamlit run wine_chatbot_modern.py
"""

import streamlit as st
import os
from openai import OpenAI
from pinecone import pinecone

# Page config
st.set_page_config(
    page_title="Wine AI",
    page_icon="🍷",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Modern, fresh wine bar CSS styling
st.markdown("""
<style>
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Clash+Display:wght@300;400;500;600&family=General+Sans:wght@300;400;500&display=swap');
    
    /* Global styling */
    .stApp {
        background: linear-gradient(180deg, #faf8f5 0%, #f5f0ea 100%);
        color: #2a2a2a;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container */
    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 750px !important;
    }
    
    /* Title styling */
    h1 {
        font-family: 'Clash Display', sans-serif !important;
        font-weight: 500 !important;
        font-size: 3.2rem !important;
        color: #8b4513 !important;
        text-align: center !important;
        letter-spacing: -0.02em !important;
        margin-bottom: 0.3rem !important;
    }
    
    /* Subtitle */
    .subtitle {
        font-family: 'General Sans', sans-serif;
        font-weight: 400;
        font-size: 1rem;
        color: #a67c52;
        text-align: center;
        margin-bottom: 3rem;
        letter-spacing: 0.02em;
    }
    
    /* Chat messages */
    .stChatMessage {
        background: white !important;
        border: 1px solid #e8dfd5 !important;
        border-radius: 16px !important;
        margin: 1.2rem 0 !important;
        padding: 1.2rem !important;
        box-shadow: 0 2px 8px rgba(139, 69, 19, 0.04) !important;
    }
    
    .stChatMessage[data-testid="user-message"] {
        background: #fff9f5 !important;
        border-left: 3px solid #d4a574 !important;
    }
    
    .stChatMessage[data-testid="assistant-message"] {
        background: white !important;
        border-left: 3px solid #8b4513 !important;
    }
    
    /* Message text */
    .stChatMessage p {
        font-family: 'General Sans', sans-serif !important;
        font-size: 1.05rem !important;
        line-height: 1.65 !important;
        color: #FAF8F5 !important;
        font-weight: 400 !important;
    }
    
    /* Chat input */
    .stChatInput {
        border: 2px solid #e8dfd5 !important;
        border-radius: 24px !important;
        background: white !important;
        box-shadow: 0 2px 12px rgba(139, 69, 19, 0.06) !important;
    }
    
    .stChatInput textarea {
        font-family: 'General Sans', sans-serif !important;
        color: #FAF8F5 !important;
        font-size: 1rem !important;
    }
    
    .stChatInput textarea::placeholder {
        color: #a89f95 !important;
    }
    
    /* Expander (sources) */
    .streamlit-expanderHeader {
        font-family: 'General Sans', sans-serif !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        color: #8b4513 !important;
        background: #faf8f5 !important;
        border-radius: 10px !important;
        border: 1px solid #e8dfd5 !important;
        padding: 0.8rem 1rem !important;
    }
    
    .streamlit-expanderContent {
        background: white !important;
        border: 1px solid #e8dfd5 !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
        padding: 1.2rem !important;
        font-family: 'General Sans', sans-serif !important;
        font-size: 0.9rem !important;
        color: #5a5a5a !important;
    }
    
    /* Source headings */
    .streamlit-expanderContent strong {
        color: #8b4513 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    
    /* Horizontal rule */
    hr {
        border-color: #e8dfd5 !important;
        margin: 1rem 0 !important;
        opacity: 0.5;
    }
    
    /* Example questions */
    .example-questions {
        background: white;
        border: 1px solid #e8dfd5;
        border-radius: 20px;
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: 0 4px 16px rgba(139, 69, 19, 0.06);
    }
    
    .example-questions h3 {
        font-family: 'Clash Display', sans-serif !important;
        font-weight: 500 !important;
        font-size: 1.4rem !important;
        color: #8b4513 !important;
        margin-bottom: 1.2rem !important;
        text-align: center;
        letter-spacing: -0.01em;
    }
    
    .example-item {
        font-family: 'General Sans', sans-serif;
        color: #5a5a5a;
        padding: 0.8rem 0;
        font-size: 0.95rem;
        border-bottom: 1px solid #f5f0ea;
        transition: all 0.2s ease;
    }
    
    .example-item:last-child {
        border-bottom: none;
    }
    
    .example-item:hover {
        color: #8b4513;
        padding-left: 0.5rem;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #d4a574 !important;
    }
    
    /* Wine glass icon */
    .wine-icon {
        text-align: center;
        font-size: 2.5rem;
        margin-bottom: 1rem;
        filter: grayscale(20%);
    }
    
    /* Accent divider */
    .accent-line {
        width: 80px;
        height: 3px;
        background: linear-gradient(90deg, transparent, #d4a574, transparent);
        margin: 1.5rem auto;
        border-radius: 2px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize clients (with caching)
@st.cache_resource
def init_clients():
    # Get API keys - works both locally and on Streamlit Cloud
    openai_key = None
    pinecone_key = None
    
    try:
        # Try Streamlit secrets first (for cloud deployment)
        openai_key = st.secrets["OPENAI_API_KEY"]
        pinecone_key = st.secrets["PINECONE_API_KEY"]
    except Exception as e:
        # Fallback to environment variables (for local development)
        try:
            from dotenv import load_dotenv
            load_dotenv()
            openai_key = os.getenv('OPENAI_API_KEY')
            pinecone_key = os.getenv('PINECONE_API_KEY')
        except:
            pass
    
    # Validate keys
    if not openai_key or not openai_key.startswith('sk-'):
        st.error("❌ OpenAI API key not found or invalid. Please check your Streamlit secrets.")
        st.stop()
    
    if not pinecone_key:
        st.error("❌ Pinecone API key not found. Please check your Streamlit secrets.")
        st.stop()
    
    try:
        client = OpenAI(api_key=openai_key)
        
        # Initialize Pinecone (v3+ API)
        from pinecone import Pinecone as PineconeClient
        pc = PineconeClient(api_key=pinecone_key)
        index = pc.Index("wine-knowledge")
        
        return client, index
    except Exception as e:
        st.error(f"❌ Error initializing clients: {str(e)}")
        st.info("💡 Try updating pinecone: pip install --upgrade pinecone")
        st.stop()

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
    
    system_prompt = """You are a knowledgeable and approachable wine expert with WSET Level 3 certification. 
You provide clear, insightful answers about wine using the provided context from the WSET Level 3 textbook.

Guidelines:
- Be conversational and accessible while maintaining expertise
- Provide educational responses based on the context
- If the context doesn't fully address the question, acknowledge this naturally
- Use wine terminology appropriately but don't be overly formal
- Share practical insights about grape varieties, regions, and production methods
- Keep answers focused and engaging"""

    user_prompt = f"""Context from WSET Level 3 textbook:

{context}

Question: {query}

Please provide a clear, insightful answer based on the context above."""

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

# App header
st.markdown("<div class='wine-icon'>🍷</div>", unsafe_allow_html=True)
st.markdown("<h1>Wine AI</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Ask me anything about wine</p>", unsafe_allow_html=True)
st.markdown("<div class='accent-line'></div>", unsafe_allow_html=True)

# Example questions (only show if no messages)
if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    st.markdown("""
    <div class='example-questions'>
        <h3>Try asking...</h3>
        <div class='example-item'>What makes Burgundy Chardonnay special?</div>
        <div class='example-item'>How does climate affect wine?</div>
        <div class='example-item'>What's the difference between Champagne and Prosecco?</div>
        <div class='example-item'>Explain malolactic fermentation</div>
        <div class='example-item'>What food pairs well with Pinot Noir?</div>
    </div>
    """, unsafe_allow_html=True)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show sources if available
        if "sources" in message:
            with st.expander("📚 Sources"):
                for i, source in enumerate(message["sources"], 1):
                    st.markdown(f"**{source['heading']}** · {source['score']:.0%} match")
                    st.text(source['text'][:200] + "...")
                    if i < len(message["sources"]):
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
        with st.spinner("Thinking..."):
            # Search knowledge base
            chunks = search_wine_knowledge(prompt, top_k=3)
            
            # Generate answer
            answer, sources = generate_answer(prompt, chunks)
            
            # Display answer
            st.markdown(answer)
            
            # Show sources
            with st.expander("📚 Sources"):
                for i, source in enumerate(sources, 1):
                    st.markdown(f"**{source['heading']}** · {source['score']:.0%} match")
                    st.text(source['text'][:200] + "...")
                    if i < len(sources):
                        st.markdown("---")
    
    # Add assistant message to chat history
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources
    })