export type OperationLevel = 'info' | 'success' | 'warning' | 'error'

export interface OperationLog {
  timestamp: string
  level: OperationLevel
  message: string
}

export interface Diagnosis {
  current_status: string
  possible_cause: string
  suggested_action: string
  estimated_recovery_time: string
  recovery_action?: string
}

export interface ContainerInfo {
  container_id: string
  image: string
  name: string
  created_at: string
}

export interface OperationResult<TData = Record<string, unknown>> {
  success: boolean
  status: string
  message: string
  data: TData
  diagnosis: Diagnosis | null
  logs: OperationLog[]
}

export type CalibrationAction =
  | 'joint_1_up'
  | 'joint_1_down'
  | 'joint_2_up'
  | 'joint_2_down'
  | 'joint_3_up'
  | 'joint_3_down'
  | 'joint_4_up'
  | 'joint_4_down'
  | 'joint_5_up'
  | 'joint_5_down'
  | 'joint_6_up'
  | 'joint_6_down'
  | 'speed_up'
  | 'speed_down'
  | 'save'
  | 'toggle_joint_limits'
  | 'recover'
  | 'home'
  | 'interrupt'

export interface CalibrationPrepareData {
  container: ContainerInfo
  mode: 'first_calibration' | 'adjust_calibration'
  firstCalibration: boolean
}

export interface CalibrationToolData {
  ready: boolean
  readiness: 'ready' | 'not_ready'
  canControl: boolean
  canSave: boolean
  messageLevel: 'INFO' | 'ERROR' | 'UNKNOWN'
  toolMessage: string
  stateReason: string
  recoveryActions: string[]
  started?: boolean
  firstCalibration?: boolean
  terminalOutput: string
}
