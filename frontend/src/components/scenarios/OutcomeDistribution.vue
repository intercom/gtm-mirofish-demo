<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  outcomes: { type: Array, default: () => [] },
  metrics: { type: Array, default: () => [] },
  categoryField: { type: String, default: 'category' },
  templateField: { type: String, default: 'template' },
})

const emit = defineEmits(['bin-click'])

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const COLORS = {
  primary: '#2068FF',
  orange: '#ff5600',
  purple: '#AA00FF',
  green: '#009900',
  text: '#050505',
}

const CATEGORY_COLORS = [
  COLORS.primary,
  COLORS.orange,
  COLORS.purple,
  COLORS.green,
  '#E91E63',
  '#00BCD4',
  '#795548',
  '#607D8B',
]

// --- State ---
const activeMetric = ref(0)
const viewMode = ref('histogram') // 'histogram' | 'boxplot'

// --- Derived data ---

const availableMetrics = computed(() => {
  if (props.metrics.length) return props.metrics
  if (!props.outcomes.length) return []
  const sample = props.outcomes[0]
  return Object.keys(sample).filter(k => {
    return typeof sample[k] === 'number' && k !== 'id' && k !== 'index'
  })
})

const currentMetricKey = computed(() => availableMetrics.value[activeMetric.value] || null)

const metricValues = computed(() => {
  if (!currentMetricKey.value || !props.outcomes.length) return []
  return props.outcomes
    .map(o => o[currentMetricKey.value])
    .filter(v => typeof v === 'number' && !isNaN(v))
})

const categories = computed(() => {
  const field = props.categoryField
  const cats = new Set()
  for (const o of props.outcomes) {
    if (o[field]) cats.add(o[field])
  }
  return Array.from(cats)
})

const categoryColorMap = computed(() => {
  const map = {}
  categories.value.forEach((cat, i) => {
    map[cat] = CATEGORY_COLORS[i % CATEGORY_COLORS.length]
  })
  return map
})

// --- Statistics ---

function computeStats(values) {
  if (!values.length) return null
  const sorted = [...values].sort((a, b) => a - b)
  const n = sorted.length
  const mean = d3.mean(sorted)
  const median = d3.median(sorted)
  const std = d3.deviation(sorted) || 0

  // Mode: most frequent value (binned)
  const binCount = Math.min(30, Math.ceil(Math.sqrt(n)))
  const extent = d3.extent(sorted)
  const binWidth = (extent[1] - extent[0]) / binCount || 1
  const freq = {}
  for (const v of sorted) {
    const bin = Math.floor((v - extent[0]) / binWidth)
    freq[bin] = (freq[bin] || 0) + 1
  }
  const modeBin = +Object.entries(freq).sort((a, b) => b[1] - a[1])[0][0]
  const mode = extent[0] + (modeBin + 0.5) * binWidth

  // Normality check via skewness
  const skewness = n > 2
    ? (n / ((n - 1) * (n - 2))) * sorted.reduce((s, v) => s + Math.pow((v - mean) / std, 3), 0)
    : 0
  const isNormal = Math.abs(skewness) < 0.5 && n >= 10

  // Quartiles for box plot
  const q1 = d3.quantile(sorted, 0.25)
  const q3 = d3.quantile(sorted, 0.75)
  const iqr = q3 - q1
  const whiskerLow = Math.max(extent[0], q1 - 1.5 * iqr)
  const whiskerHigh = Math.min(extent[1], q3 + 1.5 * iqr)
  const outliers = sorted.filter(v => v < whiskerLow || v > whiskerHigh)

  return { mean, median, mode, std, min: extent[0], max: extent[1], n, skewness, isNormal, q1, q3, iqr, whiskerLow, whiskerHigh, outliers, sorted }
}

const stats = computed(() => computeStats(metricValues.value))

// --- Rendering ---

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !metricValues.value.length || !stats.value) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  if (viewMode.value === 'boxplot') {
    renderBoxPlot(container, containerWidth)
  } else {
    renderHistogram(container, containerWidth)
  }
}

function renderHistogram(container, containerWidth) {
  const data = metricValues.value
  const s = stats.value
  const margin = { top: 16, right: 20, bottom: 44, left: 48 }
  const width = containerWidth - margin.left - margin.right
  const height = 240
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Histogram bins
  const binCount = Math.min(30, Math.ceil(Math.sqrt(data.length)))
  const x = d3.scaleLinear()
    .domain(d3.extent(data))
    .nice(binCount)
    .range([0, width])

  const histogram = d3.bin()
    .domain(x.domain())
    .thresholds(x.ticks(binCount))

  // If we have categories, build per-category bins
  const hasCats = categories.value.length > 1
  let bins, maxFreq

  if (hasCats) {
    const catKey = props.categoryField
    const allBins = histogram(data)
    // Build stacked data per bin
    bins = allBins.map(bin => {
      const catCounts = {}
      for (const cat of categories.value) catCounts[cat] = 0
      for (const outcome of props.outcomes) {
        const v = outcome[currentMetricKey.value]
        if (v >= bin.x0 && v < bin.x1) {
          const cat = outcome[catKey] || 'Other'
          catCounts[cat] = (catCounts[cat] || 0) + 1
        }
      }
      // Handle last bin edge inclusion
      if (bin.x1 === x.domain()[1]) {
        for (const outcome of props.outcomes) {
          const v = outcome[currentMetricKey.value]
          if (v === bin.x1 && v > bin.x0) {
            const cat = outcome[catKey] || 'Other'
            // Already counted above since x0 <= v < x1, but handle edge
          }
        }
      }
      return { x0: bin.x0, x1: bin.x1, total: bin.length, cats: catCounts, items: bin }
    })
    maxFreq = d3.max(bins, b => b.total)
  } else {
    bins = histogram(data).map(bin => ({
      x0: bin.x0, x1: bin.x1, total: bin.length, items: bin,
    }))
    maxFreq = d3.max(bins, b => b.total)
  }

  const y = d3.scaleLinear()
    .domain([0, maxFreq || 1])
    .nice()
    .range([height, 0])

  // Grid lines
  const yTicks = y.ticks(5)
  g.selectAll('.grid')
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
    .text(d => d)

  // Y-axis title
  g.append('text')
    .attr('transform', 'rotate(-90)')
    .attr('x', -height / 2)
    .attr('y', -38)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text('Frequency')

  // X-axis labels
  const xTicks = x.ticks(8)
  g.selectAll('.x-label')
    .data(xTicks)
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 18)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text(d => formatValue(d))

  // X-axis title
  g.append('text')
    .attr('x', width / 2)
    .attr('y', height + 36)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(formatMetricLabel(currentMetricKey.value))

  // Draw bars
  const barPad = 1

  if (hasCats) {
    // Stacked bars
    bins.forEach((bin, bi) => {
      let yOffset = 0
      const barWidth = Math.max(1, x(bin.x1) - x(bin.x0) - barPad)
      for (const cat of categories.value) {
        const count = bin.cats[cat] || 0
        if (count === 0) continue
        const barHeight = height - y(count)

        g.append('rect')
          .attr('x', x(bin.x0) + barPad / 2)
          .attr('y', height)
          .attr('width', barWidth)
          .attr('height', 0)
          .attr('fill', categoryColorMap.value[cat])
          .attr('opacity', 0.8)
          .attr('rx', 1)
          .attr('cursor', 'pointer')
          .on('click', () => emit('bin-click', { metric: currentMetricKey.value, x0: bin.x0, x1: bin.x1, items: bin.items }))
          .transition()
          .duration(500)
          .delay(bi * 20)
          .ease(d3.easeCubicOut)
          .attr('y', y(yOffset + count))
          .attr('height', barHeight)

        yOffset += count
      }
    })
  } else {
    g.selectAll('.bar')
      .data(bins)
      .join('rect')
      .attr('x', d => x(d.x0) + barPad / 2)
      .attr('y', height)
      .attr('width', d => Math.max(1, x(d.x1) - x(d.x0) - barPad))
      .attr('height', 0)
      .attr('fill', COLORS.primary)
      .attr('opacity', 0.8)
      .attr('rx', 1)
      .attr('cursor', 'pointer')
      .on('click', (_, d) => emit('bin-click', { metric: currentMetricKey.value, x0: d.x0, x1: d.x1, items: d.items }))
      .transition()
      .duration(500)
      .delay((_, i) => i * 20)
      .ease(d3.easeCubicOut)
      .attr('y', d => y(d.total))
      .attr('height', d => height - y(d.total))
  }

  // Normal distribution overlay
  if (s.isNormal && s.std > 0) {
    const normalPoints = []
    const xMin = x.domain()[0]
    const xMax = x.domain()[1]
    const step = (xMax - xMin) / 100
    const binWidth = bins.length > 1 ? bins[0].x1 - bins[0].x0 : 1
    const scaleFactor = data.length * binWidth

    for (let xv = xMin; xv <= xMax; xv += step) {
      const exponent = -0.5 * Math.pow((xv - s.mean) / s.std, 2)
      const pdf = (1 / (s.std * Math.sqrt(2 * Math.PI))) * Math.exp(exponent)
      normalPoints.push({ x: xv, y: pdf * scaleFactor })
    }

    const line = d3.line()
      .x(d => x(d.x))
      .y(d => y(d.y))
      .curve(d3.curveBasis)

    const path = g.append('path')
      .datum(normalPoints)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', COLORS.orange)
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '6,3')
      .attr('opacity', 0.7)

    const totalLength = path.node().getTotalLength()
    path
      .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
      .attr('stroke-dashoffset', totalLength)
      .transition()
      .duration(800)
      .delay(400)
      .ease(d3.easeCubicOut)
      .attr('stroke-dashoffset', 0)
      .on('end', function () {
        d3.select(this).attr('stroke-dasharray', '6,3')
      })
  }

  // Statistical markers
  renderStatMarkers(g, x, y, height, s)

  // Tooltip
  renderHistogramTooltip(container, g, bins, x, y, height, hasCats)
}

function renderStatMarkers(g, x, y, height, s) {
  const markers = [
    { label: 'Mean', value: s.mean, color: COLORS.primary, dash: 'none' },
    { label: 'Median', value: s.median, color: COLORS.green, dash: '4,2' },
    { label: 'Mode', value: s.mode, color: COLORS.purple, dash: '2,2' },
  ]

  const markerGroup = g.append('g').attr('class', 'stat-markers')

  markers.forEach((m, i) => {
    const xPos = x(m.value)
    if (xPos < 0 || xPos > x.range()[1]) return

    markerGroup.append('line')
      .attr('x1', xPos)
      .attr('x2', xPos)
      .attr('y1', 0)
      .attr('y2', height)
      .attr('stroke', m.color)
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', m.dash)
      .attr('opacity', 0)
      .transition()
      .duration(300)
      .delay(600 + i * 80)
      .attr('opacity', 0.7)

    markerGroup.append('text')
      .attr('x', xPos)
      .attr('y', -4)
      .attr('text-anchor', 'middle')
      .attr('font-size', '9px')
      .attr('font-weight', '600')
      .attr('fill', m.color)
      .attr('opacity', 0)
      .text(`${m.label}: ${formatValue(m.value)}`)
      .transition()
      .duration(300)
      .delay(600 + i * 80)
      .attr('opacity', 1)
  })
}

function renderHistogramTooltip(container, g, bins, x, y, height, hasCats) {
  const tooltip = d3.select(container)
    .append('div')
    .style('position', 'absolute')
    .style('pointer-events', 'none')
    .style('opacity', 0)
    .style('background', 'var(--color-surface, #fff)')
    .style('border', '1px solid var(--color-border, rgba(0,0,0,0.1))')
    .style('border-radius', '8px')
    .style('padding', '8px 12px')
    .style('font-size', '12px')
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.1)')
    .style('z-index', '10')

  g.selectAll('.hover-target')
    .data(bins)
    .join('rect')
    .attr('x', d => x(d.x0))
    .attr('y', 0)
    .attr('width', d => Math.max(1, x(d.x1) - x(d.x0)))
    .attr('height', height)
    .attr('fill', 'transparent')
    .attr('cursor', 'pointer')
    .on('mouseenter', (event, d) => {
      let catBreakdown = ''
      if (hasCats && d.cats) {
        catBreakdown = Object.entries(d.cats)
          .filter(([, v]) => v > 0)
          .map(([cat, v]) => `<span style="color:${categoryColorMap.value[cat]}">${cat}: ${v}</span>`)
          .join(' · ')
        catBreakdown = `<div style="margin-top:4px;font-size:11px">${catBreakdown}</div>`
      }
      tooltip
        .html(`
          <div style="font-weight:600;color:var(--color-text,#050505)">${formatValue(d.x0)} – ${formatValue(d.x1)}</div>
          <div style="color:var(--color-text-muted,#888);margin-top:2px">${d.total} simulation${d.total !== 1 ? 's' : ''}</div>
          ${catBreakdown}
          <div style="color:${COLORS.primary};font-size:10px;margin-top:4px">Click to view details</div>
        `)
        .style('opacity', 1)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 40}px`)
    })
    .on('mouseleave', () => tooltip.style('opacity', 0))
    .on('click', (_, d) => emit('bin-click', { metric: currentMetricKey.value, x0: d.x0, x1: d.x1, items: d.items }))
}

function renderBoxPlot(container, containerWidth) {
  const s = stats.value
  if (!s) return

  const margin = { top: 16, right: 20, bottom: 44, left: 48 }
  const width = containerWidth - margin.left - margin.right
  const height = 160
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3.scaleLinear()
    .domain([s.min - (s.max - s.min) * 0.05, s.max + (s.max - s.min) * 0.05])
    .range([0, width])

  const cy = height / 2
  const boxHeight = 48

  // Grid lines
  const xTicks = x.ticks(8)
  g.selectAll('.grid')
    .data(xTicks)
    .join('line')
    .attr('x1', d => x(d))
    .attr('x2', d => x(d))
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  // X-axis labels
  g.selectAll('.x-label')
    .data(xTicks)
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 18)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text(d => formatValue(d))

  // X-axis title
  g.append('text')
    .attr('x', width / 2)
    .attr('y', height + 36)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(formatMetricLabel(currentMetricKey.value))

  // Whisker line
  g.append('line')
    .attr('x1', x(s.whiskerLow))
    .attr('x2', x(s.whiskerLow))
    .attr('y1', cy)
    .attr('y2', cy)
    .attr('stroke', COLORS.text)
    .attr('stroke-width', 1.5)
    .transition()
    .duration(500)
    .ease(d3.easeCubicOut)
    .attr('x2', x(s.whiskerHigh))

  // Whisker end caps
  for (const val of [s.whiskerLow, s.whiskerHigh]) {
    g.append('line')
      .attr('x1', x(val))
      .attr('x2', x(val))
      .attr('y1', cy - boxHeight / 4)
      .attr('y2', cy + boxHeight / 4)
      .attr('stroke', COLORS.text)
      .attr('stroke-width', 1.5)
      .attr('opacity', 0)
      .transition()
      .duration(300)
      .delay(400)
      .attr('opacity', 1)
  }

  // IQR box
  g.append('rect')
    .attr('x', x(s.q1))
    .attr('y', cy - boxHeight / 2)
    .attr('width', 0)
    .attr('height', boxHeight)
    .attr('rx', 3)
    .attr('fill', COLORS.primary)
    .attr('opacity', 0.2)
    .attr('stroke', COLORS.primary)
    .attr('stroke-width', 1.5)
    .transition()
    .duration(500)
    .delay(200)
    .ease(d3.easeCubicOut)
    .attr('width', x(s.q3) - x(s.q1))

  // Median line
  g.append('line')
    .attr('x1', x(s.median))
    .attr('x2', x(s.median))
    .attr('y1', cy - boxHeight / 2)
    .attr('y2', cy + boxHeight / 2)
    .attr('stroke', COLORS.green)
    .attr('stroke-width', 2)
    .attr('opacity', 0)
    .transition()
    .duration(300)
    .delay(500)
    .attr('opacity', 1)

  // Mean marker (diamond)
  g.append('path')
    .attr('d', d3.symbol().type(d3.symbolDiamond).size(60)())
    .attr('transform', `translate(${x(s.mean)},${cy})`)
    .attr('fill', COLORS.orange)
    .attr('opacity', 0)
    .transition()
    .duration(300)
    .delay(550)
    .attr('opacity', 1)

  // Outlier dots
  if (s.outliers.length) {
    g.selectAll('.outlier')
      .data(s.outliers)
      .join('circle')
      .attr('cx', d => x(d))
      .attr('cy', cy)
      .attr('r', 0)
      .attr('fill', 'none')
      .attr('stroke', COLORS.orange)
      .attr('stroke-width', 1)
      .transition()
      .duration(300)
      .delay((_, i) => 600 + i * 30)
      .attr('r', 3)
  }

  // Labels
  const labels = [
    { text: `Min: ${formatValue(s.whiskerLow)}`, x: x(s.whiskerLow), anchor: 'middle' },
    { text: `Q1: ${formatValue(s.q1)}`, x: x(s.q1), anchor: 'middle' },
    { text: `Median: ${formatValue(s.median)}`, x: x(s.median), anchor: 'middle' },
    { text: `Q3: ${formatValue(s.q3)}`, x: x(s.q3), anchor: 'middle' },
    { text: `Max: ${formatValue(s.whiskerHigh)}`, x: x(s.whiskerHigh), anchor: 'middle' },
  ]

  g.selectAll('.box-label')
    .data(labels)
    .join('text')
    .attr('x', d => d.x)
    .attr('y', cy + boxHeight / 2 + 16)
    .attr('text-anchor', d => d.anchor)
    .attr('font-size', '9px')
    .attr('fill', '#888')
    .attr('opacity', 0)
    .text(d => d.text)
    .transition()
    .duration(300)
    .delay(600)
    .attr('opacity', 1)

  // Mean label above
  g.append('text')
    .attr('x', x(s.mean))
    .attr('y', cy - boxHeight / 2 - 8)
    .attr('text-anchor', 'middle')
    .attr('font-size', '9px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.orange)
    .attr('opacity', 0)
    .text(`Mean: ${formatValue(s.mean)}`)
    .transition()
    .duration(300)
    .delay(600)
    .attr('opacity', 1)

  // Tooltip on box
  const tooltip = d3.select(container)
    .append('div')
    .style('position', 'absolute')
    .style('pointer-events', 'none')
    .style('opacity', 0)
    .style('background', 'var(--color-surface, #fff)')
    .style('border', '1px solid var(--color-border, rgba(0,0,0,0.1))')
    .style('border-radius', '8px')
    .style('padding', '8px 12px')
    .style('font-size', '12px')
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.1)')
    .style('z-index', '10')

  g.append('rect')
    .attr('x', 0)
    .attr('y', 0)
    .attr('width', width)
    .attr('height', height)
    .attr('fill', 'transparent')
    .on('mouseenter', () => {
      tooltip
        .html(`
          <div style="font-weight:600;color:var(--color-text,#050505)">${formatMetricLabel(currentMetricKey.value)}</div>
          <div style="display:grid;grid-template-columns:auto auto;gap:2px 12px;margin-top:6px;font-size:11px">
            <span style="color:#888">N:</span><span style="font-weight:600">${s.n}</span>
            <span style="color:#888">Mean:</span><span style="color:${COLORS.orange};font-weight:600">${formatValue(s.mean)}</span>
            <span style="color:#888">Median:</span><span style="color:${COLORS.green};font-weight:600">${formatValue(s.median)}</span>
            <span style="color:#888">Std Dev:</span><span>${formatValue(s.std)}</span>
            <span style="color:#888">IQR:</span><span>${formatValue(s.q1)} – ${formatValue(s.q3)}</span>
            <span style="color:#888">Outliers:</span><span>${s.outliers.length}</span>
          </div>
        `)
        .style('opacity', 1)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 40}px`)
    })
    .on('mouseleave', () => tooltip.style('opacity', 0))
}

// --- Formatting helpers ---

function formatValue(v) {
  if (v == null) return '—'
  if (Math.abs(v) >= 1000) return d3.format(',.0f')(v)
  if (Math.abs(v) >= 1) return d3.format('.1f')(v)
  return d3.format('.2f')(v)
}

function formatMetricLabel(key) {
  if (!key) return ''
  return key
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .replace(/^\w/, c => c.toUpperCase())
    .trim()
}

// --- Lifecycle ---

watch([activeMetric, viewMode, () => props.outcomes.length], () => {
  nextTick(() => renderChart())
})

onMounted(() => {
  renderChart()
  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(renderChart, 200)
    })
    resizeObserver.observe(chartRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Outcome Distribution</h3>
      <div v-if="metricValues.length" class="flex gap-1 bg-[var(--color-tint)] rounded-md p-0.5">
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="viewMode === 'histogram'
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="viewMode = 'histogram'"
        >
          Histogram
        </button>
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="viewMode === 'boxplot'
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="viewMode = 'boxplot'"
        >
          Box Plot
        </button>
      </div>
    </div>

    <!-- Metric tabs -->
    <div v-if="availableMetrics.length > 1" class="flex gap-1 mb-4 overflow-x-auto pb-1">
      <button
        v-for="(metric, i) in availableMetrics"
        :key="metric"
        class="px-3 py-1.5 text-xs rounded-md font-medium transition-colors whitespace-nowrap"
        :class="activeMetric === i
          ? 'bg-[#2068FF] text-white'
          : 'bg-[var(--color-tint)] text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
        @click="activeMetric = i"
      >
        {{ formatMetricLabel(metric) }}
      </button>
    </div>

    <!-- Chart -->
    <div v-if="metricValues.length" class="relative" ref="chartRef" style="min-height: 200px" />

    <!-- Empty state -->
    <div v-else class="flex items-center justify-center h-[200px] text-[var(--color-text-muted)] text-sm">
      <span>No outcome data available</span>
    </div>

    <!-- Legend / Stats summary -->
    <div v-if="stats" class="flex items-center gap-4 mt-3 flex-wrap">
      <!-- Category legend -->
      <template v-if="categories.length > 1 && viewMode === 'histogram'">
        <span
          v-for="cat in categories"
          :key="cat"
          class="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]"
        >
          <span class="inline-block w-2.5 h-2.5 rounded-sm" :style="{ background: categoryColorMap[cat] }" />
          {{ cat }}
        </span>
      </template>

      <!-- Stat markers legend -->
      <div class="flex items-center gap-3 text-xs text-[var(--color-text-muted)] ml-auto">
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-3 h-0.5" style="background: #2068FF" /> Mean
        </span>
        <span class="flex items-center gap-1.5">
          <span class="inline-block w-3 h-0.5" style="background: #009900" /> Median
        </span>
        <template v-if="viewMode === 'histogram'">
          <span class="flex items-center gap-1.5">
            <span class="inline-block w-3 h-0.5 border-t border-dashed" style="border-color: #AA00FF" /> Mode
          </span>
          <span v-if="stats.isNormal" class="flex items-center gap-1.5">
            <span class="inline-block w-3 h-0.5 border-t border-dashed" style="border-color: #ff5600" /> Normal
          </span>
        </template>
        <span class="text-[10px] opacity-60">n={{ stats.n }}</span>
      </div>
    </div>
  </div>
</template>
