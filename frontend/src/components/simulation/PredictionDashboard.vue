<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  actions: { type: Array, default: () => [] },
  currentRound: { type: Number, default: 0 },
  totalRounds: { type: Number, default: 0 },
})

const donutRef = ref(null)
let resizeObserver = null
let resizeTimer = null

// --- Action categories for prediction ---
const ACTION_CATEGORIES = [
  { key: 'post', match: ['CREATE_POST', 'CREATE_THREAD'], label: 'Post', icon: '\uD83D\uDCDD' },
  { key: 'reply', match: ['REPLY', 'COMMENT'], label: 'Reply', icon: '\uD83D\uDCAC' },
  { key: 'like', match: ['LIKE', 'UPVOTE'], label: 'Like', icon: '\u2764\uFE0F' },
  { key: 'repost', match: ['REPOST', 'RETWEET', 'SHARE'], label: 'Repost', icon: '\uD83D\uDD01' },
]

function categorizeAction(actionType) {
  const t = (actionType || '').toUpperCase()
  for (const cat of ACTION_CATEGORIES) {
    if (cat.match.some(m => t.includes(m))) return cat.key
  }
  return 'post'
}

function categoryLabel(key) {
  return ACTION_CATEGORIES.find(c => c.key === key)?.label || key
}

function categoryIcon(key) {
  return ACTION_CATEGORIES.find(c => c.key === key)?.icon || '\u26A1'
}

// --- Sentiment helpers (same word lists as SentimentTimeline) ---
const POSITIVE = [
  'impressive', 'compelling', 'great', 'interested', 'good', 'recommend',
  'valuable', 'effective', 'excellent', 'innovative', 'benefit', 'better',
  'love', 'amazing', 'helpful', 'promising', 'confident', 'positive',
]
const NEGATIVE = [
  'concerned', 'skeptical', 'aggressive', 'risk', 'worried', 'expensive',
  'complex', 'difficult', 'doubt', 'problem', 'unclear', 'frustrated',
  'poor', 'slow', 'lacks', 'overpriced', 'limited', 'negative',
]

function sentimentOf(content) {
  if (!content) return 0
  const lower = content.toLowerCase()
  let pos = 0, neg = 0
  for (const w of POSITIVE) { if (lower.includes(w)) pos++ }
  for (const w of NEGATIVE) { if (lower.includes(w)) neg++ }
  if (pos + neg === 0) return 0
  return (pos - neg) / (pos + neg)
}

// --- Per-agent prediction data ---
const agentPredictions = computed(() => {
  if (!props.actions.length) return []

  const agentMap = new Map()
  for (const a of props.actions) {
    const name = a.agent_name || `Agent #${a.agent_id}`
    if (!agentMap.has(name)) {
      agentMap.set(name, { name, actions: [], sentiments: [] })
    }
    const entry = agentMap.get(name)
    entry.actions.push(categorizeAction(a.action_type))
    entry.sentiments.push(sentimentOf(a.action_args?.content))
  }

  const predictions = []
  for (const [name, data] of agentMap) {
    const freq = {}
    for (const cat of data.actions) {
      freq[cat] = (freq[cat] || 0) + 1
    }

    // Most frequent action = predicted action
    const total = data.actions.length
    let bestCat = 'post'
    let bestCount = 0
    for (const [cat, count] of Object.entries(freq)) {
      if (count > bestCount) { bestCat = cat; bestCount = count }
    }

    // Confidence = frequency ratio, boosted by consistency in recent actions
    const recentSlice = data.actions.slice(-5)
    const recentMatch = recentSlice.filter(a => a === bestCat).length
    const baseConfidence = bestCount / total
    const recencyBoost = recentMatch / recentSlice.length
    const confidence = Math.min(0.99, baseConfidence * 0.6 + recencyBoost * 0.4)

    // Average sentiment trend
    const avgSentiment = data.sentiments.reduce((s, v) => s + v, 0) / data.sentiments.length

    predictions.push({
      name,
      predictedAction: bestCat,
      confidence,
      avgSentiment,
      actionCount: total,
    })
  }

  return predictions.sort((a, b) => b.confidence - a.confidence).slice(0, 12)
})

// --- Consensus prediction ---
const consensusPrediction = computed(() => {
  if (!props.actions.length || !props.totalRounds) return null

  // Measure sentiment convergence: standard deviation over recent rounds
  const roundSentiments = new Map()
  for (const a of props.actions) {
    const round = a.round_num
    if (round == null) continue
    if (!roundSentiments.has(round)) roundSentiments.set(round, [])
    roundSentiments.get(round).push(sentimentOf(a.action_args?.content))
  }

  const rounds = Array.from(roundSentiments.keys()).sort((a, b) => a - b)
  if (rounds.length < 2) return null

  // Calculate std dev trend
  const stdDevs = rounds.map(r => {
    const vals = roundSentiments.get(r)
    const mean = vals.reduce((s, v) => s + v, 0) / vals.length
    const variance = vals.reduce((s, v) => s + (v - mean) ** 2, 0) / vals.length
    return Math.sqrt(variance)
  })

  // If std dev is decreasing, agents are converging
  const recentStd = stdDevs.slice(-3).reduce((s, v) => s + v, 0) / Math.min(3, stdDevs.length)
  const earlyStd = stdDevs.slice(0, 3).reduce((s, v) => s + v, 0) / Math.min(3, stdDevs.length)
  const convergenceRate = earlyStd > 0 ? (earlyStd - recentStd) / earlyStd : 0

  // Estimate consensus round
  const currentRound = props.currentRound || rounds[rounds.length - 1]
  const remaining = props.totalRounds - currentRound
  let estimatedRound
  let confidence

  if (convergenceRate > 0.3) {
    // Strong convergence — predict soon
    estimatedRound = Math.round(currentRound + remaining * 0.4)
    confidence = Math.min(0.95, 0.6 + convergenceRate * 0.4)
  } else if (convergenceRate > 0) {
    // Mild convergence
    estimatedRound = Math.round(currentRound + remaining * 0.7)
    confidence = 0.4 + convergenceRate * 0.3
  } else {
    // Diverging or flat — unlikely to converge soon
    estimatedRound = props.totalRounds
    confidence = Math.max(0.15, 0.3 + convergenceRate)
  }

  return {
    estimatedRound: Math.min(estimatedRound, props.totalRounds),
    rangeMin: Math.max(currentRound + 1, estimatedRound - 2),
    rangeMax: Math.min(props.totalRounds, estimatedRound + 2),
    confidence,
    convergenceRate,
  }
})

// --- Outcome prediction ---
const outcomePrediction = computed(() => {
  if (!props.actions.length) return []

  let posCount = 0, negCount = 0, neutralCount = 0
  for (const a of props.actions) {
    const s = sentimentOf(a.action_args?.content)
    if (s > 0.1) posCount++
    else if (s < -0.1) negCount++
    else neutralCount++
  }

  const total = posCount + negCount + neutralCount
  if (!total) return []

  return [
    { label: 'Positive Consensus', value: posCount / total, color: '#009900' },
    { label: 'Mixed / No Consensus', value: neutralCount / total, color: '#2068FF' },
    { label: 'Negative Consensus', value: negCount / total, color: '#ff5600' },
  ]
})

// --- Prediction accuracy tracking ---
const accuracyScore = computed(() => {
  if (props.actions.length < 10) return null

  // Compare predictions from first half to actual in second half
  const midIdx = Math.floor(props.actions.length / 2)
  const firstHalf = props.actions.slice(0, midIdx)
  const secondHalf = props.actions.slice(midIdx)

  // Build frequency model from first half
  const agentFreq = new Map()
  for (const a of firstHalf) {
    const name = a.agent_name || a.agent_id
    if (!agentFreq.has(name)) agentFreq.set(name, {})
    const cat = categorizeAction(a.action_type)
    const freq = agentFreq.get(name)
    freq[cat] = (freq[cat] || 0) + 1
  }

  // Predict most frequent for each agent, check against second half
  let correct = 0, total = 0
  for (const a of secondHalf) {
    const name = a.agent_name || a.agent_id
    const freq = agentFreq.get(name)
    if (!freq) continue

    let best = 'post', bestCount = 0
    for (const [cat, count] of Object.entries(freq)) {
      if (count > bestCount) { best = cat; bestCount = count }
    }

    if (categorizeAction(a.action_type) === best) correct++
    total++
  }

  return total > 0 ? correct / total : null
})

// --- D3 Donut chart ---
function clearDonut() {
  if (donutRef.value) d3.select(donutRef.value).selectAll('*').remove()
}

function renderDonut() {
  clearDonut()
  const container = donutRef.value
  if (!container || !outcomePrediction.value.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const size = Math.min(containerWidth, 200)
  const radius = size / 2
  const innerRadius = radius * 0.55

  const svg = d3.select(container)
    .append('svg')
    .attr('width', size)
    .attr('height', size)
    .append('g')
    .attr('transform', `translate(${radius},${radius})`)

  const pie = d3.pie()
    .value(d => d.value)
    .sort(null)
    .padAngle(0.03)

  const arc = d3.arc()
    .innerRadius(innerRadius)
    .outerRadius(radius - 4)
    .cornerRadius(4)

  const arcs = svg.selectAll('.arc')
    .data(pie(outcomePrediction.value))
    .join('g')
    .attr('class', 'arc')

  // Animated arc paths
  arcs.append('path')
    .attr('fill', d => d.data.color)
    .attr('opacity', 0.85)
    .transition()
    .duration(600)
    .attrTween('d', function (d) {
      const interp = d3.interpolate({ startAngle: 0, endAngle: 0 }, d)
      return t => arc(interp(t))
    })

  // Center label
  svg.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '-0.2em')
    .attr('font-size', '20px')
    .attr('font-weight', '600')
    .attr('fill', 'var(--color-text, #050505)')
    .text(`${Math.round((outcomePrediction.value[0]?.value || 0) * 100)}%`)

  svg.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '1.2em')
    .attr('font-size', '10px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text('Top Outcome')
}

// --- Confidence color helper ---
function confidenceColor(confidence) {
  if (confidence >= 0.8) return 'bg-[var(--color-success)]'
  if (confidence >= 0.5) return 'bg-amber-400'
  return 'bg-[var(--color-error)]'
}

function confidenceTextColor(confidence) {
  if (confidence >= 0.8) return 'text-[var(--color-success)]'
  if (confidence >= 0.5) return 'text-amber-500'
  return 'text-[var(--color-error)]'
}

function confidenceLabel(confidence) {
  if (confidence >= 0.8) return 'High'
  if (confidence >= 0.5) return 'Medium'
  return 'Low'
}

// --- Lifecycle ---
watch([() => props.actions.length, () => props.currentRound], () => {
  nextTick(() => renderDonut())
})

onMounted(() => {
  renderDonut()
  if (donutRef.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(renderDonut, 200)
    })
    resizeObserver.observe(donutRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Behavioral Predictions</h3>
      <div v-if="accuracyScore != null" class="flex items-center gap-1.5">
        <span class="text-[10px] text-[var(--color-text-muted)]">Accuracy</span>
        <span
          class="text-xs font-semibold px-1.5 py-0.5 rounded"
          :class="[
            accuracyScore >= 0.7 ? 'bg-[rgba(0,153,0,0.1)] text-[var(--color-success)]' :
            accuracyScore >= 0.4 ? 'bg-amber-50 text-amber-600' :
            'bg-[rgba(239,68,68,0.1)] text-[var(--color-error)]'
          ]"
        >
          {{ Math.round(accuracyScore * 100) }}%
        </span>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!actions.length" class="flex items-center justify-center h-[200px] text-[var(--color-text-muted)] text-sm">
      <span>Predictions will appear as agents interact</span>
    </div>

    <template v-else>
      <!-- Top row: Consensus + Outcome -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">

        <!-- Consensus Prediction -->
        <div class="bg-[var(--color-tint)] rounded-lg p-4">
          <div class="text-xs font-medium text-[var(--color-text-muted)] mb-2">Consensus Estimate</div>
          <template v-if="consensusPrediction">
            <div class="flex items-baseline gap-2 mb-2">
              <span class="text-2xl font-semibold text-[var(--color-text)]">
                Round {{ consensusPrediction.estimatedRound }}
              </span>
              <span class="text-xs text-[var(--color-text-muted)]">
                (± 2 rounds)
              </span>
            </div>
            <div class="flex items-center gap-2">
              <div class="flex-1 h-1.5 bg-[var(--color-border)] rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :class="confidenceColor(consensusPrediction.confidence)"
                  :style="{ width: `${consensusPrediction.confidence * 100}%` }"
                />
              </div>
              <span class="text-[11px] font-medium" :class="confidenceTextColor(consensusPrediction.confidence)">
                {{ confidenceLabel(consensusPrediction.confidence) }}
              </span>
            </div>
            <div class="text-[11px] text-[var(--color-text-muted)] mt-2">
              Range: R{{ consensusPrediction.rangeMin }}–R{{ consensusPrediction.rangeMax }}
              · Convergence {{ consensusPrediction.convergenceRate > 0 ? '+' : '' }}{{ (consensusPrediction.convergenceRate * 100).toFixed(0) }}%
            </div>
          </template>
          <div v-else class="text-xs text-[var(--color-text-muted)] py-4 text-center">
            Not enough data yet
          </div>
        </div>

        <!-- Outcome Prediction Donut -->
        <div class="bg-[var(--color-tint)] rounded-lg p-4">
          <div class="text-xs font-medium text-[var(--color-text-muted)] mb-2">Predicted Outcomes</div>
          <div class="flex items-center gap-4">
            <div ref="donutRef" class="flex-shrink-0" style="width: 120px; height: 120px" />
            <div class="flex flex-col gap-2">
              <div
                v-for="outcome in outcomePrediction"
                :key="outcome.label"
                class="flex items-center gap-2"
              >
                <span class="w-2.5 h-2.5 rounded-full flex-shrink-0" :style="{ backgroundColor: outcome.color }" />
                <div class="min-w-0">
                  <div class="text-[11px] text-[var(--color-text-secondary)] truncate">{{ outcome.label }}</div>
                  <div class="text-xs font-semibold text-[var(--color-text)]">{{ Math.round(outcome.value * 100) }}%</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Agent Predictions Grid -->
      <div class="text-xs font-medium text-[var(--color-text-muted)] mb-2">Per-Agent Predictions</div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
        <div
          v-for="agent in agentPredictions"
          :key="agent.name"
          class="border border-[var(--color-border)] rounded-lg p-3 hover:border-[var(--color-primary)] transition-colors"
        >
          <div class="flex items-center justify-between mb-2">
            <div class="text-xs font-medium text-[var(--color-text)] truncate mr-2">
              {{ agent.name.split(',')[0] }}
            </div>
            <span class="text-[10px] text-[var(--color-text-muted)] flex-shrink-0">
              {{ agent.actionCount }} acts
            </span>
          </div>

          <!-- Predicted action -->
          <div class="flex items-center gap-1.5 mb-2">
            <span class="text-sm">{{ categoryIcon(agent.predictedAction) }}</span>
            <span class="text-xs text-[var(--color-text-secondary)]">
              Next: <span class="font-medium text-[var(--color-text)]">{{ categoryLabel(agent.predictedAction) }}</span>
            </span>
          </div>

          <!-- Confidence bar -->
          <div class="flex items-center gap-2">
            <div class="flex-1 h-1.5 bg-[var(--color-tint)] rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-500"
                :class="confidenceColor(agent.confidence)"
                :style="{ width: `${agent.confidence * 100}%` }"
              />
            </div>
            <span class="text-[10px] font-medium w-8 text-right" :class="confidenceTextColor(agent.confidence)">
              {{ Math.round(agent.confidence * 100) }}%
            </span>
          </div>

          <!-- Sentiment indicator -->
          <div class="flex items-center gap-1 mt-1.5">
            <span
              class="w-1.5 h-1.5 rounded-full"
              :class="agent.avgSentiment > 0.1 ? 'bg-[#009900]' : agent.avgSentiment < -0.1 ? 'bg-[#ff5600]' : 'bg-[#2068FF]'"
            />
            <span class="text-[10px] text-[var(--color-text-muted)]">
              {{ agent.avgSentiment > 0.1 ? 'Positive' : agent.avgSentiment < -0.1 ? 'Negative' : 'Neutral' }} sentiment
            </span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
