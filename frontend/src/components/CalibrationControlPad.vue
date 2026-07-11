<template>
  <section class="joint-control-panel">
    <div class="section-title">
      <div>
        <h3>关节控制</h3>
        <span>{{ message ? `Message[${messageLevel}]: ${message}` : stateReason }}</span>
      </div>
      <n-tag :type="ready ? 'success' : 'warning'" round>
        {{ ready ? 'ready' : 'not ready' }}
      </n-tag>
    </div>

    <div class="joint-table">
      <div v-for="joint in joints" :key="joint" class="joint-row">
        <div class="joint-name">关节 {{ joint }}</div>
        <n-button
          size="large"
          :disabled="disabled"
          @click="emit('control', `joint_${joint}_up` as CalibrationAction)"
        >
          <template #icon><ArrowUp :size="18" /></template>
          抬起
        </n-button>
        <n-button
          size="large"
          :disabled="disabled"
          @click="emit('control', `joint_${joint}_down` as CalibrationAction)"
        >
          <template #icon><ArrowDown :size="18" /></template>
          放下
        </n-button>
      </div>
    </div>

    <div class="speed-panel">
      <div>
        <h3>速度</h3>
        <span>当前工具只确认支持加速和减速</span>
      </div>
      <div class="speed-actions">
        <n-button size="large" :disabled="disabled" @click="emit('control', 'speed_down')">
          <template #icon><Minus :size="18" /></template>
          减速
        </n-button>
        <n-button size="large" :disabled="disabled" @click="emit('control', 'speed_up')">
          <template #icon><Plus :size="18" /></template>
          加速
        </n-button>
      </div>
    </div>

    <div class="save-panel">
      <div>
        <h3>保存标定</h3>
        <span>保存后再完成并重启容器</span>
      </div>
      <n-popconfirm
        positive-text="保存"
        negative-text="取消"
        :show-icon="false"
        @positive-click="emit('control', 'save')"
      >
        <template #trigger>
          <n-button size="large" type="primary" :disabled="disabled">
            <template #icon><Save :size="18" /></template>
            保存标定
          </n-button>
        </template>
        确认保存当前标定结果？
      </n-popconfirm>
    </div>

    <div class="save-panel">
      <div>
        <h3>归位检查</h3>
        <span>保存后机器可能离开标定位置，如需检查可点击归位</span>
      </div>
      <n-button size="large" :disabled="disabled" @click="emit('control', 'home')">
        <template #icon><Home :size="18" /></template>
        归位检查
      </n-button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { NButton, NPopconfirm, NTag } from 'naive-ui'
import { ArrowDown, ArrowUp, Home, Minus, Plus, Save } from '@lucide/vue'
import type { CalibrationAction } from '../types/calibration'

defineProps<{
  disabled: boolean
  ready: boolean
  messageLevel: string
  message: string
  stateReason: string
}>()

const emit = defineEmits<{
  control: [action: CalibrationAction]
}>()

const joints = [1, 2, 3, 4, 5, 6]
</script>
