<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import ReplayViewer from '../components/simulation/ReplayViewer.vue'

const props = defineProps({
  taskId: { type: String, required: true },
})
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 md:px-6 py-6 md:py-10">
    <div class="flex items-center gap-3 mb-6">
      <router-link
        to="/simulations"
        class="p-1.5 rounded-md text-[var(--color-text-muted)] hover:text-[#2068FF] hover:bg-[rgba(32,104,255,0.08)] transition-colors no-underline"
        title="Back to simulations"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
        </svg>
      </router-link>
      <h1 class="text-xl md:text-2xl font-semibold text-[var(--color-text)]">Simulation Replay</h1>
    </div>
    <ReplayViewer :taskId="taskId" />
  </div>
</template>
