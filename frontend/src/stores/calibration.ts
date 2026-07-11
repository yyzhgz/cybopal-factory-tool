import { defineStore } from 'pinia'

import { calibrationApi } from '../services/api'
import type {
  CalibrationAction,
  ContainerInfo,
  Diagnosis,
  OperationLog,
  OperationResult
} from '../types/calibration'

interface CalibrationState {
  busy: boolean
  currentStep: number
  connected: boolean
  prepared: boolean
  toolStarted: boolean
  toolReady: boolean
  readiness: 'ready' | 'not_ready'
  messageLevel: 'INFO' | 'ERROR' | 'UNKNOWN'
  toolMessage: string
  stateReason: string
  recoveryActions: string[]
  finished: boolean
  firstCalibration: boolean | null
  container: ContainerInfo | null
  message: string
  diagnosis: Diagnosis | null
  logs: OperationLog[]
  terminalOutput: string
}

export const useCalibrationStore = defineStore('calibration', {
  state: (): CalibrationState => ({
    busy: false,
    currentStep: 1,
    connected: false,
    prepared: false,
    toolStarted: false,
    toolReady: false,
    readiness: 'not_ready',
    messageLevel: 'UNKNOWN',
    toolMessage: '',
    stateReason: '',
    recoveryActions: [],
    finished: false,
    firstCalibration: null,
    container: null,
    message: '请先连接设备',
    diagnosis: null,
    logs: [],
    terminalOutput: ''
  }),
  actions: {
    async connect() {
      await this.run(async () => {
        const result = await calibrationApi.connect()
        this.connected = result.success
        this.currentStep = result.success ? 2 : 1
        return result
      })
    },
    async prepare() {
      await this.run(async () => {
        const result = await calibrationApi.prepare()
        if (result.success) {
          this.prepared = true
          this.currentStep = 3
          this.container = result.data.container
          this.firstCalibration = result.data.firstCalibration
        }
        return result
      })
    },
    async startTool() {
      await this.run(async () => {
        const result = await calibrationApi.start()
        if (result.success) {
          this.toolStarted = true
          this.applyToolData(result.data)
          this.currentStep = 4
        }
        return result
      })
    },
    async restartTool() {
      await this.run(async () => {
        const result = await calibrationApi.restart()
        if (result.success) {
          this.toolStarted = true
          this.applyToolData(result.data)
          this.currentStep = 4
        }
        return result
      })
    },
    async recoverTool() {
      await this.run(async () => {
        const result = await calibrationApi.recover()
        if (result.success) {
          this.applyToolData(result.data)
        }
        return result
      })
    },
    async refreshToolStatus() {
      await this.run(async () => {
        const result = await calibrationApi.status()
        if (result.success) {
          this.toolStarted = Boolean(result.data.started)
          this.applyToolData(result.data)
        }
        return result
      }, false)
    },
    async control(action: CalibrationAction) {
      await this.run(async () => {
        const result = await calibrationApi.control(action)
        this.applyToolData(result.data)
        return result
      }, false)
    },
    async finish() {
      await this.run(async () => {
        const result = await calibrationApi.finish()
        if (result.success) {
          this.finished = true
          this.toolStarted = false
          this.toolReady = false
          this.readiness = 'not_ready'
          this.messageLevel = 'UNKNOWN'
          this.toolMessage = ''
          this.stateReason = ''
          this.recoveryActions = []
          this.currentStep = 5
        }
        return result
      })
    },
    async stopTool() {
      await this.run(async () => {
        const result = await calibrationApi.stop()
        if (result.success) {
          this.toolStarted = false
          this.toolReady = false
          this.readiness = 'not_ready'
          this.messageLevel = 'UNKNOWN'
          this.toolMessage = ''
          this.stateReason = ''
          this.recoveryActions = []
        }
        return result
      })
    },
    async refreshLogs() {
      const result = await calibrationApi.logs()
      this.logs = result.logs
    },
    async run<TData>(
      task: () => Promise<OperationResult<TData>>,
      showBusy = true
    ): Promise<void> {
      if (showBusy) {
        this.busy = true
      }
      this.diagnosis = null
      try {
        const result = await task()
        this.message = result.message
        this.diagnosis = result.diagnosis
        this.logs = result.logs
      } catch (error) {
        this.message = '无法连接到本地服务'
        this.diagnosis = {
          current_status: '前端没有收到后端响应。',
          possible_cause: '后端服务未启动，或网络代理配置不正确。',
          suggested_action: '确认 FastAPI 服务正在运行后重试。',
          estimated_recovery_time: '约 1 分钟'
        }
      } finally {
        this.busy = false
      }
    },
    applyToolData(data: Partial<{
      ready: boolean
      readiness: 'ready' | 'not_ready'
      messageLevel: 'INFO' | 'ERROR' | 'UNKNOWN'
      toolMessage: string
      stateReason: string
      recoveryActions: string[]
      terminalOutput: string
    }>) {
      if (typeof data.ready === 'boolean') {
        this.toolReady = data.ready
      }
      if (data.readiness) {
        this.readiness = data.readiness
      }
      if (data.messageLevel) {
        this.messageLevel = data.messageLevel
      }
      if (typeof data.toolMessage === 'string') {
        this.toolMessage = data.toolMessage
      }
      if (typeof data.stateReason === 'string') {
        this.stateReason = data.stateReason
      }
      if (Array.isArray(data.recoveryActions)) {
        this.recoveryActions = data.recoveryActions
      }
      if (typeof data.terminalOutput === 'string') {
        this.terminalOutput = data.terminalOutput
      }
    }
  }
})
