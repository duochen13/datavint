<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '@/services/api'
import ChatPanel from '@/components/ChatPanel.vue'
import CodeEditor from '@/components/CodeEditor.vue'
import Terminal from '@/components/Terminal.vue'
import CodePlayground from '@/components/CodePlayground.vue'

// Chatbox toggle state
const STORAGE_KEY = 'playgroundChatboxCollapsed'
const chatboxCollapsed = ref(false)
const isAnimating = ref(false)

const activeTab = ref('code-playground')

const code = ref('')

const terminalOutput = ref([
  { type: 'info', text: 'DataVint v0.2.0 - Ready' },
  { type: 'info', text: 'Press Run Code to execute ▶' }
])

const isRunning = ref(false)

function switchTab(tab) {
  activeTab.value = tab
}

async function runCode() {
  isRunning.value = true
  terminalOutput.value.push({ type: 'prompt', text: '$ python analysis.py' })
  terminalOutput.value.push({ type: 'info', text: 'Running analysis...' })

  try {
    const response = await api.playground.execute(code.value)

    if (response.data.success) {
      // Add stdout
      if (response.data.output.stdout) {
        terminalOutput.value.push({
          type: 'output',
          text: response.data.output.stdout
        })
      }

      // Add statistics
      if (response.data.output.statistics) {
        const stats = response.data.output.statistics
        terminalOutput.value.push({
          type: 'success',
          text: `✓ Statistics: ${stats.n_rows} rows, ${stats.n_cols} columns`
        })
      }

      // Add issues
      if (response.data.output.issues && response.data.output.issues.length > 0) {
        terminalOutput.value.push({
          type: 'output',
          text: `\n${response.data.output.issues.length} issue(s) detected:\n`
        })
        response.data.output.issues.forEach(issue => {
          const icon = issue.severity === 'HIGH' ? '🔴' : issue.severity === 'MEDIUM' ? '🟡' : '🟢'
          terminalOutput.value.push({
            type: 'output',
            text: `${icon} [${issue.type}] ${issue.feature || 'Dataset-level'}`
          })
          terminalOutput.value.push({
            type: 'output',
            text: `   ${issue.description}`
          })
        })
      }

      terminalOutput.value.push({ type: 'success', text: '\n✓ Analysis complete' })
    } else {
      terminalOutput.value.push({
        type: 'error',
        text: `Error: ${response.data.error}`
      })
    }
  } catch (error) {
    terminalOutput.value.push({
      type: 'error',
      text: `Failed to execute: ${error.message}`
    })
  } finally {
    isRunning.value = false
  }
}

function clearCode() {
  code.value = ''
}

function clearTerminal() {
  terminalOutput.value = [{ type: 'info', text: 'Terminal cleared' }]
}

function handleMessage(message) {
  // Handle chat message - can integrate with API later
  console.log('Chat message:', message)
}

// Chatbox toggle functionality
function safeLocalStorage(operation, fallback = null) {
  try {
    return operation()
  } catch (e) {
    console.warn('localStorage unavailable:', e)
    return fallback
  }
}

function toggleChatbox() {
  if (isAnimating.value) return // Prevent rapid toggle during animation

  isAnimating.value = true
  chatboxCollapsed.value = !chatboxCollapsed.value
  saveCollapseState(chatboxCollapsed.value)

  setTimeout(() => {
    isAnimating.value = false
  }, 300) // Match CSS transition duration
}

function saveCollapseState(value) {
  safeLocalStorage(() => localStorage.setItem(STORAGE_KEY, String(value)))
}

function loadCollapseState() {
  const saved = safeLocalStorage(() => localStorage.getItem(STORAGE_KEY))
  if (saved !== null) {
    chatboxCollapsed.value = saved === 'true'
  } else if (window.innerWidth < 768) {
    // Auto-collapse on mobile
    chatboxCollapsed.value = true
  }
}

function handleKeyboard(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
    e.preventDefault()
    toggleChatbox()
  }
}

// Debounce utility
function debounce(fn, delay) {
  let timeoutId
  return function (...args) {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn.apply(this, args), delay)
  }
}

function handleResize() {
  if (window.innerWidth < 768 && !chatboxCollapsed.value) {
    // Auto-collapse on mobile resize
    chatboxCollapsed.value = true
    saveCollapseState(true)
  }
}

const debouncedResize = debounce(handleResize, 250)

onMounted(() => {
  loadCollapseState()
  window.addEventListener('keydown', handleKeyboard)
  window.addEventListener('resize', debouncedResize)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyboard)
  window.removeEventListener('resize', debouncedResize)
})
</script>

<template>
  <div class="playground-view">
    <div class="split-panel">
      <!-- Collapse/Expand Button -->
      <button
        class="chatbox-toggle"
        @click="toggleChatbox"
        :title="chatboxCollapsed ? 'Expand chatbox (Ctrl+B)' : 'Collapse chatbox (Ctrl+B)'"
        :aria-label="chatboxCollapsed ? 'Expand chatbox' : 'Collapse chatbox'"
      >
        {{ chatboxCollapsed ? '›' : '‹' }}
      </button>

      <!-- Chat Panel (Left - 25%) -->
      <ChatPanel
        v-show="!chatboxCollapsed"
        class="left-panel"
        :class="{ collapsed: chatboxCollapsed }"
        @send-message="handleMessage"
      />

      <!-- IDE (Right - 75%) -->
      <div class="right-panel">
        <!-- Tab Switcher -->
        <div class="tab-bar">
          <button
            class="tab-button"
            :class="{ active: activeTab === 'custom-code' }"
            @click="switchTab('custom-code')"
          >
            Custom Code
          </button>
          <button
            class="tab-button"
            :class="{ active: activeTab === 'code-playground' }"
            @click="switchTab('code-playground')"
          >
            Code Playground
          </button>
        </div>

        <!-- Custom Code Tab -->
        <template v-if="activeTab === 'custom-code'">
          <!-- Toolbar -->
          <div class="toolbar">
            <div class="file-tabs">
              <div class="file-tab active">analysis.py</div>
            </div>
            <div class="actions">
              <button class="btn secondary" @click="clearCode">
                🗑 Clear
              </button>
              <button class="btn primary" @click="runCode" :disabled="isRunning">
                {{ isRunning ? '⏳ Running...' : '▶ Run Code' }}
              </button>
            </div>
          </div>

          <!-- Code Editor -->
          <CodeEditor v-model="code" />

          <!-- Terminal Output -->
          <Terminal
            :output="terminalOutput"
            :running="isRunning"
            @clear="clearTerminal"
          />
        </template>

        <!-- Code Playground Tab -->
        <CodePlayground v-else-if="activeTab === 'code-playground'" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.playground-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.split-panel {
  position: relative;
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* Chatbox Toggle Button */
.chatbox-toggle {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  z-index: 100;
  width: 24px;
  height: 48px;
  background: var(--bg-panel);
  border: 2px solid var(--border);
  border-left: none;
  border-radius: 0 8px 8px 0;
  color: var(--text-secondary);
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chatbox-toggle:hover {
  background: var(--bg-hover);
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
}

.chatbox-toggle:active {
  transform: translateY(-50%) scale(0.95);
}

/* Chat Panel with Transitions */
.left-panel {
  width: 25%;
  min-width: 280px;
  border-right: 3px solid var(--border);
  transition: transform 0.3s ease, opacity 0.3s ease;
  transform: translateX(0);
  opacity: 1;
}

.left-panel.collapsed {
  transform: translateX(-100%);
  opacity: 0;
  pointer-events: none;
}

.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  transition: margin-left 0.3s ease;
  margin-left: 0;
}

/* Reclaim chatbox space when collapsed */
.split-panel:has(.left-panel.collapsed) .right-panel {
  margin-left: -25%;
}

/* Tab Bar */
.tab-bar {
  display: flex;
  gap: 0;
  background: var(--bg-panel);
  border-bottom: 2px solid var(--border);
  padding: 0 16px;
}

.tab-button {
  padding: 12px 24px;
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.tab-button:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.tab-button.active {
  color: var(--accent-cyan);
  border-bottom-color: var(--accent-cyan);
  background: var(--bg-dark);
}

/* Toolbar */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-panel);
  border-bottom: 2px solid var(--border);
}

.file-tabs {
  display: flex;
  gap: 8px;
}

.file-tab {
  padding: 6px 16px;
  background: var(--bg-hover);
  border: 2px solid var(--border);
  border-radius: 6px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-primary);
  font-weight: 600;
}

.file-tab.active {
  background: var(--bg-editor);
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
}

.actions {
  display: flex;
  gap: 12px;
}

.btn {
  padding: 8px 16px;
  border: 2px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn.primary {
  background: var(--accent-cyan);
  color: var(--bg-dark);
  border-color: var(--accent-cyan);
}

.btn.primary:hover:not(:disabled) {
  background: var(--accent-lime);
  border-color: var(--accent-lime);
  transform: translateY(-1px);
}

.btn.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn.secondary {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.btn.secondary:hover {
  background: var(--bg-panel);
  color: var(--text-primary);
  border-color: var(--border-active);
}
</style>
