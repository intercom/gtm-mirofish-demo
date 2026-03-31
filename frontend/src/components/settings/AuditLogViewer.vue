<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { auditLogApi } from '../../api/auditLog'
import { useToast } from '../../composables/useToast'
import { AppBadge as Badge } from '../common'

const toast = useToast()

const logs = ref([])
const total = ref(0)
const actionTypes = ref([])
const loading = ref(false)
const error = ref(null)

// Filters
const filterAction = ref('')
const filterUser = ref('')
const filterSearch = ref('')
const filterSince = ref('')
const filterUntil = ref('')
const page = ref(0)
const limit = 25

// View mode: 'table' | 'timeline'
const viewMode = ref('table')

const filterParams = computed(() => {
  const p = {}
  if (filterAction.value) p.action = filterAction.value
  if (filterUser.value) p.user = filterUser.value
  if (filterSearch.value) p.search = filterSearch.value
  if (filterSince.value) p.since = new Date(filterSince.value).toISOString()
  if (filterUntil.value) p.until = new Date(filterUntil.value + 'T23:59:59').toISOString()
  return p
})

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / limit)))
const hasFilters = computed(() =>
  filterAction.value || filterUser.value || filterSearch.value ||
  filterSince.value || filterUntil.value
)

// Group logs by date for timeline view
const groupedLogs = computed(() => {
  const groups = {}
  for (const log of logs.value) {
    const day = log.timestamp.slice(0, 10)
    if (!groups[day]) groups[day] = []
    groups[day].push(log)
  }
  return Object.entries(groups).sort(([a], [b]) => b.localeCompare(a))
})

async function fetchLogs() {
  loading.value = true
  error.value = null
  try {
    const res = await auditLogApi.getLogs({
      ...filterParams.value,
      limit,
      offset: page.value * limit,
    })
    const d = res.data?.data || res.data
    logs.value = d.logs || []
    total.value = d.total || 0
    actionTypes.value = d.action_types || []
  } catch (e) {
    error.value = e.message || 'Failed to load audit logs'
    toast.error('Failed to load audit logs')
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filterAction.value = ''
  filterUser.value = ''
  filterSearch.value = ''
  filterSince.value = ''
  filterUntil.value = ''
  page.value = 0
}

function exportCsv() {
  const url = auditLogApi.getExportUrl(filterParams.value)
  window.open(url, '_blank')
}

function formatTime(iso) {
  const d = new Date(iso)
  return d.toLocaleString(undefined, {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function formatDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00')
  const today = new Date().toISOString().slice(0, 10)
  const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10)
  if (dateStr === today) return 'Today'
  if (dateStr === yesterday) return 'Yesterday'
  return d.toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })
}

const actionBadgeVariant = {
  login: 'primary',
  logout: 'default',
  simulation_created: 'success',
  simulation_deleted: 'error',
  report_generated: 'info',
  graph_built: 'success',
  settings_updated: 'warning',
  role_changed: 'orange',
  user_removed: 'error',
  key_created: 'primary',
  key_revoked: 'warning',
  permission_denied: 'error',
}

function badgeVariant(action) {
  return actionBadgeVariant[action] || 'default'
}

function formatAction(action) {
  return action.replace(/_/g, ' ')
}

// Reset page when filters change
watch([filterAction, filterUser, filterSearch, filterSince, filterUntil], () => {
  page.value = 0
  fetchLogs()
})

watch(page, fetchLogs)

onMounted(fetchLogs)
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
      <h2 class="text-sm font-semibold text-[var(--color-text)]">Security & Audit Log</h2>
      <div class="flex items-center gap-2">
        <!-- View toggle -->
        <div class="flex rounded-lg border border-[var(--color-border)] overflow-hidden">
          <button
            @click="viewMode = 'table'"
            class="px-3 py-1.5 text-xs font-medium transition-colors cursor-pointer"
            :class="viewMode === 'table'
              ? 'bg-[var(--color-primary)] text-white'
              : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-primary-light)]'"
          >Table</button>
          <button
            @click="viewMode = 'timeline'"
            class="px-3 py-1.5 text-xs font-medium transition-colors cursor-pointer"
            :class="viewMode === 'timeline'
              ? 'bg-[var(--color-primary)] text-white'
              : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-primary-light)]'"
          >Timeline</button>
        </div>
        <!-- Export -->
        <button
          @click="exportCsv"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border border-[var(--color-border)] rounded-lg text-[var(--color-text-secondary)] hover:bg-[var(--color-primary-light)] transition-colors cursor-pointer"
        >
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Export CSV
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-2 mb-4">
      <select
        v-model="filterAction"
        class="border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] rounded-lg px-3 py-1.5 text-xs focus:ring-2 focus:ring-[#2068FF]"
      >
        <option value="">All actions</option>
        <option v-for="a in actionTypes" :key="a" :value="a">{{ formatAction(a) }}</option>
      </select>
      <input
        v-model="filterUser"
        type="text"
        placeholder="Filter by user..."
        class="border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] rounded-lg px-3 py-1.5 text-xs focus:ring-2 focus:ring-[#2068FF] w-40"
      />
      <input
        v-model="filterSearch"
        type="text"
        placeholder="Search details..."
        class="border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] rounded-lg px-3 py-1.5 text-xs focus:ring-2 focus:ring-[#2068FF] w-40"
      />
      <input
        v-model="filterSince"
        type="date"
        class="border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] rounded-lg px-3 py-1.5 text-xs focus:ring-2 focus:ring-[#2068FF]"
      />
      <input
        v-model="filterUntil"
        type="date"
        class="border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] rounded-lg px-3 py-1.5 text-xs focus:ring-2 focus:ring-[#2068FF]"
      />
      <button
        v-if="hasFilters"
        @click="resetFilters"
        class="px-3 py-1.5 text-xs text-[var(--color-primary)] hover:underline cursor-pointer"
      >Clear filters</button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="py-12 text-center text-sm text-[var(--color-text-muted)]">
      Loading audit logs...
    </div>

    <!-- Error -->
    <div v-else-if="error" class="py-12 text-center text-sm text-[var(--color-error)]">
      {{ error }}
    </div>

    <!-- Empty -->
    <div v-else-if="logs.length === 0" class="py-12 text-center text-sm text-[var(--color-text-muted)]">
      No audit log entries found.
    </div>

    <!-- Table View -->
    <div v-else-if="viewMode === 'table'" class="overflow-x-auto rounded-lg border border-[var(--color-border)]">
      <table class="w-full text-xs">
        <thead>
          <tr class="bg-[var(--color-surface)] border-b border-[var(--color-border)]">
            <th class="text-left px-3 py-2.5 font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Time</th>
            <th class="text-left px-3 py-2.5 font-medium text-[var(--color-text-muted)] uppercase tracking-wider">User</th>
            <th class="text-left px-3 py-2.5 font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Action</th>
            <th class="text-left px-3 py-2.5 font-medium text-[var(--color-text-muted)] uppercase tracking-wider hidden md:table-cell">Resource</th>
            <th class="text-left px-3 py-2.5 font-medium text-[var(--color-text-muted)] uppercase tracking-wider hidden lg:table-cell">Details</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="log in logs"
            :key="log.id"
            class="border-b border-[var(--color-border)] last:border-b-0 hover:bg-[var(--color-primary-light)] transition-colors"
          >
            <td class="px-3 py-2.5 text-[var(--color-text-secondary)] whitespace-nowrap">{{ formatTime(log.timestamp) }}</td>
            <td class="px-3 py-2.5 text-[var(--color-text)] font-medium whitespace-nowrap">{{ log.actor }}</td>
            <td class="px-3 py-2.5">
              <Badge :variant="badgeVariant(log.action)">{{ formatAction(log.action) }}</Badge>
            </td>
            <td class="px-3 py-2.5 text-[var(--color-text-secondary)] hidden md:table-cell">
              <span v-if="log.resource_type">{{ log.resource_type }}</span>
              <span v-if="log.resource_id" class="text-[var(--color-text-muted)] ml-1">{{ log.resource_id }}</span>
            </td>
            <td class="px-3 py-2.5 text-[var(--color-text-secondary)] hidden lg:table-cell max-w-xs truncate">{{ log.details }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Timeline View -->
    <div v-else class="space-y-6">
      <div v-for="[date, entries] in groupedLogs" :key="date">
        <h3 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">
          {{ formatDate(date) }}
        </h3>
        <div class="relative pl-6 border-l-2 border-[var(--color-border)] space-y-3">
          <div
            v-for="log in entries"
            :key="log.id"
            class="relative"
          >
            <!-- Dot -->
            <div class="absolute -left-[calc(1.5rem+5px)] top-1.5 w-2 h-2 rounded-full bg-[var(--color-primary)]"></div>
            <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-3">
              <div class="flex items-center gap-2 mb-1">
                <Badge :variant="badgeVariant(log.action)">{{ formatAction(log.action) }}</Badge>
                <span class="text-xs text-[var(--color-text-muted)]">{{ formatTime(log.timestamp) }}</span>
              </div>
              <div class="text-xs text-[var(--color-text)]">
                <span class="font-medium">{{ log.actor }}</span>
                <span v-if="log.details" class="text-[var(--color-text-secondary)]"> — {{ log.details }}</span>
              </div>
              <div v-if="log.resource_type" class="text-xs text-[var(--color-text-muted)] mt-1">
                {{ log.resource_type }}<span v-if="log.resource_id"> / {{ log.resource_id }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="!loading && !error && total > limit" class="flex items-center justify-between mt-4 pt-3 border-t border-[var(--color-border)]">
      <span class="text-xs text-[var(--color-text-muted)]">
        {{ page * limit + 1 }}–{{ Math.min((page + 1) * limit, total) }} of {{ total }}
      </span>
      <div class="flex gap-1">
        <button
          @click="page = Math.max(0, page - 1)"
          :disabled="page === 0"
          class="px-2.5 py-1 text-xs border border-[var(--color-border)] rounded-md hover:bg-[var(--color-primary-light)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
        >Prev</button>
        <button
          @click="page = Math.min(totalPages - 1, page + 1)"
          :disabled="page >= totalPages - 1"
          class="px-2.5 py-1 text-xs border border-[var(--color-border)] rounded-md hover:bg-[var(--color-primary-light)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
        >Next</button>
      </div>
    </div>
  </div>
</template>
