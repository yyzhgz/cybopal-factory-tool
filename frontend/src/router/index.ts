import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/calibration'
    },
    {
      path: '/calibration',
      name: 'calibration',
      component: () => import('../views/CalibrationView.vue')
    }
  ]
})

export default router

