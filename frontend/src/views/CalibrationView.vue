<template>
  <div class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Calibration Wizard</p>
        <h1>机器标定</h1>
        <p>按顺序点击按钮完成准备、启动和标定控制。</p>
      </div>
      <n-button quaternary :loading="store.busy" @click="store.refreshLogs">
        <template #icon><RefreshCw :size="17" /></template>
        刷新日志
      </n-button>
    </header>

    <step-progress :current="store.currentStep" :steps="steps" />

    <div class="content-grid">
      <section class="workspace">
        <div class="status-band">
          <div>
            <span class="status-label">当前状态</span>
            <strong>{{ store.message }}</strong>
          </div>
          <n-tag v-if="store.firstCalibration === true" type="warning" round>
            首次标定
          </n-tag>
          <n-tag v-else-if="store.firstCalibration === false" type="success" round>
            修正标定
          </n-tag>
        </div>

        <section class="action-panel">
          <div class="action-copy">
            <h2>先完成设备准备</h2>
            <p>系统会自动连接 SSH、选择最新容器、修改固定配置并准备 motion 服务。</p>
            <p v-if="!store.connected" class="hint">设备未连接时不能准备环境。</p>
            <p v-else-if="!store.prepared" class="hint">准备环境会自动修改配置并重启 motion 服务。</p>
            <p v-else-if="!store.toolStarted" class="hint">启动后再进行关节选择和方向控制。</p>
          </div>
          <div class="action-buttons">
            <n-button
              size="large"
              type="primary"
              :loading="store.busy && !store.connected"
              @click="store.connect"
            >
              <template #icon><Cable :size="18" /></template>
              连接设备
            </n-button>
            <n-button
              size="large"
              :disabled="!store.connected"
              :loading="store.busy && store.connected && !store.prepared"
              @click="store.prepare"
            >
              <template #icon><Wrench :size="18" /></template>
              准备环境
            </n-button>
            <n-button
              size="large"
              :disabled="!store.prepared"
              :loading="store.busy && store.prepared && !store.toolStarted"
              @click="store.startTool"
            >
              <template #icon><Play :size="18" /></template>
              启动标定工具
            </n-button>
          </div>
        </section>

        <calibration-control-pad
          :disabled="!store.toolStarted || !store.toolReady || store.busy"
          :ready="store.toolReady"
          :message-level="store.messageLevel"
          :message="store.toolMessage"
          :state-reason="store.stateReason"
          @control="store.control"
        />

        <section v-if="store.toolStarted && !store.toolReady" class="ready-panel">
          <div class="ready-copy">
            <h2>标定工具暂不可用</h2>
            <p>
              {{ store.stateReason || '当前状态不允许继续标定。' }}
            </p>
            <p class="message-line">
              当前 Message：{{ store.toolMessage || '未检测到' }}
            </p>
          </div>
          <div class="ready-actions">
            <n-button size="large" :loading="store.busy" @click="store.recoverTool">
              <template #icon><RotateCcw :size="18" /></template>
              尝试恢复
            </n-button>
            <n-button size="large" type="primary" :loading="store.busy" @click="store.restartTool">
              <template #icon><RefreshCw :size="18" /></template>
              重新启动标定服务
            </n-button>
          </div>
          <pre v-if="store.terminalOutput" class="terminal-preview">{{ store.terminalOutput }}</pre>
        </section>

        <section class="finish-panel">
          <div>
            <h2>完成标定</h2>
            <p>保存标定后可归位检查。确认完成后，系统会退出工具并重启当前 Docker 容器。</p>
          </div>
          <div class="finish-actions">
            <n-button size="large" :disabled="!store.toolStarted" @click="store.stopTool">
              <template #icon><CircleStop :size="18" /></template>
              退出工具
            </n-button>
            <n-button
              size="large"
              type="primary"
              :disabled="!store.prepared"
              :loading="store.busy && store.prepared"
              @click="store.finish"
            >
              <template #icon><RotateCw :size="18" /></template>
              完成并重启容器
            </n-button>
          </div>
        </section>
      </section>

      <aside class="right-rail">
        <section class="side-panel">
          <div class="panel-title">
            <h3>设备信息</h3>
            <span>固定连接</span>
          </div>
          <dl class="info-list">
            <div>
              <dt>IP</dt>
              <dd>192.168.7.1</dd>
            </div>
            <div>
              <dt>用户</dt>
              <dd>radxa</dd>
            </div>
            <div>
              <dt>配置文件</dt>
              <dd>/etc/cytobot/gra-es.yaml</dd>
            </div>
            <div>
              <dt>首次判断</dt>
              <dd>/etc/cybopal/calibration.yaml</dd>
            </div>
          </dl>
        </section>

        <smart-diagnosis-card :diagnosis="store.diagnosis" />
        <operation-log-panel :logs="store.logs" />
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useIntervalFn } from '@vueuse/core'
import { NButton, NTag } from 'naive-ui'
import {
  Cable,
  CircleStop,
  Play,
  RefreshCw,
  RotateCcw,
  RotateCw,
  Wrench
} from '@lucide/vue'
import CalibrationControlPad from '../components/CalibrationControlPad.vue'
import OperationLogPanel from '../components/OperationLogPanel.vue'
import SmartDiagnosisCard from '../components/SmartDiagnosisCard.vue'
import StepProgress from '../components/StepProgress.vue'
import { useCalibrationStore } from '../stores/calibration'

const store = useCalibrationStore()
const shouldPollTool = computed(() => store.toolStarted && !store.finished)

useIntervalFn(
  () => {
    if (shouldPollTool.value && !store.busy) {
      void store.refreshToolStatus()
    }
  },
  1000,
  { immediate: false }
)

const steps = [
  { id: 1, label: '连接设备' },
  { id: 2, label: '准备环境' },
  { id: 3, label: '启动工具' },
  { id: 4, label: '标定控制' },
  { id: 5, label: '重启完成' }
]
</script>
