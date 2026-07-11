<template>
  <section class="side-panel">
    <div class="panel-title">
      <h3>实时日志</h3>
      <span>{{ logs.length }} 条</span>
    </div>
    <div class="log-list">
      <div v-if="logs.length === 0" class="empty-log">等待操作开始</div>
      <div v-for="log in logs" :key="`${log.timestamp}-${log.message}`" class="log-row">
        <span :class="['log-dot', log.level]" />
        <time>{{ log.timestamp }}</time>
        <span>{{ log.message }}</span>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { OperationLog } from '../types/calibration'

defineProps<{
  logs: OperationLog[]
}>()
</script>

