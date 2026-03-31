<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  columns: {
    type: Array,
    required: true,
    // Each: { key: string, label: string, sortable?: boolean, align?: 'left'|'right'|'center' }
  },
  rows: { type: Array, default: () => [] },
  title: { type: String, default: '' },
})

const filterText = ref('')
const sortKey = ref(null)
const sortDir = ref('asc') // 'asc' | 'desc'

function toggleSort(col) {
  if (!col.sortable) return
  if (sortKey.value === col.key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = col.key
    sortDir.value = 'asc'
  }
}

const filteredRows = computed(() => {
  let result = props.rows
  const q = filterText.value.trim().toLowerCase()
  if (q) {
    result = result.filter((row) =>
      props.columns.some((col) => {
        const val = row[col.key]
        return val != null && String(val).toLowerCase().includes(q)
      })
    )
  }
  if (sortKey.value) {
    const key = sortKey.value
    const dir = sortDir.value === 'asc' ? 1 : -1
    result = [...result].sort((a, b) => {
      const av = a[key] ?? ''
      const bv = b[key] ?? ''
      if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * dir
      return String(av).localeCompare(String(bv)) * dir
    })
  }
  return result
})

function exportCsv() {
  const header = props.columns.map((c) => c.label).join(',')
  const body = filteredRows.value
    .map((row) =>
      props.columns
        .map((c) => {
          const val = row[c.key] ?? ''
          const str = String(val)
          return str.includes(',') || str.includes('"') ? `"${str.replace(/"/g, '""')}"` : str
        })
        .join(',')
    )
    .join('\n')

  const csv = `${header}\n${body}`
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${props.title || 'report-data'}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function formatCell(value) {
  if (value == null) return '—'
  if (typeof value === 'number') {
    return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(2)
  }
  return value
}
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
    <!-- Header bar -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-4 border-b border-[var(--color-border)]">
      <h3 v-if="title" class="text-sm font-semibold text-[var(--color-text)]">{{ title }}</h3>
      <div class="flex items-center gap-2">
        <div class="relative">
          <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--color-text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            v-model="filterText"
            type="text"
            placeholder="Filter..."
            class="pl-8 pr-3 py-1.5 text-xs border border-[var(--color-border)] rounded-md bg-[var(--color-bg)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-[#2068FF] w-40"
          />
        </div>
        <button
          @click="exportCsv"
          class="flex items-center gap-1.5 text-xs font-medium text-[var(--color-text-secondary)] hover:text-[var(--color-text)] border border-[var(--color-border)] rounded-md px-2.5 py-1.5 transition-colors hover:bg-[var(--color-tint)]"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          CSV
        </button>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-[var(--color-border)]">
            <th
              v-for="col in columns"
              :key="col.key"
              class="px-4 py-2.5 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider select-none"
              :class="[
                col.sortable ? 'cursor-pointer hover:text-[var(--color-text)]' : '',
                col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left',
              ]"
              @click="toggleSort(col)"
            >
              <span class="inline-flex items-center gap-1">
                {{ col.label }}
                <span v-if="col.sortable && sortKey === col.key" class="text-[#2068FF]">
                  {{ sortDir === 'asc' ? '↑' : '↓' }}
                </span>
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, i) in filteredRows"
            :key="i"
            class="border-b border-[var(--color-border)] last:border-b-0 transition-colors hover:bg-[var(--color-tint)]"
          >
            <td
              v-for="col in columns"
              :key="col.key"
              class="px-4 py-2.5 text-[var(--color-text-secondary)]"
              :class="col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'"
            >
              {{ formatCell(row[col.key]) }}
            </td>
          </tr>
          <tr v-if="filteredRows.length === 0">
            <td :colspan="columns.length" class="px-4 py-8 text-center text-[var(--color-text-muted)] text-xs">
              {{ filterText ? 'No matching rows' : 'No data available' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Footer -->
    <div v-if="filteredRows.length > 0" class="px-4 py-2 border-t border-[var(--color-border)] text-xs text-[var(--color-text-muted)]">
      {{ filteredRows.length }} of {{ rows.length }} rows
    </div>
  </div>
</template>
