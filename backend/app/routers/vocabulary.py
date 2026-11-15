from fastapi import APIRouter

from ..vocabulary import VOCABULARY_KEYS, options

router = APIRouter(tags=["sistem"])


@router.get("/vocabulary")
def get_vocabulary() -> dict[str, list[dict[str, str]]]:
    """Valorile permise pentru profil, produse și interacțiuni, cu etichetele lor în română."""
    return {key: options(enum) for key, enum in VOCABULARY_KEYS.items()}
