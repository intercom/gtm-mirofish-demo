<script setup>
import { ref, onMounted, watch } from 'vue'
import { useInsightsStore } from '../../stores/insights'

const store = useInsightsStore()

const expandedEvidence = ref(new Set())

const CATEGORY_META = {
  revenue: { label: 'Revenue', color: 'bg-green-100 text-green-700', icon: '💰' },
  pipeline: { label: 'Pipeline', color: 'bg-[rgba(32,104,255,0.1)] text-[var(--color-primary)]', icon: '📊' },
  operations: { label: 'Operations', color: 'bg-[rgba(255,86,0,0.1)] text-[var(--color-fin-orange)]', icon: '⚙️' },
  simulation: { label: 'Simulation', color: 'bg-purple-100 text-purple-700', icon: '🧪' },
  system: { label: 'System', color: 'bg-black/5 text-[var(--color-text-secondary)]', icon: '🔧' },
}

function getCategoryMeta(category) {
  return CATEGORY_META[category] || CATEGORY_META.system
}

function toggleEvidence(id) {
  if (expandedEvidence.value.has(id)) {
    expandedEvidence.value.delete(id)
  } else {
    expandedEvidence.value.add(id)
  }
}

function confidenceLabel(value) {
  if (value >= 0.9) return 'Very High'
  if (value >= 0.8) return 'High'
  if (value >= 0.7) return 'Medium'
  return 'Low'
}

function confidenceColor(value) {
  if (value >= 0.9) return 'bg-green-500'
  if (value >= 0.8) return 'bg-[var(--color-primary)]'
  if (value >= 0.7) return 'bg-yellow-500'
  return 'bg-red-400'
}

const allCategories = [
  { key: null, label: 'All' },
  { key: 'revenue', label: 'Revenue' },
  { key: 'pipeline', label: 'Pipeline' },
  { key: 'operations', label: 'Operations' },
  { key: 'simulation', label: 'Simulation' },
]

onMounted(() => store.fetch())
</script>

<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <div class="flex items-center gap-2">
        <span class="text-lg">💡</span>
        <h2 class="text-base font-semibold text-[var(--color-text)]">Insights</h2>
        <span
          v-if="store.insights.length"
          class="text-xs text-[var(--color-text-muted)] bg-black/5 dark:bg-white/10 px-2 py-0.5 rounded-full"
        >
          {{ store.filteredInsights.length }}
        </span>
      </div>
      <button
        @click="store.refresh()"
        :disabled="store.loading"
        class="inline-flex items-center gap-1.5 text-xs font-medium text-[var(--color-primary)] hover:text-[#1a5ae0] transition-colors disabled:opacity-50"
      >
        <svg
          class="w-3.5 h-3.5"
          :class="{ 'animate-spin': store.loading }"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        Refresh
      </button>
    </div>

    <!-- Category Tabs -->
    <div class="flex gap-1 overflow-x-auto pb-1">
      <button
        v-for="cat in allCategories"
        :key="cat.key ?? 'all'"
        @click="store.setCategory(cat.key)"
        :class="[
          'px-3 py-1 rounded-full text-xs font-medium transition-colors whitespace-nowrap',
          store.activeCategory === cat.key
            ? 'bg-[var(--color-primary)] text-white'
            : 'bg-black/5 dark:bg-white/10 text-[var(--color-text-secondary)] hover:bg-black/10 dark:hover:bg-white/20',
        ]"
      >
        {{ cat.label }}
      </button>
    </div>

    <!-- Loading Skeleton -->
    <div v-if="store.loading" class="space-y-3">
      <div
        v-for="i in 3"
        :key="i"
        class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4 overflow-hidden"
      >
        <div class="flex items-start gap-3">
          <div class="w-8 h-8 rounded-lg bg-black/5 dark:bg-white/10 shimmer-line shrink-0" />
          <div class="flex-1 space-y-2">
            <div class="shimmer-line rounded h-4 w-3/4" />
            <div class="shimmer-line rounded h-3 w-full" />
            <div class="shimmer-line rounded h-3 w-1/2" />
          </div>
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div
      v-else-if="store.error"
      class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4 text-sm text-red-700 dark:text-red-300"
    >
      Failed to load insights: {{ store.error }}
    </div>

    <!-- Empty State -->
    <div
      v-else-if="store.filteredInsights.length === 0"
      class="flex flex-col items-center justify-center py-12 text-center"
    >
      <div class="w-12 h-12 rounded-full bg-[rgba(32,104,255,0.08)] flex items-center justify-center mb-3">
        <span class="text-2xl">💡</span>
      </div>
      <p class="text-sm font-medium text-[var(--color-text)]">No insights yet</p>
      <p class="text-xs text-[var(--color-text-muted)] mt-1">Run a simulation to generate AI-powered insights</p>
    </div>

    <!-- Insight Cards -->
    <TransitionGroup v-else name="insight" tag="div" class="space-y-3">
      <div
        v-for="insight in store.filteredInsights"
        :key="insight.id"
        class="group bg-[var(--card-bg)] border border-[var(--card-border)] rounded-xl p-4 transition-shadow hover:shadow-md"
        :class="{ 'ring-2 ring-[var(--color-primary)] ring-offset-1': insight.pinned }"
      >
        <!-- Card Header -->
        <div class="flex items-start gap-3">
          <!-- Category Icon -->
          <div
            class="w-8 h-8 rounded-lg flex items-center justify-center text-sm shrink-0"
            :class="getCategoryMeta(insight.category).color"
          >
            {{ getCategoryMeta(insight.category).icon }}
          </div>

          <!-- Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between gap-2">
              <h3 class="text-sm font-semibold text-[var(--color-text)] leading-snug">
                {{ insight.title }}
              </h3>
              <!-- Actions (visible on hover + always on mobile) -->
              <div class="flex items-center gap-1 shrink-0 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
                <button
                  @click="store.togglePin(insight.id)"
                  :title="insight.pinned ? 'Unpin' : 'Pin'"
                  class="w-6 h-6 rounded flex items-center justify-center text-xs hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
                  :class="insight.pinned ? 'text-[var(--color-primary)]' : 'text-[var(--color-text-muted)]'"
                >
                  <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a2 2 0 114 0v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
                  </svg>
                </button>
                <button
                  @click="store.dismiss(insight.id)"
                  title="Dismiss"
                  class="w-6 h-6 rounded flex items-center justify-center text-xs text-[var(--color-text-muted)] hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                >
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Category Badge -->
            <span
              :class="[
                'inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold mt-1.5',
                getCategoryMeta(insight.category).color,
              ]"
            >
              {{ getCategoryMeta(insight.category).label }}
            </span>

            <!-- Description -->
            <p class="text-xs text-[var(--color-text-secondary)] leading-relaxed mt-2">
              {{ insight.description }}
            </p>

            <!-- Confidence Bar -->
            <div class="flex items-center gap-2 mt-3">
              <span class="text-[10px] text-[var(--color-text-muted)] font-medium w-16 shrink-0">
                Confidence
              </span>
              <div class="flex-1 h-1.5 bg-black/5 dark:bg-white/10 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :class="confidenceColor(insight.confidence)"
                  :style="{ width: `${insight.confidence * 100}%` }"
                />
              </div>
              <span class="text-[10px] text-[var(--color-text-muted)] font-medium w-16 text-right shrink-0">
                {{ confidenceLabel(insight.confidence) }} ({{ Math.round(insight.confidence * 100) }}%)
              </span>
            </div>

            <!-- Evidence Toggle -->
            <button
              v-if="insight.evidence?.length"
              @click="toggleEvidence(insight.id)"
              class="flex items-center gap-1 mt-3 text-[11px] font-medium text-[var(--color-primary)] hover:text-[#1a5ae0] transition-colors"
            >
              <svg
                class="w-3 h-3 transition-transform duration-200"
                :class="{ 'rotate-90': expandedEvidence.has(insight.id) }"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
              {{ expandedEvidence.has(insight.id) ? 'Hide' : 'Show' }} evidence ({{ insight.evidence.length }})
            </button>

            <!-- Evidence List -->
            <Transition name="evidence">
              <ul
                v-if="expandedEvidence.has(insight.id)"
                class="mt-2 space-y-1.5 pl-1"
              >
                <li
                  v-for="(item, idx) in insight.evidence"
                  :key="idx"
                  class="flex items-start gap-2 text-xs text-[var(--color-text-secondary)]"
                >
                  <span class="w-1 h-1 rounded-full bg-[var(--color-primary)] mt-1.5 shrink-0" />
                  {{ item }}
                </li>
              </ul>
            </Transition>
          </div>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.shimmer-line {
  background: linear-gradient(
    90deg,
    rgba(0, 0, 0, 0.04) 25%,
    rgba(0, 0, 0, 0.08) 50%,
    rgba(0, 0, 0, 0.04) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.insight-enter-active,
.insight-leave-active {
  transition: all 0.3s ease;
}
.insight-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}
.insight-leave-to {
  opacity: 0;
  transform: translateX(16px);
}

.evidence-enter-active,
.evidence-leave-active {
  transition: all 0.2s ease;
}
.evidence-enter-from,
.evidence-leave-to {
  opacity: 0;
  max-height: 0;
}
.evidence-enter-to,
.evidence-leave-from {
  opacity: 1;
  max-height: 200px;
}
</style>
