
from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User
from app.core.security import decode_token


security = HTTPBearer()


def get_current_user(
    credentials:
    HTTPAuthorizationCredentials
    = Depends(security),

    db: Session
    = Depends(get_db),
):

    try:

        payload = decode_token(
            credentials.credentials
        )

    except Exception:

        raise HTTPException(
            status_code=
            status.HTTP_401_UNAUTHORIZED,

            detail={
                "error_code":
                "UNAUTHORIZED",

                "message":
                "请重新登录。"
            }
        )


    user_id = int(
        payload["sub"]
    )


    user = (
        db.query(User)
        .filter(
            User.id == user_id
        )
        .first()
    )


    if user is None:

        raise HTTPException(
            status_code=401,
            detail={
                "error_code":
                "UNAUTHORIZED"
            }
        )


    return user
