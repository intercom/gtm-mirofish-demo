<script setup>
import { ref, computed, onMounted } from 'vue'
import { useScenariosStore } from '../stores/scenarios'
import LoadingSpinner from '../components/ui/LoadingSpinner.vue'
import EmptyState from '../components/ui/EmptyState.vue'

const store = useScenariosStore()
const activeCategory = ref('all')

onMounted(() => {
  store.fetchScenarios()
})

const ICON_MAP = {
  mail: '📧',
  signal: '📡',
  'dollar-sign': '💰',
  sparkles: '✨',
}

function resolveIcon(icon) {
  if (!icon) return '🐟'
  if (/\p{Emoji}/u.test(icon)) return icon
  return ICON_MAP[icon] || '🐟'
}

const CATEGORY_LABELS = {
  all: 'All Scenarios',
  outbound: 'Outbound',
  signals: 'Signals',
  pricing: 'Pricing',
  personalization: 'Personalization',
}

const categories = computed(() => {
  const cats = new Set(store.scenarios.map((s) => s.category))
  return ['all', ...cats]
})

const filteredScenarios = computed(() => {
  if (activeCategory.value === 'all') return store.scenarios
  return store.scenarios.filter((s) => s.category === activeCategory.value)
})

function categoryLabel(cat) {
  return CATEGORY_LABELS[cat] || cat.charAt(0).toUpperCase() + cat.slice(1)
}

const CATEGORY_COLORS = {
  outbound: { bg: 'rgba(32,104,255,0.08)', text: '#2068FF' },
  signals: { bg: 'rgba(170,0,255,0.08)', text: '#AA00FF' },
  pricing: { bg: 'rgba(255,86,0,0.08)', text: '#ff5600' },
  personalization: { bg: 'rgba(0,153,0,0.08)', text: '#009900' },
}

function categoryColor(cat) {
  return CATEGORY_COLORS[cat] || { bg: 'rgba(32,104,255,0.08)', text: '#2068FF' }
}
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 md:px-6 py-6 md:py-10">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 md:mb-8">
      <div>
        <h1 class="text-xl md:text-2xl font-semibold text-[var(--color-text)]">
          GTM Scenarios
        </h1>
        <p class="text-sm text-[var(--color-text-muted)] mt-1">
          Pre-built simulation templates for common GTM motions
        </p>
      </div>
      <router-link
        to="/scenarios/custom"
        class="inline-flex items-center gap-2 bg-[#2068FF] hover:bg-[#1a5ae0] text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors no-underline shrink-0"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        Custom Simulation
      </router-link>
    </div>

    <!-- Category Filter -->
    <div
      v-if="!store.loading && store.scenarios.length > 0"
      class="flex flex-wrap gap-2 mb-6"
    >
      <button
        v-for="cat in categories"
        :key="cat"
        @click="activeCategory = cat"
        class="text-xs font-medium px-3 py-1.5 rounded-full border transition-colors"
        :class="
          activeCategory === cat
            ? 'bg-[#2068FF] text-white border-[#2068FF]'
            : 'border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[#2068FF]/50 hover:text-[#2068FF]'
        "
      >
        {{ categoryLabel(cat) }}
      </button>
    </div>

    <!-- Loading -->
    <LoadingSpinner v-if="store.loading" label="Loading scenarios..." />

    <!-- Error -->
    <div v-else-if="store.error" class="text-center py-16">
      <div class="w-14 h-14 rounded-full bg-[var(--color-error-light)] flex items-center justify-center mx-auto mb-4">
        <svg class="w-7 h-7 text-[var(--color-error)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
        </svg>
      </div>
      <h2 class="text-base font-semibold text-[var(--color-text)] mb-2">Failed to load scenarios</h2>
      <p class="text-sm text-[var(--color-text-muted)] mb-4">{{ store.error }}</p>
      <button
        @click="store.fetchScenarios(true)"
        class="inline-flex items-center gap-2 bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white text-sm font-medium px-5 py-2.5 rounded-lg transition-colors"
      >
        Try Again
      </button>
    </div>

    <!-- Empty -->
    <EmptyState
      v-else-if="store.scenarios.length === 0"
      icon="🐟"
      title="No scenarios available"
      description="Check back soon — scenarios are being configured."
    />

    <!-- Scenario Cards -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="scenario in filteredScenarios"
        :key="scenario.id"
        class="group border border-[var(--color-border)] bg-[var(--color-surface)] rounded-lg p-5 transition-all hover:shadow-[var(--shadow-md)] hover:border-[#2068FF]/30"
      >
        <router-link
          :to="`/scenarios/${scenario.id}`"
          class="no-underline block"
        >
          <div class="flex items-start gap-3 mb-3">
            <span class="text-2xl shrink-0">{{ resolveIcon(scenario.icon) }}</span>
            <div class="flex-1 min-w-0">
              <h3 class="text-sm font-semibold text-[var(--color-text)] group-hover:text-[#2068FF] transition-colors leading-snug">
                {{ scenario.name }}
              </h3>
              <span
                class="inline-block text-[10px] font-medium px-1.5 py-0.5 rounded-full mt-1.5"
                :style="{
                  backgroundColor: categoryColor(scenario.category).bg,
                  color: categoryColor(scenario.category).text,
                }"
              >
                {{ categoryLabel(scenario.category) }}
              </span>
            </div>
          </div>
          <p class="text-xs text-[var(--color-text-muted)] leading-relaxed line-clamp-2">
            {{ scenario.description }}
          </p>
        </router-link>
        <div class="mt-3 flex items-center gap-3">
          <router-link
            :to="`/scenarios/${scenario.id}`"
            class="flex items-center gap-1 text-xs font-medium text-[#2068FF] no-underline hover:underline"
          >
            Configure &amp; Run
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
            </svg>
          </router-link>
          <router-link
            :to="`/scenarios/${scenario.id}/walkthrough`"
            class="flex items-center gap-1 text-xs font-medium text-[var(--color-text-muted)] hover:text-[#2068FF] no-underline transition-colors"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5" />
            </svg>
            Guided Tour
          </router-link>
        </div>
      </div>

      <!-- No results for filter -->
      <div
        v-if="filteredScenarios.length === 0"
        class="md:col-span-2 text-center py-12"
      >
        <p class="text-sm text-[var(--color-text-muted)]">No scenarios in this category.</p>
        <button
          @click="activeCategory = 'all'"
          class="text-sm text-[#2068FF] hover:underline mt-2"
        >
          Show all scenarios
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
