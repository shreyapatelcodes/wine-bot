"""
Wine Recommendation Engine - Flask Application
Run with: python wine-recommender/app.py
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sys
from pathlib import Path
from typing import Dict, List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add wine-recommender directory to path for imports
wine_rec_dir = Path(__file__).parent
sys.path.insert(0, str(wine_rec_dir))

from models import UserPreferences, WineRecommendation
from agents import get_wine_recommendations

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for API requests

# Configuration
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'True') == 'True'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/results.html')
def results():
    """Serve the results page"""
    return render_template('results.html')


@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    """
    API endpoint to get wine recommendations

    Request body:
    {
        "description": "bold red wine for steak dinner",
        "budget_min": 20.0,
        "budget_max": 50.0,
        "food_pairing": null,
        "wine_type_pref": null
    }

    Response:
    {
        "recommendations": [
            {
                "wine": {...},
                "explanation": "...",
                "relevance_score": 0.92
            }
        ]
    }
    """
    try:
        # Parse request body
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        if not data.get('description'):
            return jsonify({'error': 'Description is required'}), 400

        # Create UserPreferences object
        user_prefs = UserPreferences(
            description=data.get('description'),
            budget_min=float(data.get('budget_min', 0.0)),
            budget_max=float(data.get('budget_max', 400.0)),
            food_pairing=data.get('food_pairing'),
            wine_type_pref=data.get('wine_type_pref')
        )

        # Validate budget
        if user_prefs.budget_min >= user_prefs.budget_max:
            return jsonify({'error': 'Max budget must be greater than min budget'}), 400

        # Get recommendations
        recommendations = get_wine_recommendations(
            user_prefs,
            top_n=3,
            verbose=app.config['DEBUG']
        )

        if not recommendations:
            return jsonify({
                'recommendations': [],
                'message': 'No wines found matching your criteria. Try adjusting your budget or preferences.'
            }), 200

        # Convert recommendations to dict format
        recommendations_data = []
        for rec in recommendations:
            recommendations_data.append({
                'wine': {
                    'id': rec.wine.id,
                    'name': rec.wine.name,
                    'producer': rec.wine.producer,
                    'vintage': rec.wine.vintage,
                    'wine_type': rec.wine.wine_type,
                    'varietal': rec.wine.varietal,
                    'country': rec.wine.country,
                    'region': rec.wine.region,
                    'body': rec.wine.body,
                    'sweetness': rec.wine.sweetness,
                    'acidity': rec.wine.acidity,
                    'tannin': rec.wine.tannin,
                    'characteristics': rec.wine.characteristics,
                    'flavor_notes': rec.wine.flavor_notes,
                    'description': rec.wine.description,
                    'price_usd': rec.wine.price_usd,
                    'rating': rec.wine.rating,
                    'vivino_url': rec.wine.vivino_url
                },
                'explanation': rec.explanation,
                'relevance_score': rec.relevance_score
            })

        return jsonify({
            'recommendations': recommendations_data,
            'count': len(recommendations_data)
        }), 200

    except ValueError as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        app.logger.error(f"Error getting recommendations: {str(e)}")
        return jsonify({'error': 'An error occurred while processing your request'}), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config['DEBUG']
    )
