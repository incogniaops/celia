from fastapi import FastAPI

from app.routers import uploads

app = FastAPI(title="celia")

app.include_router(uploads.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
