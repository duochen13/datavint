<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  output: {
    type: Array,
    default: () => []
  },
  running: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['clear'])

const terminalOutput = ref(null)

// Auto-scroll when output changes
watch(() => props.output, () => {
  nextTick(() => {
    if (terminalOutput.value) {
      terminalOutput.value.scrollTop = terminalOutput.value.scrollHeight
    }
  })
}, { deep: true })

function clearTerminal() {
  emit('clear')
}
</script>

<template>
  <div class="terminal-container">
    <div class="terminal-header">
      <div class="terminal-title">⚡ Console Output</div>
      <div class="terminal-controls">
        <button class="terminal-control-btn" @click="clearTerminal" title="Clear">✕</button>
      </div>
    </div>

    <div ref="terminalOutput" class="terminal-output">
      <div
        v-for="(line, index) in output"
        :key="index"
        :class="['terminal-line', `terminal-${line.type}`]"
      >
        {{ line.text }}
      </div>

      <div v-if="running" class="terminal-line terminal-info">
        <div class="spinner"></div>
        Running...
      </div>
    </div>
  </div>
</template>

<style scoped>
.terminal-container {
  height: 280px;
  display: flex;
  flex-direction: column;
  background: var(--bg-editor);
  border-top: 1px solid var(--border);
  border-radius: 8px 8px 0 0;
}

.terminal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: var(--bg-panel);
  border-bottom: 1px solid var(--border);
  border-radius: 8px 8px 0 0;
}

.terminal-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  letter-spacing: 0;
}

.terminal-controls {
  display: flex;
  gap: 4px;
}

.terminal-control-btn {
  width: 24px;
  height: 24px;
  background: none;
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text-muted);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.terminal-control-btn:hover {
  background: var(--bg-hover);
  border-color: var(--accent-orange);
  color: var(--accent-orange);
}

.terminal-output {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.6;
}

.terminal-line {
  margin-bottom: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.terminal-prompt {
  color: var(--accent-cyan);
  font-weight: 600;
}

.terminal-info {
  color: var(--text-secondary);
}

.terminal-output {
  color: var(--text-primary);
}

.terminal-success {
  color: var(--accent-lime);
  font-weight: 600;
}

.terminal-error {
  color: var(--accent-orange);
  font-weight: 600;
}

.spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid var(--border);
  border-top-color: var(--accent-cyan);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 8px;
  vertical-align: middle;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
