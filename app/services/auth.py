from datetime import UTC, datetime

import jwt
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.auth import RegisterRequest, TokenResponse


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repository = UserRepository(session)
        self.refresh_token_repository = RefreshTokenRepository(session)

    async def register(self, payload: RegisterRequest) -> User:
        email = str(payload.email).lower()

        existing_user = await self.user_repository.get_by_email(email)

        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            email=email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            role="MEMBER",
            is_active=True,
        )

        try:
            return await self.user_repository.create(user)
        except IntegrityError:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

    async def login(
        self,
        email: str,
        password: str,
    ) -> TokenResponse:
        normalized_email = email.lower()
        user = await self.user_repository.get_by_email(normalized_email)

        if user is None or not verify_password(
            password,
            user.hashed_password,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )

        access_token = create_access_token(user.id)
        refresh_token, jti = create_refresh_token(user.id)

        refresh_payload = decode_token(refresh_token)
        expires_at = datetime.fromtimestamp(
            refresh_payload["exp"],
            tz=UTC,
        )

        try:
            await self.refresh_token_repository.create_for_user(
                user_id=user.id,
                jti=jti,
                expires_at=expires_at,
            )
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    @staticmethod
    def _parse_refresh_token(token: str) -> tuple[int, str]:
        try:
            payload = decode_token(token)

            if payload.get("type") != "refresh":
                raise ValueError("Incorrect token type")

            user_id = int(payload["sub"])
            jti = payload["jti"]

            if not isinstance(jti, str) or not jti:
                raise ValueError("Missing jti")

            return user_id, jti

        except (
            jwt.InvalidTokenError,
            KeyError,
            TypeError,
            ValueError,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None

    async def refresh(
        self,
        refresh_token: str,
    ) -> TokenResponse:
        user_id, old_jti = self._parse_refresh_token(refresh_token)

        stored_token = await self.refresh_token_repository.get_active_by_jti(
            old_jti,
            for_update=True,
        )

        if stored_token is None or stored_token.user_id != user_id:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is revoked or expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await self.user_repository.get(user_id)

        if user is None or not user.is_active:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is inactive or does not exist",
                headers={"WWW-Authenticate": "Bearer"},
            )

        new_access_token = create_access_token(user.id)
        new_refresh_token, new_jti = create_refresh_token(user.id)

        new_refresh_payload = decode_token(new_refresh_token)
        new_expires_at = datetime.fromtimestamp(
            new_refresh_payload["exp"],
            tz=UTC,
        )

        try:
            self.refresh_token_repository.revoke(stored_token)

            await self.refresh_token_repository.create_for_user(
                user_id=user.id,
                jti=new_jti,
                expires_at=new_expires_at,
            )

            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )

    async def logout(
        self,
        refresh_token: str,
    ) -> None:
        user_id, jti = self._parse_refresh_token(refresh_token)

        stored_token = await self.refresh_token_repository.get_active_by_jti(
            jti,
            for_update=True,
        )

        if stored_token is None:
            await self.session.rollback()
            return

        if stored_token.user_id != user_id:
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            self.refresh_token_repository.revoke(stored_token)
            await self.session.commit()
        except SQLAlchemyError:
            await self.session.rollback()
            raise
