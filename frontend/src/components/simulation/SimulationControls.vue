<script setup>
import { computed, inject } from 'vue'

const props = defineProps({
  taskId: { type: String, required: true },
})

const polling = inject('polling')

const status = computed(() => {
  const rs = polling.runStatus.value?.runner_status
  if (!rs || rs === 'idle' || rs === 'starting') return 'building'
  if (rs === 'running' || rs === 'paused') return 'running'
  if (rs === 'completed' || rs === 'stopped') return 'completed'
  if (rs === 'failed') return 'failed'
  return 'building'
})

const statusLabel = computed(() => {
  const map = { building: 'Preparing', running: 'Running', completed: 'Completed', failed: 'Failed' }
  return map[status.value] || 'Unknown'
})

const statusStyle = computed(() => {
  const map = {
    building: 'bg-[rgba(32,104,255,0.1)] text-[var(--color-primary)]',
    running: 'bg-emerald-100 text-emerald-700',
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
  }
  return map[status.value] || 'bg-gray-100 text-gray-700'
})

const currentRound = computed(() => polling.runStatus.value?.current_round ?? 0)
const totalRounds = computed(() => polling.runStatus.value?.total_rounds ?? 0)
const totalActions = computed(() => polling.runStatus.value?.total_actions_count ?? 0)
const twitterActions = computed(() => polling.runStatus.value?.twitter_actions_count ?? 0)
const redditActions = computed(() => polling.runStatus.value?.reddit_actions_count ?? 0)
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 h-full flex flex-col">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Controls</h3>
      <span class="px-2.5 py-1 rounded-full text-xs font-semibold" :class="statusStyle">
        {{ statusLabel }}
      </span>
    </div>

    <div class="flex-1 space-y-3">
      <!-- Round counter -->
      <div class="flex items-center justify-between text-sm">
        <span class="text-[var(--color-text-muted)]">Round</span>
        <span class="font-medium text-[var(--color-text)]">{{ currentRound }} / {{ totalRounds }}</span>
      </div>

      <!-- Action counts -->
      <div class="grid grid-cols-3 gap-2">
        <div class="text-center py-2 bg-[var(--color-tint)] rounded-md">
          <div class="text-base font-semibold text-[var(--color-text)]">{{ totalActions }}</div>
          <div class="text-[10px] text-[var(--color-text-muted)]">Total</div>
        </div>
        <div class="text-center py-2 bg-[rgba(32,104,255,0.05)] rounded-md">
          <div class="text-base font-semibold text-[var(--color-primary)]">{{ twitterActions }}</div>
          <div class="text-[10px] text-[var(--color-text-muted)]">Twitter</div>
        </div>
        <div class="text-center py-2 bg-[rgba(255,86,0,0.05)] rounded-md">
          <div class="text-base font-semibold text-[#ff5600]">{{ redditActions }}</div>
          <div class="text-[10px] text-[var(--color-text-muted)]">Reddit</div>
        </div>
      </div>

      <!-- Report link on completion -->
      <router-link
        v-if="status === 'completed'"
        :to="`/report/${taskId}`"
        class="flex items-center justify-center gap-2 w-full bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white text-sm font-medium py-2.5 rounded-lg transition-colors no-underline mt-auto"
      >
        Generate Report &rarr;
      </router-link>
    </div>
  </div>
</template>
