from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.database.connection import SessionLocal
from app.database.models import (
    DrawnCard,
    Reading,
    RefreshSession,
    Session as TarotSession,
    Subscription,
    User,
    UserUsage,
)
from app.dependencies.auth import get_current_user
from app.main import app


@pytest.fixture
def real_auth_client(
    mock_authenticated_user,
):
    app.dependency_overrides.pop(
        get_current_user,
        None,
    )

    with TestClient(app) as client:
        yield client


def cleanup_account(
    email: str,
) -> None:
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.email == email).first()

        if user is None:
            return

        session_ids = [
            row[0]
            for row in (
                db.query(TarotSession.id).filter(TarotSession.user_id == user.id).all()
            )
        ]

        if session_ids:
            (
                db.query(Reading)
                .filter(Reading.session_id.in_(session_ids))
                .delete(synchronize_session=False)
            )

            (
                db.query(DrawnCard)
                .filter(DrawnCard.session_id.in_(session_ids))
                .delete(synchronize_session=False)
            )

            (
                db.query(TarotSession)
                .filter(TarotSession.id.in_(session_ids))
                .delete(synchronize_session=False)
            )

        (
            db.query(RefreshSession)
            .filter(RefreshSession.user_id == user.id)
            .delete(synchronize_session=False)
        )

        (
            db.query(UserUsage)
            .filter(UserUsage.user_id == user.id)
            .delete(synchronize_session=False)
        )

        (
            db.query(Subscription)
            .filter(Subscription.user_id == user.id)
            .delete(synchronize_session=False)
        )

        db.delete(user)
        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def test_complete_auth_lifecycle(
    real_auth_client: TestClient,
) -> None:
    client = real_auth_client

    email = f"auth-{uuid.uuid4().hex}@example.com"
    password = "Test123456"

    try:
        unauthorized = client.get("/api/users/me")

        assert unauthorized.status_code in {
            401,
            403,
        }

        registered = client.post(
            "/api/auth/register",
            json={
                "display_name": "Auth Test",
                "email": email,
                "password": password,
            },
        )

        assert registered.status_code in {
            200,
            201,
        }

        registered_data = registered.json()

        assert registered_data["access_token"]
        assert registered_data["token_type"] == "bearer"
        assert registered_data["user"]["email"] == email
        assert registered_data["user"]["plan"] == "free"

        assert "lunaarc_refresh_token" in registered.headers.get(
            "set-cookie",
            "",
        )

        duplicate = client.post(
            "/api/auth/register",
            json={
                "display_name": "Duplicate",
                "email": email,
                "password": password,
            },
        )

        assert duplicate.status_code == 409
        assert duplicate.json()["detail"]["error_code"] == "EMAIL_ALREADY_REGISTERED"

        wrong_password = client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": "WrongPassword123",
            },
        )

        assert wrong_password.status_code == 401
        assert wrong_password.json()["detail"]["error_code"] == "INVALID_CREDENTIALS"

        logged_in = client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

        assert logged_in.status_code == 200

        login_data = logged_in.json()
        access_token = login_data["access_token"]

        assert access_token
        assert login_data["user"]["email"] == email
        refresh_before_rotation = client.cookies.get("lunaarc_refresh_token")

        headers = {"Authorization": (f"Bearer {access_token}")}

        current_user = client.get(
            "/api/users/me",
            headers=headers,
        )

        assert current_user.status_code == 200

        current_user_data = current_user.json()

        assert current_user_data["email"] == email
        assert current_user_data["display_name"] == "Auth Test"
        assert current_user_data["plan"] == "free"

        subscription = client.get(
            "/api/subscriptions/me",
            headers=headers,
        )

        assert subscription.status_code == 200
        assert subscription.json()["plan"] == "free"

        usage = client.get(
            "/api/usage/me",
            headers=headers,
        )

        assert usage.status_code == 200
        assert usage.json()["daily_reading_used"] == 0
        assert usage.json()["free_readings_remaining"] == 3

        refreshed = client.post("/api/auth/refresh")

        assert refreshed.status_code == 200

        refreshed_data = refreshed.json()

        assert refreshed_data["access_token"]
        assert refreshed_data["token_type"] == "bearer"
        assert refreshed_data["expires_in"] > 0
        assert client.cookies.get("lunaarc_refresh_token") != refresh_before_rotation

        with TestClient(app) as replay_client:
            replay_client.cookies.set(
                "lunaarc_refresh_token",
                refresh_before_rotation,
                path="/api/auth",
            )
            replayed = replay_client.post("/api/auth/refresh")
        assert replayed.status_code == 401

        refreshed_headers = {
            "Authorization": ("Bearer " + refreshed_data["access_token"])
        }

        refreshed_me = client.get(
            "/api/users/me",
            headers=refreshed_headers,
        )

        assert refreshed_me.status_code == 200
        assert refreshed_me.json()["email"] == email

        rotated_again = client.post("/api/auth/refresh")
        assert rotated_again.status_code == 200
        assert rotated_again.json()["access_token"]

        logged_out = client.post(
            "/api/auth/logout",
            headers=refreshed_headers,
        )

        assert logged_out.status_code == 200
        assert logged_out.json()["status"] == "ok"

        refresh_after_logout = client.post("/api/auth/refresh")

        assert refresh_after_logout.status_code == 401
        assert (
            refresh_after_logout.json()["detail"]["error_code"]
            == "REFRESH_TOKEN_EXPIRED"
        )

    finally:
        cleanup_account(email)
