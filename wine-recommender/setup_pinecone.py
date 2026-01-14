"""
Script to set up Pinecone index and upload wine catalog.
"""

import json
import time
from pathlib import Path
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
from config import Config
from tqdm import tqdm


def create_pinecone_index():
    """Create Pinecone index for wine products if it doesn't exist."""
    pc = Pinecone(api_key=Config.PINECONE_API_KEY)

    # Check if index already exists
    existing_indexes = pc.list_indexes()
    index_names = [idx['name'] for idx in existing_indexes]

    if Config.WINE_PRODUCTS_INDEX_NAME in index_names:
        print(f"✅ Index '{Config.WINE_PRODUCTS_INDEX_NAME}' already exists")
        return pc.Index(Config.WINE_PRODUCTS_INDEX_NAME)

    print(f"Creating index '{Config.WINE_PRODUCTS_INDEX_NAME}'...")
    pc.create_index(
        name=Config.WINE_PRODUCTS_INDEX_NAME,
        dimension=Config.EMBEDDING_DIMENSION,
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )

    # Wait for index to be ready
    print("Waiting for index to be ready...")
    while not pc.describe_index(Config.WINE_PRODUCTS_INDEX_NAME).status['ready']:
        time.sleep(1)

    print(f"✅ Index '{Config.WINE_PRODUCTS_INDEX_NAME}' created successfully")
    return pc.Index(Config.WINE_PRODUCTS_INDEX_NAME)


def create_wine_text_for_embedding(wine):
    """
    Create a rich text representation of wine for embedding.
    This combines all relevant fields into a searchable text.
    """
    parts = []

    # Basic info
    parts.append(f"Wine: {wine['name']}")
    if wine.get('producer'):
        parts.append(f"Producer: {wine['producer']}")
    if wine.get('vintage'):
        parts.append(f"Vintage: {wine['vintage']}")

    # Wine characteristics
    parts.append(f"Type: {wine['wine_type']}")
    if wine.get('varietal'):
        parts.append(f"Varietal: {wine['varietal']}")
    parts.append(f"Country: {wine['country']}")
    if wine.get('region'):
        parts.append(f"Region: {wine['region']}")

    # Tasting profile
    if wine.get('body'):
        parts.append(f"Body: {wine['body']}")
    if wine.get('sweetness'):
        parts.append(f"Sweetness: {wine['sweetness']}")
    if wine.get('acidity'):
        parts.append(f"Acidity: {wine['acidity']}")
    if wine.get('tannin'):
        parts.append(f"Tannin: {wine['tannin']}")

    # Characteristics and flavors
    if wine.get('characteristics'):
        parts.append(f"Characteristics: {', '.join(wine['characteristics'])}")
    if wine.get('flavor_notes'):
        parts.append(f"Flavor notes: {', '.join(wine['flavor_notes'])}")

    # Description
    if wine.get('description'):
        parts.append(f"Description: {wine['description']}")

    # Price
    if wine.get('price_usd'):
        parts.append(f"Price: ${wine['price_usd']}")

    return " | ".join(parts)


def generate_embeddings_batch(texts, client):
    """Generate embeddings for a batch of texts using OpenAI."""
    response = client.embeddings.create(
        input=texts,
        model=Config.EMBEDDING_MODEL
    )
    return [item.embedding for item in response.data]


def upload_wines_to_pinecone(index):
    """Load wine catalog and upload to Pinecone with embeddings."""
    print(f"\nLoading wine catalog from {Config.WINES_CATALOG_PATH}...")
    with open(Config.WINES_CATALOG_PATH, 'r') as f:
        wines = json.load(f)

    print(f"Found {len(wines)} wines")

    # Initialize OpenAI client
    client = OpenAI(api_key=Config.OPENAI_API_KEY)

    # Process in batches
    batch_size = 100
    total_batches = (len(wines) + batch_size - 1) // batch_size

    print(f"\nGenerating embeddings and uploading to Pinecone...")
    print(f"Processing in {total_batches} batches of {batch_size}...")

    for i in tqdm(range(0, len(wines), batch_size), desc="Uploading wines"):
        batch = wines[i:i + batch_size]

        # Create text representations
        texts = [create_wine_text_for_embedding(wine) for wine in batch]

        # Generate embeddings
        embeddings = generate_embeddings_batch(texts, client)

        # Prepare vectors for Pinecone
        vectors = []
        for wine, embedding in zip(batch, embeddings):
            # Create metadata (exclude description to save space, keep essential fields)
            # Note: Pinecone doesn't accept None/null values, so we filter them out
            metadata = {
                'name': wine['name'],
                'producer': wine.get('producer') or '',
                'wine_type': wine['wine_type'],
                'varietal': wine.get('varietal') or '',
                'country': wine['country'],
                'region': wine.get('region') or '',
                'body': wine.get('body') or '',
                'sweetness': wine.get('sweetness') or '',
                'acidity': wine.get('acidity') or '',
                'tannin': wine.get('tannin') or '',
                'characteristics': ', '.join(wine.get('characteristics', [])),
                'flavor_notes': ', '.join(wine.get('flavor_notes', [])),
                'vivino_url': wine.get('vivino_url') or ''
            }

            # Add optional fields only if they have values
            if wine.get('vintage'):
                metadata['vintage'] = wine['vintage']
            if wine.get('price_usd'):
                metadata['price_usd'] = wine['price_usd']

            vectors.append({
                'id': wine['id'],
                'values': embedding,
                'metadata': metadata
            })

        # Upload to Pinecone
        index.upsert(vectors=vectors)

        # Small delay to avoid rate limits
        time.sleep(0.5)

    print(f"\n✅ Successfully uploaded {len(wines)} wines to Pinecone!")

    # Verify upload
    stats = index.describe_index_stats()
    print(f"\nIndex stats:")
    print(f"  Total vectors: {stats['total_vector_count']}")
    print(f"  Dimension: {stats['dimension']}")


def main():
    """Main function to set up Pinecone and upload wines."""
    print("=" * 60)
    print("Wine Catalog → Pinecone Setup")
    print("=" * 60)

    # Create index
    index = create_pinecone_index()

    # Upload wines
    upload_wines_to_pinecone(index)

    print("\n" + "=" * 60)
    print("Setup complete! 🍷")
    print("=" * 60)


if __name__ == "__main__":
    main()
