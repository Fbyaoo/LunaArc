from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_daily_card_draw() -> None:
    response = client.post(
        "/api/draw",
        json={
            "spread_type": "daily_card",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["spread_type"] == "daily_card"
    assert len(data["cards"]) == 1
    assert data["cards"][0]["position"] == "1"


def test_single_card_draw() -> None:
    response = client.post(
        "/api/draw",
        json={
            "spread_type": "single_card",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["spread_type"] == "single_card"
    assert len(data["cards"]) == 1
    assert data["cards"][0]["position"] == "1"


def test_three_card_draw() -> None:
    response = client.post(
        "/api/draw",
        json={
            "spread_type": "three_card",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["spread_type"] == "three_card"
    assert len(data["cards"]) == 3

    positions = [
        card["position"]
        for card in data["cards"]
    ]

    assert positions == [
        "1",
        "2",
        "3",
    ]
