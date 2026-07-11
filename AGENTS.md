# CyboPal Factory Tool

## Project Vision

This project is NOT another device management software.

The goal is:

> Transform complicated engineer-only maintenance procedures into a simple GUI that factory operators can complete without any engineering knowledge.

Target users:

- Factory operators
- Production line workers
- QC operators
- Hardware technicians
- Customer support

NOT

- Software engineers
- Linux engineers

Every feature should reduce operation difficulty.

The user should NEVER need to:

- SSH manually
- remember terminal commands
- edit yaml
- type shell commands
- remember keyboard shortcuts

The software should automate everything.

--------------------------------------------

## Product Philosophy

Think like Apple.

Users should click buttons instead of typing commands.

Engineers solve problems.

Operators only click Next.

Every page should answer

"What should I do now?"

instead of

"What command should I execute?"

--------------------------------------------

## Main Modules

The software contains the following modules.

### 1 Device

- Connect Device
- Detect Device
- Version
- MCU
- RootFS
- Container
- Device Status

--------------------------------------------

### 2 Calibration Wizard

The calibration workflow should become

Step 1

Environment Check

↓

Step 2

Auto Prepare Environment

↓

Step 3

Calibration

↓

Step 4

Save

↓

Step 5

Verify

↓

Step 6

Restore Environment

Each step should automatically verify success.

If any step fails

Do NOT simply display an error.

Instead

- explain the reason
- suggest recovery
- provide one-click repair

--------------------------------------------

### 3 Aging Test

Support

- Start
- Stop
- Loop
- Status
- Script Selection
- Log Viewer

The software should automatically

- upload scripts
- start server
- launch client

without requiring terminal commands.

--------------------------------------------

### 4 Device Logs

Collect

- launcher log
- ctrl log
- calibration log
- aging log

Support

- Search
- Export
- Copy

--------------------------------------------

### 5 Smart Recovery

Instead of remembering

Ctrl+M

Ctrl+R

Provide one button

Quick Recovery

Quick Recovery automatically

- reset controller
- clear states
- restart services
- verify recovery

--------------------------------------------

## Calibration UI

DO NOT copy terminal keyboard operations.

Instead

Use

Joint List

Joint Detail

Current Angle

Forward

Backward

Speed

Expected Angle

Save

Limit Check

--------------------------------------------

## Speed Modes

Support

- Precision
- Slow
- Normal
- Fast
- Custom

--------------------------------------------

## Log Panel

Every operation should generate logs.

For example

14:21:22

Stopping launcher...

OK

----------------

Restart ctrl...

OK

----------------

Waiting controller...

----------------

Timeout

----------------

Smart Diagnosis

Controller not ready.

Suggestion

Click Quick Recovery.

--------------------------------------------

## Smart Diagnosis

Never show

Unknown Error

Instead

Show

Current Status

Possible Cause

Suggested Action

Estimated Recovery Time

--------------------------------------------

## Coding Rules

Use

Frontend

Vue3

TypeScript

Pinia

Vue Router

Naive UI

Vite

--------------------------------------------

Backend

Python

FastAPI

Pydantic

SQLAlchemy

Async SSH

WebSocket

--------------------------------------------

Architecture

frontend/

backend/

shared/

docs/

--------------------------------------------

Frontend Rules

Component First

Small Components

Composable

Reusable

Avoid duplicated code.

--------------------------------------------

Backend Rules

Every operation should become a Service.

Examples

CalibrationService

RecoveryService

SSHService

DockerService

LogService

ControllerService

Do NOT place business logic inside routers.

--------------------------------------------

Code Quality

Every new feature should include

- typing
- comments
- unit tests
- documentation

--------------------------------------------

UI Style

Modern

Apple

Minimal

Rounded Corners

Soft Shadow

White Background

Gray Border

Smooth Animation

NO

Industrial style

NO

Linux tool style

--------------------------------------------

When implementing features

Always think

"If a factory worker with zero Linux knowledge uses this page,

can they finish the task?"

If the answer is no,

redesign it.