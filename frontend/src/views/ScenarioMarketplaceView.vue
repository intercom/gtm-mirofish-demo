<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useScenariosStore } from '../stores/scenarios'
import LoadingSpinner from '../components/ui/LoadingSpinner.vue'
import ErrorState from '../components/ui/ErrorState.vue'

const router = useRouter()
const store = useScenariosStore()

const searchQuery = ref('')
const activeCategory = ref('all')

onMounted(() => {
  store.fetchScenarios(true)
})

const CATEGORY_META = {
  all: { label: 'All Scenarios', icon: '🐟' },
  outbound: { label: 'Outbound', icon: '📧' },
  signals: { label: 'Signals', icon: '📡' },
  pricing: { label: 'Pricing', icon: '💰' },
  personalization: { label: 'Personalization', icon: '✨' },
}

const ICON_MAP = {
  mail: '📧',
  signal: '📡',
  'dollar-sign': '💰',
  sparkles: '✨',
  sparkle: '✨',
  dollar: '💰',
}

function resolveIcon(icon) {
  if (!icon) return '🐟'
  if (/\p{Emoji}/u.test(icon)) return icon
  return ICON_MAP[icon] || '🐟'
}

const categories = computed(() => {
  const cats = new Set(store.scenarios.map(s => s.category))
  return ['all', ...cats].map(key => ({
    key,
    ...(CATEGORY_META[key] || { label: key, icon: '🐟' }),
  }))
})

const filteredScenarios = computed(() => {
  let list = store.scenarios

  if (activeCategory.value !== 'all') {
    list = list.filter(s => s.category === activeCategory.value)
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(s =>
      s.name.toLowerCase().includes(q) ||
      s.description.toLowerCase().includes(q) ||
      (s.persona_types || []).some(p => p.toLowerCase().includes(q)) ||
      (s.industries || []).some(i => i.toLowerCase().includes(q))
    )
  }

  return list
})

function launchScenario(id) {
  router.push(`/scenarios/${id}`)
}

function formatAgentCount(count) {
  if (!count) return '—'
  return count >= 1000 ? `${(count / 1000).toFixed(0)}k` : count.toString()
}
</script>

<template>
  <div class="min-h-screen bg-[var(--color-surface)]">
    <!-- Header -->
    <div class="bg-[var(--color-navy)] text-white">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 py-10 sm:py-14">
        <h1 class="text-2xl sm:text-3xl font-bold tracking-tight mb-2">Scenario Marketplace</h1>
        <p class="text-white/60 text-sm sm:text-base max-w-2xl">
          Pre-built GTM simulation scenarios ready to run. Choose a template, customize parameters, and launch a simulation in minutes.
        </p>

        <!-- Search -->
        <div class="mt-6 relative max-w-md">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/>
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search scenarios, personas, industries..."
            class="w-full bg-white/10 border border-white/10 rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder-white/40 focus:outline-none focus:border-[#2068FF] focus:ring-1 focus:ring-[#2068FF] transition-colors"
          />
        </div>
      </div>
    </div>

    <div class="max-w-6xl mx-auto px-4 sm:px-6 py-8">
      <!-- Category tabs -->
      <div class="flex items-center gap-2 mb-8 overflow-x-auto pb-1 -mx-1 px-1">
        <button
          v-for="cat in categories"
          :key="cat.key"
          @click="activeCategory = cat.key"
          class="flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all"
          :class="activeCategory === cat.key
            ? 'bg-[#2068FF] text-white shadow-sm'
            : 'bg-[var(--color-card-bg)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] border border-[var(--color-border)]'"
        >
          <span class="text-base">{{ cat.icon }}</span>
          {{ cat.label }}
        </button>
      </div>

      <!-- Loading -->
      <LoadingSpinner v-if="store.loading" label="Loading scenarios..." />

      <!-- Error -->
      <ErrorState
        v-else-if="store.error"
        :message="store.error"
        action-label="Retry"
        @action="store.fetchScenarios(true)"
      />

      <!-- Empty search results -->
      <div v-else-if="filteredScenarios.length === 0" class="flex flex-col items-center justify-center py-16 text-center">
        <div class="w-14 h-14 rounded-full bg-[rgba(32,104,255,0.08)] flex items-center justify-center mb-4">
          <span class="text-2xl">🔍</span>
        </div>
        <p class="text-sm font-medium text-[var(--color-text)] mb-1">No scenarios found</p>
        <p class="text-sm text-[var(--color-text-muted)]">Try a different search term or category.</p>
      </div>

      <!-- Scenario grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-5">
        <article
          v-for="scenario in filteredScenarios"
          :key="scenario.id"
          class="group bg-[var(--color-card-bg)] border border-[var(--color-border)] rounded-xl overflow-hidden hover:border-[#2068FF]/40 hover:shadow-md transition-all cursor-pointer"
          @click="launchScenario(scenario.id)"
        >
          <div class="p-5 sm:p-6">
            <!-- Icon + category badge -->
            <div class="flex items-start justify-between mb-4">
              <div class="w-11 h-11 rounded-lg bg-[rgba(32,104,255,0.08)] flex items-center justify-center text-xl">
                {{ resolveIcon(scenario.icon) }}
              </div>
              <span class="text-xs font-medium text-[var(--color-text-muted)] bg-[var(--color-surface)] px-2.5 py-1 rounded-full capitalize">
                {{ scenario.category }}
              </span>
            </div>

            <!-- Title + description -->
            <h3 class="text-base font-semibold text-[var(--color-text)] mb-1.5 group-hover:text-[#2068FF] transition-colors">
              {{ scenario.name }}
            </h3>
            <p class="text-sm text-[var(--color-text-muted)] leading-relaxed mb-4 line-clamp-2">
              {{ scenario.description }}
            </p>

            <!-- Metadata chips -->
            <div class="flex flex-wrap gap-2 mb-4">
              <span
                v-if="scenario.agent_count"
                class="inline-flex items-center gap-1 text-xs text-[var(--color-text-muted)] bg-[var(--color-surface)] px-2 py-1 rounded"
              >
                <svg class="w-3 h-3" viewBox="0 0 16 16" fill="currentColor"><path d="M8 8a3 3 0 100-6 3 3 0 000 6zm2-3a2 2 0 11-4 0 2 2 0 014 0zm4 8c0 1-1 1-1 1H3s-1 0-1-1 1-4 6-4 6 3 6 4zm-1-.004c-.001-.246-.154-.986-.832-1.664C11.516 10.68 10.289 10 8 10c-2.29 0-3.516.68-4.168 1.332-.678.678-.83 1.418-.832 1.664h10z"/></svg>
                {{ formatAgentCount(scenario.agent_count) }} agents
              </span>
              <span
                v-if="scenario.duration_hours"
                class="inline-flex items-center gap-1 text-xs text-[var(--color-text-muted)] bg-[var(--color-surface)] px-2 py-1 rounded"
              >
                <svg class="w-3 h-3" viewBox="0 0 16 16" fill="currentColor"><path d="M8 3.5a.5.5 0 00-1 0V8a.5.5 0 00.252.434l3.5 2a.5.5 0 00.496-.868L8 7.71V3.5z"/><path d="M8 16A8 8 0 108 0a8 8 0 000 16zm7-8A7 7 0 111 8a7 7 0 0114 0z"/></svg>
                {{ scenario.duration_hours }}h simulation
              </span>
              <span
                v-for="industry in (scenario.industries || []).slice(0, 2)"
                :key="industry"
                class="text-xs text-[var(--color-text-muted)] bg-[var(--color-surface)] px-2 py-1 rounded"
              >
                {{ industry }}
              </span>
              <span
                v-if="(scenario.industries || []).length > 2"
                class="text-xs text-[var(--color-text-muted)] bg-[var(--color-surface)] px-2 py-1 rounded"
              >
                +{{ scenario.industries.length - 2 }}
              </span>
            </div>

            <!-- Expected outputs preview -->
            <div v-if="scenario.expected_outputs?.length" class="mb-4">
              <p class="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide mb-1.5">Outputs</p>
              <ul class="space-y-1">
                <li
                  v-for="output in scenario.expected_outputs.slice(0, 3)"
                  :key="output"
                  class="flex items-start gap-1.5 text-xs text-[var(--color-text-muted)]"
                >
                  <svg class="w-3 h-3 text-[#2068FF] mt-0.5 shrink-0" viewBox="0 0 16 16" fill="currentColor"><path d="M12.736 3.97a.733.733 0 011.047 0c.286.289.29.756.01 1.05L7.88 12.01a.733.733 0 01-1.065.02L3.217 8.384a.757.757 0 010-1.06.733.733 0 011.047 0l3.052 3.093 5.4-6.425a.247.247 0 01.02-.022z"/></svg>
                  {{ output }}
                </li>
              </ul>
              <p v-if="scenario.expected_outputs.length > 3" class="text-xs text-[var(--color-text-muted)] mt-1 pl-[18px]">
                +{{ scenario.expected_outputs.length - 3 }} more
              </p>
            </div>

            <!-- Persona tags -->
            <div v-if="scenario.persona_types?.length" class="flex flex-wrap gap-1.5">
              <span
                v-for="persona in scenario.persona_types"
                :key="persona"
                class="text-xs font-medium text-[#2068FF] bg-[rgba(32,104,255,0.08)] px-2 py-0.5 rounded"
              >
                {{ persona }}
              </span>
            </div>
          </div>

          <!-- Footer -->
          <div class="px-5 sm:px-6 py-3 bg-[var(--color-surface)] border-t border-[var(--color-border)] flex items-center justify-between">
            <span class="text-xs text-[var(--color-text-muted)]">Click to configure & launch</span>
            <svg class="w-4 h-4 text-[var(--color-text-muted)] group-hover:text-[#2068FF] group-hover:translate-x-0.5 transition-all" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"/>
            </svg>
          </div>
        </article>
      </div>

      <!-- Custom scenario CTA -->
      <div class="mt-8 bg-[var(--color-card-bg)] border border-dashed border-[var(--color-border)] rounded-xl p-6 text-center">
        <p class="text-sm font-medium text-[var(--color-text)] mb-1">Don't see what you need?</p>
        <p class="text-sm text-[var(--color-text-muted)] mb-4">Create a custom scenario with your own seed data and parameters.</p>
        <router-link
          to="/scenarios/custom"
          class="inline-flex items-center gap-2 bg-[var(--color-navy)] hover:bg-[#1a1a1a] text-white text-sm font-medium px-5 py-2.5 rounded-lg transition-colors no-underline"
        >
          <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"/>
          </svg>
          Build Custom Scenario
        </router-link>
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
