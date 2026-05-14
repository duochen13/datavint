<script setup>
import { computed } from 'vue'

const props = defineProps({
  run: {
    type: Object,
    required: true,
  },
  active: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['hover', 'click'])

// Format timestamp
const formattedTimestamp = computed(() => {
  const date = new Date(props.run.timestamp)
  const now = new Date()
  const diffMs = now - date
  const diffHours = Math.floor(diffMs / 3600000)

  if (diffHours < 1) return 'Just now'
  if (diffHours < 24) return `${diffHours}h ago`

  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays}d ago`
})

// Generate ARIA label
const ariaLabel = computed(() => {
  const metrics = Object.entries(props.run.metrics)
    .map(([key, val]) => {
      const quality = val.quality !== 'neutral' ? ` ${val.quality}` : ''
      return `${key} ${val.value}${quality}`
    })
    .join(', ')

  let prefix = ''
  if (props.run.best) prefix = 'Overall best model, '
  else if (props.run.sweepWinner) prefix = `Sweep ${props.run.sweep.id} winner, `
  else prefix = 'Model run '

  return `${prefix}${props.run.id}: ${props.run.message}, ${metrics}, created ${formattedTimestamp.value}`
})
</script>

<template>
  <article
    class="model-node"
    :class="{ active }"
    :data-id="run.id"
    tabindex="0"
    role="button"
    :aria-label="ariaLabel"
    @mouseenter="emit('hover', run.id, true)"
    @mouseleave="emit('hover', run.id, false)"
    @click="emit('click', run.id)"
    @keypress.enter="emit('click', run.id)"
    @keypress.space.prevent="emit('click', run.id)"
  >
    <div class="node-header">
      <span class="node-id">{{ run.id }}</span>
      <span class="node-timestamp">{{ formattedTimestamp }}</span>
    </div>

    <div class="node-message">{{ run.message }}</div>

    <!-- Metrics: only show on hover -->
    <div v-if="run.metrics" class="metrics">
      <div v-for="(metric, key) in run.metrics" :key="key" class="metric">
        <div class="metric-label">{{ key }}</div>
        <div class="metric-value">
          {{ metric.value }}
        </div>
      </div>
    </div>
  </article>
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

.model-node {
  background: rgba(0, 0, 0, 0.3); /* Dark transparent background */
  border: 3px solid rgba(139, 92, 246, 0.3); /* Light purple border */
  border-radius: 8px;
  padding: 16px;
  position: relative;
  cursor: pointer;
  transition: all 0.2s;
  outline: none;
  z-index: 10;
  backdrop-filter: blur(8px);
  width: 280px;
  height: 120px;
  box-sizing: border-box;
  overflow: hidden;
}

.model-node:hover,
.model-node:focus {
  border-color: rgba(139, 92, 246, 0.6);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
}

.model-node:focus-visible {
  outline: 2px solid rgba(139, 92, 246, 0.6);
  outline-offset: 2px;
}

.model-node.active {
  border-color: rgba(139, 92, 246, 0.6);
  background: rgba(139, 92, 246, 0.05);
}

.node-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.node-id {
  font-weight: 600;
  font-size: 15px;
  color: var(--text-primary);
  font-family: var(--font-mono);
}

.node-timestamp {
  font-size: 11px;
  color: var(--text-tertiary);
}

.node-message {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.metrics {
  display: none; /* Hidden by default */
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 12px;
}

.model-node:hover .metrics {
  display: grid; /* Show on hover */
}

.metric {
  background: rgba(0, 0, 0, 0.2); /* Dark background for metrics */
  padding: 8px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.metric-label {
  font-size: 10px;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.metric-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-top: 2px;
  font-family: var(--font-mono);
}
</style>
