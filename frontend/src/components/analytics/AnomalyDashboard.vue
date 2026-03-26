<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import * as d3 from 'd3'
import { analyticsApi } from '@/api/analytics'
import { AppCard, AppBadge } from '@/components/common'

const loading = ref(true)
const error = ref(null)
const data = ref(null)

const selectedCategory = ref(null)
const selectedSeverity = ref(null)
const days = ref(90)

const CATEGORY_ICONS = {
  revenue: '💰',
  pipeline: '📊',
  sync: '🔄',
  billing: '💳',
}

const SEVERITY_COLORS = {
  critical: 'var(--color-error)',
  high: 'var(--color-fin-orange)',
  medium: 'var(--color-warning)',
}

const SEVERITY_VARIANT = {
  critical: 'error',
  high: 'warning',
  medium: 'neutral',
}

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const params = { days: days.value }
    if (selectedCategory.value) params.category = selectedCategory.value
    if (selectedSeverity.value) params.severity = selectedSeverity.value
    const res = await analyticsApi.getAnomalies(params)
    data.value = res.data.data || res.data
  } catch (e) {
    error.value = e.message || 'Failed to load anomalies'
  } finally {
    loading.value = false
  }
}

const summary = computed(() => data.value?.summary || {})
const anomalies = computed(() => data.value?.anomalies || [])
const heatmapData = computed(() => data.value?.heatmap || {})

function formatValue(val, anomaly) {
  if (typeof val !== 'number') return val
  const unit = findUnit(anomaly.metric)
  if (unit === '$') return '$' + val.toLocaleString(undefined, { maximumFractionDigits: 0 })
  if (unit === '%') return val.toFixed(1) + '%'
  if (unit === 'ms') return val.toFixed(0) + 'ms'
  if (unit === 'days') return val.toFixed(0) + 'd'
  return val.toLocaleString(undefined, { maximumFractionDigits: 0 })
}

function findUnit(metricKey) {
  const categories = ['revenue', 'pipeline', 'sync', 'billing']
  const defs = {
    mrr: '$', arr: '$', expansion_revenue: '$', churn_revenue: '$',
    deal_velocity: 'days', conversion_rate: '%', new_opps: '', pipeline_value: '$',
    sync_success_rate: '%', sync_latency: 'ms', records_synced: '',
    payment_failure_rate: '%', invoice_count: '', overdue_amount: '$',
  }
  return defs[metricKey] || ''
}

function severityLabel(sev) {
  return sev.charAt(0).toUpperCase() + sev.slice(1)
}

// ── D3 Heatmap ──────────────────────────────────────────────────────────

const heatmapRef = ref(null)

function renderHeatmap() {
  if (!heatmapRef.value || !data.value?.heatmap) return
  const container = heatmapRef.value
  d3.select(container).selectAll('*').remove()

  // Flatten heatmap: rows = metrics, cols = dates (sampled weekly)
  const rows = []
  const allDates = new Set()
  for (const [, metrics] of Object.entries(heatmapData.value)) {
    for (const [metricKey, points] of Object.entries(metrics)) {
      rows.push({ metricKey, points })
      points.forEach(p => allDates.add(p.date))
    }
  }
  if (rows.length === 0) return

  const sortedDates = Array.from(allDates).sort()
  // Sample to ~30 columns for readability
  const step = Math.max(1, Math.floor(sortedDates.length / 30))
  const sampledDates = sortedDates.filter((_, i) => i % step === 0)

  const margin = { top: 8, right: 16, bottom: 60, left: 130 }
  const cellW = 18
  const cellH = 22
  const width = margin.left + sampledDates.length * cellW + margin.right
  const height = margin.top + rows.length * cellH + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  // Color scale: navy (normal) → orange (anomaly)
  const colorScale = d3.scaleSequential()
    .domain([0, 4])
    .interpolator(d3.interpolateRgbBasis(['#1a1a3e', '#2068FF', '#ff5600']))

  // Build lookup
  const lookup = {}
  rows.forEach(row => {
    row.points.forEach(p => {
      lookup[`${row.metricKey}_${p.date}`] = p.z_score
    })
  })

  // Metric labels (y-axis)
  const metricLabels = {
    mrr: 'MRR', arr: 'ARR', expansion_revenue: 'Expansion Rev',
    churn_revenue: 'Churn Rev', deal_velocity: 'Deal Velocity',
    conversion_rate: 'Conv Rate', new_opps: 'New Opps',
    pipeline_value: 'Pipeline Value', sync_success_rate: 'Sync Rate',
    sync_latency: 'Sync Latency', records_synced: 'Records Synced',
    payment_failure_rate: 'Payment Fail %', invoice_count: 'Invoices',
    overdue_amount: 'Overdue Amt',
  }

  g.selectAll('.y-label')
    .data(rows)
    .join('text')
    .attr('class', 'y-label')
    .attr('x', -8)
    .attr('y', (_, i) => i * cellH + cellH / 2)
    .attr('text-anchor', 'end')
    .attr('dominant-baseline', 'middle')
    .attr('fill', 'var(--color-text-secondary)')
    .attr('font-size', '11px')
    .text(d => metricLabels[d.metricKey] || d.metricKey)

  // Date labels (x-axis)
  g.selectAll('.x-label')
    .data(sampledDates)
    .join('text')
    .attr('class', 'x-label')
    .attr('x', (_, i) => i * cellW + cellW / 2)
    .attr('y', rows.length * cellH + 12)
    .attr('text-anchor', 'end')
    .attr('dominant-baseline', 'hanging')
    .attr('fill', 'var(--color-text-tertiary)')
    .attr('font-size', '9px')
    .attr('transform', (_, i) => `rotate(-45, ${i * cellW + cellW / 2}, ${rows.length * cellH + 12})`)
    .text(d => d.slice(5)) // MM-DD

  // Cells
  const cells = []
  rows.forEach((row, ri) => {
    sampledDates.forEach((date, di) => {
      const z = lookup[`${row.metricKey}_${date}`]
      if (z !== undefined) {
        cells.push({ ri, di, z: Math.abs(z), metricKey: row.metricKey, date })
      }
    })
  })

  g.selectAll('.cell')
    .data(cells)
    .join('rect')
    .attr('class', 'cell')
    .attr('x', d => d.di * cellW)
    .attr('y', d => d.ri * cellH)
    .attr('width', cellW - 1)
    .attr('height', cellH - 1)
    .attr('rx', 2)
    .attr('fill', d => colorScale(d.z))
    .attr('opacity', 0.9)
    .append('title')
    .text(d => `${d.metricKey} | ${d.date} | Z: ${d.z.toFixed(2)}`)
}

// ── D3 Timeline ─────────────────────────────────────────────────────────

const timelineRef = ref(null)

function renderTimeline() {
  if (!timelineRef.value || anomalies.value.length === 0) return
  const container = timelineRef.value
  d3.select(container).selectAll('*').remove()

  const margin = { top: 16, right: 24, bottom: 32, left: 40 }
  const width = container.clientWidth || 600
  const height = 160

  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)
  const innerW = width - margin.left - margin.right
  const innerH = height - margin.top - margin.bottom

  // Group anomalies by date
  const byDate = {}
  anomalies.value.forEach(a => {
    byDate[a.date] = (byDate[a.date] || 0) + 1
  })
  const dateEntries = Object.entries(byDate)
    .map(([date, count]) => ({ date: new Date(date), count }))
    .sort((a, b) => a.date - b.date)

  if (dateEntries.length === 0) return

  const x = d3.scaleTime()
    .domain(d3.extent(dateEntries, d => d.date))
    .range([0, innerW])

  const y = d3.scaleLinear()
    .domain([0, d3.max(dateEntries, d => d.count)])
    .nice()
    .range([innerH, 0])

  // X axis
  g.append('g')
    .attr('transform', `translate(0,${innerH})`)
    .call(d3.axisBottom(x).ticks(6).tickFormat(d3.timeFormat('%b %d')))
    .selectAll('text')
    .attr('fill', 'var(--color-text-tertiary)')
    .attr('font-size', '10px')

  g.selectAll('.domain, .tick line').attr('stroke', 'var(--color-border)')

  // Y axis
  g.append('g')
    .call(d3.axisLeft(y).ticks(3).tickFormat(d3.format('d')))
    .selectAll('text')
    .attr('fill', 'var(--color-text-tertiary)')
    .attr('font-size', '10px')

  // Bars
  const barWidth = Math.max(4, innerW / dateEntries.length - 2)

  g.selectAll('.bar')
    .data(dateEntries)
    .join('rect')
    .attr('class', 'bar')
    .attr('x', d => x(d.date) - barWidth / 2)
    .attr('y', d => y(d.count))
    .attr('width', barWidth)
    .attr('height', d => innerH - y(d.count))
    .attr('fill', 'var(--color-fin-orange)')
    .attr('rx', 2)
    .attr('opacity', 0.85)
    .append('title')
    .text(d => `${d3.timeFormat('%Y-%m-%d')(d.date)}: ${d.count} anomalies`)
}

watch([data], () => {
  nextTick(() => {
    renderHeatmap()
    renderTimeline()
  })
})

onMounted(fetchData)

watch([selectedCategory, selectedSeverity, days], fetchData)
</script>

<template>
  <div class="space-y-6">
    <!-- Header + Filters -->
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div>
        <h2 class="text-xl font-bold text-[--color-text]">Anomaly Detection</h2>
        <p class="text-sm text-[--color-text-secondary] mt-1">
          Z-score based detection across GTM metrics
        </p>
      </div>
      <div class="flex items-center gap-3">
        <select
          v-model="selectedCategory"
          class="text-sm border border-[--color-border] rounded-md px-3 py-1.5 bg-[--color-surface] text-[--color-text]"
        >
          <option :value="null">All Categories</option>
          <option value="revenue">Revenue</option>
          <option value="pipeline">Pipeline</option>
          <option value="sync">Data Sync</option>
          <option value="billing">Billing</option>
        </select>
        <select
          v-model="selectedSeverity"
          class="text-sm border border-[--color-border] rounded-md px-3 py-1.5 bg-[--color-surface] text-[--color-text]"
        >
          <option :value="null">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
        </select>
        <select
          v-model="days"
          class="text-sm border border-[--color-border] rounded-md px-3 py-1.5 bg-[--color-surface] text-[--color-text]"
        >
          <option :value="30">30 days</option>
          <option :value="60">60 days</option>
          <option :value="90">90 days</option>
          <option :value="180">180 days</option>
        </select>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="grid grid-cols-4 gap-4">
      <div v-for="i in 4" :key="i" class="h-24 rounded-lg bg-[--color-surface] border border-[--color-border] animate-pulse" />
    </div>

    <!-- Error -->
    <AppCard v-else-if="error" class="text-center py-8">
      <p class="text-[--color-error] font-medium">{{ error }}</p>
      <button class="mt-3 text-sm text-[--color-primary] hover:underline" @click="fetchData">
        Retry
      </button>
    </AppCard>

    <!-- Dashboard content -->
    <template v-else-if="data">
      <!-- Summary Cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <AppCard
          v-for="(count, sev) in { critical: summary.critical, high: summary.high, medium: summary.medium, total: summary.total }"
          :key="sev"
          class="relative overflow-hidden"
        >
          <div class="flex items-center justify-between">
            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-[--color-text-tertiary]">
                {{ sev === 'total' ? 'Total' : severityLabel(sev) }}
              </p>
              <p class="text-2xl font-bold mt-1" :style="sev !== 'total' ? { color: SEVERITY_COLORS[sev] } : {}">
                {{ count || 0 }}
              </p>
            </div>
            <div
              v-if="sev !== 'total'"
              class="w-10 h-10 rounded-full flex items-center justify-center text-lg"
              :style="{ backgroundColor: SEVERITY_COLORS[sev] + '15' }"
            >
              {{ sev === 'critical' ? '🔴' : sev === 'high' ? '🟠' : '🟡' }}
            </div>
            <div v-else class="w-10 h-10 rounded-full flex items-center justify-center text-lg bg-[rgba(32,104,255,0.1)]">
              📋
            </div>
          </div>
          <!-- Category breakdown for total card -->
          <div v-if="sev === 'total' && summary.by_category" class="mt-3 flex gap-2 flex-wrap">
            <span
              v-for="(catCount, catKey) in summary.by_category"
              :key="catKey"
              class="text-xs text-[--color-text-secondary]"
            >
              {{ CATEGORY_ICONS[catKey] }} {{ catCount }}
            </span>
          </div>
        </AppCard>
      </div>

      <!-- Anomaly Timeline -->
      <AppCard>
        <template #header>
          <h3 class="text-sm font-semibold text-[--color-text]">Anomaly Timeline</h3>
        </template>
        <div ref="timelineRef" class="w-full min-h-[160px]" />
        <p v-if="anomalies.length === 0" class="text-center text-sm text-[--color-text-tertiary] py-8">
          No anomalies detected in this time range
        </p>
      </AppCard>

      <!-- Heatmap -->
      <AppCard>
        <template #header>
          <h3 class="text-sm font-semibold text-[--color-text]">Metric Anomaly Heatmap</h3>
        </template>
        <div ref="heatmapRef" class="w-full overflow-x-auto" />
        <!-- Legend -->
        <div class="flex items-center gap-4 mt-3 text-xs text-[--color-text-tertiary]">
          <span>Normal</span>
          <div class="flex gap-0.5">
            <div class="w-4 h-3 rounded-sm" style="background: #1a1a3e" />
            <div class="w-4 h-3 rounded-sm" style="background: #2068FF" />
            <div class="w-4 h-3 rounded-sm" style="background: #8a5c30" />
            <div class="w-4 h-3 rounded-sm" style="background: #ff5600" />
          </div>
          <span>Anomalous</span>
        </div>
      </AppCard>

      <!-- Anomaly List -->
      <AppCard :padding="false">
        <template #header>
          <div class="px-6 pt-6 flex items-center justify-between">
            <h3 class="text-sm font-semibold text-[--color-text]">
              Detected Anomalies
              <span class="text-[--color-text-tertiary] font-normal ml-1">({{ anomalies.length }})</span>
            </h3>
          </div>
        </template>
        <div v-if="anomalies.length === 0" class="px-6 pb-6 text-center text-sm text-[--color-text-tertiary] py-8">
          No anomalies match the selected filters
        </div>
        <div v-else class="divide-y divide-[--color-border] max-h-[480px] overflow-y-auto">
          <div
            v-for="a in anomalies"
            :key="a.id"
            class="px-6 py-4 flex items-center gap-4 hover:bg-black/[0.02] transition-colors"
          >
            <!-- Severity indicator -->
            <div
              class="w-1.5 h-10 rounded-full flex-shrink-0"
              :style="{ backgroundColor: SEVERITY_COLORS[a.severity] }"
            />
            <!-- Info -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-[--color-text]">
                  {{ CATEGORY_ICONS[a.category] }} {{ a.metric_label }}
                </span>
                <AppBadge :variant="SEVERITY_VARIANT[a.severity]">
                  {{ severityLabel(a.severity) }}
                </AppBadge>
                <span class="text-xs text-[--color-text-tertiary]">{{ a.date }}</span>
              </div>
              <div class="flex items-center gap-4 mt-1 text-xs text-[--color-text-secondary]">
                <span>Expected: <strong>{{ formatValue(a.expected, a) }}</strong></span>
                <span>Actual: <strong class="text-[--color-text]">{{ formatValue(a.actual, a) }}</strong></span>
                <span :class="a.deviation > 0 ? 'text-[--color-error]' : 'text-[--color-success]'">
                  {{ a.deviation > 0 ? '+' : '' }}{{ a.deviation }}%
                </span>
              </div>
            </div>
            <!-- Z-score bar -->
            <div class="flex-shrink-0 w-24">
              <div class="text-right text-xs text-[--color-text-tertiary] mb-1">
                Z: {{ Math.abs(a.z_score).toFixed(1) }}
              </div>
              <div class="h-2 bg-black/5 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all"
                  :style="{
                    width: Math.min(100, (Math.abs(a.z_score) / 6) * 100) + '%',
                    backgroundColor: SEVERITY_COLORS[a.severity],
                  }"
                />
              </div>
            </div>
            <!-- Direction arrow -->
            <span class="text-lg flex-shrink-0" :title="a.direction">
              {{ a.direction === 'spike' ? '📈' : '📉' }}
            </span>
          </div>
        </div>
      </AppCard>
    </template>
  </div>
</template>
