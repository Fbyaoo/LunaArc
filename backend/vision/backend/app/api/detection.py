from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.detection import DetectionResponse
from app.adapters.vision_adapter import vision_adapter


router = APIRouter(prefix="/api/detect", tags=["detection"])

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

MAX_IMAGE_SIZE = 10 * 1024 * 1024


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

    image_bytes = await file.read(MAX_IMAGE_SIZE + 1)
    await file.close()

    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "EMPTY_IMAGE",
                "message": "上传的图片为空。",
            },
        )

    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error_code": "IMAGE_TOO_LARGE",
                "message": "图片大小不能超过 10 MB。",
            },
        )

    filename = file.filename or "uploaded_image"

    cards = vision_adapter.detect_cards(
        image_bytes=image_bytes,
        filename=filename,
    )

    return DetectionResponse(
        status="success",
        filename=filename,
        cards=cards,
    )
