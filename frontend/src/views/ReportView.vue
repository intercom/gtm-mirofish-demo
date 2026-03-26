<script setup>
import { ref, computed, defineAsyncComponent, watch, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'
import { API_BASE } from '../api/client'
import { useReportShortcuts } from '../composables/useReportShortcuts'
import { useToast } from '../composables/useToast'
import { useOnlineStatus } from '../composables/useOnlineStatus'
import { cacheReport, getCachedReport } from '../composables/useReportCache'
import { AppBreadcrumb } from '../components/common'
import { useBreadcrumbs } from '../composables/useBreadcrumbs'
import PhaseNav from '../components/simulation/PhaseNav.vue'
import ShimmerCard from '../components/ui/ShimmerCard.vue'
import ToolCallLog from '../components/report/ToolCallLog.vue'
import ReportSummaryCards from '../components/report/ReportSummaryCards.vue'
import DataTable from '../components/report/DataTable.vue'
import ThemeConfigurator from '../components/report-builder/ThemeConfigurator.vue'
import { useReportTheme } from '../composables/useReportTheme'
import ReportCanvas from '../components/report/ReportCanvas.vue'
import { useReportStore } from '../stores/report'
import ReportTemplateSelector from '../components/report/ReportTemplateSelector.vue'
import ReportShareModal from '../components/report/ReportShareModal.vue'
import ReportPreview from '../components/report-builder/ReportPreview.vue'
import RichTextEditor from '../components/report/RichTextEditor.vue'
import ComparisonOverlay from '../components/report/ComparisonOverlay.vue'

const ReportCharts = defineAsyncComponent({
  loader: () => import('../components/report/ReportCharts.vue'),
  loadingComponent: ShimmerCard,
  delay: 200,
})

const { resolvedTheme, themeStyles } = useReportTheme()
const showShareModal = ref(false)

const props = defineProps({ taskId: String })
const reportStore = useReportStore()
const { isOnline } = useOnlineStatus()

const { crumbs } = useBreadcrumbs()

const reportId = ref(null)
const sections = ref([])
const activeChapter = ref(0)
const generating = ref(false)
const progress = ref(0)
const progressMessage = ref('')
const error = ref(null)
const isComplete = ref(false)
const showAgentLog = ref(false)
const showThemePanel = ref(false)
const builderMode = ref(false)
const showExportMenu = ref(false)
const editingChapter = ref(null)
const editedHtml = ref({})
const editBuffer = ref('')
const servingFromCache = ref(false)
const cachedAt = ref(null)

const { success: toastSuccess } = useToast()

const agentTableRows = ref([])
const agentTableColumns = [
  { key: 'name', label: 'Agent', sortable: true },
  { key: 'total_actions', label: 'Actions', sortable: true, align: 'right' },
  { key: 'posts', label: 'Posts', sortable: true, align: 'right' },
  { key: 'replies', label: 'Replies', sortable: true, align: 'right' },
  { key: 'likes', label: 'Likes', sortable: true, align: 'right' },
]

const exportFormats = [
  { key: 'md', label: 'Markdown (.md)', icon: 'M↓' },
  { key: 'html', label: 'HTML (.html)', icon: '</>' },
  { key: 'pdf', label: 'PDF (.pdf)', icon: 'PDF' },
  { key: 'json', label: 'JSON (.json)', icon: '{ }' },
]

async function fetchAgentStats() {
  try {
    const res = await fetch(`${API_BASE}/simulation/${props.taskId}/agent-stats`)
    if (!res.ok) return
    const json = await res.json()
    if (json.success && json.data?.stats) {
      agentTableRows.value = json.data.stats.map((a) => ({
        name: a.agent_name || a.name || `Agent ${a.agent_id}`,
        total_actions: a.total_actions || 0,
        posts: a.posts || a.create_post || 0,
        replies: a.replies || a.reply || 0,
        likes: a.likes || a.like || 0,
      }))
    }
  } catch {
    // Agent stats are supplementary
  }
}

// Template selection phase — shown when no report exists yet
const showTemplateSelector = ref(false)
const selectedTemplate = ref(null)

let pollTimer = null

const chapters = computed(() =>
  sections.value.map((s) => {
    const titleMatch = s.content.match(/^##\s+(.+)/m)
    const baseHtml = marked.parse(s.content)
    return {
      title: titleMatch ? titleMatch[1] : `Section ${s.section_index}`,
      html: editedHtml.value[s.section_index] ?? baseHtml,
      markdown: s.content,
      index: s.section_index,
      edited: s.section_index in editedHtml.value,
    }
  })
)

const activeContent = computed(() => chapters.value[activeChapter.value] || null)

const keyFindings = computed(() => {
  const findings = []
  for (const ch of chapters.value) {
    const lines = ch.markdown.split('\n')
    let inFindings = false
    for (const line of lines) {
      if (/^###?\s.*(key finding|recommendation|insight|takeaway)/i.test(line)) {
        inFindings = true
        continue
      }
      if (inFindings && /^###?\s/.test(line)) break
      if (inFindings && line.startsWith('- ')) {
        findings.push(line.slice(2).trim())
      }
    }
  }
  return findings
})

const fullMarkdown = computed(() =>
  sections.value.map((s) => s.content).join('\n\n---\n\n')
)

const templateLabel = computed(() => {
  if (selectedTemplate.value) return selectedTemplate.value.name
  if (reportStore.selectedTemplate) return reportStore.selectedTemplate.name
  return null
})


async function loadFromCache() {
  const cached = await getCachedReport(props.taskId).catch(() => null)
  if (!cached) return false
  reportId.value = cached.reportId
  sections.value = cached.sections
  isComplete.value = cached.isComplete
  generating.value = false
  servingFromCache.value = true
  cachedAt.value = cached.cachedAt
  return true
}

async function saveToCache() {
  if (!reportId.value || sections.value.length === 0) return
  await cacheReport(props.taskId, {
    reportId: reportId.value,
    sections: sections.value,
    isComplete: isComplete.value,
  }).catch(() => {})
}

async function checkAndLoad() {
  if (!isOnline.value) {
    const loaded = await loadFromCache()
    if (!loaded) error.value = 'You are offline and no cached report is available.'
    return
  }
  try {
    const res = await fetch(`${API_BASE}/report/check/${props.taskId}`)
    if (!res.ok) {
      showTemplateSelector.value = true
      return
    }
    const json = await res.json()
    if (json.success && json.data.has_report) {
      reportId.value = json.data.report_id
      if (json.data.report_status === 'completed') {
        await loadSections()
        isComplete.value = true
        await saveToCache()
      } else {
        generating.value = true
        startPolling()
      }
    } else {
      showTemplateSelector.value = true
    }
  } catch {
    const loaded = await loadFromCache()
    if (!loaded) error.value = 'Failed to check report status'
  }
}

function onTemplateSelect(tpl) {
  selectedTemplate.value = tpl
  reportStore.setTemplate(tpl)
}

async function startGeneration() {
  showTemplateSelector.value = false
  generating.value = true
  try {
    const body = { simulation_id: props.taskId }
    if (selectedTemplate.value && selectedTemplate.value.id) {
      body.template_id = selectedTemplate.value.id
    }
    const res = await fetch(`${API_BASE}/report/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const json = await res.json()
    if (json.success) {
      reportId.value = json.data.report_id
      reportStore.setReportId(json.data.report_id)
      if (json.data.already_generated) {
        await loadSections()
        generating.value = false
        isComplete.value = true
      } else {
        startPolling()
      }
    } else {
      error.value = json.error || 'Failed to start report generation'
      generating.value = false
    }
  } catch {
    error.value = 'Failed to start report generation'
    generating.value = false
  }
}

async function loadSections() {
  if (!reportId.value) return
  try {
    const res = await fetch(`${API_BASE}/report/${reportId.value}/sections`)
    if (!res.ok) return
    const json = await res.json()
    if (json.success) {
      sections.value = json.data.sections
      isComplete.value = json.data.is_complete
      if (json.data.is_complete) await saveToCache()
    }
  } catch {
    // Silently retry on next poll
  }
}

async function pollProgress() {
  if (!reportId.value) return
  try {
    const res = await fetch(`${API_BASE}/report/${reportId.value}/progress`)
    if (res.ok) {
      const json = await res.json()
      if (json.success) {
        progress.value = json.data.progress || 0
        progressMessage.value = json.data.message || ''
      }
    }
  } catch {
    // Continue polling
  }
  await loadSections()
  if (isComplete.value) {
    generating.value = false
    stopPolling()
  }
}

function startPolling() {
  generating.value = true
  pollTimer = setInterval(pollProgress, 3000)
  pollProgress()
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function startEditing() {
  const ch = activeContent.value
  if (!ch) return
  editBuffer.value = ch.html
  editingChapter.value = activeChapter.value
}

function saveEditing() {
  const ch = chapters.value[editingChapter.value]
  if (ch) {
    editedHtml.value[ch.index] = editBuffer.value
  }
  editingChapter.value = null
  toastSuccess('Section updated')
}

function cancelEditing() {
  editingChapter.value = null
  editBuffer.value = ''
}

function revertEdits() {
  const ch = activeContent.value
  if (!ch) return
  delete editedHtml.value[ch.index]
  toastSuccess('Reverted to original')
}

function exportReport(format) {
  if ((servingFromCache.value || !isOnline.value) && format === 'md') {
    const blob = new Blob([fullMarkdown.value], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `report-${props.taskId}.md`
    a.click()
    URL.revokeObjectURL(url)
    showExportMenu.value = false
    return
  }
  if (reportId.value) {
    window.open(`${API_BASE}/report/${reportId.value}/download?format=${format}`, '_blank')
  }
  showExportMenu.value = false
}

function onClickOutsideExport(e) {
  if (!e.target.closest('.export-menu-wrapper')) {
    showExportMenu.value = false
  }
}

const toast = useToast()

const { showHelp, shortcuts } = useReportShortcuts({
  onPreview: () => window.print(),
  onExport: () => exportReport('md'),
  onSaveTemplate: () => toast.info('Save as template — coming soon'),
  onDeleteSection: () => toast.info('Section removal — coming soon'),
  onMoveUp: () => {
    if (activeChapter.value > 0) activeChapter.value--
  },
  onMoveDown: () => {
    if (activeChapter.value < chapters.value.length - 1) activeChapter.value++
  },
})

function handleReorder(from, to) {
  const arr = [...sections.value]
  const [moved] = arr.splice(from, 1)
  arr.splice(to, 0, moved)
  arr.forEach((s, i) => { s.section_index = i + 1 })
  sections.value = arr
}

function formatCachedDate() {
  if (!cachedAt.value) return ''
  return new Date(cachedAt.value).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
  })
}

watch(activeChapter, () => {
  if (editingChapter.value !== null) cancelEditing()
})

watch(isOnline, (online) => {
  if (online && servingFromCache.value) {
    servingFromCache.value = false
    cachedAt.value = null
    checkAndLoad()
  }
})

onMounted(() => {
  checkAndLoad()
  fetchAgentStats()
  document.addEventListener('click', onClickOutsideExport)
})
onUnmounted(() => {
  stopPolling()
  reportStore.reset()
  document.removeEventListener('click', onClickOutsideExport)
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 md:px-6 py-6 md:py-8">
    <AppBreadcrumb :crumbs="crumbs" class="-mx-4 md:-mx-6 -mt-6 md:-mt-8 mb-4" />
    <PhaseNav :taskId="taskId" activePhase="report" />

    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 md:mb-8">
      <div>
        <h1 class="text-xl md:text-2xl font-semibold text-[var(--color-text)]" style="letter-spacing: -0.64px">
          Predictive Report
        </h1>
        <p v-if="templateLabel && !showTemplateSelector" class="text-xs text-[#2068FF] font-medium mt-0.5">
          {{ templateLabel }}
        </p>
        <p v-if="generating" class="text-sm text-[var(--color-text-muted)] mt-1">
          {{ progressMessage || 'Generating multi-chapter analysis...' }}
        </p>
      </div>
      <div class="flex gap-2">
        <button
          v-if="!generating && sections.length > 1"
          @click="builderMode = !builderMode"
          class="border hover:bg-[var(--color-tint)] text-[var(--color-text)] px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          :class="builderMode ? 'border-[#2068FF] bg-[rgba(32,104,255,0.06)]' : 'border-[var(--color-border)]'"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
          {{ builderMode ? 'Done' : 'Reorder' }}
        </button>
        <button
          v-if="!generating && sections.length > 0"
          @click="showThemePanel = !showThemePanel"
          class="border border-[var(--color-border)] hover:bg-[var(--color-tint)] text-[var(--color-text)] px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          :class="showThemePanel ? 'bg-[var(--color-primary-light)] border-[var(--color-primary-border)]' : ''"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
          </svg>
          Theme
        </button>
        <button
          v-if="!generating && sections.length > 0"
          @click="showShareModal = true"
          class="border border-[var(--color-border)] hover:bg-[var(--color-tint)] text-[var(--color-text)] px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
          </svg>
          Share
        </button>
        <div v-if="!generating && sections.length > 0" class="relative export-menu-wrapper">
          <button
            @click.stop="showExportMenu = !showExportMenu"
            class="border border-[var(--color-border)] hover:bg-[var(--color-tint)] text-[var(--color-text)] px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Export
            <svg class="w-3 h-3 transition-transform" :class="{ 'rotate-180': showExportMenu }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <div
            v-if="showExportMenu"
            class="absolute right-0 top-full mt-1 w-48 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg shadow-lg z-20 py-1"
          >
            <button
              v-for="fmt in exportFormats"
              :key="fmt.key"
              @click="exportReport(fmt.key)"
              class="w-full text-left px-3 py-2 text-sm text-[var(--color-text)] hover:bg-[var(--color-tint)] flex items-center gap-3 transition-colors"
            >
              <span class="w-7 text-center text-xs font-mono text-[var(--color-text-muted)]">{{ fmt.icon }}</span>
              {{ fmt.label }}
            </button>
          </div>
        </div>
        <button
          @click="showHelp = !showHelp"
          class="border border-[var(--color-border)] hover:bg-[var(--color-tint)] text-[var(--color-text-secondary)] px-2.5 py-2 rounded-lg text-sm transition-colors"
          title="Keyboard shortcuts (?)"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        </button>
        <router-link
          :to="`/chat/${taskId}`"
          class="bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors no-underline"
        >
          Ask Follow-Up →
        </router-link>
      </div>
    </div>

    <!-- Keyboard Shortcuts Help -->
    <Transition name="fade">
      <div v-if="showHelp" class="mb-4 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-semibold text-[var(--color-text)]">Keyboard Shortcuts</h3>
          <button @click="showHelp = false" class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-1.5">
          <div v-for="s in shortcuts" :key="s.label" class="flex items-center justify-between gap-4 py-1">
            <span class="text-xs text-[var(--color-text-secondary)]">{{ s.label }}</span>
            <kbd class="shrink-0 text-[10px] font-mono bg-[var(--color-tint)] border border-[var(--color-border)] px-1.5 py-0.5 rounded text-[var(--color-text-muted)]">{{ s.keys }}</kbd>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Offline / Cached Banner -->
    <div
      v-if="servingFromCache"
      class="flex items-center gap-2 bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 rounded-lg px-4 py-3 mb-6 text-sm text-amber-700 dark:text-amber-400"
    >
      <svg class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M20.893 13.393l-1.135-1.135a2.252 2.252 0 01-.421-.585l-1.08-2.16a.414.414 0 00-.663-.107.827.827 0 01-.812.21l-1.273-.363a.89.89 0 00-.738 1.595l.587.39c.59.395.674 1.23.172 1.732l-.2.2c-.212.212-.33.498-.33.796v.41c0 .409-.11.809-.32 1.158l-1.315 2.191a2.11 2.11 0 01-1.81 1.025 1.055 1.055 0 01-1.055-1.055v-1.172c0-.92-.56-1.747-1.414-2.089l-.655-.261a2.25 2.25 0 01-1.383-2.46l.007-.042a2.25 2.25 0 01.29-.787l.09-.15a2.25 2.25 0 012.37-1.048l1.178.236a1.125 1.125 0 001.302-.795l.208-.73a1.125 1.125 0 00-.578-1.315l-.665-.332-.091.091a2.25 2.25 0 01-1.591.659h-.18a.94.94 0 00-.662.274.931.931 0 01-1.458-1.137l1.411-2.353a2.25 2.25 0 00.286-.76m11.928 9.869A9 9 0 008.965 3.525m11.928 9.868A9 9 0 118.965 3.525" />
      </svg>
      <span>
        <strong>Offline</strong> — viewing cached report from {{ formatCachedDate() }}.
        Data will sync when you reconnect.
      </span>
    </div>

    <!-- Summary Cards -->
    <ReportSummaryCards
      v-if="!generating || sections.length > 0"
      :taskId="taskId"
      :sectionsCount="sections.length"
      class="mb-6"
    />

    <!-- Error State -->
    <div v-if="error" class="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-lg p-4 mb-6 text-sm text-red-700 dark:text-red-400">
      {{ error }}
    </div>

    <!-- ══════ Template Selection Phase ══════ -->
    <div v-if="showTemplateSelector" class="space-y-6">
      <ReportTemplateSelector @select="onTemplateSelect" />

      <div class="flex justify-end">
        <button
          @click="startGeneration"
          :disabled="!selectedTemplate"
          class="bg-[#2068FF] hover:bg-[#1a5ae0] disabled:bg-[var(--color-border)] disabled:cursor-not-allowed text-white px-6 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Generate Report
        </button>
      </div>
    </div>

    <!-- Builder Mode: drag-and-drop section reorder -->
    <ReportCanvas
      v-if="builderMode && sections.length > 1"
      :sections="sections"
      @reorder="handleReorder"
      class="max-w-2xl mx-auto"
    />

    <template v-if="!builderMode">

    <!-- Progress Bar (during generation) -->
    <div v-if="generating && progress > 0" class="mb-6">
      <div class="h-1.5 bg-[var(--color-tint)] rounded-full overflow-hidden">
        <div
          class="h-full bg-[#2068FF] rounded-full transition-all duration-500"
          :style="{ width: `${progress}%` }"
        />
      </div>
      <p class="text-xs text-[var(--color-text-muted)] mt-1 text-right">{{ progress }}%</p>
    </div>

    <!-- Mobile: horizontal tab bar -->
    <div v-if="chapters.length > 0" class="md:hidden mb-4 -mx-4 px-4 overflow-x-auto">
      <div class="flex gap-2 min-w-max">
        <button
          v-for="(chapter, i) in chapters"
          :key="'tab-' + i"
          @click="activeChapter = i"
          class="px-3.5 py-2 rounded-full text-xs font-medium whitespace-nowrap transition-colors"
          :class="activeChapter === i ? 'bg-[#2068FF] text-white' : 'bg-[var(--color-tint)] text-[var(--color-text-secondary)] hover:bg-[var(--color-border)]'"
        >
          {{ chapter.title }}
        </button>
      </div>
    </div>

    <!-- Theme Configurator Panel (collapsible) -->
    <div
      v-if="showThemePanel && !generating"
      class="mb-6 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4"
    >
      <ThemeConfigurator />
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <!-- Chapter Nav Sidebar -->
      <nav class="hidden md:block space-y-1">
        <h3 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3 px-3">Chapters</h3>

        <div v-if="chapters.length === 0 && generating" class="px-3">
          <div class="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
            <svg class="w-4 h-4 animate-spin text-[#2068FF]" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Generating chapters...
          </div>
        </div>

        <button
          v-for="(chapter, i) in chapters"
          :key="'ch-' + i"
          @click="activeChapter = i"
          class="w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors flex items-center gap-2"
          :class="activeChapter === i
            ? 'bg-[#2068FF] text-white'
            : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-tint)]'"
        >
          <!-- Completion indicator -->
          <span class="shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs"
            :class="activeChapter === i
              ? 'bg-white/20 text-white'
              : 'bg-[rgba(32,104,255,0.08)] text-[#2068FF]'"
          >
            <svg v-if="isComplete" class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
            </svg>
            <span v-else>{{ i + 1 }}</span>
          </span>
          <span class="truncate">{{ chapter.title }}</span>
        </button>

        <!-- Pending indicator during generation -->
        <div v-if="generating && chapters.length > 0" class="flex items-center gap-2 px-3 py-2.5 text-sm text-[var(--color-text-muted)]">
          <span class="shrink-0 w-5 h-5 rounded-full flex items-center justify-center bg-[var(--color-tint)]">
            <svg class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </span>
          <span class="italic">Generating next...</span>
        </div>
      </nav>

      <!-- Main Content Area -->
      <div class="md:col-span-3 space-y-6">
        <!-- Chapter Content -->
        <div
          class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 md:p-8"
          :style="themeStyles"
        >
          <!-- Theme Header -->
          <div v-if="resolvedTheme.headerText || resolvedTheme.logo" class="flex items-center gap-3 mb-6 pb-4 border-b" :style="{ borderColor: 'var(--report-primary, var(--color-border))', opacity: 0.6 }">
            <img v-if="resolvedTheme.logo" :src="resolvedTheme.logo" alt="Logo" class="h-6 max-w-[100px] object-contain" @error="$event.target.style.display = 'none'" />
            <span v-if="resolvedTheme.headerText" class="text-xs font-medium" :style="{ color: 'var(--report-primary)', fontFamily: 'var(--report-font-family)' }">{{ resolvedTheme.headerText }}</span>
          </div>

          <!-- Edit controls -->
          <div v-if="activeContent && !generating && editingChapter !== activeChapter" class="flex items-center justify-end gap-2 mb-4">
            <button
              v-if="activeContent.edited"
              @click="revertEdits"
              class="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors flex items-center gap-1"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a5 5 0 015 5v2M3 10l4-4m-4 4l4 4" />
              </svg>
              Revert
            </button>
            <button
              @click="startEditing"
              class="text-xs border border-[var(--color-border)] hover:bg-[var(--color-tint)] text-[var(--color-text-secondary)] px-2.5 py-1 rounded-md transition-colors flex items-center gap-1.5"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              Edit
            </button>
          </div>

          <!-- Loading state with shimmer -->
          <div v-if="generating && !activeContent" class="space-y-6 py-4">
            <ShimmerCard :lines="2" height="48px" />
            <ShimmerCard :lines="5" height="180px" />
            <ShimmerCard :lines="4" height="140px" />
            <ShimmerCard :lines="3" height="100px" />
            <p class="text-center text-xs text-[var(--color-text-secondary)] mt-4">
              Generating predictive report &mdash; multi-chapter analysis with evidence from simulation
            </p>
          </div>

          <!-- Edit mode -->
          <div v-else-if="activeContent && editingChapter === activeChapter" class="space-y-3">
            <RichTextEditor v-model="editBuffer" />
            <div class="flex items-center gap-2 justify-end">
              <button
                @click="cancelEditing"
                class="border border-[var(--color-border)] hover:bg-[var(--color-tint)] text-[var(--color-text-secondary)] px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                @click="saveEditing"
                class="bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
              >
                Save Changes
              </button>
            </div>
          </div>

          <!-- Rendered markdown chapter (view mode) -->
          <div
            v-else-if="activeContent"
            class="report-content group relative"
            v-html="activeContent.html"
          />

          <!-- Empty state -->
          <div v-else class="text-center py-16 text-[var(--color-text-muted)]">
            <p>No report content available.</p>
          </div>

          <!-- Theme Footer -->
          <div v-if="resolvedTheme.footerText" class="mt-6 pt-4 border-t" :style="{ borderColor: 'var(--report-primary, var(--color-border))', opacity: 0.6 }">
            <span class="text-xs" :style="{ color: 'var(--color-text-muted)', fontFamily: 'var(--report-font-family)' }">{{ resolvedTheme.footerText }}</span>
          </div>
        </div>

        <!-- Inline chart for the active chapter -->
        <ReportCharts
          v-if="activeContent && !generating"
          :chapterIndex="activeChapter"
          :offlineCachedAt="servingFromCache ? cachedAt : null"
        />

        <!-- Agent Reasoning Log -->
        <div v-if="reportId">
          <button
            @click="showAgentLog = !showAgentLog"
            class="flex items-center gap-2 text-xs font-medium text-[var(--color-text-muted)] hover:text-[#2068FF] transition-colors mb-3"
          >
            <span class="transition-transform" :class="showAgentLog ? 'rotate-90' : ''">▶</span>
            {{ showAgentLog ? 'Hide' : 'Show' }} Agent Reasoning Log
          </button>
          <ToolCallLog
            v-if="showAgentLog"
            :reportId="reportId"
            :isGenerating="generating"
          />
        </div>

        <!-- Comparative Chart Overlay -->
        <ComparisonOverlay v-if="!generating && sections.length > 0" />

        <!-- Key Findings Summary -->
        <div v-if="keyFindings.length > 0" class="space-y-3">
          <h3 class="text-sm font-semibold text-[var(--color-text)]">Key Findings</h3>
          <div
            v-for="(finding, i) in keyFindings"
            :key="i"
            class="bg-[var(--color-primary-light)] border border-[var(--color-primary-border)] rounded-lg p-4 text-sm text-[var(--color-text)]"
          >
            <div class="flex gap-3">
              <span class="shrink-0 w-5 h-5 rounded-full bg-[#2068FF] text-white flex items-center justify-center text-xs font-semibold mt-0.5">
                {{ i + 1 }}
              </span>
              <span class="finding-text" v-html="marked.parseInline(finding)"></span>
            </div>
          </div>
        </div>

        <!-- Chapter navigation footer -->
        <div v-if="chapters.length > 1 && !generating" class="flex items-center justify-between pt-2">
          <button
            :disabled="activeChapter === 0"
            @click="activeChapter--"
            class="text-sm text-[var(--color-primary)] hover:underline disabled:text-[var(--color-text-muted)] disabled:no-underline transition-colors"
          >
            ← Previous Chapter
          </button>
          <span class="text-xs text-[var(--color-text-muted)]">{{ activeChapter + 1 }} of {{ chapters.length }}</span>
          <button
            :disabled="activeChapter === chapters.length - 1"
            @click="activeChapter++"
            class="text-sm text-[var(--color-primary)] hover:underline disabled:text-[var(--color-text-muted)] disabled:no-underline transition-colors"
          >
            Next Chapter →
          </button>
        </div>

        <!-- Agent Data Table -->
        <DataTable
          v-if="agentTableRows.length > 0 && !generating"
          :columns="agentTableColumns"
          :rows="agentTableRows"
          title="Agent Activity Breakdown"
        />

        <!-- Report Preview & Export -->
        <ReportPreview
          v-if="!generating && sections.length > 0"
          :sections="sections"
          :reportId="reportId"
        />
      </div>
    </div>
    </template>

    <ReportShareModal
      :open="showShareModal"
      :reportId="reportId"
      @close="showShareModal = false"
    />
  </div>
</template>

<style scoped>
.report-content :deep(h1) { font-size: var(--report-heading-size, 1.5rem); font-weight: 600; margin-bottom: 1rem; color: var(--color-text); font-family: var(--report-font-family, inherit); }
.report-content :deep(h2) { font-size: calc(var(--report-heading-size, 1.5rem) - 0.25rem); font-weight: 600; margin-top: 2rem; margin-bottom: 0.75rem; color: var(--color-text); font-family: var(--report-font-family, inherit); }
.report-content :deep(h3) { font-size: calc(var(--report-heading-size, 1.5rem) - 0.375rem); font-weight: 600; margin-top: 1.5rem; margin-bottom: 0.5rem; color: var(--color-text); font-family: var(--report-font-family, inherit); }
.report-content :deep(p) { margin-bottom: 0.75rem; line-height: 1.625; color: var(--color-text-secondary); font-size: var(--report-body-size, 0.875rem); font-family: var(--report-font-family, inherit); }
.report-content :deep(ul),
.report-content :deep(ol) { margin-bottom: 0.75rem; padding-left: 1.5rem; }
.report-content :deep(li) { margin-bottom: 0.25rem; line-height: 1.625; color: var(--color-text-secondary); font-size: var(--report-body-size, 0.875rem); font-family: var(--report-font-family, inherit); }
.report-content :deep(ul) { list-style-type: disc; }
.report-content :deep(ol) { list-style-type: decimal; }
.report-content :deep(strong) { font-weight: 600; color: var(--color-text); }

/* ═══ Blockquotes — agent quotes ═══ */
.report-content :deep(blockquote) {
  border-left: 3px solid var(--report-primary, #2068FF);
  padding: 0.75rem 1rem;
  margin: 1.25rem 0;
  background: rgba(32, 104, 255, 0.03);
  border-radius: 0 0.375rem 0.375rem 0;
  color: var(--color-text-secondary);
  font-style: italic;
  font-family: var(--report-font-family, inherit);
}
.report-content :deep(blockquote p) {
  margin-bottom: 0;
}

/* ═══ Code blocks ═══ */
.report-content :deep(code) {
  background: var(--color-tint);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.8125rem;
}
.report-content :deep(pre) {
  background: #1a1a2e;
  color: #e0e0e0;
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin: 1rem 0;
}
.report-content :deep(pre code) { background: none; padding: 0; }
/* ═══ Tables ═══ */
.report-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1.25rem 0;
  font-size: var(--report-body-size, 0.8125rem);
  font-family: var(--report-font-family, inherit);
  border-radius: 0.5rem;
  overflow: hidden;
}
.report-content :deep(thead) {
  background: rgba(32, 104, 255, 0.04);
}
.report-content :deep(th) {
  text-align: left;
  padding: 0.625rem 0.75rem;
  border-bottom: 2px solid var(--report-primary, var(--color-border-strong));
  font-weight: 600;
  color: var(--color-text);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}
.report-content :deep(td) {
  padding: 0.625rem 0.75rem;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-secondary);
}
.report-content :deep(tr:last-child td) {
  border-bottom: none;
}

/* ═══ Horizontal rules ═══ */
.report-content :deep(hr) { border: none; border-top: 1px solid var(--color-border); margin: 2rem 0; }

/* ═══ Report card print styles ═══ */
.report-card {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

@media print {
  .report-card {
    box-shadow: none;
    border: none;
    padding: 0;
  }
  .report-content :deep(blockquote) {
    border-left-color: #333;
    background: #f9f9f9;
  }
}

/* ═══ Key findings ═══ */
.finding-text :deep(strong) { font-weight: 700; color: var(--color-text); }
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
