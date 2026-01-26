"""
Wine App API - Flask application with authentication and wine management.
"""

import sys
from datetime import timedelta
from pathlib import Path
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required as flask_jwt_required,
)

from config import Config
from auth.jwt import jwt, create_tokens, jwt_required, jwt_optional
from auth.oauth import google_auth
from models.database import (
    SessionLocal,
    User,
    Wine,
    SavedBottle,
    CellarBottle,
)
from models.schemas import (
    GoogleAuthRequest,
    UserProfile,
    UserProfileUpdate,
    SavedBottleCreate,
    CellarBottleCreate,
    CellarBottleUpdate,
    CellarBottleResponse,
    RecommendationRequest,
)

# Wine recommender path for lazy loading
_wine_recommender_path = Path(__file__).parent.parent.parent / "wine-recommender"
_recommender_engine = None
_recommender_prefs_class = None


def _get_recommender():
    """Lazy load the wine recommender to avoid module conflicts."""
    global _recommender_engine, _recommender_prefs_class
    if _recommender_engine is None:
        import importlib.util

        # Save current modules that might conflict
        saved_modules = {}
        for mod_name in list(sys.modules.keys()):
            if mod_name == 'models' or mod_name.startswith('models.'):
                saved_modules[mod_name] = sys.modules.pop(mod_name)
            if mod_name == 'config' or mod_name.startswith('config.'):
                saved_modules[mod_name] = sys.modules.pop(mod_name)

        # Add wine-recommender to path
        sys.path.insert(0, str(_wine_recommender_path))

        try:
            # Load wine-recommender's modules fresh
            from agents.orchestrator import get_wine_recommendations
            from models.schemas import UserPreferences
            _recommender_engine = get_wine_recommendations
            _recommender_prefs_class = UserPreferences
        finally:
            # Remove wine-recommender from path
            if str(_wine_recommender_path) in sys.path:
                sys.path.remove(str(_wine_recommender_path))

            # Restore wine-app's modules
            for mod_name, mod in saved_modules.items():
                sys.modules[mod_name] = mod

    return _recommender_engine, _recommender_prefs_class


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Configuration
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(seconds=Config.JWT_REFRESH_TOKEN_EXPIRES)

    # Initialize extensions
    CORS(app, origins=["http://localhost:5173", Config.WEB_URL])
    jwt.init_app(app)

    # ============== Health Check ==============

    @app.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint."""
        return jsonify({"status": "healthy"})

    # ============== Auth Endpoints ==============

    @app.route("/api/v1/auth/google", methods=["POST"])
    def auth_google():
        """Authenticate with Google OAuth."""
        try:
            data = GoogleAuthRequest(**request.json)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

        user, is_new = google_auth(data.id_token)
        if not user:
            return jsonify({"error": "Authentication failed"}), 401

        tokens = create_tokens(user)
        return jsonify({
            **tokens,
            "user": UserProfile.model_validate(user).model_dump(mode="json"),
            "is_new_user": is_new,
        })

    @app.route("/api/v1/auth/refresh", methods=["POST"])
    @flask_jwt_required(refresh=True)
    def auth_refresh():
        """Refresh access token using refresh token."""
        user_id = get_jwt_identity()

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({"error": "User not found"}), 401

            tokens = create_tokens(user)
            return jsonify(tokens)
        finally:
            db.close()

    @app.route("/api/v1/auth/logout", methods=["POST"])
    @jwt_required
    def auth_logout():
        """Logout (client should discard tokens)."""
        # In a production app, you might want to blacklist the token
        return jsonify({"message": "Logged out successfully"})

    # ============== User Endpoints ==============

    @app.route("/api/v1/users/me", methods=["GET"])
    @jwt_required
    def get_current_user():
        """Get current user profile."""
        user = g.current_user
        return jsonify(UserProfile.model_validate(user).model_dump(mode="json"))

    @app.route("/api/v1/users/me", methods=["PATCH"])
    @jwt_required
    def update_current_user():
        """Update current user profile."""
        try:
            data = UserProfileUpdate(**request.json)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

        user = g.current_user
        db = g.db

        if data.display_name is not None:
            user.display_name = data.display_name
        if data.preferences is not None:
            user.preferences = {**user.preferences, **data.preferences}

        db.commit()
        db.refresh(user)

        return jsonify(UserProfile.model_validate(user).model_dump(mode="json"))

    @app.route("/api/v1/users/me", methods=["DELETE"])
    @jwt_required
    def delete_current_user():
        """Delete current user account."""
        user = g.current_user
        db = g.db

        db.delete(user)
        db.commit()

        return jsonify({"message": "Account deleted successfully"})

    # ============== Saved Bottles Endpoints ==============

    @app.route("/api/v1/saved-bottles", methods=["GET"])
    @jwt_required
    def list_saved_bottles():
        """List user's saved bottles."""
        user = g.current_user
        db = g.db

        bottles = db.query(SavedBottle).filter(
            SavedBottle.user_id == user.id
        ).order_by(SavedBottle.saved_at.desc()).all()

        return jsonify({
            "bottles": [
                {
                    "id": str(b.id),
                    "wine": {
                        "id": b.wine.id,
                        "name": b.wine.name,
                        "producer": b.wine.producer,
                        "vintage": b.wine.vintage,
                        "wine_type": b.wine.wine_type,
                        "varietal": b.wine.varietal,
                        "country": b.wine.country,
                        "region": b.wine.region,
                        "price_usd": b.wine.price_usd,
                        "metadata": b.wine.wine_metadata,
                    },
                    "recommendation_context": b.recommendation_context,
                    "notes": b.notes,
                    "saved_at": b.saved_at.isoformat(),
                }
                for b in bottles
            ],
            "count": len(bottles),
        })

    @app.route("/api/v1/saved-bottles", methods=["POST"])
    @jwt_required
    def save_bottle():
        """Save a bottle from recommendations."""
        try:
            data = SavedBottleCreate(**request.json)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

        user = g.current_user
        db = g.db

        # Check if wine exists
        wine = db.query(Wine).filter(Wine.id == data.wine_id).first()
        if not wine:
            return jsonify({"error": "Wine not found"}), 404

        # Check if already saved
        existing = db.query(SavedBottle).filter(
            SavedBottle.user_id == user.id,
            SavedBottle.wine_id == data.wine_id,
        ).first()
        if existing:
            return jsonify({"error": "Wine already saved"}), 409

        # Create saved bottle
        saved = SavedBottle(
            user_id=user.id,
            wine_id=data.wine_id,
            recommendation_context=data.recommendation_context,
            notes=data.notes,
        )
        db.add(saved)
        db.commit()
        db.refresh(saved)

        return jsonify({
            "id": str(saved.id),
            "message": "Bottle saved successfully",
        }), 201

    @app.route("/api/v1/saved-bottles/<bottle_id>", methods=["DELETE"])
    @jwt_required
    def delete_saved_bottle(bottle_id):
        """Remove a saved bottle."""
        user = g.current_user
        db = g.db

        bottle = db.query(SavedBottle).filter(
            SavedBottle.id == bottle_id,
            SavedBottle.user_id == user.id,
        ).first()

        if not bottle:
            return jsonify({"error": "Saved bottle not found"}), 404

        db.delete(bottle)
        db.commit()

        return jsonify({"message": "Saved bottle removed"})

    @app.route("/api/v1/saved-bottles/<bottle_id>/to-cellar", methods=["POST"])
    @jwt_required
    def move_to_cellar(bottle_id):
        """Move a saved bottle to cellar."""
        user = g.current_user
        db = g.db

        saved = db.query(SavedBottle).filter(
            SavedBottle.id == bottle_id,
            SavedBottle.user_id == user.id,
        ).first()

        if not saved:
            return jsonify({"error": "Saved bottle not found"}), 404

        # Check if already in cellar
        existing = db.query(CellarBottle).filter(
            CellarBottle.user_id == user.id,
            CellarBottle.wine_id == saved.wine_id,
        ).first()

        if existing:
            # Increment quantity
            existing.quantity += 1
            db.delete(saved)
            db.commit()
            return jsonify({
                "cellar_bottle_id": str(existing.id),
                "message": "Added to existing cellar entry",
            })

        # Create cellar bottle
        cellar = CellarBottle(
            user_id=user.id,
            wine_id=saved.wine_id,
            status="owned",
            quantity=1,
        )
        db.add(cellar)
        db.delete(saved)
        db.commit()
        db.refresh(cellar)

        return jsonify({
            "cellar_bottle_id": str(cellar.id),
            "message": "Moved to cellar",
        }), 201

    # ============== Cellar Endpoints ==============

    @app.route("/api/v1/cellar", methods=["GET"])
    @jwt_required
    def list_cellar():
        """List user's cellar bottles."""
        user = g.current_user
        db = g.db

        status_filter = request.args.get("status")

        query = db.query(CellarBottle).filter(CellarBottle.user_id == user.id)

        if status_filter:
            query = query.filter(CellarBottle.status == status_filter)

        bottles = query.order_by(CellarBottle.added_at.desc()).all()

        return jsonify({
            "bottles": [
                {
                    "id": str(b.id),
                    "wine": {
                        "id": b.wine.id,
                        "name": b.wine.name,
                        "producer": b.wine.producer,
                        "vintage": b.wine.vintage,
                        "wine_type": b.wine.wine_type,
                        "varietal": b.wine.varietal,
                        "country": b.wine.country,
                        "region": b.wine.region,
                        "price_usd": b.wine.price_usd,
                        "metadata": b.wine.wine_metadata,
                    } if b.wine else None,
                    "custom_wine_name": b.custom_wine_name,
                    "custom_wine_producer": b.custom_wine_producer,
                    "custom_wine_vintage": b.custom_wine_vintage,
                    "custom_wine_type": b.custom_wine_type,
                    "custom_wine_metadata": b.custom_wine_metadata,
                    "status": b.status,
                    "quantity": b.quantity,
                    "purchase_date": b.purchase_date.isoformat() if b.purchase_date else None,
                    "purchase_price": b.purchase_price,
                    "purchase_location": b.purchase_location,
                    "rating": b.rating,
                    "tasting_notes": b.tasting_notes,
                    "tried_date": b.tried_date.isoformat() if b.tried_date else None,
                    "image_url": b.image_url,
                    "added_at": b.added_at.isoformat(),
                    "updated_at": b.updated_at.isoformat(),
                }
                for b in bottles
            ],
            "count": len(bottles),
        })

    @app.route("/api/v1/cellar", methods=["POST"])
    @jwt_required
    def add_to_cellar():
        """Add a bottle to cellar."""
        try:
            data = CellarBottleCreate(**request.json)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

        user = g.current_user
        db = g.db

        # Validate: either wine_id or custom wine info required
        if not data.wine_id and not data.custom_wine_name:
            return jsonify({"error": "Either wine_id or custom_wine_name required"}), 400

        # If wine_id provided, verify it exists
        if data.wine_id:
            wine = db.query(Wine).filter(Wine.id == data.wine_id).first()
            if not wine:
                return jsonify({"error": "Wine not found"}), 404

        # Create cellar bottle
        cellar = CellarBottle(
            user_id=user.id,
            wine_id=data.wine_id,
            custom_wine_name=data.custom_wine_name,
            custom_wine_producer=data.custom_wine_producer,
            custom_wine_vintage=data.custom_wine_vintage,
            custom_wine_type=data.custom_wine_type,
            custom_wine_metadata=data.custom_wine_metadata,
            status=data.status,
            quantity=data.quantity,
            purchase_date=data.purchase_date,
            purchase_price=data.purchase_price,
            purchase_location=data.purchase_location,
            image_url=data.image_url,
            image_recognition_data=data.image_recognition_data,
        )
        db.add(cellar)
        db.commit()
        db.refresh(cellar)

        return jsonify({
            "id": str(cellar.id),
            "message": "Added to cellar",
        }), 201

    @app.route("/api/v1/cellar/<bottle_id>", methods=["GET"])
    @jwt_required
    def get_cellar_bottle(bottle_id):
        """Get a specific cellar bottle."""
        user = g.current_user
        db = g.db

        bottle = db.query(CellarBottle).filter(
            CellarBottle.id == bottle_id,
            CellarBottle.user_id == user.id,
        ).first()

        if not bottle:
            return jsonify({"error": "Cellar bottle not found"}), 404

        return jsonify(CellarBottleResponse.model_validate(bottle).model_dump(mode="json"))

    @app.route("/api/v1/cellar/<bottle_id>", methods=["PATCH"])
    @jwt_required
    def update_cellar_bottle(bottle_id):
        """Update a cellar bottle."""
        try:
            data = CellarBottleUpdate(**request.json)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

        user = g.current_user
        db = g.db

        bottle = db.query(CellarBottle).filter(
            CellarBottle.id == bottle_id,
            CellarBottle.user_id == user.id,
        ).first()

        if not bottle:
            return jsonify({"error": "Cellar bottle not found"}), 404

        # Update fields
        for field in ["status", "quantity", "rating", "tasting_notes", "tried_date"]:
            value = getattr(data, field)
            if value is not None:
                setattr(bottle, field, value)

        db.commit()
        db.refresh(bottle)

        return jsonify({"message": "Cellar bottle updated"})

    @app.route("/api/v1/cellar/<bottle_id>", methods=["DELETE"])
    @jwt_required
    def delete_cellar_bottle(bottle_id):
        """Remove a bottle from cellar."""
        user = g.current_user
        db = g.db

        bottle = db.query(CellarBottle).filter(
            CellarBottle.id == bottle_id,
            CellarBottle.user_id == user.id,
        ).first()

        if not bottle:
            return jsonify({"error": "Cellar bottle not found"}), 404

        db.delete(bottle)
        db.commit()

        return jsonify({"message": "Removed from cellar"})

    # ============== Wine Search Endpoint ==============

    @app.route("/api/v1/wines/search", methods=["GET"])
    @jwt_optional
    def search_wines():
        """Search wine catalog."""
        query = request.args.get("q", "")
        limit = min(int(request.args.get("limit", 20)), 100)

        if not query:
            return jsonify({"wines": [], "count": 0})

        db = g.db

        # Simple search by name/producer/varietal
        wines = db.query(Wine).filter(
            Wine.name.ilike(f"%{query}%") |
            Wine.producer.ilike(f"%{query}%") |
            Wine.varietal.ilike(f"%{query}%")
        ).limit(limit).all()

        return jsonify({
            "wines": [
                {
                    "id": w.id,
                    "name": w.name,
                    "producer": w.producer,
                    "vintage": w.vintage,
                    "wine_type": w.wine_type,
                    "varietal": w.varietal,
                    "country": w.country,
                    "region": w.region,
                    "price_usd": w.price_usd,
                    "metadata": w.wine_metadata,
                }
                for w in wines
            ],
            "count": len(wines),
        })

    # ============== Recommendations Endpoint ==============

    @app.route("/api/v1/recommendations", methods=["POST"])
    @jwt_optional
    def get_recommendations():
        """Get wine recommendations using the wine-recommender engine."""
        try:
            data = RecommendationRequest(**request.json)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

        # Lazy load the recommender engine
        get_recommendations_from_engine, UserPreferences = _get_recommender()

        # Convert to wine-recommender's UserPreferences format
        user_prefs = UserPreferences(
            description=data.description,
            budget_min=data.budget_min or 10.0,
            budget_max=data.budget_max or 200.0,
            food_pairing=data.food_pairing,
            wine_type_pref=data.wine_type_pref,
        )

        try:
            # Get recommendations from the engine
            recommendations = get_recommendations_from_engine(user_prefs, top_n=3)
        except Exception as e:
            return jsonify({"error": f"Recommendation engine error: {str(e)}"}), 500

        # Get user's saved/cellar wine IDs for status flags
        saved_wine_ids = set()
        cellar_wine_ids = set()
        user = getattr(g, 'current_user', None)
        if user:
            db = g.db
            saved_wine_ids = {
                sb.wine_id for sb in
                db.query(SavedBottle).filter(SavedBottle.user_id == user.id).all()
            }
            cellar_wine_ids = {
                cb.wine_id for cb in
                db.query(CellarBottle).filter(CellarBottle.user_id == user.id).all()
                if cb.wine_id
            }

        # Map recommendations to response format
        response_recs = []
        for rec in recommendations:
            wine = rec.wine
            response_recs.append({
                "wine": {
                    "id": wine.id,
                    "name": wine.name,
                    "producer": wine.producer,
                    "vintage": wine.vintage,
                    "wine_type": wine.wine_type,
                    "varietal": wine.varietal,
                    "country": wine.country,
                    "region": wine.region,
                    "price_usd": wine.price_usd,
                    "metadata": {
                        "body": wine.body,
                        "sweetness": wine.sweetness,
                        "acidity": wine.acidity,
                        "tannin": wine.tannin,
                        "characteristics": wine.characteristics,
                        "flavor_notes": wine.flavor_notes,
                    },
                },
                "explanation": rec.explanation,
                "relevance_score": rec.relevance_score,
                "is_saved": wine.id in saved_wine_ids,
                "is_in_cellar": wine.id in cellar_wine_ids,
            })

        return jsonify({
            "recommendations": response_recs,
            "count": len(response_recs),
        })

    # ============== Error Handlers ==============

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    # Validate configuration
    missing = Config.validate()
    if missing:
        print(f"Warning: Missing configuration: {', '.join(missing)}")

    app.run(debug=Config.DEBUG, port=5001)
