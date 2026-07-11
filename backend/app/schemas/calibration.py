from typing import Literal

from pydantic import BaseModel


CalibrationAction = Literal[
    "joint_1_up",
    "joint_1_down",
    "joint_2_up",
    "joint_2_down",
    "joint_3_up",
    "joint_3_down",
    "joint_4_up",
    "joint_4_down",
    "joint_5_up",
    "joint_5_down",
    "joint_6_up",
    "joint_6_down",
    "speed_up",
    "speed_down",
    "save",
    "toggle_joint_limits",
    "recover",
    "home",
    "interrupt",
]


class ControlRequest(BaseModel):
    action: CalibrationAction
