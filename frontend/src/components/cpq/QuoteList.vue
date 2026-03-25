<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  quotes: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['select'])

const STATUSES = ['All', 'Draft', 'Review', 'Approved', 'Rejected']

const STATUS_VARIANTS = {
  Draft: { bg: 'bg-black/5', text: 'text-[--color-text-secondary]' },
  Review: { bg: 'bg-[--color-warning-light]', text: 'text-[--color-warning]' },
  Approved: { bg: 'bg-[--color-success-light]', text: 'text-[--color-success]' },
  Rejected: { bg: 'bg-[--color-error-light]', text: 'text-[--color-error]' },
}

const activeStatus = ref('All')
const sortKey = ref('created_at')
const sortDir = ref('desc')
const page = ref(1)
const pageSize = ref(10)

const statusCounts = computed(() => {
  const counts = { All: props.quotes.length }
  for (const s of STATUSES.slice(1)) {
    counts[s] = props.quotes.filter((q) => q.status === s).length
  }
  return counts
})

const filtered = computed(() => {
  if (activeStatus.value === 'All') return props.quotes
  return props.quotes.filter((q) => q.status === activeStatus.value)
})

const sorted = computed(() => {
  const key = sortKey.value
  const dir = sortDir.value === 'asc' ? 1 : -1
  return [...filtered.value].sort((a, b) => {
    const av = a[key]
    const bv = b[key]
    if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * dir
    return String(av).localeCompare(String(bv)) * dir
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(sorted.value.length / pageSize.value)))

const paginated = computed(() => {
  const start = (page.value - 1) * pageSize.value
  return sorted.value.slice(start, start + pageSize.value)
})

function toggleSort(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = key === 'total' ? 'desc' : 'asc'
  }
  page.value = 1
}

function setStatus(status) {
  activeStatus.value = status
  page.value = 1
}

function setPageSize(size) {
  pageSize.value = size
  page.value = 1
}

function isExpired(quote) {
  if (!quote.expiry) return false
  return new Date(quote.expiry) < new Date()
}

function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }).format(value)
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function truncateProducts(products) {
  if (!products || products.length === 0) return '-'
  const shown = products.slice(0, 2).join(', ')
  return products.length > 2 ? `${shown} +${products.length - 2}` : shown
}

function sortIcon(key) {
  if (sortKey.value !== key) return 'none'
  return sortDir.value
}

const SORTABLE_COLUMNS = [
  { key: 'quote_number', label: 'Quote #', sortable: true },
  { key: 'account', label: 'Account', sortable: true },
  { key: 'status', label: 'Status', sortable: false },
  { key: 'products', label: 'Products', sortable: false },
  { key: 'total', label: 'Total', sortable: true },
  { key: 'created_at', label: 'Created', sortable: true },
  { key: 'expiry', label: 'Expiry', sortable: true },
]
</script>

<template>
  <div>
    <!-- Status filter chips -->
    <div class="flex flex-wrap gap-2 mb-4">
      <button
        v-for="status in STATUSES"
        :key="status"
        :class="[
          'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-colors cursor-pointer',
          activeStatus === status
            ? 'bg-[--color-primary] text-white'
            : 'bg-[--color-tint] text-[--color-text-secondary] hover:bg-[--color-primary-light] hover:text-[--color-primary]',
        ]"
        @click="setStatus(status)"
      >
        {{ status }}
        <span
          :class="[
            'inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1 rounded-full text-[10px]',
            activeStatus === status
              ? 'bg-white/20 text-white'
              : 'bg-black/5 text-[--color-text-muted]',
          ]"
        >
          {{ statusCounts[status] }}
        </span>
      </button>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto border border-[--color-border] rounded-lg">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-[--color-border] bg-[--color-tint]">
            <th
              v-for="col in SORTABLE_COLUMNS"
              :key="col.key"
              :class="[
                'px-4 py-3 text-left font-semibold text-[--color-text-secondary] text-xs uppercase tracking-wide',
                col.sortable && 'cursor-pointer select-none hover:text-[--color-text]',
              ]"
              @click="col.sortable && toggleSort(col.key)"
            >
              <span class="inline-flex items-center gap-1">
                {{ col.label }}
                <svg
                  v-if="col.sortable"
                  class="w-3.5 h-3.5 shrink-0"
                  :class="sortIcon(col.key) === 'none' ? 'opacity-30' : 'opacity-100'"
                  viewBox="0 0 14 14"
                  fill="currentColor"
                >
                  <path
                    v-if="sortIcon(col.key) !== 'desc'"
                    d="M7 2L11 6H3L7 2Z"
                    :opacity="sortIcon(col.key) === 'asc' ? 1 : 0.3"
                  />
                  <path
                    v-if="sortIcon(col.key) !== 'asc'"
                    d="M7 12L3 8H11L7 12Z"
                    :opacity="sortIcon(col.key) === 'desc' ? 1 : 0.3"
                  />
                </svg>
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="quote in paginated"
            :key="quote.id"
            :class="[
              'border-b border-[--color-border] last:border-b-0 cursor-pointer transition-colors',
              isExpired(quote)
                ? 'bg-[--color-error-light] hover:bg-red-100'
                : 'hover:bg-[--color-tint]',
            ]"
            @click="emit('select', quote.id)"
          >
            <td class="px-4 py-3 font-medium text-[--color-primary]">
              {{ quote.quote_number }}
            </td>
            <td class="px-4 py-3 text-[--color-text]">
              {{ quote.account }}
            </td>
            <td class="px-4 py-3">
              <span
                :class="[
                  'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold',
                  STATUS_VARIANTS[quote.status]?.bg,
                  STATUS_VARIANTS[quote.status]?.text,
                ]"
              >
                {{ quote.status }}
              </span>
            </td>
            <td class="px-4 py-3 text-[--color-text-secondary] max-w-[200px] truncate">
              {{ truncateProducts(quote.products) }}
            </td>
            <td class="px-4 py-3 font-semibold text-[--color-text] tabular-nums">
              {{ formatCurrency(quote.total) }}
            </td>
            <td class="px-4 py-3 text-[--color-text-secondary] tabular-nums">
              {{ formatDate(quote.created_at) }}
            </td>
            <td
              class="px-4 py-3 tabular-nums"
              :class="isExpired(quote) ? 'text-[--color-error] font-medium' : 'text-[--color-text-secondary]'"
            >
              {{ formatDate(quote.expiry) }}
            </td>
          </tr>
          <tr v-if="paginated.length === 0">
            <td colspan="7" class="px-4 py-8 text-center text-[--color-text-muted]">
              No quotes found
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="flex items-center justify-between mt-4 text-sm">
      <div class="flex items-center gap-2 text-[--color-text-secondary]">
        <span>Show</span>
        <select
          :value="pageSize"
          class="bg-[--color-surface] border border-[--color-border] rounded-md px-2 py-1 text-sm text-[--color-text] cursor-pointer"
          @change="setPageSize(Number($event.target.value))"
        >
          <option :value="10">10</option>
          <option :value="25">25</option>
          <option :value="50">50</option>
        </select>
        <span>per page</span>
      </div>

      <div class="flex items-center gap-1">
        <span class="text-[--color-text-secondary] mr-2">
          {{ Math.min((page - 1) * pageSize + 1, sorted.length) }}-{{ Math.min(page * pageSize, sorted.length) }}
          of {{ sorted.length }}
        </span>
        <button
          :disabled="page <= 1"
          class="p-1.5 rounded-md hover:bg-[--color-tint] disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-colors"
          @click="page--"
        >
          <svg class="w-4 h-4" viewBox="0 0 16 16" fill="currentColor">
            <path d="M10.354 3.354a.5.5 0 00-.708-.708l-5 5a.5.5 0 000 .708l5 5a.5.5 0 00.708-.708L5.707 8l4.647-4.646z" />
          </svg>
        </button>
        <button
          :disabled="page >= totalPages"
          class="p-1.5 rounded-md hover:bg-[--color-tint] disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-colors"
          @click="page++"
        >
          <svg class="w-4 h-4" viewBox="0 0 16 16" fill="currentColor">
            <path d="M5.646 3.354a.5.5 0 01.708-.708l5 5a.5.5 0 010 .708l-5 5a.5.5 0 01-.708-.708L10.293 8 5.646 3.354z" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>
