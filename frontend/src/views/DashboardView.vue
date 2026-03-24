<script setup>
import { computed } from 'vue'
import { useSimulationStore } from '../stores/simulation'

const store = useSimulationStore()

const runs = computed(() =>
  [...store.sessionRuns].sort((a, b) => b.timestamp - a.timestamp),
)

function relativeTime(ts) {
  const diff = Math.floor((Date.now() - ts) / 1000)
  if (diff < 60) return 'just now'
  if (diff < 3600) {
    const m = Math.floor(diff / 60)
    return `${m} min${m === 1 ? '' : 's'} ago`
  }
  if (diff < 86400) {
    const h = Math.floor(diff / 3600)
    return `${h} hour${h === 1 ? '' : 's'} ago`
  }
  const d = Math.floor(diff / 86400)
  return `${d} day${d === 1 ? '' : 's'} ago`
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 md:px-6 py-6 md:py-10">
    <div class="flex items-center justify-between mb-6 md:mb-8">
      <div class="flex items-center gap-3">
        <h1 class="text-xl md:text-2xl font-semibold text-[var(--color-text)]">Simulation Runs</h1>
        <span
          v-if="store.hasRuns"
          class="text-xs font-medium text-[#2068FF] bg-[rgba(32,104,255,0.08)] px-2.5 py-0.5 rounded-full"
        >
          {{ store.sessionRuns.length }}
        </span>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!store.hasRuns" class="text-center py-16 md:py-24">
      <div class="w-16 h-16 rounded-full bg-[rgba(32,104,255,0.08)] flex items-center justify-center mx-auto mb-5">
        <svg class="w-7 h-7 text-[#2068FF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5m.75-9 3-3 2.148 2.148A12.061 12.061 0 0 1 16.5 7.605" />
        </svg>
      </div>
      <h2 class="text-base font-semibold text-[var(--color-text)] mb-2">No simulation runs yet</h2>
      <p class="text-sm text-[var(--color-text-secondary)] mb-6 max-w-sm mx-auto">
        Run a simulation from the home page to see your results here.
      </p>
      <router-link
        to="/"
        class="inline-flex items-center gap-2 bg-[#2068FF] hover:bg-[#1a5ae0] text-white text-sm font-medium px-5 py-2.5 rounded-lg transition-colors no-underline"
      >
        Go to Home
      </router-link>
    </div>

    <!-- Run cards -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="run in runs"
        :key="run.id"
        class="border border-[var(--color-border)] bg-[var(--color-surface)] rounded-lg p-5 transition-shadow hover:shadow-[var(--shadow-md)]"
      >
        <div class="flex items-start justify-between mb-3">
          <h3 class="text-sm font-semibold text-[var(--color-text)] leading-snug">{{ run.scenarioName }}</h3>
          <span class="text-xs text-[var(--color-text-muted)] whitespace-nowrap ml-3">{{ relativeTime(run.timestamp) }}</span>
        </div>

        <div class="grid grid-cols-2 gap-3 mb-4">
          <div class="bg-[var(--color-tint)] rounded-md px-3 py-2">
            <div class="text-xs text-[var(--color-text-muted)]">Rounds</div>
            <div class="text-sm font-semibold text-[var(--color-text)]">{{ run.totalRounds }}</div>
          </div>
          <div class="bg-[var(--color-tint)] rounded-md px-3 py-2">
            <div class="text-xs text-[var(--color-text-muted)]">Actions</div>
            <div class="text-sm font-semibold text-[var(--color-text)]">{{ run.totalActions }}</div>
          </div>
          <div class="bg-[rgba(32,104,255,0.06)] rounded-md px-3 py-2">
            <div class="text-xs text-[#2068FF]">Twitter</div>
            <div class="text-sm font-semibold text-[var(--color-text)]">{{ run.twitterActions }}</div>
          </div>
          <div class="bg-[rgba(255,86,0,0.06)] rounded-md px-3 py-2">
            <div class="text-xs text-[#ff5600]">Reddit</div>
            <div class="text-sm font-semibold text-[var(--color-text)]">{{ run.redditActions }}</div>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <router-link
            :to="`/graph/${run.id}`"
            class="flex-1 text-center text-xs font-medium px-3 py-2 rounded-md border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[#2068FF]/50 hover:text-[#2068FF] transition-colors no-underline"
          >
            Graph
          </router-link>
          <router-link
            :to="`/simulation/${run.id}`"
            class="flex-1 text-center text-xs font-medium px-3 py-2 rounded-md border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[#2068FF]/50 hover:text-[#2068FF] transition-colors no-underline"
          >
            Simulation
          </router-link>
          <router-link
            :to="`/report/${run.id}`"
            class="flex-1 text-center text-xs font-medium px-3 py-2 rounded-md bg-[#2068FF] text-white hover:bg-[#1a5ae0] transition-colors no-underline"
          >
            Report
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>
