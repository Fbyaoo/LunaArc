
from fastapi import (
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
