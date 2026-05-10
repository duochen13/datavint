<script setup>
import { computed } from 'vue'

const props = defineProps({
  preview: {
    type: Object,
    required: true
  }
})

const columns = computed(() => {
  if (!props.preview.sample || props.preview.sample.length === 0) return []
  return Object.keys(props.preview.sample[0])
})

const rows = computed(() => {
  // Show only first 5 rows for preview
  return props.preview.sample?.slice(0, 5) || []
})
</script>

<template>
  <div class="dataset-preview">
    <div class="preview-header">
      <h3>Dataset Preview</h3>
      <span class="preview-info">First {{ rows.length }} rows</span>
    </div>

    <div class="table-container">
      <table class="preview-table">
        <thead>
          <tr>
            <th class="row-number-header">#</th>
            <th v-for="col in columns" :key="col">
              {{ col }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in rows" :key="idx">
            <td class="row-number">{{ idx + 1 }}</td>
            <td
              v-for="col in columns"
              :key="col"
              :class="{ 'null-cell': row[col] === null || row[col] === undefined || row[col] === '' }"
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
.dataset-preview {
  padding: 24px;
  background: var(--bg-dark);
  border-top: 2px solid var(--border);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.preview-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.preview-info {
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

.preview-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  font-family: var(--font-mono);
}

.preview-table thead {
  background: var(--bg-dark);
  position: sticky;
  top: 0;
  z-index: 10;
}

.preview-table th {
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

.preview-table td {
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  color: var(--text-secondary);
}

.preview-table tbody tr:hover {
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
