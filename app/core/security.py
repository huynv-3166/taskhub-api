from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import uuid4

import jwt
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from app.core.config import settings

TokenType = Literal["access", "refresh"]

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash password using recommended algorithm."""
    return password_hash.hash(password)


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    """Trả về False nếu password sai hoặc hash không được hỗ trợ."""
    try:
        return password_hash.verify(
            password,
            hashed_password,
        )
    except UnknownHashError:
        return False


def create_token(
    user_id: int,
    token_type: TokenType,
    expires_delta: timedelta,
    jti: str | None = None,
) -> str:
    """Tạo JWT đã được ký bằng secret của server."""
    now = datetime.now(UTC)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }

    if jti is not None:
        payload["jti"] = jti

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_access_token(user_id: int) -> str:
    """Tạo access token dùng để gọi API."""
    return create_token(
        user_id=user_id,
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: int) -> tuple[str, str]:
    """Tạo refresh token và trả về cả token lẫn jti."""
    jti = str(uuid4())

    token = create_token(
        user_id=user_id,
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        jti=jti,
    )

    return token, jti


def decode_token(token: str) -> dict[str, Any]:
    """Xác minh chữ ký, hạn sử dụng và trả về JWT payload."""
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        options={
            "require": ["sub", "type", "iat", "exp"],
        },
    )
