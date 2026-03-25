<script setup>
import { ref, computed, inject, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  taskId: { type: String, required: true },
})

const polling = inject('polling')

const startTime = ref(Date.now())
const elapsed = ref('0:00')
let elapsedTimer = null

const progressPercent = computed(() => polling.runStatus.value?.progress_percent ?? 0)
const currentRound = computed(() => polling.runStatus.value?.current_round ?? 0)
const totalRounds = computed(() => polling.runStatus.value?.total_rounds ?? 0)
const simStatus = computed(() => polling.simStatus.value)

const isActive = computed(() =>
  simStatus.value === 'running' || simStatus.value === 'building',
)

const agentNames = computed(() => {
  const names = new Set()
  for (const a of (polling.recentActions.value || [])) {
    if (a.agent_name) names.add(a.agent_name)
  }
  return [...names].slice(0, 8)
})

function updateElapsed() {
  const diff = Math.floor((Date.now() - startTime.value) / 1000)
  const mins = Math.floor(diff / 60)
  const secs = diff % 60
  elapsed.value = `${mins}:${secs.toString().padStart(2, '0')}`
}

onMounted(() => {
  startTime.value = Date.now()
  elapsedTimer = setInterval(updateElapsed, 1000)
})

onUnmounted(() => {
  if (elapsedTimer) clearInterval(elapsedTimer)
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border-t border-[var(--color-border)] px-4 md:px-6 py-2.5">
    <!-- Progress track -->
    <div class="h-1 bg-[var(--color-tint)] rounded-full overflow-hidden mb-2">
      <div
        class="h-full rounded-full transition-all duration-700 ease-out"
        :class="simStatus === 'completed' ? 'bg-[var(--color-success)]' : 'bg-[var(--color-primary)]'"
        :style="{ width: `${progressPercent}%` }"
      />
    </div>

    <div class="flex items-center gap-4 text-xs">
      <!-- Round info -->
      <div class="flex items-center gap-1.5 text-[var(--color-text-secondary)]">
        <span class="font-medium">Round {{ currentRound }}/{{ totalRounds }}</span>
        <span class="text-[var(--color-text-muted)]">&middot;</span>
        <span>{{ progressPercent }}%</span>
      </div>

      <!-- Elapsed time -->
      <div class="flex items-center gap-1.5 text-[var(--color-text-muted)]">
        <svg class="w-3 h-3" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="8" cy="8" r="6.5" />
          <polyline points="8,4.5 8,8 10.5,9.5" />
        </svg>
        <span>{{ elapsed }}</span>
      </div>

      <!-- Spacer -->
      <div class="flex-1" />

      <!-- Agent indicators -->
      <div class="hidden md:flex items-center gap-1">
        <div
          v-for="name in agentNames"
          :key="name"
          class="w-5 h-5 rounded-full flex items-center justify-center text-[8px] font-bold text-white"
          :style="{ backgroundColor: isActive ? 'var(--color-primary)' : 'var(--color-text-muted)' }"
          :title="name"
        >
          {{ name.charAt(0) }}
        </div>
        <span
          v-if="agentNames.length > 0"
          class="text-[var(--color-text-muted)] ml-1"
        >{{ agentNames.length }} active</span>
      </div>

      <!-- Status badge (mobile-friendly) -->
      <div class="flex items-center gap-1.5">
        <span
          v-if="isActive"
          class="w-2 h-2 rounded-full animate-pulse"
          :class="simStatus === 'running' ? 'bg-emerald-500' : 'bg-[var(--color-primary)]'"
        />
        <span
          v-else-if="simStatus === 'completed'"
          class="text-[var(--color-success)] font-medium"
        >Complete</span>
        <span
          v-else-if="simStatus === 'failed'"
          class="text-[var(--color-error)] font-medium"
        >Failed</span>
      </div>
    </div>
  </div>
</template>
