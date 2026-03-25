<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  billingData: { type: Object, default: null },
})

const COLORS = {
  paid: '#009900',
  pending: '#f59e0b',
  overdue: '#ef4444',
  failed: '#888888',
  primary: '#2068FF',
  text: '#050505',
}

const STATUS_KEYS = ['paid', 'pending', 'overdue', 'failed']

// --- Mock data generator (used when no billingData prop provided) ---

function generateMockData() {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
  const monthly = months.map((month) => ({
    month,
    paid: Math.round(40000 + Math.random() * 30000),
    pending: Math.round(8000 + Math.random() * 12000),
    overdue: Math.round(3000 + Math.random() * 8000),
    failed: Math.round(500 + Math.random() * 2000),
  }))

  const accounts = [
    'Acme Corp', 'TechFlow Inc', 'DataStream Ltd', 'CloudBase IO',
    'NexGen Systems', 'PivotPoint AI', 'ScaleUp HQ', 'Meridian SaaS',
    'Forge Analytics', 'BrightPath Co', 'SynergyHub', 'CatalystOps',
  ]
  const statuses = ['paid', 'pending', 'overdue', 'failed']
  const now = Date.now()
  const invoices = accounts.map((account, i) => {
    const status = statuses[i % statuses.length]
    const amount = Math.round(2000 + Math.random() * 15000)
    const daysAgo = Math.floor(Math.random() * 120)
    const dueDate = new Date(now - daysAgo * 86400000)
    const daysOverdue = status === 'overdue' ? Math.floor(Math.random() * 100) + 1 : 0
    return { account, amount, status, dueDate: dueDate.toISOString().slice(0, 10), daysOverdue }
  })

  const totalInvoiced = monthly.reduce((s, m) => s + m.paid + m.pending + m.overdue + m.failed, 0)
  const totalPaid = monthly.reduce((s, m) => s + m.paid, 0)
  const totalOverdue = invoices.filter(i => i.status === 'overdue').reduce((s, i) => s + i.amount, 0)

  const aging = [
    { bucket: '0–30 days', amount: Math.round(totalOverdue * 0.4) },
    { bucket: '31–60 days', amount: Math.round(totalOverdue * 0.3) },
    { bucket: '61–90 days', amount: Math.round(totalOverdue * 0.2) },
    { bucket: '90+ days', amount: Math.round(totalOverdue * 0.1) },
  ]

  return {
    monthly,
    invoices,
    kpis: {
      collectionRate: Math.round((totalPaid / totalInvoiced) * 1000) / 10,
      dso: Math.round(35 + Math.random() * 20),
      totalInvoicedMtd: monthly[monthly.length - 1].paid + monthly[monthly.length - 1].pending + monthly[monthly.length - 1].overdue + monthly[monthly.length - 1].failed,
      overdueAmount: totalOverdue,
    },
    aging,
  }
}

const data = computed(() => props.billingData || generateMockData())

// --- KPI formatting ---

function formatCurrency(val) {
  if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`
  if (val >= 1000) return `$${(val / 1000).toFixed(1)}K`
  return `$${val.toLocaleString()}`
}

const kpis = computed(() => [
  { label: 'Collection Rate', value: `${data.value.kpis.collectionRate}%`, color: COLORS.paid },
  { label: 'Days Sales Outstanding', value: `${data.value.kpis.dso}`, color: COLORS.primary },
  { label: 'Total Invoiced MTD', value: formatCurrency(data.value.kpis.totalInvoicedMtd), color: COLORS.text },
  { label: 'Overdue Amount', value: formatCurrency(data.value.kpis.overdueAmount), color: COLORS.overdue },
])

// --- Sortable invoices table ---

const sortKey = ref('dueDate')
const sortAsc = ref(true)

function toggleSort(key) {
  if (sortKey.value === key) {
    sortAsc.value = !sortAsc.value
  } else {
    sortKey.value = key
    sortAsc.value = true
  }
}

const sortedInvoices = computed(() => {
  const rows = [...data.value.invoices]
  const dir = sortAsc.value ? 1 : -1
  rows.sort((a, b) => {
    const va = a[sortKey.value]
    const vb = b[sortKey.value]
    if (typeof va === 'number') return (va - vb) * dir
    return String(va).localeCompare(String(vb)) * dir
  })
  return rows
})

function sortIndicator(key) {
  if (sortKey.value !== key) return ''
  return sortAsc.value ? ' ▲' : ' ▼'
}

const statusBadge = {
  paid: 'bg-green-100 text-green-700',
  pending: 'bg-yellow-100 text-yellow-700',
  overdue: 'bg-red-100 text-red-700',
  failed: 'bg-black/5 text-[--color-text-secondary]',
}

// --- D3 Charts ---

const stackedChartRef = ref(null)
const agingChartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

function clearChart(el) {
  if (el) d3.select(el).selectAll('*').remove()
}

function renderStackedBar() {
  const container = stackedChartRef.value
  if (!container) return
  clearChart(container)

  const monthly = data.value.monthly
  const containerWidth = container.clientWidth
  const margin = { top: 56, right: 24, bottom: 40, left: 56 }
  const width = containerWidth - margin.left - margin.right
  const height = 260
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 22)
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .text('Monthly Billing by Status')

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 40)
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text('Stacked view of invoice statuses per month')

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const stack = d3.stack().keys(STATUS_KEYS)
  const series = stack(monthly)

  const x = d3.scaleBand()
    .domain(monthly.map(d => d.month))
    .range([0, width])
    .padding(0.3)

  const maxY = d3.max(series[series.length - 1], d => d[1])
  const y = d3.scaleLinear()
    .domain([0, maxY * 1.1])
    .range([height, 0])

  // Grid lines
  const yTicks = y.ticks(5)
  g.selectAll('.grid-line')
    .data(yTicks)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  // Y-axis labels
  g.selectAll('.y-label')
    .data(yTicks)
    .join('text')
    .attr('x', -8)
    .attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text(d => `$${(d / 1000).toFixed(0)}K`)

  // Stacked bars
  series.forEach((s, si) => {
    g.selectAll(`.bar-${STATUS_KEYS[si]}`)
      .data(s)
      .join('rect')
      .attr('x', (d, i) => x(monthly[i].month))
      .attr('y', height)
      .attr('width', x.bandwidth())
      .attr('height', 0)
      .attr('rx', si === series.length - 1 ? 3 : 0)
      .attr('fill', COLORS[STATUS_KEYS[si]])
      .attr('opacity', 0.85)
      .transition()
      .duration(600)
      .delay((d, i) => i * 60 + si * 40)
      .ease(d3.easeCubicOut)
      .attr('y', d => y(d[1]))
      .attr('height', d => y(d[0]) - y(d[1]))
  })

  // X-axis labels
  g.selectAll('.x-label')
    .data(monthly)
    .join('text')
    .attr('x', d => x(d.month) + x.bandwidth() / 2)
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text(d => d.month)

  // Legend
  const legend = svg.append('g')
    .attr('transform', `translate(${containerWidth - margin.right - 280}, 14)`)

  STATUS_KEYS.forEach((key, i) => {
    const offset = i * 72
    legend.append('rect')
      .attr('x', offset).attr('y', 0)
      .attr('width', 10).attr('height', 10)
      .attr('rx', 2)
      .attr('fill', COLORS[key])
      .attr('opacity', 0.85)

    legend.append('text')
      .attr('x', offset + 14).attr('y', 9)
      .attr('font-size', '11px')
      .attr('fill', '#555')
      .text(key.charAt(0).toUpperCase() + key.slice(1))
  })
}

function renderAgingChart() {
  const container = agingChartRef.value
  if (!container) return
  clearChart(container)

  const aging = data.value.aging
  const containerWidth = container.clientWidth
  const margin = { top: 56, right: 24, bottom: 40, left: 56 }
  const width = containerWidth - margin.left - margin.right
  const height = 200
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 22)
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .text('Overdue Aging')

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 40)
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text('Outstanding amounts by age bucket')

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3.scaleBand()
    .domain(aging.map(d => d.bucket))
    .range([0, width])
    .padding(0.35)

  const maxY = d3.max(aging, d => d.amount)
  const y = d3.scaleLinear()
    .domain([0, maxY * 1.2])
    .range([height, 0])

  // Grid lines
  const yTicks = y.ticks(4)
  g.selectAll('.grid-line')
    .data(yTicks)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  // Y-axis labels
  g.selectAll('.y-label')
    .data(yTicks)
    .join('text')
    .attr('x', -8)
    .attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text(d => `$${(d / 1000).toFixed(0)}K`)

  // Color gradient: more red as age increases
  const barColors = ['#f59e0b', '#f97316', '#ef4444', '#dc2626']

  // Bars
  g.selectAll('.bar')
    .data(aging)
    .join('rect')
    .attr('x', d => x(d.bucket))
    .attr('y', height)
    .attr('width', x.bandwidth())
    .attr('height', 0)
    .attr('rx', 4)
    .attr('fill', (d, i) => barColors[i])
    .attr('opacity', 0.85)
    .transition()
    .duration(600)
    .delay((d, i) => i * 80)
    .ease(d3.easeCubicOut)
    .attr('y', d => y(d.amount))
    .attr('height', d => height - y(d.amount))

  // Value labels
  g.selectAll('.bar-value')
    .data(aging)
    .join('text')
    .attr('x', d => x(d.bucket) + x.bandwidth() / 2)
    .attr('y', d => y(d.amount) - 8)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .style('opacity', 0)
    .text(d => formatCurrency(d.amount))
    .transition()
    .duration(300)
    .delay((d, i) => 600 + i * 80)
    .style('opacity', 1)

  // X-axis labels
  g.selectAll('.x-label')
    .data(aging)
    .join('text')
    .attr('x', d => x(d.bucket) + x.bandwidth() / 2)
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text(d => d.bucket)
}

function renderAllCharts() {
  nextTick(() => {
    renderStackedBar()
    renderAgingChart()
  })
}

watch(() => props.billingData, renderAllCharts, { deep: true })

onMounted(() => {
  renderAllCharts()

  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(renderAllCharts, 200)
  })
  if (stackedChartRef.value) resizeObserver.observe(stackedChartRef.value)
  if (agingChartRef.value) resizeObserver.observe(agingChartRef.value)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="space-y-6">
    <!-- KPI Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div
        v-for="kpi in kpis"
        :key="kpi.label"
        class="bg-[--color-surface] border border-[--color-border] rounded-lg p-5"
      >
        <div class="text-xs font-medium text-[--color-text-muted] uppercase tracking-wide mb-1">
          {{ kpi.label }}
        </div>
        <div class="text-2xl font-bold" :style="{ color: kpi.color }">
          {{ kpi.value }}
        </div>
      </div>
    </div>

    <!-- Stacked Bar Chart: Monthly Billing by Status -->
    <div class="bg-[--color-surface] border border-[--color-border] rounded-lg p-4 md:p-6">
      <div ref="stackedChartRef" class="w-full" />
    </div>

    <!-- Recent Invoices Table -->
    <div class="bg-[--color-surface] border border-[--color-border] rounded-lg overflow-hidden">
      <div class="px-5 py-4 border-b border-[--color-border]">
        <h3 class="text-sm font-semibold text-[--color-text]">Recent Invoices</h3>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-[--color-border] text-left text-[--color-text-muted]">
              <th
                v-for="col in [
                  { key: 'account', label: 'Account' },
                  { key: 'amount', label: 'Amount' },
                  { key: 'status', label: 'Status' },
                  { key: 'dueDate', label: 'Due Date' },
                  { key: 'daysOverdue', label: 'Days Overdue' },
                ]"
                :key="col.key"
                class="px-5 py-3 font-medium text-xs uppercase tracking-wide cursor-pointer hover:text-[--color-text] transition-colors select-none"
                @click="toggleSort(col.key)"
              >
                {{ col.label }}{{ sortIndicator(col.key) }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="inv in sortedInvoices"
              :key="inv.account + inv.dueDate"
              class="border-b border-[--color-border] last:border-0 hover:bg-black/[0.02] transition-colors"
            >
              <td class="px-5 py-3 font-medium text-[--color-text]">{{ inv.account }}</td>
              <td class="px-5 py-3 text-[--color-text]">${{ inv.amount.toLocaleString() }}</td>
              <td class="px-5 py-3">
                <span
                  :class="[
                    'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold',
                    statusBadge[inv.status],
                  ]"
                >
                  {{ inv.status.charAt(0).toUpperCase() + inv.status.slice(1) }}
                </span>
              </td>
              <td class="px-5 py-3 text-[--color-text-secondary]">{{ inv.dueDate }}</td>
              <td class="px-5 py-3">
                <span v-if="inv.daysOverdue > 0" class="text-red-600 font-medium">
                  {{ inv.daysOverdue }}
                </span>
                <span v-else class="text-[--color-text-muted]">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Aging Chart -->
    <div class="bg-[--color-surface] border border-[--color-border] rounded-lg p-4 md:p-6">
      <div ref="agingChartRef" class="w-full" />
    </div>
  </div>
</template>
