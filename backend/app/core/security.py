import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.config.settings import get_settings


password_hash = PasswordHash.recommended()


def hash_password(password: str):
    return password_hash.hash(password)


def verify_password(
    password: str,
    hashed: str,
):
    return password_hash.verify(
        password,
        hashed,
    )


def create_access_token(
    subject: str,
):
    settings = get_settings()

    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_minutes)

    payload = {
        "sub": subject,
        "type": "access",
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(
    token: str,
):
    settings = get_settings()

    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def hash_token(token: str):
    return hashlib.sha256(token.encode()).hexdigest()


def create_refresh_token(
    subject: str,
):
    settings = get_settings()

    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_days)

    token_id = secrets.token_hex(16)

    payload = {
        "sub": subject,
        "type": "refresh",
        "jti": token_id,
        "exp": expire,
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return token, expire
