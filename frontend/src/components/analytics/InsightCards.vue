<script setup>
import { ref, onMounted } from 'vue'

const insights = ref([])
const loading = ref(true)

const demoInsights = [
  {
    id: 1,
    type: 'positive',
    title: 'Retention improving',
    body: 'Month-3 retention in the Q1 cohort is 8% higher than the Q4 cohort, correlating with the onboarding flow update.',
    metric: '+8%',
    category: 'Cohort',
  },
  {
    id: 2,
    type: 'warning',
    title: 'Attribution gap',
    body: 'Organic search drives 34% of first touches but only 12% of last touches — consider mid-funnel nurture content.',
    metric: '34% → 12%',
    category: 'Attribution',
  },
  {
    id: 3,
    type: 'positive',
    title: 'Enterprise segment outperforms',
    body: 'Enterprise accounts have 142% NRR vs 108% for SMB. Expansion revenue is concentrated in this segment.',
    metric: '142% NRR',
    category: 'Segment',
  },
  {
    id: 4,
    type: 'negative',
    title: 'SMB churn spike',
    body: 'SMB monthly churn rose to 4.2% in the latest cohort — 1.5x the trailing average. Investigate onboarding drop-off.',
    metric: '4.2%',
    category: 'Segment',
  },
  {
    id: 5,
    type: 'info',
    title: 'Paid social ROI',
    body: 'LinkedIn campaigns show 3.2x ROAS when attributed with time-decay model vs 1.1x with last-touch.',
    metric: '3.2x',
    category: 'Attribution',
  },
]

onMounted(() => {
  setTimeout(() => {
    insights.value = demoInsights
    loading.value = false
  }, 600)
})

function typeColor(type) {
  switch (type) {
    case 'positive': return 'text-emerald-500'
    case 'warning': return 'text-amber-500'
    case 'negative': return 'text-red-500'
    default: return 'text-[#2068FF]'
  }
}

function typeBg(type) {
  switch (type) {
    case 'positive': return 'bg-emerald-500/10 border-emerald-500/20'
    case 'warning': return 'bg-amber-500/10 border-amber-500/20'
    case 'negative': return 'bg-red-500/10 border-red-500/20'
    default: return 'bg-[rgba(32,104,255,0.08)] border-[#2068FF]/20'
  }
}

function typeIcon(type) {
  switch (type) {
    case 'positive': return 'M4.5 12.75l6 6 9-13.5'
    case 'warning': return 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z'
    case 'negative': return 'M12 9v3.75m0 0v.008m0-.008h.008M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z'
    default: return 'M11.25 11.25l.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z'
  }
}
</script>

<template>
  <div>
    <div class="flex items-center gap-2 mb-4">
      <svg class="w-4 h-4 text-[#2068FF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456Z" />
      </svg>
      <h3 class="text-sm font-semibold text-[var(--color-text)]">AI Insights</h3>
    </div>

    <!-- Loading shimmer -->
    <div v-if="loading" class="space-y-3">
      <div v-for="i in 3" :key="i" class="rounded-lg border border-[var(--color-border)] p-3 animate-pulse">
        <div class="h-3 w-24 bg-[var(--color-tint)] rounded mb-2"></div>
        <div class="h-2 w-full bg-[var(--color-tint)] rounded mb-1.5"></div>
        <div class="h-2 w-3/4 bg-[var(--color-tint)] rounded"></div>
      </div>
    </div>

    <!-- Insight cards -->
    <div v-else class="space-y-3">
      <div
        v-for="insight in insights"
        :key="insight.id"
        class="rounded-lg border p-3 transition-colors hover:border-[var(--color-border-strong)]"
        :class="typeBg(insight.type)"
      >
        <div class="flex items-start gap-2 mb-1.5">
          <svg class="w-4 h-4 shrink-0 mt-0.5" :class="typeColor(insight.type)" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" :d="typeIcon(insight.type)" />
          </svg>
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between gap-2">
              <span class="text-xs font-semibold text-[var(--color-text)]">{{ insight.title }}</span>
              <span class="text-xs font-mono font-bold shrink-0" :class="typeColor(insight.type)">{{ insight.metric }}</span>
            </div>
          </div>
        </div>
        <p class="text-xs text-[var(--color-text-secondary)] leading-relaxed ml-6">{{ insight.body }}</p>
        <div class="mt-2 ml-6">
          <span class="text-[10px] font-medium text-[var(--color-text-muted)] bg-[var(--color-surface)] px-1.5 py-0.5 rounded">
            {{ insight.category }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
