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


TEST_PASSWORD = "TestPassword123"


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


def register_user(
    client: TestClient,
    label: str,
) -> tuple[str, str]:
    email_label = label.lower().replace(" ", "-")
    email = f"{email_label}-{uuid.uuid4().hex}@example.com"

    response = client.post(
        "/api/auth/register",
        json={
            "display_name": label,
            "email": email,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code in {
        200,
        201,
    }, response.text

    data = response.json()

    assert data["access_token"]
    assert data["user"]["email"] == email

    return email, data["access_token"]


def authorization_header(
    token: str,
) -> dict[str, str]:
    return {"Authorization": (f"Bearer {token}")}


def cleanup_user(
    email: str,
) -> None:
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.email == email).first()

        if user is None:
            return

        session_ids = [
            item[0]
            for item in (
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


def test_history_isolated_between_users(
    real_auth_client: TestClient,
) -> None:
    client = real_auth_client

    first_email: str | None = None
    second_email: str | None = None

    first_question = "这是用户 A 的私有占卜问题。"
    second_question = "这是用户 B 的私有占卜问题。"

    try:
        (
            first_email,
            first_token,
        ) = register_user(
            client,
            "Isolation User A",
        )

        (
            second_email,
            second_token,
        ) = register_user(
            client,
            "Isolation User B",
        )

        first_headers = authorization_header(first_token)

        second_headers = authorization_header(second_token)

        first_reading = client.post(
            "/api/draw-and-read",
            headers=first_headers,
            json={
                "question": first_question,
                "spread_type": ("single_card"),
            },
        )

        assert first_reading.status_code == 200, first_reading.text

        second_reading = client.post(
            "/api/draw-and-read",
            headers=second_headers,
            json={
                "question": second_question,
                "spread_type": ("single_card"),
            },
        )

        assert second_reading.status_code == 200, second_reading.text

        first_history = client.get(
            "/api/history",
            headers=first_headers,
        )

        second_history = client.get(
            "/api/history",
            headers=second_headers,
        )

        assert first_history.status_code == 200, first_history.text

        assert second_history.status_code == 200, second_history.text

        first_records = first_history.json()
        second_records = second_history.json()

        assert len(first_records) == 1
        assert len(second_records) == 1

        assert first_records[0]["question"] == first_question

        assert second_records[0]["question"] == second_question

        assert all(record["question"] != second_question for record in first_records)

        assert all(record["question"] != first_question for record in second_records)

    finally:
        if first_email is not None:
            cleanup_user(first_email)

        if second_email is not None:
            cleanup_user(second_email)
