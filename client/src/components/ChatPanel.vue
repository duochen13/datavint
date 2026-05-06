<script setup>
import { ref, nextTick } from 'vue'

const emit = defineEmits(['send-message'])

const messages = ref([])
const input = ref('')
const chatMessages = ref(null)
const textarea = ref(null)

function addMessage(content, type = 'user') {
  messages.value.push({
    content,
    type,
    id: Date.now()
  })

  nextTick(() => {
    if (chatMessages.value) {
      chatMessages.value.scrollTop = chatMessages.value.scrollHeight
    }
  })
}

function sendMessage() {
  const message = input.value.trim()
  if (message) {
    addMessage(message, 'user')
    emit('send-message', message)
    input.value = ''

    // Reset textarea height
    if (textarea.value) {
      textarea.value.style.height = 'auto'
    }
  }
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
      <div class="status-indicator">
        <div class="status-dot"></div>
        <span>READY</span>
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
        <div class="message-content">{{ msg.content }}</div>
      </div>
    </div>

    <div class="chat-input-container">
      <div class="chat-input-wrapper">
        <textarea
          ref="textarea"
          v-model="input"
          class="chat-input"
          placeholder="Ask about data quality..."
          rows="1"
          @keypress="handleKeypress"
          @input="handleInput"
        ></textarea>
        <button class="send-button" @click="sendMessage">➤</button>
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

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
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
  border: 2px solid var(--border-active);
}

.chat-input-container {
  padding: 16px;
  border-top: 2px solid var(--border);
  background: var(--bg-dark);
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
</style>
