<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  dimensions: { type: Array, default: () => [] },
  simAName: { type: String, default: 'Sim A' },
  simBName: { type: String, default: 'Sim B' },
  summary: { type: Object, default: () => ({ winsA: 0, winsB: 0, ties: 0 }) },
})

const sortKey = ref(null)
const sortDir = ref('asc')

function toggleSort(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
}

const grouped = computed(() => {
  const cats = {}
  for (const d of props.dimensions) {
    if (!cats[d.category]) cats[d.category] = []
    cats[d.category].push(d)
  }
  return cats
})

const sortedDimensions = computed(() => {
  if (!sortKey.value) return props.dimensions
  const list = [...props.dimensions]
  list.sort((a, b) => {
    let va = a[sortKey.value]
    let vb = b[sortKey.value]
    if (typeof va === 'string') va = va.toLowerCase()
    if (typeof vb === 'string') vb = vb.toLowerCase()
    if (va < vb) return sortDir.value === 'asc' ? -1 : 1
    if (va > vb) return sortDir.value === 'asc' ? 1 : -1
    return 0
  })
  return list
})

function formatValue(val, format) {
  if (val == null) return '-'
  if (format === 'percent') return `${(val * 100).toFixed(0)}%`
  if (format === 'decimal') return val.toFixed(2)
  if (format === 'sentiment') return val >= 0 ? `+${val.toFixed(2)}` : val.toFixed(2)
  if (format === 'number') return val.toLocaleString()
  return String(val)
}

function winnerClasses(winner) {
  if (winner === 'A') return 'text-[#2068FF] font-semibold'
  if (winner === 'B') return 'text-[#ff5600] font-semibold'
  return 'text-[var(--color-text-muted)]'
}
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
    <!-- Summary bar -->
    <div class="flex items-center justify-between px-5 py-3 border-b border-[var(--color-border)] bg-[var(--color-tint)]">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Metrics Comparison</h3>
      <div class="flex items-center gap-4 text-xs">
        <span class="flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-[#2068FF]" />
          <span class="font-medium text-[#2068FF]">{{ summary.winsA }} wins</span>
        </span>
        <span class="text-[var(--color-text-muted)]">{{ summary.ties }} ties</span>
        <span class="flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-[#ff5600]" />
          <span class="font-medium text-[#ff5600]">{{ summary.winsB }} wins</span>
        </span>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-[var(--color-border)]">
            <th
              class="text-left px-5 py-2.5 text-xs font-medium text-[var(--color-text-muted)] cursor-pointer hover:text-[var(--color-text)]"
              @click="toggleSort('name')"
            >
              Metric
              <span v-if="sortKey === 'name'" class="ml-1">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="text-right px-4 py-2.5 text-xs font-medium text-[#2068FF]">{{ simAName }}</th>
            <th class="text-right px-4 py-2.5 text-xs font-medium text-[#ff5600]">{{ simBName }}</th>
            <th
              class="text-right px-4 py-2.5 text-xs font-medium text-[var(--color-text-muted)] cursor-pointer hover:text-[var(--color-text)]"
              @click="toggleSort('difference')"
            >
              Diff
              <span v-if="sortKey === 'difference'" class="ml-1">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
            </th>
            <th class="text-center px-4 py-2.5 text-xs font-medium text-[var(--color-text-muted)]">Winner</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="!sortKey">
            <template v-for="(metrics, category) in grouped" :key="category">
              <tr>
                <td colspan="5" class="px-5 pt-3 pb-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                  {{ category }}
                </td>
              </tr>
              <tr
                v-for="dim in metrics"
                :key="dim.key"
                class="border-b border-[var(--color-border)]/50 hover:bg-[var(--color-tint)] transition-colors"
              >
                <td class="px-5 py-2.5 text-[var(--color-text)]">{{ dim.name }}</td>
                <td class="text-right px-4 py-2.5 font-mono text-xs" :class="dim.winner === 'A' ? 'text-[#2068FF] font-semibold' : 'text-[var(--color-text-secondary)]'">
                  {{ formatValue(dim.simAValue, dim.format) }}
                </td>
                <td class="text-right px-4 py-2.5 font-mono text-xs" :class="dim.winner === 'B' ? 'text-[#ff5600] font-semibold' : 'text-[var(--color-text-secondary)]'">
                  {{ formatValue(dim.simBValue, dim.format) }}
                </td>
                <td class="text-right px-4 py-2.5 font-mono text-xs text-[var(--color-text-muted)]">
                  {{ dim.difference >= 0 ? '+' : '' }}{{ dim.format === 'percent' ? (dim.difference * 100).toFixed(0) + '%' : dim.difference.toFixed(2) }}
                </td>
                <td class="text-center px-4 py-2.5">
                  <span
                    v-if="dim.winner !== 'tie'"
                    class="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full"
                    :class="dim.winner === 'A' ? 'bg-[rgba(32,104,255,0.08)] text-[#2068FF]' : 'bg-[rgba(255,86,0,0.08)] text-[#ff5600]'"
                  >
                    {{ dim.winner }}
                    <span v-if="dim.significant" title="Statistically significant">*</span>
                  </span>
                  <span v-else class="text-xs text-[var(--color-text-muted)]">Tie</span>
                </td>
              </tr>
            </template>
          </template>
          <template v-else>
            <tr
              v-for="dim in sortedDimensions"
              :key="dim.key"
              class="border-b border-[var(--color-border)]/50 hover:bg-[var(--color-tint)] transition-colors"
            >
              <td class="px-5 py-2.5 text-[var(--color-text)]">
                <span class="text-[10px] text-[var(--color-text-muted)] mr-2">{{ dim.category }}</span>
                {{ dim.name }}
              </td>
              <td class="text-right px-4 py-2.5 font-mono text-xs" :class="dim.winner === 'A' ? 'text-[#2068FF] font-semibold' : 'text-[var(--color-text-secondary)]'">
                {{ formatValue(dim.simAValue, dim.format) }}
              </td>
              <td class="text-right px-4 py-2.5 font-mono text-xs" :class="dim.winner === 'B' ? 'text-[#ff5600] font-semibold' : 'text-[var(--color-text-secondary)]'">
                {{ formatValue(dim.simBValue, dim.format) }}
              </td>
              <td class="text-right px-4 py-2.5 font-mono text-xs text-[var(--color-text-muted)]">
                {{ dim.difference >= 0 ? '+' : '' }}{{ dim.format === 'percent' ? (dim.difference * 100).toFixed(0) + '%' : dim.difference.toFixed(2) }}
              </td>
              <td class="text-center px-4 py-2.5">
                <span :class="winnerClasses(dim.winner)" class="text-xs">
                  {{ dim.winner === 'tie' ? 'Tie' : dim.winner }}
                  <span v-if="dim.significant && dim.winner !== 'tie'">*</span>
                </span>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>
