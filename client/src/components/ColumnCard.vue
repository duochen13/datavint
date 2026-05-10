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
