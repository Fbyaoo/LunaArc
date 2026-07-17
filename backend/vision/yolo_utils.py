from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps


def load_image_from_bytes(image_bytes: bytes) -> Image.Image:
    """Decode JPG/PNG/WebP bytes into a RGB PIL image."""
    image = Image.open(BytesIO(image_bytes))
    image = ImageOps.exif_transpose(image)
    return image.convert("RGB")


def require_model_file(model_path: str | Path) -> Path:
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(
            f"YOLO model not found: {path}. "
            "请把训练好的 best.pt 复制到 models/ 目录，并在初始化时传入正确路径。"
        )
    return path


def xyxy_to_list(value) -> list[float]:
    return [float(x) for x in value]
