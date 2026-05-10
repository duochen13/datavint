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
  margin: 0;
}
</style>
