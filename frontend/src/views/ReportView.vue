<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import {
  generateReport,
  getReportGenerateStatus,
  getReport,
  getReportSections,
  poll,
} from '../api.js'

const props = defineProps({ simulationId: String })

const chapters = ref([])
const activeChapter = ref(0)
const generating = ref(true)
const progress = ref(0)
const progressMessage = ref('Starting report generation...')
const reportId = ref(null)
const error = ref(null)

let statusPoller = null

onMounted(async () => {
  try {
    // Kick off report generation
    const result = await generateReport(props.simulationId)
    const d = result.data
    reportId.value = d.report_id

    if (d.already_generated) {
      // Report already exists — fetch it directly
      await loadReport(d.report_id)
      return
    }

    // Poll for generation status
    const taskId = d.task_id
    statusPoller = poll(() => getReportGenerateStatus(taskId, props.simulationId), 3000)
    statusPoller.start(async (result, err) => {
      if (err) {
        error.value = err.message
        return
      }
      const sd = result.data
      progress.value = sd.progress || 0
      progressMessage.value = sd.message || ''

      if (sd.status === 'completed' || sd.already_completed) {
        statusPoller.stop()
        const resolvedReportId = sd.report_id || sd.result?.report_id || reportId.value
        await loadReport(resolvedReportId)
      } else if (sd.status === 'failed') {
        statusPoller.stop()
        generating.value = false
        error.value = sd.message || 'Report generation failed'
      }
    })
  } catch (e) {
    generating.value = false
    error.value = e.message
  }
})

onUnmounted(() => {
  if (statusPoller) statusPoller.stop()
})

async function loadReport(id) {
  try {
    reportId.value = id

    // Try sections endpoint first for incremental chapter display
    const sectionsResult = await getReportSections(id)
    const sections = sectionsResult.data?.sections || []

    if (sections.length > 0) {
      chapters.value = sections.map(s => ({
        title: extractTitle(s.content),
        content: s.content,
      }))
    } else {
      // Fallback to full report
      const reportResult = await getReport(id)
      const markdown = reportResult.data?.markdown_content || ''
      chapters.value = splitMarkdownIntoChapters(markdown)
    }
  } catch (e) {
    error.value = e.message
  } finally {
    generating.value = false
  }
}

function extractTitle(markdown) {
  const match = markdown.match(/^#{1,3}\s+(.+)/m)
  return match ? match[1].trim() : 'Section'
}

function splitMarkdownIntoChapters(markdown) {
  if (!markdown) return [{ title: 'Report', content: 'No content available.' }]
  const parts = markdown.split(/(?=^## )/m).filter(Boolean)
  if (parts.length === 0) return [{ title: 'Report', content: markdown }]
  return parts.map(part => ({
    title: extractTitle(part),
    content: part,
  }))
}
</script>

<template>
  <div class="max-w-6xl mx-auto px-6 py-8">
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-2xl font-semibold text-[#050505]">Simulation Report</h1>
      <div class="flex gap-2">
        <router-link :to="{ name: 'chat', params: { simulationId } }"
          class="bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors no-underline">
          Ask Follow-Up →
        </router-link>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
      {{ error }}
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <!-- Chapter Nav -->
      <div class="space-y-2">
        <div v-if="generating" class="text-sm text-[#888]">
          <div class="mb-2">Generating report...</div>
          <div class="h-1.5 bg-black/5 rounded-full overflow-hidden">
            <div class="h-full bg-[#2068FF] rounded-full transition-all duration-500"
              :style="{ width: progress + '%' }"></div>
          </div>
          <p class="text-xs text-[#aaa] mt-1">{{ progressMessage }}</p>
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
      <div class="md:col-span-3 bg-white border border-black/10 rounded-lg p-8">
        <div v-if="generating" class="text-center py-16">
          <div class="text-4xl mb-4">📝</div>
          <p class="text-[#888]">Generating predictive report...</p>
          <p class="text-xs text-[#aaa] mt-2">{{ progress }}% — {{ progressMessage }}</p>
        </div>
        <div v-else-if="chapters[activeChapter]" class="prose prose-sm max-w-none whitespace-pre-wrap">
          {{ chapters[activeChapter].content }}
        </div>
        <div v-else class="text-center py-16 text-[#888]">
          No report content available.
        </div>
      </div>
    </div>
  </div>
</template>
