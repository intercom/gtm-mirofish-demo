<script setup>
import { ref, computed, inject, watch, nextTick, onMounted, onUnmounted } from 'vue'
import * as d3 from 'd3'
import GraphSearch from './GraphSearch.vue'

const props = defineProps({
  taskId: { type: String, required: true },
  demoMode: { type: Boolean, default: false },
})

function isDarkMode() {
  return document.documentElement.classList.contains('dark')
}

// Injected polling data
const polling = inject('polling')
const { graphStatus, graphProgress, graphData, graphId, graphTask, isDemoFallback } = polling

// D3 refs
const svgRef = ref(null)
const containerRef = ref(null)
let simulation = null
let skeletonSim = null
let svg = null
let zoomGroup = null
let zoomBehavior = null
let resizeObserver = null
let resizeTimer = null
let themeObserver = null
let demoBuildTimer = null

// Local state
const selectedNode = ref(null)
const nodeCount = ref(0)
const edgeCount = ref(0)
const errorMsg = ref('')

// Entity type color mapping
const TYPE_COLORS = {
  persona: '#ff5600', person: '#ff5600', agent: '#ff5600', user: '#ff5600',
  customer: '#ff5600', stakeholder: '#ff5600', role: '#ff5600',
  topic: '#2068FF', theme: '#2068FF', subject: '#2068FF', concept: '#2068FF',
  category: '#2068FF', product: '#2068FF', feature: '#2068FF', technology: '#2068FF',
  relationship: '#AA00FF', interaction: '#AA00FF', connection: '#AA00FF',
  event: '#AA00FF', action: '#AA00FF', process: '#AA00FF',
}
const DEFAULT_COLOR = '#667'
const GENERIC_LABELS = new Set(['Entity', 'Node'])

const BUILD_MESSAGES = [
  'Parsing seed document...',
  'Extracting entities...',
  'Building persona nodes...',
  'Mapping topic clusters...',
  'Computing relationships...',
  'Finalizing graph...',
]

function getNodeColor(labels) {
  const meaningful = (labels || []).filter(l => !GENERIC_LABELS.has(l))
  if (!meaningful.length) return DEFAULT_COLOR
  const label = meaningful[0].toLowerCase()
  for (const [key, color] of Object.entries(TYPE_COLORS)) {
    if (label.includes(key)) return color
  }
  const palette = ['#ff5600', '#2068FF', '#AA00FF']
  let hash = 0
  for (const ch of label) hash = ((hash << 5) - hash + ch.charCodeAt(0)) | 0
  return palette[Math.abs(hash) % palette.length]
}

function getEntityType(labels) {
  const meaningful = (labels || []).filter(l => !GENERIC_LABELS.has(l))
  return meaningful[0] || 'Entity'
}

function computeCentrality(nodes, edges) {
  const degree = {}
  for (const n of nodes) degree[n.uuid] = 0
  for (const e of edges) {
    if (degree[e.source_node_uuid] !== undefined) degree[e.source_node_uuid]++
    if (degree[e.target_node_uuid] !== undefined) degree[e.target_node_uuid]++
  }
  const max = Math.max(1, ...Object.values(degree))
  const result = {}
  for (const [id, d] of Object.entries(degree)) result[id] = d / max
  return result
}

const entityTypeStats = computed(() => {
  const counts = {}
  for (const n of graphData.value.nodes) {
    const type = getEntityType(n.labels)
    counts[type] = (counts[type] || 0) + 1
  }
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .map(([type, count]) => ({
      type,
      count,
      color: getNodeColor([type]),
    }))
})

const buildMessage = computed(() => {
  const p = graphProgress.value
  const msgIdx = Math.min(
    Math.floor((p / 100) * BUILD_MESSAGES.length),
    BUILD_MESSAGES.length - 1,
  )
  return graphTask.value?.message || BUILD_MESSAGES[msgIdx] || 'Initializing...'
})

// --- Skeleton Graph (Phase 4A) ---

function renderSkeletonGraph() {
  const container = containerRef.value
  if (!container) return
  const width = container.clientWidth
  const height = container.clientHeight
  if (!width || !height) return

  d3.select(svgRef.value).selectAll('*').remove()

  svg = d3.select(svgRef.value).attr('width', width).attr('height', height)
  zoomGroup = svg.append('g')

  const baseCount = 4
  const progressBonus = Math.floor((graphProgress.value / 100) * 8)
  const count = Math.min(baseCount + progressBonus, 12)

  const skeletonNodes = Array.from({ length: count }, (_, i) => ({
    id: `sk-${i}`,
    x: width / 2 + (Math.random() - 0.5) * width * 0.6,
    y: height / 2 + (Math.random() - 0.5) * height * 0.6,
    radius: 8 + Math.random() * 12,
  }))

  const skeletonEdges = []
  for (let i = 1; i < count; i++) {
    const source = Math.floor(Math.random() * i)
    skeletonEdges.push({ source: skeletonNodes[source], target: skeletonNodes[i] })
  }

  zoomGroup.selectAll('line').data(skeletonEdges).join('line')
    .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
    .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
    .attr('stroke', 'rgba(32,104,255,0.1)').attr('stroke-width', 1)

  const nodeG = zoomGroup.selectAll('circle').data(skeletonNodes).join('circle')
    .attr('cx', d => d.x).attr('cy', d => d.y)
    .attr('r', d => d.radius)
    .attr('fill', 'rgba(32,104,255,0.15)')
    .attr('class', 'skeleton-pulse')

  skeletonSim = d3.forceSimulation(skeletonNodes)
    .force('center', d3.forceCenter(width / 2, height / 2).strength(0.02))
    .force('charge', d3.forceManyBody().strength(-30))
    .force('collision', d3.forceCollide(20))
    .alphaTarget(0.3)
    .on('tick', () => {
      nodeG.attr('cx', d => d.x).attr('cy', d => d.y)
      zoomGroup.selectAll('line')
        .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
    })
}

// --- Real Graph Rendering ---

function renderGraph() {
  if (!svgRef.value || !graphData.value.nodes.length) return

  // Stop skeleton simulation before drawing real graph
  if (skeletonSim) {
    skeletonSim.stop()
    skeletonSim = null
  }

  const dark = isDarkMode()
  const container = containerRef.value
  const width = container.clientWidth
  const height = container.clientHeight

  if (!width || !height) return

  const centrality = computeCentrality(graphData.value.nodes, graphData.value.edges)

  const nodeMap = new Map()
  const nodes = graphData.value.nodes.map(n => {
    const obj = {
      id: n.uuid,
      name: n.name,
      labels: n.labels,
      summary: n.summary || '',
      attributes: n.attributes || {},
      centrality: centrality[n.uuid] || 0,
      color: getNodeColor(n.labels),
      radius: 6 + (centrality[n.uuid] || 0) * 18,
    }
    nodeMap.set(n.uuid, obj)
    return obj
  })

  const links = graphData.value.edges
    .filter(e => nodeMap.has(e.source_node_uuid) && nodeMap.has(e.target_node_uuid))
    .map(e => ({
      source: e.source_node_uuid,
      target: e.target_node_uuid,
      name: e.name || '',
      fact: e.fact || '',
    }))

  nodeCount.value = nodes.length
  edgeCount.value = links.length

  d3.select(svgRef.value).selectAll('*').remove()

  svg = d3.select(svgRef.value)
    .attr('width', width)
    .attr('height', height)

  zoomBehavior = d3.zoom()
    .scaleExtent([0.2, 5])
    .on('zoom', (event) => {
      zoomGroup.attr('transform', event.transform)
    })
  svg.call(zoomBehavior)

  zoomGroup = svg.append('g')

  svg.append('defs').append('marker')
    .attr('id', 'arrow')
    .attr('viewBox', '0 -4 8 8')
    .attr('refX', 20)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-4L8,0L0,4')
    .attr('fill', dark ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.2)')

  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(120))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(d => d.radius + 4))

  const link = zoomGroup.append('g')
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('stroke', dark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.12)')
    .attr('stroke-width', 1)
    .attr('marker-end', 'url(#arrow)')
    .style('opacity', 0)

  const edgeLabel = zoomGroup.append('g')
    .selectAll('text')
    .data(links)
    .join('text')
    .text(d => d.name)
    .attr('fill', dark ? 'rgba(255,255,255,0.35)' : 'rgba(0,0,0,0.3)')
    .attr('font-size', '8px')
    .attr('text-anchor', 'middle')
    .style('pointer-events', 'none')
    .style('opacity', 0)

  const node = zoomGroup.append('g')
    .selectAll('g')
    .data(nodes)
    .join('g')
    .style('cursor', 'pointer')
    .style('opacity', 0)
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended)
    )
    .on('click', (event, d) => {
      event.stopPropagation()
      selectNode(d)
    })

  node.append('circle')
    .attr('r', d => d.radius + 4)
    .attr('fill', d => d.color)
    .attr('opacity', 0.2)

  node.append('circle')
    .attr('r', d => d.radius)
    .attr('fill', d => d.color)
    .attr('stroke', d => d.color)
    .attr('stroke-width', 1.5)
    .attr('stroke-opacity', 0.4)
    .attr('fill-opacity', 0.85)

  node.append('text')
    .text(d => d.name)
    .attr('dy', d => d.radius + 14)
    .attr('text-anchor', 'middle')
    .attr('fill', dark ? 'rgba(255,255,255,0.8)' : 'rgba(0,0,0,0.7)')
    .attr('font-size', '10px')
    .style('pointer-events', 'none')

  node.transition()
    .delay((d, i) => i * 60)
    .duration(400)
    .style('opacity', 1)

  link.transition()
    .delay((d, i) => nodes.length * 60 + i * 30)
    .duration(300)
    .style('opacity', 1)

  edgeLabel.transition()
    .delay((d, i) => nodes.length * 60 + i * 30)
    .duration(300)
    .style('opacity', 1)

  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)

    edgeLabel
      .attr('x', d => (d.source.x + d.target.x) / 2)
      .attr('y', d => (d.source.y + d.target.y) / 2)

    node.attr('transform', d => `translate(${d.x},${d.y})`)
  })

  svg.on('click', () => { selectedNode.value = null })
}

function dragstarted(event, d) {
  if (!event.active) simulation.alphaTarget(0.3).restart()
  d.fx = d.x
  d.fy = d.y
}

function dragged(event, d) {
  d.fx = event.x
  d.fy = event.y
}

function dragended(event, d) {
  if (!event.active) simulation.alphaTarget(0)
  d.fx = null
  d.fy = null
}

// --- Node Selection ---

function selectNode(d) {
  const raw = graphData.value.nodes.find(n => n.uuid === d.id)
  const connections = graphData.value.edges.filter(
    e => e.source_node_uuid === d.id || e.target_node_uuid === d.id,
  )
  selectedNode.value = {
    ...d,
    summary: raw?.summary || d.summary,
    attributes: raw?.attributes || {},
    entityType: getEntityType(d.labels),
    connections: connections.map(e => ({
      name: e.name || e.fact_type || '',
      fact: e.fact || '',
      direction: e.source_node_uuid === d.id ? 'outgoing' : 'incoming',
      target: e.source_node_uuid === d.id
        ? graphData.value.nodes.find(n => n.uuid === e.target_node_uuid)?.name || ''
        : graphData.value.nodes.find(n => n.uuid === e.source_node_uuid)?.name || '',
    })),
  }
}

function handleSearchSelect(uuid) {
  if (!zoomGroup || !simulation) return
  const simNodes = simulation.nodes()
  const target = simNodes.find(n => n.id === uuid)
  if (!target) {
    const raw = graphData.value.nodes.find(n => n.uuid === uuid)
    if (raw) selectNode({ id: raw.uuid, name: raw.name, labels: raw.labels, summary: raw.summary || '', centrality: 0, color: getNodeColor(raw.labels), radius: 10 })
    return
  }
  selectNode(target)
  if (!containerRef.value || !svg || !zoomBehavior) return
  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight
  const transform = d3.zoomIdentity.translate(width / 2 - target.x, height / 2 - target.y)
  svg.transition().duration(500).call(zoomBehavior.transform, transform)
}

// --- Demo Data ---

function loadDemoData() {
  if (demoBuildTimer) clearInterval(demoBuildTimer)

  const allNodes = [
    // Personas (15)
    { uuid: 'p1', name: 'Enterprise Buyer', labels: ['Entity', 'Persona'], summary: 'Decision-maker at large organizations evaluating platform purchases.' },
    { uuid: 'p2', name: 'SMB Founder', labels: ['Entity', 'Persona'], summary: 'Small business owner seeking affordable customer support tools.' },
    { uuid: 'p3', name: 'Developer Advocate', labels: ['Entity', 'Persona'], summary: 'Technical influencer evaluating APIs and integrations.' },
    { uuid: 'p4', name: 'VP of Support', labels: ['Entity', 'Persona'], summary: 'Senior leader responsible for support team performance and tooling.' },
    { uuid: 'p5', name: 'CX Director', labels: ['Entity', 'Persona'], summary: 'Owns end-to-end customer experience strategy and metrics.' },
    { uuid: 'p6', name: 'IT Leader', labels: ['Entity', 'Persona'], summary: 'Oversees technology stack, security, and vendor compliance.' },
    { uuid: 'p7', name: 'Head of Operations', labels: ['Entity', 'Persona'], summary: 'Drives operational efficiency across business processes.' },
    { uuid: 'p8', name: 'CFO', labels: ['Entity', 'Persona'], summary: 'Financial decision-maker focused on ROI and cost management.' },
    { uuid: 'p9', name: 'Product Manager', labels: ['Entity', 'Persona'], summary: 'Defines product roadmap based on customer and market insights.' },
    { uuid: 'p10', name: 'Sales Engineer', labels: ['Entity', 'Persona'], summary: 'Technical pre-sales resource supporting enterprise deal cycles.' },
    { uuid: 'p11', name: 'Marketing Director', labels: ['Entity', 'Persona'], summary: 'Leads demand generation, positioning, and campaign strategy.' },
    { uuid: 'p12', name: 'Customer Success Manager', labels: ['Entity', 'Persona'], summary: 'Manages post-sale relationships and drives adoption and retention.' },
    { uuid: 'p13', name: 'Chief Revenue Officer', labels: ['Entity', 'Persona'], summary: 'Owns revenue strategy spanning sales, CS, and expansion.' },
    { uuid: 'p14', name: 'Solutions Architect', labels: ['Entity', 'Persona'], summary: 'Designs technical implementation plans for complex deployments.' },
    { uuid: 'p15', name: 'Procurement Lead', labels: ['Entity', 'Persona'], summary: 'Manages vendor evaluation, contracting, and compliance.' },
    // Topics (20)
    { uuid: 't1', name: 'Customer Support', labels: ['Entity', 'Topic'], summary: 'Core product area for ticket management and live chat.' },
    { uuid: 't2', name: 'AI Automation', labels: ['Entity', 'Topic'], summary: 'Machine learning-powered features like Fin AI agent.' },
    { uuid: 't3', name: 'Pricing Strategy', labels: ['Entity', 'Topic'], summary: 'Seat-based vs usage-based pricing models and packaging.' },
    { uuid: 't4', name: 'Competitor Analysis', labels: ['Entity', 'Topic'], summary: 'Comparative positioning against Zendesk, Freshdesk, HubSpot.' },
    { uuid: 't5', name: 'Fin AI Agent', labels: ['Entity', 'Topic'], summary: 'AI-powered resolution engine handling frontline support queries.' },
    { uuid: 't6', name: 'Resolution Rate', labels: ['Entity', 'Topic'], summary: 'Percentage of support queries resolved without human escalation.' },
    { uuid: 't7', name: 'CSAT Score', labels: ['Entity', 'Topic'], summary: 'Customer satisfaction metric collected post-interaction.' },
    { uuid: 't8', name: 'Support Ticket Volume', labels: ['Entity', 'Topic'], summary: 'Inbound request volume across channels and segments.' },
    { uuid: 't9', name: 'Self-Serve Onboarding', labels: ['Entity', 'Topic'], summary: 'Guided setup flows enabling customers to activate without sales.' },
    { uuid: 't10', name: 'API Integration', labels: ['Entity', 'Topic'], summary: 'REST and webhook APIs for connecting external systems.' },
    { uuid: 't11', name: 'Zendesk Migration', labels: ['Entity', 'Topic'], summary: 'Migration tooling and playbooks for Zendesk-to-Intercom switches.' },
    { uuid: 't12', name: 'HubSpot Comparison', labels: ['Entity', 'Topic'], summary: 'Feature and pricing comparison against HubSpot Service Hub.' },
    { uuid: 't13', name: 'Cost Reduction', labels: ['Entity', 'Topic'], summary: 'Strategies to lower support cost per resolution via automation.' },
    { uuid: 't14', name: 'Response Time', labels: ['Entity', 'Topic'], summary: 'Median and p95 first-response time across support channels.' },
    { uuid: 't15', name: 'Knowledge Base', labels: ['Entity', 'Topic'], summary: 'Self-service article library powering AI and human agents.' },
    { uuid: 't16', name: 'Omnichannel Support', labels: ['Entity', 'Topic'], summary: 'Unified inbox across email, chat, social, and phone.' },
    { uuid: 't17', name: 'Inbox Management', labels: ['Entity', 'Topic'], summary: 'Routing, assignment, and prioritization of inbound conversations.' },
    { uuid: 't18', name: 'Workflow Automation', labels: ['Entity', 'Topic'], summary: 'Rules and triggers that automate repetitive support tasks.' },
    { uuid: 't19', name: 'Custom Bots', labels: ['Entity', 'Topic'], summary: 'Configurable chatbot flows for lead qualification and triage.' },
    { uuid: 't20', name: 'Reporting Analytics', labels: ['Entity', 'Topic'], summary: 'Dashboards and exports for support performance insights.' },
    // Processes/Events (12)
    { uuid: 'e1', name: 'Product-Led Growth', labels: ['Entity', 'Process'], summary: 'GTM motion focusing on self-serve onboarding and expansion.' },
    { uuid: 'e2', name: 'Sales-Led Motion', labels: ['Entity', 'Process'], summary: 'Enterprise sales cycle with demos, pilots, and procurement.' },
    { uuid: 'e3', name: 'Outbound Campaign', labels: ['Entity', 'Process'], summary: 'Targeted outreach sequences for prospecting and re-engagement.' },
    { uuid: 'e4', name: 'Inbound Lead', labels: ['Entity', 'Event'], summary: 'Prospect entering the funnel via content, ads, or referral.' },
    { uuid: 'e5', name: 'Contract Renewal', labels: ['Entity', 'Event'], summary: 'Annual or multi-year renewal negotiation and close.' },
    { uuid: 'e6', name: 'Expansion Revenue', labels: ['Entity', 'Process'], summary: 'Upsell and cross-sell motions within existing accounts.' },
    { uuid: 'e7', name: 'Churn Risk', labels: ['Entity', 'Event'], summary: 'Signals indicating potential customer attrition.' },
    { uuid: 'e8', name: 'Pilot Program', labels: ['Entity', 'Process'], summary: 'Time-boxed trial deployment to validate product fit.' },
    { uuid: 'e9', name: 'ROI Analysis', labels: ['Entity', 'Process'], summary: 'Quantitative assessment of cost savings and efficiency gains.' },
    { uuid: 'e10', name: 'Competitive Evaluation', labels: ['Entity', 'Process'], summary: 'Structured comparison of vendors during buying cycle.' },
    { uuid: 'e11', name: 'Budget Approval', labels: ['Entity', 'Event'], summary: 'Finance sign-off required before purchase commitment.' },
    { uuid: 'e12', name: 'Implementation', labels: ['Entity', 'Process'], summary: 'Post-sale deployment, configuration, and go-live.' },
    // Features (8)
    { uuid: 'f1', name: 'Onboarding Flow', labels: ['Entity', 'Feature'], summary: 'First-run experience guiding users through product setup.' },
    { uuid: 'f2', name: 'Messenger Widget', labels: ['Entity', 'Feature'], summary: 'Embeddable chat widget for web and mobile apps.' },
    { uuid: 'f3', name: 'Help Center', labels: ['Entity', 'Feature'], summary: 'Public-facing knowledge base and article search.' },
    { uuid: 'f4', name: 'Proactive Messages', labels: ['Entity', 'Feature'], summary: 'Targeted in-app messages based on user behavior.' },
    { uuid: 'f5', name: 'Team Inbox', labels: ['Entity', 'Feature'], summary: 'Shared workspace for collaborative conversation handling.' },
    { uuid: 'f6', name: 'Surveys', labels: ['Entity', 'Feature'], summary: 'In-app and email surveys for NPS, CSAT, and custom feedback.' },
    { uuid: 'f7', name: 'Data Platform', labels: ['Entity', 'Feature'], summary: 'Customer data layer powering segmentation and personalization.' },
    { uuid: 'f8', name: 'Series Automation', labels: ['Entity', 'Feature'], summary: 'Multi-step messaging workflows triggered by user events.' },
  ]
  const allEdges = [
    // Persona -> Topic/Feature/Process relationships
    { uuid: 'ed1', source_node_uuid: 'p1', target_node_uuid: 't1', name: 'evaluates', fact: 'Enterprise buyers evaluate customer support platforms for scale.' },
    { uuid: 'ed2', source_node_uuid: 'p1', target_node_uuid: 'e2', name: 'engages_via', fact: 'Enterprise buyers engage through sales-led motions with demos.' },
    { uuid: 'ed3', source_node_uuid: 'p1', target_node_uuid: 'e11', name: 'requires', fact: 'Enterprise buyers require budget approval before commitment.' },
    { uuid: 'ed4', source_node_uuid: 'p2', target_node_uuid: 'e1', name: 'converts_through', fact: 'SMB founders convert through product-led self-serve flows.' },
    { uuid: 'ed5', source_node_uuid: 'p2', target_node_uuid: 't3', name: 'influenced_by', fact: 'SMB founders are highly price-sensitive in vendor selection.' },
    { uuid: 'ed6', source_node_uuid: 'p2', target_node_uuid: 't9', name: 'depends_on', fact: 'SMB founders rely on self-serve onboarding to get started.' },
    { uuid: 'ed7', source_node_uuid: 'p3', target_node_uuid: 't10', name: 'integrates', fact: 'Developer advocates evaluate and build on API integrations.' },
    { uuid: 'ed8', source_node_uuid: 'p3', target_node_uuid: 'f1', name: 'tests', fact: 'Developer advocates evaluate the onboarding flow for friction.' },
    { uuid: 'ed9', source_node_uuid: 'p3', target_node_uuid: 'f2', name: 'integrates', fact: 'Developer advocates embed the Messenger widget in apps.' },
    { uuid: 'ed10', source_node_uuid: 'p4', target_node_uuid: 't1', name: 'serves', fact: 'VP of Support owns the customer support function.' },
    { uuid: 'ed11', source_node_uuid: 'p4', target_node_uuid: 't6', name: 'monitors', fact: 'VP of Support tracks resolution rate as a key metric.' },
    { uuid: 'ed12', source_node_uuid: 'p4', target_node_uuid: 'f5', name: 'depends_on', fact: 'VP of Support depends on Team Inbox for agent management.' },
    { uuid: 'ed13', source_node_uuid: 'p5', target_node_uuid: 't7', name: 'monitors', fact: 'CX Director tracks CSAT scores across all touchpoints.' },
    { uuid: 'ed14', source_node_uuid: 'p5', target_node_uuid: 't16', name: 'drives', fact: 'CX Director drives omnichannel support strategy.' },
    { uuid: 'ed15', source_node_uuid: 'p5', target_node_uuid: 'f6', name: 'enables', fact: 'CX Director uses surveys to measure experience quality.' },
    { uuid: 'ed16', source_node_uuid: 'p6', target_node_uuid: 't10', name: 'evaluates', fact: 'IT Leader evaluates API integration security and compliance.' },
    { uuid: 'ed17', source_node_uuid: 'p6', target_node_uuid: 'f7', name: 'evaluates', fact: 'IT Leader assesses Data Platform for privacy compliance.' },
    { uuid: 'ed18', source_node_uuid: 'p7', target_node_uuid: 't18', name: 'drives', fact: 'Head of Operations drives workflow automation adoption.' },
    { uuid: 'ed19', source_node_uuid: 'p7', target_node_uuid: 't17', name: 'enables', fact: 'Head of Operations optimizes inbox management processes.' },
    { uuid: 'ed20', source_node_uuid: 'p8', target_node_uuid: 't13', name: 'requires', fact: 'CFO requires cost reduction evidence before approving spend.' },
    { uuid: 'ed21', source_node_uuid: 'p8', target_node_uuid: 'e9', name: 'requires', fact: 'CFO requires ROI analysis for vendor purchase decisions.' },
    { uuid: 'ed22', source_node_uuid: 'p8', target_node_uuid: 'e11', name: 'enables', fact: 'CFO enables budget approval after reviewing financials.' },
    { uuid: 'ed23', source_node_uuid: 'p9', target_node_uuid: 't5', name: 'drives', fact: 'Product Manager drives Fin AI Agent roadmap and priorities.' },
    { uuid: 'ed24', source_node_uuid: 'p9', target_node_uuid: 't19', name: 'drives', fact: 'Product Manager defines custom bot capabilities and flows.' },
    { uuid: 'ed25', source_node_uuid: 'p9', target_node_uuid: 'f4', name: 'drives', fact: 'Product Manager shapes proactive messaging strategy.' },
    { uuid: 'ed26', source_node_uuid: 'p10', target_node_uuid: 'e8', name: 'supports', fact: 'Sales Engineer supports pilot programs with technical guidance.' },
    { uuid: 'ed27', source_node_uuid: 'p10', target_node_uuid: 'e2', name: 'supports', fact: 'Sales Engineer provides technical demos in sales-led motion.' },
    { uuid: 'ed28', source_node_uuid: 'p10', target_node_uuid: 'p14', name: 'enables', fact: 'Sales Engineer collaborates with Solutions Architect on deals.' },
    { uuid: 'ed29', source_node_uuid: 'p11', target_node_uuid: 'e3', name: 'drives', fact: 'Marketing Director drives outbound campaign strategy.' },
    { uuid: 'ed30', source_node_uuid: 'p11', target_node_uuid: 'e4', name: 'targets', fact: 'Marketing Director targets inbound lead generation.' },
    { uuid: 'ed31', source_node_uuid: 'p11', target_node_uuid: 't4', name: 'informs', fact: 'Marketing Director uses competitor analysis for positioning.' },
    { uuid: 'ed32', source_node_uuid: 'p12', target_node_uuid: 'e5', name: 'drives', fact: 'CSM drives contract renewal through proactive engagement.' },
    { uuid: 'ed33', source_node_uuid: 'p12', target_node_uuid: 'e7', name: 'monitors', fact: 'CSM monitors churn risk signals across the book of business.' },
    { uuid: 'ed34', source_node_uuid: 'p12', target_node_uuid: 'e6', name: 'drives', fact: 'CSM identifies and drives expansion revenue opportunities.' },
    { uuid: 'ed35', source_node_uuid: 'p13', target_node_uuid: 'e6', name: 'enables', fact: 'CRO sets expansion revenue targets and strategy.' },
    { uuid: 'ed36', source_node_uuid: 'p13', target_node_uuid: 'e2', name: 'enables', fact: 'CRO oversees sales-led motion execution.' },
    { uuid: 'ed37', source_node_uuid: 'p14', target_node_uuid: 'e12', name: 'drives', fact: 'Solutions Architect designs implementation plans.' },
    { uuid: 'ed38', source_node_uuid: 'p14', target_node_uuid: 't11', name: 'supports', fact: 'Solutions Architect leads Zendesk migration projects.' },
    { uuid: 'ed39', source_node_uuid: 'p15', target_node_uuid: 'e10', name: 'drives', fact: 'Procurement Lead runs competitive evaluation process.' },
    { uuid: 'ed40', source_node_uuid: 'p15', target_node_uuid: 'e11', name: 'requires', fact: 'Procurement Lead requires budget approval for contracts.' },
    // Topic -> Topic/Feature/Process relationships
    { uuid: 'ed41', source_node_uuid: 't1', target_node_uuid: 't2', name: 'enhanced_by', fact: 'Customer support is enhanced by AI automation capabilities.' },
    { uuid: 'ed42', source_node_uuid: 't2', target_node_uuid: 't5', name: 'enables', fact: 'AI automation powers the Fin AI Agent product.' },
    { uuid: 'ed43', source_node_uuid: 't5', target_node_uuid: 't6', name: 'produces', fact: 'Fin AI Agent directly produces resolution rate improvements.' },
    { uuid: 'ed44', source_node_uuid: 't6', target_node_uuid: 't7', name: 'drives', fact: 'Higher resolution rates drive improved CSAT scores.' },
    { uuid: 'ed45', source_node_uuid: 't5', target_node_uuid: 't8', name: 'resolves', fact: 'Fin AI Agent resolves a portion of support ticket volume.' },
    { uuid: 'ed46', source_node_uuid: 't4', target_node_uuid: 't3', name: 'informs', fact: 'Competitor analysis informs pricing strategy decisions.' },
    { uuid: 'ed47', source_node_uuid: 't4', target_node_uuid: 't12', name: 'enables', fact: 'Competitor analysis enables HubSpot comparison materials.' },
    { uuid: 'ed48', source_node_uuid: 't13', target_node_uuid: 't2', name: 'depends_on', fact: 'Cost reduction strategies depend on AI automation adoption.' },
    { uuid: 'ed49', source_node_uuid: 't15', target_node_uuid: 't5', name: 'supports', fact: 'Knowledge base articles power Fin AI Agent responses.' },
    { uuid: 'ed50', source_node_uuid: 't15', target_node_uuid: 'f3', name: 'enables', fact: 'Knowledge base content enables the Help Center experience.' },
    { uuid: 'ed51', source_node_uuid: 't18', target_node_uuid: 't17', name: 'automates', fact: 'Workflow automation streamlines inbox management processes.' },
    { uuid: 'ed52', source_node_uuid: 't19', target_node_uuid: 'e4', name: 'supports', fact: 'Custom bots qualify and route inbound leads.' },
    { uuid: 'ed53', source_node_uuid: 't20', target_node_uuid: 't14', name: 'measures', fact: 'Reporting analytics measures response time performance.' },
    { uuid: 'ed54', source_node_uuid: 't20', target_node_uuid: 't7', name: 'measures', fact: 'Reporting analytics tracks CSAT score trends.' },
    { uuid: 'ed55', source_node_uuid: 't16', target_node_uuid: 'f2', name: 'depends_on', fact: 'Omnichannel support depends on the Messenger widget.' },
    { uuid: 'ed56', source_node_uuid: 't16', target_node_uuid: 'f5', name: 'depends_on', fact: 'Omnichannel support requires Team Inbox for unified routing.' },
    { uuid: 'ed57', source_node_uuid: 't11', target_node_uuid: 't4', name: 'triggered_by', fact: 'Zendesk migration is triggered by competitive evaluation.' },
    // Process/Event -> Process/Topic/Feature relationships
    { uuid: 'ed58', source_node_uuid: 'e1', target_node_uuid: 'f1', name: 'depends_on', fact: 'Product-led growth depends on a smooth onboarding flow.' },
    { uuid: 'ed59', source_node_uuid: 'e1', target_node_uuid: 't9', name: 'depends_on', fact: 'Product-led growth relies on self-serve onboarding.' },
    { uuid: 'ed60', source_node_uuid: 'e2', target_node_uuid: 'e8', name: 'enables', fact: 'Sales-led motion enables pilot programs for prospects.' },
    { uuid: 'ed61', source_node_uuid: 'e3', target_node_uuid: 'e4', name: 'produces', fact: 'Outbound campaigns produce inbound leads.' },
    { uuid: 'ed62', source_node_uuid: 'e7', target_node_uuid: 'e5', name: 'blocks', fact: 'Churn risk threatens contract renewal success.' },
    { uuid: 'ed63', source_node_uuid: 'e9', target_node_uuid: 't13', name: 'produces', fact: 'ROI analysis quantifies cost reduction potential.' },
    { uuid: 'ed64', source_node_uuid: 'e10', target_node_uuid: 't12', name: 'enables', fact: 'Competitive evaluation produces HubSpot comparison data.' },
    { uuid: 'ed65', source_node_uuid: 'e12', target_node_uuid: 't11', name: 'depends_on', fact: 'Implementation depends on Zendesk migration tooling.' },
    // Feature -> Feature/Topic cross-links
    { uuid: 'ed66', source_node_uuid: 'f4', target_node_uuid: 'f8', name: 'depends_on', fact: 'Proactive messages are delivered through Series automation.' },
    { uuid: 'ed67', source_node_uuid: 'f7', target_node_uuid: 'f4', name: 'enables', fact: 'Data Platform enables targeted proactive messages.' },
    { uuid: 'ed68', source_node_uuid: 'f3', target_node_uuid: 't14', name: 'drives', fact: 'Help Center deflects tickets, improving response time.' },
  ]

  graphStatus.value = 'building'
  graphProgress.value = 0
  graphData.value = { nodes: [], edges: [] }
  nodeCount.value = 0
  edgeCount.value = 0

  let idx = 0
  const BATCH = 3
  const INTERVAL = 200

  demoBuildTimer = setInterval(() => {
    if (idx >= allNodes.length) {
      clearInterval(demoBuildTimer)
      demoBuildTimer = null
      graphStatus.value = 'complete'
      graphProgress.value = 100
      return
    }

    const end = Math.min(idx + BATCH, allNodes.length)
    const newNodes = allNodes.slice(idx, end)
    graphData.value.nodes.push(...newNodes)

    const nodeIds = new Set(graphData.value.nodes.map(n => n.uuid))
    graphData.value.edges = allEdges.filter(
      e => nodeIds.has(e.source_node_uuid) && nodeIds.has(e.target_node_uuid),
    )

    idx = end
    graphProgress.value = Math.round((idx / allNodes.length) * 100)
    nodeCount.value = graphData.value.nodes.length
    edgeCount.value = graphData.value.edges.length

    const msgIdx = Math.min(
      Math.floor((idx / allNodes.length) * BUILD_MESSAGES.length),
      BUILD_MESSAGES.length - 1,
    )
    graphTask.value = { message: BUILD_MESSAGES[msgIdx] }

    nextTick(() => renderGraph())
  }, INTERVAL)
}

// --- Watchers ---

// When graphData changes and status is complete, render the real graph
watch(graphData, () => {
  if (graphStatus.value === 'complete' && graphData.value.nodes.length) {
    nextTick(() => renderGraph())
  }
}, { deep: true })

// When status transitions to complete, ensure graph is rendered
watch(graphStatus, (val) => {
  if (val === 'complete' && graphData.value.nodes.length) {
    nextTick(() => renderGraph())
  }
  if (val === 'failed') {
    errorMsg.value = graphTask.value?.message || 'Build failed'
  }
})

// When building, update skeleton at progress milestones
watch(graphProgress, (val) => {
  if (graphStatus.value === 'building' && !graphData.value.nodes.length) {
    if (val % 25 === 0 || val === 0) {
      renderSkeletonGraph()
    }
  }
})

// Demo mode triggers
watch(() => props.demoMode, (val) => {
  if (val) loadDemoData()
})

watch(isDemoFallback, (val) => {
  if (val) loadDemoData()
})

// --- Lifecycle ---

onMounted(() => {
  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
      if (graphData.value.nodes.length && graphStatus.value === 'complete') {
        renderGraph()
      } else if (graphStatus.value === 'building' && !graphData.value.nodes.length) {
        renderSkeletonGraph()
      }
    }, 200)
  })
  if (containerRef.value) resizeObserver.observe(containerRef.value)

  themeObserver = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.attributeName === 'class' && graphData.value.nodes.length) {
        renderGraph()
        break
      }
    }
  })
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })

  if (graphStatus.value === 'building') {
    renderSkeletonGraph()
  }

  if (props.demoMode || isDemoFallback.value) {
    loadDemoData()
  }
})

onUnmounted(() => {
  if (demoBuildTimer) clearInterval(demoBuildTimer)
  if (simulation) simulation.stop()
  if (skeletonSim) skeletonSim.stop()
  if (resizeObserver) resizeObserver.disconnect()
  if (themeObserver) themeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div ref="containerRef" class="w-full h-full relative overflow-hidden bg-[#f8f9fa] dark:bg-[#0a0a1a]">
    <!-- Status badge top-left -->
    <div class="absolute top-4 left-4 z-10 flex items-center gap-3">
      <span
        class="px-3 py-1 rounded-full text-xs font-medium"
        :class="{
          'bg-yellow-500/20 text-yellow-400': graphStatus === 'building',
          'bg-green-500/20 text-green-400': graphStatus === 'complete',
          'bg-red-500/20 text-red-400': graphStatus === 'failed',
        }"
      >
        <template v-if="graphStatus === 'building'">Building Graph... {{ graphProgress }}%</template>
        <template v-else-if="graphStatus === 'complete'">Complete</template>
        <template v-else>Failed</template>
      </span>
    </div>

    <!-- Search (top-right, shown when graph is complete) -->
    <Transition name="fade">
      <div
        v-if="graphStatus === 'complete'"
        class="absolute top-4 right-4 z-10 w-64"
      >
        <GraphSearch
          :graph-id="graphId"
          :graph-data="graphData"
          @select-node="handleSearchSelect"
        />
      </div>
    </Transition>

    <!-- Build progress overlay center -->
    <Transition name="fade">
      <div
        v-if="graphStatus === 'building' && !demoMode && !isDemoFallback"
        class="absolute top-4 left-1/2 -translate-x-1/2 z-10 bg-black/60 dark:bg-black/70 backdrop-blur-sm rounded-xl px-5 py-3 flex items-center gap-4"
      >
        <svg viewBox="0 0 36 36" class="w-9 h-9 -rotate-90 flex-shrink-0">
          <circle cx="18" cy="18" r="14" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="3" />
          <circle
            cx="18" cy="18" r="14" fill="none" stroke="#2068FF" stroke-width="3"
            stroke-linecap="round" :stroke-dasharray="88" :stroke-dashoffset="88 - (88 * graphProgress / 100)"
            class="transition-[stroke-dashoffset] duration-300"
          />
        </svg>
        <div>
          <p class="text-white text-sm font-medium">Building Graph... {{ graphProgress }}%</p>
          <p class="text-white/50 text-xs">{{ buildMessage }}</p>
        </div>
      </div>
    </Transition>

    <!-- Error state -->
    <div
      v-if="graphStatus === 'failed'"
      class="absolute inset-0 flex items-center justify-center z-20 bg-[var(--color-surface)]/80 backdrop-blur-sm"
    >
      <div class="flex flex-col items-center text-center max-w-md">
        <div class="w-14 h-14 rounded-full bg-red-500/20 flex items-center justify-center mb-4">
          <svg class="w-7 h-7 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
          </svg>
        </div>
        <p class="text-[var(--color-text)] text-sm font-medium mb-2">Graph build failed</p>
        <p class="text-[var(--color-text-muted)] text-xs mb-6">{{ errorMsg }}</p>
      </div>
    </div>

    <!-- SVG canvas -->
    <svg ref="svgRef" class="w-full h-full graph-canvas" />

    <!-- Entity type stats panel bottom-left -->
    <div
      v-if="entityTypeStats.length && graphStatus !== 'failed'"
      class="absolute bottom-6 left-4 z-10 bg-black/5 dark:bg-white/5 backdrop-blur-sm border border-black/10 dark:border-white/10 rounded-lg p-4 max-w-56"
    >
      <h3 class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)] mb-3">Entity Types</h3>
      <div class="space-y-2">
        <div v-for="stat in entityTypeStats" :key="stat.type" class="flex items-center gap-2">
          <span class="w-2.5 h-2.5 rounded-full flex-shrink-0" :style="{ backgroundColor: stat.color }" />
          <span class="text-xs text-[var(--color-text-secondary)] flex-1 truncate">{{ stat.type }}</span>
          <span class="text-xs text-[var(--color-text-muted)] tabular-nums">{{ stat.count }}</span>
        </div>
      </div>
      <div class="mt-3 pt-3 border-t border-black/10 dark:border-white/10 flex justify-between text-xs text-[var(--color-text-muted)]">
        <span data-testid="node-count">{{ nodeCount }} nodes</span>
        <span data-testid="edge-count">{{ edgeCount }} edges</span>
      </div>
    </div>

    <!-- Node detail panel right side -->
    <Transition name="slide">
      <div
        v-if="selectedNode"
        class="absolute top-0 right-0 z-20 h-full w-80 bg-white/95 dark:bg-[#0f0f24]/95 backdrop-blur-md border-l border-black/10 dark:border-white/10 overflow-y-auto"
        data-testid="detail-panel"
      >
        <div class="p-5">
          <!-- Header -->
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-2.5">
              <span class="w-3.5 h-3.5 rounded-full" :style="{ backgroundColor: selectedNode.color }" />
              <h3 class="text-[var(--color-text)] font-semibold text-sm">{{ selectedNode.name }}</h3>
            </div>
            <button
              @click="selectedNode = null"
              class="text-black/30 dark:text-white/30 hover:text-black/60 dark:hover:text-white/60 text-lg leading-none transition-colors"
            >&times;</button>
          </div>

          <!-- Type badge -->
          <span
            class="inline-block px-2 py-0.5 rounded text-[10px] uppercase tracking-wider mb-4"
            :style="{ backgroundColor: selectedNode.color + '22', color: selectedNode.color }"
          >
            {{ selectedNode.entityType }}
          </span>

          <!-- Summary -->
          <div v-if="selectedNode.summary" class="mb-5">
            <h4 class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)] mb-1.5">Summary</h4>
            <p class="text-xs text-[var(--color-text-secondary)] leading-relaxed">{{ selectedNode.summary }}</p>
          </div>

          <!-- Centrality -->
          <div class="mb-5">
            <h4 class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)] mb-1.5">Centrality</h4>
            <div class="flex items-center gap-2">
              <div class="flex-1 h-1.5 rounded-full bg-black/10 dark:bg-white/10">
                <div
                  class="h-full rounded-full transition-all duration-300"
                  :style="{ width: (selectedNode.centrality * 100) + '%', backgroundColor: selectedNode.color }"
                />
              </div>
              <span class="text-xs text-[var(--color-text-muted)] tabular-nums">{{ Math.round(selectedNode.centrality * 100) }}%</span>
            </div>
          </div>

          <!-- Connections -->
          <div v-if="selectedNode.connections.length">
            <h4 class="text-[10px] uppercase tracking-widest text-[var(--color-text-muted)] mb-2">
              Connections ({{ selectedNode.connections.length }})
            </h4>
            <div class="space-y-2">
              <div
                v-for="(conn, i) in selectedNode.connections"
                :key="i"
                class="bg-black/5 dark:bg-white/5 rounded-lg p-3"
              >
                <div class="flex items-center gap-1.5 mb-1">
                  <span class="text-[10px]" :class="conn.direction === 'outgoing' ? 'text-[#2068FF]' : 'text-[#ff5600]'">
                    {{ conn.direction === 'outgoing' ? '\u2192' : '\u2190' }}
                  </span>
                  <span class="text-xs text-[var(--color-text-muted)]">{{ conn.name }}</span>
                  <span class="text-xs text-[var(--color-text)] font-medium">{{ conn.target }}</span>
                </div>
                <p v-if="conn.fact" class="text-[11px] text-[var(--color-text-muted)] leading-relaxed">{{ conn.fact }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Action buttons bottom-right (when graph complete) -->
    <Transition name="fade">
      <div
        v-if="graphStatus === 'complete'"
        class="absolute bottom-6 right-6 z-10 flex items-center gap-3"
      >
        <span class="text-xs text-[var(--color-text-muted)]">{{ nodeCount }} nodes, {{ edgeCount }} edges</span>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.skeleton-pulse {
  animation: skeleton-pulse 2s ease-in-out infinite;
}

@keyframes skeleton-pulse {
  0%, 100% { opacity: 0.15; }
  50% { opacity: 0.35; }
}

.graph-canvas {
  transition: opacity 0.4s ease;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.25s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
