
from sqlalchemy.orm import Session

from app.database.models import User

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)


def register_user(
    db: Session,
    email: str,
    password: str,
    display_name: str,
):

    exists = (
        db.query(User)
        .filter(
            User.email == email
        )
        .first()
    )


    if exists:

        raise ValueError(
            "EMAIL_ALREADY_REGISTERED"
        )


    user = User(

        email=email,

        password_hash=
            hash_password(password),

        display_name=
            display_name,

        plan="free",

        status="active",
    )


    db.add(user)

    db.commit()

    db.refresh(user)


    return user



def login_user(
    db: Session,
    email: str,
    password: str,
):

    user = (
        db.query(User)
        .filter(
            User.email == email
        )
        .first()
    )


    if (
        user is None
        or not verify_password(
            password,
            user.password_hash,
        )
    ):

        raise ValueError(
            "INVALID_CREDENTIALS"
        )


    return user


from datetime import datetime

from app.core.security import (
    create_refresh_token,
    hash_token,
)

from app.database.models import (
    RefreshSession,
)



def create_refresh_session(
    db,
    user,
):

    token, expire = (
        create_refresh_token(
            str(user.id)
        )
    )


    session = RefreshSession(

        user_id=user.id,

        token_hash=
            hash_token(token),

        expires_at=expire,

    )


    db.add(session)

    db.commit()


    return token



def revoke_refresh(
    db,
    token,
):

    item = (
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



def revoke_refresh_session(
    db,
    token,
):

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


    if session:

        session.revoked = True

        db.commit()

