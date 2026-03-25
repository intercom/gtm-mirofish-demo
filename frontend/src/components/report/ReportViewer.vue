<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { marked } from 'marked'
import * as d3 from 'd3'
import { reportApi } from '../../api/report'

const props = defineProps({
  reportId: { type: String, default: null },
  sections: { type: Array, default: () => [] },
  title: { type: String, default: 'Predictive Report' },
  simulationId: { type: String, default: null },
  createdAt: { type: String, default: null },
  completedAt: { type: String, default: null },
  isComplete: { type: Boolean, default: false },
})

const emit = defineEmits(['regenerate'])

const COLORS = ['#2068FF', '#ff5600', '#AA00FF', '#009900', '#888']

// ── Helpers ──

function slugify(text) {
  return text.replace(/<[^>]+>/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
}

function addHeadingIds(html) {
  return html.replace(/<h([1-3])([^>]*)>(.*?)<\/h\1>/gs, (_, lvl, attrs, inner) => {
    return `<h${lvl}${attrs} id="${slugify(inner)}">${inner}</h${lvl}>`
  })
}

// ── Table of Contents ──

const activeTocId = ref(null)
const contentEl = ref(null)

const fullMarkdown = computed(() =>
  props.sections.map(s => s.content).join('\n\n---\n\n'),
)

const tocEntries = computed(() => {
  const entries = []
  for (const line of fullMarkdown.value.split('\n')) {
    const m = line.match(/^(#{1,3})\s+(.+)/)
    if (m) entries.push({ level: m[1].length, text: m[2].trim(), id: slugify(m[2].trim()) })
  }
  return entries
})

function scrollToHeading(id) {
  activeTocId.value = id
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// ── Content Parsing (markdown + chart placeholders) ──

const contentSegments = computed(() => {
  const md = fullMarkdown.value
  if (!md) return []

  const segments = []
  const re = /\{\{chart:([^:}]+)(?::([^}]+))?\}\}/g
  let last = 0
  let match

  while ((match = re.exec(md)) !== null) {
    if (match.index > last) {
      segments.push({ type: 'html', content: addHeadingIds(marked.parse(md.slice(last, match.index))) })
    }
    segments.push({
      type: 'chart',
      chartType: match[1].trim(),
      chartKey: (match[2] || match[1]).trim(),
    })
    last = match.index + match[0].length
  }

  if (last < md.length) {
    segments.push({ type: 'html', content: addHeadingIds(marked.parse(md.slice(last))) })
  }
  return segments
})

// ── D3 Chart Rendering ──

const chartRefs = ref({})

function setChartRef(idx) {
  return (el) => {
    if (el) chartRefs.value[idx] = el
    else delete chartRefs.value[idx]
  }
}

let resizeObserver = null
let resizeTimer = null

function renderAllCharts() {
  for (const [idx, el] of Object.entries(chartRefs.value)) {
    const seg = contentSegments.value[parseInt(idx)]
    if (!seg || seg.type !== 'chart') continue
    d3.select(el).selectAll('*').remove()
    const fn = CHART_REGISTRY[seg.chartKey] || CHART_REGISTRY[seg.chartType]
    if (fn) fn(el)
    else renderFallback(el, seg.chartType)
  }
}

watch(contentSegments, () => {
  chartRefs.value = {}
  nextTick(renderAllCharts)
})

onMounted(() => {
  nextTick(renderAllCharts)
  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(renderAllCharts, 250)
  })
  if (contentEl.value) resizeObserver.observe(contentEl.value)
})

onUnmounted(() => {
  resizeObserver?.disconnect()
  clearTimeout(resizeTimer)
})

// -- Chart: Horizontal Bar --
function renderBarChart(el) {
  const data = [
    { label: 'VP Support', value: 38.4 },
    { label: 'Head of Ops', value: 35.6 },
    { label: 'CX Director', value: 31.2 },
    { label: 'CFO', value: 28.9 },
    { label: 'IT Leader', value: 22.8 },
  ]
  const w = el.clientWidth
  if (w < 100) return
  const margin = { top: 48, right: 50, bottom: 20, left: 90 }
  const iw = w - margin.left - margin.right
  const barH = 28, gap = 8
  const ih = data.length * (barH + gap) - gap

  const svg = d3.select(el).append('svg')
    .attr('width', w).attr('height', ih + margin.top + margin.bottom)

  svg.append('text').attr('x', margin.left).attr('y', 20)
    .attr('font-size', '13px').attr('font-weight', '600').attr('fill', '#050505')
    .text('Persona Engagement Rates')
  svg.append('text').attr('x', margin.left).attr('y', 36)
    .attr('font-size', '10px').attr('fill', '#888')
    .text('Average email open rate by target persona')

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)
  const x = d3.scaleLinear().domain([0, 50]).range([0, iw])
  const y = d3.scaleBand().domain(data.map(d => d.label)).range([0, ih]).padding(gap / (barH + gap))

  g.selectAll('.bg').data(data).join('rect')
    .attr('x', 0).attr('y', d => y(d.label))
    .attr('width', iw).attr('height', y.bandwidth())
    .attr('rx', 4).attr('fill', 'rgba(0,0,0,0.03)')

  g.selectAll('.lbl').data(data).join('text')
    .attr('x', -6).attr('y', d => y(d.label) + y.bandwidth() / 2)
    .attr('dy', '.35em').attr('text-anchor', 'end')
    .attr('font-size', '11px').attr('fill', '#555').text(d => d.label)

  g.selectAll('.bar').data(data).join('rect')
    .attr('x', 0).attr('y', d => y(d.label))
    .attr('width', 0).attr('height', y.bandwidth())
    .attr('rx', 4).attr('fill', (_, i) => COLORS[i]).attr('opacity', 0.85)
    .transition().duration(500).delay((_, i) => i * 60).ease(d3.easeCubicOut)
    .attr('width', d => x(d.value))

  g.selectAll('.val').data(data).join('text')
    .attr('x', d => x(d.value) + 6).attr('y', d => y(d.label) + y.bandwidth() / 2)
    .attr('dy', '.35em').attr('font-size', '11px').attr('font-weight', '600')
    .attr('fill', '#050505').style('opacity', 0).text(d => `${d.value}%`)
    .transition().duration(200).delay((_, i) => 500 + i * 60).style('opacity', 1)
}

// -- Chart: Donut --
function renderDonutChart(el) {
  const data = [
    { label: 'Active Evaluators', value: 31 },
    { label: 'Passive Observers', value: 24 },
    { label: 'Quick Converters', value: 19 },
    { label: 'Skeptical Evaluators', value: 18 },
    { label: 'Budget Blockers', value: 8 },
  ]
  const w = el.clientWidth
  if (w < 100) return
  const size = Math.min(w, 360)
  const r = size / 2 - 50
  const ir = r * 0.55

  const svg = d3.select(el).append('svg')
    .attr('width', w).attr('height', size + 50)

  svg.append('text').attr('x', w / 2).attr('y', 20)
    .attr('text-anchor', 'middle').attr('font-size', '13px').attr('font-weight', '600')
    .attr('fill', '#050505').text('Behavioral Cluster Distribution')
  svg.append('text').attr('x', w / 2).attr('y', 36)
    .attr('text-anchor', 'middle').attr('font-size', '10px').attr('fill', '#888')
    .text('Prospect segmentation by engagement pattern')

  const g = svg.append('g').attr('transform', `translate(${w / 2},${size / 2 + 40})`)
  const arc = d3.arc().innerRadius(ir).outerRadius(r).cornerRadius(3)
  const arcs = d3.pie().value(d => d.value).sort(null).padAngle(0.02)(data)

  g.selectAll('path').data(arcs).join('path')
    .attr('fill', (_, i) => COLORS[i]).attr('opacity', 0.85)
    .attr('stroke', '#fff').attr('stroke-width', 2)
    .transition().duration(500).delay((_, i) => i * 60)
    .attrTween('d', function (d) {
      const interp = d3.interpolate({ startAngle: d.startAngle, endAngle: d.startAngle }, d)
      return t => arc(interp(t))
    })

  g.append('text').attr('text-anchor', 'middle').attr('dy', '-0.1em')
    .attr('font-size', '20px').attr('font-weight', '700').attr('fill', '#050505').text('100%')
  g.append('text').attr('text-anchor', 'middle').attr('dy', '1.2em')
    .attr('font-size', '10px').attr('fill', '#888').text('of prospects')

  const labelArc = d3.arc().innerRadius(r + 14).outerRadius(r + 14)
  g.selectAll('.lbl').data(arcs).join('text')
    .attr('transform', d => `translate(${labelArc.centroid(d)})`)
    .attr('text-anchor', d => ((d.startAngle + d.endAngle) / 2 < Math.PI ? 'start' : 'end'))
    .attr('font-size', '10px').attr('fill', '#555')
    .style('opacity', 0)
    .text((_, i) => `${data[i].label} (${data[i].value}%)`)
    .transition().duration(200).delay((_, i) => 500 + i * 60).style('opacity', 1)
}

// -- Chart: Line --
function renderLineChart(el) {
  const data = [
    { label: 'Wk 1', value: 22 }, { label: 'Wk 2', value: 31 },
    { label: 'Wk 3', value: 38 }, { label: 'Wk 4', value: 35 },
    { label: 'Wk 5', value: 42 }, { label: 'Wk 6', value: 48 },
    { label: 'Wk 7', value: 44 }, { label: 'Wk 8', value: 52 },
  ]
  const w = el.clientWidth
  if (w < 100) return
  const margin = { top: 48, right: 24, bottom: 32, left: 40 }
  const iw = w - margin.left - margin.right
  const ih = 200

  const svg = d3.select(el).append('svg')
    .attr('width', w).attr('height', ih + margin.top + margin.bottom)

  svg.append('text').attr('x', margin.left).attr('y', 20)
    .attr('font-size', '13px').attr('font-weight', '600').attr('fill', '#050505')
    .text('Engagement Trend')
  svg.append('text').attr('x', margin.left).attr('y', 36)
    .attr('font-size', '10px').attr('fill', '#888')
    .text('Average engagement rate over simulation period')

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)
  const x = d3.scalePoint().domain(data.map(d => d.label)).range([0, iw]).padding(0.5)
  const y = d3.scaleLinear().domain([0, 60]).range([ih, 0])
  const yTicks = [0, 15, 30, 45, 60]

  g.selectAll('.grid').data(yTicks).join('line')
    .attr('x1', 0).attr('x2', iw).attr('y1', d => y(d)).attr('y2', d => y(d))
    .attr('stroke', 'rgba(0,0,0,0.06)').attr('stroke-dasharray', '2,3')
  g.selectAll('.ylbl').data(yTicks).join('text')
    .attr('x', -6).attr('y', d => y(d)).attr('dy', '.35em').attr('text-anchor', 'end')
    .attr('font-size', '9px').attr('fill', '#aaa').text(d => `${d}%`)
  g.selectAll('.xlbl').data(data).join('text')
    .attr('x', d => x(d.label)).attr('y', ih + 16).attr('text-anchor', 'middle')
    .attr('font-size', '9px').attr('fill', '#aaa').text(d => d.label)

  const area = d3.area().x(d => x(d.label)).y0(ih).y1(d => y(d.value)).curve(d3.curveMonotoneX)
  g.append('path').datum(data).attr('d', area).attr('fill', '#2068FF').attr('opacity', 0.08)

  const line = d3.line().x(d => x(d.label)).y(d => y(d.value)).curve(d3.curveMonotoneX)
  const path = g.append('path').datum(data).attr('d', line)
    .attr('fill', 'none').attr('stroke', '#2068FF').attr('stroke-width', 2.5)
  const totalLen = path.node().getTotalLength()
  path.attr('stroke-dasharray', totalLen).attr('stroke-dashoffset', totalLen)
    .transition().duration(800).ease(d3.easeCubicOut).attr('stroke-dashoffset', 0)

  g.selectAll('.dot').data(data).join('circle')
    .attr('cx', d => x(d.label)).attr('cy', d => y(d.value))
    .attr('r', 0).attr('fill', '#2068FF')
    .transition().duration(300).delay((_, i) => 400 + i * 50).attr('r', 3.5)
}

// -- Chart: Fallback --
function renderFallback(el, type) {
  d3.select(el).append('div')
    .style('padding', '24px').style('text-align', 'center')
    .style('color', '#888').style('font-size', '13px')
    .html(`<div style="margin-bottom:4px;font-weight:600">Chart: ${type}</div>Visualization will appear here`)
}

const CHART_REGISTRY = {
  bar: renderBarChart,
  'persona-engagement': renderBarChart,
  donut: renderDonutChart,
  pie: renderDonutChart,
  'behavioral-clusters': renderDonutChart,
  line: renderLineChart,
  'sentiment-timeline': renderLineChart,
  'engagement-trend': renderLineChart,
}

// ── Tool Call Transparency ──

const showToolCalls = ref(false)
const toolCallLog = ref([])
const loadingToolCalls = ref(false)

async function loadToolCalls() {
  if (!props.reportId || toolCallLog.value.length > 0) return
  loadingToolCalls.value = true
  try {
    const res = await reportApi.getAgentLogStream(props.reportId)
    if (res.data?.success) {
      toolCallLog.value = res.data.data?.entries || []
    }
  } catch {
    // Transparency section is optional — silently fail
  } finally {
    loadingToolCalls.value = false
  }
}

function toggleToolCalls() {
  showToolCalls.value = !showToolCalls.value
  if (showToolCalls.value && toolCallLog.value.length === 0) loadToolCalls()
}

const toolCallStats = computed(() => {
  const calls = toolCallLog.value.filter(e => e.action === 'tool_call')
  const last = toolCallLog.value[toolCallLog.value.length - 1]
  return {
    totalCalls: calls.length,
    totalSteps: toolCallLog.value.length,
    elapsed: last?.elapsed_seconds ? `${Math.round(last.elapsed_seconds)}s` : null,
  }
})

function entryLabel(entry) {
  if (entry.action === 'tool_call') return `Tool: ${entry.details?.tool_name || 'unknown'}`
  if (entry.action === 'llm_response') return 'AI Reasoning'
  if (entry.action === 'section_complete') return 'Section Complete'
  return entry.action?.replace(/_/g, ' ') || 'Step'
}

function entryBorderClass(entry) {
  if (entry.action === 'tool_call') return 'border-l-[#AA00FF]'
  if (entry.action === 'llm_response' || entry.action === 'thinking') return 'border-l-[#2068FF]'
  if (entry.action === 'section_complete') return 'border-l-[#009900]'
  return 'border-l-[#888]'
}

function entryBadge(entry) {
  if (entry.action === 'tool_call') return { text: 'Action', cls: 'bg-[#AA00FF]/10 text-[#AA00FF]' }
  if (entry.action === 'llm_response' || entry.action === 'thinking') return { text: 'Thought', cls: 'bg-[#2068FF]/10 text-[#2068FF]' }
  if (entry.action === 'section_complete') return { text: 'Result', cls: 'bg-[#009900]/10 text-[#009900]' }
  return { text: 'Step', cls: 'bg-[var(--color-tint)] text-[var(--color-text-muted)]' }
}

// ── Metadata ──

const generationTime = computed(() => {
  if (!props.createdAt || !props.completedAt) return null
  const ms = new Date(props.completedAt) - new Date(props.createdAt)
  const mins = Math.floor(ms / 60000)
  const secs = Math.floor((ms % 60000) / 1000)
  return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
})

const formattedDate = computed(() => {
  if (!props.createdAt) return null
  return new Date(props.createdAt).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
})

// ── Export & Print ──

function exportMarkdown() {
  const blob = new Blob([fullMarkdown.value], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${props.title.replace(/\s+/g, '-').toLowerCase()}.md`
  a.click()
  URL.revokeObjectURL(url)
}

function printReport() {
  window.print()
}
</script>

<template>
  <div class="report-viewer">
    <!-- Metadata Header -->
    <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 md:p-5 mb-6">
      <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
        <div>
          <h1 class="text-lg md:text-xl font-semibold text-[var(--color-text)]" style="letter-spacing: -0.5px">
            {{ title }}
          </h1>
          <div class="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1.5 text-xs text-[var(--color-text-muted)]">
            <span v-if="formattedDate" class="flex items-center gap-1">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              {{ formattedDate }}
            </span>
            <span v-if="simulationId" class="flex items-center gap-1">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Sim: {{ simulationId.slice(0, 8) }}
            </span>
            <span v-if="generationTime" class="flex items-center gap-1">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Generated in {{ generationTime }}
            </span>
            <span v-if="isComplete" class="flex items-center gap-1 text-[#009900]">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              Complete
            </span>
          </div>
        </div>
        <div class="flex gap-2 shrink-0">
          <button
            @click="exportMarkdown"
            class="border border-[var(--color-border)] hover:bg-[var(--color-tint)] text-[var(--color-text)] px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Export
          </button>
          <button
            @click="printReport"
            class="border border-[var(--color-border)] hover:bg-[var(--color-tint)] text-[var(--color-text)] px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            Print
          </button>
          <button
            @click="emit('regenerate')"
            class="bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Regenerate
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile TOC (horizontal scroll) -->
    <div v-if="tocEntries.length > 0" class="md:hidden mb-4 -mx-4 px-4 overflow-x-auto">
      <div class="flex gap-2 min-w-max">
        <button
          v-for="entry in tocEntries.filter(e => e.level <= 2)"
          :key="entry.id"
          @click="scrollToHeading(entry.id)"
          class="px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors"
          :class="activeTocId === entry.id
            ? 'bg-[#2068FF] text-white'
            : 'bg-[var(--color-tint)] text-[var(--color-text-secondary)] hover:bg-[var(--color-border)]'"
        >
          {{ entry.text }}
        </button>
      </div>
    </div>

    <!-- Grid: TOC sidebar + Content -->
    <div class="grid grid-cols-1 md:grid-cols-5 gap-6">
      <!-- TOC Sidebar -->
      <nav v-if="tocEntries.length > 0" class="hidden md:block md:col-span-1 rv-no-print">
        <div class="sticky top-6">
          <h3 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3 px-2">
            Contents
          </h3>
          <button
            v-for="entry in tocEntries"
            :key="entry.id"
            @click="scrollToHeading(entry.id)"
            class="w-full text-left py-1.5 rounded text-xs transition-colors block truncate"
            :class="[
              activeTocId === entry.id
                ? 'text-[#2068FF] font-medium'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)]',
              entry.level === 1 ? 'px-2' : entry.level === 2 ? 'pl-4 pr-2' : 'pl-6 pr-2',
            ]"
          >
            {{ entry.text }}
          </button>
        </div>
      </nav>

      <!-- Content Area -->
      <div
        ref="contentEl"
        :class="tocEntries.length > 0 ? 'md:col-span-4' : 'md:col-span-5'"
        class="space-y-4"
      >
        <!-- Report Body -->
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 md:p-8">
          <template v-if="contentSegments.length > 0">
            <template v-for="(seg, i) in contentSegments" :key="i">
              <div v-if="seg.type === 'html'" class="rv-content" v-html="seg.content" />
              <div
                v-else-if="seg.type === 'chart'"
                :ref="setChartRef(i)"
                class="my-6 bg-white border border-black/10 rounded-lg p-4 md:p-5"
              />
            </template>
          </template>
          <div v-else class="text-center py-16 text-[var(--color-text-muted)]">
            <p>No report content available.</p>
          </div>
        </div>

        <!-- Tool Call Transparency -->
        <div v-if="reportId" class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden rv-no-print">
          <button
            @click="toggleToolCalls"
            class="w-full flex items-center justify-between px-4 py-3 text-sm hover:bg-[var(--color-tint)] transition-colors"
          >
            <div class="flex items-center gap-2 text-[var(--color-text-secondary)]">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              Generation Transparency
              <span v-if="toolCallStats.totalCalls > 0" class="text-xs px-1.5 py-0.5 rounded bg-[var(--color-tint)] text-[var(--color-text-muted)]">
                {{ toolCallStats.totalCalls }} tool calls{{ toolCallStats.elapsed ? ` · ${toolCallStats.elapsed}` : '' }}
              </span>
            </div>
            <svg
              class="w-4 h-4 text-[var(--color-text-muted)] transition-transform duration-200"
              :class="{ 'rotate-180': showToolCalls }"
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <div v-if="showToolCalls" class="border-t border-[var(--color-border)] px-4 py-3">
            <div v-if="loadingToolCalls" class="flex items-center gap-2 text-sm text-[var(--color-text-muted)] py-4 justify-center">
              <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Loading agent log...
            </div>

            <div v-else-if="toolCallLog.length > 0" class="space-y-2 max-h-80 overflow-y-auto">
              <div
                v-for="(entry, i) in toolCallLog"
                :key="i"
                class="border-l-2 pl-3 py-1.5 text-xs"
                :class="entryBorderClass(entry)"
              >
                <div class="flex items-center justify-between gap-2">
                  <div class="flex items-center gap-2 min-w-0">
                    <span
                      class="shrink-0 px-1.5 py-0.5 rounded text-[10px] font-medium"
                      :class="entryBadge(entry).cls"
                    >
                      {{ entryBadge(entry).text }}
                    </span>
                    <span class="font-medium text-[var(--color-text)] truncate">
                      {{ entryLabel(entry) }}
                    </span>
                  </div>
                  <span v-if="entry.elapsed_seconds" class="shrink-0 text-[var(--color-text-muted)]">
                    {{ entry.elapsed_seconds.toFixed(1) }}s
                  </span>
                </div>
                <p
                  v-if="entry.details?.thought || entry.details?.summary"
                  class="text-[var(--color-text-secondary)] mt-0.5 line-clamp-2"
                >
                  {{ entry.details?.thought || entry.details?.summary }}
                </p>
              </div>
            </div>

            <p v-else class="text-xs text-[var(--color-text-muted)] py-4 text-center">
              No agent log available for this report.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Report content prose styling */
.rv-content :deep(h1) { font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; color: var(--color-text); }
.rv-content :deep(h2) { font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 0.75rem; color: var(--color-text); }
.rv-content :deep(h3) { font-size: 1.125rem; font-weight: 600; margin-top: 1.5rem; margin-bottom: 0.5rem; color: var(--color-text); }
.rv-content :deep(p) { margin-bottom: 0.75rem; line-height: 1.625; color: var(--color-text-secondary); font-size: 0.875rem; }
.rv-content :deep(ul),
.rv-content :deep(ol) { margin-bottom: 0.75rem; padding-left: 1.5rem; }
.rv-content :deep(li) { margin-bottom: 0.25rem; line-height: 1.625; color: var(--color-text-secondary); font-size: 0.875rem; }
.rv-content :deep(ul) { list-style-type: disc; }
.rv-content :deep(ol) { list-style-type: decimal; }
.rv-content :deep(strong) { font-weight: 600; color: var(--color-text); }
.rv-content :deep(blockquote) {
  border-left: 3px solid var(--color-primary);
  padding-left: 1rem;
  margin: 1rem 0;
  color: var(--color-text-secondary);
  font-style: italic;
}
.rv-content :deep(code) { background: var(--color-tint); padding: 0.125rem 0.375rem; border-radius: 0.25rem; font-size: 0.8125rem; }
.rv-content :deep(pre) { background: #1a1a2e; color: #e0e0e0; padding: 1rem; border-radius: 0.5rem; overflow-x: auto; margin: 1rem 0; }
.rv-content :deep(pre code) { background: none; padding: 0; }
.rv-content :deep(table) { width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.875rem; }
.rv-content :deep(th) { text-align: left; padding: 0.5rem; border-bottom: 2px solid var(--color-border-strong); font-weight: 600; color: var(--color-text); }
.rv-content :deep(td) { padding: 0.5rem; border-bottom: 1px solid var(--color-border); color: var(--color-text-secondary); }
.rv-content :deep(hr) { border: none; border-top: 1px solid var(--color-border); margin: 1.5rem 0; }

/* Print-friendly styles */
@media print {
  .report-viewer { max-width: 100% !important; }
  .rv-no-print { display: none !important; }
  .rv-content :deep(h1),
  .rv-content :deep(h2) { page-break-after: avoid; }
  .rv-content :deep(table),
  .rv-content :deep(pre),
  .rv-content :deep(blockquote) { page-break-inside: avoid; }
}
</style>
