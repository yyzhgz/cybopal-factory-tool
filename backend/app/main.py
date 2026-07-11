import asyncio

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.deps import calibration_service
from app.routers.calibration import router as calibration_router

app = FastAPI(title="CyboPal Factory Tool API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(calibration_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws/calibration/logs")
async def calibration_logs(websocket: WebSocket):
    await websocket.accept()
    service = calibration_service()
    try:
        while True:
            await websocket.send_json(
                {"logs": [item.__dict__ for item in service.logs()]}
            )
            await asyncio.sleep(1)
    except Exception:
        await websocket.close()
