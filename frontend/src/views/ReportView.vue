<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'
import { API_BASE } from '../api/client'
import { useReportShortcuts } from '../composables/useReportShortcuts'
import { useToast } from '../composables/useToast'
import PhaseNav from '../components/simulation/PhaseNav.vue'
import ShimmerCard from '../components/ui/ShimmerCard.vue'
import ReportCharts from '../components/report/ReportCharts.vue'

const props = defineProps({ taskId: String })

const reportId = ref(null)
const sections = ref([])
const activeChapter = ref(0)
const generating = ref(true)
const progress = ref(0)
const progressMessage = ref('')
const error = ref(null)
const isComplete = ref(false)

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

async function checkAndLoad() {
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
      } else {
        startPolling()
      }
    } else {
      await startGeneration()
    }
  } catch (e) {
    error.value = 'Failed to check report status'
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
  if (reportId.value) {
    window.open(`${API_BASE}/report/${reportId.value}/download`, '_blank')
  }
}

const toast = useToast()

const { showHelp, shortcuts } = useReportShortcuts({
  onPreview: () => window.print(),
  onExport: () => exportMarkdown(),
  onSaveTemplate: () => toast.info('Save as template — coming soon'),
  onDeleteSection: () => toast.info('Section removal — coming soon'),
  onMoveUp: () => {
    if (activeChapter.value > 0) activeChapter.value--
  },
  onMoveDown: () => {
    if (activeChapter.value < chapters.value.length - 1) activeChapter.value++
  },
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
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
