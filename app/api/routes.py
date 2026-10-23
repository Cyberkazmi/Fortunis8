from fastapi import FastAPI

from app.config import settings

app = FastAPI(title="Fortunis8 API")


@app.get("/")
async def root() -> dict:
    return {"message": "Fortunis8 API is running"}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict:
    settings.reload()
    missing = []
    if not settings.TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")

    if missing:
        return {"status": "not_ready", "missing": missing}
    return {"status": "ready"}
