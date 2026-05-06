/**
 * DataVint API Client
 *
 * Axios wrapper for all backend API calls
 */

import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[API Error]', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default {
  // Playground endpoints
  playground: {
    execute(code, options = {}) {
      return apiClient.post('/playground/execute', {
        code,
        options,
      })
    },

    validate(code) {
      return apiClient.post('/playground/validate', { code })
    },
  },

  // Data endpoints
  data: {
    upload(file, labelCol = null) {
      const formData = new FormData()
      formData.append('file', file)
      if (labelCol) {
        formData.append('label_col', labelCol)
      }

      return apiClient.post('/data/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
    },

    preview(datasetId, limit = 50) {
      return apiClient.get('/data/preview', {
        params: { dataset_id: datasetId, limit },
      })
    },

    statistics(datasetId) {
      return apiClient.get('/data/statistics', {
        params: { dataset_id: datasetId },
      })
    },
  },

  // Visualization endpoints
  visualization: {
    issues(datasetId) {
      return apiClient.get('/visualization/issues', {
        params: { dataset_id: datasetId },
      })
    },

    manifest(datasetId, applyCorrections = true) {
      return apiClient.post('/visualization/manifest', null, {
        params: {
          dataset_id: datasetId,
          apply_corrections: applyCorrections,
        },
      })
    },
  },

  // Profiling endpoints (simple version without NumPy issues)
  profiling: {
    simpleIssues(datasetId) {
      return apiClient.get('/profiling/simple-issues', {
        params: { dataset_id: datasetId },
      })
    },
  },

  // Health check
  health() {
    return apiClient.get('/health')
  },
}
