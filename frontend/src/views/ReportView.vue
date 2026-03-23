<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import ErrorState from '../components/ui/ErrorState.vue'
import EmptyState from '../components/ui/EmptyState.vue'
import LoadingSpinner from '../components/ui/LoadingSpinner.vue'
import { useToast } from '../composables/useToast'
import {
  generateReport,
  getReportGenerateStatus,
  getReportSections,
  pollTask,
} from '../services/api.js'

const props = defineProps({ taskId: String })
const route = useRoute()
const toast = useToast()

const simulationId = ref(route.query.simulationId || props.taskId)
const reportId = ref('')
const chapters = ref([])
const activeChapter = ref(0)
const generating = ref(true)
const progress = ref(0)
const message = ref('Starting report generation...')
const error = ref('')

let cancelled = false
let sectionPoll = null

async function generate() {
  generating.value = true
  error.value = ''
  cancelled = false
  try {
    const genRes = await generateReport({ simulationId: simulationId.value })
    reportId.value = genRes.data.report_id
    const taskId = genRes.data.task_id

    if (genRes.data.already_generated) {
      generating.value = false
      await fetchSections()
      toast.success('Report loaded')
      return
    }

    startSectionPolling()

    await pollTask(
      () => getReportGenerateStatus({ taskId, simulationId: simulationId.value }),
      {
        interval: 3000,
        onProgress(data) {
          if (cancelled) return
          progress.value = data.progress || 0
          message.value = data.message || 'Generating report...'
          if (data.report_id) reportId.value = data.report_id
        },
      },
    )

    generating.value = false
    stopSectionPolling()
    await fetchSections()
    toast.success('Report generation complete')
  } catch (e) {
    if (!cancelled) {
      generating.value = false
      error.value = e.message
      toast.error(`Report generation failed: ${e.message}`)
    }
  }
}

function retry() {
  stopSectionPolling()
  chapters.value = []
  activeChapter.value = 0
  progress.value = 0
  message.value = 'Starting report generation...'
  generate()
}

function startSectionPolling() {
  sectionPoll = setInterval(async () => {
    if (cancelled || !reportId.value) return
    await fetchSections()
  }, 4000)
}

function stopSectionPolling() {
  if (sectionPoll) {
    clearInterval(sectionPoll)
    sectionPoll = null
  }
}

async function fetchSections() {
  if (!reportId.value) return
  try {
    const res = await getReportSections(reportId.value)
    const sections = res.data?.sections || []
    chapters.value = sections.map((s) => ({
      title: extractTitle(s.content),
      content: s.content,
    }))
  } catch (e) {
    console.warn('Failed to fetch sections:', e)
  }
}

function extractTitle(markdown) {
  const match = markdown.match(/^#+\s+(.+)/m)
  return match ? match[1] : 'Untitled Section'
}

onMounted(generate)

onUnmounted(() => {
  cancelled = true
  stopSectionPolling()
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-6 py-8">
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-2xl font-semibold text-[#050505]">Simulation Report</h1>
      <div class="flex gap-2">
        <router-link v-if="!generating && !error"
          :to="{ path: `/chat/${simulationId}`, query: { simulationId } }"
          class="bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors no-underline">
          Ask Follow-Up →
        </router-link>
      </div>
    </div>

    <!-- Error State -->
    <ErrorState
      v-if="error"
      title="Report generation failed"
      :message="error"
      @retry="retry"
    />

    <!-- Loading State (initial) -->
    <template v-else-if="generating && chapters.length === 0">
      <div class="mb-6">
        <div class="bg-black/5 rounded-full h-2 overflow-hidden">
          <div class="bg-[#2068FF] h-full rounded-full transition-all duration-500" :style="{ width: progress + '%' }"></div>
        </div>
        <p class="text-xs text-[#888] mt-1">{{ message }}</p>
      </div>
      <LoadingSpinner label="Generating predictive report..." />
    </template>

    <!-- Report Content -->
    <template v-else>
      <!-- Progress Bar (still generating but chapters are arriving) -->
      <div v-if="generating" class="mb-6">
        <div class="bg-black/5 rounded-full h-2 overflow-hidden">
          <div class="bg-[#2068FF] h-full rounded-full transition-all duration-500" :style="{ width: progress + '%' }"></div>
        </div>
        <p class="text-xs text-[#888] mt-1">{{ message }}</p>
      </div>

      <!-- Empty State -->
      <EmptyState
        v-if="!generating && chapters.length === 0"
        icon="📝"
        title="No report sections"
        description="The report was generated but no sections were produced. Try running the simulation again."
        actionLabel="Back to Simulation"
        :actionTo="`/simulation/${simulationId}`"
      />

      <!-- Chapters -->
      <div v-else class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <!-- Chapter Nav -->
        <div class="space-y-2">
          <button
            v-for="(chapter, i) in chapters"
            :key="i"
            @click="activeChapter = i"
            class="w-full text-left px-3 py-2 rounded-lg text-sm transition-colors"
            :class="activeChapter === i ? 'bg-[#2068FF] text-white' : 'text-[#555] hover:bg-black/5'"
          >
            {{ chapter.title }}
          </button>
        </div>

        <!-- Content -->
        <div class="md:col-span-3 bg-white border border-black/10 rounded-lg p-8">
          <div v-if="chapters[activeChapter]" class="prose prose-sm max-w-none">
            <div class="whitespace-pre-wrap text-sm text-[#333] leading-relaxed">{{ chapters[activeChapter].content }}</div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
