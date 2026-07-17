from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def three_cards():

    return [
        {
            "card_id": "major_00",
            "name_zh": "愚者",
            "position_number": 1,
            "orientation": "upright",
        },
        {
            "card_id": "major_01",
            "name_zh": "魔术师",
            "position_number": 2,
            "orientation": "upright",
        },
        {
            "card_id": "major_02",
            "name_zh": "女祭司",
            "position_number": 3,
            "orientation": "upright",
        },
    ]


def test_create_three_card_reading():

    response = client.post(
        "/api/readings",
        json={
            "question": "我是否适合接受这份实习？",
            "spread_type": "three_card",
            "cards": three_cards(),
            "user_history": None,
        },
    )

    assert response.status_code == 200

    assert response.json()["status"] == "success"


def test_reject_incomplete_draw():

    response = client.post(
        "/api/readings",
        json={
            "question": "测试",
            "spread_type": "three_card",
            "cards": [
                {
                    "card_id": "major_00",
                    "name_zh": "愚者",
                    "position_number": 1,
                    "orientation": "upright",
                }
            ],
            "user_history": None,
        },
    )

    assert response.status_code == 400


def test_reading_contains_tarot_context():

    response = client.post(
        "/api/readings",
        json={
            "question": "新的尝试是否值得？",
            "spread_type": "three_card",
            "cards": three_cards(),
            "user_history": None,
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert "开始" in str(result)
