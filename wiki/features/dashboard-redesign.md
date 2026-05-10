# DataVint Dashboard Redesign - Implementation Plan

**Date**: 2026-05-09
**Status**: Ready for Implementation
**Estimated Effort**: 6-8 hours

## Executive Summary

Transform the DataVint dashboard from tab-isolated functionality to a unified conversational data exploration experience with:
- Persistent chatbox across all tabs (command center)
- Intelligent navigation with hybrid routing
- Kaggle-style data profiling view
- Auto-generated dataset descriptions
- Single dataset architecture (extensible to multi-dataset later)

## User Decisions

| Decision | Choice |
|----------|--------|
| Tab switching behavior | Chat is tab-agnostic (persistent context) |
| Navigation strategy | Hybrid: Auto-navigate for clear cases, suggest for ambiguous |
| Multi-dataset support | Not in MVP, design for future extensibility |
| Phase 4 features | Dataset description auto-generation only |
| Hamburger toggle | Keep it, fix overlap with Clear button |

## Architecture Changes

### Current Architecture
```
App.vue (header + router-view)
├── PlaygroundView (has ChatPanel)
│   ├── ChatPanel (upload + chat)
│   └── CodePlayground/CodeEditor
├── DataView (upload form)
└── VisualizationView
```

### New Architecture
```
App.vue (header + persistent ChatPanel + router-view)
├── ChatPanel (persistent sidebar, 25%)
└── Main Content (75%)
    ├── PlaygroundView (CodePlayground tabs only)
    ├── DataView (Kaggle-style profiling)
    └── VisualizationView
```

### State Management (NEW)
```javascript
// Pinia Store: datasetStore.js
{
  currentDataset: {
    id: string,
    filename: string,
    uploadedAt: timestamp,
    stats: DatasetStatistics,
    issues: Issue[],
    preview: { sample: [], rows: number, columns: number },
    description: string  // LLM-generated
  },
  chatHistory: Message[],
  isAnalyzing: boolean
}
```

## Implementation Phases

### Phase 1: Foundation (2-3 hours)
**Goal**: Create state management and move ChatPanel to app level

### Phase 2: DataView Redesign (2-3 hours)
**Goal**: Build Kaggle-style profiling view

### Phase 3: Navigation & Intelligence (1-2 hours)
**Goal**: Implement hybrid navigation and dataset description generation

### Phase 4: Polish & Testing (1 hour)
**Goal**: Fix UI issues, test complete flow

---

## Detailed Implementation Steps

## PHASE 1: Foundation

### Step 1.1: Create Pinia Store (30 min)

**File**: `client/src/stores/datasetStore.js` (CREATE)

```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useDatasetStore = defineStore('dataset', () => {
  // Current dataset
  const currentDataset = ref(null)

  // Chat history (persisted across tabs)
  const chatHistory = ref([])

  // Upload state
  const isAnalyzing = ref(false)
  const uploadedFile = ref(null)

  /**
   * Set current dataset after upload + analysis
   */
  function setDataset(dataset) {
    currentDataset.value = {
      ...dataset,
      uploadedAt: Date.now()
    }
  }

  /**
   * Add message to chat history
   */
  function addMessage(content, type = 'user') {
    chatHistory.value.push({
      content,
      type,
      id: Date.now()
    })
  }

  /**
   * Clear all chat history
   */
  function clearHistory() {
    chatHistory.value = []
  }

  /**
   * Reset entire store (new session)
   */
  function reset() {
    currentDataset.value = null
    chatHistory.value = []
    isAnalyzing.value = false
    uploadedFile.value = null
  }

  return {
    // State
    currentDataset,
    chatHistory,
    isAnalyzing,
    uploadedFile,

    // Actions
    setDataset,
    addMessage,
    clearHistory,
    reset
  }
})
```

**Install Pinia** (if not already):
```bash
cd client
npm install pinia
```

**Register in `client/src/main.js`**:
```javascript
import { createPinia } from 'pinia'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.mount('#app')
```

### Step 1.2: Update ChatPanel to Use Store (45 min)

**File**: `client/src/components/ChatPanel.vue` (MODIFY)

**Changes**:
1. Replace local `messages` ref with store
2. Replace local `uploadedFile` ref with store
3. After successful analysis, save to store AND add navigation CTA
4. Fix hamburger/clear button overlap

**Key Code Changes**:

```vue
<script setup>
import { ref, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { uploadAndAnalyzeCSV } from '../services/codePlaygroundApi'
import { useDatasetStore } from '../stores/datasetStore'

const router = useRouter()
const store = useDatasetStore()
const emit = defineEmits(['send-message'])

// Use store instead of local state
const messages = computed(() => store.chatHistory)
const uploadedFile = computed(() => store.uploadedFile)
const isAnalyzing = computed(() => store.isAnalyzing)

const input = ref('')
const chatMessages = ref(null)
const textarea = ref(null)
const fileInput = ref(null)

function addMessage(content, type = 'user') {
  store.addMessage(content, type)

  nextTick(() => {
    if (chatMessages.value) {
      chatMessages.value.scrollTop = chatMessages.value.scrollHeight
    }
  })
}

function handleFileUpload(event) {
  const file = event.target.files[0]
  if (!file) return

  store.uploadedFile = file
  addMessage(`📎 Uploaded: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`, 'assistant')
  addMessage('What would you like to analyze? (e.g., "check for missing values", "find duplicates")', 'assistant')
}

async function sendMessage() {
  const message = input.value.trim()
  if (!message) return

  addMessage(message, 'user')
  input.value = ''

  if (textarea.value) {
    textarea.value.style.height = 'auto'
  }

  if (uploadedFile.value) {
    store.isAnalyzing = true
    addMessage('🔄 Analyzing your dataset...', 'assistant')

    try {
      const result = await uploadAndAnalyzeCSV(uploadedFile.value, message)

      if (result.success) {
        // Save to store
        store.setDataset({
          id: `dataset_${Date.now()}`,
          filename: uploadedFile.value.name,
          stats: result.data?.stats,
          issues: result.data?.issues || [],
          preview: result.data?.preview,
          description: null  // Will be generated in Phase 3
        })

        // Show output
        addMessage(result.output, 'assistant')

        // Show generated code
        if (result.generated_code && !result.generated_code.includes('# Skill:')) {
          addMessage('Generated code:\n```python\n' + result.generated_code + '\n```', 'assistant')
        }

        // Navigation CTA (hybrid logic)
        const shouldNavigate = shouldSuggestDataView(result.data?.issues)
        if (shouldNavigate) {
          addMessage('📊 View detailed profiling in Raw Data tab →', 'assistant')
          // Add a clickable navigation button (see template changes below)
        }
      } else {
        addMessage('❌ Analysis failed: ' + (result.error || 'Unknown error'), 'assistant')
      }
    } catch (error) {
      console.error('Analysis error:', error)
      addMessage('❌ Failed to analyze: ' + error.message, 'assistant')
    } finally {
      store.isAnalyzing = false
      store.uploadedFile = null
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    }
  } else {
    emit('send-message', message)
  }
}

/**
 * Hybrid navigation logic:
 * - Auto-suggest if issues detected
 * - Auto-suggest for specific queries like "missing values", "duplicates", "quality"
 */
function shouldSuggestDataView(issues) {
  if (!issues || issues.length === 0) return false

  // If HIGH severity issues, definitely suggest
  const highSeverity = issues.filter(i => i.severity === 'HIGH')
  if (highSeverity.length > 0) return true

  // If more than 3 issues total, suggest
  if (issues.length >= 3) return true

  return false
}

function navigateToDataView() {
  router.push('/data')
}

function clearChatHistory() {
  store.clearHistory()
}

// ... rest of the component
</script>

<template>
  <div class="chat-panel">
    <div class="panel-header">
      <div class="panel-title">Assistant</div>
      <div class="header-controls">
        <div class="status-indicator">
          <div class="status-dot"></div>
          <span>READY</span>
        </div>
        <button
          v-if="messages.length > 0"
          class="clear-history-btn"
          @click="clearChatHistory"
          title="Clear chat history"
        >
          🗑️ Clear
        </button>
      </div>
    </div>

    <div ref="chatMessages" class="chat-messages">
      <!-- Welcome message -->
      <div class="welcome-message">
        <div class="welcome-title">👋 Welcome to DataVint Playground</div>
        <div class="welcome-text">
          Interactive IDE for exploring data quality detection. Try these commands:
        </div>
        <div class="welcome-commands">
          <div class="welcome-command">Analyze my dataset</div>
          <div class="welcome-command">Show me data quality issues</div>
          <div class="welcome-command">Check for missing values</div>
          <div class="welcome-command">Find duplicate rows</div>
        </div>
      </div>

      <!-- Messages -->
      <div v-for="msg in messages" :key="msg.id" :class="['message', msg.type]">
        <div class="message-label">{{ msg.type === 'user' ? 'You' : 'DataVint' }}</div>
        <div class="message-content">
          {{ msg.content }}

          <!-- Navigation CTA button -->
          <button
            v-if="msg.content.includes('View detailed profiling in Raw Data tab')"
            class="nav-cta-button"
            @click="navigateToDataView"
          >
            Go to Raw Data →
          </button>
        </div>
      </div>
    </div>

    <!-- Input section (unchanged) -->
    <div class="chat-input-container">
      <div class="upload-section">
        <input
          ref="fileInput"
          type="file"
          accept=".csv"
          @change="handleFileUpload"
          style="display: none"
        />
        <button
          class="upload-button"
          @click="fileInput.click()"
          :disabled="isAnalyzing"
        >
          📎 Upload CSV
        </button>
        <span v-if="uploadedFile" class="uploaded-filename">
          {{ uploadedFile.name }}
        </span>
      </div>

      <div class="chat-input-wrapper">
        <textarea
          ref="textarea"
          v-model="input"
          class="chat-input"
          :placeholder="uploadedFile ? 'Ask about your dataset...' : 'Ask me about check missing value, duplication rate etc'"
          rows="1"
          @keypress="handleKeypress"
          @input="handleInput"
          :disabled="isAnalyzing"
          autofocus
        ></textarea>
        <button class="send-button" @click="sendMessage" :disabled="isAnalyzing">
          {{ isAnalyzing ? '⏳' : '➤' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ... existing styles ... */

/* Navigation CTA Button */
.nav-cta-button {
  margin-top: 12px;
  padding: 10px 20px;
  background: var(--accent-cyan);
  border: none;
  border-radius: 6px;
  color: var(--bg-dark);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-block;
}

.nav-cta-button:hover {
  background: var(--accent-lime);
  transform: translateY(-1px);
}
</style>
```

### Step 1.3: Move ChatPanel to App.vue (45 min)

**File**: `client/src/App.vue` (MODIFY)

**Changes**:
1. Add persistent ChatPanel sidebar
2. Add split-panel layout
3. Add hamburger toggle (fix overlap issue)
4. Adjust main content area

```vue
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
```

### Step 1.4: Update PlaygroundView (30 min)

**File**: `client/src/views/PlaygroundView.vue` (MODIFY)

**Changes**:
1. Remove ChatPanel component (now in App.vue)
2. Remove split-panel layout
3. Remove hamburger toggle
4. Keep CodePlayground tabs functionality

```vue
<script setup>
import { ref } from 'vue'
import api from '@/services/api'
import CodeEditor from '@/components/CodeEditor.vue'
import Terminal from '@/components/Terminal.vue'
import CodePlayground from '@/components/CodePlayground.vue'

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
      if (response.data.output.stdout) {
        terminalOutput.value.push({
          type: 'output',
          text: response.data.output.stdout
        })
      }

      if (response.data.output.statistics) {
        const stats = response.data.output.statistics
        terminalOutput.value.push({
          type: 'success',
          text: `✓ Statistics: ${stats.n_rows} rows, ${stats.n_cols} columns`
        })
      }

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
</script>

<template>
  <div class="playground-view">
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

      <CodeEditor v-model="code" />

      <Terminal
        :output="terminalOutput"
        :running="isRunning"
        @clear="clearTerminal"
      />
    </template>

    <!-- Code Playground Tab -->
    <CodePlayground v-else-if="activeTab === 'code-playground'" />
  </div>
</template>

<style scoped>
.playground-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-dark);
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
```

---

## PHASE 2: DataView Redesign

### Step 2.1: Create DatasetSummary Component (30 min)

**File**: `client/src/components/DatasetSummary.vue` (CREATE)

```vue
<script setup>
import { computed } from 'vue'

const props = defineProps({
  dataset: {
    type: Object,
    required: true
  }
})

const stats = computed(() => props.dataset.stats)
const issues = computed(() => props.dataset.issues || [])

const highSeverityCount = computed(() =>
  issues.value.filter(i => i.severity === 'HIGH').length
)

const mediumSeverityCount = computed(() =>
  issues.value.filter(i => i.severity === 'MEDIUM').length
)

const lowSeverityCount = computed(() =>
  issues.value.filter(i => i.severity === 'LOW').length
)

// Auto-generated description (will be replaced with LLM in Phase 3)
const description = computed(() => {
  if (props.dataset.description) return props.dataset.description

  // Placeholder description
  return `Dataset with ${stats.value?.n_rows || 0} rows and ${stats.value?.n_cols || 0} features. ` +
         `${issues.value.length} data quality issue(s) detected across ${highSeverityCount.value} high-severity, ` +
         `${mediumSeverityCount.value} medium-severity, and ${lowSeverityCount.value} low-severity categories.`
})
</script>

<template>
  <div class="dataset-summary">
    <div class="summary-header">
      <h2 class="summary-title">About this dataset</h2>
      <div class="dataset-meta">
        <span class="meta-item">
          📁 {{ dataset.filename }}
        </span>
        <span class="meta-item">
          📅 {{ new Date(dataset.uploadedAt).toLocaleString() }}
        </span>
      </div>
    </div>

    <p class="summary-description">{{ description }}</p>

    <div class="summary-stats">
      <div class="stat-card">
        <div class="stat-value">{{ stats?.n_rows?.toLocaleString() || 0 }}</div>
        <div class="stat-label">Rows</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats?.n_cols || 0 }}</div>
        <div class="stat-label">Columns</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ issues.length }}</div>
        <div class="stat-label">Issues Detected</div>
      </div>
      <div class="stat-card severity-breakdown">
        <div class="severity-item high" v-if="highSeverityCount > 0">
          <span class="severity-dot"></span>
          {{ highSeverityCount }} High
        </div>
        <div class="severity-item medium" v-if="mediumSeverityCount > 0">
          <span class="severity-dot"></span>
          {{ mediumSeverityCount }} Medium
        </div>
        <div class="severity-item low" v-if="lowSeverityCount > 0">
          <span class="severity-dot"></span>
          {{ lowSeverityCount }} Low
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dataset-summary {
  padding: 24px;
  background: var(--bg-panel);
  border-bottom: 2px solid var(--border);
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.summary-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.dataset-meta {
  display: flex;
  gap: 16px;
}

.meta-item {
  font-size: 13px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

.summary-description {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
  margin: 0 0 20px 0;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 16px;
}

.stat-card {
  padding: 16px;
  background: var(--bg-dark);
  border: 2px solid var(--border);
  border-radius: 8px;
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--accent-cyan);
  font-family: var(--font-mono);
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 4px;
}

.severity-breakdown {
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: center;
  align-items: flex-start;
  padding: 12px 16px;
}

.severity-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
}

.severity-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.severity-item.high {
  color: #ff5252;
}

.severity-item.high .severity-dot {
  background: #ff5252;
}

.severity-item.medium {
  color: #ffa726;
}

.severity-item.medium .severity-dot {
  background: #ffa726;
}

.severity-item.low {
  color: #66bb6a;
}

.severity-item.low .severity-dot {
  background: #66bb6a;
}
</style>
```

### Step 2.2: Create ColumnCard Component (45 min)

**File**: `client/src/components/ColumnCard.vue` (CREATE)

```vue
<script setup>
import { computed } from 'vue'

const props = defineProps({
  columnName: {
    type: String,
    required: true
  },
  stats: {
    type: Object,
    required: true
  },
  issues: {
    type: Array,
    default: () => []
  }
})

const completeness = computed(() => {
  if (props.stats.completeness !== undefined) {
    return (props.stats.completeness * 100).toFixed(1)
  }
  return 100
})

const qualityBadge = computed(() => {
  const highIssues = props.issues.filter(i => i.severity === 'HIGH')
  const mediumIssues = props.issues.filter(i => i.severity === 'MEDIUM')

  if (highIssues.length > 0) return { label: 'Critical', class: 'critical' }
  if (mediumIssues.length > 0) return { label: 'Warning', class: 'warning' }
  return { label: 'Clean', class: 'clean' }
})

const distinctness = computed(() => {
  if (props.stats.distinctness !== undefined) {
    return (props.stats.distinctness * 100).toFixed(1)
  }
  return null
})

const entropy = computed(() => {
  if (props.stats.entropy !== undefined) {
    return props.stats.entropy.toFixed(2)
  }
  return null
})
</script>

<template>
  <div class="column-card">
    <div class="column-header">
      <div class="column-info">
        <h3 class="column-name">{{ columnName }}</h3>
        <span class="column-type">{{ stats.type || 'unknown' }}</span>
      </div>
      <div class="quality-badge" :class="qualityBadge.class">
        {{ qualityBadge.label }}
      </div>
    </div>

    <div class="column-metrics">
      <!-- Completeness Bar -->
      <div class="metric-row">
        <span class="metric-label">Completeness</span>
        <div class="completeness-bar">
          <div class="completeness-fill" :style="{ width: completeness + '%' }"></div>
        </div>
        <span class="metric-value">{{ completeness }}%</span>
      </div>

      <!-- Distinct Count -->
      <div class="metric-row" v-if="stats.distinct_count !== undefined">
        <span class="metric-label">Distinct Values</span>
        <span class="metric-value">{{ stats.distinct_count.toLocaleString() }}</span>
      </div>

      <!-- Distinctness -->
      <div class="metric-row" v-if="distinctness">
        <span class="metric-label">Distinctness</span>
        <span class="metric-value">{{ distinctness }}%</span>
      </div>

      <!-- Entropy -->
      <div class="metric-row" v-if="entropy">
        <span class="metric-label">Entropy</span>
        <span class="metric-value">{{ entropy }}</span>
      </div>

      <!-- Mean (for numeric) -->
      <div class="metric-row" v-if="stats.mean !== undefined">
        <span class="metric-label">Mean</span>
        <span class="metric-value">{{ stats.mean.toFixed(2) }}</span>
      </div>

      <!-- Std Dev (for numeric) -->
      <div class="metric-row" v-if="stats.std !== undefined">
        <span class="metric-label">Std Dev</span>
        <span class="metric-value">{{ stats.std.toFixed(2) }}</span>
      </div>
    </div>

    <!-- Issues List -->
    <div v-if="issues.length > 0" class="column-issues">
      <div class="issues-header">Issues Detected</div>
      <div v-for="(issue, idx) in issues" :key="idx" class="issue-item" :class="issue.severity.toLowerCase()">
        <span class="issue-icon">{{ issue.severity === 'HIGH' ? '🔴' : issue.severity === 'MEDIUM' ? '🟡' : '🟢' }}</span>
        <span class="issue-text">{{ issue.description }}</span>
      </div>
    </div>

    <!-- Mini Histogram Placeholder (future enhancement) -->
    <div class="histogram-placeholder">
      <div class="histogram-label">Distribution</div>
      <div class="histogram-bars">
        <!-- Placeholder for future histogram visualization -->
        <div class="histogram-message">Histogram visualization coming soon</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.column-card {
  background: var(--bg-panel);
  border: 2px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s;
}

.column-card:hover {
  border-color: var(--accent-cyan);
  box-shadow: 0 4px 12px rgba(0, 240, 255, 0.1);
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--border);
}

.column-info {
  flex: 1;
}

.column-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 4px 0;
  font-family: var(--font-mono);
}

.column-type {
  font-size: 12px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.quality-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.quality-badge.clean {
  background: rgba(102, 187, 106, 0.15);
  color: #66bb6a;
}

.quality-badge.warning {
  background: rgba(255, 167, 38, 0.15);
  color: #ffa726;
}

.quality-badge.critical {
  background: rgba(255, 82, 82, 0.15);
  color: #ff5252;
}

.column-metrics {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.metric-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.metric-label {
  font-size: 12px;
  color: var(--text-muted);
  min-width: 100px;
}

.metric-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-mono);
  margin-left: auto;
}

.completeness-bar {
  flex: 1;
  height: 6px;
  background: var(--bg-dark);
  border-radius: 3px;
  overflow: hidden;
}

.completeness-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent-cyan), var(--accent-lime));
  transition: width 0.3s ease;
}

.column-issues {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 2px solid var(--border);
}

.issues-header {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.issue-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px;
  background: var(--bg-dark);
  border-radius: 6px;
  margin-bottom: 6px;
}

.issue-icon {
  font-size: 14px;
}

.issue-text {
  flex: 1;
  font-size: 12px;
  line-height: 1.4;
  color: var(--text-secondary);
}

.histogram-placeholder {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 2px solid var(--border);
}

.histogram-label {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.histogram-bars {
  height: 80px;
  background: var(--bg-dark);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.histogram-message {
  font-size: 11px;
  color: var(--text-muted);
  font-style: italic;
}
</style>
```

### Step 2.3: Create DataSamples Component (30 min)

**File**: `client/src/components/DataSamples.vue` (CREATE)

```vue
<script setup>
import { computed } from 'vue'

const props = defineProps({
  preview: {
    type: Object,
    required: true
  },
  issues: {
    type: Array,
    default: () => []
  }
})

const columns = computed(() => {
  if (!props.preview.sample || props.preview.sample.length === 0) return []
  return Object.keys(props.preview.sample[0])
})

const rows = computed(() => props.preview.sample || [])

// Identify problematic columns based on issues
const problematicColumns = computed(() => {
  const cols = new Set()
  props.issues.forEach(issue => {
    if (issue.feature) {
      cols.add(issue.feature)
    }
  })
  return cols
})

function isCellProblematic(column) {
  return problematicColumns.value.has(column)
}
</script>

<template>
  <div class="data-samples">
    <div class="samples-header">
      <h3>Data Samples</h3>
      <span class="samples-count">Showing first {{ rows.length }} rows</span>
    </div>

    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th class="row-number-header">#</th>
            <th
              v-for="col in columns"
              :key="col"
              :class="{ 'problematic-column': isCellProblematic(col) }"
            >
              {{ col }}
              <span v-if="isCellProblematic(col)" class="warning-icon" title="Issues detected">⚠️</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in rows" :key="idx">
            <td class="row-number">{{ idx + 1 }}</td>
            <td
              v-for="col in columns"
              :key="col"
              :class="{
                'null-cell': row[col] === null || row[col] === undefined || row[col] === '',
                'problematic-column': isCellProblematic(col)
              }"
            >
              <span v-if="row[col] === null || row[col] === undefined || row[col] === ''" class="null-value">
                NULL
              </span>
              <span v-else>{{ row[col] }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.data-samples {
  padding: 24px;
  background: var(--bg-dark);
}

.samples-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.samples-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.samples-count {
  font-size: 13px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.table-container {
  overflow-x: auto;
  border: 2px solid var(--border);
  border-radius: 8px;
  background: var(--bg-panel);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  font-family: var(--font-mono);
}

.data-table thead {
  background: var(--bg-dark);
  position: sticky;
  top: 0;
  z-index: 10;
}

.data-table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 700;
  color: var(--text-primary);
  border-bottom: 2px solid var(--border);
  white-space: nowrap;
}

.row-number-header {
  width: 50px;
  text-align: center;
  color: var(--text-muted);
}

.problematic-column {
  background: rgba(255, 167, 38, 0.05);
}

.warning-icon {
  font-size: 12px;
  margin-left: 6px;
}

.data-table td {
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  color: var(--text-secondary);
}

.data-table tbody tr:hover {
  background: var(--bg-hover);
}

.row-number {
  text-align: center;
  color: var(--text-muted);
  font-weight: 600;
}

.null-cell {
  background: rgba(255, 82, 82, 0.08);
}

.null-value {
  color: #ff5252;
  font-style: italic;
  font-weight: 600;
}
</style>
```

### Step 2.4: Replace DataView.vue (45 min)

**File**: `client/src/views/DataView.vue` (REPLACE)

```vue
<script setup>
import { computed } from 'vue'
import { useDatasetStore } from '@/stores/datasetStore'
import DatasetSummary from '@/components/DatasetSummary.vue'
import ColumnCard from '@/components/ColumnCard.vue'
import DataSamples from '@/components/DataSamples.vue'

const store = useDatasetStore()

const dataset = computed(() => store.currentDataset)
const hasDataset = computed(() => dataset.value !== null)

// Group issues by feature (column)
const issuesByFeature = computed(() => {
  if (!dataset.value?.issues) return {}

  const grouped = {}
  dataset.value.issues.forEach(issue => {
    if (issue.feature) {
      if (!grouped[issue.feature]) {
        grouped[issue.feature] = []
      }
      grouped[issue.feature].push(issue)
    }
  })
  return grouped
})

// Get column names from stats
const columns = computed(() => {
  if (!dataset.value?.stats?.features) return []
  return Object.keys(dataset.value.stats.features)
})

function getColumnStats(columnName) {
  if (!dataset.value?.stats?.features) return {}
  return dataset.value.stats.features[columnName] || {}
}

function getColumnIssues(columnName) {
  return issuesByFeature.value[columnName] || []
}
</script>

<template>
  <div class="data-view">
    <!-- No Dataset State -->
    <div v-if="!hasDataset" class="empty-state">
      <div class="empty-icon">📊</div>
      <h3>No dataset loaded</h3>
      <p>Upload a CSV file using the Assistant to view detailed profiling</p>
      <div class="help-text">
        💡 Go to any tab and upload your dataset through the chat panel on the left
      </div>
    </div>

    <!-- Dataset Loaded: Kaggle-style View -->
    <div v-else class="profiling-view">
      <!-- About Dataset Section -->
      <DatasetSummary :dataset="dataset" />

      <!-- Columns Grid -->
      <div class="columns-section">
        <div class="section-header">
          <h3>Features & Data Quality</h3>
          <span class="column-count">{{ columns.length }} columns</span>
        </div>

        <div class="columns-grid">
          <ColumnCard
            v-for="col in columns"
            :key="col"
            :column-name="col"
            :stats="getColumnStats(col)"
            :issues="getColumnIssues(col)"
          />
        </div>
      </div>

      <!-- Data Samples -->
      <DataSamples
        v-if="dataset.preview"
        :preview="dataset.preview"
        :issues="dataset.issues"
      />
    </div>
  </div>
</template>

<style scoped>
.data-view {
  height: 100%;
  overflow-y: auto;
  background: var(--bg-dark);
}

/* Empty State */
.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  text-align: center;
}

.empty-icon {
  font-size: 80px;
  margin-bottom: 24px;
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}

.empty-state p {
  font-size: 15px;
  color: var(--text-secondary);
  margin: 0 0 24px 0;
}

.help-text {
  padding: 16px 24px;
  background: linear-gradient(135deg, rgba(0, 240, 255, 0.08), rgba(164, 255, 0, 0.08));
  border: 2px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  color: var(--text-secondary);
  max-width: 500px;
}

/* Profiling View */
.profiling-view {
  display: flex;
  flex-direction: column;
}

/* Columns Section */
.columns-section {
  padding: 24px;
  background: var(--bg-dark);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.column-count {
  font-size: 13px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.columns-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

/* Responsive */
@media (max-width: 768px) {
  .columns-grid {
    grid-template-columns: 1fr;
  }
}
</style>
```

---

## PHASE 3: Navigation & Intelligence

### Step 3.1: Add Dataset Description Generation (Backend) (30 min)

**File**: `server/api/services/description_generator.py` (CREATE)

```python
"""
Dataset Description Generator - LLM-powered dataset summarization

Generates human-readable "About this dataset" descriptions using Claude API.
"""

from anthropic import Anthropic
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Initialize Anthropic client
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

DESCRIPTION_PROMPT = """You are a data analyst writing a concise dataset description for a data quality platform.

Given the dataset statistics and issues detected, write a 2-3 sentence description that:
1. Summarizes what the dataset contains (infer from column names)
2. Highlights key statistics (rows, columns, data types)
3. Mentions notable data quality issues if any

Be conversational but precise. Write like you're explaining to a colleague.

Dataset Statistics:
- Rows: {n_rows}
- Columns: {n_cols}
- Column names: {columns}
- Data types: {dtypes}
- Issues detected: {issue_count} ({high_severity} high severity, {medium_severity} medium severity)

Write ONLY the description (no markdown, no headings). Maximum 3 sentences.
"""


async def generate_dataset_description(
    stats: Dict[str, Any],
    issues: list,
    columns: list
) -> Optional[str]:
    """
    Generate human-readable dataset description using Claude API.

    Args:
        stats: Dataset statistics from vint.profile()
        issues: List of issues detected
        columns: Column names

    Returns:
        Generated description string, or None if generation fails

    Example output:
        "This dataset contains customer transaction data with 451,017 records across 23 features,
        including demographics, transaction amounts, and fraud indicators. The dataset has notable
        quality issues with 3 columns showing over 30% missing values and a severe class imbalance
        (98.2% negative class)."
    """
    try:
        # Count severity levels
        high_severity = len([i for i in issues if i.get('severity') == 'HIGH'])
        medium_severity = len([i for i in issues if i.get('severity') == 'MEDIUM'])

        # Prepare column sample (first 10)
        column_sample = ', '.join(columns[:10])
        if len(columns) > 10:
            column_sample += ', ...'

        # Infer data types summary
        dtypes_summary = "mixed" if len(set(c.get('type', 'unknown') for c in stats.get('features', {}).values())) > 1 else "numeric"

        # Build prompt
        prompt = DESCRIPTION_PROMPT.format(
            n_rows=stats.get('n_rows', 0),
            n_cols=stats.get('n_cols', 0),
            columns=column_sample,
            dtypes=dtypes_summary,
            issue_count=len(issues),
            high_severity=high_severity,
            medium_severity=medium_severity
        )

        # Call Claude API (Haiku for cost efficiency)
        message = client.messages.create(
            model="claude-haiku-4-0",  # Haiku for fast + cheap descriptions
            max_tokens=150,
            temperature=0.3,  # Slightly creative but consistent
            messages=[{"role": "user", "content": prompt}],
            timeout=10.0
        )

        description = message.content[0].text.strip()
        logger.info(f"Generated dataset description ({len(description)} chars)")
        return description

    except Exception as e:
        logger.error(f"Description generation failed: {e}")
        return None  # Fallback to auto-generated description in frontend
```

### Step 3.2: Integrate Description Generation in Chat API (15 min)

**File**: `server/api/routes/chat.py` (MODIFY)

Add at the top with other imports:
```python
from server.api.services.description_generator import generate_dataset_description
```

Replace lines 297-308 (in the LLM path success response) with:
```python
            # Generate dataset description (async)
            dataset_description = await generate_dataset_description(
                stats=serialized_stats,
                issues=serialized_issues,
                columns=df.columns.tolist()
            )

            return AnalysisResponse(
                success=True,
                generated_code=generated_code,
                output=output_message,
                data={
                    **result_data,
                    'description': dataset_description  # Add description to response
                },
                routing={
                    "method": "llm",
                    "skill_name": None,
                    "confidence": 0.0,
                    "latency_ms": 3000,
                    "cost": 0.03
                }
            )
```

### Step 3.3: Update ChatPanel to Save Description (10 min)

**File**: `client/src/components/ChatPanel.vue` (MODIFY)

In the `sendMessage()` function, update the `store.setDataset()` call:

```javascript
// Save to store (with LLM-generated description)
store.setDataset({
  id: `dataset_${Date.now()}`,
  filename: uploadedFile.value.name,
  stats: result.data?.stats,
  issues: result.data?.issues || [],
  preview: result.data?.preview,
  description: result.data?.description || null  // LLM description from backend
})
```

---

## PHASE 4: Polish & Testing

### Step 4.1: Fix ChatPanel Header Overlap (15 min)

**File**: `client/src/components/ChatPanel.vue` (MODIFY)

Update the styles for `.panel-header` to prevent overlap between hamburger and clear button:

```vue
<style scoped>
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 16px 16px 56px; /* Add left padding to avoid hamburger */
  border-bottom: 2px solid var(--border);
  background: var(--bg-dark);
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto; /* Push to right edge */
}

/* Hide status indicator when ChatPanel is in App.vue */
.status-indicator {
  display: none; /* Removed since hamburger toggle replaces it */
}
</style>
```

### Step 4.2: Testing Checklist

**Manual Testing Steps**:

1. **Upload & Analysis Flow**
   - [ ] Upload CSV in any tab (Playground, Raw Data, Visualization)
   - [ ] Enter prompt "check missing values"
   - [ ] Verify analysis completes successfully
   - [ ] Verify dataset is saved to Pinia store
   - [ ] Verify navigation CTA appears in chat

2. **Navigation**
   - [ ] Click "Go to Raw Data →" button
   - [ ] Verify navigation to /data
   - [ ] Verify ChatPanel persists (doesn't disappear)
   - [ ] Verify dataset profiling view loads

3. **DataView Components**
   - [ ] Verify DatasetSummary shows correct stats
   - [ ] Verify description is displayed (LLM-generated or placeholder)
   - [ ] Verify ColumnCard grid layout
   - [ ] Verify each column shows completeness, distinctness, entropy
   - [ ] Verify issues are grouped by column
   - [ ] Verify DataSamples table shows first 10 rows
   - [ ] Verify null cells are highlighted

4. **Tab Persistence**
   - [ ] Upload dataset in Playground tab
   - [ ] Switch to Raw Data tab
   - [ ] Verify ChatPanel shows same messages
   - [ ] Switch to Visualization tab
   - [ ] Verify ChatPanel still shows same messages

5. **Hamburger Toggle**
   - [ ] Click hamburger to collapse ChatPanel
   - [ ] Verify smooth animation
   - [ ] Verify main content expands to full width
   - [ ] Click hamburger to expand
   - [ ] Verify ChatPanel reappears
   - [ ] Test keyboard shortcut (Ctrl+B / Cmd+B)

6. **UI Polish**
   - [ ] Verify no overlap between hamburger and Clear button
   - [ ] Verify responsive layout on mobile (<768px)
   - [ ] Verify all colors match design system
   - [ ] Verify smooth transitions

---

## GitHub Issue for Multi-Dataset Support

**Title**: Support multiple dataset uploads and comparison

**Description**:
Currently, the dashboard supports a single dataset at a time. Add multi-dataset support to enable:

**Use Cases**:
- Compare train.csv vs test.csv for distribution shift
- Analyze multiple batches of data (week1.csv, week2.csv, etc.)
- A/B test dataset comparison

**Technical Requirements**:
1. Update `datasetStore.js`:
   - Change `currentDataset` → `datasets: []` array
   - Add `activeDatasetId` to track which dataset is currently selected
   - Add `addDataset()` and `removeDataset()` methods

2. Update ChatPanel:
   - Support naming datasets during upload ("Upload as train.csv" vs "Upload as test.csv")
   - Chat context should reference datasets by name ("compare train vs test")

3. Update DataView:
   - Add dataset switcher dropdown in header
   - Show active dataset profiling
   - Add "Compare" mode to show side-by-side column stats

4. Backend:
   - Support multi-dataset profiling API: `POST /api/compare-datasets`
   - Return train-test skew issues for matching columns

**Priority**: Medium (defer to post-MVP iteration)

---

## Summary

**Estimated Total Effort**: 6-8 hours

**Files Created** (7):
- `client/src/stores/datasetStore.js`
- `client/src/components/DatasetSummary.vue`
- `client/src/components/ColumnCard.vue`
- `client/src/components/DataSamples.vue`
- `server/api/services/description_generator.py`

**Files Modified** (4):
- `client/src/App.vue`
- `client/src/components/ChatPanel.vue`
- `client/src/views/PlaygroundView.vue`
- `client/src/views/DataView.vue`
- `server/api/routes/chat.py`

**Key Features**:
✅ Persistent chatbox across all tabs (command center UX)
✅ Hybrid navigation (suggest after analysis)
✅ Kaggle-style data profiling view
✅ LLM-generated dataset descriptions
✅ Column-level quality metrics (completeness, entropy, distinctness)
✅ Visual issue highlighting in data samples
✅ Hamburger toggle with fixed overlap issue
✅ Single dataset architecture (extensible to multi-dataset)

**Next Steps**:
1. Review this plan
2. Begin Phase 1 implementation
3. Test each phase incrementally
4. Ship MVP
5. Iterate with user feedback
