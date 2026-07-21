from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient

from app.config.settings import get_settings
from app.core.security import create_refresh_token
from app.database.connection import SessionLocal
from app.database.models import UserUsage
from app.dependencies.auth import get_current_user
from app.main import app


client = TestClient(app)


def test_refresh_token_cannot_access_protected_endpoint(
    mock_authenticated_user,
) -> None:
    app.dependency_overrides.pop(get_current_user, None)
    token, _ = create_refresh_token("1")
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_expired_access_token_is_rejected(mock_authenticated_user) -> None:
    app.dependency_overrides.pop(get_current_user, None)
    settings = get_settings()
    token = jwt.encode(
        {
            "sub": "1",
            "type": "access",
            "exp": datetime.now(UTC) - timedelta(seconds=1),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_free_user_reading_quota_is_enforced(mock_authenticated_user) -> None:
    user = app.dependency_overrides[get_current_user]()
    user.plan = "free"

    db = SessionLocal()
    try:
        persisted = db.get(type(user), user.id)
        persisted.plan = "free"
        usage = db.query(UserUsage).filter(UserUsage.user_id == user.id).one()
        usage.single_reading_count = get_settings().default_daily_reading_limit
        db.commit()
    finally:
        db.close()

    response = client.post(
        "/api/draw-and-read",
        json={"question": "测试额度", "spread_type": "single_card"},
    )
    assert response.status_code == 403
    assert response.json()["detail"]["error_code"] == "READING_LIMIT_REACHED"
