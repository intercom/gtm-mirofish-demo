<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const COLORS = {
  primary: '#2068FF',
  orange: '#ff5600',
  purple: '#AA00FF',
  green: '#009900',
  amber: '#FFB800',
  text: '#050505',
  muted: '#888',
  gridLine: 'rgba(0,0,0,0.06)',
}

const PALETTE = [COLORS.primary, COLORS.orange, COLORS.purple, COLORS.green, COLORS.amber, '#00A1E0', '#E91E63', '#607D8B']

const chartSections = [
  { id: 'radar', title: 'Radar Chart', subtitle: 'Agent personality comparison across key dimensions' },
  { id: 'parallel', title: 'Parallel Coordinates', subtitle: 'Multi-dimensional account analysis' },
  { id: 'chord', title: 'Chord Diagram', subtitle: 'Agent communication flow and interaction volume' },
  { id: 'sunburst', title: 'Sunburst Chart', subtitle: 'Revenue hierarchy breakdown by segment' },
  { id: 'stream', title: 'Stream Graph', subtitle: 'Topic evolution over simulation rounds' },
  { id: 'bullet', title: 'Bullet Charts', subtitle: 'KPI target achievement comparison' },
  { id: 'calendar', title: 'Calendar Heatmap', subtitle: 'Daily activity intensity over time' },
  { id: 'smallmult', title: 'Small Multiples', subtitle: 'Monthly engagement comparisons across channels' },
]

const chartRefs = ref({})
const activeChart = ref(null)
let resizeObserver = null
let resizeTimer = null

function setChartRef(id) {
  return (el) => {
    if (el) chartRefs.value[id] = el
  }
}

function scrollToChart(id) {
  activeChart.value = id
  const el = chartRefs.value[id]
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const RENDER_MAP = {
  radar: renderRadar,
  parallel: renderParallelCoords,
  chord: renderChord,
  sunburst: renderSunburst,
  stream: renderStream,
  bullet: renderBullet,
  calendar: renderCalendar,
  smallmult: renderSmallMultiples,
}

function renderAll() {
  for (const section of chartSections) {
    const container = chartRefs.value[section.id]
    if (container) {
      d3.select(container).selectAll('svg').remove()
      nextTick(() => RENDER_MAP[section.id]?.(container))
    }
  }
}

// ── Radar Chart ─────────────────────────────────────────────

function renderRadar(container) {
  const agents = [
    { name: 'VP Support', values: [0.85, 0.72, 0.60, 0.90, 0.55, 0.78] },
    { name: 'CX Director', values: [0.65, 0.88, 0.75, 0.55, 0.80, 0.60] },
    { name: 'IT Leader', values: [0.50, 0.45, 0.92, 0.40, 0.70, 0.85] },
  ]
  const axes = ['Engagement', 'Influence', 'Technical', 'Sentiment', 'Reach', 'Consistency']
  const agentColors = [COLORS.primary, COLORS.orange, COLORS.purple]

  const w = container.clientWidth
  const size = Math.min(w, 460)
  const cx = w / 2
  const cy = size / 2 + 10
  const radius = size / 2 - 60
  const levels = 5
  const angleSlice = (Math.PI * 2) / axes.length

  const svg = d3.select(container)
    .append('svg')
    .attr('width', w)
    .attr('height', size + 50)

  const g = svg.append('g').attr('transform', `translate(${cx},${cy})`)

  // Grid circles
  for (let lvl = 1; lvl <= levels; lvl++) {
    const r = (radius / levels) * lvl
    g.append('circle')
      .attr('r', r)
      .attr('fill', 'none')
      .attr('stroke', COLORS.gridLine)
      .attr('stroke-dasharray', '2,3')
  }

  // Axes
  axes.forEach((axis, i) => {
    const angle = angleSlice * i - Math.PI / 2
    const x2 = Math.cos(angle) * radius
    const y2 = Math.sin(angle) * radius

    g.append('line')
      .attr('x1', 0).attr('y1', 0)
      .attr('x2', x2).attr('y2', y2)
      .attr('stroke', COLORS.gridLine)

    const labelR = radius + 20
    g.append('text')
      .attr('x', Math.cos(angle) * labelR)
      .attr('y', Math.sin(angle) * labelR)
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('font-size', '11px')
      .attr('fill', COLORS.muted)
      .text(axis)
  })

  // Agent polygons
  agents.forEach((agent, ai) => {
    const points = agent.values.map((v, i) => {
      const angle = angleSlice * i - Math.PI / 2
      return [Math.cos(angle) * radius * v, Math.sin(angle) * radius * v]
    })

    const line = d3.lineRadial()
      .radius((d, i) => agent.values[i] * radius)
      .angle((d, i) => i * angleSlice)
      .curve(d3.curveLinearClosed)

    g.append('path')
      .datum(agent.values)
      .attr('d', line)
      .attr('fill', agentColors[ai])
      .attr('fill-opacity', 0.1)
      .attr('stroke', agentColors[ai])
      .attr('stroke-width', 2)
      .attr('opacity', 0)
      .transition()
      .duration(500)
      .delay(ai * 150)
      .attr('opacity', 1)

    // Data points
    points.forEach(([px, py]) => {
      g.append('circle')
        .attr('cx', px).attr('cy', py)
        .attr('r', 3)
        .attr('fill', agentColors[ai])
        .attr('opacity', 0)
        .transition()
        .duration(300)
        .delay(ai * 150 + 200)
        .attr('opacity', 1)
    })
  })

  // Legend
  const legend = svg.append('g').attr('transform', `translate(${w / 2 - 120}, ${size + 20})`)
  agents.forEach((agent, i) => {
    const lx = i * 100
    legend.append('circle').attr('cx', lx).attr('cy', 0).attr('r', 5).attr('fill', agentColors[i])
    legend.append('text').attr('x', lx + 10).attr('y', 4).attr('font-size', '11px').attr('fill', COLORS.text).text(agent.name)
  })
}

// ── Parallel Coordinates ────────────────────────────────────

function renderParallelCoords(container) {
  const dimensions = ['Deal Size', 'Engagement', 'Tech Fit', 'Budget Auth', 'Timeline']
  const accounts = [
    { name: 'Acme Corp', values: [85, 72, 90, 60, 45], color: COLORS.primary },
    { name: 'TechStart Inc', values: [40, 95, 75, 80, 85], color: COLORS.orange },
    { name: 'GlobalBank', values: [95, 50, 60, 90, 30], color: COLORS.purple },
    { name: 'HealthPlus', values: [60, 80, 85, 55, 70], color: COLORS.green },
    { name: 'RetailMax', values: [75, 65, 50, 70, 60], color: COLORS.amber },
  ]

  const w = container.clientWidth
  const margin = { top: 30, right: 30, bottom: 20, left: 30 }
  const width = w - margin.left - margin.right
  const height = 280

  const svg = d3.select(container)
    .append('svg')
    .attr('width', w)
    .attr('height', height + margin.top + margin.bottom)

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3.scalePoint().domain(dimensions).range([0, width])
  const yScales = {}
  dimensions.forEach(dim => {
    yScales[dim] = d3.scaleLinear().domain([0, 100]).range([height, 0])
  })

  // Axes
  dimensions.forEach(dim => {
    const axisG = g.append('g').attr('transform', `translate(${x(dim)},0)`)
    axisG.call(d3.axisLeft(yScales[dim]).ticks(5).tickSize(0))
      .selectAll('text').attr('font-size', '9px').attr('fill', COLORS.muted)
    axisG.select('.domain').attr('stroke', COLORS.gridLine)

    axisG.append('text')
      .attr('y', -12)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', COLORS.text)
      .text(dim)
  })

  // Lines
  const line = d3.line()
  accounts.forEach((account, ai) => {
    const points = dimensions.map((dim, i) => [x(dim), yScales[dim](account.values[i])])

    g.append('path')
      .datum(points)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', account.color)
      .attr('stroke-width', 2.5)
      .attr('stroke-opacity', 0.7)
      .attr('stroke-dasharray', function () { return this.getTotalLength() })
      .attr('stroke-dashoffset', function () { return this.getTotalLength() })
      .transition()
      .duration(800)
      .delay(ai * 120)
      .ease(d3.easeCubicOut)
      .attr('stroke-dashoffset', 0)

    // Dots on each axis
    points.forEach(([px, py]) => {
      g.append('circle')
        .attr('cx', px).attr('cy', py)
        .attr('r', 4)
        .attr('fill', account.color)
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5)
        .attr('opacity', 0)
        .transition()
        .duration(300)
        .delay(ai * 120 + 600)
        .attr('opacity', 1)
    })
  })

  // Legend
  const legend = svg.append('g').attr('transform', `translate(${margin.left}, ${height + margin.top + 14})`)
  accounts.forEach((a, i) => {
    const lx = i * (width / accounts.length)
    legend.append('circle').attr('cx', lx).attr('cy', 0).attr('r', 4).attr('fill', a.color)
    legend.append('text').attr('x', lx + 8).attr('y', 4).attr('font-size', '10px').attr('fill', COLORS.text).text(a.name)
  })
}

// ── Chord Diagram ───────────────────────────────────────────

function renderChord(container) {
  const names = ['VP Support', 'CX Director', 'IT Leader', 'Ops Manager', 'CFO']
  const matrix = [
    [0, 25, 15, 10, 5],
    [20, 0, 18, 12, 8],
    [10, 22, 0, 20, 6],
    [8, 10, 15, 0, 14],
    [4, 6, 8, 12, 0],
  ]

  const w = container.clientWidth
  const size = Math.min(w, 420)
  const outerRadius = size / 2 - 50
  const innerRadius = outerRadius - 20

  const svg = d3.select(container)
    .append('svg')
    .attr('width', w)
    .attr('height', size)

  const g = svg.append('g').attr('transform', `translate(${w / 2},${size / 2})`)

  const chord = d3.chord().padAngle(0.05).sortSubgroups(d3.descending)
  const chords = chord(matrix)

  const arc = d3.arc().innerRadius(innerRadius).outerRadius(outerRadius)
  const ribbon = d3.ribbon().radius(innerRadius)

  const color = d3.scaleOrdinal().domain(d3.range(names.length)).range(PALETTE)

  // Arcs
  g.selectAll('.arc')
    .data(chords.groups)
    .join('path')
    .attr('d', arc)
    .attr('fill', d => color(d.index))
    .attr('stroke', '#fff')
    .attr('stroke-width', 1)
    .attr('opacity', 0)
    .transition()
    .duration(500)
    .delay((d, i) => i * 80)
    .attr('opacity', 0.85)

  // Labels
  g.selectAll('.label')
    .data(chords.groups)
    .join('text')
    .each(function (d) {
      const angle = (d.startAngle + d.endAngle) / 2
      d3.select(this)
        .attr('transform', `rotate(${(angle * 180 / Math.PI) - 90}) translate(${outerRadius + 12})${angle > Math.PI ? ' rotate(180)' : ''}`)
        .attr('text-anchor', angle > Math.PI ? 'end' : 'start')
    })
    .attr('font-size', '11px')
    .attr('fill', COLORS.text)
    .text((d, i) => names[i])
    .attr('opacity', 0)
    .transition()
    .duration(400)
    .delay(500)
    .attr('opacity', 1)

  // Ribbons
  g.selectAll('.ribbon')
    .data(chords)
    .join('path')
    .attr('d', ribbon)
    .attr('fill', d => color(d.source.index))
    .attr('fill-opacity', 0)
    .attr('stroke', '#fff')
    .attr('stroke-width', 0.5)
    .transition()
    .duration(600)
    .delay((d, i) => 400 + i * 30)
    .attr('fill-opacity', 0.35)
}

// ── Sunburst Chart ──────────────────────────────────────────

function renderSunburst(container) {
  const data = {
    name: 'Revenue',
    children: [
      {
        name: 'Enterprise',
        children: [
          { name: 'Healthcare', value: 340 },
          { name: 'Finance', value: 280 },
          { name: 'Tech', value: 420 },
        ],
      },
      {
        name: 'Mid-Market',
        children: [
          { name: 'SaaS', value: 220 },
          { name: 'Retail', value: 180 },
          { name: 'Manufacturing', value: 140 },
        ],
      },
      {
        name: 'SMB',
        children: [
          { name: 'Startups', value: 160 },
          { name: 'Agencies', value: 90 },
        ],
      },
    ],
  }

  const w = container.clientWidth
  const size = Math.min(w, 440)
  const radius = size / 2

  const svg = d3.select(container)
    .append('svg')
    .attr('width', w)
    .attr('height', size)

  const g = svg.append('g').attr('transform', `translate(${w / 2},${size / 2})`)

  const root = d3.hierarchy(data).sum(d => d.value).sort((a, b) => b.value - a.value)
  const partition = d3.partition().size([2 * Math.PI, radius])
  partition(root)

  const color = d3.scaleOrdinal()
    .domain(['Enterprise', 'Mid-Market', 'SMB'])
    .range([COLORS.primary, COLORS.orange, COLORS.green])

  function getColor(d) {
    while (d.depth > 1) d = d.parent
    return d.depth === 0 ? '#ddd' : color(d.data.name)
  }

  const arc = d3.arc()
    .startAngle(d => d.x0)
    .endAngle(d => d.x1)
    .padAngle(0.01)
    .padRadius(radius / 2)
    .innerRadius(d => d.y0 * 0.7)
    .outerRadius(d => d.y1 * 0.7 - 1)

  g.selectAll('path')
    .data(root.descendants().filter(d => d.depth))
    .join('path')
    .attr('fill', d => getColor(d))
    .attr('fill-opacity', d => d.depth === 1 ? 0.85 : 0.6)
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)
    .transition()
    .duration(600)
    .delay((d, i) => i * 40)
    .attrTween('d', function (d) {
      const interp = d3.interpolate({ x0: d.x0, x1: d.x0, y0: d.y0, y1: d.y1 }, d)
      return t => arc(interp(t))
    })

  // Center label
  g.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '-0.2em')
    .attr('font-size', '18px')
    .attr('font-weight', '700')
    .attr('fill', COLORS.text)
    .text('$1.83M')
    .attr('opacity', 0)
    .transition().delay(400).duration(300).attr('opacity', 1)

  g.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '1.2em')
    .attr('font-size', '11px')
    .attr('fill', COLORS.muted)
    .text('Total Pipeline')
    .attr('opacity', 0)
    .transition().delay(450).duration(300).attr('opacity', 1)

  // Leaf labels
  g.selectAll('.leaf-label')
    .data(root.leaves())
    .join('text')
    .attr('transform', function (d) {
      const angle = (d.x0 + d.x1) / 2
      const r = (d.y0 + d.y1) / 2 * 0.7
      const rotate = (angle * 180 / Math.PI) - 90
      return `rotate(${rotate}) translate(${r},0) rotate(${rotate > 90 ? 180 : 0})`
    })
    .attr('text-anchor', d => {
      const angle = (d.x0 + d.x1) / 2
      return ((angle * 180 / Math.PI) - 90) > 90 ? 'end' : 'start'
    })
    .attr('dy', '0.35em')
    .attr('font-size', '9px')
    .attr('fill', COLORS.text)
    .text(d => d.data.name)
    .attr('opacity', 0)
    .transition().delay(700).duration(300).attr('opacity', 0.8)
}

// ── Stream Graph ────────────────────────────────────────────

function renderStream(container) {
  const topics = ['AI Support', 'Pricing', 'Integration', 'Migration', 'ROI']
  const rounds = 20
  const streamData = []

  for (let r = 0; r < rounds; r++) {
    const row = { round: r + 1 }
    topics.forEach((t, i) => {
      const base = [30, 20, 25, 15, 18][i]
      const wave = Math.sin((r + i * 3) * 0.4) * 10
      const trend = i === 0 ? r * 0.8 : i === 3 ? -r * 0.3 : 0
      row[t] = Math.max(2, base + wave + trend + (Math.sin(r * 0.7 + i) * 5))
    })
    streamData.push(row)
  }

  const w = container.clientWidth
  const margin = { top: 10, right: 20, bottom: 40, left: 40 }
  const width = w - margin.left - margin.right
  const height = 280

  const svg = d3.select(container)
    .append('svg')
    .attr('width', w)
    .attr('height', height + margin.top + margin.bottom)

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const stack = d3.stack()
    .keys(topics)
    .offset(d3.stackOffsetWiggle)
    .order(d3.stackOrderInsideOut)

  const series = stack(streamData)

  const x = d3.scaleLinear().domain([1, rounds]).range([0, width])
  const y = d3.scaleLinear()
    .domain([d3.min(series, s => d3.min(s, d => d[0])), d3.max(series, s => d3.max(s, d => d[1]))])
    .range([height, 0])

  const area = d3.area()
    .x(d => x(d.data.round))
    .y0(d => y(d[0]))
    .y1(d => y(d[1]))
    .curve(d3.curveBasis)

  g.selectAll('.stream')
    .data(series)
    .join('path')
    .attr('d', area)
    .attr('fill', (d, i) => PALETTE[i])
    .attr('fill-opacity', 0)
    .attr('stroke', 'none')
    .transition()
    .duration(800)
    .delay((d, i) => i * 100)
    .attr('fill-opacity', 0.7)

  // X axis
  g.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x).ticks(10).tickFormat(d => `R${d}`))
    .selectAll('text').attr('font-size', '9px').attr('fill', COLORS.muted)

  g.select('.domain').attr('stroke', COLORS.gridLine)

  // Legend
  const legend = svg.append('g').attr('transform', `translate(${margin.left}, ${height + margin.top + 28})`)
  topics.forEach((t, i) => {
    const lx = i * (width / topics.length)
    legend.append('rect').attr('x', lx).attr('y', -5).attr('width', 10).attr('height', 10).attr('rx', 2).attr('fill', PALETTE[i]).attr('opacity', 0.7)
    legend.append('text').attr('x', lx + 14).attr('y', 4).attr('font-size', '10px').attr('fill', COLORS.text).text(t)
  })
}

// ── Bullet Charts ───────────────────────────────────────────

function renderBullet(container) {
  const kpis = [
    { label: 'Pipeline ($M)', actual: 1.83, target: 2.0, ranges: [1.0, 1.5, 2.5] },
    { label: 'Win Rate (%)', actual: 34, target: 40, ranges: [20, 30, 50] },
    { label: 'Avg Deal ($K)', actual: 48, target: 55, ranges: [30, 45, 70] },
    { label: 'NPS Score', actual: 72, target: 80, ranges: [50, 65, 100] },
    { label: 'Meetings/Wk', actual: 18, target: 20, ranges: [10, 15, 25] },
  ]

  const w = container.clientWidth
  const margin = { top: 10, right: 30, bottom: 10, left: 110 }
  const barHeight = 28
  const barGap = 18
  const width = w - margin.left - margin.right
  const height = kpis.length * (barHeight + barGap)

  const svg = d3.select(container)
    .append('svg')
    .attr('width', w)
    .attr('height', height + margin.top + margin.bottom)

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  kpis.forEach((kpi, i) => {
    const y = i * (barHeight + barGap)
    const x = d3.scaleLinear().domain([0, kpi.ranges[2]]).range([0, width])

    // Range backgrounds (poor, satisfactory, good)
    const rangeColors = ['rgba(0,0,0,0.12)', 'rgba(0,0,0,0.06)', 'rgba(0,0,0,0.02)']
    const rangePairs = [[0, kpi.ranges[0]], [kpi.ranges[0], kpi.ranges[1]], [kpi.ranges[1], kpi.ranges[2]]]
    rangePairs.forEach(([start, end], ri) => {
      g.append('rect')
        .attr('x', x(start)).attr('y', y)
        .attr('width', x(end) - x(start)).attr('height', barHeight)
        .attr('fill', rangeColors[ri])
        .attr('rx', ri === 0 ? 3 : 0)
    })

    // Actual bar
    g.append('rect')
      .attr('x', 0).attr('y', y + barHeight * 0.25)
      .attr('width', 0).attr('height', barHeight * 0.5)
      .attr('rx', 2)
      .attr('fill', kpi.actual >= kpi.target ? COLORS.green : COLORS.primary)
      .attr('opacity', 0.85)
      .transition()
      .duration(600)
      .delay(i * 80)
      .attr('width', x(kpi.actual))

    // Target marker
    g.append('line')
      .attr('x1', x(kpi.target)).attr('x2', x(kpi.target))
      .attr('y1', y + 2).attr('y2', y + barHeight - 2)
      .attr('stroke', COLORS.text)
      .attr('stroke-width', 2.5)
      .attr('opacity', 0)
      .transition()
      .duration(300)
      .delay(i * 80 + 400)
      .attr('opacity', 0.7)

    // Label
    g.append('text')
      .attr('x', -8).attr('y', y + barHeight / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'end')
      .attr('font-size', '12px')
      .attr('fill', COLORS.text)
      .text(kpi.label)

    // Value
    g.append('text')
      .attr('x', x(kpi.actual) + 6).attr('y', y + barHeight / 2)
      .attr('dy', '0.35em')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', kpi.actual >= kpi.target ? COLORS.green : COLORS.primary)
      .style('opacity', 0)
      .text(kpi.actual)
      .transition()
      .duration(300)
      .delay(i * 80 + 500)
      .style('opacity', 1)
  })
}

// ── Calendar Heatmap ────────────────────────────────────────

function renderCalendar(container) {
  const w = container.clientWidth
  const cellSize = Math.min(16, (w - 60) / 53)
  const margin = { top: 20, right: 10, bottom: 10, left: 40 }

  // Generate 6 months of data
  const startDate = new Date(2025, 6, 1)
  const endDate = new Date(2025, 11, 31)
  const data = []
  let d = new Date(startDate)
  while (d <= endDate) {
    const dayOfWeek = d.getDay()
    const weekNum = Math.floor((d - startDate) / (7 * 86400000))
    const base = dayOfWeek === 0 || dayOfWeek === 6 ? 0.2 : 0.5
    const val = Math.min(1, Math.max(0, base + Math.sin(weekNum * 0.5) * 0.3 + Math.random() * 0.3))
    data.push({ date: new Date(d), day: dayOfWeek, week: weekNum, value: val })
    d = new Date(d.getTime() + 86400000)
  }

  const weeks = d3.max(data, d => d.week) + 1
  const height = 7 * (cellSize + 2) + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', w)
    .attr('height', height)

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const colorScale = d3.scaleSequential()
    .domain([0, 1])
    .interpolator(d3.interpolate('#ebedf0', COLORS.primary))

  // Day labels
  const dayLabels = ['', 'Mon', '', 'Wed', '', 'Fri', '']
  dayLabels.forEach((label, i) => {
    if (label) {
      g.append('text')
        .attr('x', -6).attr('y', i * (cellSize + 2) + cellSize / 2)
        .attr('dy', '0.35em')
        .attr('text-anchor', 'end')
        .attr('font-size', '9px')
        .attr('fill', COLORS.muted)
        .text(label)
    }
  })

  // Cells
  g.selectAll('.cell')
    .data(data)
    .join('rect')
    .attr('x', d => d.week * (cellSize + 2))
    .attr('y', d => d.day * (cellSize + 2))
    .attr('width', cellSize)
    .attr('height', cellSize)
    .attr('rx', 2)
    .attr('fill', '#ebedf0')
    .transition()
    .duration(400)
    .delay((d, i) => i * 2)
    .attr('fill', d => colorScale(d.value))

  // Month labels
  const months = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  const weeksPerMonth = [4.4, 4.4, 4.3, 4.4, 4.3, 4.4]
  let weekOffset = 0
  months.forEach((m, i) => {
    g.append('text')
      .attr('x', weekOffset * (cellSize + 2))
      .attr('y', -6)
      .attr('font-size', '9px')
      .attr('fill', COLORS.muted)
      .text(m)
    weekOffset += weeksPerMonth[i]
  })
}

// ── Small Multiples ─────────────────────────────────────────

function renderSmallMultiples(container) {
  const channels = ['Email', 'Social', 'Direct', 'Events']
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
  const channelData = {
    Email: [45, 52, 49, 60, 55, 70],
    Social: [30, 28, 35, 42, 50, 48],
    Direct: [20, 22, 18, 25, 30, 28],
    Events: [10, 15, 40, 12, 35, 45],
  }

  const w = container.clientWidth
  const cols = w > 500 ? 4 : 2
  const cellW = (w - (cols - 1) * 16) / cols
  const cellH = 140
  const margin = { top: 24, right: 8, bottom: 24, left: 28 }
  const rows = Math.ceil(channels.length / cols)
  const totalH = rows * (cellH + 16)

  const svg = d3.select(container)
    .append('svg')
    .attr('width', w)
    .attr('height', totalH)

  channels.forEach((channel, ci) => {
    const col = ci % cols
    const row = Math.floor(ci / cols)
    const gx = col * (cellW + 16)
    const gy = row * (cellH + 16)

    const g = svg.append('g').attr('transform', `translate(${gx},${gy})`)

    // Background
    g.append('rect')
      .attr('width', cellW).attr('height', cellH)
      .attr('rx', 6)
      .attr('fill', 'rgba(0,0,0,0.02)')
      .attr('stroke', COLORS.gridLine)

    // Title
    g.append('text')
      .attr('x', margin.left).attr('y', 16)
      .attr('font-size', '12px')
      .attr('font-weight', '600')
      .attr('fill', COLORS.text)
      .text(channel)

    const plotW = cellW - margin.left - margin.right
    const plotH = cellH - margin.top - margin.bottom
    const plotG = g.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

    const values = channelData[channel]
    const x = d3.scalePoint().domain(months).range([0, plotW]).padding(0.2)
    const y = d3.scaleLinear().domain([0, 80]).range([plotH, 0])

    // Grid lines
    ;[0, 20, 40, 60, 80].forEach(tick => {
      plotG.append('line')
        .attr('x1', 0).attr('x2', plotW)
        .attr('y1', y(tick)).attr('y2', y(tick))
        .attr('stroke', COLORS.gridLine)
        .attr('stroke-dasharray', '2,3')
    })

    // Area
    const area = d3.area()
      .x((d, i) => x(months[i]))
      .y0(plotH)
      .y1(d => y(d))
      .curve(d3.curveMonotoneX)

    plotG.append('path')
      .datum(values)
      .attr('d', area)
      .attr('fill', PALETTE[ci])
      .attr('fill-opacity', 0)
      .transition()
      .duration(600)
      .delay(ci * 100)
      .attr('fill-opacity', 0.15)

    // Line
    const line = d3.line()
      .x((d, i) => x(months[i]))
      .y(d => y(d))
      .curve(d3.curveMonotoneX)

    plotG.append('path')
      .datum(values)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', PALETTE[ci])
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', function () { return this.getTotalLength() })
      .attr('stroke-dashoffset', function () { return this.getTotalLength() })
      .transition()
      .duration(800)
      .delay(ci * 100)
      .ease(d3.easeCubicOut)
      .attr('stroke-dashoffset', 0)

    // Dots
    values.forEach((v, i) => {
      plotG.append('circle')
        .attr('cx', x(months[i])).attr('cy', y(v))
        .attr('r', 3)
        .attr('fill', PALETTE[ci])
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5)
        .attr('opacity', 0)
        .transition()
        .duration(300)
        .delay(ci * 100 + 600)
        .attr('opacity', 1)
    })

    // X labels
    months.forEach(m => {
      plotG.append('text')
        .attr('x', x(m)).attr('y', plotH + 14)
        .attr('text-anchor', 'middle')
        .attr('font-size', '8px')
        .attr('fill', COLORS.muted)
        .text(m)
    })
  })
}

// ── Lifecycle ───────────────────────────────────────────────

onMounted(() => {
  nextTick(() => renderAll())

  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => renderAll(), 200)
  })

  const firstContainer = chartRefs.value[chartSections[0]?.id]
  if (firstContainer?.parentElement) {
    resizeObserver.observe(firstContainer.parentElement)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 md:px-6 py-6 md:py-10">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-xl md:text-2xl font-semibold text-[var(--color-text)]">Charts Gallery</h1>
      <p class="text-sm text-[var(--color-text-secondary)] mt-1">
        Advanced D3 visualizations for GTM simulation data — explore each chart type interactively.
      </p>
    </div>

    <!-- Quick nav -->
    <div class="flex flex-wrap gap-2 mb-8">
      <button
        v-for="section in chartSections"
        :key="section.id"
        @click="scrollToChart(section.id)"
        class="text-xs font-medium px-3 py-1.5 rounded-full border transition-colors"
        :class="activeChart === section.id
          ? 'bg-[#2068FF] text-white border-[#2068FF]'
          : 'border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[#2068FF]/50 hover:text-[#2068FF]'"
      >
        {{ section.title }}
      </button>
    </div>

    <!-- Chart sections -->
    <div class="space-y-8">
      <div
        v-for="section in chartSections"
        :key="section.id"
        class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 md:p-6 scroll-mt-20"
      >
        <div class="mb-4">
          <h2 class="text-base font-semibold text-[var(--color-text)]">{{ section.title }}</h2>
          <p class="text-xs text-[var(--color-text-muted)] mt-0.5">{{ section.subtitle }}</p>
        </div>
        <div :ref="setChartRef(section.id)" class="w-full overflow-hidden" />
      </div>
    </div>
  </div>
</template>
