"""Dependențe FastAPI comune tuturor rutelor."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from .db import session_scope
from .models import User
from .security import decode_access_token


def get_session(request: Request) -> Iterator[Session]:
    yield from session_scope(request.app.state.engine)


SessionDep = Annotated[Session, Depends(get_session)]

# auto_error=False: răspundem noi cu 401 (FastAPI ar întoarce 403 când lipsește antetul).
bearer_scheme = HTTPBearer(auto_error=False, description="Token-ul primit de la /auth/register sau /auth/login")


def get_current_user(
    request: Request,
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    """Utilizatorul autentificat, din antetul `Authorization: Bearer <token>`; altfel 401."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Trebuie să te autentifici.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    user_id = decode_access_token(credentials.credentials, request.app.state.settings.secret_key)
    user = session.get(User, user_id) if user_id is not None else None
    if user is None:
        raise unauthorized
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def get_optional_user(
    request: Request,
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User | None:
    """Utilizatorul autentificat, dacă cererea are token; None fără token. Un token invalid dă tot 401."""
    if credentials is None:
        return None
    return get_current_user(request, session, credentials)


OptionalUserDep = Annotated[User | None, Depends(get_optional_user)]
