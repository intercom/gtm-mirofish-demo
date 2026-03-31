<script setup>
import { ref, computed, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import { useSimulationStore } from '../../stores/simulation'
import { useToast } from '../../composables/useToast'
import { API_BASE } from '../../api/client'
import { AppButton } from '../common'
import ShimmerCard from '../ui/ShimmerCard.vue'

const router = useRouter()
const simStore = useSimulationStore()
const toast = useToast()

const PREFS_KEY = 'mirofish_report_wizard_prefs'

// ── Wizard state ──────────────────────────────
const currentStep = ref(0)
const steps = ['Select Simulation', 'Report Type', 'Customize', 'Generate', 'Review']

// Step 1: Simulation selection
const selectedSimulation = ref(null)

// Step 2: Report type
const reportTypes = [
  {
    id: 'comprehensive',
    label: 'Comprehensive Analysis',
    description: 'Full multi-chapter report with engagement metrics, sentiment analysis, competitive insights, and strategic recommendations.',
    icon: 'document',
  },
  {
    id: 'executive',
    label: 'Executive Summary',
    description: 'Concise overview focused on key findings, decision signals, and actionable next steps for leadership.',
    icon: 'briefcase',
  },
  {
    id: 'competitive',
    label: 'Competitive Intelligence',
    description: 'Deep dive into competitor mentions, positioning dynamics, and market perception across simulated agents.',
    icon: 'chart',
  },
]
const selectedReportType = ref('comprehensive')

// Step 3: Customization
const customPrompt = ref('')
const includeSections = ref({
  engagement: true,
  sentiment: true,
  competitive: true,
  recommendations: true,
  agentProfiles: true,
})
const chartPreference = ref('all')
const chartOptions = [
  { value: 'all', label: 'All charts' },
  { value: 'essential', label: 'Essential only' },
  { value: 'none', label: 'No charts' },
]

// Step 4: Generation
const reportId = ref(null)
const generating = ref(false)
const progress = ref(0)
const progressMessage = ref('')
const generationError = ref(null)

// Step 5: Review
const sections = ref([])
const isComplete = ref(false)
const activeChapter = ref(0)

let pollTimer = null

// ── Load saved preferences ────────────────────
function loadPrefs() {
  try {
    const raw = localStorage.getItem(PREFS_KEY)
    if (!raw) return
    const prefs = JSON.parse(raw)
    if (prefs.reportType) selectedReportType.value = prefs.reportType
    if (prefs.includeSections) includeSections.value = { ...includeSections.value, ...prefs.includeSections }
    if (prefs.chartPreference) chartPreference.value = prefs.chartPreference
  } catch { /* ignore */ }
}
loadPrefs()

function savePrefs() {
  try {
    localStorage.setItem(PREFS_KEY, JSON.stringify({
      reportType: selectedReportType.value,
      includeSections: includeSections.value,
      chartPreference: chartPreference.value,
    }))
  } catch { /* ignore */ }
}

// ── Computed ──────────────────────────────────
const completedRuns = computed(() =>
  simStore.sessionRuns
    .filter(r => {
      const s = (r.status || '').toLowerCase()
      return s === 'completed' || s === 'complete'
    })
    .sort((a, b) => b.timestamp - a.timestamp)
)

const selectedRunDetails = computed(() =>
  completedRuns.value.find(r => r.id === selectedSimulation.value)
)

const canGoNext = computed(() => {
  if (currentStep.value === 0) return !!selectedSimulation.value
  if (currentStep.value === 1) return !!selectedReportType.value
  if (currentStep.value === 2) return true
  return false
})

const chapters = computed(() =>
  sections.value.map((s) => {
    const titleMatch = s.content.match(/^##\s+(.+)/m)
    return {
      title: titleMatch ? titleMatch[1] : `Section ${s.section_index}`,
      html: marked.parse(s.content),
      index: s.section_index,
    }
  })
)

const activeContent = computed(() => chapters.value[activeChapter.value] || null)

// ── Navigation ────────────────────────────────
function nextStep() {
  if (currentStep.value === 2) {
    savePrefs()
    currentStep.value = 3
    startGeneration()
    return
  }
  if (currentStep.value < steps.length - 1 && canGoNext.value) {
    currentStep.value++
  }
}

function prevStep() {
  if (currentStep.value > 0 && currentStep.value !== 3 && currentStep.value !== 4) {
    currentStep.value--
  }
}

function goToStep(step) {
  if (step < currentStep.value && step < 3) {
    currentStep.value = step
  }
}

// ── Generation ────────────────────────────────
async function startGeneration() {
  generating.value = true
  generationError.value = null
  progress.value = 0
  progressMessage.value = 'Starting report generation...'
  sections.value = []

  try {
    const body = {
      simulation_id: selectedSimulation.value,
      report_type: selectedReportType.value,
      custom_prompt: customPrompt.value || undefined,
      include_sections: Object.entries(includeSections.value)
        .filter(([, v]) => v)
        .map(([k]) => k),
      chart_preference: chartPreference.value,
    }

    const res = await fetch(`${API_BASE}/report/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const json = await res.json()

    if (json.success) {
      reportId.value = json.data.report_id
      if (json.data.already_generated) {
        await loadSections()
        generating.value = false
        isComplete.value = true
        currentStep.value = 4
      } else {
        startPolling()
      }
    } else {
      generationError.value = json.error || 'Failed to start report generation'
      generating.value = false
    }
  } catch {
    generationError.value = 'Failed to connect to the server'
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
    }
  } catch { /* retry on next poll */ }
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
        if (json.data.status === 'failed') {
          generationError.value = json.data.message || 'Report generation failed'
          generating.value = false
          stopPolling()
          return
        }
      }
    }
  } catch { /* continue polling */ }

  await loadSections()
  if (isComplete.value) {
    generating.value = false
    stopPolling()
    currentStep.value = 4
    toast.success('Report generated successfully')
  }
}

function startPolling() {
  pollTimer = setInterval(pollProgress, 3000)
  pollProgress()
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function retryGeneration() {
  generationError.value = null
  startGeneration()
}

// ── Review actions ────────────────────────────
function viewFullReport() {
  if (selectedSimulation.value) {
    router.push(`/report/${selectedSimulation.value}`)
  }
}

function exportMarkdown() {
  if (reportId.value) {
    window.open(`${API_BASE}/report/${reportId.value}/download`, '_blank')
  }
}

function startNewReport() {
  stopPolling()
  currentStep.value = 0
  selectedSimulation.value = null
  reportId.value = null
  generating.value = false
  progress.value = 0
  progressMessage.value = ''
  generationError.value = null
  sections.value = []
  isComplete.value = false
  activeChapter.value = 0
}

// ── Helpers ───────────────────────────────────
function relativeTime(ts) {
  const diff = Math.floor((Date.now() - ts) / 1000)
  if (diff < 60) return 'just now'
  if (diff < 3600) {
    const m = Math.floor(diff / 60)
    return `${m} min${m === 1 ? '' : 's'} ago`
  }
  if (diff < 86400) {
    const h = Math.floor(diff / 3600)
    return `${h} hour${h === 1 ? '' : 's'} ago`
  }
  const d = Math.floor(diff / 86400)
  return `${d} day${d === 1 ? '' : 's'} ago`
}

// ── Cleanup ───────────────────────────────────
onUnmounted(stopPolling)

// Reset review state when stepping back from generation
watch(currentStep, (step) => {
  if (step < 3) {
    stopPolling()
    generating.value = false
  }
})
</script>

<template>
  <div class="max-w-3xl mx-auto">
    <!-- Stepper -->
    <nav class="mb-8">
      <ol class="flex items-center gap-1">
        <li
          v-for="(step, i) in steps"
          :key="i"
          class="flex items-center"
          :class="i < steps.length - 1 ? 'flex-1' : ''"
        >
          <button
            @click="goToStep(i)"
            :disabled="i >= currentStep"
            class="flex items-center gap-2 shrink-0 transition-colors"
            :class="[
              i < currentStep
                ? 'cursor-pointer'
                : i === currentStep
                  ? 'cursor-default'
                  : 'cursor-not-allowed',
            ]"
          >
            <span
              class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 transition-colors"
              :class="[
                i < currentStep
                  ? 'bg-[#2068FF] text-white'
                  : i === currentStep
                    ? 'bg-[#2068FF] text-white ring-2 ring-[#2068FF]/30'
                    : 'bg-[var(--color-tint)] text-[var(--color-text-muted)]',
              ]"
            >
              <svg v-if="i < currentStep" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
              </svg>
              <span v-else>{{ i + 1 }}</span>
            </span>
            <span
              class="text-xs font-medium hidden sm:inline whitespace-nowrap"
              :class="i <= currentStep ? 'text-[var(--color-text)]' : 'text-[var(--color-text-muted)]'"
            >
              {{ step }}
            </span>
          </button>
          <div
            v-if="i < steps.length - 1"
            class="flex-1 h-px mx-2"
            :class="i < currentStep ? 'bg-[#2068FF]' : 'bg-[var(--color-border)]'"
          />
        </li>
      </ol>
    </nav>

    <!-- ═══════════════════════════════════════ -->
    <!-- Step 1: Select Simulation              -->
    <!-- ═══════════════════════════════════════ -->
    <div v-if="currentStep === 0">
      <h2 class="text-lg font-semibold text-[var(--color-text)] mb-1">Select a Simulation</h2>
      <p class="text-sm text-[var(--color-text-muted)] mb-5">Choose a completed simulation to generate a report from.</p>

      <div v-if="completedRuns.length === 0" class="text-center py-12">
        <div class="w-14 h-14 rounded-full bg-[rgba(32,104,255,0.08)] flex items-center justify-center mx-auto mb-4">
          <svg class="w-6 h-6 text-[#2068FF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5" />
          </svg>
        </div>
        <p class="text-sm text-[var(--color-text-secondary)] mb-4">No completed simulations found.</p>
        <router-link
          to="/"
          class="text-sm text-[#2068FF] hover:underline no-underline"
        >
          Run a simulation first
        </router-link>
      </div>

      <div v-else class="space-y-2">
        <button
          v-for="run in completedRuns"
          :key="run.id"
          @click="selectedSimulation = run.id"
          class="w-full text-left px-4 py-3.5 rounded-lg border transition-all"
          :class="selectedSimulation === run.id
            ? 'border-[#2068FF] bg-[rgba(32,104,255,0.04)] ring-1 ring-[#2068FF]/20'
            : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-border-strong)]'"
        >
          <div class="flex items-center justify-between">
            <div class="min-w-0">
              <div class="text-sm font-medium text-[var(--color-text)] truncate">{{ run.scenarioName }}</div>
              <div class="text-xs text-[var(--color-text-muted)] mt-0.5">
                {{ run.totalActions }} actions · {{ run.totalRounds }} rounds · {{ relativeTime(run.timestamp) }}
              </div>
            </div>
            <div
              class="w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 ml-3 transition-colors"
              :class="selectedSimulation === run.id
                ? 'border-[#2068FF] bg-[#2068FF]'
                : 'border-[var(--color-border)]'"
            >
              <svg v-if="selectedSimulation === run.id" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>
        </button>
      </div>
    </div>

    <!-- ═══════════════════════════════════════ -->
    <!-- Step 2: Report Type                    -->
    <!-- ═══════════════════════════════════════ -->
    <div v-if="currentStep === 1">
      <h2 class="text-lg font-semibold text-[var(--color-text)] mb-1">Choose Report Type</h2>
      <p class="text-sm text-[var(--color-text-muted)] mb-5">Select the type of analysis you'd like to generate.</p>

      <div class="grid gap-3">
        <button
          v-for="rt in reportTypes"
          :key="rt.id"
          @click="selectedReportType = rt.id"
          class="text-left px-5 py-4 rounded-lg border transition-all"
          :class="selectedReportType === rt.id
            ? 'border-[#2068FF] bg-[rgba(32,104,255,0.04)] ring-1 ring-[#2068FF]/20'
            : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-border-strong)]'"
        >
          <div class="flex items-start gap-3.5">
            <!-- Icon -->
            <div
              class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
              :class="selectedReportType === rt.id
                ? 'bg-[#2068FF] text-white'
                : 'bg-[var(--color-tint)] text-[var(--color-text-muted)]'"
            >
              <svg v-if="rt.icon === 'document'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
              </svg>
              <svg v-else-if="rt.icon === 'briefcase'" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 0 0 .75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 0 0-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0 1 12 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 0 1-.673-.38m0 0A2.18 2.18 0 0 1 3 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 0 1 3.413-.387m7.5 0V5.25A2.25 2.25 0 0 0 13.5 3h-3a2.25 2.25 0 0 0-2.25 2.25v.894m7.5 0a48.667 48.667 0 0 0-7.5 0M12 12.75h.008v.008H12v-.008Z" />
              </svg>
              <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
              </svg>
            </div>
            <div class="min-w-0">
              <div class="text-sm font-semibold text-[var(--color-text)]">{{ rt.label }}</div>
              <div class="text-xs text-[var(--color-text-secondary)] mt-1 leading-relaxed">{{ rt.description }}</div>
            </div>
          </div>
        </button>
      </div>
    </div>

    <!-- ═══════════════════════════════════════ -->
    <!-- Step 3: Customize                      -->
    <!-- ═══════════════════════════════════════ -->
    <div v-if="currentStep === 2">
      <h2 class="text-lg font-semibold text-[var(--color-text)] mb-1">Customize Report</h2>
      <p class="text-sm text-[var(--color-text-muted)] mb-5">Fine-tune what your report includes. All fields are optional.</p>

      <div class="space-y-6">
        <!-- Custom prompt -->
        <div>
          <label class="block text-sm font-medium text-[var(--color-text)] mb-1.5">Custom Instructions</label>
          <textarea
            v-model="customPrompt"
            rows="3"
            placeholder="e.g., Focus on enterprise buyers, emphasize ROI metrics, compare against Zendesk..."
            class="w-full px-3 py-2.5 text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:ring-2 focus:ring-[#2068FF] focus:border-transparent resize-none"
          />
        </div>

        <!-- Sections to include -->
        <div>
          <label class="block text-sm font-medium text-[var(--color-text)] mb-2">Sections to Include</label>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <label
              v-for="(checked, key) in includeSections"
              :key="key"
              class="flex items-center gap-2.5 px-3 py-2.5 rounded-lg border cursor-pointer transition-colors"
              :class="includeSections[key]
                ? 'border-[#2068FF]/30 bg-[rgba(32,104,255,0.04)]'
                : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:bg-[var(--color-tint)]'"
            >
              <input
                type="checkbox"
                v-model="includeSections[key]"
                class="w-4 h-4 rounded border-[var(--color-border)] text-[#2068FF] focus:ring-[#2068FF] accent-[#2068FF]"
              />
              <span class="text-sm text-[var(--color-text)]">
                {{ { engagement: 'Engagement Analysis', sentiment: 'Sentiment Tracking', competitive: 'Competitive Intelligence', recommendations: 'Recommendations', agentProfiles: 'Agent Profiles' }[key] }}
              </span>
            </label>
          </div>
        </div>

        <!-- Chart preference -->
        <div>
          <label class="block text-sm font-medium text-[var(--color-text)] mb-2">Chart Preference</label>
          <div class="flex gap-2">
            <button
              v-for="opt in chartOptions"
              :key="opt.value"
              @click="chartPreference = opt.value"
              class="flex-1 px-3 py-2 rounded-lg border text-sm font-medium transition-colors"
              :class="chartPreference === opt.value
                ? 'border-[#2068FF] bg-[rgba(32,104,255,0.04)] text-[#2068FF] ring-1 ring-[#2068FF]/20'
                : 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-secondary)] hover:border-[var(--color-border-strong)]'"
            >
              {{ opt.label }}
            </button>
          </div>
        </div>

        <!-- Summary of selections -->
        <div class="bg-[var(--color-tint)] rounded-lg p-4">
          <div class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Summary</div>
          <div class="text-sm text-[var(--color-text-secondary)] space-y-1">
            <div><span class="font-medium text-[var(--color-text)]">Simulation:</span> {{ selectedRunDetails?.scenarioName }}</div>
            <div><span class="font-medium text-[var(--color-text)]">Report type:</span> {{ reportTypes.find(t => t.id === selectedReportType)?.label }}</div>
            <div><span class="font-medium text-[var(--color-text)]">Sections:</span> {{ Object.entries(includeSections).filter(([,v]) => v).length }} selected</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════ -->
    <!-- Step 4: Generate                       -->
    <!-- ═══════════════════════════════════════ -->
    <div v-if="currentStep === 3">
      <h2 class="text-lg font-semibold text-[var(--color-text)] mb-1">Generating Report</h2>
      <p class="text-sm text-[var(--color-text-muted)] mb-6">
        {{ progressMessage || 'Starting multi-chapter analysis with evidence from simulation...' }}
      </p>

      <!-- Error state -->
      <div v-if="generationError" class="space-y-4">
        <div class="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-lg p-4 text-sm text-red-700 dark:text-red-400">
          {{ generationError }}
        </div>
        <div class="flex gap-2">
          <AppButton variant="secondary" @click="currentStep = 0">Start Over</AppButton>
          <AppButton @click="retryGeneration">Retry</AppButton>
        </div>
      </div>

      <!-- Progress state -->
      <div v-else class="space-y-6">
        <!-- Progress bar -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium text-[var(--color-text)]">
              {{ progress < 10 ? 'Planning outline...' : progress < 90 ? 'Writing sections...' : 'Finalizing...' }}
            </span>
            <span class="text-sm font-semibold text-[#2068FF]">{{ Math.round(progress) }}%</span>
          </div>
          <div class="h-2 bg-[var(--color-tint)] rounded-full overflow-hidden">
            <div
              class="h-full bg-gradient-to-r from-[#2068FF] to-[#2068FF]/70 rounded-full transition-all duration-700 ease-out"
              :style="{ width: `${progress}%` }"
            />
          </div>
        </div>

        <!-- Live sections preview -->
        <div v-if="sections.length > 0" class="space-y-2">
          <div class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">
            Sections generated ({{ sections.length }})
          </div>
          <div
            v-for="(section, i) in sections"
            :key="i"
            class="flex items-center gap-2.5 px-3 py-2.5 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)]"
          >
            <svg class="w-4 h-4 text-emerald-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span class="text-sm text-[var(--color-text)]">
              {{ section.content.match(/^##\s+(.+)/m)?.[1] || `Section ${i + 1}` }}
            </span>
          </div>
          <div v-if="generating" class="flex items-center gap-2.5 px-3 py-2.5 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] border-dashed">
            <svg class="w-4 h-4 animate-spin text-[#2068FF] shrink-0" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span class="text-sm text-[var(--color-text-muted)] italic">Writing next section...</span>
          </div>
        </div>

        <!-- Shimmer loading -->
        <div v-if="sections.length === 0 && generating" class="space-y-4">
          <ShimmerCard :lines="2" height="40px" />
          <ShimmerCard :lines="3" height="60px" />
          <ShimmerCard :lines="2" height="40px" />
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════ -->
    <!-- Step 5: Review                         -->
    <!-- ═══════════════════════════════════════ -->
    <div v-if="currentStep === 4">
      <div class="flex items-center justify-between mb-5">
        <div>
          <h2 class="text-lg font-semibold text-[var(--color-text)]">Report Ready</h2>
          <p class="text-sm text-[var(--color-text-muted)]">{{ chapters.length }} chapters generated for {{ selectedRunDetails?.scenarioName }}</p>
        </div>
        <div class="flex gap-2">
          <AppButton variant="ghost" size="sm" @click="exportMarkdown">
            <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Export
          </AppButton>
          <AppButton size="sm" @click="viewFullReport">
            View Full Report
          </AppButton>
        </div>
      </div>

      <!-- Chapter tabs -->
      <div class="flex gap-1.5 mb-4 overflow-x-auto -mx-1 px-1 pb-1">
        <button
          v-for="(chapter, i) in chapters"
          :key="i"
          @click="activeChapter = i"
          class="px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors shrink-0"
          :class="activeChapter === i
            ? 'bg-[#2068FF] text-white'
            : 'bg-[var(--color-tint)] text-[var(--color-text-secondary)] hover:bg-[var(--color-border)]'"
        >
          {{ chapter.title }}
        </button>
      </div>

      <!-- Chapter content -->
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5 md:p-6">
        <div
          v-if="activeContent"
          class="report-content prose-sm"
          v-html="activeContent.html"
        />
        <div v-else class="text-center py-8 text-sm text-[var(--color-text-muted)]">
          No content available.
        </div>
      </div>

      <!-- Chapter nav -->
      <div v-if="chapters.length > 1" class="flex items-center justify-between mt-4">
        <button
          :disabled="activeChapter === 0"
          @click="activeChapter--"
          class="text-sm text-[#2068FF] hover:underline disabled:text-[var(--color-text-muted)] disabled:no-underline"
        >
          &larr; Previous
        </button>
        <span class="text-xs text-[var(--color-text-muted)]">{{ activeChapter + 1 }} / {{ chapters.length }}</span>
        <button
          :disabled="activeChapter === chapters.length - 1"
          @click="activeChapter++"
          class="text-sm text-[#2068FF] hover:underline disabled:text-[var(--color-text-muted)] disabled:no-underline"
        >
          Next &rarr;
        </button>
      </div>

      <!-- New report -->
      <div class="mt-6 pt-4 border-t border-[var(--color-border)]">
        <button
          @click="startNewReport"
          class="text-sm text-[var(--color-text-muted)] hover:text-[#2068FF] transition-colors flex items-center gap-1.5"
        >
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Generate another report
        </button>
      </div>
    </div>

    <!-- ═══════════════════════════════════════ -->
    <!-- Footer Navigation                      -->
    <!-- ═══════════════════════════════════════ -->
    <div
      v-if="currentStep < 3"
      class="flex items-center justify-between mt-8 pt-5 border-t border-[var(--color-border)]"
    >
      <AppButton
        v-if="currentStep > 0"
        variant="ghost"
        @click="prevStep"
      >
        &larr; Back
      </AppButton>
      <div v-else />
      <AppButton
        :disabled="!canGoNext"
        @click="nextStep"
      >
        {{ currentStep === 2 ? 'Generate Report' : 'Continue' }} &rarr;
      </AppButton>
    </div>
  </div>
</template>

<style scoped>
.report-content :deep(h1) { font-size: 1.375rem; font-weight: 600; margin-bottom: 0.75rem; color: var(--color-text); }
.report-content :deep(h2) { font-size: 1.125rem; font-weight: 600; margin-top: 1.5rem; margin-bottom: 0.5rem; color: var(--color-text); }
.report-content :deep(h3) { font-size: 1rem; font-weight: 600; margin-top: 1rem; margin-bottom: 0.375rem; color: var(--color-text); }
.report-content :deep(p) { margin-bottom: 0.625rem; line-height: 1.6; color: var(--color-text-secondary); font-size: 0.8125rem; }
.report-content :deep(ul),
.report-content :deep(ol) { margin-bottom: 0.625rem; padding-left: 1.25rem; }
.report-content :deep(li) { margin-bottom: 0.2rem; line-height: 1.6; color: var(--color-text-secondary); font-size: 0.8125rem; }
.report-content :deep(ul) { list-style-type: disc; }
.report-content :deep(ol) { list-style-type: decimal; }
.report-content :deep(strong) { font-weight: 600; color: var(--color-text); }
.report-content :deep(blockquote) {
  border-left: 3px solid var(--color-primary);
  padding-left: 0.75rem;
  margin: 0.75rem 0;
  color: var(--color-text-secondary);
  font-style: italic;
}
.report-content :deep(table) { width: 100%; border-collapse: collapse; margin: 0.75rem 0; font-size: 0.8125rem; }
.report-content :deep(th) { text-align: left; padding: 0.375rem 0.5rem; border-bottom: 2px solid var(--color-border-strong); font-weight: 600; color: var(--color-text); }
.report-content :deep(td) { padding: 0.375rem 0.5rem; border-bottom: 1px solid var(--color-border); color: var(--color-text-secondary); }
</style>
