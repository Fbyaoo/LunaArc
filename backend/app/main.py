from fastapi import FastAPI

from app.api.cards import router as cards_router
from app.api.readings import router as readings_router


app = FastAPI(
    title="LunaArc Backend",
    version="0.1.0",
)

app.include_router(cards_router)
app.include_router(readings_router)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
