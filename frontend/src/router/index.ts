import { createRouter, createWebHashHistory } from 'vue-router'

const router = createRouter({
  history: createWebHashHistory(),
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
