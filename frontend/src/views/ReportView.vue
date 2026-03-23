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
  <div class="max-w-6xl mx-auto px-4 md:px-6 py-6 md:py-8">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 md:mb-8">
      <h1 class="text-xl md:text-2xl font-semibold text-[#050505]">Simulation Report</h1>
      <div class="flex gap-2">
        <router-link :to="`/chat/${taskId}`"
          class="bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors no-underline">
          Ask Follow-Up →
        </router-link>
      </div>
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
        <div v-if="generating" class="text-center py-12 md:py-16">
          <div class="text-4xl mb-4">📝</div>
          <p class="text-[#888]">Generating predictive report...</p>
          <p class="text-xs text-[#aaa] mt-2">Multi-chapter analysis with evidence from simulation</p>
        </div>
        <div v-else-if="chapters[activeChapter]" class="prose prose-sm max-w-none">
          <h2>{{ chapters[activeChapter].title }}</h2>
          <div v-html="chapters[activeChapter].html"></div>
        </div>
        <!-- Mobile: empty state when no chapters -->
        <div v-if="!generating && chapters.length === 0" class="md:hidden text-sm text-[#888] text-center py-8">
          No chapters yet
        </div>
      </div>
    </div>
  </div>
</template>
