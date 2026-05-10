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
