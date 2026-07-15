from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.cards import router as cards_router
from app.api.readings import router as readings_router


app = FastAPI(
    title="LunaArc Backend",
    version="0.1.0",
)

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cards_router)
app.include_router(readings_router)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
