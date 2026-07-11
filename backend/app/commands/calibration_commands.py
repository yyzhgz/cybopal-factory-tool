from __future__ import annotations

import re
import shlex
from typing import Iterable, Optional

from app.domain import ContainerInfo


JOINT_UP_KEYS = {
    1: "!",
    2: "@",
    3: "#",
    4: "$",
    5: "%",
    6: "^",
}


CONTROL_KEY_MAP = {
    "joint_1_up": JOINT_UP_KEYS[1],
    "joint_1_down": "1",
    "joint_2_up": JOINT_UP_KEYS[2],
    "joint_2_down": "2",
    "joint_3_up": JOINT_UP_KEYS[3],
    "joint_3_down": "3",
    "joint_4_up": JOINT_UP_KEYS[4],
    "joint_4_down": "4",
    "joint_5_up": JOINT_UP_KEYS[5],
    "joint_5_down": "5",
    "joint_6_up": JOINT_UP_KEYS[6],
    "joint_6_down": "6",
    "speed_up": "+",
    "speed_down": "-",
    "save": "C",
    "toggle_joint_limits": "M",
    "recover": "R",
    "home": "H",
    "interrupt": "\x03",
}


def sudo(command: str, password: str) -> str:
    return f"printf '%s\\n' {shlex.quote(password)} | sudo -S -p '' {command}"


def sudo_interactive(command: str) -> str:
    return f"sudo -S -p '' {command}"


def docker_ps_command(password: str) -> str:
    docker_command = "docker ps -a --format '{{.ID}}|{{.Image}}|{{.Names}}|{{.CreatedAt}}'"
    return sudo(docker_command, password)


def exec_in_container(container_id: str, inner_command: str, password: str) -> str:
    quoted_id = shlex.quote(container_id)
    quoted_inner = shlex.quote(inner_command)
    return sudo(f"docker exec {quoted_id} bash -lc {quoted_inner}", password)


def interactive_exec_in_container(container_id: str, inner_command: str, password: str) -> str:
    quoted_id = shlex.quote(container_id)
    quoted_inner = shlex.quote(inner_command)
    return sudo_interactive(f"docker exec -it {quoted_id} bash -lc {quoted_inner}")


def install_dependencies_command(container_id: str, password: str) -> str:
    inner = (
        "set -e; "
        "apt update; "
        "DEBIAN_FRONTEND=noninteractive apt install -y libncurses6 nano less"
    )
    return exec_in_container(container_id, inner, password)


def patch_config_command(container_id: str, config_path: str, password: str) -> str:
    inner = f"""
set -e
CONFIG={shlex.quote(config_path)}
test -f "$CONFIG"
cp "$CONFIG" "$CONFIG.bak.$(date +%Y%m%d%H%M%S)"
sed -i -E 's|calibration_position_deg:[[:space:]]*\\[[^]]*\\]|calibration_position_deg: [0, 0, 90, 0, 0, 0]|' "$CONFIG"
sed -i -E 's|hard_collision_detect:[[:space:]]*true|hard_collision_detect: false|g' "$CONFIG"
grep -Fq 'calibration_position_deg: [0, 0, 90, 0, 0, 0]' "$CONFIG"
""".strip()
    return exec_in_container(container_id, inner, password)


def prepare_motion_services_command(container_id: str, password: str) -> str:
    inner = "set -e; systemctl stop cybopal-launcher.service; systemctl restart cytobot-ctrl"
    return exec_in_container(container_id, inner, password)


def calibration_file_state_command(
    container_id: str, calibration_flag_path: str, password: str
) -> str:
    inner = (
        f"if test -f {shlex.quote(calibration_flag_path)}; "
        "then echo calibrated; else echo first_calibration; fi"
    )
    return exec_in_container(container_id, inner, password)


def start_keyboard_control_command(
    container_id: str,
    is_first_calibration: bool,
    password: str,
) -> str:
    command = "cytobot_keyboard_control"
    if is_first_calibration:
        command += " --ignore-joint-zero-check"
    return interactive_exec_in_container(container_id, command, password)


def restart_container_command(container_id: str, password: str) -> str:
    return sudo(f"docker restart {shlex.quote(container_id)}", password)


def select_latest_container(
    docker_ps_output: str, container_hint: str = "cybopal"
) -> Optional[ContainerInfo]:
    containers = _parse_containers(docker_ps_output)
    if not containers:
        return None

    hinted = [
        item
        for item in containers
        if container_hint.lower() in item.name.lower()
        or container_hint.lower() in item.image.lower()
    ]
    candidates = hinted or containers

    def score(indexed: tuple[int, ContainerInfo]) -> tuple[str, int]:
        index, item = indexed
        version = _version_stamp((item.image, item.name, item.created_at))
        return (version or "", -index)

    _, selected = max(enumerate(candidates), key=score)
    return selected


def _parse_containers(output: str) -> list[ContainerInfo]:
    containers: list[ContainerInfo] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or "|" not in line:
            continue
        parts = line.split("|", 3)
        if len(parts) < 3:
            continue
        created_at = parts[3] if len(parts) > 3 else ""
        containers.append(
            ContainerInfo(
                container_id=parts[0].strip(),
                image=parts[1].strip(),
                name=parts[2].strip(),
                created_at=created_at.strip(),
            )
        )
    return containers


def _version_stamp(values: Iterable[str]) -> str:
    joined = " ".join(values)
    matches = re.findall(r"(20\d{6})(?:[-_]?([0-9a-fA-F]{6,12}))?", joined)
    if not matches:
        return ""
    date, suffix = matches[-1]
    return f"{date}-{suffix}"
