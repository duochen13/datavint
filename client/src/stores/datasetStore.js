import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useDatasetStore = defineStore('dataset', () => {
  // Current dataset
  const currentDataset = ref(null)

  // Chat history (persisted across tabs)
  const chatHistory = ref([])

  // Upload state
  const isAnalyzing = ref(false)
  const uploadedFile = ref(null)

  /**
   * Set current dataset after upload + analysis
   */
  function setDataset(dataset) {
    currentDataset.value = {
      ...dataset,
      uploadedAt: Date.now()
    }
  }

  /**
   * Add message to chat history
   */
  function addMessage(content, type = 'user') {
    chatHistory.value.push({
      content,
      type,
      id: Date.now()
    })
  }

  /**
   * Clear all chat history
   */
  function clearHistory() {
    chatHistory.value = []
  }

  /**
   * Reset entire store (new session)
   */
  function reset() {
    currentDataset.value = null
    chatHistory.value = []
    isAnalyzing.value = false
    uploadedFile.value = null
  }

  return {
    // State
    currentDataset,
    chatHistory,
    isAnalyzing,
    uploadedFile,

    // Actions
    setDataset,
    addMessage,
    clearHistory,
    reset
  }
})
