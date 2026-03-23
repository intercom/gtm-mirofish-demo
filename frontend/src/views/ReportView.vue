<script setup>
import { ref, onMounted } from 'vue'
import { useToastStore } from '../stores/toast.js'
import LoadingSpinner from '../components/ui/LoadingSpinner.vue'
import ErrorState from '../components/ui/ErrorState.vue'
import EmptyState from '../components/ui/EmptyState.vue'

const props = defineProps({ taskId: String })
const toast = useToastStore()

const chapters = ref([])
const activeChapter = ref(0)
const status = ref('loading')
const error = ref(null)

async function loadReport() {
  status.value = 'loading'
  error.value = null
  try {
    // TODO: Call /api/report/generate, poll for chapters
    // Render markdown with 'marked' library
    status.value = 'generating'
    toast.info('Generating predictive report...')
  } catch (e) {
    status.value = 'error'
    error.value = 'Failed to generate report: ' + e.message
    toast.error(error.value)
  }
}

onMounted(loadReport)
</script>

<template>
  <div class="max-w-6xl mx-auto px-6 py-8">
    <!-- Loading -->
    <LoadingSpinner v-if="status === 'loading'" label="Loading report..." />

    <!-- Error -->
    <ErrorState v-else-if="status === 'error'" :message="error" @retry="loadReport" />

    <!-- Report Content -->
    <template v-else>
      <div class="flex items-center justify-between mb-8">
        <h1 class="text-2xl font-semibold text-[#050505]">Simulation Report</h1>
        <div class="flex gap-2">
          <router-link :to="`/chat/${taskId}`"
            class="bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors no-underline">
            Ask Follow-Up →
          </router-link>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <!-- Chapter Nav -->
        <div class="space-y-2">
          <div v-if="status === 'generating' && chapters.length === 0" class="space-y-2">
            <div v-for="n in 4" :key="n" class="h-10 bg-black/5 rounded-lg animate-pulse"></div>
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
          <!-- Generating skeleton -->
          <div v-if="status === 'generating' && chapters.length === 0" class="space-y-4 animate-pulse">
            <div class="h-7 bg-black/5 rounded w-2/3"></div>
            <div class="h-4 bg-black/5 rounded w-full"></div>
            <div class="h-4 bg-black/5 rounded w-5/6"></div>
            <div class="h-4 bg-black/5 rounded w-4/5"></div>
            <div class="h-20 bg-black/5 rounded w-full mt-6"></div>
            <div class="h-4 bg-black/5 rounded w-3/4"></div>
            <div class="h-4 bg-black/5 rounded w-full"></div>
          </div>

          <!-- Empty (generated but no chapters produced) -->
          <EmptyState
            v-else-if="status === 'complete' && chapters.length === 0"
            icon="📄"
            title="No report data"
            description="The simulation completed but no report chapters were generated. Try running a new simulation."
            action-label="Back to Home"
            action-to="/"
          />

          <!-- Chapter content -->
          <div v-else-if="chapters[activeChapter]" class="prose prose-sm max-w-none">
            <h2>{{ chapters[activeChapter].title }}</h2>
            <div v-html="chapters[activeChapter].html"></div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
