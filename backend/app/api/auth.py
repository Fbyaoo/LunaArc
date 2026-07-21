from datetime import datetime, UTC

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
)

from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.auth_service import (
    register_user,
    login_user,
    create_refresh_session,
)

from app.database.models import (
    User,
    RefreshSession,
)

from app.core.security import (
    create_access_token,
    decode_token,
    hash_token,
)
from app.config.settings import get_settings


from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
)


def _set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key="lunaarc_refresh_token",
        value=token,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        max_age=settings.refresh_token_days * 24 * 60 * 60,
        path="/api/auth",
    )


@router.post("/refresh")
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    token = request.cookies.get("lunaarc_refresh_token")

    if not token:
        raise HTTPException(
            401,
            {
                "error_code": "REFRESH_TOKEN_EXPIRED",
                "message": "登录状态已过期，请重新登录。",
            },
        )

    session = (
        db.query(RefreshSession)
        .filter(RefreshSession.token_hash == hash_token(token))
        .first()
    )

    try:
        payload = decode_token(token)
        valid_token = payload.get("type") == "refresh"
    except Exception:
        valid_token = False

    now = datetime.now(UTC)
    expires_at = session.expires_at if session is not None else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    if (
        session is None
        or session.revoked
        or not valid_token
        or expires_at is None
        or expires_at <= now
    ):
        raise HTTPException(
            401,
            {
                "error_code": "REFRESH_TOKEN_EXPIRED",
                "message": "登录状态已过期，请重新登录。",
            },
        )

    user = db.query(User).filter(User.id == session.user_id).first()

    if user is None or user.status != "active":
        raise HTTPException(401, {"error_code": "UNAUTHORIZED"})

    revoked = (
        db.query(RefreshSession)
        .filter(
            RefreshSession.id == session.id,
            RefreshSession.revoked.is_(False),
        )
        .update(
            {RefreshSession.revoked: True},
            synchronize_session=False,
        )
    )
    if revoked != 1:
        db.rollback()
        raise HTTPException(
            401,
            {
                "error_code": "REFRESH_TOKEN_EXPIRED",
                "message": "登录状态已过期，请重新登录。",
            },
        )

    new_access = create_access_token(str(user.id))

    new_refresh = create_refresh_session(db, user)

    _set_refresh_cookie(response, new_refresh)

    db.commit()

    return {
        "access_token": new_access,
        "token_type": "bearer",
        "expires_in": get_settings().access_token_minutes * 60,
    }


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    token = request.cookies.get("lunaarc_refresh_token")

    if token:
        item = (
            db.query(RefreshSession)
            .filter(RefreshSession.token_hash == hash_token(token))
            .first()
        )

        if item:
            item.revoked = True

            db.commit()

    response.delete_cookie("lunaarc_refresh_token", path="/api/auth")

    return {"status": "ok"}


@router.post("/register")
def register(
    body: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        user = register_user(
            db,
            body.email,
            body.password,
            body.display_name,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail={
                "error_code": str(error),
                "message": "邮箱已经注册。",
            },
        )

    token = create_access_token(str(user.id))

    refresh_token = create_refresh_session(
        db,
        user,
    )

    _set_refresh_cookie(response, refresh_token)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "plan": user.plan,
        },
    }


@router.post("/login")
def login(
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        user = login_user(
            db,
            body.email,
            body.password,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": str(error),
                "message": "邮箱或密码错误。",
            },
        )

    token = create_access_token(str(user.id))

    refresh_token = create_refresh_session(
        db,
        user,
    )

    _set_refresh_cookie(response, refresh_token)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "plan": user.plan,
        },
    }
