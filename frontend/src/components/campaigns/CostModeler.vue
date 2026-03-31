<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import client from '../../api/client'

const CHANNEL_COLORS = {
  paid_search: '#2068FF',
  paid_social: '#AA00FF',
  events: '#ff5600',
  partner: '#009900',
  email: '#FFB800',
  content_seo: '#00A1E0',
}

const FUNNEL_DEFAULTS = {
  leadToMql: 0.35,
  mqlToSql: 0.40,
  sqlToClose: 0.25,
  avgDealSize: 42000,
}

const DEFAULT_CHANNELS = [
  { id: 'paid_search', name: 'Paid Search', budget: 25000, cpl: 85, conversionRate: 0.12 },
  { id: 'paid_social', name: 'Paid Social', budget: 20000, cpl: 65, conversionRate: 0.08 },
  { id: 'events', name: 'Events', budget: 30000, cpl: 150, conversionRate: 0.22 },
  { id: 'partner', name: 'Partner', budget: 15000, cpl: 45, conversionRate: 0.18 },
  { id: 'email', name: 'Email', budget: 5000, cpl: 12, conversionRate: 0.06 },
  { id: 'content_seo', name: 'Content / SEO', budget: 10000, cpl: 35, conversionRate: 0.10 },
]

const STORAGE_KEY = 'mirofish_cost_scenarios'

// --- State ---
const channels = ref(structuredClone(DEFAULT_CHANNELS))
const funnel = ref({ ...FUNNEL_DEFAULTS })
const comparisonMode = ref(false)
const optimizedChannels = ref(null)
const optimizing = ref(false)
const savedScenarios = ref([])
const scenarioName = ref('')
const showSaveDialog = ref(false)
const activeTab = ref('channels') // 'channels' | 'funnel'

// --- Chart refs ---
const currentFunnelRef = ref(null)
const optimizedFunnelRef = ref(null)
let resizeObserver = null

// --- Computed: real-time funnel calculations ---
function computeFunnel(chList) {
  let totalBudget = 0, totalLeads = 0, totalMqls = 0, totalSqls = 0, totalClosed = 0
  const channelResults = []

  for (const ch of chList) {
    const budget = Math.max(ch.budget, 0)
    const cpl = Math.max(ch.cpl, 1)
    const conv = Math.min(Math.max(ch.conversionRate, 0), 1)
    const leads = budget / cpl
    const mqls = leads * funnel.value.leadToMql * (1 + conv)
    const sqls = mqls * funnel.value.mqlToSql
    const closed = sqls * funnel.value.sqlToClose

    totalBudget += budget
    totalLeads += leads
    totalMqls += mqls
    totalSqls += sqls
    totalClosed += closed

    channelResults.push({ ...ch, leads, mqls, sqls, closed })
  }

  const revenue = totalClosed * funnel.value.avgDealSize
  const roi = totalBudget > 0 ? ((revenue - totalBudget) / totalBudget) * 100 : 0

  return {
    channels: channelResults,
    totals: {
      budget: totalBudget,
      leads: totalLeads,
      mqls: totalMqls,
      sqls: totalSqls,
      closed: totalClosed,
      revenue,
      roi,
    },
  }
}

const currentResults = computed(() => computeFunnel(channels.value))
const optimizedResults = computed(() =>
  optimizedChannels.value ? computeFunnel(optimizedChannels.value) : null,
)

const totalBudget = computed(() =>
  channels.value.reduce((sum, ch) => sum + ch.budget, 0),
)

// --- Format helpers ---
function fmtCurrency(val) {
  if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(1)}M`
  if (val >= 1_000) return `$${(val / 1_000).toFixed(1)}K`
  return `$${Math.round(val)}`
}

function fmtNumber(val) {
  if (val >= 1_000) return `${(val / 1_000).toFixed(1)}K`
  return val.toFixed(1)
}

function fmtPct(val) {
  return `${(val * 100).toFixed(0)}%`
}

// --- Optimization ---
async function runOptimization() {
  optimizing.value = true
  try {
    const { data: res } = await client.post('/v1/campaigns/cost-model/optimize', {
      channels: channels.value,
      funnel: funnel.value,
      totalBudget: totalBudget.value,
    })
    if (res.success) {
      optimizedChannels.value = res.data.channels.map((ch, i) => ({
        ...channels.value[i],
        budget: ch.budget,
      }))
      comparisonMode.value = true
    }
  } catch {
    // Fallback: client-side greedy optimization
    optimizedChannels.value = clientSideOptimize()
    comparisonMode.value = true
  } finally {
    optimizing.value = false
  }
}

function clientSideOptimize() {
  const total = totalBudget.value
  const minPct = 0.05
  const floor = total * minPct
  const n = channels.value.length

  const efficiencies = channels.value.map((ch) => {
    const cpl = Math.max(ch.cpl, 1)
    const conv = Math.min(Math.max(ch.conversionRate, 0), 1)
    return (1 / cpl)
      * funnel.value.leadToMql * (1 + conv)
      * funnel.value.mqlToSql
      * funnel.value.sqlToClose
      * funnel.value.avgDealSize
  })

  const totalEff = efficiencies.reduce((s, e) => s + e, 0) || 1
  const remaining = total - floor * n

  return channels.value.map((ch, i) => ({
    ...ch,
    budget: Math.round((floor + remaining * (efficiencies[i] / totalEff)) * 100) / 100,
  }))
}

function clearComparison() {
  comparisonMode.value = false
  optimizedChannels.value = null
}

// --- Scenario management (localStorage) ---
function loadSavedScenarios() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    savedScenarios.value = raw ? JSON.parse(raw) : []
  } catch {
    savedScenarios.value = []
  }
}

function persistScenarios() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(savedScenarios.value))
}

function saveScenario() {
  const name = scenarioName.value.trim()
  if (!name) return
  savedScenarios.value.push({
    id: `scen_${Date.now()}`,
    name,
    channels: structuredClone(channels.value),
    funnel: { ...funnel.value },
    createdAt: Date.now(),
  })
  persistScenarios()
  scenarioName.value = ''
  showSaveDialog.value = false
}

function loadScenario(scenario) {
  channels.value = structuredClone(scenario.channels)
  funnel.value = { ...FUNNEL_DEFAULTS, ...scenario.funnel }
  clearComparison()
}

function deleteScenario(id) {
  savedScenarios.value = savedScenarios.value.filter((s) => s.id !== id)
  persistScenarios()
}

function resetToDefaults() {
  channels.value = structuredClone(DEFAULT_CHANNELS)
  funnel.value = { ...FUNNEL_DEFAULTS }
  clearComparison()
}

// --- D3 Funnel Chart ---
function renderFunnel(container, results, label) {
  if (!container) return
  d3.select(container).selectAll('*').remove()

  const stages = [
    { name: 'Leads', value: results.totals.leads },
    { name: 'MQLs', value: results.totals.mqls },
    { name: 'SQLs', value: results.totals.sqls },
    { name: 'Won', value: results.totals.closed },
  ]

  const containerWidth = container.clientWidth
  const margin = { top: 40, right: 16, bottom: 24, left: 16 }
  const width = containerWidth - margin.left - margin.right
  const barHeight = 40
  const gap = 12
  const height = stages.length * (barHeight + gap)
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  // Title
  svg.append('text')
    .attr('x', containerWidth / 2)
    .attr('y', 22)
    .attr('text-anchor', 'middle')
    .attr('font-size', '13px')
    .attr('font-weight', '600')
    .attr('fill', 'var(--color-text)')
    .text(label)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const maxVal = d3.max(stages, (d) => d.value) || 1

  const colors = ['#2068FF', '#AA00FF', '#ff5600', '#009900']

  stages.forEach((stage, i) => {
    const barWidth = (stage.value / maxVal) * width
    const y = i * (barHeight + gap)
    const centerOffset = (width - barWidth) / 2

    // Bar (centered to create funnel shape)
    g.append('rect')
      .attr('x', centerOffset)
      .attr('y', y)
      .attr('width', 0)
      .attr('height', barHeight)
      .attr('rx', 6)
      .attr('fill', colors[i])
      .attr('opacity', 0.85)
      .transition()
      .duration(600)
      .delay(i * 100)
      .ease(d3.easeCubicOut)
      .attr('width', barWidth)

    // Stage label
    g.append('text')
      .attr('x', centerOffset - 4)
      .attr('y', y + barHeight / 2 + 1)
      .attr('text-anchor', 'end')
      .attr('dominant-baseline', 'middle')
      .attr('font-size', '11px')
      .attr('font-weight', '500')
      .attr('fill', 'var(--color-text-secondary)')
      .text(stage.name)

    // Value label
    g.append('text')
      .attr('x', centerOffset + barWidth + 6)
      .attr('y', y + barHeight / 2 + 1)
      .attr('dominant-baseline', 'middle')
      .attr('font-size', '12px')
      .attr('font-weight', '600')
      .attr('fill', 'var(--color-text)')
      .text(fmtNumber(stage.value))
      .attr('opacity', 0)
      .transition()
      .duration(400)
      .delay(i * 100 + 400)
      .attr('opacity', 1)

    // Conversion rate arrow between stages
    if (i < stages.length - 1) {
      const nextVal = stages[i + 1].value
      const convRate = stage.value > 0 ? ((nextVal / stage.value) * 100).toFixed(0) : 0
      const arrowY = y + barHeight + gap / 2

      g.append('text')
        .attr('x', containerWidth / 2 - margin.left)
        .attr('y', arrowY + 2)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('fill', 'var(--color-text-muted)')
        .text(`↓ ${convRate}%`)
    }
  })
}

function renderCharts() {
  nextTick(() => {
    renderFunnel(currentFunnelRef.value, currentResults.value, 'Current Allocation')
    if (comparisonMode.value && optimizedResults.value) {
      renderFunnel(optimizedFunnelRef.value, optimizedResults.value, 'Optimized Allocation')
    }
  })
}

// Re-render charts when inputs change
watch([currentResults, comparisonMode, optimizedResults], renderCharts, { deep: true })

onMounted(() => {
  loadSavedScenarios()
  nextTick(renderCharts)

  resizeObserver = new ResizeObserver(() => renderCharts())
  if (currentFunnelRef.value) resizeObserver.observe(currentFunnelRef.value)
})

onUnmounted(() => {
  resizeObserver?.disconnect()
})
</script>

<template>
  <div class="cost-modeler">
    <!-- Header -->
    <div class="modeler-header">
      <div>
        <h3 class="modeler-title">Cost Modeling Calculator</h3>
        <p class="modeler-subtitle">
          Adjust channel budgets and conversion rates to predict GTM outcomes
        </p>
      </div>
      <div class="header-actions">
        <button class="btn-secondary" @click="resetToDefaults">Reset</button>
        <button class="btn-secondary" @click="showSaveDialog = true">Save Scenario</button>
        <button
          class="btn-primary"
          :disabled="optimizing"
          @click="runOptimization"
        >
          <template v-if="optimizing">Optimizing...</template>
          <template v-else>{{ comparisonMode ? 'Re-optimize' : 'Auto-Optimize' }}</template>
        </button>
      </div>
    </div>

    <!-- Saved Scenarios Bar -->
    <div v-if="savedScenarios.length" class="scenarios-bar">
      <span class="scenarios-label">Saved:</span>
      <button
        v-for="s in savedScenarios"
        :key="s.id"
        class="scenario-chip"
        @click="loadScenario(s)"
      >
        {{ s.name }}
        <span class="chip-delete" @click.stop="deleteScenario(s.id)">&times;</span>
      </button>
    </div>

    <!-- Save Dialog -->
    <div v-if="showSaveDialog" class="save-overlay" @click.self="showSaveDialog = false">
      <div class="save-dialog">
        <h4>Save Scenario</h4>
        <input
          v-model="scenarioName"
          class="save-input"
          placeholder="Scenario name..."
          @keyup.enter="saveScenario"
        />
        <div class="save-actions">
          <button class="btn-secondary" @click="showSaveDialog = false">Cancel</button>
          <button class="btn-primary" :disabled="!scenarioName.trim()" @click="saveScenario">
            Save
          </button>
        </div>
      </div>
    </div>

    <!-- KPI Summary Cards -->
    <div class="kpi-row">
      <div class="kpi-card">
        <span class="kpi-label">Total Budget</span>
        <span class="kpi-value">{{ fmtCurrency(currentResults.totals.budget) }}</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">Predicted Leads</span>
        <span class="kpi-value">{{ fmtNumber(currentResults.totals.leads) }}</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">Predicted MQLs</span>
        <span class="kpi-value">{{ fmtNumber(currentResults.totals.mqls) }}</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">Closed Won</span>
        <span class="kpi-value">{{ fmtNumber(currentResults.totals.closed) }}</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">Predicted Revenue</span>
        <span class="kpi-value revenue">{{ fmtCurrency(currentResults.totals.revenue) }}</span>
      </div>
      <div class="kpi-card" :class="{ positive: currentResults.totals.roi > 0 }">
        <span class="kpi-label">Predicted ROI</span>
        <span class="kpi-value roi">{{ currentResults.totals.roi.toFixed(0) }}%</span>
      </div>
    </div>

    <!-- Comparison delta banner -->
    <div v-if="comparisonMode && optimizedResults" class="comparison-banner">
      <span class="banner-icon">&#9889;</span>
      <span>
        Optimized allocation yields
        <strong>{{ fmtCurrency(optimizedResults.totals.revenue) }}</strong> revenue
        ({{ optimizedResults.totals.roi > currentResults.totals.roi ? '+' : '' }}{{
          (optimizedResults.totals.roi - currentResults.totals.roi).toFixed(0)
        }}% ROI)
      </span>
      <button class="btn-ghost" @click="clearComparison">Dismiss</button>
    </div>

    <!-- Tab switcher -->
    <div class="tab-bar">
      <button
        :class="['tab-btn', { active: activeTab === 'channels' }]"
        @click="activeTab = 'channels'"
      >
        Channel Budgets
      </button>
      <button
        :class="['tab-btn', { active: activeTab === 'funnel' }]"
        @click="activeTab = 'funnel'"
      >
        Funnel Rates
      </button>
    </div>

    <!-- Channel Sliders -->
    <div v-show="activeTab === 'channels'" class="channels-grid">
      <div v-for="(ch, idx) in channels" :key="ch.id" class="channel-card">
        <div class="channel-header">
          <span
            class="channel-dot"
            :style="{ background: CHANNEL_COLORS[ch.id] }"
          ></span>
          <span class="channel-name">{{ ch.name }}</span>
          <span class="channel-budget">{{ fmtCurrency(ch.budget) }}</span>
        </div>

        <label class="slider-label">
          Budget
          <span class="slider-val">{{ fmtCurrency(ch.budget) }}</span>
        </label>
        <input
          type="range"
          :min="0"
          :max="100000"
          :step="500"
          v-model.number="channels[idx].budget"
          class="slider"
          :style="{ '--slider-color': CHANNEL_COLORS[ch.id] }"
        />

        <label class="slider-label">
          Cost per Lead
          <span class="slider-val">${{ ch.cpl }}</span>
        </label>
        <input
          type="range"
          :min="5"
          :max="300"
          :step="5"
          v-model.number="channels[idx].cpl"
          class="slider"
          :style="{ '--slider-color': CHANNEL_COLORS[ch.id] }"
        />

        <label class="slider-label">
          Conversion Rate
          <span class="slider-val">{{ fmtPct(ch.conversionRate) }}</span>
        </label>
        <input
          type="range"
          :min="0.01"
          :max="0.50"
          :step="0.01"
          v-model.number="channels[idx].conversionRate"
          class="slider"
          :style="{ '--slider-color': CHANNEL_COLORS[ch.id] }"
        />

        <!-- Channel output preview -->
        <div class="channel-output">
          <span>{{ fmtNumber(currentResults.channels[idx].leads) }} leads</span>
          <span class="sep">&rarr;</span>
          <span>{{ fmtNumber(currentResults.channels[idx].mqls) }} MQLs</span>
        </div>
      </div>
    </div>

    <!-- Funnel Rate Sliders -->
    <div v-show="activeTab === 'funnel'" class="funnel-settings">
      <div class="funnel-slider-group">
        <label class="slider-label">
          Lead &rarr; MQL Rate
          <span class="slider-val">{{ fmtPct(funnel.leadToMql) }}</span>
        </label>
        <input
          type="range" :min="0.05" :max="0.80" :step="0.01"
          v-model.number="funnel.leadToMql" class="slider"
        />
      </div>
      <div class="funnel-slider-group">
        <label class="slider-label">
          MQL &rarr; SQL Rate
          <span class="slider-val">{{ fmtPct(funnel.mqlToSql) }}</span>
        </label>
        <input
          type="range" :min="0.05" :max="0.80" :step="0.01"
          v-model.number="funnel.mqlToSql" class="slider"
        />
      </div>
      <div class="funnel-slider-group">
        <label class="slider-label">
          SQL &rarr; Closed Won Rate
          <span class="slider-val">{{ fmtPct(funnel.sqlToClose) }}</span>
        </label>
        <input
          type="range" :min="0.05" :max="0.60" :step="0.01"
          v-model.number="funnel.sqlToClose" class="slider"
        />
      </div>
      <div class="funnel-slider-group">
        <label class="slider-label">
          Avg Deal Size
          <span class="slider-val">{{ fmtCurrency(funnel.avgDealSize) }}</span>
        </label>
        <input
          type="range" :min="5000" :max="200000" :step="1000"
          v-model.number="funnel.avgDealSize" class="slider"
        />
      </div>
    </div>

    <!-- Funnel Charts (side-by-side in comparison mode) -->
    <div :class="['funnel-charts', { comparison: comparisonMode }]">
      <div class="funnel-chart-wrapper">
        <div ref="currentFunnelRef" class="funnel-chart"></div>
      </div>
      <div v-if="comparisonMode && optimizedResults" class="funnel-chart-wrapper optimized">
        <div ref="optimizedFunnelRef" class="funnel-chart"></div>
      </div>
    </div>

    <!-- Per-channel breakdown table -->
    <div class="breakdown-section">
      <h4 class="section-title">Channel Breakdown</h4>
      <div class="table-wrapper">
        <table class="breakdown-table">
          <thead>
            <tr>
              <th>Channel</th>
              <th>Budget</th>
              <th>Leads</th>
              <th>MQLs</th>
              <th>SQLs</th>
              <th>Won</th>
              <th v-if="comparisonMode">Opt. Budget</th>
              <th v-if="comparisonMode">Opt. Won</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(ch, i) in currentResults.channels" :key="ch.id">
              <td>
                <span
                  class="channel-dot-sm"
                  :style="{ background: CHANNEL_COLORS[ch.id] }"
                ></span>
                {{ ch.name }}
              </td>
              <td>{{ fmtCurrency(ch.budget) }}</td>
              <td>{{ fmtNumber(ch.leads) }}</td>
              <td>{{ fmtNumber(ch.mqls) }}</td>
              <td>{{ fmtNumber(ch.sqls) }}</td>
              <td>{{ ch.closed.toFixed(1) }}</td>
              <td v-if="comparisonMode && optimizedResults">
                {{ fmtCurrency(optimizedResults.channels[i].budget) }}
              </td>
              <td v-if="comparisonMode && optimizedResults">
                {{ optimizedResults.channels[i].closed.toFixed(1) }}
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr>
              <td><strong>Total</strong></td>
              <td><strong>{{ fmtCurrency(currentResults.totals.budget) }}</strong></td>
              <td><strong>{{ fmtNumber(currentResults.totals.leads) }}</strong></td>
              <td><strong>{{ fmtNumber(currentResults.totals.mqls) }}</strong></td>
              <td><strong>{{ fmtNumber(currentResults.totals.sqls) }}</strong></td>
              <td><strong>{{ currentResults.totals.closed.toFixed(1) }}</strong></td>
              <td v-if="comparisonMode && optimizedResults">
                <strong>{{ fmtCurrency(optimizedResults.totals.budget) }}</strong>
              </td>
              <td v-if="comparisonMode && optimizedResults">
                <strong>{{ optimizedResults.totals.closed.toFixed(1) }}</strong>
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cost-modeler {
  font-family: var(--font-family);
}

/* --- Header --- */
.modeler-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
  flex-wrap: wrap;
}

.modeler-title {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
  margin: 0;
}

.modeler-subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin: var(--space-1) 0 0;
}

.header-actions {
  display: flex;
  gap: var(--space-2);
  flex-shrink: 0;
}

/* --- Buttons --- */
.btn-primary {
  padding: var(--btn-padding-y-sm) var(--btn-padding-x-sm);
  background: var(--btn-primary-bg);
  color: var(--btn-primary-text);
  border: none;
  border-radius: var(--btn-radius);
  font-size: var(--btn-font-size);
  font-weight: var(--btn-font-weight);
  cursor: pointer;
  transition: background var(--btn-transition);
}

.btn-primary:hover:not(:disabled) {
  background: var(--btn-primary-bg-hover);
}

.btn-primary:disabled {
  opacity: var(--btn-disabled-opacity);
  cursor: not-allowed;
}

.btn-secondary {
  padding: var(--btn-padding-y-sm) var(--btn-padding-x-sm);
  background: var(--btn-secondary-bg);
  color: var(--btn-secondary-text);
  border: 1px solid var(--btn-secondary-border);
  border-radius: var(--btn-radius);
  font-size: var(--btn-font-size);
  font-weight: var(--btn-font-weight);
  cursor: pointer;
  transition: background var(--btn-transition);
}

.btn-secondary:hover {
  background: var(--btn-secondary-bg-hover);
}

.btn-ghost {
  background: none;
  border: none;
  color: var(--color-primary);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  cursor: pointer;
  padding: var(--space-1) var(--space-2);
}

.btn-ghost:hover {
  text-decoration: underline;
}

/* --- Scenarios Bar --- */
.scenarios-bar {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
  flex-wrap: wrap;
}

.scenarios-label {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  font-weight: var(--font-medium);
}

.scenario-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 2px var(--space-3);
  background: var(--color-primary-light);
  color: var(--color-primary);
  border: 1px solid var(--color-primary-border);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.scenario-chip:hover {
  background: var(--color-primary-tint-hover);
}

.chip-delete {
  font-size: 14px;
  line-height: 1;
  opacity: 0.5;
  margin-left: 2px;
}

.chip-delete:hover {
  opacity: 1;
}

/* --- Save Dialog --- */
.save-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.save-dialog {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  width: min(360px, calc(100vw - 2rem));
  box-shadow: var(--shadow-lg);
}

.save-dialog h4 {
  margin: 0 0 var(--space-4);
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text);
}

.save-input {
  width: 100%;
  padding: var(--input-padding-y) var(--input-padding-x);
  border: 1px solid var(--input-border);
  border-radius: var(--input-radius);
  font-size: var(--input-font-size);
  color: var(--input-text);
  background: var(--input-bg);
  outline: none;
  box-sizing: border-box;
}

.save-input:focus {
  border-color: var(--input-border-focus);
  box-shadow: 0 0 0 3px var(--input-ring);
}

.save-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
  margin-top: var(--space-4);
}

/* --- KPI Row --- */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.kpi-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--card-radius);
  padding: var(--space-3) var(--space-4);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.kpi-card.positive {
  border-color: var(--color-success);
  background: var(--color-success-light);
}

.kpi-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  font-weight: var(--font-medium);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.kpi-value {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--color-text);
}

.kpi-value.revenue {
  color: var(--color-primary);
}

.kpi-value.roi {
  color: var(--color-success);
}

/* --- Comparison Banner --- */
.comparison-banner {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-success-light);
  border: 1px solid rgba(0, 153, 0, 0.2);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-4);
  font-size: var(--text-sm);
  color: var(--color-text);
}

.banner-icon {
  font-size: 18px;
}

/* --- Tabs --- */
.tab-bar {
  display: flex;
  gap: var(--space-1);
  margin-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.tab-btn {
  padding: var(--space-2) var(--space-4);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: color var(--transition-fast), border-color var(--transition-fast);
}

.tab-btn.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

.tab-btn:hover:not(.active) {
  color: var(--color-text-secondary);
}

/* --- Channel Cards Grid --- */
.channels-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.channel-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--card-radius);
  padding: var(--space-4);
}

.channel-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.channel-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.channel-name {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  flex: 1;
}

.channel-budget {
  font-size: var(--text-sm);
  font-weight: var(--font-bold);
  color: var(--color-primary);
}

/* --- Sliders --- */
.slider-label {
  display: flex;
  justify-content: space-between;
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  margin-bottom: 4px;
  margin-top: var(--space-2);
}

.slider-val {
  font-weight: var(--font-semibold);
  color: var(--color-text);
}

.slider {
  width: 100%;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--color-border);
  border-radius: 3px;
  outline: none;
  cursor: pointer;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--slider-color, var(--color-primary));
  border: 2px solid var(--color-surface);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
}

.slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--slider-color, var(--color-primary));
  border: 2px solid var(--color-surface);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
}

.channel-output {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-top: var(--space-3);
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-border);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.sep {
  color: var(--color-text-muted);
}

/* --- Funnel Settings --- */
.funnel-settings {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.funnel-slider-group {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--card-radius);
  padding: var(--space-4);
}

/* --- Funnel Charts --- */
.funnel-charts {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.funnel-charts.comparison {
  grid-template-columns: 1fr 1fr;
}

.funnel-chart-wrapper {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--card-radius);
  padding: var(--space-4);
  min-height: 260px;
}

.funnel-chart-wrapper.optimized {
  border-color: var(--color-success);
  background: var(--color-success-light);
}

.funnel-chart {
  width: 100%;
}

/* --- Breakdown Table --- */
.breakdown-section {
  margin-bottom: var(--space-4);
}

.section-title {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  margin: 0 0 var(--space-3);
}

.table-wrapper {
  overflow-x: auto;
}

.breakdown-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}

.breakdown-table th {
  text-align: left;
  padding: var(--space-2) var(--space-3);
  font-weight: var(--font-semibold);
  color: var(--color-text-secondary);
  border-bottom: 2px solid var(--color-border);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.breakdown-table td {
  padding: var(--space-2) var(--space-3);
  color: var(--color-text);
  border-bottom: 1px solid var(--color-border);
}

.breakdown-table tbody tr:hover {
  background: var(--color-tint);
}

.breakdown-table tfoot td {
  border-top: 2px solid var(--color-border-strong);
  border-bottom: none;
}

.channel-dot-sm {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
}

/* --- Responsive --- */
@media (max-width: 768px) {
  .modeler-header {
    flex-direction: column;
  }

  .funnel-charts.comparison {
    grid-template-columns: 1fr;
  }

  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .channels-grid {
    grid-template-columns: 1fr;
  }
}
</style>
