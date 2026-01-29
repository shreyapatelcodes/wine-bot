"""
SQLAlchemy database models for Wine App.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import (
    DeclarativeBase,
    relationship,
    sessionmaker,
    Mapped,
    mapped_column,
)

from config import Config


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class User(Base):
    """User account (OAuth-based, no passwords stored)."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)

    # OAuth fields
    oauth_provider: Mapped[str] = mapped_column(String(20), nullable=False)  # 'google' or 'apple'
    oauth_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # User preferences (JSON for flexibility)
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    saved_bottles: Mapped[list["SavedBottle"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    cellar_bottles: Mapped[list["CellarBottle"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("oauth_provider", "oauth_id", name="uq_user_oauth"),
    )


class Wine(Base):
    """
    Wine reference table.
    Synced from Pinecone/catalog for relational queries.
    """

    __tablename__ = "wines"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # Matches Pinecone ID
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    producer: Mapped[Optional[str]] = mapped_column(String(255))
    vintage: Mapped[Optional[int]] = mapped_column(Integer)
    wine_type: Mapped[str] = mapped_column(String(20), nullable=False)  # red, white, rosé, sparkling
    varietal: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    region: Mapped[Optional[str]] = mapped_column(String(100))
    price_usd: Mapped[Optional[float]] = mapped_column(Float)

    # Extended metadata (body, sweetness, acidity, tannin, characteristics, flavor_notes, etc.)
    wine_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    saved_bottles: Mapped[list["SavedBottle"]] = relationship(back_populates="wine")
    cellar_bottles: Mapped[list["CellarBottle"]] = relationship(back_populates="wine")


class SavedBottle(Base):
    """
    Saved bottles - wines from recommendations that user wants to try.
    """

    __tablename__ = "saved_bottles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    wine_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("wines.id"), nullable=False
    )

    # Context from when it was recommended
    recommendation_context: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="saved_bottles")
    wine: Mapped["Wine"] = relationship(back_populates="saved_bottles")

    __table_args__ = (
        UniqueConstraint("user_id", "wine_id", name="uq_saved_bottle_user_wine"),
    )


class CellarBottle(Base):
    """
    Cellar bottles - wines user owns or has tried.
    Supports both catalog wines and custom entries (from image recognition or manual).
    """

    __tablename__ = "cellar_bottles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Link to catalog wine (NULL for custom entries)
    wine_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("wines.id"), nullable=True
    )

    # Custom wine fields (for wines not in our catalog)
    custom_wine_name: Mapped[Optional[str]] = mapped_column(String(255))
    custom_wine_producer: Mapped[Optional[str]] = mapped_column(String(255))
    custom_wine_vintage: Mapped[Optional[int]] = mapped_column(Integer)
    custom_wine_type: Mapped[Optional[str]] = mapped_column(String(20))
    custom_wine_varietal: Mapped[Optional[str]] = mapped_column(String(100))
    custom_wine_region: Mapped[Optional[str]] = mapped_column(String(100))
    custom_wine_country: Mapped[Optional[str]] = mapped_column(String(100))
    custom_wine_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Cellar status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="owned"
    )  # 'owned', 'tried'
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    # Purchase info
    purchase_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    purchase_price: Mapped[Optional[float]] = mapped_column(Float)
    purchase_location: Mapped[Optional[str]] = mapped_column(String(255))

    # Tasting notes (for 'tried' status)
    rating: Mapped[Optional[float]] = mapped_column(Float)  # 1-5 scale
    tasting_notes: Mapped[Optional[str]] = mapped_column(Text)
    tried_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Image recognition data
    image_url: Mapped[Optional[str]] = mapped_column(Text)
    image_recognition_data: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Timestamps
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="cellar_bottles")
    wine: Mapped[Optional["Wine"]] = relationship(back_populates="cellar_bottles")

    __table_args__ = (
        Index("idx_cellar_user_status", "user_id", "status"),
    )


class ChatSession(Base):
    """Chat session for conversation history."""

    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )  # NULL for anonymous sessions

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Session context (cellar summary, preferences, etc.)
    context: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    """Individual chat message."""

    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False
    )

    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Metadata (recommendations returned, wines mentioned, etc.)
    message_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    session: Mapped["ChatSession"] = relationship(back_populates="messages")

    __table_args__ = (
        Index("idx_messages_session", "session_id", "created_at"),
    )


class UserTasteProfile(Base):
    """
    User taste profile derived from ratings and interactions.
    Used for personalized recommendations.
    """

    __tablename__ = "user_taste_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    # Preferred wine types (weighted by ratings)
    preferred_types: Mapped[Optional[dict]] = mapped_column(JSONB)  # {"red": 0.7, "white": 0.3}

    # Preferred regions/countries
    preferred_regions: Mapped[Optional[list]] = mapped_column(JSONB)  # ["Napa Valley", "Bordeaux"]
    preferred_countries: Mapped[Optional[list]] = mapped_column(JSONB)  # ["France", "Italy"]

    # Preferred varietals
    preferred_varietals: Mapped[Optional[list]] = mapped_column(JSONB)  # ["Cabernet Sauvignon", "Pinot Noir"]

    # Price preferences
    price_range_min: Mapped[Optional[float]] = mapped_column(Float)
    price_range_max: Mapped[Optional[float]] = mapped_column(Float)

    # Flavor profile preferences (derived from highly-rated wines)
    flavor_profile: Mapped[Optional[dict]] = mapped_column(JSONB)
    # e.g., {"body": "full", "sweetness": "dry", "preferred_notes": ["cherry", "oak"]}

    # Stats
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    average_rating: Mapped[Optional[float]] = mapped_column(Float)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship(backref="taste_profile")


# Database session factory
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Alias for backwards compatibility
db = SessionLocal
