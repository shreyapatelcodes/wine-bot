"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ============== Auth Schemas ==============

class GoogleAuthRequest(BaseModel):
    """Request body for Google OAuth login."""
    id_token: str = Field(..., description="Google ID token from client")


class AppleAuthRequest(BaseModel):
    """Request body for Apple Sign-In."""
    id_token: str = Field(..., description="Apple ID token from client")
    user_name: Optional[str] = Field(None, description="User name (only sent on first auth)")


class TokenResponse(BaseModel):
    """Response with JWT tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Request body for token refresh."""
    refresh_token: str


# ============== User Schemas ==============

class UserProfile(BaseModel):
    """User profile response."""
    id: UUID
    email: EmailStr
    display_name: Optional[str]
    avatar_url: Optional[str]
    oauth_provider: str
    created_at: datetime
    preferences: dict = Field(default_factory=dict)

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """Request body for updating user profile."""
    display_name: Optional[str] = None
    preferences: Optional[dict] = None


# ============== Wine Schemas ==============

class WineBase(BaseModel):
    """Base wine schema."""
    id: str
    name: str
    producer: Optional[str]
    vintage: Optional[int]
    wine_type: Literal["red", "white", "rosé", "sparkling"]
    varietal: Optional[str]
    country: Optional[str]
    region: Optional[str]
    price_usd: Optional[float]
    wine_metadata: dict = Field(default_factory=dict)

    class Config:
        from_attributes = True


class WineSearchResult(BaseModel):
    """Wine search result with relevance score."""
    wine: WineBase
    relevance_score: float


# ============== Saved Bottles Schemas ==============

class SavedBottleCreate(BaseModel):
    """Request body for saving a bottle."""
    wine_id: str
    recommendation_context: Optional[str] = None
    notes: Optional[str] = None


class SavedBottleResponse(BaseModel):
    """Saved bottle response."""
    id: UUID
    wine: WineBase
    recommendation_context: Optional[str]
    notes: Optional[str]
    saved_at: datetime

    class Config:
        from_attributes = True


# ============== Cellar Schemas ==============

class CellarBottleCreate(BaseModel):
    """Request body for adding a bottle to cellar."""
    wine_id: Optional[str] = None  # NULL for custom entries

    # Custom wine fields
    custom_wine_name: Optional[str] = None
    custom_wine_producer: Optional[str] = None
    custom_wine_vintage: Optional[int] = None
    custom_wine_type: Optional[Literal["red", "white", "rosé", "sparkling"]] = None
    custom_wine_metadata: Optional[dict] = None

    # Cellar info
    status: Literal["owned", "tried", "wishlist"] = "owned"
    quantity: int = 1
    purchase_date: Optional[datetime] = None
    purchase_price: Optional[float] = None
    purchase_location: Optional[str] = None

    # Image data (from vision recognition)
    image_url: Optional[str] = None
    image_recognition_data: Optional[dict] = None


class CellarBottleUpdate(BaseModel):
    """Request body for updating a cellar bottle."""
    status: Optional[Literal["owned", "tried", "wishlist"]] = None
    quantity: Optional[int] = None
    rating: Optional[float] = Field(None, ge=1, le=5)
    tasting_notes: Optional[str] = None
    tried_date: Optional[datetime] = None
    notes: Optional[str] = None


class CellarBottleResponse(BaseModel):
    """Cellar bottle response."""
    id: UUID
    wine: Optional[WineBase]
    custom_wine_name: Optional[str]
    custom_wine_producer: Optional[str]
    custom_wine_vintage: Optional[int]
    custom_wine_type: Optional[str]
    custom_wine_metadata: Optional[dict]
    status: str
    quantity: int
    purchase_date: Optional[datetime]
    purchase_price: Optional[float]
    purchase_location: Optional[str]
    rating: Optional[float]
    tasting_notes: Optional[str]
    tried_date: Optional[datetime]
    image_url: Optional[str]
    added_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Recommendation Schemas ==============

class RecommendationRequest(BaseModel):
    """Request body for wine recommendations."""
    description: str = Field(..., description="Natural language description of what you're looking for")
    budget_min: Optional[float] = Field(None, ge=0)
    budget_max: Optional[float] = Field(None, ge=0)
    wine_type_pref: Optional[Literal["red", "white", "rosé", "sparkling"]] = None
    food_pairing: Optional[str] = None
    from_cellar: bool = Field(False, description="Recommend from user's cellar only")


class WineRecommendation(BaseModel):
    """A single wine recommendation."""
    wine: WineBase
    explanation: str
    relevance_score: float
    is_saved: bool = False
    is_in_cellar: bool = False


class RecommendationResponse(BaseModel):
    """Response with wine recommendations."""
    recommendations: list[WineRecommendation]
    count: int


# ============== Vision Schemas ==============

class VisionAnalyzeRequest(BaseModel):
    """Request body for image analysis."""
    image: str = Field(..., description="Base64-encoded image data")


class VisionAnalyzeResponse(BaseModel):
    """Response from vision analysis."""
    name: Optional[str]
    producer: Optional[str]
    vintage: Optional[int]
    wine_type: Optional[str]
    varietal: Optional[str]
    region: Optional[str]
    country: Optional[str]
    additional_info: Optional[str]
    confidence: float = Field(..., ge=0, le=1)


class VisionMatchResponse(BaseModel):
    """Response from vision matching."""
    analysis: VisionAnalyzeResponse
    matches: list[WineSearchResult]
    best_match: Optional[WineBase]
