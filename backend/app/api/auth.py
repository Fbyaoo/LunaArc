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

from app.dependencies.auth import (
    get_current_user,
)

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
)



@router.post("/refresh")
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):

    token = request.cookies.get(
        "lunaarc_refresh_token"
    )


    if not token:

        raise HTTPException(
            401,
            {
                "error_code":
                "REFRESH_TOKEN_EXPIRED",
                "message":
                "登录状态已过期，请重新登录。",
            }
        )


    session = (
        db.query(
            RefreshSession
        )
        .filter(
            RefreshSession.token_hash
            ==
            hash_token(token)
        )
        .first()
    )


    if (
        session is None
        or session.revoked
    ):

        raise HTTPException(
            401,
            {
                "error_code":
                "REFRESH_TOKEN_EXPIRED",
                "message":
                "登录状态已过期，请重新登录。",
            }
        )


    user = (
        db.query(User)
        .filter(
            User.id
            ==
            session.user_id
        )
        .first()
    )


    if user is None:

        raise HTTPException(
            401,
            {
                "error_code":
                "UNAUTHORIZED"
            }
        )


    session.revoked=True


    new_access = create_access_token(
        str(user.id)
    )


    db.commit()


    return {

        "access_token":
            new_access,


        "token_type":
            "bearer",


        "expires_in":
            1800,

    }



@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):

    token=request.cookies.get(
        "lunaarc_refresh_token"
    )


    if token:

        item=(
            db.query(
                RefreshSession
            )
            .filter(
                RefreshSession.token_hash
                ==
                hash_token(token)
            )
            .first()
        )

        if item:

            item.revoked=True

            db.commit()


    response.delete_cookie(
        "lunaarc_refresh_token"
    )


    return {
        "status":"ok"
    }


@router.post("/register")
def register(
    body: RegisterRequest,
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


    token = create_access_token(
        str(user.id)
    )


    refresh_token = create_refresh_session(
        db,
        user,
    )


    response.set_cookie(
        key="lunaarc_refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
    )


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


    token = create_access_token(
        str(user.id)
    )


    refresh_token = create_refresh_session(
        db,
        user,
    )


    response.set_cookie(
        key="lunaarc_refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
    )


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

