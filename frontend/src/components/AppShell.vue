<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">CP</div>
        <div>
          <strong>CyboPal</strong>
          <span>工厂维护中心</span>
        </div>
      </div>

      <nav class="nav-list">
        <router-link class="nav-item muted" to="/calibration">
          <Home :size="18" />
          首页
        </router-link>
        <router-link class="nav-item muted" to="/calibration">
          <Cpu :size="18" />
          设备
        </router-link>
        <router-link class="nav-item active" to="/calibration">
          <SlidersHorizontal :size="18" />
          标定
        </router-link>
        <router-link class="nav-item muted" to="/calibration">
          <Activity :size="18" />
          老化测试
        </router-link>
        <router-link class="nav-item muted" to="/calibration">
          <FileText :size="18" />
          日志
        </router-link>
      </nav>

      <section class="device-card">
        <div class="device-status">
          <span :class="['status-dot', store.connected ? 'online' : 'offline']" />
          <strong>{{ store.connected ? '已连接' : '未连接' }}</strong>
        </div>
        <p>192.168.7.1</p>
        <div v-if="store.container" class="container-name">{{ store.container.name }}</div>
      </section>

      <div class="operator">
        <div class="avatar">工</div>
        <div>
          <strong>工厂操作员</strong>
          <span>标定任务</span>
        </div>
      </div>
    </aside>

    <main class="main-panel">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import {
  Activity,
  Cpu,
  FileText,
  Home,
  SlidersHorizontal
} from '@lucide/vue'
import { useCalibrationStore } from '../stores/calibration'

const store = useCalibrationStore()
</script>
