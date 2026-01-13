# Wine Recommendation Engine

AI-powered wine recommendation system using WSET Level 3 knowledge and semantic vector search.

## Overview

This system uses a two-agent pipeline:
- **Agent 1 (Preference Interpreter)**: Interprets user preferences using WSET knowledge via RAG
- **Agent 2 (Wine Searcher)**: Searches wine products using vector similarity matching

Built with:
- OpenAI (GPT-4o-mini for chat, text-embedding-3-small for vectors)
- Pinecone (vector database for WSET knowledge and wine products)
- Streamlit (web interface)
- Pydantic (data validation)

## Setup

### 1. Install the Package

From the project root (`wine-ai-chatbot`), install the package in editable mode:

```bash
cd wine-ai-chatbot
pip install -e .
```

This will:
- Install all dependencies automatically
- Make the `wine_recommender` package available system-wide
- Allow you to run scripts from any directory

### 2. Set Up Environment Variables

Your existing `.env` file in the project root should have:
```
OPENAI_API_KEY=your_key_here
PINECONE_API_KEY=your_key_here
```

### 3. Seed the Wine Products Vector Database

This creates the "wine-products" Pinecone index and uploads wine data:

```bash
python -m wine_recommender.data.seed_vector_db
```

This will:
- Create the "wine-products" Pinecone index (if it doesn't exist)
- Load 15 wines from `data/wines_catalog.json`
- Generate embeddings for each wine's description
- Upload wines with metadata to Pinecone

**Note**: This only needs to be run once. The current catalog has 15 diverse wines ranging from $11.99 to $65.00.

## Running the Application

### Streamlit Web Interface

```bash
streamlit run wine-recommender/ui/streamlit_app.py
```

The app will open at [http://localhost:8501](http://localhost:8501)

### Python API Usage

```python
from wine_recommender import get_wine_recommendations, UserPreferences

# Create user preferences
user_prefs = UserPreferences(
    description="Bold red wine for a steak dinner",
    budget_min=40.0,
    budget_max=60.0,
    food_pairing="steak",
    wine_type_pref="red"
)

# Get recommendations
recommendations = get_wine_recommendations(
    user_prefs,
    top_n=3,
    verbose=True  # Show detailed agent outputs
)

# Display results
for rec in recommendations:
    print(f"{rec.wine.name} - ${rec.wine.price_usd}")
    print(f"  {rec.explanation}")
    print(f"  Score: {rec.relevance_score:.3f}")
    print(f"  URL: {rec.wine.wine_com_url}")
    print()
```

## Architecture

```
User Input → Agent 1 (WSET RAG) → Agent 2 (Vector Search) → Recommendations
```

### Agent 1: Preference Interpreter
1. Queries existing "wine-knowledge" Pinecone index with user preferences
2. Retrieves relevant WSET Level 3 knowledge (3 chunks)
3. Uses LLM to synthesize rich wine description for semantic search
4. Outputs SearchQuery with query text + price filters

### Agent 2: Wine Searcher
1. Creates embedding from SearchQuery text
2. Queries "wine-products" Pinecone index with vector similarity
3. Applies metadata filters (price range, wine type)
4. Retrieves top 3-5 matches
5. Uses LLM to generate personalized explanations
6. Outputs WineRecommendation objects

## File Structure

```
wine-recommender/
├── __init__.py
├── config.py                    # Configuration & env vars
├── data/
│   ├── wines_catalog.json       # 15 curated wines
│   ├── vector_store.py          # Pinecone management
│   └── seed_vector_db.py        # Seeding script
├── agents/
│   ├── preference_interpreter.py  # Agent 1
│   ├── wine_searcher.py           # Agent 2
│   └── orchestrator.py            # Pipeline coordinator
├── models/
│   └── schemas.py               # Pydantic data models
├── utils/
│   ├── embeddings.py            # OpenAI & Pinecone utilities
│   └── prompts.py               # LLM prompts
├── ui/
│   └── streamlit_app.py         # Web interface
└── requirements.txt
```

## Adding More Wines

To expand the wine catalog:

1. Edit `data/wines_catalog.json` and add more wine objects
2. Each wine needs these fields:
   - `id`, `name`, `producer`, `vintage` (optional)
   - `wine_type`, `varietal`, `country`, `region`
   - `body`, `sweetness`, `acidity`, `tannin` (optional for whites)
   - `characteristics` (array), `flavor_notes` (array)
   - `description` (this gets embedded for search)
   - `price_usd`, `rating` (optional)
   - `wine_com_url`

3. Re-run the seeding script:
   ```bash
   python -m wine_recommender.data.seed_vector_db
   ```

## Configuration

Key settings in [config.py](wine-recommender/config.py):

- `WSET_INDEX_NAME`: "wine-knowledge" (existing WSET data)
- `WINE_PRODUCTS_INDEX_NAME`: "wine-products" (new wine catalog)
- `EMBEDDING_MODEL`: "text-embedding-3-small" (1536 dimensions)
- `CHAT_MODEL`: "gpt-4o-mini" (cost-effective)
- `TOP_K_WSET`: 3 (WSET chunks to retrieve)
- `TOP_K_WINES`: 5 (wine candidates to retrieve)

## Testing

Example test queries:
```python
# Test 1: Bold red for steak
user_prefs = UserPreferences(
    description="Bold red wine for steak dinner",
    budget_min=40.0,
    budget_max=60.0,
    food_pairing="steak"
)

# Test 2: Crisp white for seafood
user_prefs = UserPreferences(
    description="Crisp white wine for seafood",
    budget_min=20.0,
    budget_max=35.0,
    food_pairing="seafood"
)

# Test 3: Sparkling for celebration
user_prefs = UserPreferences(
    description="Sparkling wine for celebration",
    budget_min=50.0,
    budget_max=100.0,
    wine_type_pref="sparkling"
)
```

## Future Enhancements

- Expand wine catalog to 200-300+ wines
- Add Wine.com API integration for real-time pricing
- Implement user feedback loop (thumbs up/down)
- Add "similar wines" feature
- Build FastAPI wrapper for programmatic access
- Add conversation memory across sessions

## Troubleshooting

**Import errors**: Make sure you're running from the project root and the parent directory is in your Python path.

**Pinecone errors**: Verify your API key in `.env` and that both indexes exist:
- "wine-knowledge" (should already exist)
- "wine-products" (created by seed_vector_db.py)

**No recommendations**: Try expanding your budget range or removing the wine_type filter.

## License

Built for demonstration purposes. Wine data sourced from public information.
