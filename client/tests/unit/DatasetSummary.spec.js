/**
 * Unit Tests for DatasetSummary Component
 *
 * Tests the "About this dataset" section with stats and description
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DatasetSummary from '../../src/components/DatasetSummary.vue'

describe('DatasetSummary Component', () => {
  const mockDataset = {
    filename: 'customers.csv',
    uploadedAt: 1704672000000, // 2024-01-08
    stats: {
      n_rows: 451017,
      n_cols: 23
    },
    issues: [
      { type: 'missing_values', severity: 'HIGH', feature: 'age' },
      { type: 'duplicates', severity: 'MEDIUM', feature: 'id' },
      { type: 'outliers', severity: 'LOW', feature: 'price' }
    ],
    description: 'Customer transaction dataset with demographics'
  }

  describe('Rendering', () => {
    it('should render the component', () => {
      const wrapper = mount(DatasetSummary, {
        props: { dataset: mockDataset }
      })

      expect(wrapper.exists()).toBe(true)
    })

    it('should display dataset filename', () => {
      const wrapper = mount(DatasetSummary, {
        props: { dataset: mockDataset }
      })

      const text = wrapper.text()
      expect(text).toContain('customers.csv')
    })

    it('should display upload timestamp', () => {
      const wrapper = mount(DatasetSummary, {
        props: { dataset: mockDataset }
      })

      const metaItems = wrapper.findAll('.meta-item')
      expect(metaItems.length).toBeGreaterThan(0)
      // Should contain date info
      expect(wrapper.text()).toMatch(/\d+\/\d+\/\d+/)
    })

    it('should display "About this dataset" heading', () => {
      const wrapper = mount(DatasetSummary, {
        props: { dataset: mockDataset }
      })

      expect(wrapper.find('.summary-title').text()).toBe('About this dataset')
    })

    it('should display dataset description', () => {
      const wrapper = mount(DatasetSummary, {
        props: { dataset: mockDataset }
      })

      expect(wrapper.find('.summary-description').text()).toContain(
        'Customer transaction dataset with demographics'
      )
    })
  })

  describe('Statistics Cards', () => {
    it('should display row count', () => {
      const wrapper = mount(DatasetSummary, {
        props: { dataset: mockDataset }
      })

      const statCards = wrapper.findAll('.stat-card')
      const rowsCard = statCards[0]

      expect(rowsCard.find('.stat-value').text()).toContain('451,017')
      expect(rowsCard.find('.stat-label').text()).toBe('Rows')
    })

    it('should display column count', () => {
      const wrapper = mount(DatasetSummary, {
        props: { dataset: mockDataset }
      })

      const statCards = wrapper.findAll('.stat-card')
      const colsCard = statCards[1]

      expect(colsCard.find('.stat-value').text()).toBe('23')
      expect(colsCard.find('.stat-label').text()).toBe('Columns')
    })

    it('should display total issues count', () => {
      const wrapper = mount(DatasetSummary, {
        props: { dataset: mockDataset }
      })

      const statCards = wrapper.findAll('.stat-card')
      const issuesCard = statCards[2]

      expect(issuesCard.find('.stat-value').text()).toBe('3')
      expect(issuesCard.find('.stat-label').text()).toBe('Issues Detected')
    })
  })

  describe('Severity Breakdown', () => {
    it('should show high severity count', () => {
      const wrapper = mount(DatasetSummary, {
        props: { dataset: mockDataset }
      })

      const highSeverity = wrapper.find('.severity-item.high')
      expect(highSeverity.exists()).toBe(true)
      expect(highSeverity.text()).toContain('1')
      expect(highSeverity.text()).toContain('High')
    })

    it('should show medium severity count', () => {
      const wrapper = mount(DatasetSummary, {
        props: { dataset: mockDataset }
      })

      const mediumSeverity = wrapper.find('.severity-item.medium')
      expect(mediumSeverity.exists()).toBe(true)
      expect(mediumSeverity.text()).toContain('1')
      expect(mediumSeverity.text()).toContain('Medium')
    })

    it('should show low severity count', () => {
      const wrapper = mount(DatasetSummary, {
        props: { dataset: mockDataset }
      })

      const lowSeverity = wrapper.find('.severity-item.low')
      expect(lowSeverity.exists()).toBe(true)
      expect(lowSeverity.text()).toContain('1')
      expect(lowSeverity.text()).toContain('Low')
    })

    it('should hide severity items with zero count', () => {
      const datasetNoHighSeverity = {
        ...mockDataset,
        issues: [
          { type: 'test', severity: 'MEDIUM' },
          { type: 'test2', severity: 'LOW' }
        ]
      }

      const wrapper = mount(DatasetSummary, {
        props: { dataset: datasetNoHighSeverity }
      })

      expect(wrapper.find('.severity-item.high').exists()).toBe(false)
      expect(wrapper.find('.severity-item.medium').exists()).toBe(true)
      expect(wrapper.find('.severity-item.low').exists()).toBe(true)
    })
  })

  describe('Fallback Description', () => {
    it('should generate placeholder description when LLM description is null', () => {
      const datasetNoDescription = {
        ...mockDataset,
        description: null
      }

      const wrapper = mount(DatasetSummary, {
        props: { dataset: datasetNoDescription }
      })

      const description = wrapper.find('.summary-description').text()
      expect(description).toContain('451,017')
      expect(description).toContain('23 features')
      expect(description).toContain('3 data quality issue(s)')
    })

    it('should use LLM description when available', () => {
      const wrapper = mount(DatasetSummary, {
        props: { dataset: mockDataset }
      })

      const description = wrapper.find('.summary-description').text()
      expect(description).toBe('Customer transaction dataset with demographics')
    })
  })

  describe('Edge Cases', () => {
    it('should handle dataset with no issues', () => {
      const datasetNoIssues = {
        ...mockDataset,
        issues: []
      }

      const wrapper = mount(DatasetSummary, {
        props: { dataset: datasetNoIssues }
      })

      const statCards = wrapper.findAll('.stat-card')
      expect(statCards[2].find('.stat-value').text()).toBe('0')
      expect(wrapper.find('.severity-item').exists()).toBe(false)
    })

    it('should handle missing stats gracefully', () => {
      const datasetNoStats = {
        filename: 'test.csv',
        uploadedAt: Date.now(),
        stats: {},
        issues: []
      }

      const wrapper = mount(DatasetSummary, {
        props: { dataset: datasetNoStats }
      })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.stat-value').text()).toContain('0')
    })
  })
})
