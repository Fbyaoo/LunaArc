from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.dependencies.auth import get_current_user
from app.main import app


def test_complete_course_demo_flow(mock_authenticated_user) -> None:
    app.dependency_overrides.pop(get_current_user, None)

    with TestClient(app) as client:
        registered = client.post(
            "/api/auth/register",
            json={
                "email": f"course-{uuid.uuid4().hex}@example.com",
                "password": "CourseDemo123",
                "display_name": "Course Demo",
            },
        )
        assert registered.status_code == 200
        token = registered.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        requests = [
            {"question": None, "spread_type": "daily_card"},
            {"question": "我该关注什么？", "spread_type": "single_card"},
            {"question": "接下来如何学习？", "spread_type": "three_card"},
        ]
        for payload in requests:
            response = client.post(
                "/api/draw-and-read",
                headers=headers,
                json=payload,
            )
            assert response.status_code == 200, response.text
            assert response.json()["reading"]["status"] == "success"
            assert "Mock" not in str(response.json()["reading"])

        usage = client.get("/api/usage/me", headers=headers)
        assert usage.status_code == 200
        assert usage.json()["daily_reading_used"] == 3
        assert usage.json()["free_readings_remaining"] == 0

        history = client.get("/api/history", headers=headers)
        assert history.status_code == 200
        assert len(history.json()) == 3

        rejected = client.post(
            "/api/draw-and-read",
            headers=headers,
            json={"question": "额度外请求", "spread_type": "single_card"},
        )
        assert rejected.status_code == 403
        assert rejected.json()["detail"]["error_code"] == "READING_LIMIT_REACHED"

        refreshed = client.post("/api/auth/refresh")
        assert refreshed.status_code == 200
        refreshed_headers = {
            "Authorization": f"Bearer {refreshed.json()['access_token']}"
        }
        assert client.get("/api/users/me", headers=refreshed_headers).status_code == 200

        assert client.post("/api/auth/logout").status_code == 200
        assert client.post("/api/auth/refresh").status_code == 401
