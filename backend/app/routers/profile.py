from fastapi import APIRouter
from sqlmodel import Session

from ..dependencies import CurrentUserDep, SessionDep
from ..models import User, UserProfile, utc_now
from ..schemas import ProfileIn, ProfileOut

router = APIRouter(prefix="/profile", tags=["profil"])


def get_or_create_profile(session: Session, user: User) -> UserProfile:
    """Profilul utilizatorului; îl creează gol dacă lipsește (de exemplu, un cont mai vechi decât profilurile)."""
    profile = session.get(UserProfile, user.id)
    if profile is None:
        profile = UserProfile(user_id=user.id)
        session.add(profile)
        session.commit()
        session.refresh(profile)
    return profile


def to_out(profile: UserProfile) -> ProfileOut:
    return ProfileOut(
        activities=dict(profile.activities),
        level=profile.level,
        styles=list(profile.styles),
        season=profile.season,
        max_budget=profile.max_budget,
        is_complete=bool(profile.activities),
        updated_at=profile.updated_at,
    )


@router.get("")
def get_profile(user: CurrentUserDep, session: SessionDep) -> ProfileOut:
    """Setările de profil ale utilizatorului autentificat."""
    return to_out(get_or_create_profile(session, user))


@router.put("")
def put_profile(data: ProfileIn, user: CurrentUserDep, session: SessionDep) -> ProfileOut:
    """Înlocuiește toate setările de profil ale utilizatorului autentificat."""
    profile = get_or_create_profile(session, user)
    profile.activities = {activity.value: intensity.value for activity, intensity in data.activities.items()}
    profile.level = data.level.value if data.level else None
    profile.styles = [style.value for style in data.styles]
    profile.season = data.season.value if data.season else None
    profile.max_budget = data.max_budget
    profile.updated_at = utc_now()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return to_out(profile)
