<script setup>
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
</script>

<template>
  <div class="app">
    <!-- Header with Tabs -->
    <header class="header">
      <div class="logo">
        <div class="logo-icon">dv</div>
        DataVint
      </div>
      <nav class="tabs">
        <button
          v-for="tab in router.options.routes.filter(r => r.path !== '/')"
          :key="tab.path"
          :class="['tab', { active: route.path === tab.path }]"
          @click="router.push(tab.path)"
        >
          <span class="tab-icon">{{ tab.meta.icon }}</span>
          {{ tab.meta.title }}
        </button>
      </nav>
    </header>

    <!-- Main Content Area -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<style scoped>
.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.header {
  background: rgba(0, 0, 0, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 2px solid var(--border);
  display: flex;
  align-items: stretch;
  height: 52px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 24px;
  border-right: 1px solid var(--border);
  font-weight: 600;
  font-size: 15px;
  letter-spacing: -0.01em;
  color: var(--text-primary);
}

.logo-icon {
  width: 20px;
  height: 20px;
  background: var(--accent-cyan);
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  color: white;
}

.tabs {
  display: flex;
  align-items: stretch;
  flex: 1;
}

.tab {
  padding: 0 20px;
  background: none;
  border: none;
  border-right: 1px solid var(--border);
  color: var(--text-secondary);
  font-family: var(--font-ui);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  gap: 6px;
  position: relative;
}

.tab:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.tab.active {
  background: transparent;
  color: var(--accent-cyan);
  font-weight: 600;
}

.tab.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--accent-cyan);
}

.tab-icon {
  font-size: 16px;
}

/* Main Content */
.main-content {
  flex: 1;
  overflow: hidden;
}

/* Fade transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
