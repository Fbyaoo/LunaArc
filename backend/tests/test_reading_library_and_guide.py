from fastapi.testclient import TestClient

from app.main import app


def test_reading_library_detail_save_and_guide() -> None:
    with TestClient(app) as client:
        created = client.post(
            "/api/draw-and-read",
            json={"question": "我该怎样推进课程项目？", "spread_type": "single_card"},
        )
        assert created.status_code == 200, created.text
        reading = created.json()["reading"]
        reading_id = reading["reading_id"]
        assert reading_id is not None

        recent = client.get("/api/readings/recent?limit=1")
        assert recent.status_code == 200, recent.text
        assert recent.json()["items"][0]["id"] == reading_id

        listing = client.get("/api/readings?page=1&page_size=12")
        assert listing.status_code == 200, listing.text
        assert listing.json()["total"] >= 1
        assert any(item["id"] == reading_id for item in listing.json()["items"])

        detail = client.get(f"/api/readings/{reading_id}")
        assert detail.status_code == 200, detail.text
        assert detail.json()["cards"][0]["interpretation"]
        assert detail.json()["cards"][0]["keywords"]

        saved = client.patch(f"/api/readings/{reading_id}", json={"saved": True})
        assert saved.status_code == 200, saved.text
        assert saved.json()["saved"] is True
        assert saved.json()["saved_at"] is not None

        saved_list = client.get("/api/readings?saved=true")
        assert saved_list.status_code == 200, saved_list.text
        assert any(item["id"] == reading_id for item in saved_list.json()["items"])

        guide_session = client.post(
            "/api/guide/sessions", json={"reading_id": reading_id}
        )
        assert guide_session.status_code == 201, guide_session.text
        guide_session_id = guide_session.json()["session_id"]

        reply = client.post(
            f"/api/guide/sessions/{guide_session_id}/messages",
            json={"content": "我今天可以先做什么？"},
        )
        assert reply.status_code == 201, reply.text
        assert reply.json()["role"] == "assistant"

        messages = client.get(f"/api/guide/sessions/{guide_session_id}/messages")
        assert messages.status_code == 200, messages.text
        assert [item["role"] for item in messages.json()] == ["user", "assistant"]
