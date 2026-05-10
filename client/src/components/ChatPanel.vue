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

function clearChatHistory() {
  store.clearHistory()
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

  // Reset textarea height
  if (textarea.value) {
    textarea.value.style.height = 'auto'
  }

  // If file is uploaded, analyze it
  if (uploadedFile.value) {
    store.isAnalyzing = true
    addMessage('🔄 Analyzing your dataset...', 'assistant')

    try {
      const result = await uploadAndAnalyzeCSV(uploadedFile.value, message)

      if (result.success) {
        // Save to store (including full analysis output)
        store.setDataset({
          id: `dataset_${Date.now()}`,
          filename: uploadedFile.value.name,
          stats: result.data?.stats,
          issues: result.data?.issues || [],
          preview: result.data?.preview,
          description: result.data?.description || null,
          analysisOutput: result.output // Store full analysis output for DataView
        })

        // Show simple success message (not the detailed output)
        const issueCount = result.data?.issues?.length || 0
        const highCount = result.data?.issues?.filter(i => i.severity === 'HIGH').length || 0

        let message = `✅ Analysis complete - ${issueCount} issue(s) detected`
        if (highCount > 0) {
          message += ` (${highCount} high severity)`
        }
        addMessage(message, 'assistant')

        // Navigation CTA (hybrid logic)
        const shouldNavigate = shouldSuggestDataView(result.data?.issues)
        if (shouldNavigate) {
          addMessage('📊 View detailed profiling in Raw Data tab', 'assistant')
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
    // Normal chat message (no file uploaded)
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

function handleKeypress(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function handleInput() {
  if (textarea.value) {
    textarea.value.style.height = 'auto'
    textarea.value.style.height = Math.min(textarea.value.scrollHeight, 120) + 'px'
  }
}
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
      <div class="welcome-message">
        <div class="welcome-title">👋 Welcome to DataVint Playground</div>
        <div class="welcome-text">
          Interactive IDE for exploring data quality detection. Try these commands:
        </div>
        <div class="welcome-commands">
          <div class="welcome-command">Analyze my dataset</div>
          <div class="welcome-command">Show me data quality issues</div>
          <div class="welcome-command">Generate a manifest</div>
          <div class="welcome-command">Compare train vs test data</div>
        </div>
      </div>

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
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-panel);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 2px solid var(--border);
  background: var(--bg-dark);
}

.panel-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--accent-cyan);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-indicator {
  display: none; /* Hidden when ChatPanel is in App.vue - hamburger toggle replaces it */
}

.clear-history-btn {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text-muted);
  font-size: 11px;
  font-family: var(--font-ui);
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.clear-history-btn:hover {
  background: rgba(255, 82, 82, 0.1);
  border-color: #ff5252;
  color: #ff5252;
}

.status-dot {
  width: 6px;
  height: 6px;
  background: var(--accent-lime);
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.4;
  }
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.welcome-message {
  padding: 24px;
  background: linear-gradient(135deg, rgba(0, 240, 255, 0.05), rgba(164, 255, 0, 0.05));
  border: 2px solid var(--border);
  border-radius: 8px;
  margin-bottom: 16px;
}

.welcome-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.welcome-text {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 16px;
  line-height: 1.5;
}

.welcome-commands {
  display: grid;
  gap: 8px;
}

.welcome-command {
  padding: 10px 16px;
  background: var(--bg-dark);
  border: 2px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  cursor: pointer;
  transition: all 0.2s;
}

.welcome-command:hover {
  background: var(--bg-hover);
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
  transform: translateX(4px);
}

.message {
  margin-bottom: 16px;
  animation: slideIn 0.2s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}

.message.user .message-label {
  color: var(--accent-cyan);
}

.message.assistant .message-label {
  color: var(--accent-lime);
}

.message-content {
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.message.user .message-content {
  background: var(--bg-hover);
  color: var(--text-primary);
  border: 2px solid var(--border);
}

.message.assistant .message-content {
  background: linear-gradient(135deg, rgba(0, 240, 255, 0.08), rgba(164, 255, 0, 0.08));
  color: var(--text-primary);
  border: 2px solid var(--border);
}

.chat-input-container {
  padding: 16px;
  border-top: 2px solid var(--border);
  background: var(--bg-dark);
}

.upload-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.upload-button {
  padding: 8px 16px;
  background: var(--bg-panel);
  border: 2px solid var(--border);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 14px;
  font-family: var(--font-ui);
  cursor: pointer;
  transition: all 0.2s;
}

.upload-button:hover:not(:disabled) {
  background: var(--bg-hover);
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
}

.upload-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.uploaded-filename {
  font-size: 13px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

.chat-input-wrapper {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.chat-input {
  flex: 1;
  padding: 12px;
  background: var(--bg-panel);
  border: 2px solid var(--border);
  border-radius: 6px;
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: 14px;
  resize: none;
  min-height: 44px;
  max-height: 120px;
  transition: all 0.2s;
}

.chat-input:focus {
  outline: none;
  border-color: var(--accent-cyan);
  box-shadow: 0 0 0 3px rgba(0, 240, 255, 0.1);
}

.chat-input::placeholder {
  color: var(--text-muted);
}

/* Animated caret for better focus visibility */
.chat-input:focus {
  caret-color: var(--accent-cyan);
}

@keyframes blink {
  0%, 50% {
    opacity: 1;
  }
  50.01%, 100% {
    opacity: 0;
  }
}

.send-button {
  width: 44px;
  height: 44px;
  background: var(--accent-cyan);
  border: 2px solid var(--accent-cyan);
  border-radius: 6px;
  color: var(--bg-dark);
  font-size: 18px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-button:hover {
  background: var(--accent-lime);
  border-color: var(--accent-lime);
  transform: translateY(-2px);
}

.send-button:active {
  transform: translateY(0);
}

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
