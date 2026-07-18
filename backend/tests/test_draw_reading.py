from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def history_count() -> int:
    response = client.get(
        "/api/history"
    )

    assert response.status_code == 200

    return len(response.json())


def test_daily_card_draw_and_read() -> None:
    before = history_count()

    response = client.post(
        "/api/draw-and-read",
        json={
            "question": None,
            "spread_type": "daily_card",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["cards"]) == 1
    assert data["cards"][0]["position"] == "1"
    assert data["reading"]["status"] == "success"

    assert history_count() == before + 1


def test_single_card_draw_and_read() -> None:
    before = history_count()

    response = client.post(
        "/api/draw-and-read",
        json={
            "question": "我现在最需要关注什么？",
            "spread_type": "single_card",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["cards"]) == 1
    assert data["cards"][0]["position"] == "1"
    assert data["reading"]["status"] == "success"

    assert history_count() == before + 1


def test_three_card_draw_and_read() -> None:
    before = history_count()

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

    assert [
        card["position"]
        for card in data["cards"]
    ] == [
        "1",
        "2",
        "3",
    ]

    assert data["reading"]["status"] == "success"

    assert history_count() == before + 1


def test_single_card_rejects_empty_question() -> None:
    before = history_count()

    response = client.post(
        "/api/draw-and-read",
        json={
            "question": "   ",
            "spread_type": "single_card",
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["error_code"]
        == "EMPTY_QUESTION"
    )

    assert history_count() == before


def test_three_card_rejects_empty_question() -> None:
    before = history_count()

    response = client.post(
        "/api/draw-and-read",
        json={
            "question": None,
            "spread_type": "three_card",
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]["error_code"]
        == "EMPTY_QUESTION"
    )

    assert history_count() == before
