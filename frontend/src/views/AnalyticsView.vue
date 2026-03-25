<script setup>
import { defineAsyncComponent, ref } from 'vue'
import InsightCards from '../components/analytics/InsightCards.vue'
import AiAnalyst from '../components/analytics/AiAnalyst.vue'

function placeholder(title) {
  return {
    template: `
      <div class="border border-dashed border-[var(--color-border)] rounded-xl p-8 flex flex-col items-center justify-center text-center min-h-[280px]">
        <svg class="w-8 h-8 text-[var(--color-text-muted)] mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5m.75-9 3-3 2.148 2.148A12.061 12.061 0 0 1 16.5 7.605" />
        </svg>
        <p class="text-sm font-medium text-[var(--color-text-secondary)]">${title}</p>
        <p class="text-xs text-[var(--color-text-muted)] mt-1">Component coming soon</p>
      </div>
    `,
  }
}

const CohortAnalysis = defineAsyncComponent(() =>
  import('../components/analytics/CohortAnalysis.vue').catch(() => placeholder('Cohort Analysis'))
)

const AttributionAnalysis = defineAsyncComponent(() =>
  import('../components/analytics/AttributionAnalysis.vue').catch(() => placeholder('Attribution Analysis'))
)

const SegmentPerformance = defineAsyncComponent(() =>
  import('../components/analytics/SegmentPerformance.vue').catch(() => placeholder('Segment Performance'))
)

const sidebarCollapsed = ref(false)
</script>

<template>
  <div class="max-w-[1400px] mx-auto px-4 md:px-6 py-6 md:py-10">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6 md:mb-8">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-lg bg-[rgba(32,104,255,0.08)] flex items-center justify-center">
          <svg class="w-5 h-5 text-[#2068FF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 14.25v2.25m3-4.5v4.5m3-6.75v6.75m3-9v9M3 20.25h18M3.75 20.25V3.75" />
          </svg>
        </div>
        <div>
          <h1 class="text-xl md:text-2xl font-semibold text-[var(--color-text)]">Analytics</h1>
          <p class="text-xs text-[var(--color-text-muted)] mt-0.5">Cohort trends, attribution, and segment insights</p>
        </div>
      </div>
      <button
        @click="sidebarCollapsed = !sidebarCollapsed"
        class="hidden lg:flex items-center gap-1.5 text-xs font-medium text-[var(--color-text-secondary)] hover:text-[#2068FF] px-3 py-2 rounded-lg border border-[var(--color-border)] hover:border-[#2068FF]/50 transition-colors"
      >
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />
        </svg>
        {{ sidebarCollapsed ? 'Show Insights' : 'Hide Insights' }}
      </button>
    </div>

    <!-- Main layout: content + sidebar -->
    <div class="flex gap-6">
      <!-- Main content area -->
      <div class="flex-1 min-w-0 space-y-6">
        <!-- Cohort Analysis — full width -->
        <section class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5 md:p-6">
          <CohortAnalysis />
        </section>

        <!-- Attribution + Segment — half & half -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <section class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5 md:p-6">
            <AttributionAnalysis />
          </section>
          <section class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5 md:p-6">
            <SegmentPerformance />
          </section>
        </div>
      </div>

      <!-- Insights sidebar -->
      <aside
        v-if="!sidebarCollapsed"
        class="hidden lg:block w-72 shrink-0"
      >
        <div class="sticky top-6">
          <InsightCards />
        </div>
      </aside>
    </div>

    <!-- Mobile insights — shown below content on small screens -->
    <div class="lg:hidden mt-6 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5">
      <InsightCards />
    </div>

    <!-- AI Analyst chat bubble -->
    <AiAnalyst />
  </div>
</template>
