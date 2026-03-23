<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import {
  generateReport,
  getReportGenerateStatus,
  getReportSections,
  pollTask,
} from '../services/api.js'

const props = defineProps({ taskId: String })
const route = useRoute()

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

onMounted(async () => {
  try {
    // Trigger report generation
    const genRes = await generateReport({ simulationId: simulationId.value })
    reportId.value = genRes.data.report_id
    const taskId = genRes.data.task_id

    // If report was already generated, skip polling
    if (genRes.data.already_generated) {
      generating.value = false
      await fetchSections()
      return
    }

    // Start polling for sections immediately (they arrive incrementally)
    startSectionPolling()

    // Poll task status until complete
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
  } catch (e) {
    if (!cancelled) {
      generating.value = false
      error.value = e.message
    }
  }
})

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

onUnmounted(() => {
  cancelled = true
  stopSectionPolling()
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 md:px-6 py-6 md:py-8">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 md:mb-8">
      <h1 class="text-xl md:text-2xl font-semibold text-[#050505]">Simulation Report</h1>
      <div class="flex gap-2">
        <router-link v-if="!generating"
          :to="{ path: `/chat/${simulationId}`, query: { simulationId } }"
          class="bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors no-underline">
          Ask Follow-Up →
        </router-link>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="mb-6 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-4">
      {{ error }}
    </div>

    <!-- Progress Bar -->
    <div v-if="generating" class="mb-6">
      <div class="bg-black/5 rounded-full h-2 overflow-hidden">
        <div class="bg-[#2068FF] h-full rounded-full transition-all duration-500" :style="{ width: progress + '%' }"></div>
      </div>
      <p class="text-xs text-[#888] mt-1">{{ message }}</p>
    </div>

    <!-- Mobile: horizontal tab bar -->
    <div v-if="chapters.length > 0" class="md:hidden overflow-x-auto mb-4 -mx-4 px-4">
      <div class="flex gap-2 min-w-max">
        <button
          v-for="(chapter, i) in chapters"
          :key="i"
          @click="activeChapter = i"
          class="px-3 py-1.5 rounded-full text-sm whitespace-nowrap transition-colors"
          :class="activeChapter === i ? 'bg-[#2068FF] text-white' : 'bg-black/5 text-[#555] hover:bg-black/10'"
        >
          {{ chapter.title }}
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <!-- Desktop: Chapter Nav sidebar -->
      <div class="hidden md:block space-y-2">
        <div v-if="chapters.length === 0" class="text-sm text-[#888]">
          {{ generating ? 'Generating report...' : 'No chapters yet' }}
        </div>
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
      <div class="md:col-span-3 bg-white border border-black/10 rounded-lg p-4 md:p-8">
        <div v-if="generating && chapters.length === 0" class="text-center py-12 md:py-16">
          <div class="text-4xl mb-4">📝</div>
          <p class="text-[#888]">Generating predictive report...</p>
          <p class="text-xs text-[#aaa] mt-2">Multi-chapter analysis with evidence from simulation</p>
        </div>
        <div v-else-if="chapters[activeChapter]" class="prose prose-sm max-w-none">
          <div class="whitespace-pre-wrap text-sm text-[#333] leading-relaxed">{{ chapters[activeChapter].content }}</div>
        </div>
        <!-- Mobile: empty state when no chapters -->
        <div v-if="!generating && chapters.length === 0" class="md:hidden text-sm text-[#888] text-center py-8">
          No chapters yet
        </div>
      </div>
    </div>
  </div>
</template>
