<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import ChatPanel from './components/ChatPanel.vue'

const router = useRouter()
const route = useRoute()

// Chatbox toggle state
const STORAGE_KEY = 'datavint_chatbox_collapsed'
const chatboxCollapsed = ref(false)

function toggleChatbox() {
  chatboxCollapsed.value = !chatboxCollapsed.value
  try {
    localStorage.setItem(STORAGE_KEY, String(chatboxCollapsed.value))
  } catch (e) {
    console.warn('localStorage unavailable:', e)
  }
}

function loadCollapseState() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved !== null) {
      chatboxCollapsed.value = saved === 'true'
    } else if (window.innerWidth < 768) {
      chatboxCollapsed.value = true
    }
  } catch (e) {
    console.warn('localStorage unavailable:', e)
  }
}

function handleKeyboard(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
    e.preventDefault()
    toggleChatbox()
  }
}

onMounted(() => {
  loadCollapseState()
  window.addEventListener('keydown', handleKeyboard)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyboard)
})
</script>

<template>
  <div class="app">
    <!-- Header with Tabs -->
    <header class="header">
      <!-- Hamburger Toggle (LEFT side, always visible) -->
      <button
        class="hamburger-toggle"
        @click="toggleChatbox"
        :title="chatboxCollapsed ? 'Show Assistant (Ctrl+B)' : 'Hide Assistant (Ctrl+B)'"
      >
        <div class="hamburger-icon">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </button>

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

    <!-- Main Content: Split Panel -->
    <div class="content-wrapper">
      <!-- Chat Panel (Left Sidebar - 25%) -->
      <aside
        v-show="!chatboxCollapsed"
        class="chat-sidebar"
        :class="{ collapsed: chatboxCollapsed }"
      >
        <ChatPanel />
      </aside>

      <!-- Main Content Area (Right - 75%) -->
      <main class="main-content" :class="{ 'full-width': chatboxCollapsed }">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
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
  position: relative;
}

/* Hamburger Toggle - FIXED POSITION on left */
.hamburger-toggle {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
  width: 36px;
  height: 36px;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.hamburger-toggle:hover {
  background: var(--bg-hover);
}

.hamburger-icon {
  width: 20px;
  height: 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: stretch;
}

.hamburger-icon span {
  display: block;
  height: 2px;
  background: var(--text-secondary);
  border-radius: 2px;
  transition: all 0.2s ease;
}

.hamburger-toggle:hover .hamburger-icon span {
  background: var(--accent-cyan);
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 24px;
  margin-left: 48px; /* Space for hamburger button */
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

/* Content Wrapper: Split Panel */
.content-wrapper {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* Chat Sidebar */
.chat-sidebar {
  width: 25%;
  min-width: 280px;
  max-width: 400px;
  border-right: 3px solid var(--border);
  transition: transform 0.3s ease, opacity 0.3s ease;
  transform: translateX(0);
  opacity: 1;
  background: var(--bg-panel);
}

.chat-sidebar.collapsed {
  transform: translateX(-100%);
  opacity: 0;
  pointer-events: none;
}

/* Main Content */
.main-content {
  flex: 1;
  overflow: hidden;
  transition: margin-left 0.3s ease;
}

.main-content.full-width {
  margin-left: 0;
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

/* Responsive */
@media (max-width: 768px) {
  .chat-sidebar {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 100;
    width: 80%;
    max-width: none;
  }
}
</style>
