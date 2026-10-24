from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Fortunis8 Hybrid POC")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "message": "FastAPI backend is online."}


# Preview uses one process so the frontend can demonstrate a real relative /health call.
# In the eventual hybrid publication, Webdev routes /health to this server and the SPA to static output.
frontend_dir = Path(__file__).resolve().parent.parent / "dist"
index_file = frontend_dir / "index.html"


@app.get("/dashboard", include_in_schema=False)
@app.get("/technical-poc", include_in_schema=False)
def preview_page() -> FileResponse:
    return FileResponse(index_file)


if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
