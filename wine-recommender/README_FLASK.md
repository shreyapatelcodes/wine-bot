# AI Wine Agent - Flask Web Application

A sophisticated wine recommendation engine powered by AI, featuring an elegant user interface and WSET Level 3 wine knowledge.

## Features

- **AI-Powered Recommendations**: Uses OpenAI GPT-4o-mini and vector similarity search
- **WSET Level 3 Knowledge**: Professional wine education integrated into recommendations
- **Elegant UI**: Custom-designed interface with dark mode support
- **Personalized Explanations**: Each wine recommendation includes a tailored explanation
- **Vector Search**: Semantic search through 1,500+ wines using Pinecone
- **Direct Purchase Links**: All wines link to Vivino for easy purchasing

## Quick Start

### Prerequisites

- Python 3.9 or higher
- OpenAI API key
- Pinecone API key
- Wine catalog data indexed in Pinecone

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/wine-ai-chatbot.git
cd wine-ai-chatbot/wine-recommender
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**

Create a `.env` file:
```bash
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here
```

4. **Run the application**
```bash
python app.py
```

Visit http://localhost:5000

## Project Structure

```
wine-recommender/
├── app.py                      # Flask application
├── agents/
│   ├── orchestrator.py         # Main recommendation orchestrator
│   ├── preference_interpreter.py
│   └── wine_searcher.py
├── models/
│   └── schemas.py              # Pydantic data models
├── utils/
│   ├── embeddings.py           # OpenAI & Pinecone utilities
│   └── constants.py            # Configuration constants
├── data/
│   └── wines_catalog.json      # Wine catalog (1,500+ wines)
├── templates/
│   ├── index.html              # Home page
│   └── results.html            # Results page
├── static/
│   ├── css/
│   │   └── styles.css          # Custom styles
│   └── js/
│       └── main.js             # Frontend JavaScript
├── requirements.txt            # Python dependencies
├── DEPLOYMENT.md               # Deployment guide
└── README_FLASK.md             # This file
```

## API Endpoints

### GET /
Serves the main homepage with the search interface.

### GET /results.html
Serves the results page displaying wine recommendations.

### POST /api/recommendations

Get wine recommendations based on user preferences.

**Request Body:**
```json
{
  "description": "bold red wine for steak dinner",
  "budget_min": 20.0,
  "budget_max": 50.0,
  "food_pairing": null,
  "wine_type_pref": null
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "wine": {
        "id": "wine_123",
        "name": "Caymus Vineyards Cabernet Sauvignon",
        "producer": "Caymus Vineyards",
        "varietal": "Cabernet Sauvignon",
        "region": "Napa Valley",
        "country": "USA",
        "price_usd": 45.99,
        "characteristics": ["bold", "full-bodied", "oaky"],
        "flavor_notes": ["blackberry", "vanilla", "oak"],
        "vivino_url": "https://..."
      },
      "explanation": "This bold Napa Cabernet pairs perfectly with steak...",
      "relevance_score": 0.94
    }
  ],
  "count": 3
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

## How It Works

### Two-Agent Architecture

1. **Preference Interpreter Agent**
   - Takes natural language user input
   - Queries WSET Level 3 knowledge base
   - Generates structured search query with wine characteristics

2. **Wine Searcher Agent**
   - Performs semantic vector search in Pinecone
   - Applies price and type filters
   - Generates personalized wine recommendations
   - Returns top 3 wines with explanations

### Data Flow

```
User Input
    ↓
Preference Interpreter (GPT-4o-mini + WSET Knowledge)
    ↓
Structured Search Query
    ↓
Vector Search (Pinecone + OpenAI Embeddings)
    ↓
Wine Recommendations (with explanations)
    ↓
Display Results
```

## Features in Detail

### Dark Mode
- Toggle between light and dark themes
- Preference saved in localStorage
- Elegant color scheme for both modes

### Category Quick Filters
- Crisp Minerality
- Napa Cabs
- Natural & Funky
- Bordeaux Blends

### Loading Animation
- Animated wine glass icon
- Progressive loading messages:
  - "Curating your collection..."
  - "Analyzing regional varietals..."
  - "Matching flavor profiles..."
  - "Verifying availability..."

### Wine Card Display
Each recommendation includes:
- Wine name and producer
- Varietal and region
- Price
- Personalized "Why We Chose This" explanation
- Characteristics tags
- Flavor notes
- Direct link to Vivino

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `PINECONE_API_KEY` | Pinecone API key | Yes |
| `FLASK_DEBUG` | Debug mode (True/False) | No |
| `SECRET_KEY` | Flask secret key | No |
| `PORT` | Port to run on | No |

### Model Configuration

Edit `utils/constants.py`:
```python
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"
TEMPERATURE = 0.7
TOP_K_WINES = 5
```

## Development

### Running in Development Mode

```bash
# Enable debug mode
export FLASK_DEBUG=True
python app.py
```

### Running Tests

```bash
# Test API endpoint
curl -X POST http://localhost:5000/api/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "description": "crisp white wine for seafood",
    "budget_min": 15.0,
    "budget_max": 40.0,
    "wine_type_pref": "white"
  }'
```

### Frontend Development

The UI uses:
- **Tailwind CSS** (CDN) for styling
- **Vanilla JavaScript** for interactivity
- **Google Fonts**: Playfair Display (serif), Inter (sans-serif)
- **Material Icons** for UI elements

To modify the UI:
1. Edit templates in `templates/`
2. Modify styles in `static/css/styles.css`
3. Update JavaScript in `static/js/main.js`

## Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions for:
- Vercel (Recommended)
- Render
- Railway
- AWS Elastic Beanstalk
- Docker
- VPS (DigitalOcean, Linode, etc.)

### Quick Deploy to Vercel

```bash
npm install -g vercel
vercel
```

## Performance

### Optimization Tips

1. **Use Gunicorn in production**
```bash
gunicorn --workers 4 --threads 2 app:app
```

2. **Enable caching** for repeated queries

3. **Use CDN** for static files

4. **Monitor with Sentry** for error tracking

### Expected Response Times

- Vector search: 200-500ms
- GPT-4o-mini inference: 500-1000ms
- Total recommendation time: 1-2 seconds

## Data

### Wine Catalog

The application includes 1,500+ wines from Wine.com with:
- Full metadata (varietal, region, characteristics)
- Flavor profiles
- Pricing information
- Vivino links

### Vector Database

- **Platform**: Pinecone
- **Index**: `wine-products`
- **Dimension**: 1536 (OpenAI text-embedding-3-small)
- **Metric**: Cosine similarity

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
lsof -ti:5000 | xargs kill -9
```

**ModuleNotFoundError:**
```bash
pip install -r requirements.txt --force-reinstall
```

**API key errors:**
- Check `.env` file exists in wine-recommender directory
- Verify API keys are correct
- Ensure `.env` is loaded (python-dotenv installed)

**Static files not loading:**
- Verify file paths in templates
- Check Flask static folder configuration
- Clear browser cache

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Credits

- **Wine Data**: Wine.com
- **Purchase Links**: Vivino
- **Wine Knowledge**: WSET Level 3
- **AI Models**: OpenAI (GPT-4o-mini, text-embedding-3-small)
- **Vector Database**: Pinecone
- **UI Design**: Custom elegant design with Tailwind CSS

## Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Email: concierge@wineagent.ai

---

**Built with WSET Level 3 knowledge • Powered by OpenAI & Pinecone**
