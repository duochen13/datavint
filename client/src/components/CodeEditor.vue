<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue'])

const editor = ref(null)
const syntaxHighlight = ref(null)
const lineNumbers = ref(null)
const code = ref(props.modelValue)

// Update parent when code changes
watch(code, (newCode) => {
  emit('update:modelValue', newCode)
})

// Update code when prop changes
watch(() => props.modelValue, (newValue) => {
  code.value = newValue
  updateLineNumbers()
  updateSyntaxHighlight()
})

function updateLineNumbers() {
  const lines = code.value.split('\n').length
  if (lineNumbers.value) {
    lineNumbers.value.textContent = Array.from({ length: lines }, (_, i) => i + 1).join('\n')
  }
}

function highlightSyntax(codeText) {
  // Python syntax highlighting patterns (Atom One Dark)
  const patterns = [
    { regex: /(#[^\n]*)/g, class: 'comment' },
    { regex: /(["'])((?:\\.|(?!\1)[^\\\n])*)\1/g, class: 'string' },
    {
      regex: /\b(import|from|as|def|class|if|else|elif|for|while|in|return|yield|try|except|finally|with|raise|assert|break|continue|pass|lambda|global|nonlocal|True|False|None)\b/g,
      class: 'keyword'
    },
    { regex: /\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?=\()/g, class: 'function' },
    { regex: /\b(\d+\.?\d*)\b/g, class: 'number' },
    { regex: /([=+\-*/%<>!&|^~])/g, class: 'operator' },
    { regex: /\b(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_.]*)/g, class: 'module' }
  ]

  let highlighted = codeText
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  patterns.forEach(pattern => {
    highlighted = highlighted.replace(pattern.regex, (match, ...groups) => {
      if (pattern.class === 'module') {
        const moduleName = groups[0]
        return match.replace(moduleName, `<span class="${pattern.class}">${moduleName}</span>`)
      }
      if (pattern.class === 'string' && groups.length > 0) {
        return `<span class="${pattern.class}">${match}</span>`
      }
      return `<span class="${pattern.class}">${match}</span>`
    })
  })

  return highlighted
}

function updateSyntaxHighlight() {
  if (syntaxHighlight.value) {
    syntaxHighlight.value.innerHTML = highlightSyntax(code.value)
    syncScroll()
  }
}

function handleInput() {
  updateLineNumbers()
  updateSyntaxHighlight()
}

function syncScroll() {
  if (editor.value && syntaxHighlight.value && lineNumbers.value) {
    syntaxHighlight.value.scrollTop = editor.value.scrollTop
    syntaxHighlight.value.scrollLeft = editor.value.scrollLeft
    lineNumbers.value.scrollTop = editor.value.scrollTop
  }
}

onMounted(() => {
  updateLineNumbers()
  updateSyntaxHighlight()
})
</script>

<template>
  <div class="editor-container">
    <div class="editor-wrapper">
      <div ref="lineNumbers" class="line-numbers">1</div>
      <div class="editor-content">
        <div ref="syntaxHighlight" class="syntax-highlight"></div>
        <textarea
          ref="editor"
          v-model="code"
          class="code-editor"
          spellcheck="false"
          placeholder=""
          @input="handleInput"
          @scroll="syncScroll"
        ></textarea>
      </div>
    </div>
  </div>
</template>

<style scoped>
.editor-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-editor);
  border: 1px solid var(--border);
  border-radius: 8px;
}

.editor-wrapper {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

.line-numbers {
  width: 48px;
  padding: 16px 8px;
  background: var(--bg-panel);
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.6;
  text-align: right;
  user-select: none;
  overflow: hidden;
  white-space: pre;
  border-right: 1px solid var(--border);
}

.editor-content {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: var(--bg-editor);
}

.syntax-highlight {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 16px;
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow: hidden;
  pointer-events: none;
  color: var(--text-primary);
  z-index: 1;
}

.code-editor {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 16px;
  background: transparent;
  border: none;
  outline: none;
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-primary);
  caret-color: var(--accent-cyan);
  resize: none;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-y: auto;
  overflow-x: auto;
  z-index: 2;
  -webkit-text-fill-color: transparent;
  -moz-text-fill-color: transparent;
}

.code-editor::selection {
  background: rgba(0, 122, 255, 0.2);
}

/* Syntax highlighting colors - Xcode Light */
.syntax-highlight :deep(.keyword) {
  color: var(--syntax-keyword);
  font-weight: 600;
}

.syntax-highlight :deep(.function) {
  color: var(--syntax-function);
}

.syntax-highlight :deep(.string) {
  color: var(--syntax-string);
}

.syntax-highlight :deep(.comment) {
  color: var(--syntax-comment);
  font-style: italic;
}

.syntax-highlight :deep(.number) {
  color: var(--syntax-number);
}

.syntax-highlight :deep(.operator) {
  color: var(--text-primary);
}

.syntax-highlight :deep(.module) {
  color: #3e8087;
}
</style>

<style>
/* Unscoped syntax highlighting - Xcode Light theme */
.syntax-highlight .keyword {
  color: #ad3da4;
  font-weight: 600;
}

.syntax-highlight .function {
  color: #272ad8;
}

.syntax-highlight .string {
  color: #d12f1b;
}

.syntax-highlight .comment {
  color: #6e6e73;
  font-style: italic;
}

.syntax-highlight .number {
  color: #272ad8;
}

.syntax-highlight .operator {
  color: #1d1d1f;
}

.syntax-highlight .module {
  color: #3e8087;
}
</style>
