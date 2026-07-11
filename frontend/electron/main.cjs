const { app, BrowserWindow, shell } = require('electron')
const { spawn } = require('node:child_process')
const http = require('node:http')
const path = require('node:path')

const BACKEND_HOST = '127.0.0.1'
const BACKEND_PORT = process.env.CYBOPAL_BACKEND_PORT || '8000'
const BACKEND_URL = process.env.CYBOPAL_BACKEND_URL || `http://${BACKEND_HOST}:${BACKEND_PORT}`
const VITE_DEV_SERVER_URL = process.env.VITE_DEV_SERVER_URL || 'http://127.0.0.1:5173'

let mainWindow = null
let backendProcess = null

function isDev() {
  return !app.isPackaged
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1320,
    height: 860,
    minWidth: 1040,
    minHeight: 720,
    title: 'CyboPal Factory Tool',
    backgroundColor: '#f6f4f0',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  })

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })

  if (isDev()) {
    mainWindow.loadURL(VITE_DEV_SERVER_URL)
    return
  }

  mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
}

function resolvePythonCommand() {
  if (process.env.CYBOPAL_PYTHON) {
    return process.env.CYBOPAL_PYTHON
  }
  return process.platform === 'win32' ? 'python' : 'python3'
}

function resolvePackagedBackendPath() {
  const executable = process.platform === 'win32' ? 'cybopal-api.exe' : 'cybopal-api'
  return path.join(process.resourcesPath, 'backend', executable)
}

function startBackend() {
  if (process.env.CYBOPAL_BACKEND_AUTOSTART === 'false') {
    return
  }

  if (isDev()) {
    const repoRoot = path.resolve(__dirname, '..', '..')
    const python = resolvePythonCommand()
    backendProcess = spawn(
      python,
      ['-m', 'uvicorn', 'app.main:app', '--host', BACKEND_HOST, '--port', BACKEND_PORT],
      {
        cwd: path.join(repoRoot, 'backend'),
        env: {
          ...process.env,
          PYTHONPATH: path.join(repoRoot, 'backend'),
          CYBOPAL_SSH_MOCK: process.env.CYBOPAL_SSH_MOCK || 'true'
        },
        stdio: 'pipe'
      }
    )
  } else {
    backendProcess = spawn(resolvePackagedBackendPath(), [], {
      env: {
        ...process.env,
        CYBOPAL_BACKEND_HOST: BACKEND_HOST,
        CYBOPAL_BACKEND_PORT: BACKEND_PORT,
        CYBOPAL_SSH_MOCK: process.env.CYBOPAL_SSH_MOCK || 'false'
      },
      stdio: 'pipe'
    })
  }

  backendProcess?.stdout?.on('data', (chunk) => {
    console.log(`[backend] ${chunk.toString().trim()}`)
  })
  backendProcess?.stderr?.on('data', (chunk) => {
    console.error(`[backend] ${chunk.toString().trim()}`)
  })
  backendProcess?.on('exit', (code) => {
    console.log(`[backend] exited with code ${code}`)
  })
}

function stopBackend() {
  if (!backendProcess || backendProcess.killed) {
    return
  }
  backendProcess.kill()
  backendProcess = null
}

function waitForBackend(timeoutMs = 12000) {
  const started = Date.now()

  return new Promise((resolve) => {
    const check = () => {
      const request = http.get(`${BACKEND_URL}/api/health`, (response) => {
        response.resume()
        resolve(true)
      })

      request.on('error', () => {
        if (Date.now() - started > timeoutMs) {
          resolve(false)
          return
        }
        setTimeout(check, 350)
      })

      request.setTimeout(1000, () => {
        request.destroy()
      })
    }

    check()
  })
}

app.whenReady().then(async () => {
  process.env.CYBOPAL_BACKEND_URL = BACKEND_URL
  startBackend()
  await waitForBackend()
  createWindow()
})

app.on('window-all-closed', () => {
  stopBackend()
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

app.on('before-quit', () => {
  stopBackend()
})
