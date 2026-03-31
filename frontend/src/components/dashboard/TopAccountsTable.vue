<script setup>
import { ref, computed, onMounted } from 'vue'
import { dashboardApi } from '../../api/dashboard'
import { useLocale } from '../../composables/useLocale'
import LoadingSpinner from '../ui/LoadingSpinner.vue'
import EmptyState from '../ui/EmptyState.vue'

const { formatDate: fmtDate } = useLocale()

const accounts = ref([])
const meta = ref({ total: 0, max_arr: 1, total_arr: 0, total_pipeline: 0 })
const loading = ref(true)
const error = ref(null)
const search = ref('')
const sortField = ref('arr')
const sortOrder = ref('desc')

const filteredAccounts = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return accounts.value
  return accounts.value.filter(
    (a) =>
      a.name.toLowerCase().includes(q) ||
      a.industry.toLowerCase().includes(q) ||
      a.plan.toLowerCase().includes(q),
  )
})

const sortedAccounts = computed(() => {
  const list = [...filteredAccounts.value]
  const field = sortField.value
  const desc = sortOrder.value === 'desc'

  list.sort((a, b) => {
    const va = a[field]
    const vb = b[field]
    if (typeof va === 'string') {
      return desc ? vb.localeCompare(va) : va.localeCompare(vb)
    }
    return desc ? vb - va : va - vb
  })

  return list
})

const summaryArr = computed(() =>
  sortedAccounts.value.reduce((sum, a) => sum + a.arr, 0),
)
const summaryPipeline = computed(() =>
  sortedAccounts.value.reduce((sum, a) => sum + a.pipeline, 0),
)

function toggleSort(field) {
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
  } else {
    sortField.value = field
    sortOrder.value = field === 'name' ? 'asc' : 'desc'
  }
}

function sortIcon(field) {
  if (sortField.value !== field) return ''
  return sortOrder.value === 'asc' ? '\u25B2' : '\u25BC'
}

function formatCurrency(val) {
  if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`
  if (val >= 1000) return `$${(val / 1000).toFixed(0)}K`
  return `$${val}`
}

function formatDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00')
  return fmtDate(d, { month: 'short', day: 'numeric', year: 'numeric' })
}

function healthColor(score) {
  if (score >= 70) return '#009900'
  if (score >= 40) return '#f59e0b'
  return '#ef4444'
}

function arrBarWidth(arr) {
  return `${(arr / meta.value.max_arr) * 100}%`
}

function isAtRisk(account) {
  return account.health_score < 40
}

async function fetchAccounts() {
  loading.value = true
  error.value = null
  try {
    const { data } = await dashboardApi.getTopAccounts()
    accounts.value = data.accounts
    meta.value = data.meta
  } catch (e) {
    error.value = e.message || 'Failed to load accounts'
  } finally {
    loading.value = false
  }
}

onMounted(fetchAccounts)

const columns = [
  { key: 'rank', label: '#', width: 'w-10' },
  { key: 'name', label: 'Account Name', width: 'min-w-[160px]' },
  { key: 'arr', label: 'ARR', width: 'w-[140px]' },
  { key: 'plan', label: 'Plan', width: 'w-[100px]' },
  { key: 'health_score', label: 'Health', width: 'w-[120px]' },
  { key: 'pipeline', label: 'Pipeline', width: 'w-[100px]' },
  { key: 'last_activity', label: 'Last Activity', width: 'w-[120px]' },
  { key: 'renewal_date', label: 'Renewal', width: 'w-[120px]' },
]
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between px-6 py-4 border-b border-[var(--color-border)]">
      <h3 class="text-base font-semibold text-[var(--color-text)]">Top Accounts</h3>
      <div class="relative">
        <input
          v-model="search"
          type="text"
          placeholder="Search accounts..."
          class="w-56 pl-8 pr-3 py-1.5 text-sm rounded-md border border-[var(--color-border)] bg-[var(--color-bg)]
                 text-[var(--color-text)] placeholder-[var(--color-text-muted)]
                 focus:outline-none focus:border-[#2068FF] focus:ring-1 focus:ring-[rgba(32,104,255,0.3)]"
        />
        <svg
          class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--color-text-muted)]"
          fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
    </div>

    <!-- Loading -->
    <LoadingSpinner v-if="loading" label="Loading accounts..." />

    <!-- Error -->
    <EmptyState
      v-else-if="error"
      icon="!"
      title="Failed to load accounts"
      :description="error"
      action-label="Retry"
      @action="fetchAccounts"
    />

    <!-- Empty search result -->
    <EmptyState
      v-else-if="sortedAccounts.length === 0"
      title="No accounts found"
      description="Try adjusting your search query."
    />

    <!-- Table -->
    <div v-else class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-[var(--color-border)] bg-[var(--color-bg)]">
            <th
              v-for="col in columns"
              :key="col.key"
              :class="[
                col.width,
                'px-4 py-2.5 text-left text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider cursor-pointer select-none hover:text-[var(--color-text)]',
              ]"
              @click="toggleSort(col.key)"
            >
              <span class="inline-flex items-center gap-1">
                {{ col.label }}
                <span v-if="sortIcon(col.key)" class="text-[10px] text-[#2068FF]">{{ sortIcon(col.key) }}</span>
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="account in sortedAccounts"
            :key="account.name"
            :class="[
              'border-b border-[var(--color-border)] last:border-b-0 transition-colors cursor-pointer',
              isAtRisk(account)
                ? 'bg-[rgba(239,68,68,0.04)] hover:bg-[rgba(239,68,68,0.08)]'
                : 'hover:bg-[var(--color-bg)]',
            ]"
          >
            <!-- Rank -->
            <td class="px-4 py-3 text-[var(--color-text-muted)] font-mono text-xs">
              {{ account.rank }}
            </td>

            <!-- Account Name -->
            <td class="px-4 py-3">
              <div class="font-medium text-[var(--color-text)]">{{ account.name }}</div>
              <div class="text-xs text-[var(--color-text-muted)]">{{ account.industry }}</div>
            </td>

            <!-- ARR with mini bar -->
            <td class="px-4 py-3">
              <div class="font-medium text-[var(--color-text)]">{{ formatCurrency(account.arr) }}</div>
              <div class="mt-1 h-1 rounded-full bg-[var(--color-border)] overflow-hidden">
                <div
                  class="h-full rounded-full bg-[#2068FF]"
                  :style="{ width: arrBarWidth(account.arr) }"
                />
              </div>
            </td>

            <!-- Plan -->
            <td class="px-4 py-3">
              <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-[rgba(32,104,255,0.08)] text-[#2068FF]">
                {{ account.plan }}
              </span>
            </td>

            <!-- Health Score -->
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <div class="flex-1 h-2 rounded-full bg-[var(--color-border)] overflow-hidden max-w-[60px]">
                  <div
                    class="h-full rounded-full transition-all"
                    :style="{
                      width: account.health_score + '%',
                      backgroundColor: healthColor(account.health_score),
                    }"
                  />
                </div>
                <span
                  class="text-xs font-medium min-w-[28px]"
                  :style="{ color: healthColor(account.health_score) }"
                >
                  {{ account.health_score }}
                </span>
              </div>
            </td>

            <!-- Pipeline -->
            <td class="px-4 py-3 text-[var(--color-text)]">
              {{ formatCurrency(account.pipeline) }}
            </td>

            <!-- Last Activity -->
            <td class="px-4 py-3 text-xs text-[var(--color-text-muted)]">
              {{ formatDate(account.last_activity) }}
            </td>

            <!-- Renewal Date -->
            <td class="px-4 py-3 text-xs text-[var(--color-text-muted)]">
              {{ formatDate(account.renewal_date) }}
            </td>
          </tr>
        </tbody>

        <!-- Footer summary -->
        <tfoot>
          <tr class="border-t border-[var(--color-border)] bg-[var(--color-bg)]">
            <td class="px-4 py-3" />
            <td class="px-4 py-3 text-xs font-semibold text-[var(--color-text)]">
              Total ({{ sortedAccounts.length }} accounts)
            </td>
            <td class="px-4 py-3 text-sm font-semibold text-[var(--color-text)]">
              {{ formatCurrency(summaryArr) }}
            </td>
            <td class="px-4 py-3" />
            <td class="px-4 py-3" />
            <td class="px-4 py-3 text-sm font-semibold text-[var(--color-text)]">
              {{ formatCurrency(summaryPipeline) }}
            </td>
            <td class="px-4 py-3" />
            <td class="px-4 py-3" />
          </tr>
        </tfoot>
      </table>
    </div>
  </div>
</template>
