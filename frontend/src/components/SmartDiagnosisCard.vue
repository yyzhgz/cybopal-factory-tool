<template>
  <section v-if="diagnosis" class="diagnosis-card">
    <div class="diagnosis-heading">
      <CircleAlert :size="18" />
      <h3>智能诊断</h3>
    </div>
    <dl>
      <div>
        <dt>当前状态</dt>
        <dd>{{ diagnosis.current_status }}</dd>
      </div>
      <div>
        <dt>可能原因</dt>
        <dd>{{ diagnosis.possible_cause }}</dd>
      </div>
      <div>
        <dt>建议操作</dt>
        <dd>{{ diagnosis.suggested_action }}</dd>
      </div>
      <div>
        <dt>预计耗时</dt>
        <dd>{{ diagnosis.estimated_recovery_time }}</dd>
      </div>
    </dl>
  </section>
</template>

<script setup lang="ts">
import { CircleAlert } from '@lucide/vue'
import type { Diagnosis } from '../types/calibration'

defineProps<{
  diagnosis: Diagnosis | null
}>()
</script>
