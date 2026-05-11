/**
 * Vue Router Configuration - Experiment Versioning Dashboard
 */

import { createRouter, createWebHistory } from 'vue-router'
import ExperimentView from '../views/ExperimentView.vue'

const routes = [
  {
    path: '/',
    redirect: '/playground',
  },
  {
    path: '/playground',
    name: 'Playground',
    component: ExperimentView,
    meta: {
      title: 'Experiment Lineage',
      icon: '🔬',
    },
  },
  {
    path: '/playground/:experimentId',
    name: 'PlaygroundDetail',
    component: ExperimentView,
    meta: {
      title: 'Experiment Detail',
      icon: '🔬',
    },
  },
  // Legacy alias for new URLs (in case anyone uses /experiments)
  {
    path: '/experiments',
    redirect: '/playground',
  },
  {
    path: '/experiments/:experimentId',
    redirect: to => `/playground/${to.params.experimentId}`,
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/playground',
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
    : 'DataVint - Experiment Versioning'
  next()
})

export default router
