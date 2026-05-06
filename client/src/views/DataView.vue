<script setup>
import { ref } from 'vue'
import api from '@/services/api'
import DataTable from '@/components/DataTable.vue'

import { useRouter } from 'vue-router'

const router = useRouter()
const datasetId = ref(null)
const previewData = ref(null)
const isLoading = ref(false)
const error = ref(null)
const successMessage = ref(null)

async function handleFileUpload(event) {
  const file = event.target.files[0]
  if (!file) return

  isLoading.value = true
  error.value = null
  successMessage.value = null

  try {
    const response = await api.data.upload(file)
    datasetId.value = response.data.dataset_id
    previewData.value = response.data.preview

    // Store dataset_id in localStorage for visualization tab
    localStorage.setItem('currentDatasetId', response.data.dataset_id)

    successMessage.value = 'Upload successful! Go to Visualization tab to see data quality analysis.'
  } catch (err) {
    error.value = err.message
  } finally {
    isLoading.value = false
  }
}

function goToVisualization() {
  router.push('/visualization')
}
</script>

<template>
  <div class="data-view">
    <!-- Upload Area -->
    <div class="upload-section">
      <div class="upload-card">
        <div class="upload-icon">📊</div>
        <h2>Upload CSV Dataset</h2>
        <p>Upload your training or test data for analysis</p>
        <label class="upload-btn">
          <input
            type="file"
            accept=".csv"
            @change="handleFileUpload"
            style="display: none"
          />
          Choose File
        </label>
        <div v-if="isLoading" class="loading">Uploading...</div>
        <div v-if="error" class="error">{{ error }}</div>
        <div v-if="successMessage" class="success">
          {{ successMessage }}
          <button class="viz-btn" @click="goToVisualization">
            View Analysis →
          </button>
        </div>
      </div>
    </div>

    <!-- Data Preview -->
    <div v-if="previewData" class="preview-section">
      <div class="preview-header">
        <h3>Dataset Preview</h3>
        <div class="stats">
          <span>{{ previewData.rows }} rows</span>
          <span>{{ previewData.columns }} columns</span>
        </div>
      </div>
      <DataTable :data="previewData.sample" />
    </div>

    <!-- Empty State -->
    <div v-if="!previewData && !isLoading" class="empty-state">
      <div class="empty-icon">📊</div>
      <h3>No data loaded</h3>
      <p>Upload a CSV file to view your dataset</p>
    </div>
  </div>
</template>

<style scoped>
.data-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-dark);
}

.upload-section {
  padding: 40px;
  border-bottom: 1px solid var(--border);
}

.upload-card {
  max-width: 560px;
  margin: 0 auto;
  padding: 48px;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 18px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.upload-icon {
  font-size: 56px;
  margin-bottom: 20px;
  opacity: 0.8;
}

.upload-card h2 {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.upload-card p {
  color: var(--text-secondary);
  margin-bottom: 28px;
  font-size: 14px;
}

.upload-btn {
  display: inline-block;
  padding: 11px 28px;
  background: var(--accent-cyan);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.upload-btn:hover {
  background: #0051d5;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
}

.loading {
  margin-top: 20px;
  color: var(--accent-cyan);
  font-weight: 500;
  font-size: 14px;
}

.error {
  margin-top: 20px;
  color: var(--accent-orange);
  font-weight: 500;
  font-size: 14px;
}

.success {
  margin-top: 24px;
  padding: 16px 20px;
  background: rgba(52, 199, 89, 0.08);
  border: 1px solid rgba(52, 199, 89, 0.2);
  border-radius: 12px;
  color: #1f7a34;
  font-weight: 500;
  font-size: 14px;
  text-align: center;
}

.viz-btn {
  display: block;
  margin: 14px auto 0;
  padding: 9px 20px;
  background: var(--accent-cyan);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.viz-btn:hover {
  background: #0051d5;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
}

.preview-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 32px;
  background: var(--bg-dark);
  border-bottom: 1px solid var(--border);
}

.preview-header h3 {
  font-size: 17px;
  font-weight: 600;
  color: var(--accent-cyan);
}

.stats {
  display: flex;
  gap: 24px;
  font-size: 14px;
  color: var(--text-secondary);
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 72px;
  margin-bottom: 24px;
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 20px;
  margin-bottom: 8px;
  color: var(--text-secondary);
}

.empty-state p {
  font-size: 14px;
}
</style>
