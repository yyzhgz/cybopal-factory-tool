import unittest

from app.commands.calibration_commands import (
    CONTROL_KEY_MAP,
    select_latest_container,
)
from app.core.config import Settings
from app.services.calibration_service import CalibrationService
from app.services.log_service import LogService
from app.ssh.mock_ssh_service import MockSSHService


class CalibrationServiceTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.settings = Settings(ssh_mock=True)
        self.ssh = MockSSHService()
        self.service = CalibrationService(self.settings, self.ssh, LogService())

    async def test_prepare_detects_first_calibration(self) -> None:
        result = await self.service.prepare_environment()

        self.assertTrue(result.success)
        self.assertTrue(result.data["firstCalibration"])
        self.assertEqual(result.data["mode"], "first_calibration")

    async def test_start_uses_ignore_zero_check_when_first_calibration(self) -> None:
        await self.service.prepare_environment()
        result = await self.service.start_calibration_tool()

        self.assertTrue(result.success)
        self.assertIn("--ignore-joint-zero-check", self.ssh.interactive_commands[0])
        self.assertTrue(result.data["ready"])
        self.assertEqual(self.ssh.interactive.writes[-1], CONTROL_KEY_MAP["toggle_joint_limits"])

    async def test_start_does_not_unlock_before_keyboard_screen(self) -> None:
        async def timeout_immediately(timeout_seconds: float) -> bool:
            return False

        await self.service.prepare_environment()
        self.ssh.interactive._output = (
            "[2026-07-11 03:22:29.313] [info] Registered planners\n"
            "Loading config file: /etc/cytobot/config.yaml\n"
            "[2026-07-11 03:22:29.340] [info] Loaded calibration file\n"
        )
        self.service._wait_for_keyboard_screen = timeout_immediately

        result = await self.service.start_calibration_tool()

        self.assertTrue(result.success)
        self.assertFalse(result.data["ready"])
        self.assertEqual(result.data["messageLevel"], "UNKNOWN")
        self.assertNotIn(CONTROL_KEY_MAP["toggle_joint_limits"], self.ssh.interactive.writes)

    async def test_control_sends_expected_key(self) -> None:
        await self.service.prepare_environment()
        await self.service.start_calibration_tool()
        result = await self.service.send_control("save")

        self.assertTrue(result.success)
        self.assertEqual(self.ssh.interactive.writes[-1], CONTROL_KEY_MAP["save"])

    async def test_control_is_blocked_until_ready(self) -> None:
        await self.service.prepare_environment()
        await self.service.start_calibration_tool()
        self.ssh.interactive._output = "keyboard\nMessage[ERROR]: controller not ready\n"

        result = await self.service.send_control("save")

        self.assertFalse(result.success)
        self.assertEqual(result.status, "tool_not_ready")
        self.assertNotEqual(self.ssh.interactive.writes[-1], CONTROL_KEY_MAP["save"])

    async def test_latest_error_message_controls_ready_state(self) -> None:
        await self.service.prepare_environment()
        await self.service.start_calibration_tool()
        self.ssh.interactive._output = (
            "CYTOBOT KEYBOARD CONTROL\n"
            "Message[INFO]: Ready\n"
            "Joint Positions...\n"
            "Message[ERROR]: encoder offline\n"
        )

        result = self.service.tool_status()

        self.assertTrue(result.success)
        self.assertFalse(result.data["ready"])
        self.assertEqual(result.data["readiness"], "not_ready")
        self.assertEqual(result.data["messageLevel"], "ERROR")
        self.assertEqual(result.data["toolMessage"], "encoder offline")

    async def test_recover_sends_toggle_and_recover_keys(self) -> None:
        await self.service.prepare_environment()
        await self.service.start_calibration_tool()
        self.ssh.interactive._output = "keyboard\nMessage[ERROR]: controller not ready\n"

        result = await self.service.try_recover_tool()

        self.assertTrue(result.success)
        self.assertEqual(self.ssh.interactive.writes[-2:], ["M", "R"])

    async def test_restart_reuses_previous_start_command(self) -> None:
        await self.service.prepare_environment()
        await self.service.start_calibration_tool()
        first_command = self.ssh.interactive_commands[-1]

        result = await self.service.restart_calibration_tool()

        self.assertTrue(result.success)
        self.assertEqual(self.ssh.interactive_commands[-1], first_command)

    async def test_joint_up_uses_shift_number_symbol(self) -> None:
        await self.service.prepare_environment()
        await self.service.start_calibration_tool()
        result = await self.service.send_control("joint_3_up")

        self.assertTrue(result.success)
        self.assertEqual(self.ssh.interactive.writes[-1], "#")

    async def test_finish_restarts_container(self) -> None:
        await self.service.prepare_environment()
        result = await self.service.finish_calibration()

        self.assertTrue(result.success)
        self.assertTrue(any("docker restart" in command for command in self.ssh.commands))


class ContainerSelectionTest(unittest.TestCase):
    def test_selects_newest_cybopal_container(self) -> None:
        output = "\n".join(
            [
                "old|repo/daily-20260701-aaaaaaa|cybopal_container-daily-20260701-aaaaaaa|x",
                "new|repo/daily-20260708-bbbbbbb|cybopal_container-daily-20260708-bbbbbbb|x",
            ]
        )

        selected = select_latest_container(output)

        self.assertIsNotNone(selected)
        self.assertEqual(selected.container_id, "new")


if __name__ == "__main__":
    unittest.main()
