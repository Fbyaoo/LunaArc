from io import BytesIO

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.schemas.detection import DetectionResponse
from app.adapters.vision_adapter import VisionIntegrationError, vision_adapter
from app.config.settings import get_settings


router = APIRouter(prefix="/api/detect", tags=["detection"])

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


@router.post("", response_model=DetectionResponse)
async def detect_cards(
    file: UploadFile = File(...),
) -> DetectionResponse:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "error_code": "UNSUPPORTED_IMAGE_TYPE",
                "message": "仅支持 JPG、PNG 和 WebP 图片。",
            },
        )

    max_image_size = get_settings().max_image_size_mb * 1024 * 1024
    image_bytes = await file.read(max_image_size + 1)
    await file.close()

    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "EMPTY_IMAGE",
                "message": "上传的图片为空。",
            },
        )

    if len(image_bytes) > max_image_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error_code": "IMAGE_TOO_LARGE",
                "message": f"图片大小不能超过 {get_settings().max_image_size_mb} MB。",
            },
        )

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_IMAGE",
                "message": "文件内容不是有效图片。",
            },
        )

    filename = file.filename or "uploaded_image"

    try:
        cards = vision_adapter.detect_cards(
            image_bytes=image_bytes,
            filename=filename,
        )
    except VisionIntegrationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "VISION_UNAVAILABLE",
                "message": str(error),
            },
        ) from error

    return DetectionResponse(
        status="success",
        filename=filename,
        cards=cards,
    )
