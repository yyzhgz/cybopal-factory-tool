# CyboPal Factory Tool

Factory-facing desktop application for CyboPal calibration and maintenance.

The current focus is the calibration workflow. The app is designed to become a
macOS installable package while keeping all terminal, SSH, Docker, and config
file details hidden from factory operators.

## Development

Frontend desktop shell:

```bash
cd frontend
npm install
npm run dev:desktop
```

Backend tests:

```bash
PYTHONPATH="$PWD/backend" python -m unittest discover -s backend/tests
```

On Windows PowerShell:

```powershell
$env:PYTHONPATH = (Resolve-Path .\backend).Path
python -m unittest discover -s backend\tests
```

## macOS Release

Build the operator-facing macOS app on macOS:

```bash
bash scripts/build-macos-app.sh
```

The DMG is written to `frontend/release/`. Development packages are unsigned;
set the Apple signing environment variables in CI when distributing outside
internal testing.

See:

```text
docs/release/macos.md
```
