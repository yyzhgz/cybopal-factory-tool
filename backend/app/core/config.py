from dataclasses import dataclass
import os


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    device_host: str = os.getenv("CYBOPAL_DEVICE_HOST", "192.168.7.1")
    ssh_username: str = os.getenv("CYBOPAL_SSH_USERNAME", "radxa")
    ssh_password: str = os.getenv("CYBOPAL_SSH_PASSWORD", "radxa")
    ssh_mock: bool = _env_bool("CYBOPAL_SSH_MOCK", False)
    container_hint: str = os.getenv("CYBOPAL_CONTAINER_HINT", "cybopal")
    calibration_config_path: str = os.getenv(
        "CYBOPAL_CALIBRATION_CONFIG", "/etc/cytobot/gra-es.yaml"
    )
    calibration_flag_path: str = os.getenv(
        "CYBOPAL_CALIBRATION_FLAG", "/etc/cybopal/calibration.yaml"
    )


def get_settings() -> Settings:
    return Settings()

