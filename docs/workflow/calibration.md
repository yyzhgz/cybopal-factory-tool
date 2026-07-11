# Calibration Workflow

This is the first implemented workflow for CyboPal Factory Tool.

## Operator Flow

1. Connect device.
2. Prepare calibration environment.
3. Start calibration tool.
4. Use graphical controls to calibrate joints.
5. Finish calibration and restart the current Docker container.

The operator should not type SSH, Docker, systemctl, nano, or shell commands.

## Fixed Device Settings

- Host: `192.168.7.1`
- SSH user: `radxa`
- SSH password: `radxa`
- Container config path: `/etc/cytobot/gra-es.yaml`
- First calibration flag: `/etc/cybopal/calibration.yaml`

## Automated Backend Steps

The backend performs these steps inside `CalibrationService`:

1. Connect to the device by SSH.
2. Run `docker ps -a` and select the newest CyboPal container.
3. Install `libncurses6`, `nano`, and `less`.
4. Patch `/etc/cytobot/gra-es.yaml`:
   - `calibration_position_deg` becomes `[0, 0, 90, 0, 0, 0]`.
   - `hard_collision_detect: true` becomes `hard_collision_detect: false`.
5. Stop `cybopal-launcher.service`.
6. Restart `cytobot-ctrl`.
7. Check `/etc/cybopal/calibration.yaml`.
8. Start `cytobot_keyboard_control`.
   - If the calibration file is missing, start with `--ignore-joint-zero-check`.
   - If the calibration file exists, start without that argument.
9. Wait for the keyboard screen.
   - Startup logs such as planner registration and config loading are not enough.
   - The backend waits for markers such as `CYTOBOT KEYBOARD CONTROL`,
     `Control Instructions`, `Joint Command Positions`, or `Message`.
10. Automatically send `Shift+M` after the keyboard screen appears.
11. Watch the latest keyboard screen `Message` level.
12. On finish, exit the tool and restart the selected Docker container.

Starting `cytobot_keyboard_control` does not mean the tool is ready for button
input. The backend parses the latest `Message` line from the keyboard screen.
The UI only exposes two high-level states:

- `ready`: the latest message is not `Message[ERROR]`.
- `not_ready`: the latest message is `Message[ERROR]`, the tool has not started,
  or the keyboard screen has not appeared yet.

The UI refreshes tool status every second after the keyboard tool starts. If
`Message[ERROR]` appears during calibration, the operator controls are locked
and the recovery panel is shown.

The current version intentionally does not check `cytobot_keyboard_control.log`
or `cytobot_ctrl.log`.

## Current Control Mapping

These mappings are centralized in `backend/app/commands/calibration_commands.py`
so they can be adjusted after real device confirmation.

| UI Action | Keyboard Input |
| --- | --- |
| Joint 1 Up | `Shift+1` / `!` |
| Joint 1 Down | `1` |
| Joint 2 Up | `Shift+2` / `@` |
| Joint 2 Down | `2` |
| Joint 3 Up | `Shift+3` / `#` |
| Joint 3 Down | `3` |
| Joint 4 Up | `Shift+4` / `$` |
| Joint 4 Down | `4` |
| Joint 5 Up | `Shift+5` / `%` |
| Joint 5 Down | `5` |
| Joint 6 Up | `Shift+6` / `^` |
| Joint 6 Down | `6` |
| Speed Up | `+` |
| Speed Down | `-` |
| Save Calibration | `C` |
| Toggle Joint Limits | `M` |
| Recover | `R` |
| Go Home | `H` |
| Interrupt | `Ctrl+C` |

## State Rules

The state rules live in `CalibrationStateEvaluator`.

The terminal parser supports both current and legacy output:

- `Message[INFO]: ...`
- `Message[ERROR]: ...`
- `Message: Ready`

Only `Message[ERROR]` makes the tool `not_ready`. Other known messages are
treated as `ready` for now. This rule can be updated in one place when the real
device message contract becomes clearer.

## Not Ready Recovery

If `Message[ERROR]` is visible after starting the tool or during calibration,
the UI shows a locked state and exposes only recovery controls:

1. Try Recovery: sends `Shift+M`, then `Shift+R`.
2. Restart Calibration Service: sends interrupt and runs the same command used
   for the current session.

When clicking "Start Tool" again later, the backend checks the calibration file
again:

- No `/etc/cybopal/calibration.yaml`: run with `--ignore-joint-zero-check`.
- Existing `/etc/cybopal/calibration.yaml`: run without extra arguments.

When clicking "Restart Calibration Service" from a running session, the backend
reuses the previous launch command.

## Pending Real Device Confirmation

- Whether a dedicated emergency stop key exists beyond interrupting the tool.
- Whether long-press behavior is needed or each click should send one keypress.
- Whether speed up/down has visible numeric feedback in the terminal output.
