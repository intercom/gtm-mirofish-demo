<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as d3 from 'd3'
import Badge from '../common/Badge.vue'
import { useLocale } from '../../composables/useLocale'

const { formatCurrency: fmtCurrency, formatDate: fmtDate } = useLocale()

const props = defineProps({
  orders: {
    type: Array,
    default: null,
  },
  autoRefreshInterval: {
    type: Number,
    default: 30000,
  },
})

const emit = defineEmits(['retry', 'refresh'])

const STATUSES = ['Pending', 'Validated', 'Provisioned', 'Active', 'Failed']
const STATUS_COLORS = {
  Pending: '#94a3b8',
  Validated: '#2068FF',
  Provisioned: '#ff5600',
  Active: '#009900',
  Failed: '#ef4444',
}
const STATUS_BADGE_VARIANT = {
  Pending: 'default',
  Validated: 'primary',
  Provisioned: 'orange',
  Active: 'success',
  Failed: 'error',
}

// Auto-refresh state
const autoRefresh = ref(true)
const lastRefreshed = ref(Date.now())
const secondsSinceRefresh = ref(0)
let refreshInterval = null
let tickInterval = null

function startAutoRefresh() {
  stopAutoRefresh()
  if (!autoRefresh.value) return
  refreshInterval = setInterval(() => {
    lastRefreshed.value = Date.now()
    secondsSinceRefresh.value = 0
    emit('refresh')
  }, props.autoRefreshInterval)
  tickInterval = setInterval(() => {
    secondsSinceRefresh.value = Math.floor((Date.now() - lastRefreshed.value) / 1000)
  }, 1000)
}

function stopAutoRefresh() {
  if (refreshInterval) { clearInterval(refreshInterval); refreshInterval = null }
  if (tickInterval) { clearInterval(tickInterval); tickInterval = null }
}

function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    lastRefreshed.value = Date.now()
    secondsSinceRefresh.value = 0
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

// Deterministic demo data (seeded by index for consistency across renders)
function generateDemoOrders() {
  const accounts = [
    'Acme Corp', 'TechStart Inc', 'Global Systems', 'DataFlow Ltd', 'CloudNet Pro',
    'Nexus Digital', 'Quantum Labs', 'Sigma Analytics', 'Orbit Media', 'Velocity SaaS',
  ]
  // Distribution: 5 Pending, 5 Validated, 5 Provisioned, 32 Active, 3 Failed (~95% success among completed)
  const distribution = [
    ...Array(5).fill('Pending'),
    ...Array(5).fill('Validated'),
    ...Array(5).fill('Provisioned'),
    ...Array(32).fill('Active'),
    ...Array(3).fill('Failed'),
  ]
  const baseTime = new Date('2026-03-01T00:00:00Z').getTime()
  return distribution.map((status, i) => {
    const seed = ((i + 1) * 2654435761) >>> 0
    const daysOffset = (seed % 80) + 1
    const createdDate = new Date(baseTime + daysOffset * 86400000 - i * 3600000)
    const provDays = +(1 + ((seed % 20) / 10)).toFixed(1)
    return {
      id: `ORD-${String(1000 + i)}`,
      account_name: accounts[i % accounts.length],
      status,
      total: 5000 + (seed % 95000),
      created_date: createdDate.toISOString(),
      activated_date: status === 'Active'
        ? new Date(createdDate.getTime() + provDays * 86400000).toISOString()
        : null,
      provisioning_time_days: status === 'Active' ? provDays : null,
    }
  })
}

const data = computed(() => props.orders ?? generateDemoOrders())

// Stat cards
const totalOrders = computed(() => data.value.length)

const successRate = computed(() => {
  const resolved = data.value.filter(o => o.status === 'Active' || o.status === 'Failed')
  if (resolved.length === 0) return '0.0'
  const active = resolved.filter(o => o.status === 'Active').length
  return ((active / resolved.length) * 100).toFixed(1)
})

const avgProvisioningTime = computed(() => {
  const times = data.value
    .filter(o => o.provisioning_time_days != null)
    .map(o => o.provisioning_time_days)
  if (times.length === 0) return '0.0'
  return (times.reduce((a, b) => a + b, 0) / times.length).toFixed(1)
})

const failedCount = computed(() => data.value.filter(o => o.status === 'Failed').length)

// Status distribution for chart
const statusCounts = computed(() => {
  const counts = {}
  for (const s of STATUSES) counts[s] = 0
  for (const o of data.value) {
    if (counts[o.status] !== undefined) counts[o.status]++
  }
  return counts
})

// Table sorting
const sortField = ref('created_date')
const sortDir = ref('desc')

function toggleSort(field) {
  if (sortField.value === field) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDir.value = field === 'status' ? 'asc' : 'desc'
  }
}

function sortIndicator(field) {
  if (sortField.value !== field) return ''
  return sortDir.value === 'asc' ? ' \u2191' : ' \u2193'
}

const sortedOrders = computed(() => {
  const list = [...data.value]
  list.sort((a, b) => {
    let cmp = 0
    if (sortField.value === 'created_date') {
      cmp = new Date(a.created_date) - new Date(b.created_date)
    } else if (sortField.value === 'status') {
      cmp = STATUSES.indexOf(a.status) - STATUSES.indexOf(b.status)
    }
    return sortDir.value === 'asc' ? cmp : -cmp
  })
  return list
})

// D3 stacked bar chart
const chartRef = ref(null)
const clipId = `prov-bar-${Math.random().toString(36).slice(2, 8)}`

function renderChart() {
  const el = chartRef.value
  if (!el) return

  d3.select(el).selectAll('*').remove()

  const total = totalOrders.value
  if (total === 0) return

  const width = el.clientWidth
  const height = 40

  const svg = d3.select(el)
    .append('svg')
    .attr('width', width)
    .attr('height', height)

  // Rounded corners via clip path
  svg.append('defs')
    .append('clipPath')
    .attr('id', clipId)
    .append('rect')
    .attr('width', width)
    .attr('height', height)
    .attr('rx', 8)

  const g = svg.append('g').attr('clip-path', `url(#${clipId})`)
  const scale = d3.scaleLinear().domain([0, total]).range([0, width])
  const counts = statusCounts.value
  let x = 0

  for (const status of STATUSES) {
    const count = counts[status]
    if (count === 0) continue
    const w = scale(count)

    g.append('rect')
      .attr('x', x)
      .attr('y', 0)
      .attr('width', 0)
      .attr('height', height)
      .attr('fill', STATUS_COLORS[status])
      .transition()
      .duration(600)
      .ease(d3.easeCubicOut)
      .attr('width', w)

    // Show count label if segment is wide enough
    if (w > 32) {
      g.append('text')
        .attr('x', x + w / 2)
        .attr('y', height / 2)
        .attr('dy', '0.35em')
        .attr('text-anchor', 'middle')
        .attr('fill', 'white')
        .attr('font-size', '11px')
        .attr('font-weight', '600')
        .attr('pointer-events', 'none')
        .text(count)
        .attr('opacity', 0)
        .transition()
        .delay(400)
        .duration(300)
        .attr('opacity', 1)
    }

    x += w
  }
}

let resizeTimeout = null
function handleResize() {
  if (resizeTimeout) clearTimeout(resizeTimeout)
  resizeTimeout = setTimeout(renderChart, 150)
}

watch(statusCounts, () => nextTick(renderChart), { deep: true })

onMounted(() => {
  nextTick(renderChart)
  startAutoRefresh()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  stopAutoRefresh()
  window.removeEventListener('resize', handleResize)
  if (resizeTimeout) clearTimeout(resizeTimeout)
})

// Formatters
function formatDate(iso) {
  return fmtDate(iso, { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatCurrency(val) {
  return fmtCurrency(val, 'USD', { maximumFractionDigits: 0 })
}

function handleRetry(orderId) {
  emit('retry', orderId)
}
</script>

<template>
  <div>
    <!-- Header with auto-refresh indicator -->
    <div class="flex items-center justify-between mb-5">
      <h2 class="text-lg font-semibold text-[var(--color-text)]">Provisioning Status</h2>
      <button
        @click="toggleAutoRefresh"
        class="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-md border transition-colors"
        :class="autoRefresh
          ? 'text-[#009900] border-[#009900]/30 bg-[#009900]/5 hover:bg-[#009900]/10'
          : 'text-[var(--color-text-muted)] border-[var(--color-border)] hover:bg-black/5'"
      >
        <span
          class="w-1.5 h-1.5 rounded-full"
          :class="autoRefresh ? 'bg-[#009900] animate-pulse' : 'bg-[var(--color-text-muted)]'"
        />
        {{ autoRefresh ? `Auto-refresh \u00B7 ${secondsSinceRefresh}s` : 'Auto-refresh off' }}
      </button>
    </div>

    <!-- Stat Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3">
        <div class="text-xs text-[var(--color-text-muted)] mb-1">Total Orders</div>
        <div class="text-2xl font-semibold text-[var(--color-text)]">{{ totalOrders }}</div>
      </div>
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3">
        <div class="text-xs text-[var(--color-text-muted)] mb-1">Success Rate</div>
        <div class="text-2xl font-semibold text-[#009900]">{{ successRate }}%</div>
      </div>
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3">
        <div class="text-xs text-[var(--color-text-muted)] mb-1">Avg Provisioning Time</div>
        <div class="text-2xl font-semibold text-[var(--color-text)]">{{ avgProvisioningTime }}d</div>
      </div>
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3">
        <div class="text-xs text-[var(--color-text-muted)] mb-1">Failed</div>
        <div
          class="text-2xl font-semibold"
          :class="failedCount > 0 ? 'text-[#ef4444]' : 'text-[var(--color-text)]'"
        >
          {{ failedCount }}
        </div>
      </div>
    </div>

    <!-- Stacked Bar Chart -->
    <div class="mb-6">
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs font-medium text-[var(--color-text-secondary)]">Orders by Status</span>
        <div class="flex items-center gap-3">
          <span
            v-for="s in STATUSES"
            :key="s"
            class="flex items-center gap-1 text-[10px] text-[var(--color-text-muted)]"
          >
            <span class="w-2 h-2 rounded-sm" :style="{ backgroundColor: STATUS_COLORS[s] }" />
            {{ s }}
          </span>
        </div>
      </div>
      <div ref="chartRef" class="w-full" />
    </div>

    <!-- Orders Table -->
    <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-[var(--color-border)]">
              <th class="text-left px-4 py-3 text-xs font-medium text-[var(--color-text-muted)]">Order</th>
              <th class="text-left px-4 py-3 text-xs font-medium text-[var(--color-text-muted)]">Account</th>
              <th
                class="text-left px-4 py-3 text-xs font-medium text-[var(--color-text-muted)] cursor-pointer select-none hover:text-[#2068FF] transition-colors"
                @click="toggleSort('status')"
              >
                Status{{ sortIndicator('status') }}
              </th>
              <th class="text-right px-4 py-3 text-xs font-medium text-[var(--color-text-muted)]">Amount</th>
              <th
                class="text-left px-4 py-3 text-xs font-medium text-[var(--color-text-muted)] cursor-pointer select-none hover:text-[#2068FF] transition-colors"
                @click="toggleSort('created_date')"
              >
                Created{{ sortIndicator('created_date') }}
              </th>
              <th class="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="order in sortedOrders"
              :key="order.id"
              class="border-b border-[var(--color-border)] last:border-0 transition-colors"
              :class="order.status === 'Failed' ? 'bg-[#ef4444]/5' : 'hover:bg-black/[0.02]'"
            >
              <td class="px-4 py-3 font-medium text-[var(--color-text)]">{{ order.id }}</td>
              <td class="px-4 py-3 text-[var(--color-text-secondary)]">{{ order.account_name }}</td>
              <td class="px-4 py-3">
                <Badge :variant="STATUS_BADGE_VARIANT[order.status]">{{ order.status }}</Badge>
              </td>
              <td class="px-4 py-3 text-right text-[var(--color-text)]">{{ formatCurrency(order.total) }}</td>
              <td class="px-4 py-3 text-[var(--color-text-secondary)]">{{ formatDate(order.created_date) }}</td>
              <td class="px-4 py-3 text-right">
                <button
                  v-if="order.status === 'Failed'"
                  @click="handleRetry(order.id)"
                  class="text-xs font-medium px-2.5 py-1 rounded-md bg-[#ef4444] text-white hover:bg-[#dc2626] transition-colors"
                >
                  Retry
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
