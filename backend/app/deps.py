from functools import lru_cache

from app.core.config import Settings, get_settings
from app.services.calibration_service import CalibrationService
from app.services.log_service import LogService
from app.ssh.asyncssh_service import AsyncSSHService
from app.ssh.mock_ssh_service import MockSSHService


@lru_cache
def settings() -> Settings:
    return get_settings()


@lru_cache
def log_service() -> LogService:
    return LogService()


@lru_cache
def calibration_service() -> CalibrationService:
    app_settings = settings()
    ssh_client = MockSSHService() if app_settings.ssh_mock else AsyncSSHService(app_settings)
    return CalibrationService(app_settings, ssh_client, log_service())

