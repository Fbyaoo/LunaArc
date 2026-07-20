
from fastapi import (
    Response,
    Request,
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
)

from app.services.auth_service import (
    register_user,
    login_user,
    create_refresh_session,
    revoke_refresh_session,
)

from app.core.security import (
    create_access_token,
)



router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
)



@router.post(
    "/register",
    response_model=TokenResponse,
)
def register(
    body:RegisterRequest,
    response: Response,
    db:Session=Depends(get_db),
):

    try:

        user = register_user(
            db,
            body.email,
            body.password,
            body.display_name,
        )

    except ValueError as e:

        raise HTTPException(
            409,
            {
                "error_code":str(e),
            }
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

        "access_token":token,

        "token_type":"bearer",

        "user":{

            "id":user.id,

            "email":user.email,

            "display_name":
                user.display_name,

            "plan":
                user.plan,
        }
    }



@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    body:LoginRequest,
    db:Session=Depends(get_db),
):

    try:

        user = login_user(
            db,
            body.email,
            body.password,
        )

    except ValueError as e:

        raise HTTPException(
            401,
            {
                "error_code":str(e),
            }
        )


    token = create_access_token(
        str(user.id)
    )


    return {

        "access_token":token,

        "token_type":"bearer",

        "user":{

            "id":user.id,

            "email":user.email,

            "display_name":
                user.display_name,

            "plan":
                user.plan,
        }
    }


from app.core.security import (
    decode_token,
)


@router.post("/refresh")
def refresh(
    request: Request,
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
                "REFRESH_TOKEN_EXPIRED"
            }
        )


    payload = decode_token(
        token
    )


    new_token = create_access_token(
        payload["sub"]
    )


    return {

        "access_token":
            new_token,

        "token_type":
            "bearer",
    }



@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):

    token = request.cookies.get(
        "lunaarc_refresh_token"
    )


    if token:

        revoke_refresh_session(
            db,
            token,
        )


    response.delete_cookie(
        "lunaarc_refresh_token"
    )


    return {
        "status":"ok"
    }
