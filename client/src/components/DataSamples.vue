<script setup>
import { computed } from 'vue'

const props = defineProps({
  preview: {
    type: Object,
    required: true
  },
  issues: {
    type: Array,
    default: () => []
  }
})

const columns = computed(() => {
  if (!props.preview.sample || props.preview.sample.length === 0) return []
  return Object.keys(props.preview.sample[0])
})

const rows = computed(() => props.preview.sample || [])

// Identify problematic columns based on issues
const problematicColumns = computed(() => {
  const cols = new Set()
  props.issues.forEach(issue => {
    if (issue.feature) {
      cols.add(issue.feature)
    }
  })
  return cols
})

function isCellProblematic(column) {
  return problematicColumns.value.has(column)
}
</script>

<template>
  <div class="data-samples">
    <div class="samples-header">
      <h3>Data Samples</h3>
      <span class="samples-count">Showing first {{ rows.length }} of {{ preview.rows?.toLocaleString() || rows.length }} rows</span>
    </div>

    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th class="row-number-header">#</th>
            <th
              v-for="col in columns"
              :key="col"
              :class="{ 'problematic-column': isCellProblematic(col) }"
            >
              {{ col }}
              <span v-if="isCellProblematic(col)" class="warning-icon" title="Issues detected">⚠️</span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in rows" :key="idx">
            <td class="row-number">{{ idx + 1 }}</td>
            <td
              v-for="col in columns"
              :key="col"
              :class="{
                'null-cell': row[col] === null || row[col] === undefined || row[col] === '',
                'problematic-column': isCellProblematic(col)
              }"
            >
              <span v-if="row[col] === null || row[col] === undefined || row[col] === ''" class="null-value">
                NULL
              </span>
              <span v-else>{{ row[col] }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.data-samples {
  padding: 24px;
  background: var(--bg-dark);
}

.samples-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.samples-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.samples-count {
  font-size: 13px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.table-container {
  overflow-x: auto;
  border: 2px solid var(--border);
  border-radius: 8px;
  background: var(--bg-panel);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  font-family: var(--font-mono);
}

.data-table thead {
  background: var(--bg-dark);
  position: sticky;
  top: 0;
  z-index: 10;
}

.data-table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 700;
  color: var(--text-primary);
  border-bottom: 2px solid var(--border);
  white-space: nowrap;
}

.row-number-header {
  width: 50px;
  text-align: center;
  color: var(--text-muted);
}

.problematic-column {
  background: rgba(255, 167, 38, 0.05);
}

.warning-icon {
  font-size: 12px;
  margin-left: 6px;
}

.data-table td {
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  color: var(--text-secondary);
}

.data-table tbody tr:hover {
  background: var(--bg-hover);
}

.row-number {
  text-align: center;
  color: var(--text-muted);
  font-weight: 600;
}

.null-cell {
  background: rgba(255, 82, 82, 0.08);
}

.null-value {
  color: #ff5252;
  font-style: italic;
  font-weight: 600;
}
</style>
