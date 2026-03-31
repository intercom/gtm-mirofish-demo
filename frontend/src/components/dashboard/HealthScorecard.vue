<script setup>
import { computed } from 'vue'

const props = defineProps({
  metrics: {
    type: Array,
    default: null,
  },
})

const thresholds = {
  'Pipeline Coverage': {
    target: '3.0x',
    lowerIsBetter: false,
    green: (v) => v > 3,
    yellow: (v) => v >= 2 && v <= 3,
    format: (v) => `${v.toFixed(1)}x`,
  },
  'Win Rate': {
    target: '30%',
    lowerIsBetter: false,
    green: (v) => v > 30,
    yellow: (v) => v >= 20 && v <= 30,
    format: (v) => `${v.toFixed(0)}%`,
  },
  'Churn Rate': {
    target: '<2%',
    lowerIsBetter: true,
    green: (v) => v < 2,
    yellow: (v) => v >= 2 && v <= 5,
    format: (v) => `${v.toFixed(1)}%`,
  },
  'Sales Cycle': {
    target: '<45d',
    lowerIsBetter: true,
    green: (v) => v < 45,
    yellow: (v) => v >= 45 && v <= 60,
    format: (v) => `${Math.round(v)}d`,
  },
  'NRR': {
    target: '>110%',
    lowerIsBetter: false,
    green: (v) => v > 110,
    yellow: (v) => v >= 100 && v <= 110,
    format: (v) => `${v.toFixed(0)}%`,
  },
  'Lead Response Time': {
    target: '<1h',
    lowerIsBetter: true,
    green: (v) => v < 1,
    yellow: (v) => v >= 1 && v <= 4,
    format: (v) => v < 1 ? `${Math.round(v * 60)}m` : `${v.toFixed(1)}h`,
  },
}

const defaultMetrics = [
  { name: 'Pipeline Coverage', value: 3.4, trend: 0.3 },
  { name: 'Win Rate', value: 27, trend: 2 },
  { name: 'Churn Rate', value: 1.8, trend: -0.4 },
  { name: 'Sales Cycle', value: 52, trend: -3 },
  { name: 'NRR', value: 112, trend: 1.5 },
  { name: 'Lead Response Time', value: 0.8, trend: -0.2 },
]

function getStatus(name, value) {
  const t = thresholds[name]
  if (!t) return 'red'
  if (t.green(value)) return 'green'
  if (t.yellow(value)) return 'yellow'
  return 'red'
}

const rows = computed(() => {
  const data = props.metrics || defaultMetrics
  return data.map((m) => {
    const t = thresholds[m.name]
    const status = getStatus(m.name, m.value)
    const trend = m.trend ?? 0
    const favorable = t?.lowerIsBetter ? trend < 0 : trend > 0
    return {
      name: m.name,
      value: t ? t.format(m.value) : String(m.value),
      status,
      target: t?.target ?? '—',
      trend,
      trendFavorable: trend === 0 ? null : favorable,
    }
  })
})

const overallHealth = computed(() => {
  const statuses = rows.value.map((r) => r.status)
  if (statuses.some((s) => s === 'red')) return 'red'
  if (statuses.some((s) => s === 'yellow')) return 'yellow'
  return 'green'
})

const overallLabel = computed(() => {
  const map = { green: 'Healthy', yellow: 'Needs Attention', red: 'At Risk' }
  return map[overallHealth.value]
})
</script>

<template>
  <div
    class="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-[var(--card-radius)] overflow-hidden"
    style="box-shadow: var(--card-shadow)"
  >
    <!-- Header -->
    <div class="flex items-center justify-between px-5 py-4 border-b border-[var(--card-border)]">
      <div>
        <h3 class="text-sm font-semibold text-[var(--color-text)]">GTM Health</h3>
        <p class="text-xs text-[var(--color-text-muted)] mt-0.5">6 key metrics</p>
      </div>
      <span
        class="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full"
        :class="{
          'bg-[var(--badge-success-bg-soft)] text-[var(--badge-success-text-soft)]':
            overallHealth === 'green',
          'bg-[var(--badge-warning-bg-soft)] text-[var(--badge-warning-text-soft)]':
            overallHealth === 'yellow',
          'bg-[var(--badge-error-bg-soft)] text-[var(--badge-error-text-soft)]':
            overallHealth === 'red',
        }"
      >
        <span
          class="w-1.5 h-1.5 rounded-full"
          :class="{
            'bg-[var(--color-success)]': overallHealth === 'green',
            'bg-[var(--color-warning)]': overallHealth === 'yellow',
            'bg-[var(--color-error)]': overallHealth === 'red',
          }"
        />
        {{ overallLabel }}
      </span>
    </div>

    <!-- Metrics table -->
    <table class="w-full">
      <thead>
        <tr class="text-xs text-[var(--color-text-muted)] border-b border-[var(--card-border)]">
          <th class="text-left font-medium px-5 py-2.5">Metric</th>
          <th class="text-right font-medium px-3 py-2.5">Value</th>
          <th class="text-center font-medium px-3 py-2.5">Status</th>
          <th class="text-right font-medium px-3 py-2.5">Target</th>
          <th class="text-right font-medium px-5 py-2.5">Trend</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in rows"
          :key="row.name"
          class="border-b border-[var(--card-border)] last:border-b-0 transition-colors hover:bg-[var(--color-tint)]"
        >
          <td class="px-5 py-3 text-sm font-medium text-[var(--color-text)]">
            {{ row.name }}
          </td>
          <td class="px-3 py-3 text-sm text-right font-semibold text-[var(--color-text)]">
            {{ row.value }}
          </td>
          <td class="px-3 py-3 text-center">
            <span
              class="inline-block w-2.5 h-2.5 rounded-full"
              :class="{
                'bg-[var(--color-success)]': row.status === 'green',
                'bg-[var(--color-warning)]': row.status === 'yellow',
                'bg-[var(--color-error)]': row.status === 'red',
              }"
            />
          </td>
          <td class="px-3 py-3 text-sm text-right text-[var(--color-text-muted)]">
            {{ row.target }}
          </td>
          <td class="px-5 py-3 text-right">
            <span
              class="inline-flex items-center gap-0.5 text-xs font-medium"
              :class="{
                'text-[var(--color-success)]': row.trendFavorable === true,
                'text-[var(--color-error)]': row.trendFavorable === false,
                'text-[var(--color-text-muted)]': row.trendFavorable === null,
              }"
            >
              <svg
                v-if="row.trend !== 0"
                class="w-3 h-3"
                :class="{ 'rotate-180': row.trend < 0 }"
                viewBox="0 0 12 12"
                fill="currentColor"
              >
                <path d="M6 2L10 7H2L6 2Z" />
              </svg>
              <span v-if="row.trend !== 0">
                {{ row.trend > 0 ? '+' : '' }}{{ Number.isInteger(row.trend) ? row.trend : row.trend.toFixed(1) }}
              </span>
              <span v-else>—</span>
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
