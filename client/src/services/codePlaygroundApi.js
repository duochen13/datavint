/**
 * Code Playground API Service
 *
 * Handles API calls for the interactive code editor feature
 */

import axios from 'axios'

// Create API client
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * List all available code templates
 * @returns {Promise<{templates: Array}>}
 */
export async function listTemplates() {
  const response = await apiClient.get('/code/templates')
  return response.data
}

/**
 * Execute a code template
 * @param {string} templateId - ID of the template to execute
 * @returns {Promise<{success: boolean, output: string, data: object, error?: string}>}
 */
export async function executeTemplate(templateId) {
  const response = await apiClient.post('/code/execute-template', {
    template_id: templateId
  })
  return response.data
}

/**
 * Health check for code playground service
 * @returns {Promise<object>}
 */
export async function codePlaygroundHealth() {
  const response = await apiClient.get('/code/health')
  return response.data
}

/**
 * Upload CSV and analyze with natural language prompt
 * @param {File} file - CSV file to analyze
 * @param {string} prompt - Natural language analysis request
 * @returns {Promise<{success: boolean, generated_code: string, output: string, data?: object, error?: string}>}
 */
export async function uploadAndAnalyzeCSV(file, prompt = 'profile this dataset') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('prompt', prompt)

  const response = await apiClient.post('/chat/analyze-csv', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 30000  // 30 sec timeout for LLM call
  })

  return response.data
}
