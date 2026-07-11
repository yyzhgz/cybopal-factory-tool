const { contextBridge } = require('electron')

contextBridge.exposeInMainWorld('cyboPal', {
  backendUrl: process.env.CYBOPAL_BACKEND_URL || 'http://127.0.0.1:8000',
  platform: process.platform
})

