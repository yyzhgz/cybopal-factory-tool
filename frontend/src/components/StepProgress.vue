<template>
  <div class="step-strip">
    <div
      v-for="step in steps"
      :key="step.id"
      :class="['step-item', { done: step.id < current, active: step.id === current }]"
    >
      <div class="step-index">
        <Check v-if="step.id < current" :size="15" />
        <span v-else>{{ step.id }}</span>
      </div>
      <span>{{ step.label }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Check } from '@lucide/vue'

defineProps<{
  current: number
  steps: Array<{ id: number; label: string }>
}>()
</script>
