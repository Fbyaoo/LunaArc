from fastapi import APIRouter, WebSocket

from app.adapters.gesture_adapter import gesture_adapter
from app.services.gesture_service import gesture_service
from app.services.workflow_service import tarot_workflow


router = APIRouter()


@router.websocket("/ws/gesture")
async def gesture_ws(
    websocket: WebSocket,
):

    await websocket.accept()


    while True:

        image_bytes = (
            await websocket.receive_bytes()
        )


        events = (
            gesture_service
            .process_frame(image_bytes)
        )


        for event in events:

            action = (
                gesture_adapter
                .convert(event.gesture)
            )


            workflow_result = (
                tarot_workflow
                .handle_action(
                    action.action
                )
            )


            await websocket.send_json(
                {
                    "gesture": event.model_dump(),
                    "action": action.model_dump(),
                    "workflow": workflow_result,
                }
            )
