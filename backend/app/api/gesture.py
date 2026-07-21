from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)


from app.adapters.gesture_adapter import (
    gesture_adapter,
)

from app.services.gesture_service import (
    gesture_service,
)


router = APIRouter()


@router.websocket("/ws/gesture")
async def gesture_ws(
    websocket: WebSocket,
):
    await websocket.accept()
    event_engine = gesture_service.create_event_engine()

    try:
        while True:
            image_bytes = await websocket.receive_bytes()

            try:
                events = gesture_service.process_frame(
                    image_bytes,
                    event_engine=event_engine,
                )
            except Exception as error:
                await websocket.send_json(
                    {
                        "error": {
                            "error_code": "VISION_UNAVAILABLE",
                            "message": str(error),
                        }
                    }
                )
                await websocket.close(code=1011)
                return

            for event in events:
                action = gesture_adapter.convert(event.gesture)

                await websocket.send_json(
                    {
                        "gesture": event.model_dump(),
                        "action": action.model_dump(),
                    }
                )
    except WebSocketDisconnect:
        return
