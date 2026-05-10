<script setup>
import { computed } from 'vue'
import { useDatasetStore } from '@/stores/datasetStore'
import DatasetSummary from '@/components/DatasetSummary.vue'
import DatasetPreview from '@/components/DatasetPreview.vue'
import ColumnCard from '@/components/ColumnCard.vue'
import DataSamples from '@/components/DataSamples.vue'
import AnalysisOutput from '@/components/AnalysisOutput.vue'

const store = useDatasetStore()

const dataset = computed(() => store.currentDataset)
const hasDataset = computed(() => dataset.value !== null)
const hasAnalysisOutput = computed(() => dataset.value?.analysisOutput)

// Group issues by feature (column)
const issuesByFeature = computed(() => {
  if (!dataset.value?.issues) return {}

  const grouped = {}
  dataset.value.issues.forEach(issue => {
    if (issue.feature) {
      if (!grouped[issue.feature]) {
        grouped[issue.feature] = []
      }
      grouped[issue.feature].push(issue)
    }
  })
  return grouped
})

// Get column names from stats
const columns = computed(() => {
  if (!dataset.value?.stats?.features) return []
  return Object.keys(dataset.value.stats.features)
})

function getColumnStats(columnName) {
  if (!dataset.value?.stats?.features) return {}
  return dataset.value.stats.features[columnName] || {}
}

function getColumnIssues(columnName) {
  return issuesByFeature.value[columnName] || []
}
</script>

<template>
  <div class="data-view">
    <!-- No Dataset State -->
    <div v-if="!hasDataset" class="empty-state">
      <div class="empty-icon">📊</div>
      <h3>No dataset loaded</h3>
      <p>Upload a CSV file using the Assistant to view detailed profiling</p>
      <div class="help-text">
        💡 Go to any tab and upload your dataset through the chat panel on the left
      </div>
    </div>

    <!-- Dataset Loaded: Kaggle-style View -->
    <div v-else class="profiling-view">
      <!-- About Dataset Section -->
      <DatasetSummary :dataset="dataset" />

      <!-- Dataset Preview (First 5 rows) -->
      <DatasetPreview
        v-if="dataset.preview"
        :preview="dataset.preview"
      />

      <!-- Analysis Output (Completeness, etc.) -->
      <AnalysisOutput
        v-if="hasAnalysisOutput"
        :output="dataset.analysisOutput"
      />

      <!-- Columns Grid -->
      <div class="columns-section">
        <div class="section-header">
          <h3>Training Data Preview</h3>
          <span class="column-count">{{ columns.length }} columns</span>
        </div>

        <div class="columns-grid">
          <ColumnCard
            v-for="col in columns"
            :key="col"
            :column-name="col"
            :stats="getColumnStats(col)"
            :issues="getColumnIssues(col)"
          />
        </div>
      </div>

      <!-- Data Samples -->
      <DataSamples
        v-if="dataset.preview"
        :preview="dataset.preview"
        :issues="dataset.issues"
      />
    </div>
  </div>
</template>

<style scoped>
.data-view {
  height: 100%;
  overflow-y: auto;
  background: var(--bg-dark);
}

/* Empty State */
.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  text-align: center;
}

.empty-icon {
  font-size: 80px;
  margin-bottom: 24px;
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}

.empty-state p {
  font-size: 15px;
  color: var(--text-secondary);
  margin: 0 0 24px 0;
}

.help-text {
  padding: 16px 24px;
  background: linear-gradient(135deg, rgba(0, 240, 255, 0.08), rgba(164, 255, 0, 0.08));
  border: 2px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  color: var(--text-secondary);
  max-width: 500px;
}

/* Profiling View */
.profiling-view {
  display: flex;
  flex-direction: column;
}

/* Columns Section */
.columns-section {
  padding: 24px;
  background: var(--bg-dark);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.column-count {
  font-size: 13px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.columns-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

/* Responsive */
@media (max-width: 768px) {
  .columns-grid {
    grid-template-columns: 1fr;
  }
}
</style>
