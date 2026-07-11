# CyboPal Desktop Frontend

Vue 3 calibration UI running inside Electron.

## Browser Development

```bash
npm install
npm run dev
```

## Desktop Development

```bash
npm run dev:desktop
```

Electron starts the FastAPI backend from source in development mode. By default
it enables `CYBOPAL_SSH_MOCK=true` so the UI can be tested without a device.

## macOS Package

```bash
npm run dist:mac
```

Use macOS or the GitHub Actions workflow for real `.dmg` output.

