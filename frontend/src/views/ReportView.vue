<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'
import LoadingSpinner from '../components/ui/LoadingSpinner.vue'
import ErrorState from '../components/ui/ErrorState.vue'
import EmptyState from '../components/ui/EmptyState.vue'
import { useToast } from '../composables/useToast'

const props = defineProps({ taskId: String })
const toast = useToast()

const reportId = ref(null)
const sections = ref([])
const activeChapter = ref('summary')
const loading = ref(true)
const generating = ref(false)
const error = ref(null)
const progress = ref(0)
const progressMessage = ref('')
const completedSectionTitles = ref([])
const currentSectionTitle = ref('')
const isComplete = ref(false)
const fullMarkdown = ref('')

let pollTimer = null

// --- Computed ---

const chapters = computed(() => {
  if (sections.value.length > 0) {
    return sections.value.map((s, i) => {
      const match = s.content.match(/^#+\s+(.+)/m)
      return {
        title: match ? match[1].trim() : `Section ${s.section_index || i + 1}`,
        content: s.content,
        html: marked.parse(s.content),
      }
    })
  }
  if (fullMarkdown.value) {
    return fullMarkdown.value
      .split(/(?=^## )/m)
      .filter(s => s.trim())
      .map((part, i) => {
        const match = part.match(/^#+\s+(.+)/m)
        return {
          title: match ? match[1].trim() : `Section ${i + 1}`,
          content: part,
          html: marked.parse(part),
        }
      })
  }
  return []
})

const chapterStatus = computed(() =>
  chapters.value.map(ch => {
    if (isComplete.value) return 'completed'
    if (completedSectionTitles.value.includes(ch.title)) return 'completed'
    if (currentSectionTitle.value === ch.title) return 'generating'
    return 'completed'
  })
)

const keyFindings = computed(() => {
  const findings = []
  const content = sections.value.length > 0
    ? sections.value.map(s => s.content).join('\n')
    : fullMarkdown.value
  if (!content) return findings

  const lines = content.split('\n')
  let inFindings = false
  for (const line of lines) {
    if (/^#+.*(?:key\s*finding|key\s*insight|key\s*takeaway|highlight)/i.test(line)) {
      inFindings = true
      continue
    }
    if (inFindings && /^##/.test(line)) inFindings = false
    if (inFindings && /^[-*]\s+/.test(line)) {
      findings.push(line.replace(/^[-*]\s+/, '').replace(/\*\*/g, '').trim())
    }
  }

  for (const m of content.matchAll(/\*\*(?:Key Finding)[:\s]*\*\*\s*(.+)/gi)) {
    findings.push(m[1].trim())
  }

  if (findings.length === 0) {
    const bullets = content.match(/^[-*]\s+.+/gm)
    if (bullets) {
      bullets.slice(0, 5).forEach(b =>
        findings.push(b.replace(/^[-*]\s+/, '').replace(/\*\*/g, '').trim())
      )
    }
  }

  return [...new Set(findings)].slice(0, 8)
})

const activeContent = computed(() => {
  if (activeChapter.value === 'summary') return null
  return chapters.value[activeChapter.value] || null
})

// --- API ---

async function initReport() {
  loading.value = true
  error.value = null
  try {
    const res = await fetch('/api/report/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ simulation_id: props.taskId }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const json = await res.json()
    if (!json.success) throw new Error(json.error || 'Report generation failed')

    reportId.value = json.data.report_id

    if (json.data.already_generated || json.data.status === 'completed') {
      await fetchReport()
    } else {
      generating.value = true
      loading.value = false
      startPolling()
    }
  } catch (e) {
    error.value = e.message
    loading.value = false
    toast.error('Failed to generate report')
  }
}

async function fetchReport() {
  try {
    const res = await fetch(`/api/report/${reportId.value}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const json = await res.json()
    if (!json.success) throw new Error(json.error)

    fullMarkdown.value = json.data.markdown_content || ''
    isComplete.value = true
    generating.value = false
    await fetchSections()
  } catch (e) {
    error.value = e.message
    toast.error('Failed to fetch report')
  } finally {
    loading.value = false
  }
}

async function fetchSections() {
  if (!reportId.value) return
  try {
    const res = await fetch(`/api/report/${reportId.value}/sections`)
    if (!res.ok) return
    const json = await res.json()
    if (json.success) {
      sections.value = json.data.sections || []
      if (json.data.is_complete) {
        isComplete.value = true
        generating.value = false
        stopPolling()
      }
    }
  } catch { /* non-critical */ }
}

async function fetchProgress() {
  if (!reportId.value) return
  try {
    const res = await fetch(`/api/report/${reportId.value}/progress`)
    if (!res.ok) return
    const json = await res.json()
    if (json.success) {
      progress.value = json.data.progress || 0
      progressMessage.value = json.data.message || ''
      completedSectionTitles.value = json.data.completed_sections || []
      currentSectionTitle.value = json.data.current_section || ''
      if (json.data.status === 'completed') await fetchReport()
    }
  } catch { /* non-critical */ }
}

function startPolling() {
  fetchSections()
  fetchProgress()
  pollTimer = setInterval(() => {
    if (isComplete.value) return stopPolling()
    fetchSections()
    fetchProgress()
  }, 3000)
}

function stopPolling() {
  clearInterval(pollTimer)
  pollTimer = null
}

function exportMarkdown() {
  let content = fullMarkdown.value
  if (!content && sections.value.length > 0) {
    content = sections.value.map(s => s.content).join('\n\n---\n\n')
  }
  if (!content) return toast.error('No content to export')

  const blob = new Blob([content], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `report-${props.taskId}.md`
  a.click()
  URL.revokeObjectURL(url)
  toast.success('Report exported')
}

onMounted(initReport)
onUnmounted(stopPolling)
</script>

<template>
  <div class="max-w-6xl mx-auto px-6 py-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-semibold text-[#050505]" style="letter-spacing: -0.64px">
          Simulation Report
        </h1>
        <p class="text-sm text-[#888] mt-0.5">Task: {{ taskId }}</p>
      </div>
      <div class="flex gap-2">
        <button
          v-if="chapters.length > 0"
          @click="exportMarkdown"
          class="flex items-center gap-2 bg-white border border-black/10 text-[#050505] px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#fafafa] transition-colors"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
          </svg>
          Export .md
        </button>
        <router-link
          :to="`/chat/${taskId}`"
          class="bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors no-underline"
        >
          Ask Follow-Up →
        </router-link>
      </div>
    </div>

    <!-- Loading -->
    <LoadingSpinner v-if="loading" label="Loading report..." />

    <!-- Error -->
    <ErrorState
      v-else-if="error"
      title="Report generation failed"
      :message="error"
      @retry="initReport"
    />

    <!-- Empty State -->
    <EmptyState
      v-else-if="!generating && chapters.length === 0"
      icon="📊"
      title="No report data yet"
      description="Run a simulation first to generate a predictive report with multi-chapter analysis."
      action-label="Go to Scenarios"
      action-to="/"
    />

    <!-- Generating (no sections yet) -->
    <div v-else-if="generating && chapters.length === 0" class="max-w-md mx-auto text-center py-16">
      <LoadingSpinner :label="progressMessage || 'Analyzing simulation data...'" />
      <div class="mt-6">
        <div class="w-full h-2 bg-black/5 rounded-full overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-500 bg-[#2068FF]"
            :style="{ width: `${progress}%` }"
          />
        </div>
        <p class="text-xs text-[#888] mt-2">{{ Math.round(progress) }}% complete</p>
      </div>
    </div>

    <!-- Report Content -->
    <div v-else class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <!-- Sidebar: Chapter Navigation -->
      <nav class="space-y-1">
        <!-- Summary -->
        <button
          @click="activeChapter = 'summary'"
          class="w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-2.5"
          :class="activeChapter === 'summary'
            ? 'bg-[#2068FF] text-white'
            : 'text-[#555] hover:bg-[rgba(32,104,255,0.06)]'"
        >
          <span
            class="w-5 h-5 rounded-full flex items-center justify-center shrink-0 text-xs"
            :class="activeChapter === 'summary' ? 'bg-white/20 text-white' : 'bg-[rgba(32,104,255,0.08)] text-[#2068FF]'"
          >★</span>
          Summary
        </button>

        <div class="h-px bg-black/10 my-2" />

        <!-- Chapter Items -->
        <button
          v-for="(chapter, i) in chapters"
          :key="i"
          @click="activeChapter = i"
          class="w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors flex items-center gap-2.5"
          :class="activeChapter === i
            ? 'bg-[#2068FF] text-white font-medium'
            : 'text-[#555] hover:bg-[rgba(32,104,255,0.06)]'"
        >
          <!-- Completion indicator -->
          <span
            class="w-5 h-5 rounded-full flex items-center justify-center shrink-0"
            :class="activeChapter === i ? 'bg-white/20' : {
              'bg-[rgba(0,153,0,0.1)]': chapterStatus[i] === 'completed',
              'bg-[rgba(32,104,255,0.1)]': chapterStatus[i] === 'generating',
              'bg-black/5': chapterStatus[i] === 'pending',
            }"
          >
            <svg
              v-if="chapterStatus[i] === 'completed'"
              class="w-3 h-3"
              :class="activeChapter === i ? 'text-white' : 'text-[#009900]'"
              fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
            </svg>
            <span
              v-else-if="chapterStatus[i] === 'generating'"
              class="w-2 h-2 rounded-full animate-pulse"
              :class="activeChapter === i ? 'bg-white' : 'bg-[#2068FF]'"
            />
            <span
              v-else
              class="w-2 h-2 rounded-full"
              :class="activeChapter === i ? 'bg-white/40' : 'bg-black/20'"
            />
          </span>
          <span class="truncate">{{ chapter.title }}</span>
        </button>

        <!-- Progress during generation -->
        <div v-if="generating" class="mt-4 px-3">
          <div class="w-full h-1.5 bg-black/5 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500 bg-[#2068FF]"
              :style="{ width: `${progress}%` }"
            />
          </div>
          <p class="text-xs text-[#888] mt-1">{{ Math.round(progress) }}% complete</p>
        </div>
      </nav>

      <!-- Main Content Area -->
      <div class="md:col-span-3">
        <!-- Summary View -->
        <div v-if="activeChapter === 'summary'" class="bg-white border border-black/10 rounded-lg p-8">
          <h2 class="text-lg font-semibold text-[#050505] mb-6">Key Findings</h2>

          <div v-if="keyFindings.length > 0" class="space-y-3">
            <div
              v-for="(finding, i) in keyFindings"
              :key="i"
              class="flex gap-3 p-4 rounded-lg bg-[rgba(32,104,255,0.06)] border-l-4 border-[#2068FF]"
            >
              <span class="shrink-0 w-6 h-6 rounded-full bg-[#2068FF] text-white flex items-center justify-center text-xs font-semibold">
                {{ i + 1 }}
              </span>
              <p class="text-sm text-[#050505] leading-relaxed">{{ finding }}</p>
            </div>
          </div>

          <p v-else class="text-sm text-[#888] text-center py-8">
            {{ generating ? 'Key findings will appear as chapters are generated...' : 'No key findings identified in this report.' }}
          </p>

          <!-- Report stats -->
          <div v-if="chapters.length > 0" class="mt-8 pt-6 border-t border-black/10 grid grid-cols-3 gap-4 text-center">
            <div>
              <div class="text-2xl font-semibold text-[#2068FF]">{{ chapters.length }}</div>
              <div class="text-xs text-[#888] mt-0.5">Chapters</div>
            </div>
            <div>
              <div class="text-2xl font-semibold text-[#2068FF]">{{ keyFindings.length }}</div>
              <div class="text-xs text-[#888] mt-0.5">Key Findings</div>
            </div>
            <div>
              <div class="text-2xl font-semibold text-[#2068FF]">
                {{ isComplete ? '✓' : `${Math.round(progress)}%` }}
              </div>
              <div class="text-xs text-[#888] mt-0.5">
                {{ isComplete ? 'Complete' : 'Progress' }}
              </div>
            </div>
          </div>
        </div>

        <!-- Chapter Content -->
        <div v-else-if="activeContent" class="bg-white border border-black/10 rounded-lg p-8">
          <div class="report-content" v-html="activeContent.html" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.report-content :deep(h1) { font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; color: #050505; }
.report-content :deep(h2) { font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 0.75rem; color: #050505; }
.report-content :deep(h3) { font-size: 1.125rem; font-weight: 600; margin-top: 1.5rem; margin-bottom: 0.5rem; color: #050505; }
.report-content :deep(p) { margin-bottom: 0.75rem; line-height: 1.625; color: #333; font-size: 0.875rem; }
.report-content :deep(ul),
.report-content :deep(ol) { margin-bottom: 0.75rem; padding-left: 1.5rem; }
.report-content :deep(li) { margin-bottom: 0.25rem; line-height: 1.625; color: #333; font-size: 0.875rem; }
.report-content :deep(ul) { list-style-type: disc; }
.report-content :deep(ol) { list-style-type: decimal; }
.report-content :deep(strong) { font-weight: 600; color: #050505; }
.report-content :deep(blockquote) {
  border-left: 3px solid #2068FF;
  padding-left: 1rem;
  margin: 1rem 0;
  color: #555;
  font-style: italic;
}
.report-content :deep(code) {
  background: rgba(0, 0, 0, 0.05);
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
  border-bottom: 2px solid rgba(0, 0, 0, 0.1);
  font-weight: 600;
  color: #050505;
}
.report-content :deep(td) { padding: 0.5rem; border-bottom: 1px solid rgba(0, 0, 0, 0.05); color: #333; }
.report-content :deep(hr) { border: none; border-top: 1px solid rgba(0, 0, 0, 0.1); margin: 1.5rem 0; }
</style>
