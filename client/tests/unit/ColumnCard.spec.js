/**
 * Unit Tests for ColumnCard Component
 *
 * Tests individual column profiling cards with metrics and issues
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ColumnCard from '../../src/components/ColumnCard.vue'

describe('ColumnCard Component', () => {
  const mockNumericColumn = {
    columnName: 'age',
    stats: {
      type: 'numeric',
      completeness: 0.85,
      distinct_count: 87,
      distinctness: 0.45,
      entropy: 3.24,
      mean: 35.2,
      std: 12.5
    },
    issues: [
      {
        type: 'missing_values',
        severity: 'HIGH',
        description: '15% of values are missing'
      }
    ]
  }

  const mockCategoricalColumn = {
    columnName: 'country',
    stats: {
      type: 'categorical',
      completeness: 1.0,
      distinct_count: 25,
      distinctness: 0.12,
      entropy: 2.15
    },
    issues: []
  }

  describe('Rendering', () => {
    it('should render the component', () => {
      const wrapper = mount(ColumnCard, {
        props: mockNumericColumn
      })

      expect(wrapper.exists()).toBe(true)
    })

    it('should display column name', () => {
      const wrapper = mount(ColumnCard, {
        props: mockNumericColumn
      })

      expect(wrapper.find('.column-name').text()).toBe('age')
    })

    it('should display column type', () => {
      const wrapper = mount(ColumnCard, {
        props: mockNumericColumn
      })

      expect(wrapper.find('.column-type').text()).toBe('numeric')
    })
  })

  describe('Quality Badge', () => {
    it('should show "Critical" badge for HIGH severity issues', () => {
      const wrapper = mount(ColumnCard, {
        props: mockNumericColumn
      })

      const badge = wrapper.find('.quality-badge')
      expect(badge.text()).toBe('Critical')
      expect(badge.classes()).toContain('critical')
    })

    it('should show "Warning" badge for MEDIUM severity issues', () => {
      const mediumIssueColumn = {
        ...mockNumericColumn,
        issues: [{ type: 'test', severity: 'MEDIUM', description: 'test' }]
      }

      const wrapper = mount(ColumnCard, {
        props: mediumIssueColumn
      })

      const badge = wrapper.find('.quality-badge')
      expect(badge.text()).toBe('Warning')
      expect(badge.classes()).toContain('warning')
    })

    it('should show "Clean" badge when no issues', () => {
      const wrapper = mount(ColumnCard, {
        props: mockCategoricalColumn
      })

      const badge = wrapper.find('.quality-badge')
      expect(badge.text()).toBe('Clean')
      expect(badge.classes()).toContain('clean')
    })
  })

  describe('Completeness Metric', () => {
    it('should display completeness percentage', () => {
      const wrapper = mount(ColumnCard, {
        props: mockNumericColumn
      })

      const completenessRow = wrapper.findAll('.metric-row')[0]
      expect(completenessRow.find('.metric-label').text()).toBe('Completeness')
      expect(completenessRow.find('.metric-value').text()).toBe('85.0%')
    })

    it('should show completeness bar with correct width', () => {
      const wrapper = mount(ColumnCard, {
        props: mockNumericColumn
      })

      const completenessFill = wrapper.find('.completeness-fill')
      expect(completenessFill.attributes('style')).toContain('width: 85%')
    })

    it('should handle 100% completeness', () => {
      const wrapper = mount(ColumnCard, {
        props: mockCategoricalColumn
      })

      const completenessRow = wrapper.findAll('.metric-row')[0]
      expect(completenessRow.find('.metric-value').text()).toBe('100.0%')
    })

    it('should default to 100% when completeness is undefined', () => {
      const columnNoCompleteness = {
        columnName: 'test',
        stats: { type: 'text' },
        issues: []
      }

      const wrapper = mount(ColumnCard, {
        props: columnNoCompleteness
      })

      const completenessRow = wrapper.findAll('.metric-row')[0]
      expect(completenessRow.find('.metric-value').text()).toBe('100.0%')
    })
  })

  describe('Numeric Metrics', () => {
    it('should display distinct count', () => {
      const wrapper = mount(ColumnCard, {
        props: mockNumericColumn
      })

      const text = wrapper.text()
      expect(text).toContain('Distinct Values')
      expect(text).toContain('87')
    })

    it('should display distinctness percentage', () => {
      const wrapper = mount(ColumnCard, {
        props: mockNumericColumn
      })

      const text = wrapper.text()
      expect(text).toContain('Distinctness')
      expect(text).toContain('45.0%')
    })

    it('should display entropy value', () => {
      const wrapper = mount(ColumnCard, {
        props: mockNumericColumn
      })

      const text = wrapper.text()
      expect(text).toContain('Entropy')
      expect(text).toContain('3.24')
    })

    it('should display mean for numeric columns', () => {
      const wrapper = mount(ColumnCard, {
        props: mockNumericColumn
      })

      const text = wrapper.text()
      expect(text).toContain('Mean')
      expect(text).toContain('35.20')
    })

    it('should display standard deviation for numeric columns', () => {
      const wrapper = mount(ColumnCard, {
        props: mockNumericColumn
      })

      const text = wrapper.text()
      expect(text).toContain('Std Dev')
      expect(text).toContain('12.50')
    })

    it('should hide mean/std for non-numeric columns', () => {
      const wrapper = mount(ColumnCard, {
        props: mockCategoricalColumn
      })

      const text = wrapper.text()
      expect(text).not.toContain('Mean')
      expect(text).not.toContain('Std Dev')
    })
  })

  describe('Issues List', () => {
    it('should display issues section when issues exist', () => {
      const wrapper = mount(ColumnCard, {
        props: mockNumericColumn
      })

      const issuesSection = wrapper.find('.column-issues')
      expect(issuesSection.exists()).toBe(true)
      expect(issuesSection.find('.issues-header').text()).toBe('Issues Detected')
    })

    it('should not display issues section when no issues', () => {
      const wrapper = mount(ColumnCard, {
        props: mockCategoricalColumn
      })

      expect(wrapper.find('.column-issues').exists()).toBe(false)
    })

    it('should display issue description', () => {
      const wrapper = mount(ColumnCard, {
        props: mockNumericColumn
      })

      const issueText = wrapper.find('.issue-text').text()
      expect(issueText).toBe('15% of values are missing')
    })

    it('should show correct severity icon', () => {
      const wrapper = mount(ColumnCard, {
        props: mockNumericColumn
      })

      const issueIcon = wrapper.find('.issue-icon').text()
      expect(issueIcon).toBe('🔴') // HIGH severity
    })

    it('should display multiple issues', () => {
      const multiIssueColumn = {
        ...mockNumericColumn,
        issues: [
          { type: 'missing', severity: 'HIGH', description: 'Issue 1' },
          { type: 'outliers', severity: 'MEDIUM', description: 'Issue 2' },
          { type: 'range', severity: 'LOW', description: 'Issue 3' }
        ]
      }

      const wrapper = mount(ColumnCard, {
        props: multiIssueColumn
      })

      const issueItems = wrapper.findAll('.issue-item')
      expect(issueItems.length).toBe(3)
    })
  })

  describe('Histogram Placeholder', () => {
    it('should display histogram placeholder', () => {
      const wrapper = mount(ColumnCard, {
        props: mockNumericColumn
      })

      const histogram = wrapper.find('.histogram-placeholder')
      expect(histogram.exists()).toBe(true)
      expect(histogram.find('.histogram-label').text()).toBe('Distribution')
      expect(histogram.find('.histogram-message').text()).toBe(
        'Histogram visualization coming soon'
      )
    })
  })

  describe('Hover Effect', () => {
    it('should have hover transition class', () => {
      const wrapper = mount(ColumnCard, {
        props: mockNumericColumn
      })

      const card = wrapper.find('.column-card')
      expect(card.exists()).toBe(true)
      // Component should have the class that enables hover effects
      expect(card.classes()).toContain('column-card')
    })
  })

  describe('Edge Cases', () => {
    it('should handle column with minimal stats', () => {
      const minimalColumn = {
        columnName: 'id',
        stats: { type: 'text' },
        issues: []
      }

      const wrapper = mount(ColumnCard, {
        props: minimalColumn
      })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.column-name').text()).toBe('id')
    })

    it('should handle undefined optional metrics gracefully', () => {
      const columnNoOptionalMetrics = {
        columnName: 'test',
        stats: {
          type: 'numeric',
          completeness: 1.0
          // No distinctness, entropy, mean, std
        },
        issues: []
      }

      const wrapper = mount(ColumnCard, {
        props: columnNoOptionalMetrics
      })

      expect(wrapper.exists()).toBe(true)
      const text = wrapper.text()
      expect(text).not.toContain('Distinctness')
      expect(text).not.toContain('Entropy')
      expect(text).not.toContain('Mean')
    })
  })
})
