<script setup>
import { ref, nextTick, computed, watch } from 'vue'

const messages = ref([
  {
    id: 1,
    content: '👋 Hi! I can help you understand your experiment results. Try asking me about your data or models.',
    type: 'assistant',
    timestamp: new Date(Date.now() - 2 * 3600000).toISOString(),
  },
  {
    id: 2,
    content: 'Which data version improved NE the most?',
    type: 'user',
    timestamp: new Date(Date.now() - 1 * 3600000).toISOString(),
  },
  {
    id: 3,
    content: 'D1 (fix user feature coverage) produced the best results. Models trained on D1 achieved:\n\n• M2.2: 0.867 NE (+1.3% vs best D0 model)\n• M2.1: 0.841 NE\n\nThe improved feature coverage in D1 was the key factor.',
    type: 'assistant',
    timestamp: new Date(Date.now() - 1 * 3600000).toISOString(),
  },
  {
    id: 4,
    content: 'Why did M2 win in Sweep 1?',
    type: 'user',
    timestamp: new Date(Date.now() - 1800000).toISOString(),
  },
  {
    id: 5,
    content: 'M2 (lr=0.005) had the best balance:\n\n• NE: 0.856 (highest in sweep)\n• Learning rate wasn\'t too aggressive (M1, M0 overfit)\n• Learning rate wasn\'t too conservative (M3 underfit)\n\nThat\'s why lr=0.005 was selected for Sweep 2.',
    type: 'assistant',
    timestamp: new Date(Date.now() - 1800000).toISOString(),
  },
])

const input = ref('')
const chatMessages = ref(null)
const textarea = ref(null)
const suggestedQueries = [
  'Compare M2.1 vs M2.2',
  'Show all NE scores',
  '/help',
]

// Command autocomplete
const availableCommands = [
  { command: '/clear', description: 'Clear chat history' },
  { command: '/help', description: 'Show available commands' },
]

const showCommandSuggestions = ref(false)
const selectedCommandIndex = ref(0)

// Filter commands based on current input
const filteredCommands = computed(() => {
  if (!input.value.startsWith('/')) {
    return []
  }

  const query = input.value.toLowerCase()
  const filtered = availableCommands.filter(cmd =>
    cmd.command.toLowerCase().startsWith(query)
  )

  return filtered
})

// Watch input to show/hide suggestions
watch(input, (newValue) => {
  if (newValue.startsWith('/') && newValue.length > 0) {
    showCommandSuggestions.value = filteredCommands.value.length > 0
    selectedCommandIndex.value = 0
  } else {
    showCommandSuggestions.value = false
  }
})

function addMessage(content, type = 'user') {
  messages.value.push({
    id: Date.now(),
    content,
    type,
    timestamp: new Date().toISOString(),
  })

  nextTick(() => {
    if (chatMessages.value) {
      chatMessages.value.scrollTop = chatMessages.value.scrollHeight
    }
  })
}

function clearChatHistory() {
  messages.value = messages.value.slice(0, 1) // Keep welcome message
}

async function sendMessage() {
  const message = input.value.trim()
  if (!message) return

  // Handle slash commands
  if (message.startsWith('/')) {
    handleCommand(message)
    input.value = ''

    // Reset textarea height
    if (textarea.value) {
      textarea.value.style.height = 'auto'
    }
    return
  }

  addMessage(message, 'user')
  input.value = ''

  // Reset textarea height
  if (textarea.value) {
    textarea.value.style.height = 'auto'
  }

  // Mock response (will be replaced with API call later)
  setTimeout(() => {
    addMessage(
      'I can help with that! Try clicking on nodes in the graph to explore connections, or ask me more specific questions about your experiments.',
      'assistant'
    )
  }, 800)
}

function handleCommand(command) {
  const cmd = command.toLowerCase().trim()

  switch (cmd) {
    case '/clear':
      messages.value = [{
        id: Date.now(),
        content: '👋 Hi! I can help you understand your experiment results. Try asking me about your data or models.',
        type: 'assistant',
        timestamp: new Date().toISOString(),
      }]
      break

    case '/help':
      addMessage('/help', 'user')
      addMessage(
        'Available commands:\n\n' +
        '• /clear - Clear chat history\n' +
        '• /help - Show this help message\n\n' +
        'You can also ask questions about your experiments!',
        'assistant'
      )
      break

    default:
      addMessage(command, 'user')
      addMessage(
        `Unknown command: ${command}\n\nType /help to see available commands.`,
        'assistant'
      )
  }
}

function useSuggestedQuery(query) {
  input.value = query
  textarea.value?.focus()
}

function selectCommand(command) {
  input.value = command + ' '
  showCommandSuggestions.value = false
  textarea.value?.focus()
}

function handleKeypress(e) {
  // Handle autocomplete navigation
  if (showCommandSuggestions.value) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      selectedCommandIndex.value = Math.min(selectedCommandIndex.value + 1, filteredCommands.value.length - 1)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      selectedCommandIndex.value = Math.max(selectedCommandIndex.value - 1, 0)
    } else if (e.key === 'Tab' || e.key === 'Enter') {
      if (filteredCommands.value.length > 0) {
        e.preventDefault()
        selectCommand(filteredCommands.value[selectedCommandIndex.value].command)
      }
    } else if (e.key === 'Escape') {
      showCommandSuggestions.value = false
    }
    return
  }

  // Regular enter to send
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

function formatTimestamp(isoString) {
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now - date
  const diffHours = Math.floor(diffMs / 3600000)

  if (diffHours < 1) return 'Just now'
  if (diffHours < 24) return `${diffHours}h ago`

  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
}
</script>

<template>
  <div class="chat-panel">
    <!-- Header -->
    <div class="panel-header">
      <div class="panel-title">Assistant</div>
      <div class="panel-subtitle">Ask about your experiments</div>
    </div>

    <!-- Messages -->
    <div ref="chatMessages" class="chat-messages" role="log" aria-live="polite" aria-label="Chat conversation">
      <div v-for="msg in messages" :key="msg.id" :class="['message', msg.type]">
        <div class="message-bubble">
          {{ msg.content }}
        </div>
        <div class="message-timestamp">{{ formatTimestamp(msg.timestamp) }}</div>
      </div>
    </div>

    <!-- Suggested Queries -->
    <div class="suggested-queries">
      <div class="suggested-title">Suggested</div>
      <div class="suggested-chips" role="group" aria-label="Suggested questions">
        <button
          v-for="query in suggestedQueries"
          :key="query"
          class="suggested-chip"
          @click="useSuggestedQuery(query)"
          tabindex="0"
        >
          {{ query }}
        </button>
      </div>
    </div>

    <!-- Input -->
    <div class="chat-input-container">
      <label for="chat-input" class="sr-only">Ask a question</label>

      <!-- Command suggestions dropdown -->
      <div v-if="showCommandSuggestions" class="command-suggestions">
        <div
          v-for="(cmd, index) in filteredCommands"
          :key="cmd.command"
          :class="['command-suggestion', { selected: index === selectedCommandIndex }]"
          @click="selectCommand(cmd.command)"
          @mouseenter="selectedCommandIndex = index"
        >
          <span class="command-text">{{ cmd.command }}</span>
          <span class="command-description">{{ cmd.description }}</span>
        </div>
      </div>

      <div class="chat-input-wrapper">
        <textarea
          id="chat-input"
          ref="textarea"
          v-model="input"
          class="chat-input"
          placeholder="Ask about your experiments..."
          rows="1"
          @keypress="handleKeypress"
          @input="handleInput"
          aria-label="Ask about your experiments"
        ></textarea>
        <button
          class="send-button"
          @click="sendMessage"
          aria-label="Send message"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Screen reader only */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-panel);
}

/* Header */
.panel-header {
  padding: 20px;
  border-bottom: 1px solid var(--border);
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.panel-subtitle {
  font-size: 13px;
  color: var(--text-tertiary);
}

/* Messages */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: var(--bg-panel);
}

.chat-messages::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #374151;
}

.message {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message.user {
  align-items: flex-end;
}

.message.assistant {
  align-items: flex-start;
}

.message-bubble {
  max-width: 85%;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
}

.message.user .message-bubble {
  background: var(--bg-hover);
  color: var(--text-primary);
  border: 1px solid var(--border);
}

.message.assistant .message-bubble {
  background: transparent;
  color: var(--text-primary);
  border: none;
}

.message-timestamp {
  font-size: 11px;
  color: var(--text-tertiary);
  padding: 0 4px;
}

/* Suggested Queries */
.suggested-queries {
  padding: 12px 20px;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

.suggested-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.suggested-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.suggested-chip {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border);
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  font-family: var(--font-ui);
}

.suggested-chip:hover,
.suggested-chip:focus {
  background: var(--accent-purple);
  color: white;
  border-color: var(--accent-purple);
  outline: none;
}

.suggested-chip:focus-visible {
  outline: 2px solid var(--accent-purple);
  outline-offset: 2px;
}

/* Input */
.chat-input-container {
  padding: 16px 20px;
  border-top: 1px solid var(--border);
  background: var(--bg-panel);
}

.chat-input-wrapper {
  display: flex;
  gap: 8px;
  align-items: center;
}

.chat-input {
  flex: 1;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 13px;
  font-family: var(--font-ui);
  color: var(--text-primary);
  resize: none;
  outline: none;
  transition: border-color 0.2s;
}

.chat-input:focus {
  border-color: var(--accent-purple);
}

.chat-input::placeholder {
  color: var(--text-tertiary);
}

.send-button {
  width: 36px;
  height: 36px;
  background: var(--accent-purple);
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  flex-shrink: 0;
}

.send-button:hover,
.send-button:focus {
  background: #7C3AED;
  outline: none;
}

.send-button:focus-visible {
  outline: 2px solid var(--accent-purple);
  outline-offset: 2px;
}

.send-button:disabled {
  background: var(--border);
  cursor: not-allowed;
}

/* Command Suggestions Dropdown */
.command-suggestions {
  position: absolute;
  bottom: 100%;
  left: 0;
  right: 0;
  margin-bottom: 8px;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.2);
  max-height: 200px;
  overflow-y: auto;
}

.command-suggestion {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid var(--border);
}

.command-suggestion:last-child {
  border-bottom: none;
}

.command-suggestion:hover,
.command-suggestion.selected {
  background: var(--bg-hover);
}

.command-text {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  color: var(--accent-purple);
}

.command-description {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-left: 12px;
}
</style>
