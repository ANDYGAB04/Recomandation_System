"""Formatul JSON al cererilor și răspunsurilor API (vezi docs/api.md)."""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field, PlainSerializer, StringConstraints


def _as_utc(value: datetime) -> datetime:
    # SQLite nu păstrează fusul orar; momentele salvate sunt mereu în UTC.
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


# Moment în UTC, scris ca "2026-11-15T14:30:00Z".
UtcDatetime = Annotated[
    datetime,
    AfterValidator(_as_utc),
    PlainSerializer(lambda v: _as_utc(v).isoformat(timespec="seconds").replace("+00:00", "Z"), return_type=str),
]

Email = Annotated[EmailStr, AfterValidator(str.lower)]


# ---------- Conturi ----------


class RegisterRequest(BaseModel):
    email: Email
    password: str = Field(min_length=8, max_length=256)
    display_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class LoginRequest(BaseModel):
    email: Email
    password: str = Field(min_length=1, max_length=256)


class UserPublic(BaseModel):
    id: int
    email: str
    display_name: str


class UserMe(UserPublic):
    created_at: UtcDatetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
