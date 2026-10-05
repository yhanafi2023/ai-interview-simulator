import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.config import settings
from app.db.session import get_db
from app.models import RefreshToken, User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserOut
from app.services.rate_limit import consume
from app.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_NAME = "refresh_token"
COOKIE_PATH = "/auth"


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session"
    )


def _issue_refresh_cookie(
    db: Session, response: Response, user: User, family_id: uuid.UUID | None = None
) -> None:
    raw, token_hash = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            family_id=family_id or uuid.uuid4(),
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
        )
    )
    response.set_cookie(
        key=COOKIE_NAME,
        value=raw,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.refresh_token_days * 24 * 60 * 60,
        path=COOKIE_PATH,
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    body: RegisterRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    existing = db.execute(select(User).where(User.email == body.email)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=body.email,
        display_name=body.display_name,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.flush()
    _issue_refresh_cookie(db, response, user)
    db.commit()
    db.refresh(user)

    return AuthResponse(
        access_token=create_access_token(str(user.id)),
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=AuthResponse)
def login(
    body: LoginRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    limit = consume(
        f"login:{body.email.lower()}",
        capacity=settings.login_bucket_capacity,
        refill_per_second=settings.login_bucket_refill_per_hour / 3600,
    )
    if not limit.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": str(limit.retry_after_seconds)},
        )
    user = db.execute(select(User).where(User.email == body.email)).scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    _issue_refresh_cookie(db, response, user)
    db.commit()
    return AuthResponse(
        access_token=create_access_token(str(user.id)),
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=AuthResponse)
def refresh_session(
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> AuthResponse:
    if refresh_token is None:
        raise _unauthorized()
    record = db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(refresh_token))
    ).scalar_one_or_none()
    if record is None:
        raise _unauthorized()
    now = datetime.now(UTC)
    if record.revoked_at is not None:
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == record.family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        db.commit()
        response.delete_cookie(COOKIE_NAME, path=COOKIE_PATH)
        raise _unauthorized()
    if record.expires_at <= now:
        raise _unauthorized()
    user = db.get(User, record.user_id)
    if user is None:
        raise _unauthorized()
    record.revoked_at = now
    _issue_refresh_cookie(db, response, user, family_id=record.family_id)
    db.commit()

    return AuthResponse(
        access_token=create_access_token(str(user.id)), user=UserOut.model_validate(user)
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> None:
    if refresh_token is not None:
        db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == hash_refresh_token(refresh_token),
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        db.commit()
        response.delete_cookie(COOKIE_NAME, path=COOKIE_PATH)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
