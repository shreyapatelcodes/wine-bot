"""
Embedding and vector search utilities.
Reuses functions from the existing wine chatbot with extensions for wine recommendations.
"""

import sys
from pathlib import Path
from openai import OpenAI
from pinecone import Pinecone
from typing import List, Dict, Any, Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config


# Initialize clients
_openai_client = None
_pinecone_client = None
_pinecone_indexes = {}


def get_openai_client() -> OpenAI:
    """Get or create OpenAI client (singleton pattern)."""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
    return _openai_client


def get_pinecone_client() -> Pinecone:
    """Get or create Pinecone client (singleton pattern)."""
    global _pinecone_client
    if _pinecone_client is None:
        _pinecone_client = Pinecone(api_key=Config.PINECONE_API_KEY)
    return _pinecone_client


def get_pinecone_index(index_name: str):
    """Get a Pinecone index by name (cached)."""
    global _pinecone_indexes
    if index_name not in _pinecone_indexes:
        pc = get_pinecone_client()
        _pinecone_indexes[index_name] = pc.Index(index_name)
    return _pinecone_indexes[index_name]


def create_embedding(text: str) -> List[float]:
    """
    Create an embedding vector for text using OpenAI's embedding model.

    Args:
        text: Text to embed

    Returns:
        List of floats representing the embedding vector (dimension=1536)
    """
    client = get_openai_client()
    response = client.embeddings.create(
        input=text,
        model=Config.EMBEDDING_MODEL
    )
    return response.data[0].embedding


def query_pinecone_index(
    index_name: str,
    query_vector: List[float],
    top_k: int = 5,
    filter_dict: Optional[Dict[str, Any]] = None,
    include_metadata: bool = True
) -> List[Dict[str, Any]]:
    """
    Query a Pinecone index with a vector and optional metadata filters.

    Args:
        index_name: Name of the Pinecone index
        query_vector: Query embedding vector
        top_k: Number of results to return
        filter_dict: Optional metadata filters (e.g., {"wine_type": "red"})
        include_metadata: Whether to include metadata in results

    Returns:
        List of match dictionaries with 'id', 'score', and optionally 'metadata'
    """
    index = get_pinecone_index(index_name)

    query_params = {
        "vector": query_vector,
        "top_k": top_k,
        "include_metadata": include_metadata
    }

    if filter_dict:
        query_params["filter"] = filter_dict

    results = index.query(**query_params)
    return results['matches']


def search_wset_knowledge(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Search the WSET wine knowledge base for relevant information.
    Reuses logic from existing wine_chatbot.py.

    Args:
        query: Natural language query
        top_k: Number of chunks to retrieve

    Returns:
        List of knowledge chunks with 'text', 'heading', and 'score'
    """
    # Create embedding for the query
    query_embedding = create_embedding(query)

    # Search Pinecone wine-knowledge index
    matches = query_pinecone_index(
        index_name=Config.WSET_INDEX_NAME,
        query_vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )

    # Extract relevant chunks
    chunks = []
    for match in matches:
        chunks.append({
            'text': match['metadata']['text'],
            'heading': match['metadata']['heading'],
            'score': match['score']
        })

    return chunks


def search_wine_products(
    query_text: str,
    price_min: float,
    price_max: float,
    wine_type: Optional[str] = None,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Search the wine products vector database with semantic search + metadata filters.

    Args:
        query_text: Rich natural language description of desired wine
        price_min: Minimum price in USD
        price_max: Maximum price in USD
        wine_type: Optional wine type filter ('red', 'white', 'rosé', 'sparkling')
        top_k: Number of wine products to return

    Returns:
        List of wine matches with metadata and similarity scores
    """
    # Create embedding for the query
    query_embedding = create_embedding(query_text)

    # Build metadata filter
    filter_dict = {
        "price_usd": {"$gte": price_min, "$lte": price_max}
    }
    if wine_type:
        filter_dict["wine_type"] = wine_type

    # Search Pinecone wine-products index
    matches = query_pinecone_index(
        index_name=Config.WINE_PRODUCTS_INDEX_NAME,
        query_vector=query_embedding,
        top_k=top_k,
        filter_dict=filter_dict,
        include_metadata=True
    )

    return matches
