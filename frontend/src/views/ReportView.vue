<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'
import { API_BASE } from '../api/client'
import { useOnlineStatus } from '../composables/useOnlineStatus'
import { cacheReport, getCachedReport } from '../composables/useReportCache'
import PhaseNav from '../components/simulation/PhaseNav.vue'
import ShimmerCard from '../components/ui/ShimmerCard.vue'
import ReportCharts from '../components/report/ReportCharts.vue'

const props = defineProps({ taskId: String })
const { isOnline } = useOnlineStatus()

const reportId = ref(null)
const sections = ref([])
const activeChapter = ref(0)
const generating = ref(true)
const progress = ref(0)
const progressMessage = ref('')
const error = ref(null)
const isComplete = ref(false)
const servingFromCache = ref(false)
const cachedAt = ref(null)

let pollTimer = null

const chapters = computed(() =>
  sections.value.map((s) => {
    const titleMatch = s.content.match(/^##\s+(.+)/m)
    return {
      title: titleMatch ? titleMatch[1] : `Section ${s.section_index}`,
      html: marked.parse(s.content),
      markdown: s.content,
      index: s.section_index,
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
      await startGeneration()
      return
    }
    const json = await res.json()
    if (json.success && json.data.has_report) {
      reportId.value = json.data.report_id
      if (json.data.report_status === 'completed') {
        await loadSections()
        generating.value = false
        isComplete.value = true
        await saveToCache()
      } else {
        startPolling()
      }
    } else {
      await startGeneration()
    }
  } catch {
    const loaded = await loadFromCache()
    if (!loaded) error.value = 'Failed to check report status'
  }
}

async function startGeneration() {
  try {
    const res = await fetch(`${API_BASE}/report/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ simulation_id: props.taskId }),
    })
    const json = await res.json()
    if (json.success) {
      reportId.value = json.data.report_id
      if (json.data.already_generated) {
        await loadSections()
        generating.value = false
        isComplete.value = true
      } else {
        startPolling()
      }
    } else {
      error.value = json.error || 'Failed to start report generation'
    }
  } catch (e) {
    error.value = 'Failed to start report generation'
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

function exportMarkdown() {
  if (servingFromCache.value || !isOnline.value) {
    const blob = new Blob([fullMarkdown.value], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `report-${props.taskId}.md`
    a.click()
    URL.revokeObjectURL(url)
    return
  }
  if (reportId.value) {
    window.open(`${API_BASE}/report/${reportId.value}/download`, '_blank')
  }
}

function formatCachedDate() {
  if (!cachedAt.value) return ''
  return new Date(cachedAt.value).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
  })
}

watch(isOnline, (online) => {
  if (online && servingFromCache.value) {
    servingFromCache.value = false
    cachedAt.value = null
    checkAndLoad()
  }
})

onMounted(checkAndLoad)
onUnmounted(stopPolling)
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 md:px-6 py-6 md:py-8">
    <PhaseNav :taskId="taskId" activePhase="report" />

    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 md:mb-8">
      <div>
        <h1 class="text-xl md:text-2xl font-semibold text-[var(--color-text)]" style="letter-spacing: -0.64px">
          Predictive Report
        </h1>
        <p v-if="generating" class="text-sm text-[var(--color-text-muted)] mt-1">
          {{ progressMessage || 'Generating multi-chapter analysis...' }}
        </p>
      </div>
      <div class="flex gap-2">
        <button
          v-if="!generating && sections.length > 0"
          @click="exportMarkdown"
          class="border border-[var(--color-border)] hover:bg-[var(--color-tint)] text-[var(--color-text)] px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Export Markdown
        </button>
        <router-link
          :to="`/chat/${taskId}`"
          class="bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors no-underline"
        >
          Ask Follow-Up →
        </router-link>
      </div>
    </div>

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

    <!-- Error State -->
    <div v-if="error" class="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-lg p-4 mb-6 text-sm text-red-700 dark:text-red-400">
      {{ error }}
    </div>

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
          class="px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors"
          :class="activeChapter === i ? 'bg-[#2068FF] text-white' : 'bg-[var(--color-tint)] text-[var(--color-text-secondary)] hover:bg-[var(--color-border)]'"
        >
          {{ chapter.title }}
        </button>
      </div>
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
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 md:p-8">
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

          <!-- Rendered markdown chapter -->
          <div
            v-else-if="activeContent"
            class="report-content"
            v-html="activeContent.html"
          />

          <!-- Empty state -->
          <div v-else class="text-center py-16 text-[var(--color-text-muted)]">
            <p>No report content available.</p>
          </div>
        </div>

        <!-- Inline chart for the active chapter -->
        <ReportCharts
          v-if="activeContent && !generating"
          :chapterIndex="activeChapter"
          :offlineCachedAt="servingFromCache ? cachedAt : null"
        />

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
      </div>
    </div>
  </div>
</template>

<style scoped>
.report-content :deep(h1) { font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; color: var(--color-text); }
.report-content :deep(h2) { font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 0.75rem; color: var(--color-text); }
.report-content :deep(h3) { font-size: 1.125rem; font-weight: 600; margin-top: 1.5rem; margin-bottom: 0.5rem; color: var(--color-text); }
.report-content :deep(p) { margin-bottom: 0.75rem; line-height: 1.625; color: var(--color-text-secondary); font-size: 0.875rem; }
.report-content :deep(ul),
.report-content :deep(ol) { margin-bottom: 0.75rem; padding-left: 1.5rem; }
.report-content :deep(li) { margin-bottom: 0.25rem; line-height: 1.625; color: var(--color-text-secondary); font-size: 0.875rem; }
.report-content :deep(ul) { list-style-type: disc; }
.report-content :deep(ol) { list-style-type: decimal; }
.report-content :deep(strong) { font-weight: 600; color: var(--color-text); }
.report-content :deep(blockquote) {
  border-left: 3px solid var(--color-primary);
  padding-left: 1rem;
  margin: 1rem 0;
  color: var(--color-text-secondary);
  font-style: italic;
}
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
.report-content :deep(table) { width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.875rem; }
.report-content :deep(th) {
  text-align: left;
  padding: 0.5rem;
  border-bottom: 2px solid var(--color-border-strong);
  font-weight: 600;
  color: var(--color-text);
}
.report-content :deep(td) { padding: 0.5rem; border-bottom: 1px solid var(--color-border); color: var(--color-text-secondary); }
.report-content :deep(hr) { border: none; border-top: 1px solid var(--color-border); margin: 1.5rem 0; }
.finding-text :deep(strong) { font-weight: 700; color: var(--color-text); }
</style>
