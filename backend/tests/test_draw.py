from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_single_draw():

    response = client.post(
        "/api/draw",
        json={
            "spread_type": "single_card"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["spread_type"] == "single_card"

    assert len(data["cards"]) == 1

    assert (
        data["cards"][0]["card_id"]
        .startswith("major_")
    )


def test_three_draw():

    response = client.post(
        "/api/draw",
        json={
            "spread_type": "three_card"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["spread_type"] == "three_card"

    assert len(data["cards"]) == 3

    for card in data["cards"]:
        assert card["card_id"].startswith(
            "major_"
        )
