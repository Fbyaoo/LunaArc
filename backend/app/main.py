from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.gesture import router as gesture_router
from app.api.draw import router as draw_router
from app.api.draw_reading import router as draw_reading_router

from app.api.auth import router as auth_router
from app.api.users import router as users_router

from app.api.subscriptions import router as subscriptions_router

from app.api.usage import router as usage_router

from app.api.cards import router as cards_router
from app.api.detection import router as detection_router
from app.api.readings import router as readings_router
from app.api.clarify import router as clarify_router
from app.api.history import router as history_router
from app.config.settings import get_settings


settings = get_settings()
settings.validate_runtime()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(users_router)

app.include_router(subscriptions_router)

app.include_router(usage_router)

app.include_router(cards_router)

app.include_router(detection_router)
app.include_router(readings_router)
app.include_router(clarify_router)
app.include_router(history_router)
app.include_router(gesture_router)
app.include_router(draw_router)
app.include_router(draw_reading_router)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
