<script setup>
import { ref, computed, watch } from 'vue'
import { useLocale } from '../../../composables/useLocale'

const { formatCurrency: fmtCurrency, formatDate: fmtDate, formatNumber: fmtNumber } = useLocale()

const props = defineProps({
  config: {
    type: Object,
    default: () => ({}),
  },
  data: {
    type: [Array, Object],
    default: () => [],
  },
  loading: Boolean,
  error: String,
  onConfigChange: Function,
})

const sortKey = ref(props.config.defaultSortKey || '')
const sortDir = ref(props.config.defaultSortDir || 'asc')
const currentPage = ref(1)
const editing = ref(false)

const columns = computed(() => {
  if (props.config.columns?.length) return props.config.columns
  const rows = normalizedRows.value
  if (!rows.length) return []
  return Object.keys(rows[0]).map((key) => ({ key, label: key }))
})

const normalizedRows = computed(() => {
  if (Array.isArray(props.data)) return props.data
  if (props.data?.rows) return props.data.rows
  return []
})

const rowLimit = computed(() => props.config.rowLimit || 10)

const sortedRows = computed(() => {
  const rows = [...normalizedRows.value]
  if (!sortKey.value) return rows
  return rows.sort((a, b) => {
    const av = a[sortKey.value]
    const bv = b[sortKey.value]
    if (av == null) return 1
    if (bv == null) return -1
    const cmp = typeof av === 'number' ? av - bv : String(av).localeCompare(String(bv))
    return sortDir.value === 'asc' ? cmp : -cmp
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(sortedRows.value.length / rowLimit.value)))

const paginatedRows = computed(() => {
  if (!props.config.pagination) return sortedRows.value.slice(0, rowLimit.value)
  const start = (currentPage.value - 1) * rowLimit.value
  return sortedRows.value.slice(start, start + rowLimit.value)
})

watch(
  () => props.config,
  () => {
    currentPage.value = 1
  },
)

function toggleSort(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
  currentPage.value = 1
}

function formatCell(value, col) {
  if (value == null) return '—'
  switch (col.format) {
    case 'currency':
      return fmtCurrency(value, col.currency || 'USD')
    case 'percentage':
      return `${(typeof value === 'number' && value <= 1 ? value * 100 : value).toFixed(1)}%`
    case 'date':
      return fmtDate(value, { month: 'short', day: 'numeric', year: 'numeric' })
    case 'number':
      return fmtNumber(value)
    default:
      return String(value)
  }
}

function emitConfig(patch) {
  if (props.onConfigChange) {
    props.onConfigChange({ ...props.config, ...patch })
  }
}

function addColumn() {
  const cols = [...(props.config.columns || []), { key: '', label: '', format: 'text' }]
  emitConfig({ columns: cols })
}

function removeColumn(idx) {
  const cols = [...(props.config.columns || [])]
  cols.splice(idx, 1)
  emitConfig({ columns: cols })
}

function updateColumn(idx, field, value) {
  const cols = (props.config.columns || []).map((c, i) =>
    i === idx ? { ...c, [field]: value } : c,
  )
  emitConfig({ columns: cols })
}
</script>

<template>
  <div class="table-widget">
    <!-- Error state -->
    <div v-if="error" class="flex items-center justify-center h-full min-h-[120px] text-[var(--color-error)] text-sm">
      {{ error }}
    </div>

    <!-- Loading state -->
    <div v-else-if="loading" class="flex items-center justify-center h-full min-h-[120px]">
      <div class="table-widget-skeleton">
        <div v-for="i in 4" :key="i" class="skeleton-row" />
      </div>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="!normalizedRows.length"
      class="flex flex-col items-center justify-center h-full min-h-[120px] text-[var(--color-text-muted)] text-sm gap-1"
    >
      <svg class="w-8 h-8 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M3 10h18M3 14h18M3 6h18M3 18h18" />
      </svg>
      <span>No data available</span>
    </div>

    <!-- Table -->
    <template v-else>
      <!-- Edit mode -->
      <div v-if="editing" class="table-widget-editor">
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs uppercase tracking-wider text-[var(--color-text-muted)]">Column Configuration</span>
          <button class="text-xs text-[var(--color-primary)] hover:underline" @click="editing = false">Done</button>
        </div>
        <div v-for="(col, idx) in config.columns || []" :key="idx" class="editor-row">
          <input
            :value="col.key"
            placeholder="Field key"
            class="editor-input"
            @input="updateColumn(idx, 'key', $event.target.value)"
          />
          <input
            :value="col.label"
            placeholder="Label"
            class="editor-input"
            @input="updateColumn(idx, 'label', $event.target.value)"
          />
          <select :value="col.format || 'text'" class="editor-input" @change="updateColumn(idx, 'format', $event.target.value)">
            <option value="text">Text</option>
            <option value="number">Number</option>
            <option value="currency">Currency</option>
            <option value="percentage">Percentage</option>
            <option value="date">Date</option>
          </select>
          <button class="text-[var(--color-error)] text-xs hover:underline" @click="removeColumn(idx)">Remove</button>
        </div>
        <button class="text-xs text-[var(--color-primary)] hover:underline mt-2" @click="addColumn">+ Add column</button>

        <div class="mt-3 flex gap-3">
          <label class="flex items-center gap-2 text-xs text-[var(--color-text-secondary)]">
            <input
              type="checkbox"
              :checked="config.pagination"
              @change="emitConfig({ pagination: $event.target.checked })"
            />
            Pagination
          </label>
          <label class="flex items-center gap-2 text-xs text-[var(--color-text-secondary)]">
            Rows
            <input
              type="number"
              :value="config.rowLimit || 10"
              min="1"
              max="100"
              class="editor-input w-16"
              @input="emitConfig({ rowLimit: parseInt($event.target.value) || 10 })"
            />
          </label>
        </div>
      </div>

      <!-- Data table -->
      <div v-else class="table-widget-scroll">
        <table class="table-widget-table">
          <thead>
            <tr>
              <th
                v-for="col in columns"
                :key="col.key"
                class="table-widget-th"
                @click="toggleSort(col.key)"
              >
                <span class="flex items-center gap-1 select-none cursor-pointer">
                  {{ col.label || col.key }}
                  <svg
                    v-if="sortKey === col.key"
                    class="w-3 h-3 shrink-0"
                    :class="{ 'rotate-180': sortDir === 'desc' }"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
                  </svg>
                </span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in paginatedRows" :key="idx" class="table-widget-tr">
              <td v-for="col in columns" :key="col.key" class="table-widget-td">
                {{ formatCell(row[col.key], col) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="config.pagination && totalPages > 1 && !editing" class="table-widget-pagination">
        <button :disabled="currentPage <= 1" class="page-btn" @click="currentPage--">&lsaquo;</button>
        <span class="text-xs text-[var(--color-text-muted)]">{{ currentPage }} / {{ totalPages }}</span>
        <button :disabled="currentPage >= totalPages" class="page-btn" @click="currentPage++">&rsaquo;</button>
      </div>

      <!-- Footer with edit toggle -->
      <div v-if="onConfigChange && !editing" class="table-widget-footer">
        <button class="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-primary)]" @click="editing = true">
          Configure columns
        </button>
        <span class="text-xs text-[var(--color-text-muted)]">
          {{ normalizedRows.length }} row{{ normalizedRows.length === 1 ? '' : 's' }}
        </span>
      </div>
    </template>
  </div>
</template>

<style scoped>
.table-widget {
  display: flex;
  flex-direction: column;
  height: 100%;
  font-family: var(--font-family);
}

.table-widget-scroll {
  flex: 1;
  overflow: auto;
}

.table-widget-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}

.table-widget-th {
  position: sticky;
  top: 0;
  z-index: 1;
  padding: var(--space-2) var(--space-3);
  text-align: left;
  font-weight: var(--font-semibold);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}

.table-widget-tr {
  transition: background var(--transition-fast);
}

.table-widget-tr:hover {
  background: var(--color-primary-lighter);
}

.table-widget-td {
  padding: var(--space-2) var(--space-3);
  color: var(--color-text);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}

.table-widget-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-2) 0;
  border-top: 1px solid var(--color-border);
}

.page-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--text-base);
  cursor: pointer;
  transition: var(--transition-fast);
}

.page-btn:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.page-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.table-widget-footer {
  display: flex;
  justify-content: space-between;
  padding: var(--space-2) var(--space-1);
}

.table-widget-editor {
  padding: var(--space-3);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius);
  margin-bottom: var(--space-2);
}

.editor-row {
  display: flex;
  gap: var(--space-2);
  align-items: center;
  margin-bottom: var(--space-2);
}

.editor-input {
  padding: var(--space-1) var(--space-2);
  font-size: var(--text-xs);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  outline: none;
}

.editor-input:focus {
  border-color: var(--color-primary);
}

.table-widget-skeleton {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-3);
}

.skeleton-row {
  height: 14px;
  border-radius: var(--radius-sm);
  background: var(--color-border);
  animation: shimmer 1.5s ease-in-out infinite alternate;
}

.skeleton-row:nth-child(1) { width: 100%; }
.skeleton-row:nth-child(2) { width: 90%; }
.skeleton-row:nth-child(3) { width: 95%; }
.skeleton-row:nth-child(4) { width: 80%; }

@keyframes shimmer {
  from { opacity: 0.4; }
  to { opacity: 0.7; }
}
</style>
