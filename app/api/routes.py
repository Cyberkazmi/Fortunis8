from fastapi import FastAPI

app = FastAPI(title="Fortunis8 API")


@app.get("/")
async def root() -> dict:
    return {"message": "Fortunis8 API is running"}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
