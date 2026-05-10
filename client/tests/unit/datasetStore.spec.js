/**
 * Unit Tests for Dataset Store (Pinia)
 *
 * Tests the centralized state management for dataset and chat history
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useDatasetStore } from '../../src/stores/datasetStore'

describe('Dataset Store', () => {
  beforeEach(() => {
    // Create a fresh pinia instance for each test
    setActivePinia(createPinia())
  })

  describe('Initial State', () => {
    it('should have null currentDataset initially', () => {
      const store = useDatasetStore()
      expect(store.currentDataset).toBeNull()
    })

    it('should have empty chatHistory initially', () => {
      const store = useDatasetStore()
      expect(store.chatHistory).toEqual([])
    })

    it('should have isAnalyzing false initially', () => {
      const store = useDatasetStore()
      expect(store.isAnalyzing).toBe(false)
    })

    it('should have null uploadedFile initially', () => {
      const store = useDatasetStore()
      expect(store.uploadedFile).toBeNull()
    })
  })

  describe('setDataset', () => {
    it('should set current dataset with uploadedAt timestamp', () => {
      const store = useDatasetStore()
      const mockDataset = {
        id: 'test123',
        filename: 'test.csv',
        stats: { n_rows: 100, n_cols: 5 },
        issues: []
      }

      store.setDataset(mockDataset)

      expect(store.currentDataset).toBeDefined()
      expect(store.currentDataset.id).toBe('test123')
      expect(store.currentDataset.filename).toBe('test.csv')
      expect(store.currentDataset.uploadedAt).toBeDefined()
      expect(typeof store.currentDataset.uploadedAt).toBe('number')
    })

    it('should preserve all dataset properties', () => {
      const store = useDatasetStore()
      const mockDataset = {
        id: 'dataset_456',
        filename: 'customers.csv',
        stats: {
          n_rows: 451017,
          n_cols: 23,
          features: { age: { type: 'numeric', mean: 35.2 } }
        },
        issues: [{ type: 'missing_values', severity: 'HIGH' }],
        preview: { sample: [{ age: 25 }], rows: 451017, columns: 23 },
        description: 'Test dataset'
      }

      store.setDataset(mockDataset)

      expect(store.currentDataset.stats.n_rows).toBe(451017)
      expect(store.currentDataset.issues.length).toBe(1)
      expect(store.currentDataset.preview).toBeDefined()
      expect(store.currentDataset.description).toBe('Test dataset')
    })
  })

  describe('addMessage', () => {
    it('should add user message to chatHistory', () => {
      const store = useDatasetStore()

      store.addMessage('Hello', 'user')

      expect(store.chatHistory.length).toBe(1)
      expect(store.chatHistory[0].content).toBe('Hello')
      expect(store.chatHistory[0].type).toBe('user')
      expect(store.chatHistory[0].id).toBeDefined()
    })

    it('should add assistant message to chatHistory', () => {
      const store = useDatasetStore()

      store.addMessage('Analysis complete', 'assistant')

      expect(store.chatHistory.length).toBe(1)
      expect(store.chatHistory[0].content).toBe('Analysis complete')
      expect(store.chatHistory[0].type).toBe('assistant')
    })

    it('should add multiple messages in order', () => {
      const store = useDatasetStore()

      store.addMessage('Message 1', 'user')
      store.addMessage('Reply 1', 'assistant')
      store.addMessage('Message 2', 'user')

      expect(store.chatHistory.length).toBe(3)
      expect(store.chatHistory[0].content).toBe('Message 1')
      expect(store.chatHistory[1].content).toBe('Reply 1')
      expect(store.chatHistory[2].content).toBe('Message 2')
    })

    it('should generate unique IDs for each message', () => {
      const store = useDatasetStore()

      store.addMessage('Message 1', 'user')
      store.addMessage('Message 2', 'user')

      expect(store.chatHistory[0].id).not.toBe(store.chatHistory[1].id)
    })
  })

  describe('clearHistory', () => {
    it('should clear all chat messages', () => {
      const store = useDatasetStore()

      store.addMessage('Message 1', 'user')
      store.addMessage('Message 2', 'assistant')
      expect(store.chatHistory.length).toBe(2)

      store.clearHistory()

      expect(store.chatHistory.length).toBe(0)
    })
  })

  describe('reset', () => {
    it('should reset all store state to initial values', () => {
      const store = useDatasetStore()

      // Set some state
      store.setDataset({ id: 'test', filename: 'test.csv' })
      store.addMessage('Test message', 'user')
      store.isAnalyzing = true
      store.uploadedFile = { name: 'test.csv' }

      // Reset
      store.reset()

      // Verify all state is reset
      expect(store.currentDataset).toBeNull()
      expect(store.chatHistory).toEqual([])
      expect(store.isAnalyzing).toBe(false)
      expect(store.uploadedFile).toBeNull()
    })
  })

  describe('State Persistence Across Multiple Operations', () => {
    it('should maintain dataset while adding chat messages', () => {
      const store = useDatasetStore()

      const mockDataset = { id: 'test', filename: 'test.csv' }
      store.setDataset(mockDataset)

      store.addMessage('Message 1', 'user')
      store.addMessage('Message 2', 'assistant')

      expect(store.currentDataset).toBeDefined()
      expect(store.currentDataset.id).toBe('test')
      expect(store.chatHistory.length).toBe(2)
    })

    it('should allow updating dataset without affecting chat history', () => {
      const store = useDatasetStore()

      store.addMessage('Message 1', 'user')

      const dataset1 = { id: 'dataset1', filename: 'file1.csv' }
      store.setDataset(dataset1)

      const dataset2 = { id: 'dataset2', filename: 'file2.csv' }
      store.setDataset(dataset2)

      expect(store.currentDataset.id).toBe('dataset2')
      expect(store.chatHistory.length).toBe(1)
      expect(store.chatHistory[0].content).toBe('Message 1')
    })
  })
})
