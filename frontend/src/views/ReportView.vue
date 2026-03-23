<script setup>
import { ref } from 'vue'

const props = defineProps({ taskId: String })
const chapters = ref([])
const activeChapter = ref(0)
const generating = ref(true)

// TODO: Call /api/report/generate, poll for chapters
// Render markdown with 'marked' library
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

    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <!-- Chapter Nav -->
      <div class="space-y-2">
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
      <div class="md:col-span-3 bg-white border border-black/10 rounded-lg p-8">
        <div v-if="generating" class="text-center py-16">
          <div class="w-10 h-10 border-2 border-[#2068FF] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p class="text-[#888]">Generating predictive report...</p>
          <p class="text-xs text-[#aaa] mt-2">Multi-chapter analysis with evidence from simulation</p>
        </div>
        <div v-else-if="chapters[activeChapter]" class="prose prose-sm max-w-none">
          <h2>{{ chapters[activeChapter].title }}</h2>
          <div v-html="chapters[activeChapter].html"></div>
        </div>
      </div>
    </div>
  </div>
</template>
