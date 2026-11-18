
import base64
import hashlib
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

ACCESS_TOKEN_LIFETIME = timedelta(days=7)
JWT_ALGORITHM = "HS256"


def _bcrypt_input(password: str) -> bytes:
    return base64.b64encode(hashlib.sha256(password.encode("utf-8")).digest())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_bcrypt_input(password), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_bcrypt_input(password), password_hash.encode("ascii"))
    except ValueError:  
        return False


DUMMY_PASSWORD_HASH = hash_password("parola-inexistenta")


def _signing_key(secret_key: str) -> bytes:
    return hashlib.sha256(secret_key.encode("utf-8")).digest()


def create_access_token(user_id: int, secret_key: str, now: datetime | None = None) -> str:
    issued_at = now or datetime.now(UTC)
    payload = {"sub": str(user_id), "iat": issued_at, "exp": issued_at + ACCESS_TOKEN_LIFETIME}
    return jwt.encode(payload, _signing_key(secret_key), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str, secret_key: str) -> int | None:
    try:
        payload = jwt.decode(
            token, _signing_key(secret_key), algorithms=[JWT_ALGORITHM], options={"require": ["sub", "exp"]}
        )
        return int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError):
        return None
