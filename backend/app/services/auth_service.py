
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
