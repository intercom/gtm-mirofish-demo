import { ref, computed, watch } from 'vue'
import { defineStore } from 'pinia'
import { reportBuilderApi } from '../api/reportBuilder'

const DEFAULT_THEME = {
  primaryColor: '#2068FF',
  accentColor: '#ff5600',
  fontFamily: 'Inter, system-ui, sans-serif',
  headingFont: 'Inter, system-ui, sans-serif',
  fontSize: 14,
  spacing: 'comfortable',
}

function createSection(type, position = -1, config = {}) {
  return {
    id: crypto.randomUUID(),
    type,
    position,
    config: { title: '', ...config },
    createdAt: Date.now(),
  }
}

export const useReportBuilderStore = defineStore('reportBuilder', () => {
  // --- State ---
  const templates = ref([])
  const activeTemplate = ref(null)
  const activeReport = ref(null)
  const sections = ref([])
  const theme = ref({ ...DEFAULT_THEME })
  const isDirty = ref(false)
  const loading = ref(false)
  const error = ref(null)

  // --- Computed ---
  const hasTemplates = computed(() => templates.value.length > 0)
  const hasSections = computed(() => sections.value.length > 0)
  const sectionCount = computed(() => sections.value.length)

  // Track mutations to sections and theme
  let dirtyWatchEnabled = false
  watch(
    [sections, theme],
    () => {
      if (dirtyWatchEnabled) isDirty.value = true
    },
    { deep: true },
  )

  // --- Actions ---

  async function fetchTemplates(force = false) {
    if (templates.value.length > 0 && !force) return templates.value

    loading.value = true
    error.value = null
    try {
      const res = await reportBuilderApi.listTemplates()
      templates.value = res.data?.templates ?? res.data ?? []
      return templates.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function loadTemplate(id) {
    loading.value = true
    error.value = null
    try {
      const res = await reportBuilderApi.getTemplate(id)
      const tmpl = res.data
      activeTemplate.value = tmpl
      sections.value = (tmpl.sections || []).map((s, i) => ({
        ...s,
        id: s.id || crypto.randomUUID(),
        position: s.position ?? i,
      }))
      theme.value = { ...DEFAULT_THEME, ...(tmpl.theme || {}) }
      isDirty.value = false
      dirtyWatchEnabled = true
      return tmpl
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function saveTemplate() {
    if (!activeTemplate.value) return null

    loading.value = true
    error.value = null
    try {
      const payload = {
        ...activeTemplate.value,
        sections: sections.value,
        theme: theme.value,
      }
      const isNew = !activeTemplate.value.id
      const res = isNew
        ? await reportBuilderApi.saveTemplate(payload)
        : await reportBuilderApi.updateTemplate(activeTemplate.value.id, payload)
      activeTemplate.value = res.data
      isDirty.value = false
      return res.data
    } catch (e) {
      error.value = e.message
      return null
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
      if (activeTemplate.value?.id === templateId) {
        activeTemplate.value = null
        sections.value = []
        theme.value = { ...DEFAULT_THEME }
      }
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  function addSection(type, position = -1, config = {}) {
    const section = createSection(type, position, config)
    if (position >= 0 && position < sections.value.length) {
      sections.value.splice(position, 0, section)
    } else {
      sections.value.push(section)
    }
    sections.value.forEach((s, i) => { s.position = i })
    return section
  }

  function removeSection(id) {
    const idx = sections.value.findIndex(s => s.id === id)
    if (idx === -1) return
    sections.value.splice(idx, 1)
    sections.value.forEach((s, i) => { s.position = i })
  }

  function updateSection(id, config) {
    const section = sections.value.find(s => s.id === id)
    if (!section) return
    Object.assign(section.config, config)
  }

  function reorderSections(newOrder) {
    const ordered = newOrder
      .map(id => sections.value.find(s => s.id === id))
      .filter(Boolean)
    ordered.forEach((s, i) => { s.position = i })
    sections.value = ordered
  }

  function setTheme(newTheme) {
    Object.assign(theme.value, newTheme)
  }

  async function generateReport(simulationIds) {
    loading.value = true
    error.value = null
    try {
      const res = await reportBuilderApi.generate({
        templateId: activeTemplate.value?.id,
        sections: sections.value,
        theme: theme.value,
        simulationIds,
      })
      activeReport.value = res.data
      return res.data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchReports(params) {
    loading.value = true
    error.value = null
    try {
      const res = await reportBuilderApi.listReports(params)
      return res.data?.reports ?? res.data ?? []
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchReport(id) {
    loading.value = true
    error.value = null
    try {
      const res = await reportBuilderApi.getReport(id)
      activeReport.value = res.data
      return res.data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  function newTemplate(name = 'Untitled Report') {
    activeTemplate.value = { name, sections: [], theme: { ...DEFAULT_THEME } }
    sections.value = []
    theme.value = { ...DEFAULT_THEME }
    isDirty.value = false
    dirtyWatchEnabled = true
  }

  function reset() {
    templates.value = []
    activeTemplate.value = null
    activeReport.value = null
    sections.value = []
    theme.value = { ...DEFAULT_THEME }
    isDirty.value = false
    dirtyWatchEnabled = false
    loading.value = false
    error.value = null
  }

  return {
    // State
    templates,
    activeTemplate,
    activeReport,
    sections,
    theme,
    isDirty,
    loading,
    error,
    // Computed
    hasTemplates,
    hasSections,
    sectionCount,
    // Actions
    fetchTemplates,
    loadTemplate,
    saveTemplate,
    deleteTemplate,
    addSection,
    removeSection,
    updateSection,
    reorderSections,
    setTheme,
    generateReport,
    fetchReports,
    fetchReport,
    newTemplate,
    reset,
  }
})
