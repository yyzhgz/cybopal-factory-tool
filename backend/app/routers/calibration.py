from fastapi import APIRouter, Depends

from app.deps import calibration_service
from app.schemas.calibration import ControlRequest
from app.services.calibration_service import CalibrationService

router = APIRouter(prefix="/api/calibration", tags=["calibration"])


@router.post("/connect")
async def connect(service: CalibrationService = Depends(calibration_service)):
    return (await service.connect_device()).to_dict()


@router.post("/prepare")
async def prepare(service: CalibrationService = Depends(calibration_service)):
    return (await service.prepare_environment()).to_dict()


@router.post("/start")
async def start(service: CalibrationService = Depends(calibration_service)):
    return (await service.start_calibration_tool()).to_dict()


@router.post("/restart")
async def restart(service: CalibrationService = Depends(calibration_service)):
    return (await service.restart_calibration_tool()).to_dict()


@router.post("/recover")
async def recover(service: CalibrationService = Depends(calibration_service)):
    return (await service.try_recover_tool()).to_dict()


@router.get("/status")
async def status(service: CalibrationService = Depends(calibration_service)):
    return service.tool_status().to_dict()


@router.post("/control")
async def control(
    payload: ControlRequest,
    service: CalibrationService = Depends(calibration_service),
):
    return (await service.send_control(payload.action)).to_dict()


@router.post("/finish")
async def finish(service: CalibrationService = Depends(calibration_service)):
    return (await service.finish_calibration()).to_dict()


@router.post("/stop")
async def stop(service: CalibrationService = Depends(calibration_service)):
    return (await service.stop_tool()).to_dict()


@router.get("/logs")
async def logs(service: CalibrationService = Depends(calibration_service)):
    return {"logs": [item.__dict__ for item in service.logs()]}
