from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_cards() -> None:
    response = client.get("/api/cards")

    assert response.status_code == 200

    cards = response.json()

    # 大阿尔卡纳共22张
    assert len(cards) == 22

    # 第一张：愚者
    assert cards[0]["card_id"] == "major_00"
    assert cards[0]["class_id"] == 0
    assert cards[0]["name_zh"] == "愚者"
    assert cards[0]["arcana"] == "major"

    assert cards[0]["core_symbolism"] == [
        "开始",
        "冒险",
        "自由",
        "未知"
    ]
    # 最后一张：世界
    assert cards[-1]["card_id"] == "major_21"
    assert cards[-1]["class_id"] == 21
    assert cards[-1]["name_zh"] == "世界"


def test_create_single_card_reading() -> None:
    response = client.post(
        "/api/readings",
        json={
            "question": "我是否适合接受这份实习？",
            "spread_type": "single_card",
            "cards": [
                {
                    "card_id": "major_00",
                    "name_zh": "愚者",
                    "position": "core",
                    "orientation": "upright",
                }
            ],
            "user_history": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_reject_empty_question() -> None:
    response = client.post(
        "/api/readings",
        json={
            "question": "   ",
            "spread_type": "single_card",
            "cards": [
                {
                    "card_id": "major_00",
                    "name_zh": "愚者",
                    "position": "core",
                    "orientation": "upright",
                }
            ],
            "user_history": None,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == "EMPTY_QUESTION"


def test_reject_incomplete_three_card_draw() -> None:
    response = client.post(
        "/api/readings",
        json={
            "question": "我接下来应该如何规划实习？",
            "spread_type": "three_card",
            "cards": [
                {
                    "card_id": "major_00",
                    "name_zh": "愚者",
                    "position": "past",
                    "orientation": "upright",
                }
            ],
            "user_history": None,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == "INCOMPLETE_DRAW"


def test_reject_unsupported_image_type() -> None:
    response = client.post(
        "/api/detect",
        files={
            "file": (
                "test.txt",
                b"not an image",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415
    assert (
        response.json()["detail"]["error_code"]
        == "UNSUPPORTED_IMAGE_TYPE"
    )

def test_detect_no_card():
    response = client.post(
        "/api/detect",
        files={
            "file": (
                "none.jpg",
                b"fake image",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["cards"] == []


def test_detect_multiple_cards():
    response = client.post(
        "/api/detect",
        files={
            "file": (
                "multi.jpg",
                b"fake image",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 200

    cards = response.json()["cards"]

    assert len(cards) == 2
    assert cards[0]["card_id"] == "major_00"
    assert cards[1]["card_id"] == "major_01"

def test_reading_contains_tarot_context():
    response = client.post(
        "/api/readings",
        json={
            "question": "我是否适合开始新的尝试？",
            "spread_type": "single_card",
            "cards": [
                {
                    "card_id": "major_00",
                    "name_zh": "愚者",
                    "position": "core",
                    "orientation": "upright",
                }
            ],
            "user_history": None,
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["status"] == "success"

    interpretation = (
        result["card_readings"][0]["interpretation"]
    )

    # 验证 Agent 收到了 tarot_cards.json 的信息
    assert "开始" in interpretation
    assert "冒险" in interpretation