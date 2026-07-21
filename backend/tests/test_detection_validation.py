from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


client = TestClient(app)


def png_bytes() -> bytes:
    output = BytesIO()
    Image.new("RGB", (2, 2), "white").save(output, format="PNG")
    return output.getvalue()


def test_detect_rejects_fake_image_content() -> None:
    response = client.post(
        "/api/detect",
        files={"file": ("fake.png", b"not an image", "image/png")},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == "INVALID_IMAGE"


def test_detect_filters_low_confidence_results() -> None:
    response = client.post(
        "/api/detect",
        files={"file": ("low.png", png_bytes(), "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["cards"] == []


def test_detect_accepts_valid_image() -> None:
    response = client.post(
        "/api/detect",
        files={"file": ("card.png", png_bytes(), "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["cards"][0]["card_id"] == "major_00"
