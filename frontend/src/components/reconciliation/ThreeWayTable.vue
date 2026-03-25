<script setup>
import { ref, computed, onMounted } from 'vue'
import { reconciliationApi } from '../../api/reconciliation'

const records = ref([])
const loading = ref(true)
const error = ref(null)
const searchQuery = ref('')
const filterMode = ref('all')
const sortColumn = ref('max_diff')
const sortAsc = ref(false)
const expandedRows = ref(new Set())
const resolutionNotes = ref({})

onMounted(async () => {
  try {
    const { data } = await reconciliationApi.getRecords()
    records.value = data.records
  } catch (e) {
    error.value = e.message || 'Failed to load reconciliation data'
  } finally {
    loading.value = false
  }
})

function sfBillingDiff(r) {
  return Math.abs(r.salesforce_mrr - r.billing_mrr)
}

function sfSnowDiff(r) {
  return Math.abs(r.salesforce_mrr - r.snowflake_mrr)
}

function maxDiff(r) {
  return Math.max(sfBillingDiff(r), sfSnowDiff(r))
}

function isMatch(r) {
  return r.salesforce_mrr === r.billing_mrr && r.salesforce_mrr === r.snowflake_mrr
}

function diffSeverity(diff) {
  if (diff === 0) return 'match'
  if (diff < 100) return 'low'
  if (diff <= 1000) return 'medium'
  return 'high'
}

function statusLabel(r) {
  if (isMatch(r)) return 'Matched'
  if (r.resolved) return 'Resolved'
  return 'Discrepancy'
}

const SORT_FNS = {
  account: (a, b) => a.account.localeCompare(b.account),
  salesforce_mrr: (a, b) => a.salesforce_mrr - b.salesforce_mrr,
  billing_mrr: (a, b) => a.billing_mrr - b.billing_mrr,
  snowflake_mrr: (a, b) => a.snowflake_mrr - b.snowflake_mrr,
  sf_billing_diff: (a, b) => sfBillingDiff(a) - sfBillingDiff(b),
  sf_snow_diff: (a, b) => sfSnowDiff(a) - sfSnowDiff(b),
  max_diff: (a, b) => maxDiff(a) - maxDiff(b),
  status: (a, b) => statusLabel(a).localeCompare(statusLabel(b)),
}

const filteredRecords = computed(() => {
  let list = records.value

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter((r) => r.account.toLowerCase().includes(q))
  }

  if (filterMode.value === 'matched') {
    list = list.filter(isMatch)
  } else if (filterMode.value === 'discrepancies') {
    list = list.filter((r) => !isMatch(r))
  }

  const fn = SORT_FNS[sortColumn.value] || SORT_FNS.max_diff
  list = [...list].sort(fn)
  if (!sortAsc.value) list.reverse()

  return list
})

const totals = computed(() => {
  const list = filteredRecords.value
  return {
    salesforce: list.reduce((s, r) => s + r.salesforce_mrr, 0),
    billing: list.reduce((s, r) => s + r.billing_mrr, 0),
    snowflake: list.reduce((s, r) => s + r.snowflake_mrr, 0),
    sfBillingDiff: list.reduce((s, r) => s + sfBillingDiff(r), 0),
    sfSnowDiff: list.reduce((s, r) => s + sfSnowDiff(r), 0),
  }
})

const columns = [
  { key: 'account', label: 'Account', align: 'left' },
  { key: 'salesforce_mrr', label: 'Salesforce MRR', align: 'right' },
  { key: 'billing_mrr', label: 'Billing MRR', align: 'right' },
  { key: 'snowflake_mrr', label: 'Snowflake MRR', align: 'right' },
  { key: 'sf_billing_diff', label: 'SF vs Billing', align: 'right' },
  { key: 'sf_snow_diff', label: 'SF vs Snow', align: 'right' },
  { key: 'status', label: 'Status', align: 'center' },
]

function toggleSort(key) {
  if (sortColumn.value === key) {
    sortAsc.value = !sortAsc.value
  } else {
    sortColumn.value = key
    sortAsc.value = key === 'account'
  }
}

function sortIndicator(key) {
  if (sortColumn.value !== key) return ''
  return sortAsc.value ? ' \u25B2' : ' \u25BC'
}

function toggleExpand(id) {
  const next = new Set(expandedRows.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  expandedRows.value = next
}

function formatMrr(value) {
  return '$' + value.toLocaleString('en-US', { minimumFractionDigits: 0 })
}

function formatDiff(value) {
  if (value === 0) return '-'
  return '$' + value.toLocaleString('en-US', { minimumFractionDigits: 0 })
}

function differsFrom(r, source) {
  if (source === 'salesforce') return false
  if (source === 'billing') return r.salesforce_mrr !== r.billing_mrr
  if (source === 'snowflake') return r.salesforce_mrr !== r.snowflake_mrr
  return false
}

async function resolveRecord(record) {
  const notes = resolutionNotes.value[record.id] || ''
  try {
    await reconciliationApi.resolve(record.id, { notes })
    record.resolved = true
    record.resolution = notes
    resolutionNotes.value[record.id] = ''
  } catch {
    // toast could be added here
  }
}
</script>

<template>
  <div class="bg-[--color-surface] border border-[--color-border] rounded-lg overflow-hidden">
    <!-- Header controls -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center gap-3 p-4 border-b border-[--color-border]">
      <h3 class="text-sm font-semibold text-[--color-text] whitespace-nowrap">
        MRR Reconciliation
      </h3>

      <div class="flex flex-1 items-center gap-3 w-full sm:w-auto">
        <!-- Search -->
        <div class="relative flex-1 max-w-xs">
          <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[--color-text-muted]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search accounts..."
            class="w-full pl-8 pr-3 py-1.5 text-xs bg-[--color-bg] border border-[--color-border] rounded-md text-[--color-text] placeholder:text-[--color-text-muted] focus:outline-none focus:border-[--color-primary] transition-colors"
          />
        </div>

        <!-- Filter tabs -->
        <div class="flex rounded-md border border-[--color-border] text-xs overflow-hidden">
          <button
            v-for="opt in [
              { key: 'all', label: 'All' },
              { key: 'matched', label: 'Matched' },
              { key: 'discrepancies', label: 'Discrepancies' },
            ]"
            :key="opt.key"
            :class="[
              'px-3 py-1.5 transition-colors',
              filterMode === opt.key
                ? 'bg-[--color-primary] text-white font-semibold'
                : 'text-[--color-text-secondary] hover:bg-[--color-primary-light]',
            ]"
            @click="filterMode = opt.key"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="p-12 text-center text-sm text-[--color-text-muted]">
      Loading reconciliation data...
    </div>

    <!-- Error -->
    <div v-else-if="error" class="p-12 text-center text-sm text-red-500">
      {{ error }}
    </div>

    <!-- Table -->
    <div v-else class="overflow-x-auto">
      <table class="w-full text-xs">
        <thead>
          <tr class="border-b border-[--color-border] bg-[--color-bg]">
            <th class="w-8 px-2 py-2.5" />
            <th
              v-for="col in columns"
              :key="col.key"
              :class="[
                'px-3 py-2.5 font-semibold text-[--color-text-secondary] cursor-pointer select-none hover:text-[--color-text] transition-colors whitespace-nowrap',
                col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left',
              ]"
              @click="toggleSort(col.key)"
            >
              {{ col.label }}{{ sortIndicator(col.key) }}
            </th>
          </tr>
        </thead>

        <tbody>
          <template v-for="record in filteredRecords" :key="record.id">
            <!-- Main row -->
            <tr
              :class="[
                'border-b border-[--color-border] transition-colors',
                expandedRows.has(record.id) ? 'bg-[--color-primary-light]' : 'hover:bg-[--color-bg]',
                !isMatch(record) && 'cursor-pointer',
              ]"
              @click="!isMatch(record) && toggleExpand(record.id)"
            >
              <!-- Expand icon -->
              <td class="px-2 py-2.5 text-center text-[--color-text-muted]">
                <svg
                  v-if="!isMatch(record)"
                  :class="['w-3.5 h-3.5 transition-transform', expandedRows.has(record.id) && 'rotate-90']"
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </td>

              <!-- Account -->
              <td class="px-3 py-2.5 font-medium text-[--color-text]">
                {{ record.account }}
              </td>

              <!-- Salesforce MRR -->
              <td class="px-3 py-2.5 text-right tabular-nums text-[--color-text]">
                {{ formatMrr(record.salesforce_mrr) }}
              </td>

              <!-- Billing MRR -->
              <td
                :class="[
                  'px-3 py-2.5 text-right tabular-nums',
                  differsFrom(record, 'billing') ? 'text-[--color-fin-orange] font-semibold' : 'text-[--color-text]',
                ]"
              >
                {{ formatMrr(record.billing_mrr) }}
              </td>

              <!-- Snowflake MRR -->
              <td
                :class="[
                  'px-3 py-2.5 text-right tabular-nums',
                  differsFrom(record, 'snowflake') ? 'text-[--color-fin-orange] font-semibold' : 'text-[--color-text]',
                ]"
              >
                {{ formatMrr(record.snowflake_mrr) }}
              </td>

              <!-- SF vs Billing diff -->
              <td class="px-3 py-2.5 text-right">
                <span
                  :class="[
                    'inline-block px-1.5 py-0.5 rounded text-xs tabular-nums font-medium',
                    {
                      'bg-green-100 text-green-700': diffSeverity(sfBillingDiff(record)) === 'match',
                      'bg-yellow-100 text-yellow-700': diffSeverity(sfBillingDiff(record)) === 'low',
                      'bg-orange-100 text-orange-700': diffSeverity(sfBillingDiff(record)) === 'medium',
                      'bg-red-100 text-red-700': diffSeverity(sfBillingDiff(record)) === 'high',
                    },
                  ]"
                >
                  {{ formatDiff(sfBillingDiff(record)) }}
                </span>
              </td>

              <!-- SF vs Snow diff -->
              <td class="px-3 py-2.5 text-right">
                <span
                  :class="[
                    'inline-block px-1.5 py-0.5 rounded text-xs tabular-nums font-medium',
                    {
                      'bg-green-100 text-green-700': diffSeverity(sfSnowDiff(record)) === 'match',
                      'bg-yellow-100 text-yellow-700': diffSeverity(sfSnowDiff(record)) === 'low',
                      'bg-orange-100 text-orange-700': diffSeverity(sfSnowDiff(record)) === 'medium',
                      'bg-red-100 text-red-700': diffSeverity(sfSnowDiff(record)) === 'high',
                    },
                  ]"
                >
                  {{ formatDiff(sfSnowDiff(record)) }}
                </span>
              </td>

              <!-- Status -->
              <td class="px-3 py-2.5 text-center">
                <span
                  :class="[
                    'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold',
                    isMatch(record) ? 'bg-green-100 text-green-700'
                      : record.resolved ? 'bg-blue-100 text-blue-700'
                      : 'bg-red-100 text-red-700',
                  ]"
                >
                  {{ statusLabel(record) }}
                </span>
              </td>
            </tr>

            <!-- Expanded detail row -->
            <tr v-if="expandedRows.has(record.id) && !isMatch(record)" :key="record.id + '-detail'">
              <td :colspan="columns.length + 1" class="bg-[--color-bg] px-6 py-4 border-b border-[--color-border]">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl">
                  <!-- Discrepancy details -->
                  <div>
                    <h4 class="text-xs font-semibold text-[--color-text] mb-2">Discrepancy Details</h4>
                    <dl class="space-y-1 text-xs">
                      <div class="flex justify-between">
                        <dt class="text-[--color-text-muted]">Type</dt>
                        <dd class="font-medium text-[--color-text] capitalize">{{ record.discrepancy_type || 'Unknown' }}</dd>
                      </div>
                      <div class="flex justify-between">
                        <dt class="text-[--color-text-muted]">SF vs Billing</dt>
                        <dd class="font-medium text-[--color-text]">{{ formatDiff(sfBillingDiff(record)) }}</dd>
                      </div>
                      <div class="flex justify-between">
                        <dt class="text-[--color-text-muted]">SF vs Snowflake</dt>
                        <dd class="font-medium text-[--color-text]">{{ formatDiff(sfSnowDiff(record)) }}</dd>
                      </div>
                      <div class="flex justify-between">
                        <dt class="text-[--color-text-muted]">Last Updated</dt>
                        <dd class="font-medium text-[--color-text]">{{ record.last_updated }}</dd>
                      </div>
                    </dl>
                  </div>

                  <!-- Resolution -->
                  <div>
                    <h4 class="text-xs font-semibold text-[--color-text] mb-2">Resolution</h4>
                    <div v-if="record.resolved" class="text-xs text-green-700">
                      Resolved: {{ record.resolution || 'No notes' }}
                    </div>
                    <div v-else class="space-y-2">
                      <textarea
                        v-model="resolutionNotes[record.id]"
                        placeholder="Add resolution notes..."
                        rows="2"
                        class="w-full px-2 py-1.5 text-xs bg-[--color-surface] border border-[--color-border] rounded-md text-[--color-text] placeholder:text-[--color-text-muted] focus:outline-none focus:border-[--color-primary] resize-none"
                        @click.stop
                      />
                      <button
                        class="px-3 py-1.5 text-xs font-semibold text-white bg-[--color-primary] rounded-md hover:bg-[--color-primary-hover] transition-colors"
                        @click.stop="resolveRecord(record)"
                      >
                        Mark Resolved
                      </button>
                    </div>
                  </div>
                </div>
              </td>
            </tr>
          </template>
        </tbody>

        <!-- Totals -->
        <tfoot>
          <tr class="border-t-2 border-[--color-border] bg-[--color-bg] font-semibold text-[--color-text]">
            <td class="px-2 py-2.5" />
            <td class="px-3 py-2.5">
              Total ({{ filteredRecords.length }} accounts)
            </td>
            <td class="px-3 py-2.5 text-right tabular-nums">{{ formatMrr(totals.salesforce) }}</td>
            <td class="px-3 py-2.5 text-right tabular-nums">{{ formatMrr(totals.billing) }}</td>
            <td class="px-3 py-2.5 text-right tabular-nums">{{ formatMrr(totals.snowflake) }}</td>
            <td class="px-3 py-2.5 text-right tabular-nums">{{ formatDiff(totals.sfBillingDiff) }}</td>
            <td class="px-3 py-2.5 text-right tabular-nums">{{ formatDiff(totals.sfSnowDiff) }}</td>
            <td class="px-3 py-2.5" />
          </tr>
        </tfoot>
      </table>

      <!-- Empty state -->
      <div v-if="filteredRecords.length === 0" class="p-8 text-center text-xs text-[--color-text-muted]">
        No records match your search or filter.
      </div>
    </div>
  </div>
</template>
