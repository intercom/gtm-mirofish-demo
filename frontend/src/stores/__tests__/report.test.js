import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useReportStore } from '../report'

describe('useReportStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  // --- Initial state ---

  it('has correct initial state', () => {
    const store = useReportStore()
    expect(store.selectedTemplate).toBeNull()
    expect(store.reportId).toBeNull()
    expect(store.templateId).toBeNull()
  })

  // --- hasTemplate computed ---

  it('hasTemplate is false when no template set', () => {
    const store = useReportStore()
    expect(store.hasTemplate).toBe(false)
  })

  it('hasTemplate is true when template is set', () => {
    const store = useReportStore()
    store.setTemplate({ id: 'tpl-1', name: 'Standard', section_count: 3 })
    expect(store.hasTemplate).toBe(true)
  })

  // --- isAIPlanned computed ---

  it('isAIPlanned is true when no template', () => {
    const store = useReportStore()
    expect(store.isAIPlanned).toBe(true)
  })

  it('isAIPlanned is true when template has section_count 0', () => {
    const store = useReportStore()
    store.setTemplate({ id: 'tpl-1', name: 'Empty', section_count: 0 })
    expect(store.isAIPlanned).toBe(true)
  })

  it('isAIPlanned is false when template has sections', () => {
    const store = useReportStore()
    store.setTemplate({ id: 'tpl-1', name: 'Standard', section_count: 5 })
    expect(store.isAIPlanned).toBe(false)
  })

  // --- setTemplate ---

  it('setTemplate stores template and sets templateId', () => {
    const store = useReportStore()
    const tpl = { id: 'tpl-42', name: 'Custom Report', section_count: 7 }
    store.setTemplate(tpl)
    expect(store.selectedTemplate).toEqual(tpl)
    expect(store.templateId).toBe('tpl-42')
  })

  it('setTemplate sets templateId to null when template has no id', () => {
    const store = useReportStore()
    store.setTemplate({ name: 'No ID Template' })
    expect(store.selectedTemplate).toEqual({ name: 'No ID Template' })
    expect(store.templateId).toBeNull()
  })

  it('setTemplate with null clears template and templateId', () => {
    const store = useReportStore()
    store.setTemplate({ id: 'tpl-1', name: 'Test' })
    store.setTemplate(null)
    expect(store.selectedTemplate).toBeNull()
    expect(store.templateId).toBeNull()
  })

  // --- setReportId ---

  it('setReportId stores the report id', () => {
    const store = useReportStore()
    store.setReportId('report-99')
    expect(store.reportId).toBe('report-99')
  })

  // --- reset ---

  it('reset clears all state', () => {
    const store = useReportStore()
    store.setTemplate({ id: 'tpl-1', name: 'Test', section_count: 3 })
    store.setReportId('report-1')

    store.reset()

    expect(store.selectedTemplate).toBeNull()
    expect(store.reportId).toBeNull()
    expect(store.templateId).toBeNull()
    expect(store.hasTemplate).toBe(false)
    expect(store.isAIPlanned).toBe(true)
  })
})
