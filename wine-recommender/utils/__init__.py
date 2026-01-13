"""Utility functions for the wine recommendation system."""

from .embeddings import (
    create_embedding,
    query_pinecone_index,
    search_wset_knowledge,
    search_wine_products,
    get_openai_client
)
from .prompts import (
    AGENT1_SYSTEM_PROMPT,
    create_agent1_user_prompt,
    create_agent2_explanation_prompt,
    STREAMLIT_WELCOME,
    STREAMLIT_EXAMPLES
)

__all__ = [
    "create_embedding",
    "query_pinecone_index",
    "search_wset_knowledge",
    "search_wine_products",
    "get_openai_client",
    "AGENT1_SYSTEM_PROMPT",
    "create_agent1_user_prompt",
    "create_agent2_explanation_prompt",
    "STREAMLIT_WELCOME",
    "STREAMLIT_EXAMPLES"
]
