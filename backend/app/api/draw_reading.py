from fastapi import (
    APIRouter,
    HTTPException,
    status,
)
from sqlalchemy.exc import SQLAlchemyError

from app.adapters.agent_adapter import (
    AgentIntegrationError,
)
from app.schemas.draw_reading import (
    DrawReadingRequest,
    DrawReadingResponse,
)
from app.services.draw_reading_service import (
    DrawReadingRequestError,
    draw_reading_service,
)


router = APIRouter(
    prefix="/api/draw-and-read",
    tags=["draw-reading"],
)


@router.post(
    "",
    response_model=DrawReadingResponse,
)
def draw_and_read(
    request: DrawReadingRequest,
) -> DrawReadingResponse:
    try:
        return draw_reading_service.execute(
            question=request.question,
            spread_type=request.spread_type,
        )

    except DrawReadingRequestError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": error.error_code,
                "message": error.message,
            },
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_AGENT_REQUEST",
                "message": str(error),
            },
        ) from error

    except AgentIntegrationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "AGENT_UNAVAILABLE",
                "message": str(error),
            },
        ) from error

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DATABASE_ERROR",
                "message": "占卜结果保存失败，请稍后重试。",
            },
        ) from error
