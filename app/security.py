"""Хэширование паролей и подписанные токены сессии (только стандартная библиотека)."""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

SECRET_KEY = os.getenv("SECRET_KEY", "bookstore-dev-secret-change-me")
TOKEN_TTL = 8 * 60 * 60  # рабочая смена
PBKDF2_ITERATIONS = 200_000

ROLE_ADMIN = "Администратор"
ROLE_MANAGER = "Менеджер"
ROLE_SELLER = "Продавец"


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt, expected = stored.split("$")
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations))
    return hmac.compare_digest(digest.hex(), expected)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _sign(payload: str) -> str:
    return _b64(hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).digest())


def create_token(user_id: int) -> str:
    payload = _b64(json.dumps({"uid": user_id, "exp": int(time.time()) + TOKEN_TTL}).encode())
    return f"{payload}.{_sign(payload)}"


def read_token(token: str) -> int | None:
    try:
        payload, signature = token.split(".")
    except ValueError:
        return None
    if not hmac.compare_digest(signature, _sign(payload)):
        return None
    data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    if data["exp"] < time.time():
        return None
    return data["uid"]


def current_user(
    authorization: str | None = Header(default=None), db: Session = Depends(get_db)
) -> User | None:
    """Пользователь из заголовка Authorization; None означает гостя."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    user_id = read_token(authorization.removeprefix("Bearer "))
    if user_id is None:
        raise HTTPException(401, "Сессия истекла, войдите снова")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(401, "Пользователь не найден")
    return user


def require_roles(*roles: str):
    def checker(user: User | None = Depends(current_user)) -> User:
        if user is None:
            raise HTTPException(401, "Требуется авторизация")
        if user.role.name not in roles:
            raise HTTPException(403, "Недостаточно прав для этого действия")
        return user

    return checker
