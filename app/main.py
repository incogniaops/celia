from fastapi import FastAPI

from app.routers import auth, dashboard, sensor_log, sync, uploads

app = FastAPI(title="celia")

app.include_router(uploads.router)
app.include_router(auth.router)
app.include_router(sync.router)
app.include_router(sensor_log.router)
app.include_router(dashboard.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
