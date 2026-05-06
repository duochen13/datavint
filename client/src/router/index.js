/**
 * Vue Router Configuration
 */

import { createRouter, createWebHistory } from 'vue-router'
import PlaygroundView from '../views/PlaygroundView.vue'
import DataView from '../views/DataView.vue'
import VisualizationView from '../views/VisualizationView.vue'

const routes = [
  {
    path: '/',
    redirect: '/playground',
  },
  {
    path: '/playground',
    name: 'Playground',
    component: PlaygroundView,
    meta: {
      title: 'Playground',
      icon: '⚡',
    },
  },
  {
    path: '/data',
    name: 'Data',
    component: DataView,
    meta: {
      title: 'Raw Data',
      icon: '📊',
    },
  },
  {
    path: '/visualization',
    name: 'Visualization',
    component: VisualizationView,
    meta: {
      title: 'Visualization Board',
      icon: '📈',
    },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Update document title on route change
router.beforeEach((to, from, next) => {
  document.title = to.meta.title
    ? `${to.meta.title} - DataVint`
    : 'DataVint - Data Quality Platform'
  next()
})

export default router
