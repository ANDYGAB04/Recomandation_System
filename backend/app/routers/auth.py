from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from ..dependencies import CurrentUserDep, SessionDep
from ..models import User, UserProfile
from ..schemas import LoginRequest, RegisterRequest, TokenResponse, UserMe, UserPublic
from ..security import DUMMY_PASSWORD_HASH, create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["conturi"])

EMAIL_TAKEN = "Există deja un cont cu acest e-mail."
BAD_CREDENTIALS = "E-mail sau parolă greșită."


def _token_response(request: Request, user: User) -> TokenResponse:
    token = create_access_token(user.id, request.app.state.settings.secret_key)
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user, from_attributes=True))


def _find_by_email(session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, request: Request, session: SessionDep) -> TokenResponse:
    """Creează contul și un profil gol, apoi întoarce direct un token."""
    if _find_by_email(session, data.email) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=EMAIL_TAKEN)

    user = User(email=data.email, password_hash=hash_password(data.password), display_name=data.display_name)
    session.add(user)
    try:
        session.flush()  # obține user.id
        session.add(UserProfile(user_id=user.id))
        session.commit()
    except IntegrityError:  # alt cont cu același e-mail creat între timp
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail=EMAIL_TAKEN) from None
    session.refresh(user)
    return _token_response(request, user)


@router.post("/login")
def login(data: LoginRequest, request: Request, session: SessionDep) -> TokenResponse:
    user = _find_by_email(session, data.email)
    # Verificăm o parolă și când contul nu există, ca răspunsul să dureze la fel.
    password_ok = verify_password(data.password, user.password_hash if user else DUMMY_PASSWORD_HASH)
    if user is None or not password_ok:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail=BAD_CREDENTIALS, headers={"WWW-Authenticate": "Bearer"}
        )
    return _token_response(request, user)


@router.get("/me")
def me(user: CurrentUserDep) -> UserMe:
    """Contul utilizatorului autentificat."""
    return UserMe.model_validate(user, from_attributes=True)
