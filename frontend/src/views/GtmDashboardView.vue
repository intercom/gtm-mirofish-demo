<script setup>
import { ref } from 'vue'
import GtmDashboardLayout from '../components/dashboard/GtmDashboardLayout.vue'
import { useToast } from '../composables/useToast'

const toast = useToast()
const loading = ref(false)

async function onRefresh(dateRange) {
  loading.value = true
  // Simulated refresh delay — replaced by real API calls when widgets are wired up
  await new Promise(r => setTimeout(r, 600))
  loading.value = false
  toast.info('Dashboard refreshed')
}
</script>

<template>
  <GtmDashboardLayout
    title="GTM Dashboard"
    :loading="loading"
    @refresh="onRefresh"
    @date-change="onRefresh"
  >
    <template #kpis>
      <div
        v-for="kpi in [
          { label: 'Total ARR', value: '$2.2M' },
          { label: 'MRR Growth', value: '+4.2%' },
          { label: 'Pipeline', value: '$3.1M' },
          { label: 'Win Rate', value: '35%' },
          { label: 'Net Retention', value: '112%' },
          { label: 'Avg Deal Size', value: '$48K' },
          { label: 'Sales Cycle', value: '45d' },
          { label: 'Customers', value: '500' },
        ]"
        :key="kpi.label"
        class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3"
      >
        <div class="text-xs text-[var(--color-text-muted)]">{{ kpi.label }}</div>
        <div class="text-lg font-semibold text-[var(--color-text)]">{{ kpi.value }}</div>
      </div>
    </template>

    <template #chart-left>
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6 min-h-[320px] flex items-center justify-center">
        <div class="text-center text-[var(--color-text-muted)]">
          <svg class="w-10 h-10 mx-auto mb-3 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
          </svg>
          <p class="text-sm font-medium">Revenue & Pipeline Chart</p>
          <p class="text-xs mt-1">D3.js visualization slot</p>
        </div>
      </div>
    </template>

    <template #chart-right>
      <div class="flex flex-col gap-4">
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5 min-h-[150px] flex items-center justify-center">
          <div class="text-center text-[var(--color-text-muted)]">
            <p class="text-sm font-medium">Health Scorecard</p>
            <p class="text-xs mt-1">Traffic-light metrics</p>
          </div>
        </div>
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5 min-h-[150px] flex items-center justify-center">
          <div class="text-center text-[var(--color-text-muted)]">
            <p class="text-sm font-medium">Activity Feed</p>
            <p class="text-xs mt-1">Real-time events</p>
          </div>
        </div>
      </div>
    </template>

    <template #full-chart>
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6 min-h-[200px] flex items-center justify-center">
        <div class="text-center text-[var(--color-text-muted)]">
          <svg class="w-10 h-10 mx-auto mb-3 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
          </svg>
          <p class="text-sm font-medium">Deal Velocity & Funnel</p>
          <p class="text-xs mt-1">Gauge + funnel visualization slot</p>
        </div>
      </div>
    </template>

    <template #table>
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-6 min-h-[200px] flex items-center justify-center">
        <div class="text-center text-[var(--color-text-muted)]">
          <svg class="w-10 h-10 mx-auto mb-3 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 0 1-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0 1 12 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75h-7.5c-.621 0-1.125.504-1.125 1.125m8.625-1.125c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125M12 10.875v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 10.875c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125M13.125 12h7.5m-7.5 0c-.621 0-1.125.504-1.125 1.125M20.625 12c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5M12 14.625v-1.5m0 1.5c0 .621-.504 1.125-1.125 1.125M12 14.625c0 .621.504 1.125 1.125 1.125m-2.25 0c.621 0 1.125.504 1.125 1.125m0 0v1.5c0 .621-.504 1.125-1.125 1.125M3.375 15.75h7.5" />
          </svg>
          <p class="text-sm font-medium">Top Accounts Table</p>
          <p class="text-xs mt-1">Sortable accounts data</p>
        </div>
      </div>
    </template>
  </GtmDashboardLayout>
</template>
