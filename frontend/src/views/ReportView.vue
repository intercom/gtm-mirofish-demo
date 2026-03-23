<script setup>
import { ref, onMounted } from 'vue'
import LoadingSpinner from '../components/ui/LoadingSpinner.vue'
import ErrorState from '../components/ui/ErrorState.vue'
import EmptyState from '../components/ui/EmptyState.vue'
import { useToast } from '../composables/useToast'

const props = defineProps({ taskId: String })
const toast = useToast()

const chapters = ref([])
const activeChapter = ref(0)
const loading = ref(true)
const error = ref(null)

async function generateReport() {
  loading.value = true
  error.value = null
  try {
    // TODO: Call /api/report/generate, poll for chapters
    // Render markdown with 'marked' library
    // Simulating load for now
    loading.value = false
  } catch (e) {
    error.value = e.message
    loading.value = false
    toast.error('Failed to generate report')
  }
}

onMounted(generateReport)
</script>

<template>
  <div class="max-w-6xl mx-auto px-6 py-8">
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-2xl font-semibold text-[#050505]">Simulation Report</h1>
      <div class="flex gap-2">
        <router-link :to="`/chat/${taskId}`"
          class="bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors no-underline">
          Ask Follow-Up →
        </router-link>
      </div>
    </div>

    <!-- Loading State -->
    <LoadingSpinner v-if="loading" label="Generating predictive report..." />

    <!-- Error State -->
    <ErrorState
      v-else-if="error"
      title="Report generation failed"
      :message="error"
      @retry="generateReport"
    />

    <!-- Empty State -->
    <EmptyState
      v-else-if="chapters.length === 0"
      icon="📊"
      title="No report data yet"
      description="Run a simulation first to generate a predictive report with multi-chapter analysis."
      action-label="Go to Scenarios"
      action-to="/"
    />

    <!-- Report Content -->
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
          <h2>{{ chapters[activeChapter].title }}</h2>
          <div v-html="chapters[activeChapter].html"></div>
        </div>
      </div>
    </div>
  </div>
</template>
