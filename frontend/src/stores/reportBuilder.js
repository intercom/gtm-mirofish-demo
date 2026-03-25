import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { reportBuilderApi } from '../api/reportBuilder'

const STORAGE_KEY = 'mirofish_report_builder'

function loadDraft() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export const useReportBuilderStore = defineStore('reportBuilder', () => {
  // Current template being edited
  const template = ref(null)
  const templates = ref([])
  const reports = ref([])
  const loading = ref(false)
  const error = ref(null)

  const hasTemplate = computed(() => template.value !== null)
  const sectionCount = computed(() => template.value?.sections?.length ?? 0)

  // ── Template editing ────────────────────────────────────────

  function createTemplate(name = 'Untitled Report') {
    template.value = {
      id: null,
      name,
      sections: [],
      theme: {
        primary_color: '#2068FF',
        accent_color: '#ff5600',
        font_family: 'system-ui',
      },
      page_orientation: 'portrait',
      header_config: { show_logo: true, title: '', subtitle: '' },
      footer_config: { show_page_numbers: true, text: '' },
    }
    saveDraft()
  }

  function addSection(section) {
    if (!template.value) return
    const id = `sec_${Date.now().toString(36)}`
    template.value.sections.push({
      id,
      type: section.type || 'text',
      title: section.title || '',
      position: template.value.sections.length,
      width: section.width || 'full',
      config: section.config || {},
      data_source: section.data_source || null,
    })
    reindexPositions()
    saveDraft()
  }

  function updateSection(sectionId, updates) {
    if (!template.value) return
    const idx = template.value.sections.findIndex(s => s.id === sectionId)
    if (idx === -1) return
    Object.assign(template.value.sections[idx], updates)
    saveDraft()
  }

  function removeSection(sectionId) {
    if (!template.value) return
    template.value.sections = template.value.sections.filter(s => s.id !== sectionId)
    reindexPositions()
    saveDraft()
  }

  function moveSection(sectionId, newPosition) {
    if (!template.value) return
    const sections = template.value.sections
    const idx = sections.findIndex(s => s.id === sectionId)
    if (idx === -1 || newPosition < 0 || newPosition >= sections.length) return
    const [moved] = sections.splice(idx, 1)
    sections.splice(newPosition, 0, moved)
    reindexPositions()
    saveDraft()
  }

  function reindexPositions() {
    if (!template.value) return
    template.value.sections.forEach((s, i) => { s.position = i })
  }

  function updateTheme(theme) {
    if (!template.value) return
    Object.assign(template.value.theme, theme)
    saveDraft()
  }

  function updateHeaderConfig(config) {
    if (!template.value) return
    Object.assign(template.value.header_config, config)
    saveDraft()
  }

  function updateFooterConfig(config) {
    if (!template.value) return
    Object.assign(template.value.footer_config, config)
    saveDraft()
  }

  // ── Draft persistence (localStorage) ───────────────────────

  function saveDraft() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(template.value))
    } catch {
      // Storage full — silently ignore
    }
  }

  function loadDraftTemplate() {
    const draft = loadDraft()
    if (draft) template.value = draft
  }

  function clearDraft() {
    localStorage.removeItem(STORAGE_KEY)
  }

  // ── API interactions ────────────────────────────────────────

  async function fetchTemplates() {
    loading.value = true
    error.value = null
    try {
      const res = await reportBuilderApi.listTemplates()
      templates.value = res.data.templates ?? []
    } catch (e) {
      error.value = e.message || 'Failed to load templates'
    } finally {
      loading.value = false
    }
  }

  async function saveTemplate() {
    if (!template.value) return null
    loading.value = true
    error.value = null
    try {
      let res
      if (template.value.id) {
        res = await reportBuilderApi.updateTemplate(template.value.id, template.value)
      } else {
        res = await reportBuilderApi.createTemplate(template.value)
      }
      const saved = res.data.template
      template.value.id = saved.id
      clearDraft()
      await fetchTemplates()
      return saved
    } catch (e) {
      error.value = e.message || 'Failed to save template'
      return null
    } finally {
      loading.value = false
    }
  }

  async function loadTemplate(templateId) {
    loading.value = true
    error.value = null
    try {
      const res = await reportBuilderApi.getTemplate(templateId)
      template.value = res.data.template
    } catch (e) {
      error.value = e.message || 'Failed to load template'
    } finally {
      loading.value = false
    }
  }

  async function deleteTemplate(templateId) {
    loading.value = true
    error.value = null
    try {
      await reportBuilderApi.deleteTemplate(templateId)
      templates.value = templates.value.filter(t => t.id !== templateId)
      if (template.value?.id === templateId) template.value = null
    } catch (e) {
      error.value = e.message || 'Failed to delete template'
    } finally {
      loading.value = false
    }
  }

  async function fetchReports() {
    loading.value = true
    error.value = null
    try {
      const res = await reportBuilderApi.listReports()
      reports.value = res.data.reports ?? []
    } catch (e) {
      error.value = e.message || 'Failed to load reports'
    } finally {
      loading.value = false
    }
  }

  async function generateReport(simulationIds, method = 'template') {
    if (!template.value?.id) return null
    loading.value = true
    error.value = null
    try {
      const res = await reportBuilderApi.generate({
        template_id: template.value.id,
        simulation_ids: simulationIds,
        generation_method: method,
      })
      const report = res.data.report
      reports.value.unshift(report)
      return report
    } catch (e) {
      error.value = e.message || 'Failed to generate report'
      return null
    } finally {
      loading.value = false
    }
  }

  function reset() {
    template.value = null
    error.value = null
    clearDraft()
  }

  return {
    template,
    templates,
    reports,
    loading,
    error,
    hasTemplate,
    sectionCount,
    createTemplate,
    addSection,
    updateSection,
    removeSection,
    moveSection,
    updateTheme,
    updateHeaderConfig,
    updateFooterConfig,
    saveDraft,
    loadDraftTemplate,
    clearDraft,
    fetchTemplates,
    saveTemplate,
    loadTemplate,
    deleteTemplate,
    fetchReports,
    generateReport,
    reset,
  }
})
