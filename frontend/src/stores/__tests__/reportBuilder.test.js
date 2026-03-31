import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('../../api/reportBuilder', () => ({
  reportBuilderApi: {
    listTemplates: vi.fn(),
    getTemplate: vi.fn(),
    saveTemplate: vi.fn(),
    updateTemplate: vi.fn(),
    deleteTemplate: vi.fn(),
    generate: vi.fn(),
    listReports: vi.fn(),
    getReport: vi.fn(),
    deleteReport: vi.fn(),
  },
}))

import { useReportBuilderStore } from '../reportBuilder'
import { reportBuilderApi } from '../../api/reportBuilder'

describe('useReportBuilderStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('has empty templates', () => {
      const store = useReportBuilderStore()
      expect(store.templates).toEqual([])
    })

    it('has null activeTemplate and activeReport', () => {
      const store = useReportBuilderStore()
      expect(store.activeTemplate).toBeNull()
      expect(store.activeReport).toBeNull()
    })

    it('has default theme', () => {
      const store = useReportBuilderStore()
      expect(store.theme).toEqual({
        primaryColor: '#2068FF',
        accentColor: '#ff5600',
        fontFamily: 'Inter, system-ui, sans-serif',
        headingFont: 'Inter, system-ui, sans-serif',
        fontSize: 14,
        spacing: 'comfortable',
      })
    })

    it('has empty sections', () => {
      const store = useReportBuilderStore()
      expect(store.sections).toEqual([])
    })

    it('is not loading, dirty, or errored', () => {
      const store = useReportBuilderStore()
      expect(store.loading).toBe(false)
      expect(store.isDirty).toBe(false)
      expect(store.error).toBeNull()
    })
  })

  describe('computed', () => {
    it('hasTemplates is false when empty', () => {
      const store = useReportBuilderStore()
      expect(store.hasTemplates).toBe(false)
    })

    it('hasTemplates is true when templates exist', () => {
      const store = useReportBuilderStore()
      store.templates = [{ id: '1', name: 'Test' }]
      expect(store.hasTemplates).toBe(true)
    })

    it('hasSections is false when empty', () => {
      const store = useReportBuilderStore()
      expect(store.hasSections).toBe(false)
    })

    it('hasSections is true when sections exist', () => {
      const store = useReportBuilderStore()
      store.addSection('chart')
      expect(store.hasSections).toBe(true)
    })

    it('sectionCount reflects the number of sections', () => {
      const store = useReportBuilderStore()
      expect(store.sectionCount).toBe(0)
      store.addSection('chart')
      store.addSection('table')
      expect(store.sectionCount).toBe(2)
    })
  })

  describe('addSection', () => {
    it('appends to the end by default', () => {
      const store = useReportBuilderStore()
      store.addSection('chart')
      store.addSection('table')
      expect(store.sections).toHaveLength(2)
      expect(store.sections[0].type).toBe('chart')
      expect(store.sections[1].type).toBe('table')
    })

    it('inserts at a specific position', () => {
      const store = useReportBuilderStore()
      store.addSection('chart')
      store.addSection('table')
      store.addSection('text', 1)
      expect(store.sections).toHaveLength(3)
      expect(store.sections[1].type).toBe('text')
    })

    it('generates unique id for each section', () => {
      const store = useReportBuilderStore()
      const s1 = store.addSection('chart')
      const s2 = store.addSection('table')
      expect(s1.id).toBeTruthy()
      expect(s2.id).toBeTruthy()
      expect(s1.id).not.toBe(s2.id)
    })

    it('sets position indices correctly', () => {
      const store = useReportBuilderStore()
      store.addSection('chart')
      store.addSection('table')
      store.addSection('text', 1)
      expect(store.sections[0].position).toBe(0)
      expect(store.sections[1].position).toBe(1)
      expect(store.sections[2].position).toBe(2)
    })
  })

  describe('removeSection', () => {
    it('removes by id and re-indexes positions', () => {
      const store = useReportBuilderStore()
      const s1 = store.addSection('chart')
      store.addSection('table')
      const s3 = store.addSection('text')

      store.removeSection(s1.id)

      expect(store.sections).toHaveLength(2)
      expect(store.sections[0].type).toBe('table')
      expect(store.sections[0].position).toBe(0)
      expect(store.sections[1].id).toBe(s3.id)
      expect(store.sections[1].position).toBe(1)
    })

    it('does nothing for non-existent id', () => {
      const store = useReportBuilderStore()
      store.addSection('chart')
      store.removeSection('non-existent')
      expect(store.sections).toHaveLength(1)
    })
  })

  describe('updateSection', () => {
    it('merges config into existing section', () => {
      const store = useReportBuilderStore()
      const section = store.addSection('chart', -1, { title: 'Revenue' })

      store.updateSection(section.id, { color: 'blue', title: 'Updated' })

      const updated = store.sections.find(s => s.id === section.id)
      expect(updated.config.title).toBe('Updated')
      expect(updated.config.color).toBe('blue')
    })

    it('does nothing for non-existent id', () => {
      const store = useReportBuilderStore()
      store.addSection('chart')
      store.updateSection('non-existent', { title: 'foo' })
      expect(store.sections[0].config.title).toBe('')
    })
  })

  describe('reorderSections', () => {
    it('reorders by id array and updates positions', () => {
      const store = useReportBuilderStore()
      const s1 = store.addSection('chart')
      const s2 = store.addSection('table')
      const s3 = store.addSection('text')

      store.reorderSections([s3.id, s1.id, s2.id])

      expect(store.sections[0].id).toBe(s3.id)
      expect(store.sections[0].position).toBe(0)
      expect(store.sections[1].id).toBe(s1.id)
      expect(store.sections[1].position).toBe(1)
      expect(store.sections[2].id).toBe(s2.id)
      expect(store.sections[2].position).toBe(2)
    })
  })

  describe('setTheme', () => {
    it('merges new theme properties', () => {
      const store = useReportBuilderStore()
      store.setTheme({ primaryColor: '#000', fontSize: 18 })
      expect(store.theme.primaryColor).toBe('#000')
      expect(store.theme.fontSize).toBe(18)
      expect(store.theme.accentColor).toBe('#ff5600')
    })
  })

  describe('newTemplate', () => {
    it('creates a new empty template workspace', () => {
      const store = useReportBuilderStore()
      store.addSection('chart')
      store.newTemplate('My Report')

      expect(store.activeTemplate).toEqual({
        name: 'My Report',
        sections: [],
        theme: store.theme,
      })
      expect(store.sections).toEqual([])
      expect(store.isDirty).toBe(false)
    })

    it('defaults name to Untitled Report', () => {
      const store = useReportBuilderStore()
      store.newTemplate()
      expect(store.activeTemplate.name).toBe('Untitled Report')
    })
  })

  describe('reset', () => {
    it('clears all state back to defaults', () => {
      const store = useReportBuilderStore()
      store.templates = [{ id: '1' }]
      store.activeTemplate = { id: '1' }
      store.activeReport = { id: 'r1' }
      store.addSection('chart')
      store.error = 'some error'
      store.loading = true

      store.reset()

      expect(store.templates).toEqual([])
      expect(store.activeTemplate).toBeNull()
      expect(store.activeReport).toBeNull()
      expect(store.sections).toEqual([])
      expect(store.isDirty).toBe(false)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })
  })

  describe('fetchTemplates', () => {
    it('fetches from API and stores results', async () => {
      const store = useReportBuilderStore()
      const mockTemplates = [{ id: '1', name: 'T1' }, { id: '2', name: 'T2' }]
      reportBuilderApi.listTemplates.mockResolvedValue({ data: { templates: mockTemplates } })

      const result = await store.fetchTemplates()

      expect(reportBuilderApi.listTemplates).toHaveBeenCalledOnce()
      expect(result).toEqual(mockTemplates)
      expect(store.templates).toEqual(mockTemplates)
      expect(store.loading).toBe(false)
    })

    it('returns cached data when already loaded and not forced', async () => {
      const store = useReportBuilderStore()
      store.templates = [{ id: '1', name: 'Cached' }]

      const result = await store.fetchTemplates()

      expect(reportBuilderApi.listTemplates).not.toHaveBeenCalled()
      expect(result).toEqual([{ id: '1', name: 'Cached' }])
    })

    it('forces refetch when force is true', async () => {
      const store = useReportBuilderStore()
      store.templates = [{ id: '1', name: 'Cached' }]
      reportBuilderApi.listTemplates.mockResolvedValue({ data: { templates: [{ id: '2', name: 'New' }] } })

      await store.fetchTemplates(true)

      expect(reportBuilderApi.listTemplates).toHaveBeenCalledOnce()
      expect(store.templates).toEqual([{ id: '2', name: 'New' }])
    })

    it('handles API error', async () => {
      const store = useReportBuilderStore()
      reportBuilderApi.listTemplates.mockRejectedValue(new Error('Network error'))

      const result = await store.fetchTemplates()

      expect(result).toEqual([])
      expect(store.error).toBe('Network error')
      expect(store.loading).toBe(false)
    })
  })

  describe('deleteTemplate', () => {
    it('removes from list', async () => {
      const store = useReportBuilderStore()
      store.templates = [{ id: '1' }, { id: '2' }]
      reportBuilderApi.deleteTemplate.mockResolvedValue({})

      await store.deleteTemplate('1')

      expect(store.templates).toEqual([{ id: '2' }])
    })

    it('clears active if it matches deleted template', async () => {
      const store = useReportBuilderStore()
      store.templates = [{ id: '1' }, { id: '2' }]
      store.activeTemplate = { id: '1' }
      store.addSection('chart')
      reportBuilderApi.deleteTemplate.mockResolvedValue({})

      await store.deleteTemplate('1')

      expect(store.activeTemplate).toBeNull()
      expect(store.sections).toEqual([])
    })

    it('does not clear active if it does not match', async () => {
      const store = useReportBuilderStore()
      store.templates = [{ id: '1' }, { id: '2' }]
      store.activeTemplate = { id: '2' }
      reportBuilderApi.deleteTemplate.mockResolvedValue({})

      await store.deleteTemplate('1')

      expect(store.activeTemplate).toEqual({ id: '2' })
    })
  })
})
