import client from './client'

export const comparisonApi = {
  compare: (ids) =>
    client.get('/simulations/compare', { params: { ids: ids.join(',') } }),
  listRuns: () => client.get('/comparison/runs'),
  getData: (runIds, metric) =>
    client.post('/comparison/data', {
      run_ids: runIds,
      ...(metric && { metric }),
    }),
}

// Seeded PRNG for deterministic mock data
function seededRandom(seed) {
  let s = seed
  return () => {
    s = (s * 16807 + 0) % 2147483647
    return (s - 1) / 2147483646
  }
}

function hashString(str) {
  let hash = 5381
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash + str.charCodeAt(i)) | 0
  }
  return Math.abs(hash)
}

const METRIC_CATEGORIES = [
  {
    category: 'Engagement',
    metrics: [
      { name: 'Total Actions', key: 'totalActions', format: 'number' },
      { name: 'Avg Actions/Round', key: 'avgActionsPerRound', format: 'decimal' },
      { name: 'Active Agents', key: 'activeAgents', format: 'number' },
      { name: 'Reply Rate', key: 'replyRate', format: 'percent' },
    ],
  },
  {
    category: 'Sentiment',
    metrics: [
      { name: 'Overall Sentiment', key: 'overallSentiment', format: 'sentiment' },
      { name: 'Positive Ratio', key: 'positiveRatio', format: 'percent' },
      { name: 'Sentiment Volatility', key: 'sentimentVolatility', format: 'decimal' },
    ],
  },
  {
    category: 'Outcomes',
    metrics: [
      { name: 'Consensus Reached', key: 'consensusReached', format: 'percent' },
      { name: 'Decision Quality', key: 'decisionQuality', format: 'decimal' },
      { name: 'Information Spread', key: 'informationSpread', format: 'percent' },
    ],
  },
]

const RADAR_DIMENSIONS = [
  'Overall Sentiment',
  'Consensus Reached',
  'Decision Quality',
  'Agent Engagement',
  'Information Spread',
  'Outcome Satisfaction',
]

function generateMetricsForSim(run, rand) {
  const rounds = run.totalRounds || 24
  const actions = run.totalActions || Math.floor(rand() * 400 + 100)
  return {
    totalActions: actions,
    avgActionsPerRound: +(actions / rounds).toFixed(1),
    activeAgents: Math.floor(rand() * 8 + 7),
    replyRate: +(rand() * 0.4 + 0.2).toFixed(2),
    overallSentiment: +(rand() * 1.2 - 0.3).toFixed(2),
    positiveRatio: +(rand() * 0.4 + 0.3).toFixed(2),
    sentimentVolatility: +(rand() * 0.3 + 0.05).toFixed(2),
    consensusReached: +(rand() * 0.5 + 0.3).toFixed(2),
    decisionQuality: +(rand() * 0.4 + 0.5).toFixed(2),
    informationSpread: +(rand() * 0.3 + 0.5).toFixed(2),
  }
}

function generateTimeline(rounds, rand) {
  const data = []
  let sentiment = rand() * 0.4 - 0.1
  for (let r = 1; r <= rounds; r++) {
    sentiment += (rand() - 0.48) * 0.15
    sentiment = Math.max(-0.8, Math.min(0.8, sentiment))
    data.push({
      round: r,
      sentiment: +sentiment.toFixed(3),
      actions: Math.floor(rand() * 12 + 2),
      agents: Math.floor(rand() * 6 + 4),
    })
  }
  return data
}

export function generateMockComparison(runA, runB) {
  const seedA = hashString(runA.id || 'a')
  const seedB = hashString(runB.id || 'b')
  const randA = seededRandom(seedA)
  const randB = seededRandom(seedB)

  const metricsA = generateMetricsForSim(runA, randA)
  const metricsB = generateMetricsForSim(runB, randB)

  const dimensions = METRIC_CATEGORIES.flatMap((cat) =>
    cat.metrics.map((m) => {
      const valA = metricsA[m.key]
      const valB = metricsB[m.key]
      const diff = +(valA - valB).toFixed(3)
      const absDiff = Math.abs(diff)
      const higherIsBetter = m.key !== 'sentimentVolatility'
      const winner =
        absDiff < 0.01 ? 'tie' : (diff > 0) === higherIsBetter ? 'A' : 'B'
      return {
        category: cat.category,
        name: m.name,
        key: m.key,
        format: m.format,
        simAValue: valA,
        simBValue: valB,
        difference: diff,
        winner,
        significant: absDiff > 0.05,
      }
    }),
  )

  const roundsA = runA.totalRounds || 24
  const roundsB = runB.totalRounds || 24
  const randA2 = seededRandom(seedA + 99)
  const randB2 = seededRandom(seedB + 99)
  const timelineA = generateTimeline(roundsA, randA2)
  const timelineB = generateTimeline(roundsB, randB2)

  const randRadarA = seededRandom(seedA + 200)
  const randRadarB = seededRandom(seedB + 200)
  const radar = RADAR_DIMENSIONS.map((dim) => ({
    dimension: dim,
    valueA: +(randRadarA() * 0.5 + 0.4).toFixed(2),
    valueB: +(randRadarB() * 0.5 + 0.4).toFixed(2),
  }))

  const winsA = dimensions.filter((d) => d.winner === 'A').length
  const winsB = dimensions.filter((d) => d.winner === 'B').length

  return {
    simA: { id: runA.id, name: runA.scenarioName || 'Simulation A', metrics: metricsA },
    simB: { id: runB.id, name: runB.scenarioName || 'Simulation B', metrics: metricsB },
    dimensions,
    radar,
    timelineA,
    timelineB,
    summary: { winsA, winsB, ties: dimensions.length - winsA - winsB },
  }
}
