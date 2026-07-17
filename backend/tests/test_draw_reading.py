from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_draw_and_read():

    response = client.post(
        "/api/draw-and-read",
        json={
            "question": "我适合接受这份实习吗？",
            "spread_type": "three_card",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["cards"]) == 3

    assert (
        data["reading"]["status"]
        == "success"
    )
