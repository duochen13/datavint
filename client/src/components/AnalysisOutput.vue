<script setup>
const props = defineProps({
  output: {
    type: String,
    required: true
  }
})
</script>

<template>
  <div class="analysis-output">
    <div class="output-header">
      <h3>Data Quality Report</h3>
    </div>
    <pre class="output-content">{{ output }}</pre>
  </div>
</template>

<style scoped>
.analysis-output {
  padding: 24px;
  background: var(--bg-dark);
  border-top: 2px solid var(--border);
}

.output-header {
  margin-bottom: 16px;
}

.output-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.output-content {
  padding: 20px;
  background: var(--bg-panel);
  border: 2px solid var(--border);
  border-radius: 8px;
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* Syntax highlighting for special characters */
.output-content::selection {
  background: rgba(0, 240, 255, 0.2);
}
</style>
