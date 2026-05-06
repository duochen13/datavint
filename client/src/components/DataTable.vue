<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
})

const columns = computed(() => {
  if (props.data.length === 0) return []
  return Object.keys(props.data[0])
})
</script>

<template>
  <div class="data-table-wrapper">
    <table v-if="data.length > 0" class="data-table">
      <thead>
        <tr>
          <th v-for="col in columns" :key="col">{{ col }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, index) in data" :key="index">
          <td v-for="col in columns" :key="col">{{ row[col] }}</td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty-table">
      <div class="empty-icon">📊</div>
      <div class="empty-text">No data to display</div>
    </div>
  </div>
</template>

<style scoped>
.data-table-wrapper {
  flex: 1;
  overflow: auto;
  background: var(--bg-dark);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  font-family: var(--font-mono);
}

.data-table thead {
  position: sticky;
  top: 0;
  background: var(--bg-panel);
  z-index: 10;
}

.data-table th {
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border);
  border-right: 1px solid rgba(0, 0, 0, 0.06);
  white-space: nowrap;
  font-size: 12px;
  letter-spacing: 0;
}

.data-table th:last-child {
  border-right: none;
}

.data-table tbody tr {
  transition: background 0.15s;
}

.data-table tbody tr:hover {
  background: var(--bg-hover);
}

.data-table td {
  padding: 10px 16px;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border);
  border-right: 1px solid var(--border);
  white-space: nowrap;
}

.data-table td:last-child {
  border-right: none;
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.empty-table {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-text {
  font-size: 14px;
}
</style>
