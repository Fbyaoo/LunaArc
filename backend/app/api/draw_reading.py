from sqlalchemy.orm import Session

from fastapi import (
    Depends,
    APIRouter,
    HTTPException,
    status,
)
from sqlalchemy.exc import SQLAlchemyError

from app.adapters.agent_adapter import (
    AgentIntegrationError,
)
from app.dependencies.auth import get_current_user
from app.database.models import User
from app.database.connection import get_db

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DrawReadingResponse:
    try:
        return draw_reading_service.execute(
            question=request.question,
            spread_type=request.spread_type,
            user=current_user,
            db=db,
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
