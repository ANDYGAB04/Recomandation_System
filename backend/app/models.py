
from datetime import UTC, datetime

from sqlalchemy import JSON, CheckConstraint, Column, Index
from sqlmodel import Field, SQLModel

from .vocabulary import EventType


def utc_now() -> datetime:
    return datetime.now(UTC)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=254)
    password_hash: str
    display_name: str = Field(max_length=100)
    created_at: datetime = Field(default_factory=utc_now)


class UserProfile(SQLModel, table=True):

    __tablename__ = "user_profiles"

    user_id: int = Field(foreign_key="users.id", primary_key=True, ondelete="CASCADE")
    activities: dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    level: str | None = None
    styles: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    season: str | None = None
    max_budget: float | None = Field(default=None, gt=0)
    updated_at: datetime = Field(default_factory=utc_now)

    __table_args__ = (CheckConstraint("max_budget IS NULL OR max_budget > 0", name="ck_profile_budget"),)


class Product(SQLModel, table=True):
    __tablename__ = "products"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=200)
    category: str = Field(index=True)
    usages: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    levels: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    styles: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    seasons: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    description: str = ""
    price: float
    available: bool = True
    is_test_data: bool = True

    __table_args__ = (CheckConstraint("price >= 0", name="ck_product_price"),)


class Interaction(SQLModel, table=True):
    __tablename__ = "interactions"

    id: int | None = Field(default=None, primary_key=True)
    event_id: str = Field(unique=True, max_length=64)
    user_id: int = Field(foreign_key="users.id", ondelete="CASCADE")
    product_id: int = Field(foreign_key="products.id")
    type: str
    created_at: datetime = Field(default_factory=utc_now)

    __table_args__ = (
        CheckConstraint(
            "type IN (" + ", ".join(f"'{t.value}'" for t in EventType) + ")",
            name="ck_interaction_type",
        ),
        Index("ix_interactions_user_time", "user_id", "created_at"),
        Index("ix_interactions_type_product", "type", "product_id"),
    )


class Favorite(SQLModel, table=True):

    __tablename__ = "favorites"

    user_id: int = Field(foreign_key="users.id", primary_key=True, ondelete="CASCADE")
    product_id: int = Field(foreign_key="products.id", primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)


class RecommendationFeedback(SQLModel, table=True):

    __tablename__ = "recommendation_feedback"

    user_id: int = Field(foreign_key="users.id", primary_key=True, ondelete="CASCADE")
    product_id: int = Field(foreign_key="products.id", primary_key=True)
    useful: bool
    strategy: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    __table_args__ = (
        CheckConstraint("strategy IN ('personalized', 'popular')", name="ck_feedback_strategy"),
    )


class SurveyResponse(SQLModel, table=True):

    __tablename__ = "survey_responses"

    id: int | None = Field(default=None, primary_key=True)
    answers: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=utc_now)
    is_test_data: bool = False


class SurveyParticipant(SQLModel, table=True):

    __tablename__ = "survey_participants"

    user_id: int = Field(foreign_key="users.id", primary_key=True, ondelete="CASCADE")
