<script setup>
import { ref, computed } from 'vue'

const COLORS = {
  a: '#2068FF',
  b: '#ff5600',
  tie: '#888',
}

const DEFAULT_METRICS = [
  // Engagement
  { category: 'Engagement', name: 'Total Actions', valueA: 1224, valueB: 1087, format: 'number', significant: true },
  { category: 'Engagement', name: 'Twitter Actions', valueA: 673, valueB: 554, format: 'number', significant: true },
  { category: 'Engagement', name: 'Reddit Actions', valueA: 551, valueB: 533, format: 'number', significant: false },
  { category: 'Engagement', name: 'Avg. Actions/Agent', valueA: 81.6, valueB: 72.5, format: 'decimal', significant: true },
  { category: 'Engagement', name: 'Active Agents', valueA: 15, valueB: 14, format: 'number', significant: false },
  // Sentiment
  { category: 'Sentiment', name: 'Positive Sentiment', valueA: 62.4, valueB: 58.1, format: 'percent', significant: false },
  { category: 'Sentiment', name: 'Negative Sentiment', valueA: 8.2, valueB: 12.7, format: 'percent', lowerWins: true, significant: true },
  { category: 'Sentiment', name: 'Sentiment Score', valueA: 0.72, valueB: 0.61, format: 'score', significant: true },
  { category: 'Sentiment', name: 'Sentiment Volatility', valueA: 0.14, valueB: 0.23, format: 'score', lowerWins: true, significant: true },
  // Outcomes
  { category: 'Outcomes', name: 'Consensus Events', valueA: 18, valueB: 14, format: 'number', significant: true },
  { category: 'Outcomes', name: 'Decision Points', valueA: 24, valueB: 21, format: 'number', significant: false },
  { category: 'Outcomes', name: 'Influence Cascades', valueA: 8, valueB: 11, format: 'number', significant: true },
  { category: 'Outcomes', name: 'Competitive Mentions', valueA: 42, valueB: 37, format: 'number', significant: false },
  // Efficiency
  { category: 'Efficiency', name: 'Simulated Hours', valueA: 72, valueB: 72, format: 'number', significant: false },
  { category: 'Efficiency', name: 'Avg. Response Time (min)', valueA: 14.2, valueB: 18.7, format: 'decimal', lowerWins: true, significant: true },
  { category: 'Efficiency', name: 'Cross-Platform Rate', valueA: 34.8, valueB: 29.1, format: 'percent', significant: true },
]

const props = defineProps({
  labelA: { type: String, default: 'Simulation A' },
  labelB: { type: String, default: 'Simulation B' },
  metrics: {
    type: Array,
    default: () => DEFAULT_METRICS,
    validator: (v) => v.every((m) => m.category && m.name && 'valueA' in m && 'valueB' in m),
  },
})

const sortKey = ref(null)
const sortAsc = ref(true)

function toggleSort(key) {
  if (sortKey.value === key) {
    sortAsc.value = !sortAsc.value
  } else {
    sortKey.value = key
    sortAsc.value = key === 'name' || key === 'category'
  }
}

function computeWinner(metric) {
  const { valueA, valueB, lowerWins } = metric
  if (valueA === valueB) return 'tie'
  if (lowerWins) return valueA < valueB ? 'a' : 'b'
  return valueA > valueB ? 'a' : 'b'
}

function computeDiff(metric) {
  return metric.valueA - metric.valueB
}

const categories = computed(() => {
  const seen = new Set()
  return props.metrics.reduce((acc, m) => {
    if (!seen.has(m.category)) {
      seen.add(m.category)
      acc.push(m.category)
    }
    return acc
  }, [])
})

const enrichedMetrics = computed(() =>
  props.metrics.map((m) => ({
    ...m,
    winner: computeWinner(m),
    diff: computeDiff(m),
  })),
)

const sortedMetrics = computed(() => {
  if (!sortKey.value) return enrichedMetrics.value

  const sorted = [...enrichedMetrics.value]
  const key = sortKey.value
  const dir = sortAsc.value ? 1 : -1

  sorted.sort((a, b) => {
    let va, vb
    if (key === 'name' || key === 'category' || key === 'winner') {
      va = a[key]
      vb = b[key]
      return va.localeCompare(vb) * dir
    }
    if (key === 'diff') {
      va = Math.abs(a.diff)
      vb = Math.abs(b.diff)
    } else {
      va = a[key] ?? 0
      vb = b[key] ?? 0
    }
    return (va - vb) * dir
  })
  return sorted
})

const groupedMetrics = computed(() => {
  if (sortKey.value && sortKey.value !== 'category') {
    return [{ category: null, rows: sortedMetrics.value }]
  }
  return categories.value.map((cat) => ({
    category: cat,
    rows: sortedMetrics.value.filter((m) => m.category === cat),
  }))
})

const summary = computed(() => {
  let winsA = 0
  let winsB = 0
  let ties = 0
  for (const m of enrichedMetrics.value) {
    if (m.winner === 'a') winsA++
    else if (m.winner === 'b') winsB++
    else ties++
  }
  return { winsA, winsB, ties, total: enrichedMetrics.value.length }
})

function formatValue(value, format) {
  if (value == null) return '—'
  switch (format) {
    case 'percent':
      return `${value.toFixed(1)}%`
    case 'decimal':
      return value.toFixed(1)
    case 'score':
      return value.toFixed(2)
    default:
      return value.toLocaleString()
  }
}

function formatDiff(diff, format) {
  const absDiff = Math.abs(diff)
  const sign = diff > 0 ? '+' : diff < 0 ? '-' : ''
  let formatted
  switch (format) {
    case 'percent':
      formatted = `${absDiff.toFixed(1)}pp`
      break
    case 'decimal':
      formatted = absDiff.toFixed(1)
      break
    case 'score':
      formatted = absDiff.toFixed(2)
      break
    default:
      formatted = absDiff.toLocaleString()
  }
  return diff === 0 ? '—' : `${sign}${formatted}`
}

function winnerColor(winner) {
  return COLORS[winner] || COLORS.tie
}

function winnerLabel(winner) {
  if (winner === 'a') return 'A'
  if (winner === 'b') return 'B'
  return 'Tie'
}

function sortIndicator(key) {
  if (sortKey.value !== key) return ''
  return sortAsc.value ? ' \u25B2' : ' \u25BC'
}
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
    <!-- Header -->
    <div class="px-4 md:px-6 py-4 border-b border-[var(--color-border)]">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Comparison Metrics</h3>
      <p class="text-xs text-[var(--color-text-muted)] mt-0.5">
        Side-by-side performance across {{ summary.total }} metrics
      </p>
    </div>

    <!-- Summary bar -->
    <div class="px-4 md:px-6 py-3 bg-[var(--color-tint)] border-b border-[var(--color-border)] flex items-center gap-4 text-xs">
      <div class="flex items-center gap-1.5">
        <span
          class="inline-block w-2.5 h-2.5 rounded-sm"
          :style="{ backgroundColor: COLORS.a }"
        />
        <span class="font-medium text-[var(--color-text)]">{{ labelA }}</span>
        <span class="font-semibold" :style="{ color: COLORS.a }">{{ summary.winsA }} wins</span>
      </div>
      <div class="flex items-center gap-1.5">
        <span
          class="inline-block w-2.5 h-2.5 rounded-sm"
          :style="{ backgroundColor: COLORS.b }"
        />
        <span class="font-medium text-[var(--color-text)]">{{ labelB }}</span>
        <span class="font-semibold" :style="{ color: COLORS.b }">{{ summary.winsB }} wins</span>
      </div>
      <div v-if="summary.ties > 0" class="flex items-center gap-1.5 text-[var(--color-text-muted)]">
        <span
          class="inline-block w-2.5 h-2.5 rounded-sm"
          :style="{ backgroundColor: COLORS.tie }"
        />
        {{ summary.ties }} tied
      </div>

      <!-- Win bar -->
      <div class="ml-auto hidden sm:flex items-center gap-2 min-w-[120px]">
        <div class="flex-1 h-1.5 rounded-full overflow-hidden flex" style="background: rgba(0,0,0,0.06)">
          <div
            class="h-full transition-all duration-300"
            :style="{ width: `${(summary.winsA / summary.total) * 100}%`, backgroundColor: COLORS.a }"
          />
          <div
            class="h-full transition-all duration-300"
            :style="{ width: `${(summary.ties / summary.total) * 100}%`, backgroundColor: COLORS.tie }"
          />
          <div
            class="h-full transition-all duration-300"
            :style="{ width: `${(summary.winsB / summary.total) * 100}%`, backgroundColor: COLORS.b }"
          />
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-[var(--color-border)]">
            <th
              class="text-left px-4 md:px-6 py-2.5 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider cursor-pointer select-none hover:text-[var(--color-text)]"
              @click="toggleSort('name')"
            >
              Metric{{ sortIndicator('name') }}
            </th>
            <th
              class="text-right px-3 py-2.5 text-xs font-semibold uppercase tracking-wider cursor-pointer select-none hover:text-[var(--color-text)]"
              :style="{ color: COLORS.a }"
              @click="toggleSort('valueA')"
            >
              {{ labelA }}{{ sortIndicator('valueA') }}
            </th>
            <th
              class="text-right px-3 py-2.5 text-xs font-semibold uppercase tracking-wider cursor-pointer select-none hover:text-[var(--color-text)]"
              :style="{ color: COLORS.b }"
              @click="toggleSort('valueB')"
            >
              {{ labelB }}{{ sortIndicator('valueB') }}
            </th>
            <th
              class="text-right px-3 py-2.5 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider cursor-pointer select-none hover:text-[var(--color-text)]"
              @click="toggleSort('diff')"
            >
              Diff{{ sortIndicator('diff') }}
            </th>
            <th
              class="text-center px-3 py-2.5 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider cursor-pointer select-none hover:text-[var(--color-text)]"
              @click="toggleSort('winner')"
            >
              Winner{{ sortIndicator('winner') }}
            </th>
            <th class="text-center px-3 md:px-4 py-2.5 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">
              Sig.
            </th>
          </tr>
        </thead>
        <tbody>
          <template v-for="group in groupedMetrics" :key="group.category || 'all'">
            <!-- Category header row -->
            <tr v-if="group.category" class="bg-[var(--color-tint)]">
              <td
                colspan="6"
                class="px-4 md:px-6 py-2 text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wider"
              >
                {{ group.category }}
              </td>
            </tr>

            <tr
              v-for="row in group.rows"
              :key="row.name"
              class="border-b border-[var(--color-border)] last:border-b-0 hover:bg-[var(--color-tint)] transition-colors"
            >
              <!-- Metric name -->
              <td class="px-4 md:px-6 py-2.5 text-[var(--color-text)]" :class="{ 'font-semibold': row.significant }">
                {{ row.name }}
              </td>
              <!-- Value A -->
              <td class="text-right px-3 py-2.5 tabular-nums" :class="{ 'font-semibold': row.winner === 'a' && row.significant }" :style="row.winner === 'a' ? { color: COLORS.a } : {}">
                {{ formatValue(row.valueA, row.format) }}
              </td>
              <!-- Value B -->
              <td class="text-right px-3 py-2.5 tabular-nums" :class="{ 'font-semibold': row.winner === 'b' && row.significant }" :style="row.winner === 'b' ? { color: COLORS.b } : {}">
                {{ formatValue(row.valueB, row.format) }}
              </td>
              <!-- Difference -->
              <td class="text-right px-3 py-2.5 text-[var(--color-text-muted)] tabular-nums text-xs">
                {{ formatDiff(row.diff, row.format) }}
              </td>
              <!-- Winner -->
              <td class="text-center px-3 py-2.5">
                <span
                  class="inline-flex items-center justify-center w-6 h-6 rounded-full text-white text-xs font-bold"
                  :style="{ backgroundColor: winnerColor(row.winner) }"
                >
                  {{ winnerLabel(row.winner) }}
                </span>
              </td>
              <!-- Significance -->
              <td class="text-center px-3 md:px-4 py-2.5">
                <span v-if="row.significant" class="text-[var(--color-primary)] font-bold text-xs">***</span>
                <span v-else class="text-[var(--color-text-muted)] text-xs">ns</span>
              </td>
            </tr>
          </template>
        </tbody>
        <!-- Summary footer -->
        <tfoot>
          <tr class="border-t-2 border-[var(--color-border)] bg-[var(--color-tint)]">
            <td class="px-4 md:px-6 py-3 font-semibold text-[var(--color-text)]">Overall Score</td>
            <td class="text-right px-3 py-3 font-bold" :style="{ color: COLORS.a }">
              {{ summary.winsA }} / {{ summary.total }}
            </td>
            <td class="text-right px-3 py-3 font-bold" :style="{ color: COLORS.b }">
              {{ summary.winsB }} / {{ summary.total }}
            </td>
            <td class="text-right px-3 py-3 text-xs text-[var(--color-text-muted)]">
              {{ summary.ties > 0 ? `${summary.ties} tied` : '' }}
            </td>
            <td class="text-center px-3 py-3">
              <span
                class="inline-flex items-center justify-center w-6 h-6 rounded-full text-white text-xs font-bold"
                :style="{
                  backgroundColor: summary.winsA > summary.winsB ? COLORS.a : summary.winsB > summary.winsA ? COLORS.b : COLORS.tie,
                }"
              >
                {{ summary.winsA > summary.winsB ? 'A' : summary.winsB > summary.winsA ? 'B' : '=' }}
              </span>
            </td>
            <td />
          </tr>
        </tfoot>
      </table>
    </div>
  </div>
</template>
