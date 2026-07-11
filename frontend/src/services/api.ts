import type {
  CalibrationAction,
  CalibrationToolData,
  CalibrationPrepareData,
  OperationLog,
  OperationResult
} from '../types/calibration'

const API_BASE = window.cyboPal?.backendUrl ?? import.meta.env.VITE_API_BASE ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {})
    },
    ...init
  })

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`)
  }

  return response.json() as Promise<T>
}

export const calibrationApi = {
  connect() {
    return request<OperationResult>('/api/calibration/connect', { method: 'POST' })
  },
  prepare() {
    return request<OperationResult<CalibrationPrepareData>>('/api/calibration/prepare', {
      method: 'POST'
    })
  },
  start() {
    return request<OperationResult<CalibrationToolData>>('/api/calibration/start', { method: 'POST' })
  },
  restart() {
    return request<OperationResult<CalibrationToolData>>('/api/calibration/restart', {
      method: 'POST'
    })
  },
  recover() {
    return request<OperationResult<CalibrationToolData>>('/api/calibration/recover', {
      method: 'POST'
    })
  },
  status() {
    return request<OperationResult<CalibrationToolData>>('/api/calibration/status')
  },
  control(action: CalibrationAction) {
    return request<OperationResult<Partial<CalibrationToolData>>>('/api/calibration/control', {
      method: 'POST',
      body: JSON.stringify({ action })
    })
  },
  finish() {
    return request<OperationResult>('/api/calibration/finish', { method: 'POST' })
  },
  stop() {
    return request<OperationResult>('/api/calibration/stop', { method: 'POST' })
  },
  logs() {
    return request<{ logs: OperationLog[] }>('/api/calibration/logs')
  }
}
