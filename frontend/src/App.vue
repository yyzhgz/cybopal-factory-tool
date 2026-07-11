<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-message-provider>
      <app-shell />
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { NConfigProvider, NMessageProvider, type GlobalThemeOverrides } from 'naive-ui'
import AppShell from './components/AppShell.vue'

const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#1f8f4d',
    primaryColorHover: '#25a85c',
    primaryColorPressed: '#176f3b',
    borderRadius: '8px',
    fontFamily:
      'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
  },
  Button: {
    borderRadiusMedium: '8px',
    borderRadiusLarge: '8px'
  },
  Card: {
    borderRadius: '8px',
    boxShadow: '0 12px 34px rgba(15, 23, 42, 0.06)'
  }
}
</script>

