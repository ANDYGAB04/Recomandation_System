"""Dependențe FastAPI comune tuturor rutelor."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlmodel import Session

from .db import session_scope


def get_session(request: Request) -> Iterator[Session]:
    yield from session_scope(request.app.state.engine)


SessionDep = Annotated[Session, Depends(get_session)]
